"""Setup screen: folder, prefix, sequence, sort, and extensions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, OptionList, Select, Static
from textual.widgets.option_list import Option

from reimage.core.plan import build_plan
from reimage.models import (
    DEFAULT_EXTENSIONS,
    Draft,
    SortMode,
    build_settings,
    folder_error,
    prefix_error,
    separator_error,
)
from reimage.screens.preview import PreviewScreen
from reimage.storage import load_recent_folders, touch_recent

_EMPTY_RECENTS = "No recent folders"


class SetupScreen(Screen):
    BINDINGS = [
        Binding("p", "preview", "Preview"),
        Binding("u", "undo", "Undo", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="form"):
            yield Label("Folder")
            yield Input(placeholder="Paste a folder path", id="folder")
            yield Static("", id="folder-error")
            yield Label("Recent folders")
            yield OptionList(id="recents")
            yield Label("Prefix")
            yield Input(
                placeholder="vacation",
                id="prefix",
                restrict=r'[^\\/:*?"<>|]*',
            )
            yield Static("", id="prefix-error")
            yield Label("Separator, width, and start")
            with Horizontal(id="sequence"):
                yield Input(placeholder="Separator", id="separator")
                yield Input(placeholder="Width", id="width", restrict=r"[0-9]*")
                yield Input(placeholder="Start", id="start", restrict=r"[0-9]*")
            yield Static("", id="sequence-error")
            yield Label("Sort")
            yield Select(
                [
                    ("Creation time", SortMode.CREATION.value),
                    ("Modification time", SortMode.MODIFICATION.value),
                    ("Name", SortMode.NAME.value),
                ],
                value=SortMode.CREATION.value,
                allow_blank=False,
                id="sort",
            )
            yield Label("Extensions")
            with Horizontal(id="extensions"):
                for extension in DEFAULT_EXTENSIONS:
                    yield Checkbox(extension, value=True, id=_extension_id(extension))
        with Horizontal(id="actions"):
            yield Button("Preview", id="preview", variant="primary", disabled=True)
            yield Button("Quit", id="quit")
        yield Footer()

    def on_mount(self) -> None:
        draft: Draft = self.app.draft
        self.query_one("#folder", Input).value = draft.folder
        self.query_one("#prefix", Input).value = draft.prefix
        self.query_one("#separator", Input).value = draft.separator
        self.query_one("#width", Input).value = draft.width
        self.query_one("#start", Input).value = draft.start
        self.query_one("#sort", Select).value = draft.sort
        selected = set(draft.extensions)
        for extension in DEFAULT_EXTENSIONS:
            self.query_one(f"#{_extension_id(extension)}", Checkbox).value = extension in selected
        self._reload_recents()
        self._sync()

    def on_screen_resume(self) -> None:
        self._reload_recents()

    def on_input_changed(self, _event: Input.Changed) -> None:
        self._sync()

    def on_checkbox_changed(self, _event: Checkbox.Changed) -> None:
        self._sync()

    def on_select_changed(self, _event: Select.Changed) -> None:
        self._sync()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        choice = str(event.option.prompt)
        if choice == _EMPTY_RECENTS:
            return
        self.query_one("#folder", Input).value = choice
        self._sync()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "preview":
            self.action_preview()
        elif event.button.id == "quit":
            self.app.action_quit()

    def action_preview(self) -> None:
        if self.app.busy:
            return
        try:
            settings = self._settings()
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        try:
            plan = build_plan(settings)
        except OSError as exc:
            self.notify(str(exc), severity="error")
            return
        self._save_draft()
        touch_recent(settings.folder)
        self.app.push_screen(PreviewScreen(plan))

    def action_undo(self) -> None:
        from reimage.core.apply import undo
        from reimage.screens.result import ResultScreen

        if self.app.busy:
            return
        folder_text = self.query_one("#folder", Input).value
        if folder_error(folder_text):
            self.notify("Choose a folder before undoing.", severity="warning")
            return
        settings = self._settings_or_none()
        folder = None if settings is None else settings.folder
        if folder is None:
            from pathlib import Path

            folder = Path(folder_text.strip().strip('"').strip("'")).expanduser()
        try:
            result = undo(folder)
        except FileNotFoundError as exc:
            self.notify(str(exc), severity="warning")
            return
        except (OSError, ValueError) as exc:
            self.notify(str(exc), severity="error")
            return
        self.app.push_screen(ResultScreen(result, folder, noun="Restored"))

    def _settings(self):
        self._save_draft()
        draft: Draft = self.app.draft
        return build_settings(
            draft.folder,
            draft.prefix,
            separator=draft.separator,
            width=draft.width,
            start=draft.start,
            sort=draft.sort,
            extensions=self._selected_extensions(),
        )

    def _settings_or_none(self):
        try:
            return self._settings()
        except ValueError:
            return None

    def _save_draft(self) -> None:
        draft: Draft = self.app.draft
        draft.folder = self.query_one("#folder", Input).value
        draft.prefix = self.query_one("#prefix", Input).value
        draft.separator = self.query_one("#separator", Input).value
        draft.width = self.query_one("#width", Input).value
        draft.start = self.query_one("#start", Input).value
        sort_value = self.query_one("#sort", Select).value
        draft.sort = str(sort_value)
        draft.extensions = tuple(self._selected_extensions())

    def _selected_extensions(self) -> list[str]:
        selected: list[str] = []
        for extension in DEFAULT_EXTENSIONS:
            if self.query_one(f"#{_extension_id(extension)}", Checkbox).value:
                selected.append(extension)
        return selected

    def _reload_recents(self) -> None:
        widget = self.query_one("#recents", OptionList)
        widget.clear_options()
        folders = load_recent_folders()
        if not folders:
            widget.add_option(Option(_EMPTY_RECENTS, disabled=True))
            return
        for folder in folders:
            widget.add_option(Option(folder))

    def _sync(self) -> None:
        folder_text = self.query_one("#folder", Input).value
        prefix_text = self.query_one("#prefix", Input).value
        separator_text = self.query_one("#separator", Input).value
        folder_problem = folder_error(folder_text)
        prefix_problem = prefix_error(prefix_text)
        separator_problem = separator_error(separator_text)
        width_problem = _number_problem(self.query_one("#width", Input).value, "Width", 1)
        start_problem = _number_problem(self.query_one("#start", Input).value, "Start", 0)
        sequence_problem = separator_problem or width_problem or start_problem
        self.query_one("#folder-error", Static).update(folder_problem or "")
        self.query_one("#prefix-error", Static).update(prefix_problem or "")
        self.query_one("#sequence-error", Static).update(sequence_problem or "")
        ready = (
            folder_problem is None
            and prefix_problem is None
            and sequence_problem is None
            and bool(self._selected_extensions())
        )
        self.query_one("#preview", Button).disabled = not ready


def _extension_id(extension: str) -> str:
    return f"ext-{extension[1:]}"


def _number_problem(text: str, label: str, minimum: int) -> str | None:
    raw = text.strip()
    if not raw.isdigit() or int(raw) < minimum:
        return f"{label} must be an integer of at least {minimum}."
    return None
