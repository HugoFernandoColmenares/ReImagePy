"""Rename through a temporary name and write the undo log."""

from __future__ import annotations

import uuid
from pathlib import Path

from reimage.core.plan import name_key
from reimage.models import ApplyResult, FileFailure, Plan
from reimage.storage import (
    data_root,
    empty_log,
    latest_log,
    read_log,
    undo_log_path,
    write_log,
)


def apply_plan(plan: Plan, *, root: Path | None = None) -> ApplyResult:
    """Rename every clean row. Collisions and empty plans are refused."""

    if not plan.can_apply:
        raise ValueError("The plan is empty or has collisions.")

    data = root or data_root()
    skipped = tuple(item.source for item in plan.items if _same_name(item.source, item.target_name))
    pending = [item for item in plan.items if item.source not in skipped]
    if not pending:
        return ApplyResult(renamed=(), skipped=skipped, failed=(), log_path=None)

    log_path = undo_log_path(plan.folder, data)
    payload = empty_log(plan.folder)
    # The log exists before the first move so a crash still points at this run.
    write_log(log_path, payload)

    staged: list[tuple[Path, Path, Path]] = []
    failed: list[FileFailure] = []
    for item in pending:
        source = item.source
        if not source.exists():
            failed.append(FileFailure(source, "file is missing"))
            continue
        temporary = _temporary_path(plan.folder)
        try:
            source.rename(temporary)
        except OSError as exc:
            failed.append(FileFailure(source, str(exc)))
            continue
        staged.append((source, temporary, item.target))

    renamed: list[tuple[Path, Path]] = []
    for source, temporary, final in staged:
        try:
            if final.exists():
                raise FileExistsError(f"{final.name} already exists")
            temporary.rename(final)
        except OSError as exc:
            restored = _restore(temporary, source)
            message = str(exc) if restored else f"{exc}; file left at {temporary.name}"
            failed.append(FileFailure(source, message))
            continue
        renamed.append((source, final))
        payload["moves"].append({"source": str(source), "destination": str(final)})
        write_log(log_path, payload)

    return ApplyResult(
        renamed=tuple(renamed),
        skipped=skipped,
        failed=tuple(failed),
        log_path=log_path,
    )


def undo(folder: Path | None = None, *, root: Path | None = None) -> ApplyResult:
    """Move the logged files back. `folder` selects the log; otherwise the latest log is used."""

    data = root or data_root()
    log_path = undo_log_path(folder, data) if folder is not None else latest_log(data)
    if log_path is None or not log_path.is_file():
        raise FileNotFoundError("No undo log for this folder.")

    payload = read_log(log_path)
    moves = [move for move in payload["moves"] if isinstance(move, dict)]
    if not moves:
        return ApplyResult(renamed=(), skipped=(), failed=(), log_path=log_path)

    staged: list[tuple[Path, Path, Path]] = []
    failed: list[FileFailure] = []
    for move in reversed(moves):
        destination = Path(str(move.get("destination", "")))
        source = Path(str(move.get("source", "")))
        if not destination.exists():
            failed.append(FileFailure(destination, "renamed file is missing"))
            continue
        temporary = _temporary_path(destination.parent)
        try:
            destination.rename(temporary)
        except OSError as exc:
            failed.append(FileFailure(destination, str(exc)))
            continue
        staged.append((destination, temporary, source))

    renamed: list[tuple[Path, Path]] = []
    for destination, temporary, source in staged:
        try:
            if source.exists() and not _same_file(temporary, source):
                raise FileExistsError(f"{source.name} already exists")
            temporary.rename(source)
        except OSError as exc:
            restored = _restore(temporary, destination)
            message = str(exc) if restored else f"{exc}; file left at {temporary.name}"
            failed.append(FileFailure(destination, message))
            continue
        renamed.append((destination, source))

    restored_destinations = {name_key(str(destination)) for destination, _source in renamed}
    remaining = [
        move
        for move in moves
        if name_key(str(move.get("destination", ""))) not in restored_destinations
    ]
    if remaining:
        payload["moves"] = remaining
        write_log(log_path, payload)
        kept: Path | None = log_path
    else:
        log_path.unlink(missing_ok=True)
        kept = None
    return ApplyResult(
        renamed=tuple(renamed),
        skipped=(),
        failed=tuple(failed),
        log_path=kept,
    )


def _same_name(source: Path, target_name: str) -> bool:
    return name_key(source.name) == name_key(target_name)


def _same_file(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except OSError:
        return False


def _restore(temporary: Path, original: Path) -> bool:
    try:
        if temporary.exists():
            temporary.rename(original)
        return original.exists()
    except OSError:
        return False


def _temporary_path(folder: Path) -> Path:
    while True:
        candidate = folder / f".reimage-{uuid.uuid4().hex}.tmp"
        if not candidate.exists():
            return candidate
