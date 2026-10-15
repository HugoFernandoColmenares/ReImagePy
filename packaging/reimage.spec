# -*- mode: python ; coding: utf-8 -*-
"""Freeze `python -m reimage` into a one-folder console bundle.

PyInstaller does not cross-compile. Run this spec on the OS you want to ship:
Windows writes dist/windows/reimage/reimage.exe, macOS writes
dist/macos/reimage/reimage, and Linux writes dist/linux/reimage/reimage.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# PyInstaller executes this file with exec(), so __file__ does not exist.
# SPEC is the absolute path of this spec, injected into the namespace.
spec_path = Path(SPEC).resolve()
project_root = spec_path.parent.parent
platform_name = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")

import PyInstaller.config as pyinstaller_config

dist_dir = project_root / "dist" / platform_name
work_dir = project_root / "build" / platform_name
dist_dir.mkdir(parents=True, exist_ok=True)
work_dir.mkdir(parents=True, exist_ok=True)
pyinstaller_config.CONF["distpath"] = str(dist_dir)
pyinstaller_config.CONF["workpath"] = str(work_dir)

datas, binaries, hiddenimports = collect_all("textual")

a = Analysis(
    [str(project_root / "src" / "reimage" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reimage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="reimage",
)
