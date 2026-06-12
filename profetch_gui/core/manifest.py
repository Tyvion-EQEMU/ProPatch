from __future__ import annotations
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"

_BUNDLED_MANIFEST: list[dict] = [
    {"id": "rekkas_mq", "section": "mq",     "name": "MQ Install (Rekkas)",     "source": "RekkasGit/E3NextAndMQNextBinary", "type": "binary_zip"},
    {"id": "mq2rwarp",  "section": "mq",     "name": "MQ2RWarp",                "source": "Tyvion-EQEMU/MQ2RWarp",          "type": "github_release"},
    {"id": "rgmercs",   "section": "mq",     "name": "RGMercs",                 "source": "DerpleDude/rgmercs",             "type": "git_sha"},
    {"id": "proloot",   "section": "mq",     "name": "ProLoot",                 "source": "Tyvion-EQEMU/ProLoot",           "type": "github_release"},
    {"id": "spells_us", "section": "server", "name": "spells_us.txt",           "source": "EQProfusion/game-server",        "type": "eq_file"},
    {"id": "dbstr_us",  "section": "server", "name": "dbstr_us.txt",            "source": "EQProfusion/game-server",        "type": "eq_file"},
]


def load_manifest() -> list[dict]:
    """Load the curated component manifest from data/manifest.json.
    TODO: swap in remote fetch from profetch-manifest GitHub repo.
    """
    manifest_file = _DATA_DIR / "manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return _BUNDLED_MANIFEST
