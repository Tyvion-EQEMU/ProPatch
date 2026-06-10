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
from profetch.components import COMPONENTS

# Short aliases the user can type on the CLI
_ALIASES: dict[str, str] = {
    "rekkas":   "rekkas_mq",
    "rekkas_mq": "rekkas_mq",
    "mq2rwarp": "mq2rwarp",
    "rwarp":    "mq2rwarp",
    "rgmercs":  "rgmercs",
    "mercs":    "rgmercs",
    "e9loot":   "e9loot",
    "proloot":  "e9loot",
    "loot":     "e9loot",
}

app = typer.Typer(
    name="profetch",
    help="proFetch — EQProfusion Component Manager",
    no_args_is_help=True,
)


def _enabled_components(settings) -> list[str]:
    result = []
    for cid in COMPONENTS:
        try:
            enabled = settings.get(f"COMPONENTS.{cid}", default=True)
        except Exception:
            enabled = True
        if enabled:
            result.append(cid)
    return result


@app.command()
def status():
    """Show current installed versions vs. remote."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()
    enabled = _enabled_components(settings)

    asyncio.run(_status_async(db_path, enabled))


async def _status_async(db_path, enabled: list[str]) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)
    statuses = await updater.get_all_statuses(db_path, enabled)
    table = ui.build_status_table(statuses)
    ui.console.print(table)


@app.command()
def update(
    component: str = typer.Argument(
        None,
        help="Component to update: rekkas, mq2rwarp, rgmercs, e9loot. Omit to update all.",
    ),
):
    """Download and install updates for all (or one) component."""
    settings = config.load_settings()
    config.ensure_data_dir()
    db_path = config.get_db_path()

    try:
        mq_rekkas = Path(settings.PATHS.mq_rekkas)
    except Exception:
        mq_rekkas = Path(r"C:\Games\MQ-Rekka")

    if component is not None:
        cid = _ALIASES.get(component.lower())
        if not cid:
            valid = ", ".join(sorted(set(_ALIASES.values())))
            ui.print_error(f"Unknown component '{component}'. Valid IDs: {valid}")
            raise typer.Exit(1)
        component_ids = [cid]
    else:
        component_ids = _enabled_components(settings)

    asyncio.run(_update_async(db_path, mq_rekkas, component_ids))


async def _update_async(db_path: Path, mq_rekkas: Path, component_ids: list[str]) -> None:
    await db.init_db(db_path)
    ui.print_header(__version__)

    # Generous read timeout — Rekkas binary zip can be large
    timeout = httpx.Timeout(connect=30.0, read=None, write=None, pool=30.0)

    updated = current = errors = 0
    installed = await db.get_all_versions(db_path)

    async with httpx.AsyncClient(timeout=timeout) as client:
        with ui.console.status("") as spinner:
            for cid in component_ids:
                if cid not in COMPONENTS:
                    continue
                comp = COMPONENTS[cid]

                spinner.update(f"  [dim]{comp.name}[/dim]  Checking...")

                result = await updater.update_one(
                    client,
                    comp,
                    mq_rekkas,
                    db_path,
                    installed.get(cid),
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
    app()


if __name__ == "__main__":
    main()
