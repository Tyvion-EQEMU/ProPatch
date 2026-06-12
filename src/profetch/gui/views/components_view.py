from __future__ import annotations
import logging
import threading
import tkinter as tk
from datetime import datetime
import customtkinter as ctk

from profetch.gui.widgets.component_row import ComponentRow, COL_VER_W, COL_STATUS_W
from profetch.gui.widgets.header import build_header, _STRIP_BG, _MARGIN
from profetch.gui.worker import run_status_check, run_update
from profetch import config

logger = logging.getLogger("profetch")

_SECTION_ORDER = ["mq", "server", "custom"]
_SECTION_NAMES = {
    "mq":     "MQ Components",
    "server": "Server Components",
    "custom": "User Provided Patching",
}


class ComponentsView(ctk.CTkFrame):
    """Primary screen: banner header, component list, action bar."""

    def __init__(self, parent_app, settings: dict, manifest: list[dict], **kwargs):
        super().__init__(parent_app, fg_color="transparent", **kwargs)
        self._app = parent_app
        self._gui_settings = settings
        self._manifest = manifest
        self._rows: dict[str, ComponentRow] = {}
        self._worker_thread: threading.Thread | None = None

        self._banner_h = 0
        self._build()
        self._fit_window()
        self.after(500, self._do_rescan)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header().grid(row=0, column=0, sticky="ew")
        self._build_column_headers().grid(row=1, column=0, sticky="ew", padx=25, pady=(8, 0))
        self._build_list().grid(row=2, column=0, sticky="nsew", padx=25)
        self._build_action_bar().grid(row=3, column=0, sticky="ew", padx=25, pady=8)

    def _build_header(self) -> ctk.CTkFrame:
        header, banner_h = build_header(self)
        self._banner_h = banner_h

        strip = header.grid_slaves(row=1, column=0)[0]
        self._checked_label = tk.Label(
            strip,
            text="● Last checked: —",
            font=("Consolas", 10), fg="#888888", bg=_STRIP_BG,
            padx=0, pady=0,
        )
        self._checked_label.place(relx=1.0, rely=0.5, anchor="e", x=-_MARGIN)

        return header

    def _build_column_headers(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color=("#1e1e30", "#0e0e1a"))
        frame.grid_propagate(False)
        frame.grid_columnconfigure(1, weight=1)

        lbl = dict(font=ctk.CTkFont(size=10, weight="bold"),
                   text_color=("#888888", "#666666"),
                   fg_color="transparent")

        ctk.CTkLabel(frame, text="", width=38, fg_color="transparent").grid(row=0, column=0)
        ctk.CTkLabel(frame, text="NAME", anchor="w", **lbl).grid(
            row=0, column=1, sticky="ew", padx=(0, 6)
        )
        ctk.CTkLabel(frame, text="INSTALLED", width=COL_VER_W, anchor="center", **lbl).grid(
            row=0, column=2, padx=3
        )
        ctk.CTkLabel(frame, text="REMOTE", width=COL_VER_W, anchor="center", **lbl).grid(
            row=0, column=3, padx=3
        )
        ctk.CTkLabel(frame, text="STATUS", width=COL_STATUS_W, anchor="center", **lbl).grid(
            row=0, column=4, padx=(18, 6)
        )
        return frame

    def _build_list(self) -> ctk.CTkScrollableFrame:
        frame = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray14"), corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)

        selected = set(self._gui_settings.get("selected_components", []))

        sections: dict[str, list[dict]] = {k: [] for k in _SECTION_ORDER}
        for comp in self._manifest:
            key = comp.get("section", "mq")
            sections.setdefault(key, []).append(comp)
        for comp in self._gui_settings.get("custom_components", []):
            sections["custom"].append(comp)

        first = True
        for section_key in _SECTION_ORDER:
            comps = sections.get(section_key, [])
            if not comps:
                continue
            if not first:
                sep = ctk.CTkFrame(frame, height=2, fg_color=("#cccccc", "#4a4a5a"))
                sep.pack(fill="x", padx=4, pady=(6, 0))
                sep.pack_propagate(False)
            first = False
            self._add_section_divider(frame, _SECTION_NAMES[section_key])
            for comp in comps:
                row = ComponentRow(
                    frame,
                    component=comp,
                    on_checkbox_change=self._on_checkbox_change,
                    checked=comp["id"] in selected,
                )
                row.pack(fill="x", pady=1)
                self._rows[comp["id"]] = row

        self._add_btn = ctk.CTkButton(
            frame,
            text="+ Add custom component",
            fg_color="transparent",
            border_width=1,
            border_color=("#aaaaaa", "#555555"),
            text_color=("#555555", "#aaaaaa"),
            hover_color=("#eeeeee", "#2a2a2a"),
            command=self._open_add_dialog,
        )
        self._add_btn.pack(fill="x", padx=4, pady=(12, 6))

        self._list_frame = frame
        return frame

    def _add_section_divider(self, parent, title: str) -> None:
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(10, 3))
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

    def _rebuild_list(self) -> None:
        if hasattr(self, "_list_frame") and self._list_frame.winfo_exists():
            self._list_frame.destroy()
        self._rows.clear()
        self._build_list().grid(row=2, column=0, sticky="nsew", padx=25)

    def _build_action_bar(self) -> ctk.CTkFrame:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(expand=True)
        buttons: list[tuple[str, str | None, object]] = [
            ("Update",       "#4a9eff", self._on_update),
            ("Rescan",       None,      self._on_rescan),
            ("Re-run Setup", None,      lambda: self._app.switch_view("setup")),
            ("Log",          None,      lambda: self._app.switch_view("log")),
            ("Exit",         "#992222", self._app.destroy),
        ]
        for text, color, cmd in buttons:
            kw: dict = {"text": text, "command": cmd, "width": 110, "height": 32}
            if color:
                kw["fg_color"] = color
            ctk.CTkButton(inner, **kw).pack(side="left", padx=7)
        return bar

    def _fit_window(self) -> None:
        LIST_MIN = 280
        ACTION_H = 56
        STRIP_H  = 60
        COLHDR_H = 26
        img_h = self._banner_h if self._banner_h else 80
        total = int((img_h + STRIP_H + COLHDR_H + LIST_MIN + ACTION_H) * 1.39) - 96
        self._app.geometry(f"680x{total}")
        self._app.minsize(680, 400)

    # ── Worker helpers ─────────────────────────────────────────────────────────

    def _selected_ids(self) -> list[str]:
        return [cid for cid, row in self._rows.items() if row.is_checked]

    def _start_worker(self, target, *args) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Worker already running — ignoring request")
            return
        self._worker_thread = threading.Thread(target=target, args=args, daemon=True)
        self._worker_thread.start()

    def _status_callback(self, cid: str, status: str, local: str | None, remote: str | None) -> None:
        self._app.after(0, lambda: self._apply_status(cid, status, local, remote))

    def _apply_status(self, cid: str, status: str, local: str | None, remote: str | None) -> None:
        if not self.winfo_exists():
            return
        row = self._rows.get(cid)
        if row:
            row.set_status(status, local, remote)
        if status in ("current", "update_available", "updated", "error"):
            self._refresh_checked_label()

    def _refresh_checked_label(self) -> None:
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._checked_label.configure(text=f"● Last checked: {ts}")

    # ── Button handlers ────────────────────────────────────────────────────────

    def _on_rescan(self) -> None:
        self._do_rescan()

    def _do_rescan(self) -> None:
        self._start_worker(run_status_check, self._selected_ids(), self._status_callback)

    def _on_update(self) -> None:
        self._start_worker(
            run_update,
            self._selected_ids(),
            self._status_callback,
            lambda: self._app.after(0, self._refresh_checked_label),
        )

    def _on_checkbox_change(self, cid: str, checked: bool) -> None:
        selected: set[str] = set(self._gui_settings.get("selected_components", []))
        if checked:
            selected.add(cid)
        else:
            selected.discard(cid)
        self._gui_settings["selected_components"] = list(selected)
        config.save_gui_settings(self._gui_settings)

    def _open_add_dialog(self) -> None:
        AddComponentDialog(self._app, on_save=self._on_custom_added)

    def _on_custom_added(self, comp: dict) -> None:
        self._gui_settings.setdefault("custom_components", []).append(comp)
        config.save_gui_settings(self._gui_settings)
        logger.info(f"Custom component registered: {comp.get('name')}")
        self._rebuild_list()


# ── Add custom component dialog ────────────────────────────────────────────────

_COMP_TYPES = ["github_release", "git_sha", "binary_zip", "local_path"]


class AddComponentDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save: object = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_save = on_save
        self.title("Add Custom Component")
        self.geometry("420x320")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        pad = {"padx": 24, "pady": (0, 8)}

        ctk.CTkLabel(
            self,
            text="Add Custom Component",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 12))

        ctk.CTkLabel(self, text="Name:", anchor="w").pack(fill="x", **pad)
        self._name = ctk.CTkEntry(self, width=370)
        self._name.pack(**pad)

        ctk.CTkLabel(self, text="Source (owner/repo or local path):", anchor="w").pack(
            fill="x", **pad
        )
        self._source = ctk.CTkEntry(self, width=370)
        self._source.pack(**pad)

        ctk.CTkLabel(self, text="Type:", anchor="w").pack(fill="x", **pad)
        self._type_var = ctk.StringVar(value="github_release")
        ctk.CTkOptionMenu(self, values=_COMP_TYPES, variable=self._type_var, width=370).pack(**pad)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(8, 0))
        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color="#555555",
                      command=self.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Add", width=100,
                      command=self._save).pack(side="left", padx=6)

    def _save(self) -> None:
        name   = self._name.get().strip()
        source = self._source.get().strip()
        if not name or not source:
            return
        comp = {
            "id":          name.lower().replace(" ", "_"),
            "name":        name,
            "source":      source,
            "type":        self._type_var.get(),
            "description": "",
            "custom":      True,
        }
        if self._on_save:
            self._on_save(comp)
        self.destroy()
