from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional

from profetch import config, db, updater
from profetch.components import COMPONENTS

logger = logging.getLogger("profetch")

StatusCallback = Callable[[str, str, Optional[str], Optional[str]], None]


def _get_eq_dirs(settings) -> list[Path]:
    try:
        raw = settings.get("PATHS.eq_dirs", default=[])
        if isinstance(raw, str):
            raw = [raw]
        return [Path(d) for d in raw if d]
    except Exception:
        return []


def _display_ver(sha: str | None, version_tag: str | None = None) -> str:
    if version_tag:
        return version_tag
    if sha is None:
        return "—"
    if len(sha) >= 7 and all(c in "0123456789abcdef" for c in sha.lower()):
        return sha[:7]
    return sha


def _emit_status(result: dict, on_status: StatusCallback) -> None:
    cid    = result["id"]
    status = result.get("status", "error")
    vtag   = result.get("version_tag")

    if status == "current":
        ver = _display_ver(result.get("installed"), vtag)
        on_status(cid, "current", ver, ver)
    elif status in ("update_available", "not_installed"):
        local  = _display_ver(result.get("installed"), vtag)
        remote = _display_ver(result.get("remote"), vtag)
        on_status(cid, "update_available", local, remote)
    elif status == "untracked":
        ver = _display_ver(result.get("remote"), vtag)
        on_status(cid, "current", ver, ver)
    else:
        on_status(cid, "error", None, None)


async def _load_manifest():
    import httpx
    from profetch import github as gh
    settings      = config.load_settings()
    github_token  = config.get_github_token(settings)
    timeout = httpx.Timeout(connect=30.0, read=60.0, write=None, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout, headers=gh.auth_headers(github_token)) as client:
        try:
            from profetch.manifest import fetch_manifest
            components_list, eq_files = await fetch_manifest(client)
            return {c.id: c for c in components_list}, eq_files
        except Exception as exc:
            logger.warning(f"Manifest fetch failed ({exc}), using built-in list")
            return dict(COMPONENTS), []


def run_status_check(component_ids: list[str], on_status: StatusCallback) -> None:
    settings     = config.load_settings()
    db_path      = config.get_db_path()
    github_token = config.get_github_token(settings)
    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = None

    for cid in component_ids:
        on_status(cid, "checking", None, None)

    async def _run():
        await db.init_db(db_path)
        components, eq_files = await _load_manifest()

        mq_ids = [cid for cid in component_ids if cid in components]
        eq_ids = [cid for cid in component_ids if cid not in components]

        results: list[dict] = []
        if mq_ids:
            results += await updater.get_all_statuses(
                db_path, mq_ids, components, mq_rekkas, github_token
            )
        if eq_ids and eq_files:
            relevant = [ef for ef in eq_files if ef.id in eq_ids]
            if relevant:
                results += await updater.get_eq_file_statuses(
                    db_path, relevant, _get_eq_dirs(settings), github_token
                )
        return results

    try:
        for r in asyncio.run(_run()):
            _emit_status(r, on_status)
    except Exception as exc:
        logger.error(f"Status check failed: {exc}")
        for cid in component_ids:
            on_status(cid, "error", None, None)


def run_update(
    component_ids: list[str],
    on_status: StatusCallback,
    on_done: Callable[[], None],
) -> None:
    settings     = config.load_settings()
    db_path      = config.get_db_path()
    github_token = config.get_github_token(settings)
    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = Path(r"C:\Games\MQ-Rekkas")
    eq_dirs = _get_eq_dirs(settings)

    async def _run():
        await db.init_db(db_path)
        import httpx
        from profetch import github as gh
        timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, headers=gh.auth_headers(github_token)) as client:
            try:
                from profetch.manifest import fetch_manifest
                components_list, eq_files = await fetch_manifest(client)
                components = {c.id: c for c in components_list}
            except Exception:
                components = dict(COMPONENTS)
                eq_files   = []

            installed    = await db.get_all_versions(db_path)
            eq_installed = await db.get_all_eq_versions(db_path)

            for cid in component_ids:
                if cid in components:
                    comp = components[cid]
                    on_status(cid, "updating", _display_ver(installed.get(cid)), None)
                    result = await updater.update_one(
                        client, comp, mq_rekkas, db_path, installed.get(cid),
                        on_downloading=lambda c=comp: on_status(
                            c.id, "updating", _display_ver(installed.get(c.id)), None
                        ),
                    )
                    if result["status"] in ("updated", "adopted"):
                        ver = _display_ver(result.get("new_version"))
                        on_status(cid, "updated", ver, ver)
                    elif result["status"] == "current":
                        ver = _display_ver(result.get("new_version"))
                        on_status(cid, "current", ver, ver)
                    else:
                        on_status(cid, "error", None, None)
                else:
                    relevant = [ef for ef in eq_files if ef.id == cid]
                    if relevant and eq_dirs:
                        ef = relevant[0]
                        on_status(cid, "updating", None, None)
                        result = await updater.update_eq_file(
                            client, ef, eq_dirs, db_path, eq_installed.get(cid)
                        )
                        if result["status"] in ("updated", "current"):
                            badge = "updated" if result["status"] == "updated" else "current"
                            on_status(cid, badge, "✓", "✓")
                        else:
                            on_status(cid, "error", None, None)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Update failed: {exc}")
        for cid in component_ids:
            on_status(cid, "error", None, None)
    finally:
        on_done()
