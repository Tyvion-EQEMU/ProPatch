from __future__ import annotations
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_SETTINGS_FILE = _DATA_DIR / "settings.json"

_DEFAULTS: dict = {
    "first_run_complete": False,
    "profetch_install_path": r"C:\Games\ProFetch",
    "install_mq": True,
    "install_path": r"C:\Games\MQ-Rekkas",
    "eq_instances": [],
    "selected_components": ["rekkas_mq", "mq2rwarp", "rgmercs", "proloot", "spells_us", "dbstr_us"],
    "custom_components": [],
    "log_level": "INFO",
}


def load_settings() -> dict:
    """Return settings from disk; defaults (first_run_complete=False) if file is absent."""
    if not _SETTINGS_FILE.exists():
        return dict(_DEFAULTS)
    try:
        with open(_SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)


def save_settings(settings: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
