"""Keep tests away from the real per-user data directory."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reimage_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "reimage-data"
    root.mkdir()
    monkeypatch.setenv("REIMAGE_DATA_DIR", str(root))
    return root
