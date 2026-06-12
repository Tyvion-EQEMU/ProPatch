from __future__ import annotations
import customtkinter as ctk

from profetch import config, log as plog
from profetch.gui.views.components_view import ComponentsView
from profetch.gui.views.log_view import LogView
from profetch.gui.views.setup_wizard import SetupWizard

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = "ProFetch — EQ Profusion Component Manager"


def _build_gui_manifest() -> list[dict]:
    """Convert the hardcoded Component objects to the dict format the GUI views expect."""
    from profetch.components import COMPONENTS
    result = []
    for comp in COMPONENTS.values():
        result.append({
            "id":          comp.id,
            "name":        comp.name,
            "section":     "mq",
            "description": "",
        })
    return result


class App(ctk.CTk):
    """Root application window. Owns shared state and view switching."""

    def __init__(self) -> None:
        super().__init__()
        self.title(_TITLE)
        self.geometry("680x600")
        self.resizable(False, True)
        self.minsize(680, 400)

        plog.setup(config.get_data_dir() / "profetch.log")

        self._gui_settings = config.load_gui_settings()
        self._manifest     = _build_gui_manifest()
        self._current_view: ctk.CTkFrame | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if self._gui_settings.get("first_run_complete"):
            self.switch_view("components")
        else:
            self.switch_view("setup")

    def switch_view(self, name: str) -> None:
        if self._current_view is not None:
            self._current_view.destroy()
            self._current_view = None

        if name == "components":
            self._current_view = ComponentsView(
                self, settings=self._gui_settings, manifest=self._manifest
            )
        elif name == "log":
            self._current_view = LogView(self)
        elif name == "setup":
            self._current_view = SetupWizard(self, settings=self._gui_settings)

        if self._current_view is not None:
            self._current_view.grid(row=0, column=0, sticky="nsew")


def launch() -> None:
    config.ensure_data_dir()
    app = App()
    app.mainloop()
