"""Rename plans and collision rules."""

from __future__ import annotations

from pathlib import Path

from reimage.core.plan import DUPLICATE, OUTSIDE, build_plan, collision_statuses
from reimage.models import Settings, SortMode


def _settings(folder: Path, **overrides) -> Settings:
    values = {
        "folder": folder,
        "prefix": "vacation",
        "separator": "_",
        "width": 3,
        "start": 1,
        "sort": SortMode.NAME,
        "extensions": frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}),
    }
    values.update(overrides)
    return Settings(**values)


def test_default_names_keep_extension_case(tmp_path: Path) -> None:
    (tmp_path / "b.JPG").write_bytes(b"b")
    (tmp_path / "a.png").write_bytes(b"a")

    plan = build_plan(_settings(tmp_path))

    assert [(item.source.name, item.target_name, item.status) for item in plan.items] == [
        ("a.png", "vacation_001.png", "ok"),
        ("b.JPG", "vacation_002.JPG", "ok"),
    ]
    assert plan.can_apply


def test_custom_sequence(tmp_path: Path) -> None:
    (tmp_path / "shot.jpeg").write_bytes(b"x")

    plan = build_plan(_settings(tmp_path, prefix="trip", separator="-", width=2, start=5))

    assert plan.items[0].target_name == "trip-05.jpeg"


def test_directory_blocking_the_target_is_a_collision(tmp_path: Path) -> None:
    (tmp_path / "pic.jpg").write_bytes(b"x")
    (tmp_path / "vacation_001.jpg").mkdir()

    plan = build_plan(_settings(tmp_path))

    assert plan.items[0].status == OUTSIDE
    assert not plan.can_apply


def test_duplicate_targets_and_batch_occupants(tmp_path: Path) -> None:
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    first.write_bytes(b"a")
    second.write_bytes(b"b")

    duplicate = collision_statuses(tmp_path, [(first, "same.jpg"), (second, "same.jpg")])
    handover = collision_statuses(tmp_path, [(first, "b.jpg"), (second, "c.jpg")])
    same = collision_statuses(tmp_path, [(first, "a.jpg")])

    assert duplicate == [DUPLICATE, DUPLICATE]
    assert handover == ["ok", "ok"]
    assert same == ["ok"]
