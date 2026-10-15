"""Preview screen: current name, new name, and collision status."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from reimage.core.apply import apply_plan
from reimage.models import Plan
from reimage.screens.result import ResultScreen


class PreviewScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("enter", "apply", "Apply"),
    ]

    def __init__(self, plan: Plan) -> None:
        super().__init__()
        self.plan = plan

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="plan")
        count = len(self.plan.items)
        noun = "file" if count == 1 else "files"
        yield Static(f"{count} {noun} · {self.plan.sort_label}", id="meta")
        with Horizontal(id="actions"):
            yield Button("Apply", id="apply", variant="primary", disabled=not self.plan.can_apply)
            yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#plan", DataTable)
        table.add_columns("Current name", "New name", "Status")
        for item in self.plan.items:
            table.add_row(item.source.name, item.target_name, item.status)
        self.sub_title = self.plan.sort_label
        if self.plan.can_apply:
            self.query_one("#apply", Button).focus()
        else:
            self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            self.action_apply()
        elif event.button.id == "back":
            self.action_back()

    def action_back(self) -> None:
        if self.app.busy:
            return
        self.app.pop_screen()

    def action_apply(self) -> None:
        if self.app.busy or not self.plan.can_apply:
            return
        self.app.busy = True
        self.query_one("#apply", Button).disabled = True
        self.query_one("#back", Button).disabled = True
        self.run_worker(self._apply(), exclusive=True)

    async def _apply(self) -> None:
        try:
            result = await asyncio.to_thread(apply_plan, self.plan)
        except Exception as exc:  # shown on the result path; keep the screen usable
            self.app.busy = False
            self.query_one("#back", Button).disabled = False
            self.notify(str(exc), severity="error")
            return
        self.app.busy = False
        folder = self.plan.folder
        self.app.pop_screen()
        self.app.push_screen(ResultScreen(result, folder))
