"""Textual application, screen flow, and the command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from textual.app import App
from textual.binding import Binding

from reimage.core.apply import apply_plan, undo
from reimage.core.plan import build_plan
from reimage.models import Draft, build_settings
from reimage.screens.setup import SetupScreen
from reimage.storage import touch_recent


class ReImageApp(App):
    """Collect settings, show the plan, and rename only after confirm."""

    TITLE = "ReImage"
    CSS = """
    #form {
        height: 1fr;
        padding: 1 2;
    }
    #sequence {
        height: auto;
    }
    #sequence Input {
        width: 1fr;
    }
    #extensions {
        height: auto;
    }
    #actions {
        dock: bottom;
        height: auto;
        padding: 0 2 1 2;
    }
    #folder-error, #prefix-error, #sequence-error {
        color: $error;
        height: auto;
    }
    #recents {
        height: 7;
    }
    DataTable {
        height: 1fr;
    }
    #meta, #summary {
        height: auto;
        padding: 0 2;
    }
    #summary {
        height: 1fr;
        padding: 1 2;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, folder: str = "", prefix: str = "") -> None:
        super().__init__()
        self.busy = False
        self.draft = Draft(folder=folder, prefix=prefix)

    def on_mount(self) -> None:
        self.push_screen(SetupScreen())

    def action_quit(self) -> None:
        if self.busy:
            self.notify("Wait until the rename finishes.", severity="warning")
            return
        self.exit()


def main(argv: list[str] | None = None) -> None:
    """Console-script entry. Exits with the status from `run`."""

    raise SystemExit(run(argv))


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.undo and (args.yes or args.dry_run):
        print("Choose either --undo or a rename.", file=sys.stderr)
        return 2
    if args.yes and args.dry_run:
        print("Choose either --yes or --dry-run.", file=sys.stderr)
        return 2
    if args.undo:
        return _undo(args)
    if args.yes or args.dry_run:
        return _headless(args, apply=args.yes)
    ReImageApp(folder=args.folder or "", prefix=args.prefix or "").run()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reimage",
        description="Rename images in a folder with a shared prefix and a numeric sequence.",
    )
    parser.add_argument("--folder", help="Folder that contains the images.")
    parser.add_argument("--prefix", help="Shared prefix for the new names.")
    parser.add_argument("--separator", default="_", help="Text between the prefix and the number.")
    parser.add_argument("--width", type=int, default=3, help="Digits in the number. Default: 3.")
    parser.add_argument("--start", type=int, default=1, help="First number. Default: 1.")
    parser.add_argument(
        "--sort",
        choices=["creation", "modification", "name"],
        default="creation",
        help="Order before numbering. Default: creation.",
    )
    parser.add_argument("--yes", action="store_true", help="Apply the default plan without the TUI.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan and write nothing.")
    parser.add_argument("--undo", action="store_true", help="Undo the last apply for this folder.")
    return parser


def _headless(args: argparse.Namespace, *, apply: bool) -> int:
    if not args.folder or not args.prefix:
        print("--folder and --prefix are required.", file=sys.stderr)
        return 2
    try:
        settings = build_settings(
            args.folder,
            args.prefix,
            separator=args.separator,
            width=args.width,
            start=args.start,
            sort=args.sort,
        )
        plan = build_plan(settings)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not apply or not plan.can_apply:
        for item in plan.items:
            line = f"{item.source.name} -> {item.target_name}"
            if not item.ok:
                line = f"{line}  {item.status}"
            print(line)
        if not apply:
            return 1 if plan.items and not plan.can_apply else 0
        print("Nothing was renamed.", file=sys.stderr)
        return 1
    touch_recent(settings.folder)
    result = apply_plan(plan)
    for source, destination in result.renamed:
        print(f"{source.name} -> {destination.name}")
    for failure in result.failed:
        print(f"{failure.path.name}: {failure.message}", file=sys.stderr)
    return 1 if result.failed else 0


def _undo(args: argparse.Namespace) -> int:
    folder = Path(args.folder).expanduser() if args.folder else None
    if folder is not None and not folder.is_dir():
        print("Folder does not exist.", file=sys.stderr)
        return 2
    try:
        result = undo(folder)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for destination, source in result.renamed:
        print(f"{destination.name} -> {source.name}")
    for failure in result.failed:
        print(f"{failure.path.name}: {failure.message}", file=sys.stderr)
    if not result.renamed and not result.failed:
        print("Nothing to undo.", file=sys.stderr)
        return 1
    return 1 if result.failed else 0
