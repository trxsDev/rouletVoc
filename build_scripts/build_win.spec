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

# ---------------------------------------------------------
# CRITICAL FIX: Bundle mediapipe/tasks/c/ shared library package
# MediaPipe >=0.10.14 loads its C shared library via:
#   importlib.resources.files('mediapipe.tasks.c')
# This is a dynamic lookup invisible to PyInstaller, so we must
# manually include the entire mediapipe/tasks/c/ directory
# (contains __init__.py + libmediapipe.dll on Windows).
# ---------------------------------------------------------
try:
    import mediapipe
    mp_root = os.path.dirname(mediapipe.__file__)
    mp_tasks_c = os.path.join(mp_root, 'tasks', 'c')
    if os.path.isdir(mp_tasks_c):
        datas.append((mp_tasks_c, os.path.join('mediapipe', 'tasks', 'c')))
        print(f'[build_win.spec] Bundling mediapipe/tasks/c/ from: {mp_tasks_c}')
    else:
        print(f'[build_win.spec] WARNING: mediapipe/tasks/c/ not found at {mp_tasks_c}')
except ImportError:
    print('[build_win.spec] WARNING: mediapipe not installed, skipping tasks/c bundle')

a = Analysis(
    [os.path.join(base_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'cv2',
        'mediapipe',
        'mediapipe.tasks',
        'mediapipe.tasks.c',                              # C shared library package
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.core',
        'mediapipe.tasks.python.core.mediapipe_c_bindings', # ctypes loader
        'mediapipe.tasks.python.core.mediapipe_c_utils',
        'mediapipe.tasks.python.core.serial_dispatcher',
        'mediapipe.tasks.python.vision',
        'mediapipe.tasks.python.vision.core',
        'mediapipe.tasks.python.vision.core.image',
        'mediapipe.tasks.python.vision.hand_landmarker',
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
