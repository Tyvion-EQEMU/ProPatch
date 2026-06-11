from __future__ import annotations

import shutil
import sys
from pathlib import Path

from rich.prompt import Confirm, Prompt

from profetch import ui
from profetch.config import _DEFAULT_SETTINGS


_DEFAULT_INSTALL_DIR = r"C:\Games\proFetch"


def maybe_run_install_wizard() -> None:
    """Intercept the very first frozen run and guide the user to a permanent install location."""
    if not getattr(sys, "frozen", False):
        return

    data_dir = Path(sys.executable).parent
    if (data_dir / "settings.toml").exists():
        return  # already installed here — normal run

    try:
        _run_install_wizard()
    except KeyboardInterrupt:
        ui.console.print("\n[yellow]Setup cancelled.[/yellow]")
    sys.exit(0)


def run_setup(data_dir: Path) -> None:
    """Re-run path configuration — called by the 'profetch setup' command."""
    ui.console.print()
    ui.console.print("[bold cyan]  proFetch — Reconfigure Paths[/bold cyan]")
    ui.console.print()
    try:
        mq_rekkas, eq_instances = _prompt_paths()
    except KeyboardInterrupt:
        ui.console.print("\n[yellow]Setup cancelled.[/yellow]")
        return
    _write_settings_local(data_dir, mq_rekkas, eq_instances)
    ui.console.print()
    ui.console.print("[green]✓[/green] Settings updated.")
    ui.print_setup_reminder()


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

    ui.console.print()
    mq_rekkas, eq_instances = _prompt_paths()
    ui.console.print()

    # ── Create directories ────────────────────────────────────────────────────
    data_dir = install_dir
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        ui.print_error(f"Could not create install directory: {exc}")
        sys.exit(1)

    # ── Write settings ────────────────────────────────────────────────────────
    (data_dir / "settings.toml").write_text(_DEFAULT_SETTINGS, encoding="utf-8")
    _write_settings_local(data_dir, mq_rekkas, eq_instances)

    # ── Copy exe ──────────────────────────────────────────────────────────────
    dest_exe = install_dir / "profetch.exe"
    src_exe = Path(sys.executable).resolve()
    if src_exe != dest_exe.resolve():
        try:
            shutil.copy2(src_exe, dest_exe)
        except OSError as exc:
            ui.print_error(f"Could not copy profetch.exe to {install_dir}: {exc}")
            sys.exit(1)

    # ── Done ──────────────────────────────────────────────────────────────────
    ui.console.print(f"[green]✓[/green] Installed to:  [bold]{dest_exe}[/bold]")
    ui.console.print(f"[green]✓[/green] Settings in:   [bold]{data_dir}[/bold]")
    ui.console.print()
    ui.console.print("  Run proFetch from its new location:")
    ui.console.print(f"  [bold cyan]{dest_exe}[/bold cyan]")
    ui.print_setup_reminder()


def _prompt_paths() -> tuple[str, list[tuple[str, str]]]:
    """Ask for MQ Patch path and EQ game directories. Returns (mq_path, [(dir, name), ...])."""

    # MQ Patch
    ui.console.print(
        "  [dim]MQ Install — root folder of the Rekkas MQ install (e.g. C:\\Games\\MQ-Rekkas)[/dim]"
    )
    mq_rekkas = Prompt.ask(
        "  MQ Install", default=r"C:\Games\MQ-Rekkas", console=ui.console
    )

    # EQ directories
    ui.console.print()
    ui.console.print(
        "  [dim]EQ game directory — needed for EQ file updates (spells, dbstr, etc.)[/dim]"
    )
    ui.console.print(
        "  [dim]Leave blank to skip; you can add this later with 'profetch setup'.[/dim]"
    )
    eq_dir_raw = Prompt.ask("  EQ game directory", default="", console=ui.console)

    eq_instances: list[tuple[str, str]] = []
    eq_dir = eq_dir_raw.strip()

    if eq_dir:
        more = Confirm.ask(
            "  Do you have additional EQ instances?", default=False, console=ui.console
        )
        if more:
            name1 = Prompt.ask(
                "  Name for this instance", default="Main", console=ui.console
            )
            eq_instances.append((eq_dir, name1))

            while True:
                ui.console.print()
                next_dir = Prompt.ask(
                    "  Next EQ game directory", console=ui.console
                )
                next_name = Prompt.ask(
                    "  Name for this instance",
                    default=f"Instance {len(eq_instances) + 1}",
                    console=ui.console,
                )
                eq_instances.append((next_dir.strip(), next_name))
                again = Confirm.ask(
                    "  Do you have more EQ instances?", default=False, console=ui.console
                )
                if not again:
                    break
        else:
            eq_instances.append((eq_dir, ""))

    return mq_rekkas, eq_instances


def _toml_str(value: str) -> str:
    """Escape a string for use inside a TOML double-quoted value."""
    return value.replace("\\", "\\\\")


def _write_settings_local(
    data_dir: Path, mq_rekkas: str, eq_instances: list[tuple[str, str]]
) -> None:
    lines = ["[paths]", f'mq_rekkas = "{_toml_str(mq_rekkas)}"']

    if eq_instances:
        paths_toml = ", ".join(f'"{_toml_str(inst[0])}"' for inst in eq_instances)
        lines.append(f"eq_dirs = [{paths_toml}]")

        names = [inst[1] for inst in eq_instances]
        if any(names):
            names_toml = ", ".join(f'"{_toml_str(n)}"' for n in names)
            lines.append(f"eq_dir_names = [{names_toml}]")

    (data_dir / "settings.local.toml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
