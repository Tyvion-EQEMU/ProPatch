from __future__ import annotations
import customtkinter as ctk
from typing import Callable
from profetch.gui.widgets.tooltip import Tooltip

# (light_mode_color, dark_mode_color)
_STATUS_COLORS: dict[str, tuple[str, str]] = {
    "idle":             ("#cccccc", "#444444"),
    "checking":         ("#4a9eff", "#2a7eff"),
    "current":          ("#4caf50", "#388e3c"),
    "update_available": ("#ff9800", "#e65c00"),
    "updating":         ("#4a9eff", "#2a7eff"),
    "updated":          ("#4caf50", "#2e7d32"),
    "error":            ("#f44336", "#b71c1c"),
}

_STATUS_LABELS: dict[str, str] = {
    "idle":             "—",
    "checking":         "Checking...",
    "current":          "Up to date",
    "update_available": "Update avail.",
    "updating":         "Updating...",
    "updated":          "Updated!",
    "error":            "Error",
}

_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Column widths — must match _build_column_headers() in components_view.py
COL_LAUNCH_W = 36   # launch button (rekkas_mq only) / empty placeholder
COL_VER_W    = 88   # installed / remote version columns
COL_STATUS_W = 122  # status badge


class ComponentRow(ctk.CTkFrame):
    """Table row: checkbox | name | installed ver | remote ver | status badge."""

    def __init__(
        self,
        parent,
        component: dict,
        on_checkbox_change: Callable[[str, bool], None],
        checked: bool = True,
        launch_callback: Callable | None = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._component = component
        self._on_checkbox_change = on_checkbox_change
        self._launch_callback = launch_callback
        self._status = "idle"
        self._spinner_idx = 0
        self._spinner_after_id: str | None = None
        self._checked_var = ctk.BooleanVar(value=checked)
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # col 0 — checkbox
        self._checkbox = ctk.CTkCheckBox(
            self, text="", variable=self._checked_var, width=28, command=self._on_check
        )
        self._checkbox.grid(row=0, column=0, padx=(6, 4), pady=7, sticky="ns")

        # col 1 — component name
        self._name_label = ctk.CTkLabel(
            self,
            text=self._component.get("name", ""),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self._name_label.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=7)

        # col 2 — launch button (rekkas_mq only) or empty placeholder
        if self._launch_callback is not None:
            btn = ctk.CTkButton(
                self,
                text="▶",
                width=COL_LAUNCH_W,
                height=26,
                fg_color=("#4caf50", "#388e3c"),
                hover_color=("#66bb6a", "#4caf50"),
                corner_radius=4,
                font=ctk.CTkFont(size=13),
                command=self._launch_callback,
            )
            btn.grid(row=0, column=2, padx=3, pady=7)
            Tooltip(btn, "Launch MQ Now")
        else:
            ctk.CTkLabel(self, text="", width=COL_LAUNCH_W, fg_color="transparent").grid(
                row=0, column=2, padx=3, pady=7
            )

        # col 3 — installed version
        self._local_label = ctk.CTkLabel(
            self,
            text="—",
            width=COL_VER_W,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("#555555", "#aaaaaa"),
            anchor="center",
        )
        self._local_label.grid(row=0, column=3, padx=3, pady=7)

        # col 4 — remote version
        self._remote_label = ctk.CTkLabel(
            self,
            text="—",
            width=COL_VER_W,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("#555555", "#aaaaaa"),
            anchor="center",
        )
        self._remote_label.grid(row=0, column=4, padx=3, pady=7)

        # col 5 — status badge
        self._status_badge = ctk.CTkLabel(
            self,
            text="—",
            width=COL_STATUS_W,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            fg_color=_STATUS_COLORS["idle"],
            text_color=("white", "white"),
        )
        self._status_badge.grid(row=0, column=5, padx=(18, 6), pady=7)

        # separator
        ctk.CTkFrame(self, height=1, fg_color=("#e0e0e0", "#2a2a2a")).grid(
            row=1, column=0, columnspan=6, sticky="ew", padx=6
        )

    def _on_check(self) -> None:
        self._on_checkbox_change(self._component["id"], self._checked_var.get())

    def set_status(self, status: str, local: str | None = None, remote: str | None = None) -> None:
        if not self.winfo_exists():
            return
        self._status = status
        self._stop_spinner()

        if status == "checking":
            self._local_label.configure(text="—")
            self._remote_label.configure(text="—")
        else:
            if local is not None:
                self._local_label.configure(text=local)
            if remote is not None:
                self._remote_label.configure(text=remote)

        colors = _STATUS_COLORS.get(status, _STATUS_COLORS["idle"])
        label  = _STATUS_LABELS.get(status, status)
        self._status_badge.configure(fg_color=colors, text=label, text_color=("white", "white"))

        if status in ("checking", "updating"):
            self._start_spinner(label)

    def _start_spinner(self, base_label: str) -> None:
        self._spinner_idx = 0
        self._tick_spinner(base_label)

    def _tick_spinner(self, base_label: str) -> None:
        if not self.winfo_exists():
            return
        frame = _SPINNER[self._spinner_idx % len(_SPINNER)]
        self._status_badge.configure(text=f"{frame} {base_label}")
        self._spinner_idx += 1
        self._spinner_after_id = self.after(80, self._tick_spinner, base_label)

    def _stop_spinner(self) -> None:
        if self._spinner_after_id is not None:
            self.after_cancel(self._spinner_after_id)
            self._spinner_after_id = None

    @property
    def component_id(self) -> str:
        return self._component["id"]

    @property
    def is_checked(self) -> bool:
        return self._checked_var.get()
