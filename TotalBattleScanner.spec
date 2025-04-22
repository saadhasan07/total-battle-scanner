# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['TotalBattleScanner_FULL.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('silver_area.png', '.'),
        ('ingot_area.png', '.'),
        ('wood_area.png', '.'),
        ('stone_area.png', '.'),
        ('peace_shield_icon.png', '.'),
        ('online_status.png', '.'),
        ('troop_area.png', '.')
    ],
    hiddenimports=['PIL._tkinter_finder'],
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
    a.binaries,
    a.datas,
    [],
    name='TotalBattleScanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'
) 