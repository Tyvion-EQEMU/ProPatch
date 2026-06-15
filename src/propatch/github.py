from __future__ import annotations

from pathlib import Path

import httpx

GITHUB_API = "https://api.github.com"
_HEADERS = {"Accept": "application/vnd.github.v3+json"}


def auth_headers(token: str | None = None) -> dict:
    h = dict(_HEADERS)
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _raise_for_status(r) -> None:
    if r.status_code == 403:
        body = r.text.lower()
        if "rate limit" in body or "rate limit" in r.headers.get("x-ratelimit-remaining", ""):
            raise RuntimeError(
                "GitHub API rate limit exceeded. Add a github_token to settings.local.toml "
                "to raise the limit from 60 to 5000 requests/hour."
            )
    r.raise_for_status()


async def get_latest_commit_sha(
    client: httpx.AsyncClient, owner: str, repo: str, branch: str = "main"
) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}"
    r = await client.get(url, headers=_HEADERS)
    _raise_for_status(r)
    return r.json()["sha"]


async def get_latest_release(
    client: httpx.AsyncClient, owner: str, repo: str
) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest"
    r = await client.get(url, headers=_HEADERS)
    _raise_for_status(r)
    return r.json()


async def get_latest_tag(
    client: httpx.AsyncClient, owner: str, repo: str
) -> str | None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/tags"
    r = await client.get(url, headers=_HEADERS)
    _raise_for_status(r)
    tags = r.json()
    return tags[0]["name"] if tags else None


async def get_latest_version_tag(
    client: httpx.AsyncClient, owner: str, repo: str
) -> str | None:
    """Try the releases API first (human-published); fall back to git tags."""
    try:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest"
        r = await client.get(url, headers=_HEADERS)
        if r.status_code == 200:
            return r.json()["tag_name"]
        _raise_for_status(r)
    except Exception:
        pass
    try:
        return await get_latest_tag(client, owner, repo)
    except Exception:
        return None


def find_release_asset_url(release: dict, filename: str) -> str | None:
    for asset in release.get("assets", []):
        if asset["name"] == filename:
            return asset["browser_download_url"]
    return None


async def download_tag_zip(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    tag: str,
    dest: Path,
) -> Path:
    url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.zip"
    async with client.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            async for chunk in r.aiter_bytes(chunk_size=65536):
                f.write(chunk)
    return dest


async def download_zip(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    branch: str,
    dest: Path,
) -> Path:
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    async with client.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            async for chunk in r.aiter_bytes(chunk_size=65536):
                f.write(chunk)
    return dest


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
) -> Path:
    async with client.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            async for chunk in r.aiter_bytes(chunk_size=65536):
                f.write(chunk)
    return dest
