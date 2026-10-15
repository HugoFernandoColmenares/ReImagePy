"""Settings, scan results, rename plans, and apply results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_EXTENSIONS: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
)
ILLEGAL_FILENAME_CHARS = frozenset('\\/:*?"<>|')


class SortMode(str, Enum):
    CREATION = "creation"
    MODIFICATION = "modification"
    NAME = "name"


@dataclass
class Draft:
    """Field values remembered while the user moves between screens."""

    folder: str = ""
    prefix: str = ""
    separator: str = "_"
    width: str = "3"
    start: str = "1"
    sort: str = SortMode.CREATION.value
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS


@dataclass(frozen=True)
class Settings:
    folder: Path
    prefix: str
    separator: str = "_"
    width: int = 3
    start: int = 1
    sort: SortMode = SortMode.CREATION
    extensions: frozenset[str] = frozenset(DEFAULT_EXTENSIONS)


@dataclass(frozen=True)
class ScanResult:
    files: tuple[Path, ...]
    sort_label: str


@dataclass(frozen=True)
class RenameItem:
    source: Path
    target_name: str
    status: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    @property
    def target(self) -> Path:
        return self.source.parent / self.target_name


@dataclass(frozen=True)
class Plan:
    folder: Path
    items: tuple[RenameItem, ...]
    sort_label: str

    @property
    def can_apply(self) -> bool:
        return bool(self.items) and all(item.ok for item in self.items)


@dataclass(frozen=True)
class FileFailure:
    path: Path
    message: str


@dataclass(frozen=True)
class ApplyResult:
    renamed: tuple[tuple[Path, Path], ...]
    skipped: tuple[Path, ...]
    failed: tuple[FileFailure, ...]
    log_path: Path | None


def normalize_extensions(values: tuple[str, ...] | list[str] | frozenset[str]) -> frozenset[str]:
    normalized: set[str] = set()
    for value in values:
        extension = value if value.startswith(".") else f".{value}"
        normalized.add(extension.casefold())
    return frozenset(normalized)


def parse_sort(value: str) -> SortMode:
    try:
        return SortMode(value)
    except ValueError as exc:
        raise ValueError("Sort must be creation, modification, or name.") from exc


def folder_error(text: str) -> str | None:
    raw = text.strip().strip('"').strip("'")
    if not raw:
        return "Folder is required."
    path = Path(raw).expanduser()
    if not path.is_dir():
        return "Folder does not exist."
    return None


def prefix_error(text: str) -> str | None:
    cleaned = text.strip()
    if not cleaned:
        return "Prefix is required."
    illegal = sorted({char for char in cleaned if char in ILLEGAL_FILENAME_CHARS})
    if illegal:
        return "Prefix contains illegal characters: " + " ".join(illegal)
    return None


def separator_error(text: str) -> str | None:
    illegal = sorted({char for char in text if char in ILLEGAL_FILENAME_CHARS})
    if illegal:
        return "Separator contains illegal characters: " + " ".join(illegal)
    return None


def _positive_int(text: str, label: str, minimum: int) -> int:
    raw = text.strip() if isinstance(text, str) else str(text)
    if not raw.isdigit():
        raise ValueError(f"{label} must be an integer of at least {minimum}.")
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{label} must be an integer of at least {minimum}.")
    return value


def build_settings(
    folder: str,
    prefix: str,
    *,
    separator: str = "_",
    width: str | int = 3,
    start: str | int = 1,
    sort: SortMode | str = SortMode.CREATION,
    extensions: tuple[str, ...] | list[str] | frozenset[str] = DEFAULT_EXTENSIONS,
) -> Settings:
    """Validate a form or command line and return settings for the pipeline."""

    folder_problem = folder_error(folder)
    if folder_problem:
        raise ValueError(folder_problem)
    prefix_problem = prefix_error(prefix)
    if prefix_problem:
        raise ValueError(prefix_problem)
    separator_problem = separator_error(separator)
    if separator_problem:
        raise ValueError(separator_problem)
    parsed_width = _positive_int(str(width), "Width", 1)
    parsed_start = _positive_int(str(start), "Start", 0)
    parsed_sort = sort if isinstance(sort, SortMode) else parse_sort(sort)
    parsed_extensions = normalize_extensions(extensions)
    if not parsed_extensions:
        raise ValueError("Select at least one extension.")
    return Settings(
        folder=Path(folder.strip().strip('"').strip("'")).expanduser(),
        prefix=prefix.strip(),
        separator=separator,
        width=parsed_width,
        start=parsed_start,
        sort=parsed_sort,
        extensions=parsed_extensions,
    )
