from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite


async def init_db(db_path: Path) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS installed_versions (
                component_id TEXT PRIMARY KEY,
                version      TEXT NOT NULL,
                installed_at TEXT NOT NULL
            )
        """)
        await conn.commit()


async def get_installed_version(db_path: Path, component_id: str) -> str | None:
    async with aiosqlite.connect(db_path) as conn:
        cur = await conn.execute(
            "SELECT version FROM installed_versions WHERE component_id = ?",
            (component_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def set_installed_version(
    db_path: Path, component_id: str, version: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """
            INSERT OR REPLACE INTO installed_versions (component_id, version, installed_at)
            VALUES (?, ?, ?)
            """,
            (component_id, version, now),
        )
        await conn.commit()


async def get_all_versions(db_path: Path) -> dict[str, str]:
    async with aiosqlite.connect(db_path) as conn:
        cur = await conn.execute(
            "SELECT component_id, version FROM installed_versions"
        )
        rows = await cur.fetchall()
        return {row[0]: row[1] for row in rows}
