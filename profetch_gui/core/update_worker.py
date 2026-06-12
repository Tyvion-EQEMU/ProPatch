from __future__ import annotations
import time
import random
import logging
from typing import Callable, Optional

logger = logging.getLogger("profetch")

# (installed_local, latest_remote).  None for remote = already current.
_FAKE_VERSIONS: dict[str, tuple[str, str | None]] = {
    "rekkas_mq": ("abc1234", "def5678"),
    "mq2rwarp":  ("v1.2.3",  "v1.2.4"),
    "rgmercs":   ("bbb9999", None),
    "proloot":   ("v0.9.1",  None),
    "spells_us": ("sha:a1b2c3d4", None),
    "dbstr_us":  ("sha:e5f6g7h8", "sha:f9a0b1c2"),
}

# (cid, status, local_ver_or_None, remote_ver_or_None)
StatusCallback = Callable[[str, str, Optional[str], Optional[str]], None]


def run_status_check(component_ids: list[str], on_status: StatusCallback) -> None:
    """Simulate version checks sequentially.
    TODO: replace with real GitHub API calls and EQ server hash checks.
    """
    logger.info("Status scan started")
    for cid in component_ids:
        on_status(cid, "checking", None, None)
        time.sleep(random.uniform(0.5, 1.2))
        local, remote = _FAKE_VERSIONS.get(cid, ("?", None))
        if remote:
            on_status(cid, "update_available", local, remote)
            logger.info(f"[{cid}] Update available: {local} → {remote}")
        else:
            on_status(cid, "current", local, local)
            logger.info(f"[{cid}] Up to date ({local})")
    logger.info("Status scan complete")


def run_update(
    component_ids: list[str],
    on_status: StatusCallback,
    on_done: Callable[[], None],
) -> None:
    """Simulate sequential updates. Skips components that are already current.
    TODO: replace with real download/install logic.
    """
    logger.info("Update started")
    for cid in component_ids:
        local, remote = _FAKE_VERSIONS.get(cid, ("?", None))
        if not remote:
            on_status(cid, "current", local, local)
            time.sleep(0.25)
            continue
        on_status(cid, "updating", local, remote)
        logger.info(f"[{cid}] Downloading {remote}")
        time.sleep(random.uniform(1.0, 2.5))
        on_status(cid, "updated", remote, remote)
        logger.info(f"[{cid}] Done: {remote}")
    logger.info("Update complete")
    on_done()
