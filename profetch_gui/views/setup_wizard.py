from __future__ import annotations
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from core.settings import save_settings
from widgets.header import build_header, _WARM_GOLD, _STRIP_BG, _MARGIN
from widgets.tooltip import Tooltip

logger = logging.getLogger("profetch")

_MQ_COMPONENTS = {"rekkas_mq", "mq2rwarp", "rgmercs", "proloot"}

_NARRATIVE = (
    "Welcome to ProFetch — the EQ Profusion component manager.\n\n"
    "This setup will walk you through the essentials: where ProFetch lives on your machine, "
    "whether you want MacroQuest managed for you, and where your EverQuest installation(s) are. "
    "You can always revisit these settings later from the main panel.\n\n"
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
        self._app      = parent_app
        self._settings = settings
        self._eq_rows: list[dict] = []
        self._mq_path_frame: ctk.CTkFrame | None = None
        self._banner_h = 0
        self._build()
        self._fit_window()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _fit_window(self) -> None:
        STRIP_H      = 60
        NARRATIVE_H  = 110
        QUESTIONS_MIN = 320
        ACTION_H     = 56
        img_h = self._banner_h if self._banner_h else 80
        total = int((img_h + STRIP_H + NARRATIVE_H + QUESTIONS_MIN + ACTION_H) * 1.39) - 96
        self._app.geometry(f"680x{total}")
        self._app.minsize(680, 500)

    def _build(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header, self._banner_h = build_header(self)
        header.grid(row=0, column=0, sticky="ew")

        # "Setup Wizard" on the right side of the info strip
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

        self._build_section_header(scroll, "ProFetch")
        self._build_profetch_path(scroll)

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

    # ── ProFetch install path ─────────────────────────────────────────────────

    def _build_profetch_path(self, parent) -> None:
        row, lbl = self._make_path_row(
            parent,
            label="ProFetch Install Path",
            default=self._settings.get("profetch_install_path", r"C:\Games\ProFetch"),
            setting_key="profetch_install_path",
        )
        row.pack(fill="x", pady=3)
        Tooltip(lbl, "This patcher will be copied here, plus all settings and logs will be kept here.")

    # ── MacroQuest ────────────────────────────────────────────────────────────

    def _build_mq_section(self, parent) -> None:
        toggle_row = ctk.CTkFrame(parent, fg_color="transparent")
        toggle_row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            toggle_row,
            text="Install and update MacroQuest",
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=_LABEL_W + _ENTRY_W,
        ).pack(side="left", padx=(8, 0))

        self._mq_var = ctk.BooleanVar(value=self._settings.get("install_mq", True))
        mq_switch = ctk.CTkSwitch(
            toggle_row,
            text="",
            variable=self._mq_var,
            width=48,
            command=self._on_mq_toggle,
        )
        mq_switch.pack(side="left", padx=(12, 0))
        Tooltip(mq_switch, "If you wish to ignore and leave off all MQ components, toggle this OFF")

        self._mq_path_frame, _ = self._make_path_row(
            parent,
            label="MQ Install Path",
            default=self._settings.get("install_path", r"C:\Games\MQ-Rekkas"),
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
        Tooltip(self._add_eq_btn, "If you have multiple installs, ensure all appropriate instances have server files for Profusion.")

    def _add_eq_row(self, show_name: bool = True, path: str = "", name: str = "") -> None:
        row_frame = ctk.CTkFrame(self._eq_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)

        path_var = tk.StringVar(value=path)
        name_var = tk.StringVar(value=name)

        # Path sub-row
        path_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        path_row.pack(fill="x")
        ctk.CTkLabel(path_row, text="EQ Install Path",
                     width=_LABEL_W, anchor="w",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 0))
        ctk.CTkEntry(path_row, textvariable=path_var, width=_ENTRY_W).pack(side="left", padx=(6, 4))
        ctk.CTkButton(path_row, text="Browse", width=_BTN_W,
                      command=lambda v=path_var: self._browse_folder(v)).pack(side="left", padx=(0, 4))

        # Name sub-row
        name_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        name_lbl = ctk.CTkLabel(name_frame, text="Instance Name",
                                width=_LABEL_W, anchor="w",
                                font=ctk.CTkFont(size=12))
        name_lbl.pack(side="left", padx=(8, 0))
        Tooltip(name_lbl, "Friendly name to help keep track each EQ install, eg Tanks vs Bots")
        ctk.CTkEntry(name_frame, textvariable=name_var, width=_ENTRY_W,
                     placeholder_text="e.g. Main, Boxes…").pack(side="left", padx=(6, 4))

        # Remove button on rows beyond the first
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
        """Returns (row_frame, label_widget) so callers can attach tooltips."""
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
        self._settings["first_run_complete"]    = True
        self._settings["profetch_install_path"] = getattr(self, "_var_profetch_install_path").get().strip()
        self._settings["install_mq"]            = self._mq_var.get()
        self._settings["install_path"]          = getattr(self, "_var_install_path").get().strip() if self._mq_var.get() else ""

        selected = set(self._settings.get("selected_components", []))
        if not self._mq_var.get():
            selected -= _MQ_COMPONENTS
        else:
            selected |= _MQ_COMPONENTS
        self._settings["selected_components"] = list(selected)

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
        self._settings["eq_instances"] = instances

        save_settings(self._settings)
        logger.info("First-run setup complete")
        self._app.switch_view("components")
