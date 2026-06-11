from __future__ import annotations

import shutil
import sys
from pathlib import Path

from rich.prompt import Prompt

from profetch import ui
from profetch.config import _DEFAULT_SETTINGS


_DEFAULT_INSTALL_DIR = r"C:\proFetch"


def maybe_run_install_wizard() -> None:
    """Intercept the very first frozen run and guide the user to a permanent install location."""
    if not getattr(sys, "frozen", False):
        return

    data_dir = Path(sys.executable).parent / "proFetch"
    if (data_dir / "settings.toml").exists():
        return  # already installed here — normal run

    try:
        _run_install_wizard()
    except KeyboardInterrupt:
        ui.console.print("\n[yellow]Setup cancelled.[/yellow]")
    sys.exit(0)


def _run_install_wizard() -> None:
    ui.console.print()
    ui.console.print("[bold cyan]  proFetch — First-Time Setup[/bold cyan]")
    ui.console.print(
        "  [dim]proFetch will copy itself to a permanent location and configure your paths.[/dim]"
    )
    ui.console.print()

    # ── Install directory ─────────────────────────────────────────────────────
    install_dir = Path(
        Prompt.ask("  Install directory", default=_DEFAULT_INSTALL_DIR, console=ui.console)
    )

    # ── MQ-Rekka path ─────────────────────────────────────────────────────────
    ui.console.print()
    ui.console.print(
        "  [dim]MQ-Rekka path — root folder of the Rekkas MQ stack (e.g. C:\\Games\\MQ-Rekka)[/dim]"
    )
    mq_rekkas = Prompt.ask(
        "  MQ-Rekka path", default=r"C:\Games\MQ-Rekka", console=ui.console
    )

    # ── EQ game directory (optional) ──────────────────────────────────────────
    ui.console.print()
    ui.console.print(
        "  [dim]EQ game directory — needed for EQ file updates (spells, dbstr, etc.)[/dim]"
    )
    ui.console.print("  [dim]Leave blank to skip; you can add this later in settings.local.toml.[/dim]")
    eq_dir_raw = Prompt.ask("  EQ game directory", default="", console=ui.console)

    ui.console.print()

    # ── Create directories ────────────────────────────────────────────────────
    data_dir = install_dir / "proFetch"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        ui.print_error(f"Could not create install directory: {exc}")
        sys.exit(1)

    # ── Write settings.toml (shipped defaults) ────────────────────────────────
    (data_dir / "settings.toml").write_text(_DEFAULT_SETTINGS, encoding="utf-8")

    # ── Write settings.local.toml (user's paths) ──────────────────────────────
    local_lines = ["[paths]", f'mq_rekkas = "{mq_rekkas}"']
    eq_dir = eq_dir_raw.strip()
    if eq_dir:
        local_lines.append(f'eq_dirs = ["{eq_dir}"]')
    (data_dir / "settings.local.toml").write_text(
        "\n".join(local_lines) + "\n", encoding="utf-8"
    )

    # ── Copy exe to install directory ─────────────────────────────────────────
    dest_exe = install_dir / "profetch.exe"
    try:
        shutil.copy2(sys.executable, dest_exe)
    except OSError as exc:
        ui.print_error(f"Could not copy profetch.exe to {install_dir}: {exc}")
        sys.exit(1)

    # ── Done ──────────────────────────────────────────────────────────────────
    ui.console.print(f"[green]✓[/green] Installed to:  [bold]{dest_exe}[/bold]")
    ui.console.print(f"[green]✓[/green] Settings in:   [bold]{data_dir}[/bold]")
    ui.console.print()
    ui.console.print("  Run proFetch from its new location:")
    ui.console.print(f"  [bold cyan]{dest_exe}[/bold cyan]")
    ui.console.print()
    ui.console.print(
        "  [dim]To customize settings, edit:[/dim] "
        f"[dim]{data_dir / 'settings.local.toml'}[/dim]"
    )
    ui.console.print()
