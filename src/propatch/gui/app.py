from __future__ import annotations
import asyncio
import logging
import customtkinter as ctk

from propatch import config, db, log as plog
from propatch.gui.views.components_view import ComponentsView
from propatch.gui.views.log_view import LogView
from propatch.gui.views.setup_wizard import SetupWizard

logger = logging.getLogger("propatch")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = "ProPatch — EQ Profusion Component Manager [BETA]"


def _check_update_breadcrumb() -> None:
    import json
    path = config.get_data_dir() / "update_breadcrumb.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        from_v = data.get("from_version", "?")
        to_v   = data.get("to_version",   "?")
        ts     = data.get("timestamp",    "?")
        logger.info(f"Self-update completed successfully: {from_v} → {to_v} (initiated {ts})")
    except Exception as exc:
        logger.warning(f"Self-update breadcrumb found but unreadable: {exc}")
    finally:
        try:
            path.unlink()
        except Exception:
            pass


def _seed_propatch_version() -> None:
    from propatch.__about__ import __version__

    async def _seed():
        db_path = config.get_db_path()
        await db.init_db(db_path)
        await db.set_installed_version(db_path, "propatch", f"v{__version__}")

    try:
        asyncio.run(_seed())
    except Exception:
        pass


def _build_gui_manifest() -> list[dict]:
    """Build the display manifest for the component table.

    ProPatch itself is listed first in the 'patcher' section so users can
    see at a glance whether the patcher needs updating.  MQ entries come
    from the hardcoded COMPONENTS fallback; EQ server files are a static
    fallback since they're only defined in the remote manifest TOML.
    """
    from propatch.components import COMPONENTS

    result = [
        {"id": "propatch", "name": "ProPatch", "section": "patcher", "description": ""},
    ]
    for comp in COMPONENTS.values():
        if comp.id == "propatch":
            continue  # already listed in patcher section above
        result.append({
            "id":          comp.id,
            "name":        comp.name,
            "section":     "mq",
            "description": "",
        })

    # EQ server files — mirrored from manifest.toml; section="server" maps to
    # "Server Components" in the table header
    _EQ_SERVER_FILES = [
        {"id": "spells_us", "name": "Spells (spells_us.txt)",          "section": "server", "description": ""},
        {"id": "dbstr_us",  "name": "DB Strings (dbstr_us.txt)",       "section": "server", "description": ""},
        {"id": "skillcaps", "name": "Skill Caps (SkillCaps.txt)",      "section": "server", "description": ""},
        {"id": "basedata",  "name": "Base Data (BaseData.txt)",        "section": "server", "description": ""},
        {"id": "dinput8",   "name": "DirectInput Shim (dinput8.dll)",  "section": "server", "description": ""},
    ]
    result.extend(_EQ_SERVER_FILES)

    return result


class App(ctk.CTk):
    """Root application window. Owns shared state and view switching."""

    def __init__(self) -> None:
        super().__init__()
        self.title(_TITLE)
        self.geometry("680x600")
        self.resizable(False, True)
        self.minsize(680, 400)

        plog.setup(config.get_data_dir() / "propatch.log")
        _check_update_breadcrumb()
        _seed_propatch_version()

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
    app.deiconify()
    app.lift()
    app.focus_force()
    app.mainloop()
