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
from profetch import config, db, ui, updater
from profetch.components import COMPONENTS, Component, EqFile

# Short aliases the user can type on the CLI
_ALIASES: dict[str, str] = {
    "rekkas":    "rekkas_mq",
    "rekkas_mq": "rekkas_mq",
    "mq2rwarp":  "mq2rwarp",
    "rwarp":     "mq2rwarp",
    "rgmercs":   "rgmercs",
    "mercs":     "rgmercs",
    "e9loot":    "e9loot",
    "proloot":   "e9loot",
    "loot":      "e9loot",
}

app = typer.Typer(
    name="profetch",
    help="proFetch — EQProfusion Component Manager",
    no_args_is_help=True,
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

    asyncio.run(_status_async(db_path, settings))


def _build_config_info(settings) -> dict:
    from profetch.config import get_data_dir
    try:
        mq_path = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_path = None
    eq_dirs = _get_eq_dirs(settings)
    data_dir = get_data_dir()
    return {
        "mq_rekkas": {"path": mq_path, "exists": mq_path is not None and mq_path.exists()},
        "eq_dirs": [{"path": d, "exists": d.exists()} for d in eq_dirs],
        "data_dir": {"path": data_dir, "exists": data_dir.exists()},
    }


async def _status_async(db_path: Path, settings) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    timeout = httpx.Timeout(connect=30.0, read=60.0, write=None, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        components, eq_files = await _load_manifest(client)

    enabled = _enabled_components(settings, components)
    mq_statuses, eq_statuses = await asyncio.gather(
        updater.get_all_statuses(db_path, enabled, components),
        updater.get_eq_file_statuses(db_path, eq_files),
    )
    table = ui.build_status_table(mq_statuses, eq_statuses)
    ui.console.print(table)
    ui.print_config_section(_build_config_info(settings))


@app.command()
def update(
    component: str = typer.Argument(
        None,
        help="Component to update: rekkas, mq2rwarp, rgmercs, e9loot. Omit to update all.",
    ),
):
    """Download and install updates for MQ components (and EQ files when updating all)."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()

    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = Path(r"C:\Games\MQ-Rekka")

    eq_dirs = _get_eq_dirs(settings)

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

    if not eq_dirs:
        ui.print_error(
            "No EQ directories configured. Add eq_dirs to settings.local.toml:\n"
            '  [paths]\n  eq_dirs = ["C:\\\\Games\\\\EverQuest"]'
        )
        raise typer.Exit(1)

    asyncio.run(_update_eq_async(db_path, eq_dirs))


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

    timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)
    updated = current = errors = 0

    async with httpx.AsyncClient(timeout=timeout) as client:
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

        installed = await db.get_all_versions(db_path)

        with ui.console.status("") as spinner:
            for cid in cids:
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

                if result["status"] == "updated":
                    updated += 1
                elif result["status"] == "current":
                    current += 1
                else:
                    errors += 1

            if include_eq and eq_files:
                ui.console.print()
                eq_installed = await db.get_all_eq_versions(db_path)
                for ef in eq_files:
                    spinner.update(f"  [dim]{ef.name}[/dim]  Checking...")
                    result = await updater.update_eq_file(
                        client, ef, eq_dirs, db_path, eq_installed.get(ef.id),
                        on_downloading=lambda f=ef: spinner.update(
                            f"  [dim]{f.name}[/dim]  Downloading..."
                        ),
                    )
                    ui.print_update_result(result)
                    if result["status"] == "updated":
                        updated += 1
                    elif result["status"] == "current":
                        current += 1
                    elif result["status"] not in ("skipped",):
                        errors += 1
            elif include_eq and not eq_files:
                pass  # manifest had no eq_files; nothing to do

    parts = []
    if updated:
        parts.append(f"[green]{updated} updated[/green]")
    if current:
        parts.append(f"[dim]{current} current[/dim]")
    if errors:
        parts.append(f"[red]{errors} error(s)[/red]")

    summary = ", ".join(parts) if parts else "nothing to do"
    ui.console.print(f"\nDone. {summary}.")


async def _update_eq_async(db_path: Path, eq_dirs: list[Path]) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)
    updated = current = errors = 0

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


@app.command()
def version():
    """Show proFetch version."""
    typer.echo(f"proFetch v{__version__}")


def main() -> None:
    if getattr(sys, "frozen", False):
        from profetch.setup import maybe_run_install_wizard
        maybe_run_install_wizard()
    app()


if __name__ == "__main__":
    main()
