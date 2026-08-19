import sys
import os
import pygame

# ---------------------------------------------------------
# Base Paths (Supports PyInstaller Bundled Mode & Dev Mode)
# ---------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

# ---------------------------------------------------------
# Display Dimensions & FPS (1080p Ultra-Sharp Virtual Canvas)
# ---------------------------------------------------------
WIDTH, HEIGHT = 1920, 1080
FPS = 60

# macOS Safe Area Insets (Prevents overlap with macOS Dock & Menu Bar)
SAFE_INSET_TOP = 40
SAFE_INSET_BOTTOM = 80
SAFE_INSET_X = 60

# ---------------------------------------------------------
# Color Palette (TRXS Sleek Dark Theme)
# ---------------------------------------------------------
BG_COLOR = (15, 23, 42)
CARD_BACK_COLOR = (30, 41, 59, 235)
CARD_BORDER = (51, 65, 85)
TEXT_WHITE = (248, 250, 252)

ACCENT_CYAN = (6, 182, 212)
ACCENT_EMERALD = (16, 185, 129)
ACCENT_AMBER = (245, 158, 11)
ACCENT_ROSE = (244, 63, 94)
ACCENT_PURPLE = (168, 85, 247)
ACCENT_BLUE = (59, 130, 246)

# ---------------------------------------------------------
# 8 Dynamic Team Palettes
# ---------------------------------------------------------
TEAM_PALETTES = [
    {"name": "Team 1", "thai": "ทีมที่ 1", "color": (239, 68, 68), "bg_col": (127, 29, 29)},
    {"name": "Team 2", "thai": "ทีมที่ 2", "color": (59, 130, 246), "bg_col": (30, 58, 138)},
    {"name": "Team 3", "thai": "ทีมที่ 3", "color": (16, 185, 129), "bg_col": (6, 78, 59)},
    {"name": "Team 4", "thai": "ทีมที่ 4", "color": (245, 158, 11), "bg_col": (120, 53, 15)},
    {"name": "Team 5", "thai": "ทีมที่ 5", "color": (168, 85, 247), "bg_col": (88, 28, 135)},
    {"name": "Team 6", "thai": "ทีมที่ 6", "color": (236, 72, 153), "bg_col": (131, 24, 67)},
    {"name": "Team 7", "thai": "ทีมที่ 7", "color": (249, 115, 22), "bg_col": (124, 45, 18)},
    {"name": "Team 8", "thai": "ทีมที่ 8", "color": (6, 182, 212), "bg_col": (14, 116, 144)}
]

# ---------------------------------------------------------
# MediaPipe Hand Skeleton Connections (21 Landmarks)
# ---------------------------------------------------------
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]
