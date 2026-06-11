from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

_DEFAULT_SETTINGS = """\
[paths]
mq_rekkas = "C:\\\\Games\\\\MQ-Rekkas"
eq_dirs = []

# Optional: GitHub Personal Access Token
# Raises the API rate limit from 60 to 5000 requests/hour.
# Create one at https://github.com/settings/tokens (no scopes needed for public repos)
# github_token = "ghp_..."

[components]
rekkas_mq = true
mq2rwarp = true
rgmercs = true
proloot = true

[protected]
always = ["config/*", "MacroQuest.ini"]
"""


def get_data_dir() -> Path:
    # When packaged as a PyInstaller exe, data lives in the same folder as the exe
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

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


def get_github_token(settings) -> str | None:
    try:
        val = settings.get("github_token", default=None)
        return str(val).strip() or None if val else None
    except Exception:
        return None


def save_component_settings(data_dir: Path, component_states: dict[str, bool]) -> None:
    """Write [components] block to settings.local.toml without touching other sections."""
    settings_path = data_dir / "settings.local.toml"
    content = settings_path.read_text(encoding="utf-8") if settings_path.exists() else ""

    block_lines = ["[components]"]
    for cid, enabled in component_states.items():
        block_lines.append(f"{cid} = {'true' if enabled else 'false'}")
    new_block = "\n".join(block_lines)

    # Strip existing [components] section (up to next section header or EOF)
    cleaned = re.sub(r"\[components\].*?(?=\n\[|\Z)", "", content, flags=re.DOTALL).rstrip()
    content = (cleaned + "\n\n" + new_block + "\n") if cleaned else (new_block + "\n")
    settings_path.write_text(content, encoding="utf-8")


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
