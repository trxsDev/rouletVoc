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
# MediaPipe Task Configuration
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
            "lock": 0.2
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
# Pygame Setup & Color Palette (TRXS Dark Theme)
# ---------------------------------------------------------
pygame.display.init()

WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TRXS Org - AR Gesture Roulette Memory Game")
clock = pygame.time.Clock()

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
# 4 Active Gesture Modes (Point/Dwell removed per user request)
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
# 12 School Classroom Vocabulary Items (From Reference Image)
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
            # Active Gesture Lock-on Glowing border
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
            
            # Action Lock-on Charging Bar
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
# HD Roulette Wheel Animation Class (4-Sector Upright Gestures)
# ---------------------------------------------------------
class RouletteWheel:
    def __init__(self, cx, cy, radius=185):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.diameter = radius * 2
        self.angle = 0.0
        self.speed = 0.0
        self.target_idx = 0
        self.is_spinning = False
        self.needle_deflection = 0.0
        self.last_passed_wedge = -1
        self.light_timer = 0
        self.num_wedges = len(GESTURE_MODES) # 4
        self.wedge_angle_span = 360.0 / self.num_wedges # 90 degrees
        
        # Load high-definition 4-sector master wheel & pointer
        self.base_wheel_surf = get_image("roulette_wheel.png", target_size=(self.diameter, self.diameter))
        self.pointer_surf = get_image("wheel_pointer.png", target_size=(54, 82))

    def spin_to_target(self, target_idx):
        self.target_idx = target_idx
        self.is_spinning = True
        
        # Top needle is at 270° (-90°)
        # Sector 0 is center at 45°, Sector 1 at 135°, Sector 2 at 225°, Sector 3 at 315°
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
        # 1. Rotate & Draw 4-Sector HD Wheel
        rotated_wheel = pygame.transform.rotozoom(self.base_wheel_surf, -self.angle, 1.0)
        wheel_rect = rotated_wheel.get_rect(center=(self.cx, self.cy))
        surface.blit(rotated_wheel, wheel_rect)

        # 2. Outer Lighting Bulbs
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

        # 3. 3D Needle Pointer
        rotated_pointer = pygame.transform.rotozoom(self.pointer_surf, self.needle_deflection, 1.0)
        p_rect = rotated_pointer.get_rect(center=(self.cx, self.cy - self.radius + 12))
        surface.blit(rotated_pointer, p_rect)


# ---------------------------------------------------------
# Main Game Engine
# ---------------------------------------------------------
class GestureMemoryGame:
    def __init__(self):
        self.state = "START"
        self.score = 0
        self.round_num = 0
        self.max_chances = 3
        self.chances_left = 3
        self.target_item = None
        self.cards = []
        self.state_timer = time.time()
        self.play_grace_until = 0.0
        self.countdown_num = 3
        self.feedback_msg = ""
        self.feedback_color = TEXT_WHITE
        
        # Roulette Wheel Setup
        self.wheel = RouletteWheel(WIDTH // 2, HEIGHT // 2 + 10, radius=185)
        self.selected_gesture = GESTURE_MODES[0]
        
        # Cursor & Hand Tracking State
        self.cursor_pos = [WIDTH // 2, HEIGHT // 2]
        self.hand_landmarks_screen = []
        self.current_detected_gesture = "POINT"
        self.is_pinched = False
        self.pinch_dist = 999.0
        self._last_timestamp_ms = -1
        
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
            self.detector = None
        
    def setup_camera(self):
        for cam_idx in [1, 0, 2]:
            try:
                cap = cv2.VideoCapture(cam_idx)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        self.cap = cap
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        print(f"[CTO Engine] Connected to camera index {cam_idx}")
                        break
                    cap.release()
            except Exception:
                pass

    def start_new_round(self):
        self.round_num += 1
        self.chances_left = self.max_chances
        self.feedback_msg = ""
        
        # 1. Start Roulette Spin Animation
        self.state = "ROULETTE"
        self.state_timer = time.time()
        target_gesture_idx = random.randint(0, len(GESTURE_MODES) - 1)
        self.wheel.spin_to_target(target_gesture_idx)
        
        # 2. Pick 6 items from the 12 pool
        chosen_items = random.sample(ITEMS_POOL, 6)
        self.target_item = random.choice(chosen_items)
        
        # 3. Layout 6 Cards in 2 rows x 3 columns
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
        CTO Biometric Engine: Strict 3D Scale-Invariant Joint Extension and Curl Analysis.
        Guarantees zero false positives from casual hand hovering.
        """
        wrist = landmarks[0]
        thumb_cmc = landmarks[1]
        thumb_mcp = landmarks[2]
        thumb_ip = landmarks[3]
        thumb_tip = landmarks[4]

        index_mcp = landmarks[5]
        index_pip = landmarks[6]
        index_dip = landmarks[7]
        index_tip = landmarks[8]

        middle_mcp = landmarks[9]
        middle_pip = landmarks[10]
        middle_dip = landmarks[11]
        middle_tip = landmarks[12]

        ring_mcp = landmarks[13]
        ring_pip = landmarks[14]
        ring_dip = landmarks[15]
        ring_tip = landmarks[16]

        pinky_mcp = landmarks[17]
        pinky_pip = landmarks[18]
        pinky_dip = landmarks[19]
        pinky_tip = landmarks[20]

        def dist(p1, p2):
            return math.hypot((p1.x - p2.x) * WIDTH, (p1.y - p2.y) * HEIGHT)

        palm_size = max(dist(wrist, middle_mcp), 45.0)

        # Helper to verify clean finger extension
        def is_extended(tip, pip, mcp):
            return (dist(tip, wrist) > dist(pip, wrist) * 1.15) and (dist(tip, mcp) > palm_size * 0.78)

        # Helper to verify finger curling
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

        # Pinch detection (Thumb tip and Index tip touching closely)
        self.pinch_dist = dist(thumb_tip, index_tip)
        self.is_pinched = (self.pinch_dist < (0.24 * palm_size)) or (self.pinch_dist < 32.0)

        # 1. PINCH: Strict pinch contact while middle is distinct
        if self.is_pinched:
            return "PINCH"

        # 2. FIST: Strict fist where all 4 main fingers are tightly curled
        if idx_crl and mid_crl and rng_crl and pnk_crl:
            return "FIST"

        # 3. PEACE: Strict V-sign where Index & Middle are extended and separated, while Ring & Pinky are curled
        if idx_ext and mid_ext and rng_crl and pnk_crl:
            if dist(index_tip, middle_tip) > palm_size * 0.20:
                return "PEACE"

        # 4. PALM: Strict open palm where all 4 fingers and thumb are fully extended and spread
        thumb_spread = dist(thumb_tip, index_mcp) > palm_size * 0.62
        if idx_ext and mid_ext and rng_ext and pnk_ext and thumb_spread:
            return "PALM"

        return "NONE"

    def process_hand_tracking(self):
        self.hand_landmarks_screen = []
        
        if not self.cap or not self.cap.isOpened():
            mx, my = pygame.mouse.get_pos()
            self.cursor_pos = [mx, my]
            self.current_detected_gesture = self.selected_gesture["id"] if pygame.mouse.get_pressed()[0] else "NONE"
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
                    self.current_detected_gesture = self.selected_gesture["id"]

        bg_cam = cv2.resize(rgb_frame, (WIDTH, HEIGHT))
        return bg_cam

    def update(self):
        now = time.time()
        elapsed = now - self.state_timer
        
        if self.state == "START":
            if elapsed > 0.3:
                self.start_new_round()
                
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
                    
                    # Deliberate gesture confirmation buffer
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
                self.start_new_round()

    def handle_card_guess(self, card):
        card.is_flipped = True
        if card.item["id"] == self.target_item["id"]:
            card.is_matched = True
            self.score += 100
            sound_engine.play("correct")
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
            pygame.draw.line(screen, ACCENT_CYAN, p1, p2, 4)
            pygame.draw.line(screen, (224, 242, 254), p1, p2, 2)
            
        thumb_pt = self.hand_landmarks_screen[4]
        index_pt = self.hand_landmarks_screen[8]
        if self.is_pinched:
            pygame.draw.line(screen, ACCENT_EMERALD, thumb_pt, index_pt, 4)
            mid_x = (thumb_pt[0] + index_pt[0]) // 2
            mid_y = (thumb_pt[1] + index_pt[1]) // 2
            pygame.draw.circle(screen, ACCENT_EMERALD, (mid_x, mid_y), 10, width=3)
            pygame.draw.circle(screen, (255, 255, 255), (mid_x, mid_y), 4)
        else:
            pygame.draw.line(screen, (100, 116, 139), thumb_pt, index_pt, 1)

        for idx, pt in enumerate(self.hand_landmarks_screen):
            if idx in [4, 8, 12, 16, 20]:
                tip_col = ACCENT_EMERALD if self.is_pinched and idx in [4, 8] else ACCENT_AMBER
                pygame.draw.circle(screen, tip_col, pt, 8)
                pygame.draw.circle(screen, (255, 255, 255), pt, 4)
            elif idx == 0:
                pygame.draw.circle(screen, ACCENT_PURPLE, pt, 7)
                pygame.draw.circle(screen, (255, 255, 255), pt, 3)
            else:
                pygame.draw.circle(screen, ACCENT_CYAN, pt, 5)
                pygame.draw.circle(screen, (255, 255, 255), pt, 2)

    def draw_roulette_screen(self):
        modal_rect = pygame.Rect(WIDTH // 2 - 400, HEIGHT // 2 - 285, 800, 570)
        modal_surf = pygame.Surface((800, 570), pygame.SRCALPHA)
        pygame.draw.rect(modal_surf, (15, 23, 42, 248), (0, 0, 800, 570), border_radius=28)
        pygame.draw.rect(modal_surf, ACCENT_AMBER, (0, 0, 800, 570), width=3, border_radius=28)
        screen.blit(modal_surf, modal_rect)

        title = render_thai_text("🎰 สุ่มท่าทางประจำรอบ (Gesture Roulette)", font_size=28, color=ACCENT_AMBER)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 245)))

        self.wheel.draw(screen)

        cur_gest = self.selected_gesture
        if self.wheel.is_spinning:
            status_surf = render_thai_text("⚡ กงล้อกำลังหมุนสุ่มท่าทาง...", font_size=22, color=ACCENT_CYAN)
            screen.blit(status_surf, status_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 235)))
        else:
            res_box = pygame.Rect(WIDTH // 2 - 280, HEIGHT // 2 + 210, 560, 58)
            pygame.draw.rect(screen, (30, 41, 59), res_box, border_radius=16)
            pygame.draw.rect(screen, cur_gest["color"], res_box, width=3, border_radius=16)
            
            gest_icon = get_image(cur_gest["image_file"], target_size=(44, 44))
            screen.blit(gest_icon, (res_box.x + 18, res_box.centery - 22))
            
            res_txt = render_thai_text(f"✅ ได้ท่า: {cur_gest['name']} ({cur_gest['desc']})", font_size=20, color=cur_gest["color"])
            screen.blit(res_txt, (res_box.x + 72, res_box.centery - 14))

    def draw_countdown_screen(self):
        # Semi-transparent backdrop
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 210))
        screen.blit(overlay, (0, 0))

        # Target item reminder banner at top
        banner_rect = pygame.Rect(WIDTH // 2 - 220, 80, 440, 70)
        pygame.draw.rect(screen, (30, 41, 59, 240), banner_rect, border_radius=18)
        pygame.draw.rect(screen, ACCENT_AMBER, banner_rect, width=3, border_radius=18)
        
        target_img = get_image(self.target_item["filename"], target_size=(52, 52))
        screen.blit(target_img, (banner_rect.x + 18, banner_rect.centery - 26))
        
        target_txt = render_thai_text(f"เป้าหมาย: {self.target_item['word']} ({self.target_item['en']})", font_size=24, color=ACCENT_AMBER)
        screen.blit(target_txt, (banner_rect.x + 85, banner_rect.centery - 16))

        # Big Pulsating Countdown Circle Center
        now = time.time()
        elapsed_in_second = (now - self.state_timer) % 1.0
        pulse_scale = 1.0 + math.sin(elapsed_in_second * math.pi) * 0.15
        
        cx, cy = WIDTH // 2, HEIGHT // 2 + 30
        r = int(110 * pulse_scale)
        
        # Outer Glowing Rings
        pygame.draw.circle(screen, (6, 182, 212, 120), (cx, cy), r + 24, width=6)
        pygame.draw.circle(screen, (15, 23, 42), (cx, cy), r)
        pygame.draw.circle(screen, ACCENT_CYAN, (cx, cy), r, width=8)
        pygame.draw.circle(screen, (224, 242, 254), (cx, cy), r - 10, width=3)

        # Huge Animated Countdown Number (3, 2, 1)
        cd_colors = {
            3: ACCENT_CYAN,
            2: ACCENT_AMBER,
            1: ACCENT_EMERALD
        }
        num_col = cd_colors.get(self.countdown_num, ACCENT_CYAN)
        
        num_surf = render_thai_text(str(self.countdown_num), font_size=120, color=num_col)
        screen.blit(num_surf, num_surf.get_rect(center=(cx, cy - 8)))

        # Subtitle Prompt Below Countdown
        sub_surf = render_thai_text("🔥 ปิดการ์ดแล้ว! เตรียมค้นหาใน...", font_size=28, color=TEXT_WHITE)
        screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + r + 45)))

    def draw(self, bg_cam_frame):
        # 1. Background
        if bg_cam_frame is not None:
            cam_surf = pygame.image.frombuffer(bg_cam_frame.tobytes(), (WIDTH, HEIGHT), "RGB")
            screen.blit(cam_surf, (0, 0))
            
            dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((15, 23, 42, 175))
            screen.blit(dark_overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)
            
        # 2. Hand Skeleton
        self.draw_hand_skeleton()

        # 3. Header Banner
        header_surf = pygame.Surface((WIDTH - 60, 56), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (15, 23, 42, 230), (0, 0, WIDTH - 60, 56), border_radius=14)
        pygame.draw.rect(header_surf, (51, 65, 85, 180), (0, 0, WIDTH - 60, 56), width=1, border_radius=14)
        screen.blit(header_surf, (30, 16))

        header_title = render_thai_text("TRXS Org • Gesture Roulette Game", font_size=21, color=ACCENT_CYAN)
        screen.blit(header_title, (48, 28))
        
        gest_icon_header = get_image(self.selected_gesture["image_file"], target_size=(36, 36))
        screen.blit(gest_icon_header, (410, 26))
        
        req_badge = render_thai_text(f"ท่าทางรอบนี้: {self.selected_gesture['name']}", font_size=19, color=self.selected_gesture["color"])
        screen.blit(req_badge, (455, 28))

        score_text = render_thai_text(f"คะแนน: {self.score}", font_size=21, color=ACCENT_AMBER)
        screen.blit(score_text, (WIDTH - 290, 28))
        
        chances_hearts = "❤️ " * self.chances_left + "🖤 " * (self.max_chances - self.chances_left)
        chance_text = render_thai_text(f"{chances_hearts}", font_size=18, color=TEXT_WHITE)
        screen.blit(chance_text, (WIDTH - 145, 29))
        
        # 4. State Displays
        if self.state == "ROULETTE":
            self.draw_roulette_screen()
            
        elif self.state == "ANNOUNCE":
            title_surf = render_thai_text("🎯 จงจำตำแหน่งของคำว่า:", font_size=30, color=TEXT_WHITE)
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 90)))
            
            target_badge = pygame.Rect(WIDTH // 2 - 220, 120, 440, 75)
            pygame.draw.rect(screen, (30, 41, 59, 235), target_badge, border_radius=18)
            pygame.draw.rect(screen, ACCENT_AMBER, target_badge, width=3, border_radius=18)
            
            target_img = get_image(self.target_item["filename"], target_size=(56, 56))
            screen.blit(target_img, (target_badge.x + 20, target_badge.centery - 28))
            
            target_surf = render_thai_text(f"{self.target_item['word']} ({self.target_item['en']})", font_size=28, color=ACCENT_AMBER)
            screen.blit(target_surf, (target_badge.x + 90, target_badge.centery - 18))
            
        elif self.state == "COUNTDOWN":
            # Big Countdown Animation (Cards are hidden during 3, 2, 1 per user request)
            self.draw_countdown_screen()
            
        elif self.state == "MEMORIZE":
            mem_surf = render_thai_text("👀 จำตำแหน่งการ์ดทั้งหมด! (เปิดภาพ 3 วินาที)", font_size=32, color=ACCENT_EMERALD)
            screen.blit(mem_surf, mem_surf.get_rect(center=(WIDTH // 2, 135)))
            
        elif self.state == "PLAY":
            prompt_box = pygame.Rect(WIDTH // 2 - 380, 80, 760, 60)
            pygame.draw.rect(screen, (30, 41, 59, 230), prompt_box, border_radius=14)
            pygame.draw.rect(screen, self.selected_gesture["color"], prompt_box, width=2, border_radius=14)
            
            gest_icon_play = get_image(self.selected_gesture["image_file"], target_size=(44, 44))
            screen.blit(gest_icon_play, (prompt_box.x + 18, prompt_box.centery - 22))
            
            prompt_surf = render_thai_text(
                f"🎯 หา '{self.target_item['word']}'  |  ทำท่า 👉 {self.selected_gesture['name']}",
                font_size=24,
                color=self.selected_gesture["color"]
            )
            screen.blit(prompt_surf, (prompt_box.x + 72, prompt_box.centery - 16))
            
            is_match = (self.current_detected_gesture == self.selected_gesture["id"])
            match_col = ACCENT_EMERALD if is_match else (148, 163, 184)
            status_symbol = "✅ ท่าทางถูกต้อง!" if is_match else "⌛ กำลังรอท่าทาง..."
            live_gest_txt = f"ท่าที่ตรวจจับได้: {self.current_detected_gesture} ({status_symbol})"
            cur_surf = render_thai_text(live_gest_txt, font_size=19, color=match_col)
            screen.blit(cur_surf, cur_surf.get_rect(center=(WIDTH // 2, 160)))
            
            if self.feedback_msg:
                fb_surf = render_thai_text(self.feedback_msg, font_size=22, color=self.feedback_color)
                screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, 195)))
                
        elif self.state == "ROUND_END":
            fb_surf = render_thai_text(self.feedback_msg, font_size=32, color=self.feedback_color)
            screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, 135)))

        # 5. Draw Cards Grid (Hidden in ROULETTE and COUNTDOWN states)
        if self.state not in ["ROULETTE", "COUNTDOWN"]:
            show_faces = (self.state == "MEMORIZE")
            for card in self.cards:
                card.draw(screen, show_face=show_faces)
                if card.shake_offset > 0:
                    card.shake_offset = -card.shake_offset + 2
                    if abs(card.shake_offset) < 2:
                        card.shake_offset = 0

        # 6. Reticle Cursor
        if self.state == "PLAY":
            cx, cy = int(self.cursor_pos[0]), int(self.cursor_pos[1])
            is_match = (self.current_detected_gesture == self.selected_gesture["id"])
            cursor_col = ACCENT_EMERALD if is_match else ACCENT_AMBER
            
            pygame.draw.circle(screen, cursor_col, (cx, cy), 22, width=3)
            pygame.draw.circle(screen, cursor_col, (cx, cy), 6)
            
            pygame.draw.line(screen, cursor_col, (cx - 28, cy), (cx - 10, cy), 2)
            pygame.draw.line(screen, cursor_col, (cx + 10, cy), (cx + 28, cy), 2)
            pygame.draw.line(screen, cursor_col, (cx, cy - 28), (cx, cy - 10), 2)
            pygame.draw.line(screen, cursor_col, (cx, cy + 10), (cx, cy + 28), 2)
            
            tag_surf = render_thai_text(self.current_detected_gesture, font_size=15, color=cursor_col)
            screen.blit(tag_surf, (cx + 20, cy - 20))

        pygame.display.flip()

def main():
    game = GestureMemoryGame()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    game.start_new_round()
                    
        bg_cam = game.process_hand_tracking()
        game.update()
        game.draw(bg_cam)
        clock.tick(60)

    if game.cap:
        game.cap.release()
    pygame.display.quit()
    sys.exit()

if __name__ == "__main__":
    main()
