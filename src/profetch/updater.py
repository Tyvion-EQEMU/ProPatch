from __future__ import annotations

import asyncio
import hashlib
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx

from profetch import db, github, installer
from profetch.components import COMPONENTS, Component, EqFile, TrackingMethod


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Status checks (used by `profetch status`) ────────────────────────────────

async def _check_one(
    client: httpx.AsyncClient,
    component: Component,
    installed_version: str | None,
) -> dict:
    version_tag = None
    try:
        if component.tracking == TrackingMethod.COMMIT_SHA:
            if component.show_version:
                sha_task = github.get_latest_commit_sha(
                    client, component.owner, component.repo, component.branch
                )
                rel_task = github.get_latest_release(client, component.owner, component.repo)
                sha_result, rel_result = await asyncio.gather(
                    sha_task, rel_task, return_exceptions=True
                )
                if isinstance(sha_result, Exception):
                    raise sha_result
                remote = sha_result
                if not isinstance(rel_result, Exception):
                    version_tag = rel_result["tag_name"]
            else:
                remote = await github.get_latest_commit_sha(
                    client, component.owner, component.repo, component.branch
                )
        else:
            release = await github.get_latest_release(
                client, component.owner, component.repo
            )
            remote = release["tag_name"]
            version_tag = remote
    except Exception as exc:
        return {
            "id": component.id,
            "name": component.name,
            "installed": installed_version,
            "remote": None,
            "version_tag": None,
            "status": "error",
            "error": str(exc),
        }

    if installed_version is None:
        status = "not_installed"
    elif installed_version == remote:
        status = "current"
    else:
        status = "update_available"

    return {
        "id": component.id,
        "name": component.name,
        "installed": installed_version,
        "remote": remote,
        "version_tag": version_tag,
        "status": status,
    }


async def _check_eq_one(
    client: httpx.AsyncClient,
    eq_file: EqFile,
    installed_version: str | None,
) -> dict:
    base = {"id": eq_file.id, "name": eq_file.name, "kind": "eq_file"}

    if eq_file.tracking == TrackingMethod.COMMIT_SHA:
        try:
            remote = await github.get_latest_commit_sha(
                client, eq_file.owner, eq_file.repo, eq_file.branch
            )
        except Exception as exc:
            return {**base, "installed": installed_version, "remote": None,
                    "status": "error", "error": str(exc)}

        if installed_version is None:
            status = "not_installed"
        elif installed_version == remote:
            status = "current"
        else:
            status = "update_available"

        return {**base, "installed": installed_version, "remote": remote, "status": status}

    # Content-hash tracked: download and hash to compare
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = eq_file.filename or Path(eq_file.url).name
            file_path = Path(tmpdir) / fname
            await github.download_file(client, eq_file.url, file_path)
            remote_hash = _sha256(file_path)
    except Exception as exc:
        return {**base, "installed": installed_version, "remote": None,
                "status": "error", "error": str(exc)}

    if installed_version is None:
        status = "not_installed"
    elif installed_version == remote_hash:
        status = "current"
    else:
        status = "update_available"

    return {**base, "installed": installed_version, "remote": remote_hash, "status": status}


async def get_all_statuses(
    db_path: Path, enabled_ids: list[str], components: dict[str, Component] | None = None
) -> list[dict]:
    if components is None:
        components = COMPONENTS
    installed = await db.get_all_versions(db_path)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            _check_one(client, components[cid], installed.get(cid))
            for cid in enabled_ids
            if cid in components
        ]
        results = await asyncio.gather(*tasks)

    return list(results)


async def get_eq_file_statuses(
    db_path: Path, eq_files: list[EqFile]
) -> list[dict]:
    installed = await db.get_all_eq_versions(db_path)

    timeout = httpx.Timeout(connect=30.0, read=120.0, write=None, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            _check_eq_one(client, ef, installed.get(ef.id))
            for ef in eq_files
        ]
        results = await asyncio.gather(*tasks)

    return list(results)


# ── Update logic (used by `profetch update`) ──────────────────────────────────

def _error_result(
    component: Component,
    old_ver: str | None,
    new_ver: str | None,
    error: str,
) -> dict:
    return {
        "id": component.id,
        "name": component.name,
        "status": "error",
        "old_version": old_ver,
        "new_version": new_ver,
        "written": 0,
        "skipped": 0,
        "error": error,
    }


async def update_one(
    client: httpx.AsyncClient,
    component: Component,
    mq_rekkas: Path,
    db_path: Path,
    installed_version: str | None,
    on_downloading: Callable[[], None] | None = None,
) -> dict:
    release_data = None
    try:
        if component.tracking == TrackingMethod.COMMIT_SHA:
            remote = await github.get_latest_commit_sha(
                client, component.owner, component.repo, component.branch
            )
        else:
            release_data = await github.get_latest_release(
                client, component.owner, component.repo
            )
            remote = release_data["tag_name"]
    except Exception as exc:
        return _error_result(component, installed_version, None, str(exc))

    if installed_version == remote:
        return {
            "id": component.id,
            "name": component.name,
            "status": "current",
            "old_version": installed_version,
            "new_version": remote,
            "written": 0,
            "skipped": 0,
        }

    if on_downloading:
        on_downloading()

    dest_root = mq_rekkas / component.destination if component.destination else mq_rekkas

    try:
        dest_root.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            if component.tracking == TrackingMethod.COMMIT_SHA:
                zip_path = tmp / f"{component.repo}.zip"
                await github.download_zip(
                    client, component.owner, component.repo, component.branch, zip_path
                )
                written, skipped = installer.extract_zip(
                    zip_path, dest_root, component.protected_patterns, component.zip_subdir
                )
            else:
                asset_url = github.find_release_asset_url(
                    release_data, component.release_asset_name
                )
                if not asset_url:
                    raise ValueError(
                        f"Asset '{component.release_asset_name}' not found in release {remote}"
                    )
                file_path = tmp / component.release_asset_name
                await github.download_file(client, asset_url, file_path)
                ok = installer.install_single_file(
                    file_path, dest_root, component.protected_patterns
                )
                written, skipped = (1, 0) if ok else (0, 1)

    except Exception as exc:
        return _error_result(component, installed_version, remote, str(exc))

    await db.set_installed_version(db_path, component.id, remote)

    return {
        "id": component.id,
        "name": component.name,
        "status": "updated",
        "old_version": installed_version,
        "new_version": remote,
        "written": written,
        "skipped": skipped,
    }


# ── EQ file update logic ──────────────────────────────────────────────────────

def _eq_error_result(eq_file: EqFile, error: str) -> dict:
    return {
        "id": eq_file.id,
        "name": eq_file.name,
        "status": "error",
        "written": 0,
        "error": error,
        "kind": "eq_file",
    }


async def update_eq_file(
    client: httpx.AsyncClient,
    eq_file: EqFile,
    eq_dirs: list[Path],
    db_path: Path,
    installed_version: str | None,
    on_downloading: Callable[[], None] | None = None,
) -> dict:
    if not eq_dirs:
        return {
            "id": eq_file.id,
            "name": eq_file.name,
            "status": "skipped",
            "written": 0,
            "error": "no eq_dirs configured",
            "kind": "eq_file",
        }

    # Commit-SHA tracked: cheap remote check first, skip download if current
    if eq_file.tracking == TrackingMethod.COMMIT_SHA:
        try:
            remote_version = await github.get_latest_commit_sha(
                client, eq_file.owner, eq_file.repo, eq_file.branch
            )
        except Exception as exc:
            return _eq_error_result(eq_file, str(exc))

        if installed_version == remote_version:
            return {
                "id": eq_file.id,
                "name": eq_file.name,
                "status": "current",
                "written": 0,
                "kind": "eq_file",
            }

        if on_downloading:
            on_downloading()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / f"{eq_file.repo}.zip"
                await github.download_zip(
                    client, eq_file.owner, eq_file.repo, eq_file.branch, zip_path
                )
                written, _ = installer.extract_zip_to_eq_dirs(
                    zip_path, eq_dirs, eq_file.destination
                )
        except Exception as exc:
            return _eq_error_result(eq_file, str(exc))

        await db.set_eq_file_version(db_path, eq_file.id, remote_version)
        return {
            "id": eq_file.id,
            "name": eq_file.name,
            "status": "updated",
            "written": written,
            "dirs": len(eq_dirs),
            "kind": "eq_file",
        }

    # Content-hash tracked (default for direct-URL files): download, hash, compare
    if on_downloading:
        on_downloading()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fname = eq_file.filename or Path(eq_file.url).name
            file_path = tmp / fname
            await github.download_file(client, eq_file.url, file_path)

            new_hash = _sha256(file_path)

            if installed_version == new_hash:
                return {
                    "id": eq_file.id,
                    "name": eq_file.name,
                    "status": "current",
                    "written": 0,
                    "kind": "eq_file",
                }

            if eq_file.extract:
                written, _ = installer.extract_zip_to_eq_dirs(
                    file_path, eq_dirs, eq_file.destination
                )
            else:
                written = installer.install_eq_file(
                    file_path, eq_dirs, eq_file.destination
                )

    except Exception as exc:
        return _eq_error_result(eq_file, str(exc))

    await db.set_eq_file_version(db_path, eq_file.id, new_hash)
    return {
        "id": eq_file.id,
        "name": eq_file.name,
        "status": "updated",
        "written": written,
        "dirs": len(eq_dirs),
        "kind": "eq_file",
    }
