from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logger: logging.Logger | None = None


def setup(log_path: Path) -> logging.Logger:
    global _logger
    logger = logging.getLogger("propatch")
    if logger.handlers:
        return logger  # already configured this process

    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        log_path, maxBytes=512_000, backupCount=1, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    _logger = logger
    return logger


def get() -> logging.Logger:
    return _logger or logging.getLogger("propatch")
