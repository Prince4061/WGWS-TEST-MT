# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

datas = [
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
    ('sample_data', 'sample_data'),
]

# Collect reportlab dependencies (fonts, styles, encodings)
rl_datas, rl_binaries, rl_hiddenimports = collect_all('reportlab')
datas += rl_datas

hiddenimports = [
    'sqlalchemy.sql.default_comparator',
    'pydantic',
    'pydantic_core',
    'deepagents',
    'langchain',
    'langchain_core',
    'langchain_groq',
    'langchain_openai',
] + rl_hiddenimports

a = Analysis(
    ['run_desktop.py'],
    pathex=['.'],
    binaries=rl_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='StudentAssessment',
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
)
