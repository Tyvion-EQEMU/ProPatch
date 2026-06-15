from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure the terminal can display Unicode (e.g., ✓ ↑ ✗) on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import httpx
import typer

from profetch.__about__ import __version__
from profetch import config, db, log as plog, ui, updater
from profetch.components import COMPONENTS, Component, EqFile

# Short aliases the user can type on the CLI
_ALIASES: dict[str, str] = {
    "rekkas":    "rekkas_mq",
    "rekkas_mq": "rekkas_mq",
    "mq2rwarp":  "mq2rwarp",
    "rwarp":     "mq2rwarp",
    "rgmercs":   "rgmercs",
    "mercs":     "rgmercs",
    "e9loot":    "proloot",
    "proloot":   "proloot",
    "loot":      "proloot",
}

app = typer.Typer(
    name="profetch",
    help="ProFetch — EQProfusion Component Manager",
    no_args_is_help=False,
    invoke_without_command=True,
)


def _enabled_components(settings, components: dict[str, Component]) -> list[str]:
    result = []
    for cid in components:
        try:
            enabled = settings.get(f"COMPONENTS.{cid}", default=True)
        except Exception:
            enabled = True
        if enabled:
            result.append(cid)
    return result


def _get_eq_dirs(settings) -> list[Path]:
    try:
        raw = settings.get("PATHS.eq_dirs", default=[])
        if isinstance(raw, str):
            raw = [raw]
        return [Path(d) for d in raw if d]
    except Exception:
        return []


async def _load_manifest(client: httpx.AsyncClient) -> tuple[dict[str, Component], list[EqFile]]:
    """Fetch the manifest; fall back to hardcoded COMPONENTS on failure."""
    try:
        from profetch.manifest import fetch_manifest
        components_list, eq_files = await fetch_manifest(client)
        components = {c.id: c for c in components_list}
        return components, eq_files
    except Exception as exc:
        ui.print_info(f"Manifest unavailable ({exc}), using built-in component list.")
        return COMPONENTS, []


@app.command()
def status():
    """Show current installed versions vs. remote."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()
    plog.setup(config.get_data_dir() / "profetch.log")

    asyncio.run(_status_async(db_path, settings))


def _build_config_info(settings) -> dict:
    from profetch.config import get_data_dir
    try:
        mq_path = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_path = None
    eq_dirs = _get_eq_dirs(settings)
    try:
        raw_names = settings.get("PATHS.eq_dir_names", default=[])
        if isinstance(raw_names, str):
            raw_names = [raw_names]
        eq_dir_names = list(raw_names) if raw_names else []
    except Exception:
        eq_dir_names = []
    data_dir = get_data_dir()
    return {
        "mq_rekkas": {"path": mq_path, "exists": mq_path is not None and mq_path.exists()},
        "eq_dirs": [
            {"path": d, "exists": d.exists(), "name": eq_dir_names[i] if i < len(eq_dir_names) else ""}
            for i, d in enumerate(eq_dirs)
        ],
        "data_dir": {"path": data_dir, "exists": data_dir.exists()},
    }


async def _status_async(db_path: Path, settings) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    github_token = config.get_github_token(settings)
    timeout = httpx.Timeout(connect=30.0, read=60.0, write=None, pool=30.0)
    from profetch import github as gh
    async with httpx.AsyncClient(timeout=timeout, headers=gh.auth_headers(github_token)) as client:
        components, eq_files = await _load_manifest(client)

    enabled = _enabled_components(settings, components)
    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = None
    eq_dirs = _get_eq_dirs(settings)

    with ui.console.status("[dim]Checking for updates...[/dim]"):
        mq_statuses, eq_statuses = await asyncio.gather(
            updater.get_all_statuses(db_path, enabled, components, mq_rekkas, github_token),
            updater.get_eq_file_statuses(db_path, eq_files, eq_dirs, github_token),
        )
    table = ui.build_status_table(mq_statuses, eq_statuses)
    ui.console.print(table)
    ui.print_config_section(_build_config_info(settings))
    ui.print_setup_reminder()

    log = plog.get()
    log.info("--- status ---")
    for s in mq_statuses + eq_statuses:
        code = s.get("status", "unknown")
        name = s["name"]
        if code == "current":
            log.info(f"  {name}: current ({ui._short(s.get('installed'))})")
        elif code == "update_available":
            vtag = f" [{s['version_tag']}]" if s.get("version_tag") else ""
            log.info(f"  {name}: update available ({ui._short(s.get('installed'))} -> {ui._short(s.get('remote'))}{vtag})")
        elif code == "not_installed":
            log.info(f"  {name}: not installed")
        elif code == "untracked":
            log.info(f"  {name}: untracked (files on disk, not in database)")
        elif code == "error":
            log.warning(f"  {name}: error — {s.get('error')}")


@app.command()
def update(
    component: str = typer.Argument(
        None,
        help="Component to update: rekkas, mq2rwarp, rgmercs, proloot. Omit to update all.",
    ),
):
    """Download and install updates for MQ components (and EQ files when updating all)."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()

    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = Path(r"C:\Games\MQ-Profusion")

    eq_dirs = _get_eq_dirs(settings)
    plog.setup(config.get_data_dir() / "profetch.log")

    if component is not None:
        cid = _ALIASES.get(component.lower())
        if not cid:
            valid = ", ".join(sorted(set(_ALIASES.values())))
            ui.print_error(f"Unknown component '{component}'. Valid IDs: {valid}")
            raise typer.Exit(1)
        asyncio.run(_update_async(db_path, mq_rekkas, [cid], eq_dirs, settings, include_eq=False))
    else:
        asyncio.run(_update_async(db_path, mq_rekkas, None, eq_dirs, settings, include_eq=True))


@app.command(name="update-eq")
def update_eq():
    """Download and install EQ server-specific files to each configured EQ directory."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()
    eq_dirs = _get_eq_dirs(settings)

    plog.setup(config.get_data_dir() / "profetch.log")

    if not eq_dirs:
        ui.print_error(
            "No EQ directories configured. Add eq_dirs to settings.local.toml:\n"
            '  [paths]\n  eq_dirs = ["C:\\\\Games\\\\EverQuest"]'
        )
        raise typer.Exit(1)

    asyncio.run(_update_eq_async(db_path, eq_dirs))


def _log_update_result(log, result: dict) -> None:
    name = result["name"]
    status = result.get("status")
    if status == "updated":
        old = ui._short(result.get("old_version"))
        new = ui._short(result.get("new_version"))
        written = result.get("written", 0)
        log.info(f"  {name}: updated {old} -> {new} ({written} files)")
    elif status == "adopted":
        new = ui._short(result.get("new_version"))
        log.info(f"  {name}: adopted (existing files registered as {new})")
    elif status == "current":
        log.info(f"  {name}: already current")
    elif status == "error":
        log.error(f"  {name}: {result.get('error', 'unknown error')}")


async def _update_async(
    db_path: Path,
    mq_rekkas: Path,
    component_ids: list[str] | None,
    eq_dirs: list[Path],
    settings,
    include_eq: bool,
) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    github_token = config.get_github_token(settings)
    from profetch import github as gh
    timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)
    updated = current = errors = 0

    async with httpx.AsyncClient(timeout=timeout, headers=gh.auth_headers(github_token)) as client:
        components, eq_files = await _load_manifest(client)

        # Resolve component list
        if component_ids is None:
            cids = _enabled_components(settings, components)
        else:
            cids = [cid for cid in component_ids if cid in components]
            if not cids and component_ids:
                # Manifest might not have it; fall back to COMPONENTS
                cids = [cid for cid in component_ids if cid in COMPONENTS]
                components = {**components, **{c: COMPONENTS[c] for c in cids}}

        # ── Pre-flight check ─────────────────────────────────────────────────
        eq_to_check = eq_files if (include_eq and eq_dirs) else []
        with ui.console.status("[dim]Checking for updates...[/dim]"):
            mq_statuses, eq_statuses = await asyncio.gather(
                updater.get_all_statuses(db_path, cids, components, mq_rekkas, github_token),
                updater.get_eq_file_statuses(db_path, eq_to_check, eq_dirs, github_token),
            )

        needs_update_ids = {
            s["id"] for s in mq_statuses + eq_statuses
            if s["status"] in ("not_installed", "update_available", "untracked")
        }

        log = plog.get()
        log.info("--- update ---")
        for s in mq_statuses + eq_statuses:
            code = s.get("status", "unknown")
            name = s["name"]
            if code == "current":
                log.info(f"  {name}: current ({ui._short(s.get('installed'))})")
            elif code in ("not_installed", "update_available", "untracked"):
                log.info(f"  {name}: {code.replace('_', ' ')}")
            elif code == "error":
                log.warning(f"  {name}: error — {s.get('error')}")

        if not needs_update_ids:
            ui.console.print("  [green]Everything is up to date.[/green]")
            ui.print_setup_reminder()
            return

        ui.print_preflight([s for s in mq_statuses + eq_statuses if s["id"] in needs_update_ids])
        typer.confirm("  Proceed?", default=True, abort=True)
        ui.console.print()

        # ── Apply updates ─────────────────────────────────────────────────────
        cids_to_update = [cid for cid in cids if cid in needs_update_ids]
        eq_files_to_update = [ef for ef in eq_files if ef.id in needs_update_ids]

        installed = await db.get_all_versions(db_path)

        with ui.console.status("") as spinner:
            for cid in cids_to_update:
                if cid not in components:
                    continue
                comp = components[cid]
                spinner.update(f"  [dim]{comp.name}[/dim]  Checking...")

                result = await updater.update_one(
                    client, comp, mq_rekkas, db_path, installed.get(cid),
                    on_downloading=lambda c=comp: spinner.update(
                        f"  [dim]{c.name}[/dim]  Downloading..."
                    ),
                )
                ui.print_update_result(result)
                _log_update_result(log, result)

                if result["status"] == "updated":
                    updated += 1
                elif result["status"] == "current":
                    current += 1
                else:
                    errors += 1

            if include_eq and eq_files_to_update:
                ui.console.print()
                eq_installed = await db.get_all_eq_versions(db_path)
                for ef in eq_files_to_update:
                    spinner.update(f"  [dim]{ef.name}[/dim]  Downloading...")
                    result = await updater.update_eq_file(
                        client, ef, eq_dirs, db_path, eq_installed.get(ef.id),
                        on_downloading=lambda f=ef: spinner.update(
                            f"  [dim]{f.name}[/dim]  Downloading..."
                        ),
                    )
                    ui.print_update_result(result)
                    _log_update_result(log, result)
                    if result["status"] == "updated":
                        updated += 1
                    elif result["status"] == "current":
                        current += 1
                    elif result["status"] not in ("skipped",):
                        errors += 1

    parts = []
    if updated:
        parts.append(f"[green]{updated} updated[/green]")
    if current:
        parts.append(f"[dim]{current} current[/dim]")
    if errors:
        parts.append(f"[red]{errors} error(s)[/red]")

    summary = ", ".join(parts) if parts else "nothing to do"
    ui.console.print(f"\nDone. {summary}.")
    log.info(f"  done: {updated} updated, {current} current, {errors} error(s)")
    ui.print_setup_reminder()


async def _update_eq_async(db_path: Path, eq_dirs: list[Path]) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)
    updated = current = errors = 0
    log = plog.get()
    log.info("--- update-eq ---")

    async with httpx.AsyncClient(timeout=timeout) as client:
        _, eq_files = await _load_manifest(client)

        if not eq_files:
            ui.print_info("No EQ files defined in manifest.")
            return

        eq_installed = await db.get_all_eq_versions(db_path)

        with ui.console.status("") as spinner:
            for ef in eq_files:
                spinner.update(f"  [dim]{ef.name}[/dim]  Checking...")
                result = await updater.update_eq_file(
                    client, ef, eq_dirs, db_path, eq_installed.get(ef.id),
                    on_downloading=lambda f=ef: spinner.update(
                        f"  [dim]{f.name}[/dim]  Downloading..."
                    ),
                )
                ui.print_update_result(result)
                _log_update_result(log, result)
                if result["status"] == "updated":
                    updated += 1
                elif result["status"] == "current":
                    current += 1
                elif result["status"] not in ("skipped",):
                    errors += 1

    parts = []
    if updated:
        parts.append(f"[green]{updated} updated[/green]")
    if current:
        parts.append(f"[dim]{current} current[/dim]")
    if errors:
        parts.append(f"[red]{errors} error(s)[/red]")

    summary = ", ".join(parts) if parts else "nothing to do"
    ui.console.print(f"\nDone. {summary}.")
    log.info(f"  done: {updated} updated, {current} current, {errors} error(s)")
    ui.print_setup_reminder()


@app.command()
def components():
    """Interactively enable or disable managed components."""
    settings = config.load_settings()
    config.ensure_data_dir()
    plog.setup(config.get_data_dir() / "profetch.log")
    asyncio.run(_components_async(settings))


async def _components_async(settings) -> None:
    ui.print_header(__version__)

    github_token = config.get_github_token(settings)
    from profetch import github as gh
    timeout = httpx.Timeout(connect=30.0, read=60.0, write=None, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout, headers=gh.auth_headers(github_token)) as client:
        all_components, _ = await _load_manifest(client)

    cid_list = list(all_components.keys())

    # Read current enabled state
    enabled: dict[str, bool] = {}
    for cid in cid_list:
        try:
            enabled[cid] = bool(settings.get(f"COMPONENTS.{cid}", default=True))
        except Exception:
            enabled[cid] = True

    ui.console.print("  [bold]Component Selection[/bold]\n")
    ui.console.print("  Enter a number to toggle a component on or off.\n"
                     "  Press Enter with no input to save and exit.\n")

    while True:
        for i, cid in enumerate(cid_list, 1):
            comp = all_components[cid]
            check = "[green]✓[/green]" if enabled[cid] else "[dim] [/dim]"
            ui.console.print(f"    [{i}] {check}  {comp.name}")
        ui.console.print()

        raw = typer.prompt("  Toggle", default="", show_default=False)
        ui.console.print()

        if not raw.strip():
            break

        try:
            idx = int(raw.strip()) - 1
            if 0 <= idx < len(cid_list):
                cid = cid_list[idx]
                enabled[cid] = not enabled[cid]
            else:
                ui.console.print(f"  [red]Enter a number between 1 and {len(cid_list)}[/red]\n")
        except ValueError:
            ui.console.print("  [red]Please enter a number.[/red]\n")

    config.save_component_settings(config.get_data_dir(), enabled)
    ui.console.print("  [green]Saved.[/green] Run [bold white]profetch status[/bold white] to verify.\n")


@app.command()
def setup():
    """Reconfigure ProFetch paths and settings."""
    from profetch.setup import run_setup
    config.ensure_data_dir()
    run_setup(config.get_data_dir())


@app.command()
def version():
    """Show ProFetch version."""
    typer.echo(f"ProFetch v{__version__}")


def _launch_gui() -> None:
    from profetch.gui.app import launch
    launch()


def main() -> None:
    # No subcommand → launch GUI
    if len(sys.argv) == 1:
        _launch_gui()
        return

    app()


if __name__ == "__main__":
    main()
