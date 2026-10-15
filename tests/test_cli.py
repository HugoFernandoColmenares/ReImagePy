"""Headless commands and recent folders."""

from __future__ import annotations

from pathlib import Path

import pytest

from reimage.app import run
from reimage.storage import load_recent_folders, touch_recent


def test_dry_run_prints_the_plan_and_leaves_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "photo.JPG").write_bytes(b"x")

    code = run(["--folder", str(tmp_path), "--prefix", "vacation", "--dry-run", "--sort", "name"])

    assert code == 0
    assert capsys.readouterr().out.strip() == "photo.JPG -> vacation_001.JPG"
    assert (tmp_path / "photo.JPG").exists()


def test_yes_renames_and_undo_restores(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"x")

    code = run(["--folder", str(tmp_path), "--prefix", "vacation", "--yes", "--sort", "name"])

    assert code == 0
    assert capsys.readouterr().out.strip() == "photo.jpg -> vacation_001.jpg"
    assert (tmp_path / "vacation_001.jpg").read_bytes() == b"x"

    undo_code = run(["--undo", "--folder", str(tmp_path)])

    assert undo_code == 0
    assert capsys.readouterr().out.strip() == "vacation_001.jpg -> photo.jpg"
    assert (tmp_path / "photo.jpg").exists()


def test_yes_reports_a_collision_without_moving(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "pic.jpg").write_bytes(b"x")
    (tmp_path / "vacation_001.jpg").mkdir()

    code = run(["--folder", str(tmp_path), "--prefix", "vacation", "--yes", "--sort", "name"])

    captured = capsys.readouterr()
    assert code == 1
    assert "target exists outside the batch" in captured.out
    assert (tmp_path / "pic.jpg").is_file()


def test_recent_folders_keep_the_last_five(tmp_path: Path) -> None:
    folders = []
    for index in range(6):
        folder = tmp_path / f"album-{index}"
        folder.mkdir()
        folders.append(folder)
        touch_recent(folder)

    stored = load_recent_folders()

    assert stored == [str(folder.resolve()) for folder in reversed(folders[-5:])]
    touch_recent(folders[1])
    assert load_recent_folders()[0] == str(folders[1].resolve())
    assert len(load_recent_folders()) == 5
