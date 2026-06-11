# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for proFetch — produces a single standalone profetch.exe

a = Analysis(
    ['src/profetch/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # tomli is imported conditionally (Python < 3.11) inside manifest.py
        'tomli',
        # dynaconf loaders are loaded by name at runtime
        'dynaconf.loaders.toml_loader',
        'dynaconf.loaders.env_loader',
        'dynaconf.utils.boxing',
        # aiosqlite uses importlib internally for its connection factory
        'aiosqlite',
    ],
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
    name='profetch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
