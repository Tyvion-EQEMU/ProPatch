from __future__ import annotations
import logging
from pathlib import Path

_LOGS_DIR = Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOGS_DIR / "profetch.log"


def setup_logger() -> logging.Logger:
    """Configure the profetch logger to write to logs/profetch.log."""
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("profetch")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
    return logger


def seed_log_if_empty() -> None:
    """Write sample entries so the log view has content on first run."""
    if _LOG_FILE.exists() and _LOG_FILE.stat().st_size > 0:
        return
    log = logging.getLogger("profetch")
    log.info("ProFetch GUI started")
    log.info("Loading manifest from data/manifest.json")
    log.info("Manifest loaded: 4 components")
    log.debug("Settings loaded from data/settings.json")
    log.info("Beginning status scan for all components")
    log.info("[rekka_mq] Checking version... current: abc1234")
    log.info("[rekka_mq] Status: Up to date")
    log.info("[mq2rwarp] Checking version... current: v1.2.3")
    log.warning("[mq2rwarp] Update available: v1.2.4")
    log.info("[rgmercs] Checking version... current: def5678")
    log.info("[rgmercs] Status: Up to date")
    log.info("[proloot] Checking version... current: v0.9.1")
    log.info("[proloot] Status: Up to date")
    log.info("Status scan complete")


def get_log_path() -> Path:
    return _LOG_FILE
