import cv2
import pygame
import numpy as np
import random
import time
import sys
import math
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------------------------------------------------
# MediaPipe Task Configuration & File Paths
# ---------------------------------------------------------
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

# ---------------------------------------------------------
# Low-Latency Non-Blocking Audio Engine
# ---------------------------------------------------------
import subprocess
import threading

class SoundEngine:
    def __init__(self):
        self.last_played = {}
        self.min_intervals = {
            "tick": 0.04,
            "countdown_beep": 0.3,
            "countdown_go": 0.5,
            "wheel_win": 0.5,
            "correct": 0.3,
            "wrong": 0.3,
            "lock": 0.2,
            "ok_ready": 0.5,
            "ready_ping": 0.09,
            "podium_fanfare": 1.0
        }

    def play(self, sound_name):
        now = time.time()
        min_int = self.min_intervals.get(sound_name, 0.05)
        if now - self.last_played.get(sound_name, 0.0) < min_int:
            return
        self.last_played[sound_name] = now
        
        file_path = os.path.join(SOUNDS_DIR, f"{sound_name}.wav")
        if os.path.exists(file_path):
            threading.Thread(
                target=lambda: subprocess.run(["afplay", file_path], capture_output=True),
                daemon=True
            ).start()

sound_engine = SoundEngine()

# ---------------------------------------------------------
# Pygame Setup & Color Palette (Kid-Friendly Vibrant Theme)
# ---------------------------------------------------------
pygame.display.init()

WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RouletVoc • AR Hand Gesture Vocabulary Game")
clock = pygame.time.Clock()

BG_COLOR = (15, 23, 42)
CARD_BACK_COLOR = (30, 41, 59, 235)
CARD_BORDER = (51, 65, 85)
TEXT_WHITE = (248, 250, 252)

# Kid-friendly vibrant pastels & glows
ACCENT_CYAN = (6, 182, 212)
ACCENT_SKY = (56, 189, 248)
ACCENT_EMERALD = (16, 185, 129)
ACCENT_MINT = (52, 211, 153)
ACCENT_AMBER = (245, 158, 11)
ACCENT_SUNNY = (250, 204, 21)
ACCENT_ROSE = (244, 63, 94)
ACCENT_PINK = (244, 114, 182)
ACCENT_PURPLE = (168, 85, 247)
ACCENT_LAVENDER = (192, 132, 252)
ACCENT_BLUE = (59, 130, 246)
ACCENT_ORANGE = (251, 146, 60)

# Team Color Palette (Up to 4 Teams)
TEAM_PALETTES = [
    {"name": "Team Red", "thai": "ทีมสีแดง 🔴", "color": (239, 68, 68), "bg_col": (127, 29, 29), "emoji": "🦁"},
    {"name": "Team Blue", "thai": "ทีมสีน้ำเงิน 🔵", "color": (59, 130, 246), "bg_col": (30, 58, 138), "emoji": "🐬"},
    {"name": "Team Green", "thai": "ทีมสีเขียว 🟢", "color": (16, 185, 129), "bg_col": (6, 78, 59), "emoji": "🦖"},
    {"name": "Team Yellow", "thai": "ทีมสีเหลือง 🟡", "color": (245, 158, 11), "bg_col": (120, 53, 15), "emoji": "🐯"}
]

# ---------------------------------------------------------
# MediaPipe Hand Connections (21 Landmarks Skeleton)
# ---------------------------------------------------------
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]

# ---------------------------------------------------------
# 4 Active Gesture Modes for Roulette
# ---------------------------------------------------------
GESTURE_MODES = [
    {
        "id": "PINCH",
        "name": "จีบนิ้ว (Pinch)",
        "emoji": "🤏",
        "image_file": "gesture_pinch.png",
        "desc": "จีบนิ้วชี้กับนิ้วโป้งเข้าหากันเพื่อเปิดการ์ด",
        "color": (245, 158, 11),
        "wedge_color": (217, 119, 6)
    },
    {
        "id": "FIST",
        "name": "กำมือ (Fist / Grab)",
        "emoji": "✊",
        "image_file": "gesture_fist.png",
        "desc": "กำมือเพื่อคว้าเปิดการ์ด",
        "color": (239, 68, 68),
        "wedge_color": (185, 28, 28)
    },
    {
        "id": "PEACE",
        "name": "ชู 2 นิ้ว (Peace Sign)",
        "emoji": "✌️",
        "image_file": "gesture_peace.png",
        "desc": "ชู 2 นิ้ว (ชี้+กลาง) เพื่อเปิดการ์ด",
        "color": (168, 85, 247),
        "wedge_color": (126, 34, 206)
    },
    {
        "id": "PALM",
        "name": "แบมือ (Open Palm)",
        "emoji": "🖐️",
        "image_file": "gesture_palm.png",
        "desc": "กางนิ้วมือทั้งหมดเพื่อเปิดการ์ด",
        "color": (16, 185, 129),
        "wedge_color": (4, 120, 87)
    }
]

# ---------------------------------------------------------
# 12 School Classroom Vocabulary Items
# ---------------------------------------------------------
ITEMS_POOL = [
    {"id": "book", "word": "หนังสือ", "en": "Book", "filename": "book.png", "color": (56, 189, 248)},
    {"id": "backpack", "word": "กระเป๋านักเรียน", "en": "School Bag", "filename": "backpack.png", "color": (96, 165, 250)},
    {"id": "pen", "word": "ปากกา", "en": "Pen", "filename": "pen.png", "color": (129, 140, 248)},
    {"id": "pencil", "word": "ดินสอ", "en": "Pencil", "filename": "pencil.png", "color": (251, 191, 36)},
    {"id": "ruler", "word": "ไม้บรรทัด", "en": "Ruler", "filename": "ruler.png", "color": (245, 158, 11)},
    {"id": "eraser", "word": "ยางลบ", "en": "Eraser", "filename": "eraser.png", "color": (56, 189, 248)},
    {"id": "chair", "word": "เก้าอี้", "en": "Chair", "filename": "chair.png", "color": (251, 146, 60)},
    {"id": "table", "word": "โต๊ะ", "en": "Table / Desk", "filename": "table.png", "color": (249, 115, 22)},
    {"id": "notebook", "word": "สมุด", "en": "Notebook", "filename": "notebook.png", "color": (74, 222, 128)},
    {"id": "window", "word": "หน้าต่าง", "en": "Window", "filename": "window.png", "color": (250, 204, 21)},
    {"id": "clock", "word": "นาฬิกา", "en": "Clock", "filename": "clock.png", "color": (248, 113, 113)},
    {"id": "fan", "word": "พัดลม", "en": "Fan", "filename": "fan.png", "color": (56, 189, 248)},
]

# ---------------------------------------------------------
# Asset & Font Loaders
# ---------------------------------------------------------
_loaded_images = {}
def get_image(filename, target_size=(100, 100)):
    key = f"{filename}_{target_size[0]}_{target_size[1]}"
    if key in _loaded_images:
        return _loaded_images[key]
    
    file_path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(file_path):
        try:
            pil_img = Image.open(file_path).convert("RGBA")
            pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)
            surf = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, "RGBA")
            _loaded_images[key] = surf
            return surf
        except Exception as e:
            print(f"[Asset Loader] Error loading {file_path}: {e}")
            
    surf = pygame.Surface(target_size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (100, 116, 139), (0, 0, target_size[0], target_size[1]), border_radius=12)
    _loaded_images[key] = surf
    return surf

_font_cache = {}
def get_font(size):
    if size in _font_cache:
        return _font_cache[size]
    font = None
    for path in [
        "/System/Library/Fonts/Supplemental/SukhumvitSet.ttc",
        "/System/Library/Fonts/Supplemental/Thonburi.ttc",
        "/System/Library/Fonts/ThonburiUI.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]:
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue
    if not font:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font

_text_cache = {}
def render_thai_text(text, font_size=32, color=(255, 255, 255)):
    cache_key = f"{text}_{font_size}_{color}"
    if cache_key in _text_cache:
        return _text_cache[cache_key]

    font = get_font(font_size)
    bbox = font.getbbox(text)
    
    pad_x, pad_y = 16, 12
    text_w = (bbox[2] - bbox[0]) + (pad_x * 2)
    text_h = (bbox[3] - bbox[1]) + (pad_y * 2)
    
    img = Image.new("RGBA", (max(text_w, 20), max(text_h, 20)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font, fill=(color[0], color[1], color[2], 255))
    
    surf = pygame.image.fromstring(img.tobytes(), img.size, "RGBA")
    _text_cache[cache_key] = surf
    return surf

# ---------------------------------------------------------
# Card Class
# ---------------------------------------------------------
class Card:
    def __init__(self, x, y, width, height, item_data, index):
        self.rect = pygame.Rect(x, y, width, height)
        self.item = item_data
        self.index = index
        self.is_flipped = False
        self.is_matched = False
        self.hover_progress = 0.0
        self.action_charge = 0.0
        self.shake_offset = 0

    def draw(self, surface, show_face=False):
        draw_x = self.rect.x + self.shake_offset
        draw_y = self.rect.y
        draw_rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)
        
        card_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        border_color = CARD_BORDER
        bg_col = (20, 30, 48, 235)
        
        if self.action_charge > 0.05:
            border_color = (
                int(ACCENT_AMBER[0] + (ACCENT_EMERALD[0] - ACCENT_AMBER[0]) * self.action_charge),
                int(ACCENT_AMBER[1] + (ACCENT_EMERALD[1] - ACCENT_AMBER[1]) * self.action_charge),
                int(ACCENT_AMBER[2] + (ACCENT_EMERALD[2] - ACCENT_AMBER[2]) * self.action_charge),
            )
            bg_col = (35, 55, 90, 250)
        elif self.hover_progress > 0:
            border_color = (
                int(CARD_BORDER[0] + (ACCENT_CYAN[0] - CARD_BORDER[0]) * self.hover_progress),
                int(CARD_BORDER[1] + (ACCENT_CYAN[1] - CARD_BORDER[1]) * self.hover_progress),
                int(CARD_BORDER[2] + (ACCENT_CYAN[2] - CARD_BORDER[2]) * self.hover_progress),
            )
            bg_col = (28, 45, 75, 245)
            
        if self.is_matched:
            border_color = ACCENT_EMERALD
            bg_col = (6, 78, 59, 245)
        elif show_face or self.is_flipped:
            bg_col = (15, 23, 42, 245)
            border_color = ACCENT_AMBER
            
        pygame.draw.rect(card_surf, bg_col, (0, 0, self.rect.width, self.rect.height), border_radius=18)
        border_w = 5 if self.action_charge > 0.1 else 3
        pygame.draw.rect(card_surf, border_color, (0, 0, self.rect.width, self.rect.height), width=border_w, border_radius=18)
        
        surface.blit(card_surf, (draw_x, draw_y))
        
        if show_face or self.is_flipped or self.is_matched:
            img_surf = get_image(self.item["filename"], target_size=(105, 105))
            img_rect = img_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery - 26))
            surface.blit(img_surf, img_rect)
            
            text_surf = render_thai_text(self.item["word"], font_size=24, color=self.item["color"])
            surface.blit(text_surf, text_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + 45)))
            
            en_surf = render_thai_text(self.item["en"], font_size=15, color=(148, 163, 184))
            surface.blit(en_surf, en_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + 70)))
        else:
            pattern_surf = render_thai_text("?", font_size=52, color=(100, 116, 139))
            surface.blit(pattern_surf, pattern_surf.get_rect(center=draw_rect.center))
            
            if self.action_charge > 0.05:
                bar_w = int(draw_rect.width * 0.85 * self.action_charge)
                bar_rect = pygame.Rect(draw_rect.x + int(draw_rect.width * 0.075), draw_rect.bottom - 20, bar_w, 8)
                pygame.draw.rect(surface, ACCENT_EMERALD, bar_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 255, 255), bar_rect, width=1, border_radius=4)
            elif self.hover_progress > 0.05:
                bar_w = int(draw_rect.width * 0.8 * self.hover_progress)
                bar_rect = pygame.Rect(draw_rect.x + int(draw_rect.width * 0.1), draw_rect.bottom - 16, bar_w, 6)
                pygame.draw.rect(surface, ACCENT_CYAN, bar_rect, border_radius=3)

# ---------------------------------------------------------
# 4-Sector Master Roulette Wheel Component
# ---------------------------------------------------------
class RouletteWheel:
    def __init__(self, cx, cy, radius=180):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = 0.0
        self.speed = 0.0
        self.deceleration = 0.0
        self.is_spinning = False
        
        self.num_wedges = len(GESTURE_MODES) # 4
        self.wedge_angle_span = 360.0 / self.num_wedges
        
        self.needle_deflection = 0.0
        self.last_passed_wedge = -1
        self.light_timer = 0
        
        self.base_wheel_surf = get_image("roulette_wheel.png", target_size=(self.radius * 2, self.radius * 2))
        self.pointer_surf = get_image("wheel_pointer.png", target_size=(68, 110))

    def spin_to_target(self, target_idx):
        self.is_spinning = True
        target_wedge_center = target_idx * self.wedge_angle_span + (self.wedge_angle_span / 2.0)
        target_final_angle = (270.0 - target_wedge_center) % 360.0
        
        extra_rotations = random.randint(4, 6) * 360.0
        current_mod = self.angle % 360.0
        angle_diff = (target_final_angle - current_mod) % 360.0
        if angle_diff < 120.0:
            angle_diff += 360.0
            
        total_distance = extra_rotations + angle_diff
        self.speed = math.sqrt(2 * 0.28 * total_distance)
        self.deceleration = (self.speed ** 2) / (2 * total_distance)

    def update(self):
        if self.is_spinning:
            self.angle += self.speed
            self.speed = max(0.0, self.speed - self.deceleration)
            
            pointer_wheel_angle = (270.0 - self.angle) % 360.0
            current_wedge = int(pointer_wheel_angle // self.wedge_angle_span) % self.num_wedges
            
            if current_wedge != self.last_passed_wedge:
                self.needle_deflection = -18.0
                self.last_passed_wedge = current_wedge
                sound_engine.play("tick")
                
            if self.speed <= 0.01:
                self.speed = 0.0
                self.is_spinning = False
                sound_engine.play("wheel_win")
                
        self.needle_deflection += (0.0 - self.needle_deflection) * 0.25
        self.light_timer += 1

    def get_current_selected_gesture(self):
        pointer_wheel_angle = (270.0 - self.angle) % 360.0
        idx = int(pointer_wheel_angle // self.wedge_angle_span) % self.num_wedges
        return GESTURE_MODES[idx]

    def draw(self, surface):
        rotated_wheel = pygame.transform.rotozoom(self.base_wheel_surf, -self.angle, 1.0)
        wheel_rect = rotated_wheel.get_rect(center=(self.cx, self.cy))
        surface.blit(rotated_wheel, wheel_rect)

        num_bulbs = 24
        for b in range(num_bulbs):
            b_ang = math.radians(b * (360.0 / num_bulbs) + (self.light_timer * 3 if self.is_spinning else 0))
            bx = self.cx + math.cos(b_ang) * (self.radius + 10)
            by = self.cy + math.sin(b_ang) * (self.radius + 10)
            is_lit = ((b + (self.light_timer // 4)) % 2 == 0)
            bulb_col = (250, 204, 21) if is_lit else (100, 116, 139)
            pygame.draw.circle(surface, bulb_col, (int(bx), int(by)), 5)
            if is_lit:
                pygame.draw.circle(surface, (255, 255, 255), (int(bx), int(by)), 2)

        rotated_pointer = pygame.transform.rotozoom(self.pointer_surf, self.needle_deflection, 1.0)
        p_rect = rotated_pointer.get_rect(center=(self.cx, self.cy - self.radius + 12))
        surface.blit(rotated_pointer, p_rect)

# ---------------------------------------------------------
# Master Game Engine with Freedom & Team Battle Modes
# ---------------------------------------------------------
class GestureMemoryGame:
    def __init__(self):
        self.mode = "FREEDOM" # "FREEDOM" or "TEAM"
        self.state = "LANDING_MENU" # LANDING_MENU, TEAM_SETUP, TEAM_READY, ROULETTE, ANNOUNCE, MEMORIZE, COUNTDOWN, PLAY, ROUND_END, PODIUM_DASHBOARD
        
        # Freedom Mode Metrics
        self.freedom_score = 0
        self.rounds_played = 0
        
        # Team Battle Configuration & Tournament State
        self.num_teams = 2
        self.words_per_team = 3
        self.current_team_idx = 0
        self.team_scores = [] # [{"name", "score", "time_spent", "words_done", "color", "emoji"}]
        self.team_start_time = 0.0
        self.team_ready_charge = 0.0
        
        # In-round state
        self.score = 0
        self.chances_left = 3
        self.target_item = None
        self.cards = []
        self.state_timer = time.time()
        self.play_grace_until = 0.0
        self.countdown_num = 3
        self.feedback_msg = ""
        self.feedback_color = TEXT_WHITE
        
        # Roulette Wheel Component
        self.wheel = RouletteWheel(WIDTH // 2, HEIGHT // 2 + 10, radius=185)
        self.selected_gesture = GESTURE_MODES[0]
        
        # Cursor & Hand Tracking State
        self.cursor_pos = [WIDTH // 2, HEIGHT // 2]
        self.hand_landmarks_screen = []
        self.current_detected_gesture = "NONE"
        self.is_pinched = False
        self.pinch_dist = 999.0
        self._last_timestamp_ms = -1
        
        # Decorative floating background bubbles for kid UI
        self.bubbles = []
        for _ in range(18):
            self.bubbles.append({
                "x": random.randint(20, WIDTH - 20),
                "y": random.randint(20, HEIGHT - 20),
                "r": random.randint(8, 28),
                "speed": random.uniform(0.4, 1.2),
                "color": random.choice([ACCENT_SKY, ACCENT_PINK, ACCENT_SUNNY, ACCENT_MINT, ACCENT_LAVENDER])
            })
            
        # MediaPipe Detector & Camera Setup
        self.detector = None
        self.cap = None
        self.setup_tracking_engine()
        self.setup_camera()

    def setup_tracking_engine(self):
        if not os.path.exists(MODEL_PATH):
            print(f"[CTO Engine] Downloading MediaPipe model from {MODEL_URL}...")
            try:
                urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
                print("[CTO Engine] Download completed successfully!")
            except Exception as e:
                print("[CTO Engine] Failed to download model:", e)

        try:
            base_options = python.BaseOptions(
                model_asset_path=MODEL_PATH,
                delegate=python.BaseOptions.Delegate.CPU
            )
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[CTO Engine] MediaPipe Tasks HandLandmarker initialized successfully!")
        except Exception as e:
            print("[CTO Engine] HandLandmarker init error:", e)

    def setup_camera(self):
        for idx in [1, 0, 2]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.cap = cap
                    print(f"[CTO Engine] Connected to camera index {idx}")
                    return
                cap.release()
        print("[CTO Engine] Warning: No active webcam found. Mouse fallback active.")

    def start_team_tournament(self):
        self.team_scores = []
        for i in range(self.num_teams):
            p = TEAM_PALETTES[i]
            self.team_scores.append({
                "id": i,
                "name": p["name"],
                "thai": p["thai"],
                "color": p["color"],
                "bg_col": p["bg_col"],
                "emoji": p["emoji"],
                "score": 0,
                "words_done": 0,
                "time_spent": 0.0
            })
        self.current_team_idx = 0
        self.team_ready_charge = 0.0
        self.state = "TEAM_READY"
        self.state_timer = time.time()

    def start_team_turn(self):
        self.team_start_time = time.time()
        self.start_new_round()

    def start_new_round(self):
        self.state = "ROULETTE"
        self.state_timer = time.time()
        self.feedback_msg = ""
        self.chances_left = 3
        
        target_gesture_idx = random.randint(0, len(GESTURE_MODES) - 1)
        self.wheel.spin_to_target(target_gesture_idx)
        
        chosen_items = random.sample(ITEMS_POOL, 6)
        self.target_item = random.choice(chosen_items)
        
        self.cards = []
        card_w, card_h = 190, 205
        start_x = (WIDTH - (3 * card_w + 2 * 34)) // 2
        start_y = 230
        
        idx = 0
        for r in range(2):
            for c in range(3):
                x = start_x + c * (card_w + 34)
                y = start_y + r * (card_h + 30)
                self.cards.append(Card(x, y, card_w, card_h, chosen_items[idx], idx))
                idx += 1

    def classify_hand_gesture(self, landmarks):
        """
        CTO Biometric Engine: Scale-Invariant 3D Joint Extension & Curl Analysis.
        Detects: PINCH, FIST, PEACE, PALM, OK, NONE.
        """
        wrist = landmarks[0]
        thumb_tip = landmarks[4]

        index_mcp = landmarks[5]
        index_pip = landmarks[6]
        index_tip = landmarks[8]

        middle_mcp = landmarks[9]
        middle_pip = landmarks[10]
        middle_tip = landmarks[12]

        ring_mcp = landmarks[13]
        ring_pip = landmarks[14]
        ring_tip = landmarks[16]

        pinky_mcp = landmarks[17]
        pinky_pip = landmarks[18]
        pinky_tip = landmarks[20]

        def dist(p1, p2):
            return math.hypot((p1.x - p2.x) * WIDTH, (p1.y - p2.y) * HEIGHT)

        palm_size = max(dist(wrist, middle_mcp), 45.0)

        def is_extended(tip, pip, mcp):
            return (dist(tip, wrist) > dist(pip, wrist) * 1.15) and (dist(tip, mcp) > palm_size * 0.78)

        def is_curled(tip, pip, mcp):
            return (dist(tip, wrist) < dist(pip, wrist) * 1.02) or (dist(tip, mcp) < palm_size * 0.58)

        idx_ext = is_extended(index_tip, index_pip, index_mcp)
        idx_crl = is_curled(index_tip, index_pip, index_mcp)

        mid_ext = is_extended(middle_tip, middle_pip, middle_mcp)
        mid_crl = is_curled(middle_tip, middle_pip, middle_mcp)

        rng_ext = is_extended(ring_tip, ring_pip, ring_mcp)
        rng_crl = is_curled(ring_tip, ring_pip, ring_mcp)

        pnk_ext = is_extended(pinky_tip, pinky_pip, pinky_mcp)
        pnk_crl = is_curled(pinky_tip, pinky_pip, pinky_mcp)

        self.pinch_dist = dist(thumb_tip, index_tip)
        self.is_pinched = (self.pinch_dist < (0.24 * palm_size)) or (self.pinch_dist < 32.0)

        # 1. OK Gesture (👌): Thumb and Index pinching circle, Middle+Ring+Pinky extended
        if self.is_pinched and mid_ext and rng_ext and pnk_ext:
            return "OK"

        # 2. PINCH: Thumb and Index touching, others curled or neutral
        if self.is_pinched:
            return "PINCH"

        # 3. FIST: All 4 main fingers curled tightly
        if idx_crl and mid_crl and rng_crl and pnk_crl:
            return "FIST"

        # 4. PEACE: Index & Middle extended with spread, Ring & Pinky curled
        if idx_ext and mid_ext and rng_crl and pnk_crl:
            if dist(index_tip, middle_tip) > palm_size * 0.20:
                return "PEACE"

        # 5. PALM: All 5 fingers extended and spread
        thumb_spread = dist(thumb_tip, index_mcp) > palm_size * 0.62
        if idx_ext and mid_ext and rng_ext and pnk_ext and thumb_spread:
            return "PALM"

        return "NONE"

    def process_hand_tracking(self):
        self.hand_landmarks_screen = []
        
        if not self.cap or not self.cap.isOpened():
            mx, my = pygame.mouse.get_pos()
            self.cursor_pos = [mx, my]
            if pygame.mouse.get_pressed()[0]:
                self.current_detected_gesture = "OK" if self.state == "TEAM_READY" else self.selected_gesture["id"]
            else:
                self.current_detected_gesture = "NONE"
            return None

        ret, frame = self.cap.read()
        if not ret:
            mx, my = pygame.mouse.get_pos()
            self.cursor_pos = [mx, my]
            return None

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_detected = False

        if self.detector:
            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int(time.time() * 1000)
                if timestamp_ms <= self._last_timestamp_ms:
                    timestamp_ms = self._last_timestamp_ms + 1
                self._last_timestamp_ms = timestamp_ms
                
                result = self.detector.detect_for_video(mp_image, timestamp_ms)
                
                if result and result.hand_landmarks and len(result.hand_landmarks) > 0:
                    lm = result.hand_landmarks[0]
                    self.hand_landmarks_screen = [(int(p.x * WIDTH), int(p.y * HEIGHT)) for p in lm]
                    
                    index_tip = lm[8]
                    thumb_tip = lm[4]
                    
                    if self.is_pinched:
                        target_x = int(((index_tip.x + thumb_tip.x) / 2) * WIDTH)
                        target_y = int(((index_tip.y + thumb_tip.y) / 2) * HEIGHT)
                    else:
                        target_x = int(index_tip.x * WIDTH)
                        target_y = int(index_tip.y * HEIGHT)
                    
                    self.cursor_pos[0] += (target_x - self.cursor_pos[0]) * 0.65
                    self.cursor_pos[1] += (target_y - self.cursor_pos[1]) * 0.65
                    
                    self.current_detected_gesture = self.classify_hand_gesture(lm)
                    hand_detected = True
            except Exception:
                pass

        if not hand_detected:
            mx, my = pygame.mouse.get_pos()
            if pygame.mouse.get_focused():
                self.cursor_pos[0] += (mx - self.cursor_pos[0]) * 0.5
                self.cursor_pos[1] += (my - self.cursor_pos[1]) * 0.5
                if pygame.mouse.get_pressed()[0]:
                    self.current_detected_gesture = "OK" if self.state == "TEAM_READY" else self.selected_gesture["id"]

        bg_cam = cv2.resize(rgb_frame, (WIDTH, HEIGHT))
        return bg_cam

    def update(self):
        now = time.time()
        elapsed = now - self.state_timer
        
        # Update decorative bubbles
        for b in self.bubbles:
            b["y"] -= b["speed"]
            if b["y"] < -30:
                b["y"] = HEIGHT + 30
                b["x"] = random.randint(20, WIDTH - 20)
                
        if self.state == "LANDING_MENU":
            pass
            
        elif self.state == "TEAM_SETUP":
            pass
            
        elif self.state == "TEAM_READY":
            # OK Gesture Ready Check (Hold OK for 0.4s to start team turn)
            if self.current_detected_gesture == "OK":
                self.team_ready_charge = min(1.0, self.team_ready_charge + 0.05)
                sound_engine.play("ready_ping")
                if self.team_ready_charge >= 1.0:
                    sound_engine.play("ok_ready")
                    self.start_team_turn()
            else:
                self.team_ready_charge = max(0.0, self.team_ready_charge - 0.08)
                
        elif self.state == "ROULETTE":
            self.wheel.update()
            self.selected_gesture = self.wheel.get_current_selected_gesture()
            
            if not self.wheel.is_spinning and elapsed > 3.0:
                self.state = "ANNOUNCE"
                self.state_timer = now
                
        elif self.state == "ANNOUNCE":
            if elapsed > 2.6:
                self.state = "MEMORIZE"
                self.state_timer = now
                
        elif self.state == "MEMORIZE":
            if elapsed > 3.5:
                self.state = "COUNTDOWN"
                self.state_timer = now
                self.countdown_num = 3
                for card in self.cards:
                    card.is_flipped = False
                    
        elif self.state == "COUNTDOWN":
            cd = 3 - int(elapsed)
            if cd > 0:
                if self.countdown_num != cd:
                    sound_engine.play("countdown_beep")
                self.countdown_num = cd
            else:
                self.state = "PLAY"
                self.state_timer = now
                self.play_grace_until = now + 0.45
                sound_engine.play("countdown_go")
                    
        elif self.state == "PLAY":
            cursor_rect = pygame.Rect(self.cursor_pos[0] - 14, self.cursor_pos[1] - 14, 28, 28)
            req_gesture = self.selected_gesture["id"]
            is_armed = (now >= self.play_grace_until)
            
            for card in self.cards:
                if card.rect.colliderect(cursor_rect) and not card.is_matched and not card.is_flipped:
                    card.hover_progress = min(1.0, card.hover_progress + 0.08)
                    
                    if is_armed and (self.current_detected_gesture == req_gesture):
                        card.action_charge = min(1.0, card.action_charge + 0.09)
                        if card.action_charge >= 1.0:
                            sound_engine.play("lock")
                            self.handle_card_guess(card)
                            break
                    else:
                        card.action_charge = max(0.0, card.action_charge - 0.12)
                else:
                    card.hover_progress = max(0.0, card.hover_progress - 0.08)
                    card.action_charge = max(0.0, card.action_charge - 0.20)
                    
        elif self.state == "ROUND_END":
            if elapsed > 2.8:
                if self.mode == "FREEDOM":
                    self.start_new_round()
                else:
                    # Team Tournament Progression
                    team = self.team_scores[self.current_team_idx]
                    team["words_done"] += 1
                    team["time_spent"] += (now - self.team_start_time)
                    
                    if team["words_done"] < self.words_per_team:
                        # Team continues next word
                        self.start_team_turn()
                    else:
                        # Next team or Tournament complete
                        self.current_team_idx += 1
                        if self.current_team_idx < self.num_teams:
                            self.team_ready_charge = 0.0
                            self.state = "TEAM_READY"
                            self.state_timer = now
                        else:
                            # All teams finished -> Show Podium Dashboard!
                            sound_engine.play("podium_fanfare")
                            self.state = "PODIUM_DASHBOARD"
                            self.state_timer = now

    def handle_card_guess(self, card):
        card.is_flipped = True
        if card.item["id"] == self.target_item["id"]:
            card.is_matched = True
            sound_engine.play("correct")
            if self.mode == "FREEDOM":
                self.freedom_score += 100
                self.score = self.freedom_score
            else:
                self.team_scores[self.current_team_idx]["score"] += 100
                self.score = self.team_scores[self.current_team_idx]["score"]
                
            self.feedback_msg = f"🎉 ท่าทางถูกต้อง + เลือกถูกการ์ด! (+100 คะแนน)"
            self.feedback_color = ACCENT_EMERALD
            self.state = "ROUND_END"
            self.state_timer = time.time()
        else:
            self.chances_left -= 1
            card.shake_offset = 14
            sound_engine.play("wrong")
            self.feedback_msg = f"❌ ยังไม่ใช่ '{self.target_item['word']}' (เหลืออีก {self.chances_left} ครั้ง)"
            self.feedback_color = ACCENT_ROSE
            
            if self.chances_left <= 0:
                for c in self.cards:
                    if c.item["id"] == self.target_item["id"]:
                        c.is_flipped = True
                self.feedback_msg = f"❌ หมดโอกาสแล้ว! คำตอบคือ '{self.target_item['word']}'"
                self.state = "ROUND_END"
                self.state_timer = time.time()

    def draw_hand_skeleton(self):
        if not self.hand_landmarks_screen or len(self.hand_landmarks_screen) < 21:
            return
            
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            p1 = self.hand_landmarks_screen[p1_idx]
            p2 = self.hand_landmarks_screen[p2_idx]
            pygame.draw.line(screen, ACCENT_SKY, p1, p2, 4)
            pygame.draw.line(screen, (224, 242, 254), p1, p2, 2)
            
        thumb_pt = self.hand_landmarks_screen[4]
        index_pt = self.hand_landmarks_screen[8]
        
        if self.is_pinched:
            pygame.draw.line(screen, ACCENT_AMBER, thumb_pt, index_pt, 6)
            mid_x = (thumb_pt[0] + index_pt[0]) // 2
            mid_y = (thumb_pt[1] + index_pt[1]) // 2
            pygame.draw.circle(screen, ACCENT_AMBER, (mid_x, mid_y), 16)
            pygame.draw.circle(screen, (255, 255, 255), (mid_x, mid_y), 9)

        for pt in self.hand_landmarks_screen:
            pygame.draw.circle(screen, ACCENT_EMERALD, pt, 5)
            pygame.draw.circle(screen, (255, 255, 255), pt, 2)

    def draw_floating_bubbles(self):
        for b in self.bubbles:
            bubble_surf = pygame.Surface((b["r"] * 2, b["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(bubble_surf, (b["color"][0], b["color"][1], b["color"][2], 45), (b["r"], b["r"]), b["r"])
            pygame.draw.circle(bubble_surf, (255, 255, 255, 90), (b["r"] - b["r"] // 3, b["r"] - b["r"] // 3), max(2, b["r"] // 3))
            screen.blit(bubble_surf, (b["x"] - b["r"], b["y"] - b["r"]))

    def draw_landing_menu(self):
        # Semi-transparent dark gradient overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 230))
        screen.blit(overlay, (0, 0))
        
        self.draw_floating_bubbles()
        
        # Bouncy Floating Logo Badge
        pulse_offset = math.sin(time.time() * 2.5) * 6
        
        title_surf = render_thai_text("🎡 RouletVoc", font_size=58, color=ACCENT_SUNNY)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 130 + pulse_offset))
        screen.blit(title_surf, title_rect)
        
        sub_surf = render_thai_text("เกมจับคู่คำศัพท์ & ท่าทางมือ AR แสนสนุกสำหรับเด็ก ✨", font_size=24, color=ACCENT_SKY)
        sub_rect = sub_surf.get_rect(center=(WIDTH // 2, 185 + pulse_offset))
        screen.blit(sub_surf, sub_rect)
        
        # Mode Cards
        mouse_pos = pygame.mouse.get_pos()
        card_w, card_h = 360, 320
        gap = 50
        
        # 1. Freedom Mode Card
        c1_x = (WIDTH - (2 * card_w + gap)) // 2
        c1_y = 250
        c1_rect = pygame.Rect(c1_x, c1_y, card_w, card_h)
        c1_hover = c1_rect.collidepoint(mouse_pos)
        
        c1_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        c1_bg = (30, 58, 138, 245) if c1_hover else (17, 24, 39, 235)
        c1_border = ACCENT_SKY if c1_hover else (51, 65, 85)
        pygame.draw.rect(c1_surf, c1_bg, (0, 0, card_w, card_h), border_radius=28)
        pygame.draw.rect(c1_surf, c1_border, (0, 0, card_w, card_h), width=4 if c1_hover else 2, border_radius=28)
        screen.blit(c1_surf, (c1_x, c1_y))
        
        badge1 = render_thai_text("🌟 Freedom Mode", font_size=32, color=ACCENT_SKY)
        screen.blit(badge1, badge1.get_rect(center=(c1_rect.centerx, c1_y + 60)))
        
        desc1_1 = render_thai_text("โหมดเล่นเดี่ยว ผจญภัยตามใจชอบ", font_size=20, color=(224, 242, 254))
        desc1_2 = render_thai_text("สะสมคะแนนเรื่อยๆ ไม่มีกำหนดรอบ", font_size=18, color=(148, 163, 184))
        screen.blit(desc1_1, desc1_1.get_rect(center=(c1_rect.centerx, c1_y + 130)))
        screen.blit(desc1_2, desc1_2.get_rect(center=(c1_rect.centerx, c1_y + 165)))
        
        btn1_surf = pygame.Surface((240, 55), pygame.SRCALPHA)
        pygame.draw.rect(btn1_surf, ACCENT_SKY, (0, 0, 240, 55), border_radius=28)
        btn1_t = render_thai_text("🎮 เล่นคนเดียว", font_size=22, color=(15, 23, 42))
        btn1_surf.blit(btn1_t, btn1_t.get_rect(center=(120, 27)))
        screen.blit(btn1_surf, (c1_rect.centerx - 120, c1_y + 230))
        
        # 2. Team Battle Mode Card
        c2_x = c1_x + card_w + gap
        c2_y = 250
        c2_rect = pygame.Rect(c2_x, c2_y, card_w, card_h)
        c2_hover = c2_rect.collidepoint(mouse_pos)
        
        c2_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        c2_bg = (120, 53, 15, 245) if c2_hover else (17, 24, 39, 235)
        c2_border = ACCENT_SUNNY if c2_hover else (51, 65, 85)
        pygame.draw.rect(c2_surf, c2_bg, (0, 0, card_w, card_h), border_radius=28)
        pygame.draw.rect(c2_surf, c2_border, (0, 0, card_w, card_h), width=4 if c2_hover else 2, border_radius=28)
        screen.blit(c2_surf, (c2_x, c2_y))
        
        badge2 = render_thai_text("🏆 Team Battle", font_size=32, color=ACCENT_SUNNY)
        screen.blit(badge2, badge2.get_rect(center=(c2_rect.centerx, c2_y + 60)))
        
        desc2_1 = render_thai_text("โหมดประลองความจำแบบทีม", font_size=20, color=(254, 240, 138))
        desc2_2 = render_thai_text("สะสมแต้ม ชิงโพเดียม TOP 3!", font_size=18, color=(148, 163, 184))
        screen.blit(desc2_1, desc2_1.get_rect(center=(c2_rect.centerx, c2_y + 130)))
        screen.blit(desc2_2, desc2_2.get_rect(center=(c2_rect.centerx, c2_y + 165)))
        
        btn2_surf = pygame.Surface((240, 55), pygame.SRCALPHA)
        pygame.draw.rect(btn2_surf, ACCENT_SUNNY, (0, 0, 240, 55), border_radius=28)
        btn2_t = render_thai_text("⚔️ แข่งเป็นทีม", font_size=22, color=(15, 23, 42))
        btn2_surf.blit(btn2_t, btn2_t.get_rect(center=(120, 27)))
        screen.blit(btn2_surf, (c2_rect.centerx - 120, c2_y + 230))

        # Check clicks
        if pygame.mouse.get_pressed()[0]:
            if c1_hover:
                self.mode = "FREEDOM"
                self.freedom_score = 0
                self.start_new_round()
            elif c2_hover:
                self.mode = "TEAM"
                self.state = "TEAM_SETUP"

    def draw_team_setup(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 235))
        screen.blit(overlay, (0, 0))
        
        self.draw_floating_bubbles()
        
        title_surf = render_thai_text("⚙️ ตั้งค่าการแข่งขันแบบทีม (Tournament Setup)", font_size=42, color=ACCENT_SUNNY)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 90)))
        
        mouse_pos = pygame.mouse.get_pos()
        clicked = pygame.mouse.get_pressed()[0]
        
        # 1. Number of Teams
        lbl1 = render_thai_text("1. จำนวนทีมที่เข้าแข่งขัน:", font_size=26, color=TEXT_WHITE)
        screen.blit(lbl1, (WIDTH // 2 - 320, 160))
        
        for i, count in enumerate([2, 3, 4]):
            btn_rect = pygame.Rect(WIDTH // 2 - 120 + i * 110, 155, 95, 48)
            is_active = (self.num_teams == count)
            is_hover = btn_rect.collidepoint(mouse_pos)
            
            col = ACCENT_SKY if is_active else ((51, 65, 85) if not is_hover else (71, 85, 105))
            text_col = (15, 23, 42) if is_active else TEXT_WHITE
            
            pygame.draw.rect(screen, col, btn_rect, border_radius=14)
            if is_active:
                pygame.draw.rect(screen, (255, 255, 255), btn_rect, width=2, border_radius=14)
                
            t_surf = render_thai_text(f"{count} ทีม", font_size=20, color=text_col)
            screen.blit(t_surf, t_surf.get_rect(center=btn_rect.center))
            
            if clicked and is_hover:
                self.num_teams = count
                
        # Team preview badges
        for t in range(self.num_teams):
            p = TEAM_PALETTES[t]
            t_rect = pygame.Rect(WIDTH // 2 - 320 + t * 165, 225, 150, 60)
            pygame.draw.rect(screen, p["color"], t_rect, border_radius=16)
            p_surf = render_thai_text(f"{p['emoji']} {p['name']}", font_size=18, color=TEXT_WHITE)
            screen.blit(p_surf, p_surf.get_rect(center=t_rect.center))
            
        # 2. Words per Team
        lbl2 = render_thai_text("2. จำนวนคำศัพท์ต่อทีม:", font_size=26, color=TEXT_WHITE)
        screen.blit(lbl2, (WIDTH // 2 - 320, 320))
        
        for i, count in enumerate([3, 5, 8]):
            btn_rect = pygame.Rect(WIDTH // 2 - 120 + i * 110, 315, 95, 48)
            is_active = (self.words_per_team == count)
            is_hover = btn_rect.collidepoint(mouse_pos)
            
            col = ACCENT_SUNNY if is_active else ((51, 65, 85) if not is_hover else (71, 85, 105))
            text_col = (15, 23, 42) if is_active else TEXT_WHITE
            
            pygame.draw.rect(screen, col, btn_rect, border_radius=14)
            if is_active:
                pygame.draw.rect(screen, (255, 255, 255), btn_rect, width=2, border_radius=14)
                
            t_surf = render_thai_text(f"{count} คำ", font_size=20, color=text_col)
            screen.blit(t_surf, t_surf.get_rect(center=btn_rect.center))
            
            if clicked and is_hover:
                self.words_per_team = count
                
        # Big Start Button
        start_btn = pygame.Rect(WIDTH // 2 - 160, 440, 320, 70)
        st_hover = start_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, ACCENT_EMERALD if st_hover else (5, 150, 105), start_btn, border_radius=35)
        pygame.draw.rect(screen, (255, 255, 255), start_btn, width=3, border_radius=35)
        st_surf = render_thai_text("🚀 เริ่มการแข่งขัน!", font_size=32, color=TEXT_WHITE)
        screen.blit(st_surf, st_surf.get_rect(center=start_btn.center))
        
        # Back Button
        back_btn = pygame.Rect(WIDTH // 2 - 100, 540, 200, 45)
        bk_hover = back_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (51, 65, 85) if not bk_hover else (71, 85, 105), back_btn, border_radius=22)
        bk_surf = render_thai_text("🔙 กลับหน้าหลัก", font_size=20, color=TEXT_WHITE)
        screen.blit(bk_surf, bk_surf.get_rect(center=back_btn.center))
        
        if clicked:
            if st_hover:
                self.start_team_tournament()
            elif bk_hover:
                self.state = "LANDING_MENU"

    def draw_team_ready(self):
        team = self.team_scores[self.current_team_idx]
        
        # Top Team Tag
        tag_surf = pygame.Surface((WIDTH, 110), pygame.SRCALPHA)
        tag_surf.fill((team["color"][0], team["color"][1], team["color"][2], 215))
        screen.blit(tag_surf, (0, 0))
        
        t_text = render_thai_text(f"🏁 ถึงตา {team['emoji']} {team['name']} ({team['thai']}) แล้ว!", font_size=36, color=TEXT_WHITE)
        screen.blit(t_text, t_text.get_rect(center=(WIDTH // 2, 55)))
        
        # Center Ready Card & OK Gesture Instruction
        center_card = pygame.Rect(WIDTH // 2 - 280, HEIGHT // 2 - 170, 560, 360)
        card_surf = pygame.Surface((560, 360), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (15, 23, 42, 230), (0, 0, 560, 360), border_radius=32)
        pygame.draw.rect(card_surf, team["color"], (0, 0, 560, 360), width=4, border_radius=32)
        screen.blit(card_surf, center_card.topleft)
        
        ok_img = get_image("gesture_ok.png", target_size=(140, 140))
        screen.blit(ok_img, ok_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
        
        r_text1 = render_thai_text("ยกมือทำท่า OK 👌 เพื่อยืนยันความพร้อม!", font_size=26, color=ACCENT_SUNNY)
        r_text2 = render_thai_text(f"รอบนี้ต้องค้นหาทั้งหมด {self.words_per_team} คำ", font_size=20, color=(224, 242, 254))
        screen.blit(r_text1, r_text1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))
        screen.blit(r_text2, r_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 88)))
        
        # Ready Progress Bar
        bar_w = 420
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = HEIGHT // 2 + 130
        pygame.draw.rect(screen, (51, 65, 85), (bar_x, bar_y, bar_w, 20), border_radius=10)
        if self.team_ready_charge > 0:
            fill_w = int(bar_w * self.team_ready_charge)
            pygame.draw.rect(screen, ACCENT_EMERALD, (bar_x, bar_y, fill_w, 20), border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, fill_w, 20), width=2, border_radius=10)

    def draw_podium_dashboard(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 240))
        screen.blit(overlay, (0, 0))
        
        self.draw_floating_bubbles()
        
        title_surf = render_thai_text("🏆 สรุปผลการแข่งขัน (Tournament Champions)", font_size=42, color=ACCENT_SUNNY)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 70)))
        
        # Sort teams by Score (Descending), then by Time Spent (Ascending)
        ranked_teams = sorted(self.team_scores, key=lambda t: (-t["score"], t["time_spent"]))
        
        # 1. TOP 3 PODIUM (1st, 2nd, 3rd)
        podium_cx = WIDTH // 2
        podium_base_y = 390
        
        # Placement Positions: [Rank 2 (Left), Rank 1 (Center), Rank 3 (Right)]
        slots = [
            {"rank": 2, "idx": 1, "x": podium_cx - 190, "h": 140, "col": (148, 163, 184), "label": "🥈 2nd Place", "cup": "🥈"},
            {"rank": 1, "idx": 0, "x": podium_cx, "h": 190, "col": (245, 158, 11), "label": "🥇 Champion!", "cup": "🥇"},
            {"rank": 3, "idx": 2, "x": podium_cx + 190, "h": 100, "col": (180, 83, 9), "label": "🥉 3rd Place", "cup": "🥉"}
        ]
        
        for slot in slots:
            if slot["idx"] < len(ranked_teams):
                team = ranked_teams[slot["idx"]]
                sx = slot["x"]
                pw = 155
                ph = slot["h"]
                py = podium_base_y - ph
                
                # Pillar
                pygame.draw.rect(screen, slot["col"], (sx - pw // 2, py, pw, ph), border_radius=16)
                pygame.draw.rect(screen, (255, 255, 255), (sx - pw // 2, py, pw, ph), width=3, border_radius=16)
                
                # Rank Label on Pillar
                r_surf = render_thai_text(f"#{slot['rank']}", font_size=36, color=(15, 23, 42))
                screen.blit(r_surf, r_surf.get_rect(center=(sx, py + 45)))
                
                # Team Info Above Pillar
                cup_surf = render_thai_text(slot["cup"], font_size=38)
                screen.blit(cup_surf, cup_surf.get_rect(center=(sx, py - 65)))
                
                tname_surf = render_thai_text(f"{team['emoji']} {team['name']}", font_size=20, color=team["color"])
                screen.blit(tname_surf, tname_surf.get_rect(center=(sx, py - 32)))
                
                score_surf = render_thai_text(f"{team['score']} pts", font_size=20, color=TEXT_WHITE)
                screen.blit(score_surf, score_surf.get_rect(center=(sx, py - 10)))
                
        # 2. Ranking Leaderboard Table
        table_y = 435
        header_surf = pygame.Surface((720, 36), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (30, 41, 59, 230), (0, 0, 720, 36), border_radius=8)
        screen.blit(header_surf, (WIDTH // 2 - 360, table_y))
        
        th1 = render_thai_text("อันดับ", font_size=16, color=ACCENT_SKY)
        th2 = render_thai_text("ทีม", font_size=16, color=ACCENT_SKY)
        th3 = render_thai_text("คะแนนสะสม", font_size=16, color=ACCENT_SKY)
        th4 = render_thai_text("เวลาที่ใช้", font_size=16, color=ACCENT_SKY)
        screen.blit(th1, (WIDTH // 2 - 330, table_y + 4))
        screen.blit(th2, (WIDTH // 2 - 200, table_y + 4))
        screen.blit(th3, (WIDTH // 2 + 40, table_y + 4))
        screen.blit(th4, (WIDTH // 2 + 220, table_y + 4))
        
        for i, team in enumerate(ranked_teams):
            row_y = table_y + 42 + i * 36
            row_surf = pygame.Surface((720, 32), pygame.SRCALPHA)
            bg = (245, 158, 11, 40) if i == 0 else (17, 24, 39, 180)
            pygame.draw.rect(row_surf, bg, (0, 0, 720, 32), border_radius=6)
            screen.blit(row_surf, (WIDTH // 2 - 360, row_y))
            
            r_label = f"#{i+1}" if i >= 3 else ["🥇 1st", "🥈 2nd", "🥉 3rd"][i]
            td1 = render_thai_text(r_label, font_size=16, color=TEXT_WHITE)
            td2 = render_thai_text(f"{team['emoji']} {team['name']}", font_size=16, color=team["color"])
            td3 = render_thai_text(f"{team['score']} คะแนน", font_size=16, color=ACCENT_SUNNY)
            td4 = render_thai_text(f"{team['time_spent']:.1f} วินาที", font_size=16, color=(148, 163, 184))
            
            screen.blit(td1, (WIDTH // 2 - 330, row_y + 2))
            screen.blit(td2, (WIDTH // 2 - 200, row_y + 2))
            screen.blit(td3, (WIDTH // 2 + 40, row_y + 2))
            screen.blit(td4, (WIDTH // 2 + 220, row_y + 2))
            
        # Action Buttons (Play Again / Main Menu)
        mouse_pos = pygame.mouse.get_pos()
        clicked = pygame.mouse.get_pressed()[0]
        
        btn_replay = pygame.Rect(WIDTH // 2 - 210, HEIGHT - 75, 195, 52)
        btn_menu = pygame.Rect(WIDTH // 2 + 15, HEIGHT - 75, 195, 52)
        
        rep_hover = btn_replay.collidepoint(mouse_pos)
        men_hover = btn_menu.collidepoint(mouse_pos)
        
        pygame.draw.rect(screen, ACCENT_SUNNY if rep_hover else (217, 119, 6), btn_replay, border_radius=26)
        pygame.draw.rect(screen, (255, 255, 255), btn_replay, width=2, border_radius=26)
        t_rep = render_thai_text("🔄 แข่งอีกครั้ง", font_size=20, color=(15, 23, 42))
        screen.blit(t_rep, t_rep.get_rect(center=btn_replay.center))
        
        pygame.draw.rect(screen, (51, 65, 85) if not men_hover else (71, 85, 105), btn_menu, border_radius=26)
        pygame.draw.rect(screen, (255, 255, 255), btn_menu, width=2, border_radius=26)
        t_men = render_thai_text("🏠 กลับหน้าหลัก", font_size=20, color=TEXT_WHITE)
        screen.blit(t_men, t_men.get_rect(center=btn_menu.center))
        
        if clicked:
            if rep_hover:
                self.state = "TEAM_SETUP"
            elif men_hover:
                self.state = "LANDING_MENU"

    def draw(self, bg_cam=None):
        screen.fill(BG_COLOR)
        
        if bg_cam is not None:
            surf_cam = pygame.surfarray.make_surface(np.transpose(bg_cam, (1, 0, 2)))
            screen.blit(surf_cam, (0, 0))
            
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 110))
        screen.blit(dim, (0, 0))
        
        if self.state == "LANDING_MENU":
            self.draw_landing_menu()
            self.draw_cursor_and_skeleton()
            return
            
        if self.state == "TEAM_SETUP":
            self.draw_team_setup()
            self.draw_cursor_and_skeleton()
            return
            
        if self.state == "TEAM_READY":
            self.draw_team_ready()
            self.draw_cursor_and_skeleton()
            return
            
        if self.state == "PODIUM_DASHBOARD":
            self.draw_podium_dashboard()
            self.draw_cursor_and_skeleton()
            return

        # Top In-Game HUD Header
        hud_h = 74
        header_surf = pygame.Surface((WIDTH, hud_h), pygame.SRCALPHA)
        header_surf.fill((15, 23, 42, 235))
        pygame.draw.line(header_surf, CARD_BORDER, (0, hud_h - 1), (WIDTH, hud_h - 1), 2)
        screen.blit(header_surf, (0, 0))
        
        # Menu Exit Button (Top-Left)
        menu_btn = pygame.Rect(18, 14, 110, 46)
        m_hover = menu_btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (51, 65, 85) if not m_hover else (71, 85, 105), menu_btn, border_radius=20)
        m_text = render_thai_text("🏠 เมนู", font_size=18, color=TEXT_WHITE)
        screen.blit(m_text, m_text.get_rect(center=menu_btn.center))
        if pygame.mouse.get_pressed()[0] and m_hover:
            self.state = "LANDING_MENU"
            return
        
        # Current Mode & Team Badge
        if self.mode == "FREEDOM":
            m_badge = render_thai_text("🌟 Freedom Mode", font_size=20, color=ACCENT_SKY)
            screen.blit(m_badge, (140, 24))
            
            score_text = render_thai_text(f"⭐ คะแนน: {self.freedom_score}", font_size=24, color=ACCENT_SUNNY)
            screen.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
        else:
            team = self.team_scores[self.current_team_idx]
            m_badge = render_thai_text(f"{team['emoji']} {team['name']} • คำที่ {team['words_done'] + 1}/{self.words_per_team}", font_size=22, color=team["color"])
            screen.blit(m_badge, (140, 24))
            
            score_text = render_thai_text(f"⭐ แต้มทีม: {team['score']}", font_size=24, color=ACCENT_SUNNY)
            screen.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
            
        # Chances Display
        chances_surf = render_thai_text(f"❤️ x {self.chances_left}", font_size=22, color=ACCENT_ROSE)
        screen.blit(chances_surf, chances_surf.get_rect(center=(WIDTH // 2, 37)))

        # State Renderings
        if self.state == "ROULETTE":
            self.wheel.draw(screen)
            r_tip = render_thai_text("กำลังสุ่มท่าทางที่ต้องใช้...", font_size=32, color=ACCENT_AMBER)
            screen.blit(r_tip, r_tip.get_rect(center=(WIDTH // 2, HEIGHT - 55)))
            
        elif self.state == "ANNOUNCE":
            self.wheel.draw(screen)
            banner = pygame.Surface((700, 110), pygame.SRCALPHA)
            pygame.draw.rect(banner, (15, 23, 42, 245), (0, 0, 700, 110), border_radius=24)
            pygame.draw.rect(banner, self.selected_gesture["color"], (0, 0, 700, 110), width=4, border_radius=24)
            screen.blit(banner, (WIDTH // 2 - 350, HEIGHT - 135))
            
            t1 = render_thai_text(f"ท่าที่ต้องใช้: {self.selected_gesture['emoji']} {self.selected_gesture['name']}", font_size=30, color=self.selected_gesture["color"])
            t2 = render_thai_text(self.selected_gesture["desc"], font_size=20, color=TEXT_WHITE)
            screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT - 100)))
            screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT - 55)))
            
        elif self.state == "MEMORIZE":
            t_banner = pygame.Surface((640, 80), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 640, 80), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_SUNNY, (0, 0, 640, 80), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 320, 100))
            
            w_text = render_thai_text(f"👀 จำตำแหน่งการ์ด! หาคำว่า: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_SUNNY)
            screen.blit(w_text, w_text.get_rect(center=(WIDTH // 2, 140)))
            
            for card in self.cards:
                card.draw(screen, show_face=True)
                
        elif self.state == "COUNTDOWN":
            for card in self.cards:
                card.draw(screen, show_face=False)
                
            cd_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            cd_overlay.fill((15, 23, 42, 160))
            screen.blit(cd_overlay, (0, 0))
            
            pulse = 1.0 + (math.sin(time.time() * 12) * 0.15)
            cd_size = int(120 * pulse)
            cd_surf = render_thai_text(str(self.countdown_num), font_size=cd_size, color=ACCENT_SUNNY)
            screen.blit(cd_surf, cd_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            
            sub_cd = render_thai_text("เตรียมพร้อม...", font_size=36, color=TEXT_WHITE)
            screen.blit(sub_cd, sub_cd.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))
            
        elif self.state == "PLAY":
            t_banner = pygame.Surface((680, 85), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 680, 85), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_CYAN, (0, 0, 680, 85), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 340, 100))
            
            target_surf = render_thai_text(f"🎯 จงหา: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_SUNNY)
            screen.blit(target_surf, target_surf.get_rect(center=(WIDTH // 2, 126)))
            
            inst_surf = render_thai_text(f"ใช้ท่า: {self.selected_gesture['emoji']} {self.selected_gesture['name']} ค้างบนการ์ดเพื่อเปิด", font_size=18, color=self.selected_gesture["color"])
            screen.blit(inst_surf, inst_surf.get_rect(center=(WIDTH // 2, 158)))
            
            for card in self.cards:
                card.draw(screen, show_face=False)
                
            if self.feedback_msg:
                fb_surf = render_thai_text(self.feedback_msg, font_size=24, color=self.feedback_color)
                screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, HEIGHT - 35)))
                
        elif self.state == "ROUND_END":
            for card in self.cards:
                card.draw(screen, show_face=card.is_matched)
                
            if self.feedback_msg:
                fb_banner = pygame.Surface((680, 60), pygame.SRCALPHA)
                pygame.draw.rect(fb_banner, (15, 23, 42, 245), (0, 0, 680, 60), border_radius=16)
                pygame.draw.rect(fb_banner, self.feedback_color, (0, 0, 680, 60), width=3, border_radius=16)
                screen.blit(fb_banner, (WIDTH // 2 - 340, HEIGHT - 70))
                
                fb_surf = render_thai_text(self.feedback_msg, font_size=24, color=self.feedback_color)
                screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        self.draw_cursor_and_skeleton()

    def draw_cursor_and_skeleton(self):
        self.draw_hand_skeleton()
        
        # Cursor indicator
        cx, cy = int(self.cursor_pos[0]), int(self.cursor_pos[1])
        cursor_col = ACCENT_AMBER if self.is_pinched else (ACCENT_EMERALD if self.current_detected_gesture == "OK" else ACCENT_CYAN)
        
        pygame.draw.circle(screen, cursor_col, (cx, cy), 18, width=3)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 5)
        
        if self.current_detected_gesture != "NONE":
            g_tag = render_thai_text(f"🖐️ {self.current_detected_gesture}", font_size=15, color=cursor_col)
            screen.blit(g_tag, (cx + 20, cy - 12))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in ["LANDING_MENU", "PODIUM_DASHBOARD"]:
                            running = False
                        else:
                            self.state = "LANDING_MENU"

            bg_cam = self.process_hand_tracking()
            self.update()
            self.draw(bg_cam)
            
            pygame.display.flip()
            clock.tick(60)

        if self.cap:
            self.cap.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GestureMemoryGame()
    game.run()
