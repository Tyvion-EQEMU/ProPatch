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


def _log_scan_result(r: dict, components: dict) -> None:
    cid    = r["id"]
    name   = r.get("name", cid)
    status = r.get("status", "error")
    vtag   = r.get("version_tag")
    comp   = components.get(cid)
    gh_url = (f"https://github.com/{comp.owner}/{comp.repo}/releases"
              if comp else "")
    inst   = _display_ver(r.get("installed"), vtag)
    remote = _display_ver(r.get("remote"),    vtag)

    if status == "current":
        msg = f"  {name}: current ({inst})"
    elif status == "update_available":
        msg = f"  {name}: update available  {inst} → {remote}"
    elif status == "not_installed":
        msg = f"  {name}: not installed (latest: {remote})"
    elif status == "untracked":
        msg = f"  {name}: untracked ({remote})"
    elif status == "error":
        msg = f"  {name}: error — {r.get('error', 'unknown')}"
    else:
        msg = f"  {name}: {status}"

    if gh_url and status != "error":
        msg += f"  {gh_url}"

    if status == "error":
        logger.warning(msg)
    else:
        logger.info(msg)


def _log_update_result(r: dict, components: dict) -> None:
    cid    = r["id"]
    name   = r.get("name", cid)
    status = r.get("status", "error")
    comp   = components.get(cid)
    gh_url = (f"https://github.com/{comp.owner}/{comp.repo}/releases"
              if comp else "")
    old_v  = r.get("old_version") or "—"
    new_v  = r.get("new_version") or "—"

    if status == "updated":
        msg = f"  {name}: updated  {old_v} → {new_v}"
    elif status == "adopted":
        msg = f"  {name}: adopted  (registered as {new_v})"
    elif status == "current":
        msg = f"  {name}: already current ({new_v})"
    elif status == "error":
        msg = f"  {name}: update error — {r.get('error', 'unknown')}"
    else:
        msg = f"  {name}: {status}"

    if gh_url and status != "error":
        msg += f"  {gh_url}"

    if status == "error":
        logger.warning(msg)
    else:
        logger.info(msg)


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


async def _self_update_profetch(client, comp, installed_version: str | None) -> dict:
    """Download the latest profetch.exe release and launch a bat-swap restart.

    Returns a status dict:
      "current"              — already on the latest version
      "update_available"     — newer version found but running in dev mode (no swap)
      "self_update_pending"  — bat launched, app should exit
    Raises on download or bat-write failure so the caller can fall back gracefully.
    """
    import os
    import subprocess
    import sys
    from profetch import github

    release = await github.get_latest_release(client, comp.owner, comp.repo)
    remote  = release["tag_name"]

    if installed_version == remote:
        return {"status": "current", "new_version": remote}

    if not getattr(sys, "frozen", False):
        # Dev mode — no exe to swap; just report the update
        return {"status": "update_available", "new_version": remote}

    asset_name = comp.release_asset_name or "profetch.exe"
    asset_url  = github.find_release_asset_url(release, asset_name)
    if not asset_url:
        raise ValueError(f"Release asset '{asset_name}' not found in {remote}")

    exe_path = Path(sys.executable)
    exe_dir  = exe_path.parent
    new_exe  = exe_dir / "profetch_new.exe"
    bat_path = exe_dir / "profetch_update.bat"

    logger.info(f"  ProFetch: downloading {remote} from {asset_url}")
    await github.download_file(client, asset_url, new_exe)

    pid     = os.getpid()
    exe_str = str(exe_path)
    new_str = str(new_exe)

    # Loop on the PID so we only move the exe once the old process is gone.
    # A fixed sleep races with PyInstaller shutdown and loses — the exe stays
    # locked until the process truly exits.
    bat_content = (
        "@echo off\n"
        ":WAIT\n"
        f'tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul 2>&1\n'
        "if not errorlevel 1 (\n"
        "    timeout /t 1 /nobreak >nul\n"
        "    goto WAIT\n"
        ")\n"
        f'move /y "{new_str}" "{exe_str}"\n'
        f'start "" "{exe_str}"\n'
        'del "%~f0"\n'
    )
    bat_path.write_text(bat_content, encoding="utf-8")

    _CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=_CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    return {"status": "self_update_pending", "new_version": remote}


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

        logger.info("--- scan ---")
        for r in results:
            _log_scan_result(r, components)

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

            logger.info("--- update ---")

            for cid in component_ids:
                # ── ProFetch self-update (special bat-swap path) ───────────────
                if cid == "profetch" and cid in components:
                    comp = components[cid]
                    on_status(cid, "updating", _display_ver(installed.get(cid)), None)
                    try:
                        result = await _self_update_profetch(client, comp, installed.get(cid))
                    except Exception as exc:
                        logger.error(f"  ProFetch: self-update failed — {exc}")
                        on_status(cid, "update_available", _display_ver(installed.get(cid)), None)
                        continue

                    new_v = _display_ver(result.get("new_version"))
                    if result["status"] == "self_update_pending":
                        logger.info(f"  ProFetch: restarting to apply {new_v}")
                        on_status(cid, "self_update_pending", new_v, new_v)
                    elif result["status"] == "current":
                        logger.info(f"  ProFetch: already current ({new_v})")
                        on_status(cid, "current", new_v, new_v)
                    else:
                        # update_available in dev mode
                        logger.info(f"  ProFetch: update available (dev mode — no swap)")
                        on_status(cid, "update_available", _display_ver(installed.get(cid)), new_v)
                    continue

                # ── MQ directory components ────────────────────────────────────
                if cid in components:
                    comp = components[cid]
                    on_status(cid, "updating", _display_ver(installed.get(cid)), None)
                    result = await updater.update_one(
                        client, comp, mq_rekkas, db_path, installed.get(cid),
                        on_downloading=lambda c=comp: on_status(
                            c.id, "updating", _display_ver(installed.get(c.id)), None
                        ),
                    )
                    _log_update_result(result, components)
                    if result["status"] in ("updated", "adopted"):
                        ver = _display_ver(result.get("new_version"))
                        on_status(cid, "updated", ver, ver)
                    elif result["status"] == "current":
                        ver = _display_ver(result.get("new_version"))
                        on_status(cid, "current", ver, ver)
                    else:
                        on_status(cid, "error", None, None)

                # ── EQ server files ────────────────────────────────────────────
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
                            logger.info(
                                f"  {ef.name}: {result['status']}"
                                + (f" ({result.get('written', 0)} files)" if result["status"] == "updated" else "")
                            )
                            on_status(cid, badge, "✓", "✓")
                        else:
                            logger.warning(f"  {ef.name}: {result.get('status')} — {result.get('error', '')}")
                            on_status(cid, "error", None, None)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Update failed: {exc}")
        for cid in component_ids:
            on_status(cid, "error", None, None)
    finally:
        on_done()
