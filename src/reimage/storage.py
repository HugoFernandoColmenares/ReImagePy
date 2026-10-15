"""Per-user settings and one undo log per folder."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import platformdirs

RECENT_LIMIT = 5


def data_root() -> Path:
    override = os.environ.get("REIMAGE_DATA_DIR")
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir("reimage", appauthor=False))


def _settings_path(root: Path | None = None) -> Path:
    return (root or data_root()) / "settings.json"


def _undo_dir(root: Path | None = None) -> Path:
    return (root or data_root()) / "undo"


def folder_key(folder: Path) -> str:
    text = os.path.normcase(str(folder.expanduser().resolve()))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def undo_log_path(folder: Path, root: Path | None = None) -> Path:
    return _undo_dir(root) / f"{folder_key(folder)}.json"


def load_recent_folders(root: Path | None = None) -> list[str]:
    path = _settings_path(root)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    folders = payload.get("recent_folders", [])
    if not isinstance(folders, list):
        return []
    return [item for item in folders if isinstance(item, str)][:RECENT_LIMIT]


def touch_recent(folder: Path, root: Path | None = None) -> list[str]:
    text = str(folder.expanduser().resolve())
    key = os.path.normcase(text)
    kept = [item for item in load_recent_folders(root) if os.path.normcase(item) != key]
    updated = [text, *kept][:RECENT_LIMIT]
    path = _settings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, {"recent_folders": updated})
    return updated


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def empty_log(folder: Path) -> dict:
    return {
        "folder": str(folder.expanduser().resolve()),
        "updated": _now(),
        "moves": [],
    }


def write_log(path: Path, payload: dict) -> None:
    payload["updated"] = _now()
    _write_json(path, payload)


def read_log(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("moves"), list):
        raise ValueError(f"Undo log is unreadable: {path}")
    return payload


def latest_log(root: Path | None = None) -> Path | None:
    directory = _undo_dir(root)
    if not directory.is_dir():
        return None
    files = [path for path in directory.glob("*.json") if path.is_file()]
    if not files:
        return None

    def stamp(path: Path) -> str:
        try:
            payload = read_log(path)
        except (OSError, json.JSONDecodeError, ValueError):
            return ""
        updated = payload.get("updated", "")
        return updated if isinstance(updated, str) else ""

    return max(files, key=lambda path: (stamp(path), path.stat().st_mtime))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
