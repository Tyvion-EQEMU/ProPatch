from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TrackingMethod(str, Enum):
    COMMIT_SHA = "commit_sha"
    RELEASE_TAG = "release_tag"
    CONTENT_HASH = "content_hash"


@dataclass
class Component:
    id: str
    name: str
    owner: str
    repo: str
    tracking: TrackingMethod
    destination: str  # relative path under mq_rekkas root; "" = root
    protected_patterns: list[str]
    enabled_key: str
    branch: str | None = None  # required when tracking == COMMIT_SHA
    release_asset_name: str | None = None  # required when tracking == RELEASE_TAG
    zip_subdir: str | None = None  # extract only this subdir from the zip (strips its prefix)
    show_version: bool = False  # also fetch latest release tag for display alongside commit SHA


@dataclass
class EqFile:
    id: str
    name: str
    filename: str        # target filename on disk; "" for zip packs
    url: str             # direct download URL; "" for GitHub-sourced
    destination: str     # relative to each EQ dir; "" = root
    owner: str | None = None
    repo: str | None = None
    branch: str | None = None
    tracking: TrackingMethod | None = None  # None = always re-download
    extract: bool = False  # True = downloaded file is a zip to be extracted


# Hardcoded fallback — used if the manifest cannot be fetched
COMPONENTS: dict[str, Component] = {
    "rekkas_mq": Component(
        id="rekkas_mq",
        name="MQ Install (Rekkas)",
        owner="RekkasGit",
        repo="E3NextAndMQNextBinary",
        tracking=TrackingMethod.COMMIT_SHA,
        branch="main",
        destination="",
        protected_patterns=["config/*", "MacroQuest.ini"],
        enabled_key="rekkas_mq",
        show_version=True,
    ),
    "mq2rwarp": Component(
        id="mq2rwarp",
        name="MQ2RWarp",
        owner="Tyvion-EQEMU",
        repo="MQ2RWarp",
        tracking=TrackingMethod.RELEASE_TAG,
        branch=None,
        destination="plugins",
        protected_patterns=[],
        enabled_key="mq2rwarp",
        release_asset_name="MQ2RWarp.dll",
    ),
    "rgmercs": Component(
        id="rgmercs",
        name="RGMercs",
        owner="DerpleDude",
        repo="rgmercs",
        tracking=TrackingMethod.COMMIT_SHA,
        branch="main",
        destination="lua/rgmercs",
        protected_patterns=["config/*"],
        enabled_key="rgmercs",
        show_version=True,
    ),
    "proloot": Component(
        id="proloot",
        name="ProLoot",
        owner="Tyvion-EQEMU",
        repo="proLoot",
        tracking=TrackingMethod.COMMIT_SHA,
        branch="main",
        destination="lua/proloot",
        zip_subdir="proloot",
        protected_patterns=["config/*"],
        enabled_key="proloot",
        show_version=True,
    ),
}
