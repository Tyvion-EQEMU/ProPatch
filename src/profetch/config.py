from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

_DEFAULT_SETTINGS = """\
[paths]
mq_rekkas = "C:\\\\Games\\\\MQ-Rekkas"
eq_dirs = []

[components]
rekkas_mq = true
mq2rwarp = true
rgmercs = true
e9loot = true

[protected]
always = ["config/*", "MacroQuest.ini"]
"""


def get_data_dir() -> Path:
    # When packaged as a PyInstaller exe, store data next to the executable
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "proFetch"

    # Dev / editable install — use a separate dev directory so test data
    # never collides with a real production install
    if os.name == "nt":
        public = os.environ.get("PUBLIC", r"C:\Users\Public")
        return Path(public) / "proFetch-dev"

    import platformdirs
    return Path(platformdirs.user_data_dir("proFetch-dev"))


def get_db_path() -> Path:
    return get_data_dir() / "profetch.db"


def ensure_data_dir() -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    settings_path = data_dir / "settings.toml"
    if not settings_path.exists():
        bundled = Path(__file__).parent.parent.parent / "settings.toml"
        if bundled.exists():
            shutil.copy2(bundled, settings_path)
        else:
            settings_path.write_text(_DEFAULT_SETTINGS, encoding="utf-8")

    return data_dir


def load_settings():
    from dynaconf import Dynaconf

    data_dir = ensure_data_dir()
    return Dynaconf(
        envvar_prefix="PROFETCH",
        settings_files=[
            str(data_dir / "settings.toml"),
            str(data_dir / "settings.local.toml"),
        ],
        merge_enabled=True,
    )
