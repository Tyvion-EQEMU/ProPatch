from __future__ import annotations
import customtkinter as ctk

from core.settings import load_settings
from core.manifest import load_manifest
from core.logger import setup_logger, seed_log_if_empty
from views.components_view import ComponentsView
from views.log_view import LogView
from views.setup_wizard import SetupWizard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = "ProFetch — EQ Profusion Component Manager"


class App(ctk.CTk):
    """Root application window. Owns shared state and view switching."""

    def __init__(self) -> None:
        super().__init__()
        self.title(_TITLE)
        self.geometry("680x600")
        self.resizable(False, True)
        self.minsize(680, 400)

        setup_logger()
        seed_log_if_empty()

        self._settings = load_settings()
        self._manifest = load_manifest()
        self._current_view: ctk.CTkFrame | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if self._settings.get("first_run_complete"):
            self.switch_view("components")
        else:
            self.switch_view("setup")

    def switch_view(self, name: str) -> None:
        """Destroy the current view frame and show the requested one."""
        if self._current_view is not None:
            self._current_view.destroy()
            self._current_view = None

        if name == "components":
            self._current_view = ComponentsView(
                self, settings=self._settings, manifest=self._manifest
            )
        elif name == "log":
            self._current_view = LogView(self)
        elif name == "setup":
            self._current_view = SetupWizard(self, settings=self._settings)

        if self._current_view is not None:
            self._current_view.grid(row=0, column=0, sticky="nsew")
