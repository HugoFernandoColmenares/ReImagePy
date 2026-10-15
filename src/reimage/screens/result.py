"""Result screen: renamed, skipped, failed, and undo."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from reimage.core.apply import undo
from reimage.models import ApplyResult


class ResultScreen(Screen):
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("u", "undo", "Undo"),
    ]

    def __init__(self, result: ApplyResult, folder: Path, *, noun: str = "Renamed") -> None:
        super().__init__()
        self.result = result
        self.folder = folder
        self.noun = noun

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="summary"):
            yield Static("", id="summary-text")
        with Horizontal(id="actions"):
            yield Button("Undo", id="undo", disabled=not _can_undo(self.result))
            yield Button("Close", id="close", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self._render_summary()
        self.query_one("#close", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "undo":
            self.action_undo()
        elif event.button.id == "close":
            self.action_close()

    def action_close(self) -> None:
        if self.app.busy:
            return
        self.app.pop_screen()

    def action_undo(self) -> None:
        if self.app.busy or not _can_undo(self.result):
            if not self.app.busy and not _can_undo(self.result):
                self.notify("Nothing to undo.", severity="warning")
            return
        self.app.busy = True
        self.query_one("#undo", Button).disabled = True
        self.query_one("#close", Button).disabled = True
        self.run_worker(self._undo(), exclusive=True)

    async def _undo(self) -> None:
        try:
            result = await asyncio.to_thread(undo, self.folder)
        except Exception as exc:
            self.app.busy = False
            self.query_one("#close", Button).disabled = False
            self.notify(str(exc), severity="error")
            return
        self.result = result
        self.noun = "Restored"
        self.app.busy = False
        self._render_summary()
        self.query_one("#undo", Button).disabled = True
        self.query_one("#close", Button).disabled = False
        self.query_one("#close", Button).focus()

    def _render_summary(self) -> None:
        lines = [
            f"{self.noun}: {len(self.result.renamed)}",
            f"Skipped: {len(self.result.skipped)}",
            f"Failed: {len(self.result.failed)}",
        ]
        lines.extend(f"{failure.path.name}: {failure.message}" for failure in self.result.failed)
        lines.extend(f"{source.name} -> {destination.name}" for source, destination in self.result.renamed)
        self.query_one("#summary-text", Static).update("\n".join(lines))


def _can_undo(result: ApplyResult) -> bool:
    return bool(result.renamed) and result.log_path is not None
