from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx

from profetch import db, github, installer
from profetch.components import COMPONENTS, Component, TrackingMethod


# ── Status checks (used by `profetch status`) ────────────────────────────────

async def _check_one(
    client: httpx.AsyncClient,
    component: Component,
    installed_version: str | None,
) -> dict:
    try:
        if component.tracking == TrackingMethod.COMMIT_SHA:
            remote = await github.get_latest_commit_sha(
                client, component.owner, component.repo, component.branch
            )
        else:
            release = await github.get_latest_release(
                client, component.owner, component.repo
            )
            remote = release["tag_name"]
    except Exception as exc:
        return {
            "id": component.id,
            "name": component.name,
            "installed": installed_version,
            "remote": None,
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
        "status": status,
    }


async def get_all_statuses(
    db_path: Path, enabled_ids: list[str]
) -> list[dict]:
    installed = await db.get_all_versions(db_path)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            _check_one(client, COMPONENTS[cid], installed.get(cid))
            for cid in enabled_ids
            if cid in COMPONENTS
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
    """
    Check remote version, download if needed, install, record in DB.
    Calls on_downloading() (sync) right before the download begins so the
    caller can update a progress spinner.
    """
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
