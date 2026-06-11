from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Disable legacy Windows renderer so Rich writes directly to the file object,
# which we configure as UTF-8 in main.py.
console = Console(legacy_windows=False)

# Pre-rendered 24×12 Unicode half-block art of the ProFusion logo.
# Generated from assets/profusion_logo_32x32.png using Pillow at build time.
_LOGO_LINES = [
    '[#2c655b on #3b8877]▀[/][#225751 on #357c6f]▀[/][#20534f on #33776b]▀[/][#22534f on #3e8070]▀[/][#1f514e on #35746a]▀[/][#1f5352 on #276862]▀[/][#1a504f on #237268]▀[/][#174c49 on #1e6c62]▀[/][#1c4b47 on #225c55]▀[/][#1d4d4a on #0e5b5a]▀[/][#07464d on #71885b]▀[/][#878751 on #cc973b]▀[/][#848351 on #c9963c]▀[/][#0c3e47 on #6f7d57]▀[/][#1f4443 on #10474a]▀[/][#225b51 on #2a6f63]▀[/][#2f6c88 on #29527f]▀[/][#24387b on #243975]▀[/][#1a2f4d on #3a9b91]▀[/][#1e2e63 on #327e7d]▀[/][#3f73a2 on #234581]▀[/][#5e9274 on #629896]▀[/][#495643 on #6b5730]▀[/][#594135 on #3e241a]▀[/]',
    '[#47a68e on #55b89a]▀[/][#50ac8f on #4fa58f]▀[/][#4b9f86 on #337a78]▀[/][#387f77 on #286970]▀[/][#469083 on #4da290]▀[/][#37877a on #3d9788]▀[/][#297e74 on #379283]▀[/][#2d8375 on #2d9387]▀[/][#18786e on #6f936b]▀[/][#6a8b60 on #cc862a]▀[/][#d29335 on #543e29]▀[/][#524131 on #485360]▀[/][#514432 on #485260]▀[/][#d09537 on #503b28]▀[/][#677956 on #c88a30]▀[/][#1b6b67 on #688363]▀[/][#316383 on #31918d]▀[/][#36878b on #47b89b]▀[/][#3eb593 on #4699ae]▀[/][#56d2b9 on #316799]▀[/][#356a9b on #3467a6]▀[/][#416887 on #375771]▀[/][#5d4e2f on #3c2215]▀[/][#1f1a22 on #1d0f15]▀[/]',
    '[#3d857e on #1d6978]▀[/][#286971 on #64c1a6]▀[/][#317476 on #79dfb2]▀[/][#55a591 on #37968c]▀[/][#5ab496 on #288487]▀[/][#55b399 on #46bba7]▀[/][#2e9b90 on #659a76]▀[/][#6b9974 on #b8732b]▀[/][#c5802e on #593821]▀[/][#553a25 on #2d466b]▀[/][#30415d on #535a67]▀[/][#565555 on #585856]▀[/][#555455 on #585858]▀[/][#2e425e on #565b64]▀[/][#563b27 on #2c4569]▀[/][#c17e2e on #593922]▀[/][#68976e on #b6772d]▀[/][#379b96 on #75b084]▀[/][#37679d on #348196]▀[/][#5baab9 on #315e89]▀[/][#38649b on #173e5c]▀[/][#195b76 on #0f466a]▀[/][#454d50 on #636969]▀[/][#462113 on #88643b]▀[/]',
    '[#5b7d6b on #865625]▀[/][#7da880 on #b58b3c]▀[/][#7ba77b on #816539]▀[/][#5d7e65 on #382e34]▀[/][#57816b on #4d403d]▀[/][#70956c on #4d3f3b]▀[/][#a26925 on #22273e]▀[/][#553422 on #203d66]▀[/][#213a62 on #2f4c71]▀[/][#485167 on #26436b]▀[/][#3c4359 on #3e5c7a]▀[/][#554c45 on #35516e]▀[/][#574e47 on #314c6a]▀[/][#3e455a on #325377]▀[/][#465267 on #28476c]▀[/][#1f3960 on #365476]▀[/][#513120 on #2a4365]▀[/][#a2712b on #34313c]▀[/][#84b87c on #4a3e3d]▀[/][#6b8967 on #49413f]▀[/][#6e5e39 on #4b4245]▀[/][#745e3b on #51433c]▀[/][#735b40 on #967c3e]▀[/][#927347 on #906a33]▀[/]',
    '[#4b2d15 on #3f2c26]▀[/][#b3862f on #a78234]▀[/][#c19f48 on #3c291d]▀[/][#737a69 on #b69240]▀[/][#6a5f42 on #a6863c]▀[/][#c0a449 on #50361b]▀[/][#536e7b on #b78e3c]▀[/][#6a7168 on #8c713d]▀[/][#bea258 on #785a2f]▀[/][#526060 on #ab944f]▀[/][#be9f46 on #5a543e]▀[/][#988142 on #4c4338]▀[/][#757152 on #7a774f]▀[/][#767150 on #77714a]▀[/][#94885d on #ca9832]▀[/][#a68b48 on #312d33]▀[/][#967d43 on #796638]▀[/][#596561 on #ad964b]▀[/][#b09d61 on #86642d]▀[/][#696558 on #8b7143]▀[/][#908455 on #d6a938]▀[/][#414853 on #746f50]▀[/][#a07f39 on #88703a]▀[/][#71491b on #573b22]▀[/]',
    '[#29293b on #574433]▀[/][#b99137 on #b59236]▀[/][#1f2a4d on #585c4f]▀[/][#9a6718 on #b97c19]▀[/][#c29532 on #8c5a1b]▀[/][#87774d on #b48a36]▀[/][#a66e16 on #745a30]▀[/][#766338 on #6e5c3f]▀[/][#333e50 on #3f5060]▀[/][#c18f2d on #b37a1f]▀[/][#a49459 on #8c6327]▀[/][#7e724c on #73582c]▀[/][#726f51 on #665f4a]▀[/][#6e6b49 on #726648]▀[/][#af7b21 on #483d3a]▀[/][#707769 on #a5813c]▀[/][#5e5f4c on #8f753e]▀[/][#d49d27 on #b77617]▀[/][#2f3a52 on #334a65]▀[/][#887141 on #8b7342]▀[/][#d19121 on #a56818]▀[/][#9a7e40 on #a3762c]▀[/][#967636 on #aa7b2a]▀[/][#433938 on #583f2a]▀[/]',
    '[#4f3b28 on #2a2534]▀[/][#cda83f on #9d681f]▀[/][#c9a446 on #432616]▀[/][#653a11 on #000b33]▀[/][#5a3e27 on #795933]▀[/][#674828 on #514032]▀[/][#886633 on #805b2a]▀[/][#6a593f on #7f5f32]▀[/][#79775d on #9d7736]▀[/][#98641c on #563d2a]▀[/][#46484c on #76674c]▀[/][#3b4650 on #123b67]▀[/][#7d6f4b on #a37934]▀[/][#836e43 on #7f6335]▀[/][#4e4e4f on #695535]▀[/][#6a593c on #9e7839]▀[/][#af7520 on #8a571c]▀[/][#8b5a1f on #55402e]▀[/][#6c6b5a on #a87c35]▀[/][#95773b on #735631]▀[/][#7a4f1e on #5f4731]▀[/][#865f2a on #5f432d]▀[/][#d8972b on #d28a1f]▀[/][#31252c on #382c30]▀[/]',
    '[#4b3126 on #402a20]▀[/][#a07028 on #9d6827]▀[/][#232c42 on #273247]▀[/][#1a2d57 on #16274b]▀[/][#322b2f on #213350]▀[/][#232a42 on #575f5f]▀[/][#363036 on #45515b]▀[/][#44362b on #495158]▀[/][#1c2138 on #535b60]▀[/][#243048 on #5a5e5d]▀[/][#333842 on #5b6160]▀[/][#134076 on #5f6a6d]▀[/][#252d3f on #55666e]▀[/][#223049 on #575d5e]▀[/][#23314b on #425161]▀[/][#372f31 on #49555f]▀[/][#2d2d36 on #515b61]▀[/][#273044 on #5f6461]▀[/][#292431 on #515b63]▀[/][#202841 on #2b394f]▀[/][#795c36 on #7e5524]▀[/][#3a2f35 on #292a3a]▀[/][#ad691c on #8d531d]▀[/][#5a3820 on #57351d]▀[/]',
    '[#512c1a on #665832]▀[/][#9d6927 on #ac671c]▀[/][#332830 on #515a44]▀[/][#302433 on #5a6442]▀[/][#3e2b33 on #637a4b]▀[/][#483433 on #596a41]▀[/][#423e41 on #6d3918]▀[/][#2a344a on #5f3d2c]▀[/][#2f3a51 on #1d2c4e]▀[/][#353d54 on #25345b]▀[/][#3b4559 on #2e3e61]▀[/][#36485e on #444a53]▀[/][#2d4360 on #454b57]▀[/][#39455b on #303d62]▀[/][#2c3b59 on #2b375d]▀[/][#2b3a58 on #233153]▀[/][#2a3951 on #633c28]▀[/][#484141 on #70411f]▀[/][#493a38 on #534b44]▀[/][#41373a on #5a301d]▀[/][#44312b on #4a2616]▀[/][#2f2a35 on #332a2f]▀[/][#805221 on #996723]▀[/][#643b1a on #6e411a]▀[/]',
    '[#6c683d on #507b5b]▀[/][#605d3b on #3f8d75]▀[/][#4eb88c on #459876]▀[/][#44a57d on #4fb180]▀[/][#43a77b on #479f79]▀[/][#46b980 on #45926f]▀[/][#55784a on #41a477]▀[/][#823914 on #4b5d41]▀[/][#624432 on #7f3b15]▀[/][#192c51 on #614737]▀[/][#343950 on #1c2b4a]▀[/][#6b513a on #523a31]▀[/][#694f3b on #533f36]▀[/][#333a56 on #273653]▀[/][#1f2f54 on #674932]▀[/][#6b452f on #7b340e]▀[/][#823c0f on #4a6241]▀[/][#4e7763 on #368a8d]▀[/][#365b79 on #3b3b4f]▀[/][#391009 on #3e1407]▀[/][#17080e on #251214]▀[/][#19212b on #1f1f1d]▀[/][#4e341d on #0e222e]▀[/][#774a25 on #3d3024]▀[/]',
    '[#459f7a on #2e6858]▀[/][#4a9f76 on #40946e]▀[/][#439673 on #377e63]▀[/][#439975 on #316c5b]▀[/][#439a74 on #2c6256]▀[/][#3b8b69 on #255a4e]▀[/][#367e62 on #285f52]▀[/][#338068 on #2b6355]▀[/][#494f37 on #2c745e]▀[/][#813f16 on #423d2b]▀[/][#5c4637 on #793a13]▀[/][#192443 on #58443a]▀[/][#1d2846 on #584437]▀[/][#644834 on #7a390f]▀[/][#7b3910 on #434031]▀[/][#45543c on #307764]▀[/][#3b9173 on #326c61]▀[/][#2d5a78 on #204268]▀[/][#3c313d on #3c2d2e]▀[/][#3b150a on #3c130e]▀[/][#261215 on #1d161d]▀[/][#0a1b27 on #262924]▀[/][#142732 on #443c2e]▀[/][#141a1e on #121a22]▀[/]',
    '[#2a5c56 on #2b5c51]▀[/][#2b5a54 on #29594f]▀[/][#316c5e on #2b5751]▀[/][#2c6659 on #285b52]▀[/][#255851 on #265650]▀[/][#245451 on #25544d]▀[/][#255951 on #23524b]▀[/][#276054 on #225049]▀[/][#2e6e5b on #214d46]▀[/][#276456 on #24574d]▀[/][#403624 on #1f4f46]▀[/][#7d4219 on #4c321a]▀[/][#7c4016 on #4b311a]▀[/][#403828 on #1f514b]▀[/][#276159 on #24564e]▀[/][#27574f on #215148]▀[/][#214c55 on #1e4752]▀[/][#19365c on #1b2a50]▀[/][#3c2b28 on #383b31]▀[/][#39201e on #294d45]▀[/][#211e24 on #282d2d]▀[/][#4f4127 on #3a372a]▀[/][#55452b on #343429]▀[/][#1e2126 on #2c2a2e]▀[/]',
]


def print_logo() -> None:
    for line in _LOGO_LINES:
        console.print(line, end="\n")


def print_header(version: str) -> None:
    print_logo()
    console.print(
        f"\n[bold cyan]ProFetch v{version}[/bold cyan] — EQProfusion Component Manager\n"
    )


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
