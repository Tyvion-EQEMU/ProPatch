from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Disable legacy Windows renderer so Rich writes directly to the file object,
# which we configure as UTF-8 in main.py.
console = Console(legacy_windows=False)

# Pre-rendered 8×4 Unicode half-block art of the ProFusion logo.
# Generated from assets/profusion_logo_32x32.png using Pillow at build time.
_LOGO_LINES = [
    '[#387f6f on #47998d]▀[/][#307068 on #43a192]▀[/][#1d6d66 on #638461]▀[/][#6d7247 on #5a4f4a]▀[/][#6d6d42 on #584d49]▀[/][#246677 on #668566]▀[/][#387a93 on #39839d]▀[/][#4a514d on #404148]▀[/]',
    '[#7e784b on #7c5f31]▀[/][#697053 on #9d722c]▀[/][#5c5650 on #856e3f]▀[/][#525b60 on #88723f]▀[/][#505a5e on #7f6f43]▀[/][#615a4d on #8b723e]▀[/][#67664e on #98783c]▀[/][#766240 on #896931]▀[/]',
    '[#695131 on #5f462e]▀[/][#4c3b32 on #3d4a49]▀[/][#665339 on #433c43]▀[/][#535048 on #38475e]▀[/][#595448 on #35455e]▀[/][#695437 on #413f4a]▀[/][#685438 on #443938]▀[/][#7f5527 on #613e23]▀[/]',
    '[#528e67 on #2f6e5e]▀[/][#47a174 on #285f56]▀[/][#526042 on #246155]▀[/][#493739 on #4c442e]▀[/][#4d3b39 on #4c462e]▀[/][#545e4c on #23535a]▀[/][#31262a on #31282b]▀[/][#2b241e on #2e2e27]▀[/]',
]

# Text overlaid on the right side of the logo, row by row (None = no text)
_HEADER_SUFFIX = [
    None,
    "  [bold cyan]ProFetch v{version}[/bold cyan]",
    "  [dim]EQ Profusion Component Manager[/dim]",
    None,
]


def print_header(version: str) -> None:
    console.print()
    for logo_line, suffix_template in zip(_LOGO_LINES, _HEADER_SUFFIX):
        suffix = suffix_template.format(version=version) if suffix_template else ""
        console.print(logo_line + suffix)
    console.print()


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def _short(version: str | None) -> str:
    if version is None:
        return "Not installed"
    # Shorten commit SHAs (40 chars) and SHA-256 hashes (64 chars) to 7 chars
    if len(version) in (40, 64) and all(c in "0123456789abcdef" for c in version.lower()):
        return version[:7]
    return version


def print_update_result(result: dict) -> None:
    name = result["name"]
    status = result.get("status")

    if result.get("kind") == "eq_file":
        _print_eq_result(result)
        return

    old = _short(result.get("old_version"))
    new = _short(result.get("new_version"))
    written = result.get("written", 0)
    skipped = result.get("skipped", 0)
    files_note = f"({written} files" + (f", {skipped} skipped)" if skipped else ")")

    if status == "current":
        console.print(f"  [green]✓[/green] [white]{name}[/white]  [dim]up to date ({new})[/dim]")
    elif status == "adopted":
        console.print(
            f"  [green]✓[/green] [white]{name}[/white]  "
            f"[dim]adopted (existing files registered as[/dim] [cyan]{new}[/cyan][dim])[/dim]"
        )
    elif status == "updated":
        if old == "Not installed":
            console.print(
                f"  [green]✓[/green] [white]{name}[/white]  "
                f"[dim]installed[/dim]  [cyan]{new}[/cyan]  [dim]{files_note}[/dim]"
            )
        else:
            console.print(
                f"  [green]✓[/green] [white]{name}[/white]  "
                f"[dim]{old}[/dim] → [cyan]{new}[/cyan]  [dim]{files_note}[/dim]"
            )
    elif status == "error":
        console.print(
            f"  [bold red]✗[/bold red] [white]{name}[/white]  "
            f"[red]{result.get('error', 'unknown error')}[/red]"
        )


def _print_eq_result(result: dict) -> None:
    name = result["name"]
    status = result.get("status")
    written = result.get("written", 0)
    dirs = result.get("dirs", 0)

    if status == "current":
        console.print(f"  [green]✓[/green] [white]{name}[/white]  [dim]up to date[/dim]")
    elif status == "updated":
        loc = f"{dirs} dir{'s' if dirs != 1 else ''}" if dirs else f"{written} files"
        console.print(
            f"  [green]✓[/green] [white]{name}[/white]  "
            f"[dim]installed →[/dim] [cyan]{loc}[/cyan]"
        )
    elif status == "skipped":
        console.print(
            f"  [dim]– {name}  {result.get('error', 'skipped')}[/dim]"
        )
    elif status == "error":
        console.print(
            f"  [bold red]✗[/bold red] [white]{name}[/white]  "
            f"[red]{result.get('error', 'unknown error')}[/red]"
        )


def _status_row(table: Table, s: dict) -> None:
    code = s.get("status", "unknown")
    installed_display = _short(s.get("installed"))
    remote_raw = s.get("remote")
    remote_display = _short(remote_raw) if remote_raw is not None else Text("—", style="dim")

    if code == "current":
        status_text = Text("✓ Current", style="green")
    elif code == "update_available":
        status_text = Text("↑ Update Available", style="yellow")
    elif code == "not_installed":
        status_text = Text("✗ Not Installed", style="red")
        installed_display = Text("—", style="dim")
    elif code == "untracked":
        status_text = Text("? Untracked", style="yellow")
        installed_display = Text("on disk", style="dim")
    elif code == "error":
        status_text = Text(f"! Error: {s.get('error', '')[:40]}", style="red")
    else:
        status_text = Text("? Unknown", style="dim")

    table.add_row(s["name"], installed_display, remote_display, status_text)


def build_status_table(mq_statuses: list[dict], eq_statuses: list[dict]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white", no_wrap=True, min_width=20)
    table.add_column("Installed", style="dim", min_width=8)
    table.add_column("Remote", style="dim", min_width=8)
    table.add_column("Status", no_wrap=True)

    for s in mq_statuses:
        _status_row(table, s)

    if eq_statuses:
        table.add_section()
        for s in eq_statuses:
            _status_row(table, s)

    return table


def print_preflight(items: list[dict]) -> None:
    n = len(items)
    console.print(f"  [bold]{n} item{'s' if n != 1 else ''} to install/update:[/bold]\n")
    for s in items:
        name = s["name"]
        if s["status"] == "not_installed":
            console.print(f"    [red]✗[/red] {name}  [dim]not installed[/dim]")
        elif s["status"] == "untracked":
            rem = _short(s.get("remote"))
            console.print(f"    [yellow]?[/yellow] {name}  [dim]on disk, untracked → will sync to[/dim] [cyan]{rem}[/cyan]")
        else:
            inst = _short(s.get("installed"))
            rem = _short(s.get("remote"))
            console.print(f"    [yellow]↑[/yellow] {name}  [dim]{inst} →[/dim] [cyan]{rem}[/cyan]")
    console.print()


def print_setup_reminder() -> None:
    console.print()
    console.print(
        "  [dim]Run [bold white]profetch setup[/bold white]"
        " at any time to reconfigure paths.[/dim]"
    )
    console.print()


def print_config_section(config_info: dict) -> None:
    console.print("[bold]  Configured Paths[/bold]")
    console.print()

    t = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    t.add_column("Key", style="dim", no_wrap=True, min_width=12)
    t.add_column("Value", no_wrap=True)
    t.add_column("Status", no_wrap=True)

    # MQ Install path
    mq = config_info["mq_rekkas"]
    if mq["path"] is None:
        t.add_row("MQ Install", Text("Not configured", style="red"), Text("✗", style="red"))
    else:
        icon = Text("✓", style="green") if mq["exists"] else Text("✗ Path not found", style="red")
        t.add_row("MQ Install", str(mq["path"]), icon)

    # EQ dirs
    eq_dirs = config_info["eq_dirs"]
    if not eq_dirs:
        t.add_row("EQ Dirs", Text("Not configured", style="red"), Text("✗", style="red"))
    else:
        for i, d in enumerate(eq_dirs):
            name = d.get("name", "")
            label = "EQ Dirs" if i == 0 else ""
            display = f"{d['path']}  [dim]({name})[/dim]" if name else str(d["path"])
            icon = Text("✓", style="green") if d["exists"] else Text("✗ Not found", style="red")
            t.add_row(label, display, icon)

    # Data dir
    dd = config_info["data_dir"]
    icon = Text("✓", style="green") if dd["exists"] else Text("✗ Not found", style="red")
    t.add_row("Data Dir", str(dd["path"]), icon)

    console.print(t)
    console.print()
