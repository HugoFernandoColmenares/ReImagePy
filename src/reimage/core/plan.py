"""Build the rename plan and flag names that would collide."""

from __future__ import annotations

import os
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from reimage.core.scan import scan
from reimage.models import Plan, RenameItem, Settings

DUPLICATE = "duplicate target in batch"
OUTSIDE = "target exists outside the batch"


def name_key(name: str) -> str:
    """Compare names the way the host filesystem does."""

    if sys.platform in {"win32", "darwin"}:
        return name.casefold()
    return name


def collision_statuses(folder: Path, planned: Sequence[tuple[Path, str]]) -> list[str]:
    """Return `ok` or a collision reason for each planned target name."""

    batch = {name_key(source.name) for source, _target in planned}
    counts = Counter(name_key(target) for _source, target in planned)
    statuses: list[str] = []
    for source, target in planned:
        reasons: list[str] = []
        if counts[name_key(target)] > 1:
            reasons.append(DUPLICATE)
        destination = folder / target
        if os.path.lexists(destination) and not _same_entry(source, destination):
            if name_key(destination.name) not in batch:
                reasons.append(OUTSIDE)
        statuses.append("ok" if not reasons else "; ".join(reasons))
    return statuses


def build_plan(settings: Settings) -> Plan:
    scanned = scan(settings.folder, settings.extensions, settings.sort)
    targets = [
        f"{settings.prefix}{settings.separator}{settings.start + index:0{settings.width}d}{path.suffix}"
        for index, path in enumerate(scanned.files)
    ]
    pairs = list(zip(scanned.files, targets, strict=True))
    statuses = collision_statuses(settings.folder, pairs)
    items = tuple(
        RenameItem(source=source, target_name=target, status=status)
        for (source, target), status in zip(pairs, statuses, strict=True)
    )
    return Plan(folder=settings.folder, items=items, sort_label=scanned.sort_label)


def _same_entry(source: Path, destination: Path) -> bool:
    try:
        if source.exists() and destination.exists() and source.samefile(destination):
            return True
    except OSError:
        pass
    return name_key(source.name) == name_key(destination.name) and os.path.normcase(
        str(source.parent)
    ) == os.path.normcase(str(destination.parent))
