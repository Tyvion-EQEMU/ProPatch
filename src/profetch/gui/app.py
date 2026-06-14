from __future__ import annotations
import asyncio
import logging
import customtkinter as ctk

from profetch import config, db, log as plog
from profetch.gui.views.components_view import ComponentsView
from profetch.gui.views.log_view import LogView
from profetch.gui.views.setup_wizard import SetupWizard

logger = logging.getLogger("profetch")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = "ProFetch — EQ Profusion Component Manager"


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


def _seed_profetch_version() -> None:
    """Store the running ProFetch version in the DB on every startup.

    This ensures the patcher's own version is always tracked correctly —
    including after a self-update bat swap where a new exe boots for the
    first time.
    """
    from profetch.__about__ import __version__

    async def _seed():
        db_path = config.get_db_path()
        await db.init_db(db_path)
        await db.set_installed_version(db_path, "profetch", f"v{__version__}")

    try:
        asyncio.run(_seed())
    except Exception:
        pass


def _build_gui_manifest() -> list[dict]:
    """Build the display manifest for the component table.

    ProFetch itself is listed first in the 'patcher' section so users can
    see at a glance whether the patcher needs updating.  MQ entries come
    from the hardcoded COMPONENTS fallback; EQ server files are a static
    fallback since they're only defined in the remote manifest TOML.
    """
    from profetch.components import COMPONENTS

    result = [
        {"id": "profetch", "name": "ProFetch", "section": "patcher", "description": ""},
    ]
    for comp in COMPONENTS.values():
        if comp.id == "profetch":
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

        plog.setup(config.get_data_dir() / "profetch.log")
        _check_update_breadcrumb()
        _seed_profetch_version()

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
