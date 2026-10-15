# -*- mode: python ; coding: utf-8 -*-
"""Freeze `python -m reimage` into a one-folder console bundle.

PyInstaller does not cross-compile. Run this spec on the OS you want to ship:
Windows writes dist/windows/reimage/reimage.exe, macOS writes
dist/macos/reimage/reimage, and Linux writes dist/linux/reimage/reimage.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

spec_path = Path(globals().get("SPEC", __file__)).resolve()
project_root = spec_path.parent.parent
platform_name = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")

try:
    import PyInstaller.config as pyinstaller_config

    pyinstaller_config.CONF["distpath"] = str(project_root / "dist" / platform_name)
    pyinstaller_config.CONF["workpath"] = str(project_root / "build" / platform_name)
except Exception:
    pass

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
