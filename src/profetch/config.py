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


_GUI_DEFAULTS: dict = {
    "first_run_complete":     False,
    "profetch_install_path":  r"C:\Games\ProFetch",
    "install_mq":             True,
    "install_path":           r"C:\Games\MQ-Rekkas",
    "eq_instances":           [],
    "selected_components":    ["profetch",
                               "rekkas_mq", "mq2rwarp", "rgmercs", "proloot",
                               "spells_us", "dbstr_us", "skillcaps", "basedata", "dinput8"],
    "custom_components":      [],
    "log_level":              "INFO",
}


def _gui_settings_path() -> Path:
    return get_data_dir() / "gui_settings.json"


def load_gui_settings() -> dict:
    import json
    ensure_data_dir()
    path = _gui_settings_path()
    settings = dict(_GUI_DEFAULTS)
    if path.exists():
        try:
            on_disk = json.loads(path.read_text(encoding="utf-8"))
            settings.update(on_disk)
        except Exception:
            pass
    return settings


def save_gui_settings(settings: dict) -> None:
    import json
    ensure_data_dir()
    _gui_settings_path().write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _toml_str(value: str) -> str:
    return value.replace("\\", "\\\\")


def save_path_settings(
    mq_rekkas: str,
    eq_instances: list[dict],
) -> None:
    """Write [paths] block to settings.local.toml.

    eq_instances is the GUI format: [{"path": ..., "name": ...}, ...]
    """
    data_dir = ensure_data_dir()

    lines = ["[paths]", f'mq_rekkas = "{_toml_str(mq_rekkas)}"']

    eq_dirs  = [inst["path"] for inst in eq_instances if inst.get("path")]
    eq_names = [inst.get("name", "") for inst in eq_instances if inst.get("path")]

    if eq_dirs:
        paths_toml = ", ".join(f'"{_toml_str(p)}"' for p in eq_dirs)
        lines.append(f"eq_dirs = [{paths_toml}]")
        if any(eq_names):
            names_toml = ", ".join(f'"{_toml_str(n)}"' for n in eq_names)
            lines.append(f"eq_dir_names = [{names_toml}]")

    (data_dir / "settings.local.toml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
