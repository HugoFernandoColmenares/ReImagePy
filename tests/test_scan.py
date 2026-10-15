"""Scan filters, clocks, and sort order."""

from __future__ import annotations

import os
from pathlib import Path

from reimage.core.scan import clock_from_stat, scan
from reimage.models import SortMode


def _touch(path: Path, stamp: int | None = None) -> Path:
    path.write_bytes(b"img")
    if stamp is not None:
        os.utime(path, (stamp, stamp))
    return path


def test_scan_keeps_images_and_skips_the_rest(tmp_path: Path) -> None:
    _touch(tmp_path / "photo.JPG")
    _touch(tmp_path / "anim.GIF")
    _touch(tmp_path / "notes.txt")
    nested = tmp_path / "album"
    nested.mkdir()
    _touch(nested / "hidden.png")
    _touch(tmp_path / ".reimage-crash.jpg")

    result = scan(tmp_path, frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}), SortMode.NAME)

    assert [path.name for path in result.files] == ["anim.GIF", "photo.JPG"]
    assert result.sort_label == "name"


def test_scan_orders_by_modification_time(tmp_path: Path) -> None:
    newer = _touch(tmp_path / "newer.png", 2_000)
    older = _touch(tmp_path / "older.png", 1_000)

    result = scan(tmp_path, frozenset({".png"}), SortMode.MODIFICATION)

    assert list(result.files) == [older, newer]
    assert result.sort_label == "modification time"


def test_scan_orders_by_injected_creation_clock(tmp_path: Path, monkeypatch) -> None:
    _touch(tmp_path / "a.jpg")
    _touch(tmp_path / "b.jpg")

    def fake(st: object, mode: SortMode, platform: str, name: str) -> tuple[tuple, str]:
        return (({"b.jpg": 1, "a.jpg": 2}[name], name), "creation time")

    monkeypatch.setattr("reimage.core.scan.clock_from_stat", fake)
    result = scan(tmp_path, frozenset({".jpg"}), SortMode.CREATION)

    assert [path.name for path in result.files] == ["b.jpg", "a.jpg"]
    assert result.sort_label == "creation time"


def test_creation_clock_uses_birth_time_or_platform_fallback() -> None:
    class Birth:
        st_birthtime = 3.0
        st_mtime = 5.0
        st_ctime = 9.0

    class NoBirth:
        st_birthtime = None
        st_mtime = 5.0
        st_ctime = 9.0

    birth_key, birth_label = clock_from_stat(Birth(), SortMode.CREATION, "linux", "a.jpg")
    linux_key, linux_label = clock_from_stat(NoBirth(), SortMode.CREATION, "linux", "a.jpg")
    windows_key, windows_label = clock_from_stat(NoBirth(), SortMode.CREATION, "win32", "a.jpg")

    assert birth_key[0] == 3.0 and birth_label == "creation time"
    assert linux_key[0] == 5.0 and linux_label == "modification time (birth time unavailable)"
    assert windows_key[0] == 9.0 and windows_label == "creation time"


def test_missing_birth_time_changes_the_folder_label(tmp_path: Path, monkeypatch) -> None:
    _touch(tmp_path / "a.jpg")

    def fake(st: object, mode: SortMode, platform: str, name: str) -> tuple[tuple, str]:
        return ((1.0, name), "modification time (birth time unavailable)")

    monkeypatch.setattr("reimage.core.scan.clock_from_stat", fake)
    result = scan(tmp_path, frozenset({".jpg"}), SortMode.CREATION)

    assert result.sort_label == "modification time (birth time unavailable)"
