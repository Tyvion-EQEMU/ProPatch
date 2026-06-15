from __future__ import annotations

import shutil
import zipfile
from fnmatch import fnmatch
from pathlib import Path


def _is_protected(relative_path: str, patterns: list[str]) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(fnmatch(normalized, p) for p in patterns)


def extract_zip(
    zip_path: Path,
    dest_root: Path,
    protected_patterns: list[str],
    zip_subdir: str | None = None,
) -> tuple[int, int]:
    """
    Extract a GitHub branch zip into dest_root, skipping protected files.

    GitHub zips always have one top-level folder (repo-branch/) that is
    stripped first. If zip_subdir is given, only files under that subdirectory
    are extracted and its prefix is also stripped.
    Returns (files_written, files_skipped).
    """
    written = skipped = 0
    subdir_prefix = (zip_subdir.rstrip("/") + "/") if zip_subdir else None

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        if not members:
            return 0, 0

        prefix = members[0].split("/")[0] + "/"

        for member in members:
            relative = member[len(prefix):] if member.startswith(prefix) else member
            if not relative:
                continue

            if subdir_prefix:
                if not relative.startswith(subdir_prefix):
                    continue
                relative = relative[len(subdir_prefix):]
                if not relative:
                    continue

            target = dest_root / relative

            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue

            if _is_protected(relative, protected_patterns) and target.exists():
                skipped += 1
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            written += 1

    return written, skipped


def install_single_file(
    src: Path,
    dest_dir: Path,
    protected_patterns: list[str],
) -> bool:
    """Copy src into dest_dir. Returns False if the file is protected."""
    if _is_protected(src.name, protected_patterns):
        return False
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_dir / src.name)
    return True


def install_eq_file(src: Path, eq_dirs: list[Path], destination: str) -> int:
    """Copy a single file into destination subfolder of each EQ directory. Returns count installed."""
    count = 0
    for eq_dir in eq_dirs:
        dest = (eq_dir / destination) if destination else eq_dir
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest / src.name)
        count += 1
    return count


def extract_zip_to_eq_dirs(
    zip_path: Path,
    eq_dirs: list[Path],
    destination: str,
) -> tuple[int, int]:
    """Extract a plain zip (no top-level prefix stripping) into destination under each EQ dir."""
    total_written = total_dirs = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        if not members:
            return 0, 0
        # Strip the GitHub top-level folder (repo-branch/)
        prefix = members[0].split("/")[0] + "/"
        for eq_dir in eq_dirs:
            dest_root = (eq_dir / destination) if destination else eq_dir
            for member in members:
                relative = member[len(prefix):] if member.startswith(prefix) else member
                if not relative:
                    continue
                target = dest_root / relative
                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    total_dirs += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                total_written += 1
    return total_written, total_dirs
