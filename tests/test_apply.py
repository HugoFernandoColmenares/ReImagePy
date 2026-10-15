"""Safe apply and undo."""

from __future__ import annotations

import os
from pathlib import Path

from reimage.core.apply import apply_plan, undo
from reimage.core.plan import build_plan
from reimage.models import Settings, SortMode


def _plan(folder: Path, **overrides):
    values = {
        "folder": folder,
        "prefix": "vacation",
        "separator": "_",
        "width": 3,
        "start": 1,
        "sort": SortMode.NAME,
        "extensions": frozenset({".jpg"}),
    }
    values.update(overrides)
    return build_plan(Settings(**values))


def test_swap_uses_temporary_names_and_undo_restores(tmp_path: Path) -> None:
    older = tmp_path / "a_002.jpg"
    newer = tmp_path / "a_001.jpg"
    older.write_bytes(b"two")
    newer.write_bytes(b"one")
    os.utime(older, (1_000, 1_000))
    os.utime(newer, (2_000, 2_000))

    plan = _plan(tmp_path, prefix="a", sort=SortMode.MODIFICATION)
    result = apply_plan(plan)

    assert (tmp_path / "a_001.jpg").read_bytes() == b"two"
    assert (tmp_path / "a_002.jpg").read_bytes() == b"one"
    assert len(result.renamed) == 2

    restored = undo(tmp_path)

    assert (tmp_path / "a_001.jpg").read_bytes() == b"one"
    assert (tmp_path / "a_002.jpg").read_bytes() == b"two"
    assert len(restored.renamed) == 2
    assert restored.log_path is None


def test_missing_file_does_not_roll_back_a_finished_rename(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "b.jpg").write_bytes(b"b")
    plan = _plan(tmp_path)
    plan.items[1].source.unlink()

    result = apply_plan(plan)

    assert (tmp_path / "vacation_001.jpg").read_bytes() == b"a"
    assert [failure.path.name for failure in result.failed] == ["b.jpg"]

    undo(tmp_path)

    assert (tmp_path / "a.jpg").read_bytes() == b"a"
    assert not (tmp_path / "vacation_001.jpg").exists()


def test_apply_refuses_a_collision(tmp_path: Path) -> None:
    (tmp_path / "pic.jpg").write_bytes(b"x")
    (tmp_path / "vacation_001.jpg").mkdir()

    try:
        apply_plan(_plan(tmp_path))
    except ValueError as exc:
        assert "collision" in str(exc)
    else:
        raise AssertionError("apply_plan accepted a colliding plan")
