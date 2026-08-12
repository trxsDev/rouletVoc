# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Base directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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
        'pygame',
        'sounddevice',
        'speech_recognition',
        'PIL',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
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
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='RouletVoc',
)
