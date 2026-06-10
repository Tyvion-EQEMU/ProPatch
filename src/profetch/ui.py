from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Disable legacy Windows renderer so Rich writes directly to the file object,
# which we configure as UTF-8 in main.py.
console = Console(legacy_windows=False)


def print_header(version: str) -> None:
    console.print(
        f"\n[bold cyan]proFetch v{version}[/bold cyan] — EQProfusion Component Manager\n"
    )


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def _short(version: str | None) -> str:
    if version is None:
        return "Not installed"
    # Shorten full commit SHAs to 7 chars
    if len(version) == 40 and all(c in "0123456789abcdef" for c in version.lower()):
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


def build_status_table(statuses: list[dict]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white", no_wrap=True, min_width=18)
    table.add_column("Installed", style="dim", min_width=12)
    table.add_column("Remote", style="dim", min_width=12)
    table.add_column("Status", no_wrap=True)

    for s in statuses:
        code = s.get("status", "unknown")
        installed_display = _short(s.get("installed"))
        remote_display = _short(s.get("remote"))

        if code == "current":
            status_text = Text("✓ Current", style="green")
        elif code == "update_available":
            status_text = Text("↑ Update Available", style="yellow")
        elif code == "not_installed":
            status_text = Text("✗ Not Installed", style="red")
        elif code == "error":
            status_text = Text(f"! Error: {s.get('error', '')[:40]}", style="red")
        else:
            status_text = Text("? Unknown", style="dim")

        table.add_row(s["name"], installed_display, remote_display, status_text)

    return table
