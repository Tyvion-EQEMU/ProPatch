from __future__ import annotations

import sys

import httpx

from profetch.components import Component, EqFile, TrackingMethod

MANIFEST_URL = (
    "https://raw.githubusercontent.com/Tyvion-EQEMU/profetch-manifest/main/manifest.toml"
)


def _load_toml(text: str) -> dict:
    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore[import]
        return tomllib.loads(text)
    import tomli  # type: ignore[import]
    return tomli.loads(text)


def _parse_component(d: dict) -> Component:
    return Component(
        id=d["id"],
        name=d["name"],
        owner=d["owner"],
        repo=d["repo"],
        tracking=TrackingMethod(d["tracking"]),
        destination=d.get("destination", ""),
        protected_patterns=d.get("protected_patterns", []),
        enabled_key=d["id"],
        branch=d.get("branch"),
        release_asset_name=d.get("release_asset_name"),
        zip_subdir=d.get("zip_subdir"),
    )


def _parse_eq_file(d: dict) -> EqFile:
    tracking_str = d.get("tracking")
    return EqFile(
        id=d["id"],
        name=d["name"],
        filename=d.get("filename", ""),
        url=d.get("url", ""),
        destination=d.get("destination", ""),
        owner=d.get("owner"),
        repo=d.get("repo"),
        branch=d.get("branch"),
        tracking=TrackingMethod(tracking_str) if tracking_str else None,
        extract=d.get("extract", False),
    )


def _parse_help_pack(d: dict) -> EqFile:
    return EqFile(
        id=d["id"],
        name=d["name"],
        filename="",
        url="",
        destination=d.get("destination", "help"),
        owner=d["owner"],
        repo=d["repo"],
        branch=d.get("branch", "main"),
        tracking=TrackingMethod(d.get("tracking", "commit_sha")),
        extract=True,
    )


async def fetch_manifest(
    client: httpx.AsyncClient,
) -> tuple[list[Component], list[EqFile]]:
    r = await client.get(MANIFEST_URL, follow_redirects=True)
    r.raise_for_status()
    data = _load_toml(r.text)

    components = [_parse_component(c) for c in data.get("components", [])]
    eq_files = [_parse_eq_file(f) for f in data.get("eq_files", [])]
    help_packs = [_parse_help_pack(h) for h in data.get("help_packs", [])]

    return components, eq_files + help_packs
