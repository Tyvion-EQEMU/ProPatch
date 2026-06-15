from __future__ import annotations
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from propatch import config
from propatch.gui.widgets.header import build_header, _WARM_GOLD, _STRIP_BG, _MARGIN
from propatch.gui.widgets.tooltip import Tooltip

logger = logging.getLogger("propatch")

_MQ_COMPONENTS = {"rekkas_mq", "mq2rwarp", "rgmercs", "proloot"}

_NARRATIVE = (
    "Welcome to ProPatch — the EQ Profusion component manager.\n\n"
    "This setup will walk you through the essentials: where ProPatch lives on your machine, "
    "whether you want MacroQuest managed for you, and where your EverQuest installation(s) are. "
    "You can always revisit these settings later from the main panel.\n\n"
    "MacroQuest is not required, nor is it built-in to this patcher. "
    "If you would like to not use MQ or not have it installed, simply toggle it off in the section below.\n\n"
    "Take a moment to review each option below, then hit Finish Setup when you're ready."
)

_LABEL_W = 180
_ENTRY_W = 260
_BTN_W   = 90
_PAD_X   = 25


class SetupWizard(ctk.CTkFrame):
    """First-run setup wizard — same look as the main panel."""

    def __init__(self, parent_app, settings: dict, **kwargs):
        super().__init__(parent_app, fg_color="transparent", **kwargs)
        self._app          = parent_app
        self._gui_settings = settings
        self._eq_rows: list[dict] = []
        self._mq_path_frame: ctk.CTkFrame | None = None
        self._banner_h = 0

        # Load current path/token settings from settings.local.toml so that
        # GUI and CLI always share the same source of truth.
        self._current_mq_path   = r"C:\Games\MQ-Profusion"
        self._current_eq_instances: list[dict] = []
        self._current_token     = ""
        try:
            _s = config.load_settings()
            try:
                self._current_mq_path = str(_s.PATHS.mq_rekkas)
            except Exception:
                pass
            try:
                _dirs = _s.get("PATHS.eq_dirs", default=[])
                if isinstance(_dirs, str):
                    _dirs = [_dirs]
                _dirs = [str(d) for d in _dirs if d]
                _names = _s.get("PATHS.eq_dir_names", default=[])
                if isinstance(_names, str):
                    _names = [_names]
                _names = list(_names)
                self._current_eq_instances = [
                    {"path": _dirs[i], "name": _names[i] if i < len(_names) else ""}
                    for i in range(len(_dirs))
                ]
            except Exception:
                pass
            self._current_token = config.get_github_token(_s) or ""
        except Exception:
            pass

        self._build()
        self._fit_window()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _fit_window(self) -> None:
        STRIP_H       = 60
        NARRATIVE_H   = 110
        QUESTIONS_MIN = 320
        ACTION_H      = 56
        img_h = self._banner_h if self._banner_h else 80
        total = int((img_h + STRIP_H + NARRATIVE_H + QUESTIONS_MIN + ACTION_H) * 1.39) - 96
        self._app.geometry(f"680x{total}")
        self._app.minsize(680, 500)

    def _build(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header, self._banner_h = build_header(self)
        header.grid(row=0, column=0, sticky="ew")

        strip = header.grid_slaves(row=1, column=0)[0]
        tk.Label(
            strip,
            text="Setup Wizard",
            font=("Consolas", 14, "bold"),
            fg=_WARM_GOLD,
            bg=_STRIP_BG,
            padx=0,
            pady=0,
        ).place(relx=1.0, rely=0.5, anchor="e", x=-_MARGIN)

        self._build_narrative().grid(row=1, column=0, sticky="ew", padx=_PAD_X, pady=(12, 0))
        self._build_questions().grid(row=2, column=0, sticky="nsew", padx=_PAD_X, pady=(8, 0))
        self._build_action_bar().grid(row=3, column=0, sticky="ew", padx=_PAD_X, pady=8)

    def _build_narrative(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, corner_radius=6, fg_color=("#12122a", "#0a0a18"))
        ctk.CTkLabel(
            frame,
            text=_NARRATIVE,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("#aaaacc", "#8888aa"),
            justify="left",
            wraplength=610,
            anchor="w",
        ).pack(padx=16, pady=12, fill="x")
        return frame

    def _build_questions(self) -> ctk.CTkScrollableFrame:
        scroll = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray14"), corner_radius=0)
        scroll.grid_columnconfigure(0, weight=1)

        self._build_section_header(scroll, "ProPatch")
        self._build_propatch_path(scroll)
        self._build_github_token(scroll)

        self._build_section_header(scroll, "MacroQuest")
        self._build_mq_section(scroll)

        self._build_section_header(scroll, "EverQuest")
        self._build_eq_section(scroll)

        self._scroll_frame = scroll
        return scroll

    # ── Section header ────────────────────────────────────────────────────────

    def _build_section_header(self, parent, title: str) -> None:
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(14, 4))
        wrapper.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            wrapper,
            text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#4a9eff", "#4477aa"),
            fg_color="transparent",
            anchor="w",
        ).grid(row=0, column=0, padx=(4, 8))
        ctk.CTkFrame(wrapper, height=1, fg_color=("#4a9eff", "#1e2d42")).grid(
            row=0, column=1, sticky="ew", padx=(0, 4)
        )

    # ── ProPatch install path ─────────────────────────────────────────────────

    def _build_propatch_path(self, parent) -> None:
        row, lbl = self._make_path_row(
            parent,
            label="ProPatch Install Path",
            default=self._gui_settings.get("propatch_install_path", r"C:\Games\ProPatch"),
            setting_key="propatch_install_path",
        )
        row.pack(fill="x", pady=3)
        Tooltip(lbl, "This patcher will be copied here, plus all settings and logs will be kept here.")

        shortcut_row = ctk.CTkFrame(parent, fg_color="transparent")
        shortcut_row.pack(fill="x", pady=3)
        shortcut_lbl = ctk.CTkLabel(
            shortcut_row,
            text="Create Desktop Shortcut",
            font=ctk.CTkFont(size=12),
            width=_LABEL_W + _ENTRY_W,
            anchor="w",
        )
        shortcut_lbl.pack(side="left", padx=(8, 0))
        self._shortcut_var = ctk.BooleanVar(value=True)
        shortcut_switch = ctk.CTkSwitch(
            shortcut_row,
            text="",
            variable=self._shortcut_var,
            width=48,
        )
        shortcut_switch.pack(side="left", padx=(12, 0))
        Tooltip(shortcut_lbl, "Place a ProPatch shortcut on your Windows Desktop for quick access.")

    # ── GitHub token ─────────────────────────────────────────────────────────

    def _build_github_token(self, parent) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        lbl = ctk.CTkLabel(row, text="GitHub Token (optional)",
                           width=_LABEL_W, anchor="w", font=ctk.CTkFont(size=12))
        lbl.pack(side="left", padx=(8, 0))

        # Pre-fill from existing settings if present
        self._token_var = tk.StringVar(value=self._current_token)
        ctk.CTkEntry(row, textvariable=self._token_var, width=_ENTRY_W,
                     placeholder_text="ghp_…  (raises limit to 5000 req/hr)",
                     show="").pack(side="left", padx=(6, 4))
        Tooltip(lbl,
                "Personal Access Token from github.com/settings/tokens — "
                "no scopes needed for public repos. Raises the GitHub API "
                "rate limit from 60 to 5000 requests per hour.")

    # ── MacroQuest ────────────────────────────────────────────────────────────

    def _build_mq_section(self, parent) -> None:
        toggle_row = ctk.CTkFrame(parent, fg_color="transparent")
        toggle_row.pack(fill="x", pady=3)

        mq_lbl = ctk.CTkLabel(
            toggle_row,
            text="Install and update MacroQuest",
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=_LABEL_W + _ENTRY_W,
        )
        mq_lbl.pack(side="left", padx=(8, 0))
        Tooltip(mq_lbl, "If you wish to ignore and leave off all MQ components, toggle this OFF")

        self._mq_var = ctk.BooleanVar(value=self._gui_settings.get("install_mq", True))
        mq_switch = ctk.CTkSwitch(
            toggle_row,
            text="",
            variable=self._mq_var,
            width=48,
            command=self._on_mq_toggle,
        )
        mq_switch.pack(side="left", padx=(12, 0))

        self._mq_path_frame, _ = self._make_path_row(
            parent,
            label="MQ Install Path",
            default=self._current_mq_path,
            setting_key="install_path",
        )
        if self._mq_var.get():
            self._mq_path_frame.pack(fill="x", pady=3)

    def _on_mq_toggle(self) -> None:
        if self._mq_var.get():
            self._mq_path_frame.pack(fill="x", pady=3)
        else:
            self._mq_path_frame.pack_forget()

    # ── EverQuest instances ───────────────────────────────────────────────────

    def _build_eq_section(self, parent) -> None:
        self._eq_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._eq_container.pack(fill="x")

        existing = self._current_eq_instances

        if existing:
            for inst in existing:
                self._add_eq_row(
                    show_name=len(existing) > 1,
                    path=inst.get("path", ""),
                    name=inst.get("name", ""),
                )
        else:
            self._add_eq_row(show_name=False)

        self._add_eq_btn = ctk.CTkButton(
            parent,
            text="＋ Add EQ Instance",
            fg_color="transparent",
            border_width=1,
            border_color=("#aaaaaa", "#555555"),
            text_color=("#555555", "#aaaaaa"),
            hover_color=("#eeeeee", "#2a2a2a"),
            height=28,
            command=self._on_add_eq_instance,
        )
        self._add_eq_btn.pack(fill="x", padx=4, pady=(6, 4))

    def _add_eq_row(self, show_name: bool = True, path: str = "", name: str = "") -> None:
        row_frame = ctk.CTkFrame(self._eq_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)

        path_var = tk.StringVar(value=path)
        name_var = tk.StringVar(value=name)

        path_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        path_row.pack(fill="x")
        eq_path_lbl = ctk.CTkLabel(path_row, text="EQ Install Path",
                                   width=_LABEL_W, anchor="w",
                                   font=ctk.CTkFont(size=12))
        eq_path_lbl.pack(side="left", padx=(8, 0))
        Tooltip(eq_path_lbl,
                "If you have multiple installs, ensure all appropriate instances have server files for Profusion.")
        ctk.CTkEntry(path_row, textvariable=path_var, width=_ENTRY_W).pack(side="left", padx=(6, 4))
        ctk.CTkButton(path_row, text="Browse", width=_BTN_W,
                      command=lambda v=path_var: self._browse_folder(v)).pack(side="left", padx=(0, 4))

        name_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        name_lbl = ctk.CTkLabel(name_frame, text="Instance Name",
                                width=_LABEL_W, anchor="w",
                                font=ctk.CTkFont(size=12))
        name_lbl.pack(side="left", padx=(8, 0))
        Tooltip(name_lbl, "Friendly name to help keep track each EQ install, eg Tanks vs Bots")
        ctk.CTkEntry(name_frame, textvariable=name_var, width=_ENTRY_W,
                     placeholder_text="e.g. Main, Boxes…").pack(side="left", padx=(6, 4))

        if len(self._eq_rows) > 0:
            ctk.CTkButton(
                path_row, text="✕", width=32, fg_color="#992222",
                command=lambda f=row_frame: self._remove_eq_row(f),
            ).pack(side="left", padx=(0, 4))

        entry = {"frame": row_frame, "path_var": path_var,
                 "name_var": name_var, "name_frame": name_frame}
        self._eq_rows.append(entry)

        if show_name:
            name_frame.pack(fill="x", pady=(2, 0))

    def _on_add_eq_instance(self) -> None:
        if len(self._eq_rows) == 1:
            self._eq_rows[0]["name_frame"].pack(fill="x", pady=(2, 0))
        self._add_eq_row(show_name=True)

    def _remove_eq_row(self, frame: ctk.CTkFrame) -> None:
        frame.destroy()
        self._eq_rows = [r for r in self._eq_rows if r["frame"].winfo_exists()]
        if len(self._eq_rows) == 1:
            self._eq_rows[0]["name_frame"].pack_forget()

    # ── Shared path-row builder ───────────────────────────────────────────────

    def _make_path_row(self, parent, label: str, default: str,
                       setting_key: str) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        var = tk.StringVar(value=default)
        setattr(self, f"_var_{setting_key}", var)

        lbl = ctk.CTkLabel(frame, text=label, width=_LABEL_W, anchor="w",
                           font=ctk.CTkFont(size=12))
        lbl.pack(side="left", padx=(8, 0))
        ctk.CTkEntry(frame, textvariable=var, width=_ENTRY_W).pack(side="left", padx=(6, 4))
        ctk.CTkButton(frame, text="Browse", width=_BTN_W,
                      command=lambda: self._browse_folder(var)).pack(side="left", padx=(0, 4))
        return frame, lbl

    # ── Action bar ────────────────────────────────────────────────────────────

    def _build_action_bar(self) -> ctk.CTkFrame:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(expand=True)

        finish_btn = ctk.CTkButton(
            inner,
            text="Finish Setup  →",
            font=ctk.CTkFont(size=14),
            width=220,
            height=38,
            command=self._finish,
        )
        finish_btn.pack(side="left", padx=7)
        Tooltip(finish_btn, "This setup wizard can be ran again to make changes")

        ctk.CTkButton(
            inner,
            text="Exit",
            width=110,
            height=38,
            fg_color="#992222",
            command=self._app.destroy,
        ).pack(side="left", padx=7)
        return bar

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _browse_folder(self, var: tk.StringVar) -> None:
        initial = var.get() if Path(var.get()).exists() else "/"
        chosen = filedialog.askdirectory(title="Select folder", initialdir=initial)
        if chosen:
            var.set(chosen)

    def _finish(self) -> None:
        self._gui_settings["first_run_complete"]    = True
        self._gui_settings["propatch_install_path"] = getattr(self, "_var_propatch_install_path").get().strip()
        self._gui_settings["install_mq"]            = self._mq_var.get()

        selected = set(self._gui_settings.get("selected_components", []))
        if not self._mq_var.get():
            selected -= _MQ_COMPONENTS
        else:
            selected |= _MQ_COMPONENTS
        self._gui_settings["selected_components"] = list(selected)

        instances = []
        for row in self._eq_rows:
            if not row["frame"].winfo_exists():
                continue
            path = row["path_var"].get().strip()
            name = row["name_var"].get().strip()
            if path:
                entry: dict = {"path": path}
                if name:
                    entry["name"] = name
                instances.append(entry)

        mq_rekkas = getattr(self, "_var_install_path").get().strip() or r"C:\Games\MQ-Profusion"

        # Write TOML settings (paths + optional token) — single source of truth
        try:
            config.save_path_settings(
                mq_rekkas=mq_rekkas,
                eq_instances=instances,
                github_token=self._token_var.get().strip(),
            )
            logger.info(f"Saved settings.local.toml to {config.get_data_dir()}")
        except Exception as exc:
            logger.error(f"Failed to write settings.local.toml: {exc}")

        if self._shortcut_var.get():
            try:
                _create_desktop_shortcut()
                logger.info("Desktop shortcut created: ProPatch on Desktop")
            except Exception as exc:
                logger.warning(f"Desktop shortcut creation failed: {exc}")

        config.save_gui_settings(self._gui_settings)
        logger.info("First-run setup complete")
        self._app.switch_view("components")


# ── Desktop shortcut helper ───────────────────────────────────────────────────

def _create_desktop_shortcut() -> None:
    """Create a 'ProPatch.lnk' shortcut on the Windows Desktop.

    Only runs when executing as a frozen PyInstaller exe; silently no-ops
    in dev mode (no exe to point to).
    """
    import subprocess
    import sys

    if not getattr(sys, "frozen", False):
        return

    exe_path     = Path(sys.executable)
    shortcut_path = Path.home() / "Desktop" / "ProPatch.lnk"
    exe_str      = str(exe_path)
    shortcut_str = str(shortcut_path)

    ps_cmd = (
        f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{shortcut_str}");'
        f'$s.TargetPath="{exe_str}";'
        f'$s.IconLocation="{exe_str},0";'
        f'$s.Description="ProPatch - EQ Profusion Component Manager";'
        f'$s.Save()'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"PowerShell returned {result.returncode}: {stderr}")
