# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Base directory (PyInstaller defines SPECPATH for spec file directory)
try:
    base_dir = os.path.abspath(os.path.join(SPECPATH, '..'))
except NameError:
    base_dir = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(base_dir, 'assets'), 'assets'),
    (os.path.join(base_dir, 'config'), 'config'),
]

# Include model task if present
model_task = os.path.join(base_dir, 'hand_landmarker.task')
if os.path.exists(model_task):
    datas.append((model_task, '.'))

a = Analysis(
    [os.path.join(base_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'cv2',
        'mediapipe',
        'mediapipe.tasks',
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.vision',
        'matplotlib',
        'pygame',
        'sounddevice',
        'speech_recognition',
        'PIL',
        'numpy',
        'requests',
        'gtts',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RouletVoc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, 'assets', 'icons', 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RouletVoc',
)
