from __future__ import annotations
import logging
import customtkinter as ctk

from propatch import config, log as plog

logger = logging.getLogger("propatch")

_LEVEL_SETS: dict[str, set[str]] = {
    "DEBUG":   {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
    "INFO":    {"INFO", "WARNING", "ERROR", "CRITICAL"},
    "WARNING": {"WARNING", "ERROR", "CRITICAL"},
    "ERROR":   {"ERROR", "CRITICAL"},
}


class LogView(ctk.CTkFrame):
    """Full-screen log panel: level filter, scrollable log text, back button."""

    def __init__(self, parent_app, **kwargs):
        super().__init__(parent_app, fg_color="transparent", **kwargs)
        self._app = parent_app
        self._current_level = "INFO"
        self._all_lines: list[str] = []
        self._build()
        self._load_log()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))

        ctk.CTkButton(
            top,
            text="← Components",
            width=130,
            command=lambda: self._app.switch_view("components"),
        ).pack(side="left")

        ctk.CTkLabel(top, text="Level:").pack(side="left", padx=(16, 4))

        self._level_seg = ctk.CTkSegmentedButton(
            top,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            command=self._on_level_change,
            width=280,
        )
        self._level_seg.set("INFO")
        self._level_seg.pack(side="left")

        ctk.CTkButton(
            top, text="Refresh", width=80, command=self._load_log
        ).pack(side="right")

        self._textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
            wrap="none",
            activate_scrollbars=True,
        )
        self._textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _on_level_change(self, value: str) -> None:
        self._current_level = value
        self._apply_filter()

    def _load_log(self) -> None:
        path = config.get_data_dir() / "propatch.log"
        if not path.exists():
            self._all_lines = ["(No log file yet — run a scan or update to populate it.)\n"]
        else:
            try:
                with open(path, encoding="utf-8") as f:
                    self._all_lines = f.readlines()
            except OSError as exc:
                self._all_lines = [f"(Error reading log: {exc})\n"]
        self._apply_filter()

    def _apply_filter(self) -> None:
        allowed = _LEVEL_SETS.get(self._current_level, set())
        result: list[str] = []
        for line in self._all_lines:
            has_level = any(f"] {lvl}:" in line for lvl in _LEVEL_SETS["DEBUG"])
            if has_level:
                if not any(f"] {lvl}:" in line for lvl in allowed):
                    continue
            result.append(line)

        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("end", "".join(result))
        self._textbox.configure(state="disabled")
        self._textbox.see("end")
