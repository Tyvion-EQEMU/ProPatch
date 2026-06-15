from __future__ import annotations

import shutil
import sys
from pathlib import Path

from rich.prompt import Confirm, Prompt

from propatch import ui
from propatch.config import _DEFAULT_SETTINGS


_DEFAULT_INSTALL_DIR = r"C:\Games\ProPatch"


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
    """Re-run path configuration — called by the 'propatch setup' command."""
    from propatch import config as cfg

    settings = cfg.load_settings()

    # Load current values to use as prompt defaults
    try:
        current_mq = str(settings.PATHS.mq_rekkas)
    except Exception:
        current_mq = r"C:\Games\MQ-Profusion"

    current_eq: list[tuple[str, str]] = []
    try:
        raw_dirs = settings.get("PATHS.eq_dirs", default=[])
        if isinstance(raw_dirs, str):
            raw_dirs = [raw_dirs]
        dirs = [str(d) for d in raw_dirs if d]
        raw_names = settings.get("PATHS.eq_dir_names", default=[])
        if isinstance(raw_names, str):
            raw_names = [raw_names]
        names = list(raw_names)
        current_eq = [
            (dirs[i], names[i] if i < len(names) else "")
            for i in range(len(dirs))
        ]
    except Exception:
        pass

    existing_token = cfg.get_github_token(settings) or ""

    ui.console.print()
    ui.console.print("[bold cyan]  ProPatch — Reconfigure Paths[/bold cyan]")
    ui.console.print()
    try:
        mq_rekkas, eq_instances = _prompt_paths(current_mq, current_eq)
    except KeyboardInterrupt:
        ui.console.print("\n[yellow]Setup cancelled.[/yellow]")
        return

    _write_settings_local(data_dir, mq_rekkas, eq_instances, existing_token)
    ui.console.print()
    ui.console.print("[green]✓[/green] Settings updated.")
    ui.print_setup_reminder()


def _run_install_wizard() -> None:
    ui.console.print()
    ui.console.print("[bold cyan]  ProPatch — First-Time Setup[/bold cyan]")
    ui.console.print(
        "  [dim]ProPatch will copy itself to a permanent location and configure your paths.[/dim]"
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
    dest_exe = install_dir / "propatch.exe"
    src_exe = Path(sys.executable).resolve()
    if src_exe != dest_exe.resolve():
        try:
            shutil.copy2(src_exe, dest_exe)
        except OSError as exc:
            ui.print_error(f"Could not copy propatch.exe to {install_dir}: {exc}")
            sys.exit(1)

    # ── Done ──────────────────────────────────────────────────────────────────
    ui.console.print(f"[green]✓[/green] Installed to:  [bold]{dest_exe}[/bold]")
    ui.console.print(f"[green]✓[/green] Settings in:   [bold]{data_dir}[/bold]")
    ui.console.print()
    ui.console.print("  Run ProPatch from its new location:")
    ui.console.print(f"  [bold cyan]{dest_exe}[/bold cyan]")
    ui.print_setup_reminder()


def _prompt_paths(
    current_mq: str = r"C:\Games\MQ-Profusion",
    current_eq: list[tuple[str, str]] | None = None,
) -> tuple[str, list[tuple[str, str]]]:
    """Prompt for MQ and EQ paths, showing existing values as defaults."""
    if current_eq is None:
        current_eq = []

    # MQ path
    ui.console.print(
        "  [dim]MQ Install — root folder of the Rekkas MQ install (e.g. C:\\Games\\MQ-Profusion)[/dim]"
    )
    mq_rekkas = Prompt.ask("  MQ Install", default=current_mq, console=ui.console)

    # EQ directories
    ui.console.print()
    ui.console.print(
        "  [dim]EQ game directory — needed for EQ file updates (spells, dbstr, etc.)[/dim]"
    )

    if current_eq:
        ui.console.print("  [dim]Current EQ directories:[/dim]")
        for path, name in current_eq:
            label = f"  ({name})" if name else ""
            ui.console.print(f"  [dim]    {path}{label}[/dim]")
        ui.console.print()
        keep = Confirm.ask("  Keep existing EQ directories?", default=True, console=ui.console)
        if keep:
            return mq_rekkas, current_eq

    ui.console.print(
        "  [dim]Leave blank to skip; you can add this later with 'propatch setup'.[/dim]"
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
    data_dir: Path,
    mq_rekkas: str,
    eq_instances: list[tuple[str, str]],
    token: str = "",
) -> None:
    lines: list[str] = []

    if token.strip():
        lines.append(f'github_token = "{_toml_str(token.strip())}"')
        lines.append("")

    lines += ["[paths]", f'mq_rekkas = "{_toml_str(mq_rekkas)}"']

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
