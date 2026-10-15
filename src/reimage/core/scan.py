"""Discover images in one folder and read the clock used to sort them."""

from __future__ import annotations

import sys
from pathlib import Path

from reimage.models import ScanResult, SortMode

_TEMP_PREFIX = ".reimage-"


def clock_from_stat(st: object, mode: SortMode, platform: str, name: str) -> tuple[tuple, str]:
    """Return a sort key and the clock label for one file.

    Windows and macOS expose a birth time. On Linux that field is often
    missing, so creation order falls back to modification time and says so.
    """

    tie = name.casefold()
    if mode is SortMode.NAME:
        return ((tie,), "name")
    if mode is SortMode.MODIFICATION:
        return ((float(getattr(st, "st_mtime")), tie), "modification time")

    birth = getattr(st, "st_birthtime", None)
    if birth is not None:
        return ((float(birth), tie), "creation time")
    if platform == "win32":
        return ((float(getattr(st, "st_ctime")), tie), "creation time")
    return ((float(getattr(st, "st_mtime")), tie), "modification time (birth time unavailable)")


def scan(folder: Path, extensions: frozenset[str], sort: SortMode) -> ScanResult:
    """List matching images in `folder` without entering subfolders."""

    if not folder.is_dir():
        raise NotADirectoryError(f"Folder does not exist: {folder}")

    allowed = {extension.casefold() for extension in extensions}
    ranked: list[tuple[tuple, str, Path]] = []
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith(_TEMP_PREFIX):
            continue
        if entry.suffix.casefold() not in allowed:
            continue
        key, label = clock_from_stat(entry.stat(), sort, sys.platform, entry.name)
        ranked.append((key, label, entry))

    ranked.sort(key=lambda item: item[0])
    files = tuple(item[2] for item in ranked)
    return ScanResult(files=files, sort_label=_folder_label(sort, [item[1] for item in ranked]))


def _folder_label(sort: SortMode, labels: list[str]) -> str:
    if sort is SortMode.NAME:
        return "name"
    if sort is SortMode.MODIFICATION:
        return "modification time"
    if not labels:
        return "creation time"
    if any(label != "creation time" for label in labels):
        return "modification time (birth time unavailable)"
    return "creation time"
