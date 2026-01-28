# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for FreeFood."""

from pathlib import Path
import importlib.util


def rich_unicode_hiddenimports() -> list[str]:
    """Include Rich unicode table modules with hyphenated names."""
    spec = importlib.util.find_spec("rich._unicode_data")
    if not spec or not spec.submodule_search_locations:
        return []
    base = Path(next(iter(spec.submodule_search_locations)))
    return [
        f"rich._unicode_data.{path.stem}"
        for path in base.glob("unicode*-*.py")
    ]

a = Analysis(
    ['freefood/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('freefood/app.tcss', 'freefood')],
    hiddenimports=rich_unicode_hiddenimports(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='freefood',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    exclude_binaries=False,
)
