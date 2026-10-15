"""The TUI reaches a preview and refuses to quit mid-rename."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import Button, DataTable

from reimage.app import ReImageApp


def test_preview_lists_the_new_name_and_escape_returns(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"x")
    app = ReImageApp()

    async def body() -> None:
        async with app.run_test(size=(100, 36)) as pilot:
            folder = app.screen.query_one("#folder")
            prefix = app.screen.query_one("#prefix")
            folder.value = str(tmp_path)
            prefix.value = "vacation"
            await pilot.pause()
            await pilot.click("#preview")
            await pilot.pause()
            table = app.screen.query_one(DataTable)
            assert list(table.get_row_at(0)) == ["photo.jpg", "vacation_001.jpg", "ok"]
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen.query_one("#prefix").value == "vacation"

    asyncio.run(body())


def test_collision_disables_apply(tmp_path: Path) -> None:
    (tmp_path / "pic.jpg").write_bytes(b"x")
    (tmp_path / "vacation_001.jpg").mkdir()
    app = ReImageApp()

    async def body() -> None:
        async with app.run_test(size=(100, 36)) as pilot:
            app.screen.query_one("#folder").value = str(tmp_path)
            app.screen.query_one("#prefix").value = "vacation"
            await pilot.pause()
            await pilot.click("#preview")
            await pilot.pause()
            row = list(app.screen.query_one(DataTable).get_row_at(0))
            assert row[2] == "target exists outside the batch"
            assert app.screen.query_one("#apply", Button).disabled

    asyncio.run(body())


def test_apply_from_the_preview(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"x")
    app = ReImageApp()

    async def body() -> None:
        async with app.run_test(size=(100, 36)) as pilot:
            app.screen.query_one("#folder").value = str(tmp_path)
            app.screen.query_one("#prefix").value = "vacation"
            await pilot.pause()
            await pilot.click("#preview")
            await pilot.pause()
            await pilot.click("#apply")
            for _ in range(30):
                await pilot.pause()
                if (tmp_path / "vacation_001.jpg").exists():
                    break
            assert (tmp_path / "vacation_001.jpg").read_bytes() == b"x"
            assert app.screen.__class__.__name__ == "ResultScreen"
            assert len(app.screen.result.renamed) == 1

    asyncio.run(body())


def test_quit_waits_while_a_rename_is_running(tmp_path: Path) -> None:
    app = ReImageApp()

    async def body() -> None:
        async with app.run_test(size=(80, 24)) as pilot:
            app.busy = True
            await pilot.click("#quit")
            await pilot.pause()
            assert not app._exit
            app.busy = False
            # The warning toast covers the button, so activate it directly.
            app.screen.query_one("#quit", Button).press()
            await pilot.pause()
            assert app._exit

    asyncio.run(body())
