# Features for a robust, complete, and scalable ReImage

This guide is the feature set beyond the first Windows installer. The core library stays free of terminal code. The TUI, the PyInstaller bundle, and the Windows installer are shells over that library. Each feature below names the behavior a later change should ship, and the limit that keeps the program small.

Shipped today: preview before any rename, collision report, two-step apply, one undo log per folder, creation / modification / name order, separator, width, and start index, the six historical extensions, the last five folders, headless `--dry-run`, `--yes`, and `--undo`, and a per-user Windows install with an optional folder right-click command.

## Robustness

These features keep a rename recoverable when a file is locked, a path is awkward, or the process stops halfway.

1. **Crash recovery for temporary names.** Apply moves each file to `.reimage-<id>.tmp` and then to the final name. If the process dies between those two moves, the next launch on that folder lists the leftover temporary files, matches them to the undo log when it can, and offers to finish the rename or move them back. Temporary names stay excluded from the scan.
2. **Durable undo before the next move.** The log is written before the first successful move and updated after each one. A change is not treated as committed until the log replace has finished. A failed replace stops the batch and leaves the remaining files on their current names.
3. **Partial failure stays partial.** A locked, missing, or read-only file is one row on the result screen. Files already renamed stay renamed. Undo restores only the moves recorded in the log. The installer and the TUI use the same rule.
4. **Long and reserved paths.** The plan rejects a target that is a Windows reserved device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`), ends in a space or a dot, or exceeds the path the host can create. The preview shows the reason and Apply stays off.
5. **Same-volume rename only.** The two-step move stays inside the chosen folder. The plan refuses a target that would leave that folder, so a prefix cannot smuggle a path separator. Illegal characters are already rejected in the prefix and the separator.
6. **Sharing violations are reported, not retried forever.** One attempt is made per file. The result row includes the operating-system message. A later option may retry a sharing violation a fixed number of times; the default stays a single attempt so a locked file cannot stall the batch.
7. **Remember the last successful settings.** Recent folders already keep five paths. Also store, per user, the last prefix, separator, width, start index, sort, and extension set, and fill Setup from that record. A corrupt settings file is ignored and replaced by the defaults.
8. **Installer repair.** Installing again replaces the program files, recreates the Start menu shortcut, and rewrites the context-menu keys only when the checkbox is selected. Clearing the checkbox, or running uninstall, removes both `Directory` and `Directory\Background` keys. User settings and undo logs, which live under the platform data directory, are not deleted with the program.
9. **Context-menu launch is non-destructive.** The menu runs `reimage.exe --folder "<path>"` and opens Setup with that folder filled. It does not pass `--yes`. A background click in a folder window uses the folder path (`%V`). A click on the folder itself uses `%1`.
10. **Tests cover the installer command.** The headless parser, the folder prefill, and the registry command strings (`--folder "%1"` and `--folder "%V"`) stay under test so a packaging change cannot silently rename a folder.

## Completeness

These features make the product cover the jobs the architecture already lists as follow-ups, without changing the default `{prefix}_{001}{ext}` result.

1. **Optional recursion.** A Setup switch includes images in subfolders. The default stays the current folder only. New names are still written next to each source file, not flattened into the root, unless a later template says otherwise. Undo records every move with absolute paths.
2. **Native folder picker.** A button next to the path field opens the operating-system folder dialog and writes the chosen path into the field. Paste and the recent-folder list remain.
3. **Drag and drop.** Dropping a folder on the Setup screen fills the path field. Dropping files uses their parent folder and does not rename files that were not part of the drop when a selection was explicit.
4. **EXIF capture time.** A fourth sort reads the capture timestamp from JPEG EXIF when it is present, and falls back to the creation clock otherwise. The preview label names which clock was used for the batch when the fallback was needed. Image pixels are still not decoded for display.
5. **Format templates.** The default template remains `{prefix}{separator}{number}{extension}`. A template field may also use `{name}`, `{stem}`, `{date}`, and a width on the number. The planner is the only component that expands the template. Collisions use the same rules as the fixed pattern.
6. **Batch profiles.** A named profile stores folder-independent settings (prefix, template, sort, extensions) in the user data directory. Setup can load and save a profile. Profiles do not store absolute undo logs.
7. **Right-click on a selection of images.** When the selection is files rather than a folder, the command renames that selection only, in the parent folder, and leaves other images alone. The preview lists just the selection.
8. **Send To.** The installer can add a Send To shortcut that passes the folder the same way the context menu does. It is a separate checkbox from the context menu.
9. **Undo from Explorer.** A second, unchecked-by-default menu item runs `reimage.exe --undo --folder "<path>"` only when a log exists for that folder. If no log exists, the program prints the current message and does not change files.
10. **English and Spanish UI.** Strings live in one catalog. The default language follows the operating system, with a switch in Setup. Rename rules, file names, and the undo log stay language-neutral.
11. **Guides stay next to the screens.** `docs/screenshots/` keeps `setup.png`, `preview.png`, and a collision capture. The install, release, undo, and this feature guide link to those files instead of describing a screen that has drifted.

## Scalability

These features keep one folder of a few dozen images and a folder of tens of thousands on the same code path.

1. **The core does not load image bytes.** Scanning reads directory entries and timestamps only. That rule stays in place when EXIF is added: read the header, not the pixel buffer. Pillow is not a runtime dependency unless a feature needs it, and then only for metadata.
2. **Plan generation is streaming.** The scanner yields files in sort order, or sorts an index of paths and timestamps, without building a widget per file first. The preview table requests rows as they are shown. Apply walks the same plan the table showed.
3. **Cancel and progress.** Apply runs off the UI thread, as it does now, and reports how many files have moved. Cancel finishes the file in flight, writes the log for completed moves, and stops. Quit stays disabled until that file and the log write have finished.
4. **One undo log per folder, bounded.** The log stores only the latest confirmed run. It is not an append-only history of every rename ever made in that folder. A run that renames nothing does not erase a previous log.
5. **Stable ordering for equal timestamps.** Equal clocks break ties by file name, case-folded, so two runs on an unchanged folder produce the same plan.
6. **Packaging stays per operating system.** PyInstaller still builds a one-folder console bundle on the OS that will run it. The Windows installer only wraps `dist/windows/reimage`. It does not cross-compile macOS or Linux.
7. **A thin installer.** The installer copies the bundle, creates the Start menu shortcut, and optionally writes two registry keys. It does not embed a second copy of the rename rules. Uninstall removes program files and those keys.
8. **Headless and TUI share the planner.** `--dry-run`, `--yes`, the preview table, and a future GUI call `build_plan` and `apply_plan`. A new shell must not rename files on its own.
9. **Continuous build.** One workflow installs the package, runs `pytest`, and builds the bundle on Windows, macOS, and Linux. The Windows job also compiles `packaging/reimage.iss` when the Inno Setup compiler is present. Tests do not require a display.
10. **Extension points, not forks.** A sort key and a name template are data the planner accepts. New sorts and templates register behind those two inputs so the collision check and the two-step apply do not gain a special case per feature.

## Explicitly out of scope

Cloud sync of undo logs, watching a folder for new files, rewriting metadata inside images, and an auto-update channel that downloads code. Those need a trust and a storage story this desktop utility does not have. Recursive search, a native picker, drag and drop, EXIF sort, templates, profiles, and the context menu are the completeness work; they are specified above and are not part of the installer change.
