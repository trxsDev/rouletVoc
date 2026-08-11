import cv2
import pygame
import numpy as np
import random
import time
import sys
import math
import os
import difflib
import urllib.request
import subprocess
import threading
from PIL import Image, ImageDraw, ImageFont

import speech_recognition as sr
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
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")

# ---------------------------------------------------------
# Low-Latency Non-Blocking Audio Engine
# ---------------------------------------------------------
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

    def play_vocab(self, word_id):
        """Plays studio-quality English pronunciation of the target word."""
        for ext in [".wav", ".mp3"]:
            filepath = os.path.join(AUDIO_DIR, f"{word_id}{ext}")
            if os.path.exists(filepath):
                threading.Thread(
                    target=lambda: subprocess.run(["afplay", filepath], capture_output=True),
                    daemon=True
                ).start()
                return

sound_engine = SoundEngine()

# ---------------------------------------------------------
# Pygame Setup & Color Palette (Sleek TRXS Dark Theme)
# ---------------------------------------------------------
pygame.display.init()

WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RouletVoc • AR Hand Gesture & Voice Vocabulary Game")
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

TEAM_PALETTES = [
    {"name": "Team 1", "thai": "ทีมที่ 1", "color": (239, 68, 68), "bg_col": (127, 29, 29), "emoji": "🔴"},
    {"name": "Team 2", "thai": "ทีมที่ 2", "color": (59, 130, 246), "bg_col": (30, 58, 138), "emoji": "🔵"},
    {"name": "Team 3", "thai": "ทีมที่ 3", "color": (16, 185, 129), "bg_col": (6, 78, 59), "emoji": "🟢"},
    {"name": "Team 4", "thai": "ทีมที่ 4", "color": (245, 158, 11), "bg_col": (120, 53, 15), "emoji": "🟡"},
    {"name": "Team 5", "thai": "ทีมที่ 5", "color": (168, 85, 247), "bg_col": (88, 28, 135), "emoji": "🟣"},
    {"name": "Team 6", "thai": "ทีมที่ 6", "color": (236, 72, 153), "bg_col": (131, 24, 67), "emoji": "🌸"},
    {"name": "Team 7", "thai": "ทีมที่ 7", "color": (249, 115, 22), "bg_col": (124, 45, 18), "emoji": "🟠"},
    {"name": "Team 8", "thai": "ทีมที่ 8", "color": (6, 182, 212), "bg_col": (14, 116, 144), "emoji": "🔷"}
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
# 12 School Classroom Vocabulary Items & Speech Aliases
# ---------------------------------------------------------
ITEMS_POOL = [
    {"id": "backpack", "word": "กระเป๋า", "en": "Backpack", "filename": "backpack.png", "color": (96, 165, 250), "aliases": ["backpack", "pack", "bag", "school bag", "back pack"]},
    {"id": "book", "word": "หนังสือ", "en": "Book", "filename": "book.png", "color": (56, 189, 248), "aliases": ["book", "books"]},
    {"id": "chair", "word": "เก้าอี้", "en": "Chair", "filename": "chair.png", "color": (251, 146, 60), "aliases": ["chair", "chairs", "cheer"]},
    {"id": "clock", "word": "นาฬิกา", "en": "Clock", "filename": "clock.png", "color": (248, 113, 113), "aliases": ["clock", "clocks", "watch"]},
    {"id": "eraser", "word": "ยางลบ", "en": "Eraser", "filename": "eraser.png", "color": (56, 189, 248), "aliases": ["eraser", "erasers", "rubber", "erase"]},
    {"id": "fan", "word": "พัดลม", "en": "Fan", "filename": "fan.png", "color": (56, 189, 248), "aliases": ["fan", "fans"]},
    {"id": "notebook", "word": "สมุด", "en": "Notebook", "filename": "notebook.png", "color": (74, 222, 128), "aliases": ["notebook", "notebooks", "note book", "note"]},
    {"id": "pen", "word": "ปากกา", "en": "Pen", "filename": "pen.png", "color": (129, 140, 248), "aliases": ["pen", "pens", "pan"]},
    {"id": "pencil", "word": "ดินสอ", "en": "Pencil", "filename": "pencil.png", "color": (251, 191, 36), "aliases": ["pencil", "pencils"]},
    {"id": "ruler", "word": "ไม้บรรทัด", "en": "Ruler", "filename": "ruler.png", "color": (245, 158, 11), "aliases": ["ruler", "rulers"]},
    {"id": "table", "word": "โต๊ะ", "en": "Table", "filename": "table.png", "color": (249, 115, 22), "aliases": ["table", "tables", "desk"]},
    {"id": "window", "word": "หน้าต่าง", "en": "Window", "filename": "window.png", "color": (250, 204, 21), "aliases": ["window", "windows"]}
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
        self.team_scores = []
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
        
        # Active Player Hand Lock-On Engine
        self.locked_hand_pos = None
        self.locked_palm_size = 0.0
        self.last_player_seen_time = 0.0
        
        # Speech Recognition & Voice Verification Engine
        self.speech_recognizer = sr.Recognizer()
        self.speech_recognizer.energy_threshold = 280
        self.speech_recognizer.dynamic_energy_threshold = True
        self.is_listening = False
        self.voice_attempts = 0
        self.voice_recognized_text = ""
        self.voice_success = False
        self.voice_feedback_msg = ""
        self.target_voice_played = False
        
        # Exhaustive Shuffled Decks (100% Vocabulary & Gesture Coverage)
        self.unplayed_vocab_deck = []
        self.unplayed_gesture_deck = []
        
        # MediaPipe Detector & Camera Setup
        self.detector = None
        self.cap = None
        self.setup_tracking_engine()
        self.setup_camera()

    def listen_speech_worker(self):
        """
        Background worker that listens to the microphone, recognizes English speech,
        and verifies pronunciation before awarding points.
        """
        try:
            with sr.Microphone() as source:
                self.speech_recognizer.adjust_for_ambient_noise(source, duration=0.6)
                if self.speech_recognizer.energy_threshold > 300:
                    self.speech_recognizer.energy_threshold = 300
                audio = self.speech_recognizer.listen(source, timeout=5.0, phrase_time_limit=4.0)
                
                try:
                    text = self.speech_recognizer.recognize_google(audio, language="en-US")
                except Exception:
                    try:
                        text = self.speech_recognizer.recognize_google(audio, language="th-TH")
                    except Exception:
                        text = ""
                        
                self.voice_recognized_text = text
                target_en = self.target_item["en"].lower()
                aliases = self.target_item.get("aliases", [target_en])
                
                is_correct = any(
                    (t in text.lower()) or 
                    (difflib.SequenceMatcher(None, t, text.lower()).ratio() >= 0.55)
                    for t in aliases
                )
                
                if is_correct:
                    self.voice_success = True
                    sound_engine.play("correct")
                    if self.mode == "FREEDOM":
                        self.freedom_score += 100
                        self.score = self.freedom_score
                    else:
                        self.team_scores[self.current_team_idx]["score"] += 100
                        self.score = self.team_scores[self.current_team_idx]["score"]
                    self.feedback_msg = f"🎉 ออกเสียงถูกต้อง! '{text}' (+100 คะแนน)"
                    self.feedback_color = ACCENT_EMERALD
                    time.sleep(1.4)
                    self.state = "ROUND_END"
                    self.state_timer = time.time()
                else:
                    self.voice_attempts += 1
                    sound_engine.play("wrong")
                    if self.voice_attempts >= 2:
                        self.feedback_msg = f"⚠️ ได้ยิน: '{text}' (หมดโควต้าฟังเสียง ข้ามไปรอบถัดไป)"
                        self.feedback_color = ACCENT_ROSE
                        time.sleep(1.6)
                        self.state = "ROUND_END"
                        self.state_timer = time.time()
                    else:
                        self.feedback_msg = f"⚠️ ได้ยิน: '{text}' (ยังไม่ถูกต้อง ลองออกเสียงใหม่อีกครั้ง!)"
                        self.feedback_color = ACCENT_AMBER
                        self.state_timer = time.time()
                        time.sleep(0.8)
                        if self.state == "VOICE_VERIFY":
                            threading.Thread(target=self.listen_speech_worker, daemon=True).start()
        except sr.WaitTimeoutError:
            self.voice_attempts += 1
            if self.voice_attempts >= 2:
                self.feedback_msg = "⏱️ หมดเวลาฟังเสียง! ข้ามไปรอบถัดไป"
                self.feedback_color = ACCENT_ROSE
                time.sleep(1.4)
                self.state = "ROUND_END"
                self.state_timer = time.time()
            else:
                self.feedback_msg = "⏱️ ไม่ได้ยินเสียง ลองพูดใหม่อีกครั้ง..."
                self.feedback_color = ACCENT_AMBER
                self.state_timer = time.time()
                if self.state == "VOICE_VERIFY":
                    threading.Thread(target=self.listen_speech_worker, daemon=True).start()
        except Exception as e:
            print("[Speech Engine] Recognition error:", e)
            self.feedback_msg = "ข้ามการตรวจจับเสียงไปยังรอบถัดไป"
            self.feedback_color = ACCENT_AMBER
            time.sleep(1.0)
            self.state = "ROUND_END"
            self.state_timer = time.time()
        finally:
            self.is_listening = False

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
                num_hands=4,  # Detect all hands in frame to filter out background bystanders
                min_hand_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[CTO Engine] MediaPipe Tasks HandLandmarker (Multi-Hand Lock-On) initialized successfully!")
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

    def get_next_target_item(self):
        """
        Exhaustive Bag: Ensures 100% of all 12 vocabulary items are played
        as targets before any word repeats.
        """
        if not self.unplayed_vocab_deck:
            self.unplayed_vocab_deck = random.sample(ITEMS_POOL, len(ITEMS_POOL))
        return self.unplayed_vocab_deck.pop(0)

    def get_next_gesture_target(self):
        """
        Exhaustive Bag: Ensures all 4 gestures are evenly distributed across rounds.
        """
        if not self.unplayed_gesture_deck:
            self.unplayed_gesture_deck = random.sample(list(range(len(GESTURE_MODES))), len(GESTURE_MODES))
        return self.unplayed_gesture_deck.pop(0)

    def start_team_tournament(self):
        self.unplayed_vocab_deck = []
        self.unplayed_gesture_deck = []
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
        self.target_voice_played = False
        
        # 1. Draw next target gesture from exhaustive bag
        target_gesture_idx = self.get_next_gesture_target()
        self.wheel.spin_to_target(target_gesture_idx)
        
        # 2. Draw next target vocabulary from exhaustive bag (100% coverage)
        self.target_item = self.get_next_target_item()
        
        # 3. Pick 5 distinct distractor items from remaining pool
        distractors = [item for item in ITEMS_POOL if item["id"] != self.target_item["id"]]
        chosen_distractors = random.sample(distractors, 5)
        
        # 4. Combine target + 5 distractors and shuffle board positions randomly
        chosen_items = [self.target_item] + chosen_distractors
        random.shuffle(chosen_items)
        
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

        # Finger tip distances
        thumb_idx_dist = dist(thumb_tip, index_tip)
        self.pinch_dist = thumb_idx_dist
        self.is_pinched = (thumb_idx_dist < (0.28 * palm_size)) or (thumb_idx_dist < 36.0)

        # 1. OK Gesture (👌) - Natural, high-tolerance detection
        # Thumb and Index tip touching or near, while other fingers are open/unfolded
        thumb_index_touch = (thumb_idx_dist < (0.42 * palm_size)) or (thumb_idx_dist < 56.0)
        open_fingers_count = int(mid_ext or not mid_crl) + int(rng_ext or not rng_crl) + int(pnk_ext or not pnk_crl)
        
        if thumb_index_touch and (not mid_crl) and (open_fingers_count >= 2):
            return "OK"

        # 2. PINCH
        if self.is_pinched:
            return "PINCH"

        # 3. FIST
        if idx_crl and mid_crl and rng_crl and pnk_crl:
            return "FIST"

        # 4. PEACE
        if idx_ext and mid_ext and rng_crl and pnk_crl:
            if dist(index_tip, middle_tip) > palm_size * 0.18:
                return "PEACE"

        # 5. PALM
        thumb_spread = dist(thumb_tip, index_mcp) > palm_size * 0.58
        if idx_ext and mid_ext and rng_ext and pnk_ext and thumb_spread:
            return "PALM"

        return "NONE"

    def process_hand_tracking(self):
        self.hand_landmarks_screen = []
        
        # 1. Before game starts (Menu screens) -> Completely pause MediaPipe detection
        if self.state in ["LANDING_MENU", "TEAM_SETUP", "PODIUM_DASHBOARD"]:
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
            if not self.cap or not self.cap.isOpened():
                return None
            ret, frame = self.cap.read()
            if not ret:
                return None
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return cv2.resize(rgb_frame, (WIDTH, HEIGHT))

        # 2. In-Game -> Active 100% Camera Hand Tracking
        if not self.cap or not self.cap.isOpened():
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
            return None

        ret, frame = self.cap.read()
        if not ret:
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
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
                    best_lm = None
                    best_score = 999999.0
                    now = time.time()
                    has_recent_lock = (self.locked_hand_pos is not None) and ((now - self.last_player_seen_time) < 1.0)
                    
                    for candidate_lm in result.hand_landmarks:
                        wrist = candidate_lm[0]
                        mid_mcp = candidate_lm[9]
                        cx = int(wrist.x * WIDTH)
                        cy = int(wrist.y * HEIGHT)
                        palm_size = math.hypot((wrist.x - mid_mcp.x) * WIDTH, (wrist.y - mid_mcp.y) * HEIGHT)
                        
                        # Discard tiny/distant background bystander hands
                        if palm_size < 35.0:
                            continue
                            
                        if has_recent_lock:
                            # Track existing player: Minimum distance to previous track + size consistency
                            dist_to_prev = math.hypot(cx - self.locked_hand_pos[0], cy - self.locked_hand_pos[1])
                            scale_diff = abs(palm_size - self.locked_palm_size)
                            score = dist_to_prev + scale_diff * 1.5 - (palm_size * 0.4)
                        else:
                            # Lock on to new player: Largest foreground palm size + closest to center
                            dist_center = math.hypot(cx - WIDTH // 2, cy - HEIGHT // 2)
                            score = dist_center * 0.3 - (palm_size * 2.0)
                            
                        if score < best_score:
                            best_score = score
                            best_lm = candidate_lm
                            
                    if best_lm is not None:
                        lm = best_lm
                        self.hand_landmarks_screen = [(int(p.x * WIDTH), int(p.y * HEIGHT)) for p in lm]
                        
                        wrist = lm[0]
                        mid_mcp = lm[9]
                        self.locked_hand_pos = (int(wrist.x * WIDTH), int(wrist.y * HEIGHT))
                        self.locked_palm_size = math.hypot((wrist.x - mid_mcp.x) * WIDTH, (wrist.y - mid_mcp.y) * HEIGHT)
                        self.last_player_seen_time = time.time()
                        
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
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"

        bg_cam = cv2.resize(rgb_frame, (WIDTH, HEIGHT))
        return bg_cam

    def update(self):
        now = time.time()
        elapsed = now - self.state_timer
        
        if self.state == "LANDING_MENU":
            pass
            
        elif self.state == "TEAM_SETUP":
            pass
            
        elif self.state == "TEAM_READY":
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
                sound_engine.play("wheel_win")
                self.state = "ANNOUNCE"
                self.state_timer = now
                
        elif self.state == "ANNOUNCE":
            if elapsed > 2.2:
                self.state = "TARGET_FOCUS_READ"
                self.state_timer = now
                self.target_voice_played = False
                
        elif self.state == "TARGET_FOCUS_READ":
            # Play English pronunciation aloud when the card is in full focus
            if elapsed >= 0.8 and not self.target_voice_played:
                sound_engine.play_vocab(self.target_item["id"])
                self.target_voice_played = True
                
            if elapsed > 4.6:
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
                    
        elif self.state == "VOICE_VERIFY":
            # Managed asynchronously by listen_speech_worker
            pass
            
        elif self.state == "ROUND_END":
            if elapsed > 2.8:
                if self.mode == "FREEDOM":
                    self.start_new_round()
                else:
                    team = self.team_scores[self.current_team_idx]
                    team["words_done"] += 1
                    team["time_spent"] += (now - self.team_start_time)
                    
                    if team["words_done"] < self.words_per_team:
                        self.start_team_turn()
                    else:
                        self.current_team_idx += 1
                        if self.current_team_idx < self.num_teams:
                            self.team_ready_charge = 0.0
                            self.locked_hand_pos = None
                            self.state = "TEAM_READY"
                            self.state_timer = now
                        else:
                            sound_engine.play("podium_fanfare")
                            self.locked_hand_pos = None
                            self.state = "PODIUM_DASHBOARD"
                            self.state_timer = now

    def handle_card_guess(self, card):
        card.is_flipped = True
        if card.item["id"] == self.target_item["id"]:
            card.is_matched = True
            sound_engine.play("lock")
            
            # Transition to Voice Verification: Score is awarded ONLY after speaking correctly!
            self.state = "VOICE_VERIFY"
            self.state_timer = time.time()
            self.voice_attempts = 0
            self.voice_recognized_text = ""
            self.voice_success = False
            self.is_listening = True
            self.feedback_msg = f"🎙️ กรุณาออกเสียง: '{self.target_item['en'].upper()}' ({self.target_item['word']})"
            self.feedback_color = ACCENT_AMBER
            threading.Thread(target=self.listen_speech_worker, daemon=True).start()
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
            pygame.draw.line(screen, ACCENT_AMBER, thumb_pt, index_pt, 6)
            mid_x = (thumb_pt[0] + index_pt[0]) // 2
            mid_y = (thumb_pt[1] + index_pt[1]) // 2
            pygame.draw.circle(screen, ACCENT_AMBER, (mid_x, mid_y), 16)
            pygame.draw.circle(screen, (255, 255, 255), (mid_x, mid_y), 9)

        for pt in self.hand_landmarks_screen:
            pygame.draw.circle(screen, ACCENT_EMERALD, pt, 5)
            pygame.draw.circle(screen, (255, 255, 255), pt, 2)

    def draw_landing_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 235))
        screen.blit(overlay, (0, 0))
        
        # Clean Title & Subtitle
        title_surf = render_thai_text("🎡 RouletVoc", font_size=56, color=ACCENT_AMBER)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 130))
        screen.blit(title_surf, title_rect)
        
        sub_surf = render_thai_text("เกมวงล้อจับคู่คำศัพท์ & ท่าทางมือ AR", font_size=22, color=ACCENT_CYAN)
        sub_rect = sub_surf.get_rect(center=(WIDTH // 2, 180))
        screen.blit(sub_surf, sub_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        card_w, card_h = 360, 310
        gap = 50
        
        # 1. Freedom Mode Card
        c1_x = (WIDTH - (2 * card_w + gap)) // 2
        c1_y = 245
        c1_rect = pygame.Rect(c1_x, c1_y, card_w, card_h)
        c1_hover = c1_rect.collidepoint(mouse_pos)
        
        c1_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        c1_bg = (30, 48, 75, 245) if c1_hover else (20, 30, 48, 235)
        c1_border = ACCENT_CYAN if c1_hover else CARD_BORDER
        pygame.draw.rect(c1_surf, c1_bg, (0, 0, card_w, card_h), border_radius=20)
        pygame.draw.rect(c1_surf, c1_border, (0, 0, card_w, card_h), width=3 if c1_hover else 2, border_radius=20)
        screen.blit(c1_surf, (c1_x, c1_y))
        
        badge1 = render_thai_text("🌟 Freedom Mode", font_size=28, color=ACCENT_CYAN)
        screen.blit(badge1, badge1.get_rect(center=(c1_rect.centerx, c1_y + 55)))
        
        desc1_1 = render_thai_text("โหมดเล่นอิสระ สะสมคะแนนเรื่อยๆ", font_size=18, color=TEXT_WHITE)
        desc1_2 = render_thai_text("เล่นเพลินไม่มีกำหนดรอบเวลา", font_size=16, color=(148, 163, 184))
        screen.blit(desc1_1, desc1_1.get_rect(center=(c1_rect.centerx, c1_y + 120)))
        screen.blit(desc1_2, desc1_2.get_rect(center=(c1_rect.centerx, c1_y + 155)))
        
        btn1_surf = pygame.Surface((230, 50), pygame.SRCALPHA)
        pygame.draw.rect(btn1_surf, ACCENT_CYAN, (0, 0, 230, 50), border_radius=25)
        btn1_t = render_thai_text("🎮 เล่นคนเดียว", font_size=20, color=(15, 23, 42))
        btn1_surf.blit(btn1_t, btn1_t.get_rect(center=(115, 25)))
        screen.blit(btn1_surf, (c1_rect.centerx - 115, c1_y + 225))
        
        # 2. Team Battle Mode Card
        c2_x = c1_x + card_w + gap
        c2_y = 245
        c2_rect = pygame.Rect(c2_x, c2_y, card_w, card_h)
        c2_hover = c2_rect.collidepoint(mouse_pos)
        
        c2_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        c2_bg = (55, 45, 20, 245) if c2_hover else (20, 30, 48, 235)
        c2_border = ACCENT_AMBER if c2_hover else CARD_BORDER
        pygame.draw.rect(c2_surf, c2_bg, (0, 0, card_w, card_h), border_radius=20)
        pygame.draw.rect(c2_surf, c2_border, (0, 0, card_w, card_h), width=3 if c2_hover else 2, border_radius=20)
        screen.blit(c2_surf, (c2_x, c2_y))
        
        badge2 = render_thai_text("🏆 Team Battle", font_size=28, color=ACCENT_AMBER)
        screen.blit(badge2, badge2.get_rect(center=(c2_rect.centerx, c2_y + 55)))
        
        desc2_1 = render_thai_text("โหมดประลองความจำแบบทีม", font_size=18, color=TEXT_WHITE)
        desc2_2 = render_thai_text("สะสมแต้ม ชิงโพเดียม TOP 3", font_size=16, color=(148, 163, 184))
        screen.blit(desc2_1, desc2_1.get_rect(center=(c2_rect.centerx, c2_y + 120)))
        screen.blit(desc2_2, desc2_2.get_rect(center=(c2_rect.centerx, c2_y + 155)))
        
        btn2_surf = pygame.Surface((230, 50), pygame.SRCALPHA)
        pygame.draw.rect(btn2_surf, ACCENT_AMBER, (0, 0, 230, 50), border_radius=25)
        btn2_t = render_thai_text("⚔️ แข่งเป็นทีม", font_size=20, color=(15, 23, 42))
        btn2_surf.blit(btn2_t, btn2_t.get_rect(center=(115, 25)))
        screen.blit(btn2_surf, (c2_rect.centerx - 115, c2_y + 225))

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
        overlay.fill((15, 23, 42, 240))
        screen.blit(overlay, (0, 0))
        
        title_surf = render_thai_text("⚙️ ตั้งค่าการแข่งขันแบบทีม (Tournament Setup)", font_size=36, color=ACCENT_AMBER)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        
        mouse_pos = pygame.mouse.get_pos()
        clicked = getattr(self, "mouse_clicked", False)
        
        # 1. Number of Teams Selector (2 to 8 Teams)
        lbl1 = render_thai_text("1. จำนวนทีม (2 - 8 ทีม):", font_size=22, color=TEXT_WHITE)
        screen.blit(lbl1, (WIDTH // 2 - 380, 115))
        
        # Left Arrow (Decrease)
        btn_team_dec = pygame.Rect(WIDTH // 2 - 40, 108, 48, 44)
        dec_hover = btn_team_dec.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (30, 41, 59) if not dec_hover else (51, 65, 85), btn_team_dec, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, btn_team_dec, width=1, border_radius=10)
        arr_l = render_thai_text("◀", font_size=20, color=ACCENT_CYAN if self.num_teams > 2 else (100, 116, 139))
        screen.blit(arr_l, arr_l.get_rect(center=btn_team_dec.center))
        
        # Team Count Display Box
        val_team_rect = pygame.Rect(WIDTH // 2 + 18, 108, 120, 44)
        pygame.draw.rect(screen, (20, 30, 48), val_team_rect, border_radius=10)
        pygame.draw.rect(screen, ACCENT_CYAN, val_team_rect, width=2, border_radius=10)
        v_team = render_thai_text(f"{self.num_teams} ทีม", font_size=22, color=ACCENT_CYAN)
        screen.blit(v_team, v_team.get_rect(center=val_team_rect.center))
        
        # Right Arrow (Increase)
        btn_team_inc = pygame.Rect(WIDTH // 2 + 148, 108, 48, 44)
        inc_hover = btn_team_inc.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (30, 41, 59) if not inc_hover else (51, 65, 85), btn_team_inc, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, btn_team_inc, width=1, border_radius=10)
        arr_r = render_thai_text("▶", font_size=20, color=ACCENT_CYAN if self.num_teams < 8 else (100, 116, 139))
        screen.blit(arr_r, arr_r.get_rect(center=btn_team_inc.center))
        
        # Handle Team count clicks
        if clicked:
            if dec_hover and self.num_teams > 2:
                self.num_teams -= 1
            elif inc_hover and self.num_teams < 8:
                self.num_teams += 1
                
        # Display 8-Team Badges (in 2 rows of 4)
        for t in range(self.num_teams):
            p = TEAM_PALETTES[t]
            row = t // 4
            col = t % 4
            cards_in_this_row = min(4, self.num_teams - row * 4) if row > 0 else min(4, self.num_teams)
            row_start_x = (WIDTH - (cards_in_this_row * 140 + (cards_in_this_row - 1) * 16)) // 2
            t_x = row_start_x + col * (140 + 16)
            t_y = 168 + row * 52
            
            t_rect = pygame.Rect(t_x, t_y, 140, 44)
            pygame.draw.rect(screen, (20, 30, 48), t_rect, border_radius=12)
            pygame.draw.rect(screen, p["color"], t_rect, width=2, border_radius=12)
            p_surf = render_thai_text(f"{p['emoji']} {p['name']}", font_size=17, color=p["color"])
            screen.blit(p_surf, p_surf.get_rect(center=t_rect.center))
            
        # 2. Words per Team Selector (1 to 12 Words)
        max_words = len(ITEMS_POOL) # 12
        w_y = 290
        lbl2 = render_thai_text(f"2. จำนวนคำต่อทีม (1 - {max_words} คำ):", font_size=22, color=TEXT_WHITE)
        screen.blit(lbl2, (WIDTH // 2 - 380, w_y + 7))
        
        # Left Arrow (Decrease)
        btn_word_dec = pygame.Rect(WIDTH // 2 - 40, w_y, 48, 44)
        w_dec_hover = btn_word_dec.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (30, 41, 59) if not w_dec_hover else (51, 65, 85), btn_word_dec, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, btn_word_dec, width=1, border_radius=10)
        w_arr_l = render_thai_text("◀", font_size=20, color=ACCENT_AMBER if self.words_per_team > 1 else (100, 116, 139))
        screen.blit(w_arr_l, w_arr_l.get_rect(center=btn_word_dec.center))
        
        # Word Count Display Box
        val_word_rect = pygame.Rect(WIDTH // 2 + 18, w_y, 120, 44)
        pygame.draw.rect(screen, (20, 30, 48), val_word_rect, border_radius=10)
        pygame.draw.rect(screen, ACCENT_AMBER, val_word_rect, width=2, border_radius=10)
        v_word = render_thai_text(f"{self.words_per_team} คำ", font_size=22, color=ACCENT_AMBER)
        screen.blit(v_word, v_word.get_rect(center=val_word_rect.center))
        
        # Right Arrow (Increase)
        btn_word_inc = pygame.Rect(WIDTH // 2 + 148, w_y, 48, 44)
        w_inc_hover = btn_word_inc.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (30, 41, 59) if not w_inc_hover else (51, 65, 85), btn_word_inc, border_radius=10)
        pygame.draw.rect(screen, CARD_BORDER, btn_word_inc, width=1, border_radius=10)
        w_arr_r = render_thai_text("▶", font_size=20, color=ACCENT_AMBER if self.words_per_team < max_words else (100, 116, 139))
        screen.blit(w_arr_r, w_arr_r.get_rect(center=btn_word_inc.center))
        
        if clicked:
            if w_dec_hover and self.words_per_team > 1:
                self.words_per_team -= 1
            elif w_inc_hover and self.words_per_team < max_words:
                self.words_per_team += 1
                
        # Subtitle instructions / Keyboard Shortcuts Guide
        tip_surf = render_thai_text("💡 ใช้เมาส์คลิก หรือกดปุ่มลูกศร ◀ / ▶ (ปรับทีม) และ ▲ / ▼ (ปรับจำนวนคำ) บนคีย์บอร์ดได้", font_size=15, color=(148, 163, 184))
        screen.blit(tip_surf, tip_surf.get_rect(center=(WIDTH // 2, 380)))
        
        # Start Button
        start_btn = pygame.Rect(WIDTH // 2 - 150, 430, 300, 60)
        st_hover = start_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, ACCENT_EMERALD if st_hover else (5, 150, 105), start_btn, border_radius=30)
        st_surf = render_thai_text("🚀 เริ่มการแข่งขัน", font_size=26, color=TEXT_WHITE)
        screen.blit(st_surf, st_surf.get_rect(center=start_btn.center))
        
        # Back Button
        back_btn = pygame.Rect(WIDTH // 2 - 90, 520, 180, 42)
        bk_hover = back_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (30, 41, 59) if not bk_hover else (51, 65, 85), back_btn, border_radius=21)
        pygame.draw.rect(screen, CARD_BORDER, back_btn, width=1, border_radius=21)
        bk_surf = render_thai_text("🔙 กลับหน้าหลัก", font_size=18, color=TEXT_WHITE)
        screen.blit(bk_surf, bk_surf.get_rect(center=back_btn.center))
        
        if clicked:
            if st_hover:
                self.start_team_tournament()
            elif bk_hover:
                self.state = "LANDING_MENU"

    def draw_team_ready(self):
        team = self.team_scores[self.current_team_idx]
        
        tag_surf = pygame.Surface((WIDTH, 85), pygame.SRCALPHA)
        tag_surf.fill((20, 30, 48, 240))
        pygame.draw.line(tag_surf, team["color"], (0, 83), (WIDTH, 83), 3)
        screen.blit(tag_surf, (0, 0))
        
        t_text = render_thai_text(f"🏁 ถึงตา {team['emoji']} {team['name']} แล้ว!", font_size=30, color=team["color"])
        screen.blit(t_text, t_text.get_rect(center=(WIDTH // 2, 42)))
        
        center_card = pygame.Rect(WIDTH // 2 - 270, HEIGHT // 2 - 160, 540, 340)
        card_surf = pygame.Surface((540, 340), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 240), (0, 0, 540, 340), border_radius=24)
        pygame.draw.rect(card_surf, team["color"], (0, 0, 540, 340), width=3, border_radius=24)
        screen.blit(card_surf, center_card.topleft)
        
        ok_img = get_image("gesture_ok.png", target_size=(130, 130))
        screen.blit(ok_img, ok_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
        
        r_text1 = render_thai_text("ยกมือทำท่า OK 👌 เพื่อเริ่มเล่น!", font_size=24, color=ACCENT_AMBER)
        r_text2 = render_thai_text(f"รอบนี้ต้องค้นหาคำศัพท์ {self.words_per_team} คำ", font_size=18, color=TEXT_WHITE)
        screen.blit(r_text1, r_text1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))
        screen.blit(r_text2, r_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))
        
        bar_w = 400
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = HEIGHT // 2 + 115
        pygame.draw.rect(screen, (30, 41, 59), (bar_x, bar_y, bar_w, 16), border_radius=8)
        if self.team_ready_charge > 0:
            fill_w = int(bar_w * self.team_ready_charge)
            pygame.draw.rect(screen, ACCENT_EMERALD, (bar_x, bar_y, fill_w, 16), border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, fill_w, 16), width=1, border_radius=8)

    def draw_podium_dashboard(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 240))
        screen.blit(overlay, (0, 0))
        
        title_surf = render_thai_text("🏆 สรุปผลการแข่งขัน (Tournament Champions)", font_size=38, color=ACCENT_AMBER)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 65)))
        
        ranked_teams = sorted(self.team_scores, key=lambda t: (-t["score"], t["time_spent"]))
        
        podium_cx = WIDTH // 2
        podium_base_y = 380
        
        slots = [
            {"rank": 2, "idx": 1, "x": podium_cx - 190, "h": 130, "col": (148, 163, 184), "cup": "🥈"},
            {"rank": 1, "idx": 0, "x": podium_cx, "h": 180, "col": (245, 158, 11), "cup": "🥇"},
            {"rank": 3, "idx": 2, "x": podium_cx + 190, "h": 90, "col": (180, 83, 9), "cup": "🥉"}
        ]
        
        for slot in slots:
            if slot["idx"] < len(ranked_teams):
                team = ranked_teams[slot["idx"]]
                sx = slot["x"]
                pw = 150
                ph = slot["h"]
                py = podium_base_y - ph
                
                pygame.draw.rect(screen, slot["col"], (sx - pw // 2, py, pw, ph), border_radius=14)
                pygame.draw.rect(screen, (255, 255, 255), (sx - pw // 2, py, pw, ph), width=2, border_radius=14)
                
                r_surf = render_thai_text(f"#{slot['rank']}", font_size=32, color=(15, 23, 42))
                screen.blit(r_surf, r_surf.get_rect(center=(sx, py + 40)))
                
                cup_surf = render_thai_text(slot["cup"], font_size=34)
                screen.blit(cup_surf, cup_surf.get_rect(center=(sx, py - 60)))
                
                tname_surf = render_thai_text(f"{team['emoji']} {team['name']}", font_size=18, color=team["color"])
                screen.blit(tname_surf, tname_surf.get_rect(center=(sx, py - 30)))
                
                score_surf = render_thai_text(f"{team['score']} pts", font_size=18, color=TEXT_WHITE)
                screen.blit(score_surf, score_surf.get_rect(center=(sx, py - 10)))
                
        table_y = 425
        header_surf = pygame.Surface((700, 34), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (30, 41, 59, 230), (0, 0, 700, 34), border_radius=8)
        screen.blit(header_surf, (WIDTH // 2 - 350, table_y))
        
        th1 = render_thai_text("อันดับ", font_size=16, color=ACCENT_CYAN)
        th2 = render_thai_text("ทีม", font_size=16, color=ACCENT_CYAN)
        th3 = render_thai_text("คะแนนสะสม", font_size=16, color=ACCENT_CYAN)
        th4 = render_thai_text("เวลาที่ใช้", font_size=16, color=ACCENT_CYAN)
        screen.blit(th1, (WIDTH // 2 - 320, table_y + 4))
        screen.blit(th2, (WIDTH // 2 - 190, table_y + 4))
        screen.blit(th3, (WIDTH // 2 + 40, table_y + 4))
        screen.blit(th4, (WIDTH // 2 + 210, table_y + 4))
        
        for i, team in enumerate(ranked_teams):
            row_y = table_y + 38 + i * 34
            row_surf = pygame.Surface((700, 30), pygame.SRCALPHA)
            bg = (245, 158, 11, 35) if i == 0 else (20, 30, 48, 200)
            pygame.draw.rect(row_surf, bg, (0, 0, 700, 30), border_radius=6)
            screen.blit(row_surf, (WIDTH // 2 - 350, row_y))
            
            r_label = f"#{i+1}" if i >= 3 else ["🥇 1st", "🥈 2nd", "🥉 3rd"][i]
            td1 = render_thai_text(r_label, font_size=16, color=TEXT_WHITE)
            td2 = render_thai_text(f"{team['emoji']} {team['name']}", font_size=16, color=team["color"])
            td3 = render_thai_text(f"{team['score']} คะแนน", font_size=16, color=ACCENT_AMBER)
            td4 = render_thai_text(f"{team['time_spent']:.1f} วินาที", font_size=16, color=(148, 163, 184))
            
            screen.blit(td1, (WIDTH // 2 - 320, row_y + 2))
            screen.blit(td2, (WIDTH // 2 - 190, row_y + 2))
            screen.blit(td3, (WIDTH // 2 + 40, row_y + 2))
            screen.blit(td4, (WIDTH // 2 + 210, row_y + 2))
            
        mouse_pos = pygame.mouse.get_pos()
        clicked = pygame.mouse.get_pressed()[0]
        
        btn_replay = pygame.Rect(WIDTH // 2 - 200, HEIGHT - 70, 185, 48)
        btn_menu = pygame.Rect(WIDTH // 2 + 15, HEIGHT - 70, 185, 48)
        
        rep_hover = btn_replay.collidepoint(mouse_pos)
        men_hover = btn_menu.collidepoint(mouse_pos)
        
        pygame.draw.rect(screen, ACCENT_AMBER if rep_hover else (217, 119, 6), btn_replay, border_radius=24)
        t_rep = render_thai_text("🔄 แข่งอีกครั้ง", font_size=18, color=(15, 23, 42))
        screen.blit(t_rep, t_rep.get_rect(center=btn_replay.center))
        
        pygame.draw.rect(screen, (30, 41, 59) if not men_hover else (51, 65, 85), btn_menu, border_radius=24)
        pygame.draw.rect(screen, CARD_BORDER, btn_menu, width=1, border_radius=24)
        t_men = render_thai_text("🏠 กลับหน้าหลัก", font_size=18, color=TEXT_WHITE)
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
            return
            
        if self.state == "TEAM_SETUP":
            self.draw_team_setup()
            return
            
        if self.state == "TEAM_READY":
            self.draw_team_ready()
            self.draw_cursor_and_skeleton()
            return
            
        if self.state == "PODIUM_DASHBOARD":
            self.draw_podium_dashboard()
            return

        # In-Game Clean HUD Header
        hud_h = 74
        header_surf = pygame.Surface((WIDTH, hud_h), pygame.SRCALPHA)
        header_surf.fill((15, 23, 42, 235))
        pygame.draw.line(header_surf, CARD_BORDER, (0, hud_h - 1), (WIDTH, hud_h - 1), 2)
        screen.blit(header_surf, (0, 0))
        
        menu_btn = pygame.Rect(18, 14, 100, 46)
        m_hover = menu_btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (30, 41, 59) if not m_hover else (51, 65, 85), menu_btn, border_radius=16)
        pygame.draw.rect(screen, CARD_BORDER, menu_btn, width=1, border_radius=16)
        m_text = render_thai_text("🏠 เมนู", font_size=18, color=TEXT_WHITE)
        screen.blit(m_text, m_text.get_rect(center=menu_btn.center))
        if pygame.mouse.get_pressed()[0] and m_hover:
            self.state = "LANDING_MENU"
            return
        
        if self.mode == "FREEDOM":
            m_badge = render_thai_text("🌟 Freedom Mode", font_size=20, color=ACCENT_CYAN)
            screen.blit(m_badge, (135, 24))
            
            score_text = render_thai_text(f"⭐ คะแนน: {self.freedom_score}", font_size=24, color=ACCENT_AMBER)
            screen.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
        else:
            team = self.team_scores[self.current_team_idx]
            m_badge = render_thai_text(f"{team['emoji']} {team['name']} • คำที่ {team['words_done'] + 1}/{self.words_per_team}", font_size=22, color=team["color"])
            screen.blit(m_badge, (135, 24))
            
            score_text = render_thai_text(f"⭐ แต้มทีม: {team['score']}", font_size=24, color=ACCENT_AMBER)
            screen.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
            
        chances_surf = render_thai_text(f"❤️ x {self.chances_left}", font_size=22, color=ACCENT_ROSE)
        screen.blit(chances_surf, chances_surf.get_rect(center=(WIDTH // 2, 37)))

        if self.state == "ROULETTE":
            self.wheel.draw(screen)
            r_tip = render_thai_text("กำลังสุ่มท่าทางที่ต้องใช้...", font_size=32, color=ACCENT_AMBER)
            screen.blit(r_tip, r_tip.get_rect(center=(WIDTH // 2, HEIGHT - 55)))
            
        elif self.state == "ANNOUNCE":
            self.wheel.draw(screen)
            banner = pygame.Surface((740, 110), pygame.SRCALPHA)
            pygame.draw.rect(banner, (15, 23, 42, 245), (0, 0, 740, 110), border_radius=24)
            pygame.draw.rect(banner, self.selected_gesture["color"], (0, 0, 740, 110), width=4, border_radius=24)
            screen.blit(banner, (WIDTH // 2 - 370, HEIGHT - 135))
            
            t1 = render_thai_text(f"ท่าที่ต้องใช้: {self.selected_gesture['emoji']} {self.selected_gesture['name']}", font_size=28, color=self.selected_gesture["color"])
            t2 = render_thai_text(self.selected_gesture["desc"], font_size=20, color=TEXT_WHITE)
            screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT - 100)))
            screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
            
        elif self.state == "TARGET_FOCUS_READ":
            self.draw_target_focus_read()
            
        elif self.state == "MEMORIZE":
            t_banner = pygame.Surface((640, 80), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 640, 80), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_AMBER, (0, 0, 640, 80), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 320, 100))
            
            w_text = render_thai_text(f"👀 จำตำแหน่งการ์ด! หาคำว่า: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_AMBER)
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
            cd_surf = render_thai_text(str(self.countdown_num), font_size=cd_size, color=ACCENT_AMBER)
            screen.blit(cd_surf, cd_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            
            sub_cd = render_thai_text("เตรียมพร้อม...", font_size=36, color=TEXT_WHITE)
            screen.blit(sub_cd, sub_cd.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))
            
        elif self.state == "PLAY":
            t_banner = pygame.Surface((680, 85), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 680, 85), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_CYAN, (0, 0, 680, 85), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 340, 100))
            
            target_surf = render_thai_text(f"🎯 จงหา: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_AMBER)
            screen.blit(target_surf, target_surf.get_rect(center=(WIDTH // 2, 126)))
            
            inst_surf = render_thai_text(f"ใช้ท่า: {self.selected_gesture['emoji']} {self.selected_gesture['name']} ค้างบนการ์ดเพื่อเปิด", font_size=18, color=self.selected_gesture["color"])
            screen.blit(inst_surf, inst_surf.get_rect(center=(WIDTH // 2, 158)))
            
            for card in self.cards:
                card.draw(screen, show_face=False)
                
            if self.feedback_msg:
                fb_surf = render_thai_text(self.feedback_msg, font_size=24, color=self.feedback_color)
                screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, HEIGHT - 35)))
                
        elif self.state == "VOICE_VERIFY":
            self.draw_voice_verify()
            
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

    def draw_target_focus_read(self):
        elapsed = time.time() - self.state_timer
        
        # 1. Animation Timing:
        # 0.0s - 1.0s: Zoom In (t: 0.0 -> 1.0)
        # 1.0s - 3.8s: Full Focus & Slow Audio Playback (t: 1.0)
        # 3.8s - 4.6s: Zoom Out back to grid (t: 1.0 -> 0.0)
        if elapsed < 1.0:
            p = elapsed / 1.0
            t = math.sin(p * math.pi / 2)
        elif elapsed < 3.8:
            t = 1.0
        else:
            p = min(1.0, (elapsed - 3.8) / 0.8)
            t = 1.0 - math.sin(p * math.pi / 2)
            
        target_card = next((c for c in self.cards if c.item["id"] == self.target_item["id"]), self.cards[0])
        
        # 2. Draw other 5 cards in their grid slots
        for card in self.cards:
            if card.item["id"] != self.target_item["id"]:
                card.draw(screen, show_face=True)
                
        # 3. Cinematic Dim Vignette Layer
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, int(t * 225)))
        screen.blit(dim, (0, 0))
        
        # 4. Interpolate Target Card Rect (from grid slot to large center stage)
        orig_r = target_card.rect
        dest_w, dest_h = 420, 440
        dest_x = (WIDTH - dest_w) // 2
        dest_y = (HEIGHT - dest_h) // 2 - 15
        
        cur_x = int(orig_r.x + (dest_x - orig_r.x) * t)
        cur_y = int(orig_r.y + (dest_y - orig_r.y) * t)
        cur_w = int(orig_r.width + (dest_w - orig_r.width) * t)
        cur_h = int(orig_r.height + (dest_h - orig_r.height) * t)
        
        # Draw expanding focus card
        card_surf = pygame.Surface((cur_w, cur_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 252), (0, 0, cur_w, cur_h), border_radius=int(18 + t * 10))
        border_col = ACCENT_AMBER
        border_w = int(3 + t * 3)
        pygame.draw.rect(card_surf, border_col, (0, 0, cur_w, cur_h), width=border_w, border_radius=int(18 + t * 10))
        screen.blit(card_surf, (cur_x, cur_y))
        
        # Card inner art & labels
        draw_rect = pygame.Rect(cur_x, cur_y, cur_w, cur_h)
        art_size = int(105 + t * 75)
        img_surf = get_image(self.target_item["filename"], target_size=(art_size, art_size))
        img_rect = img_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery - int(26 + t * 45)))
        screen.blit(img_surf, img_rect)
        
        # English Word (Large, slow, clear)
        font_en_size = int(18 + t * 24)
        en_text = f"🗣️ \"{self.target_item['en'].upper()}\"" if t > 0.3 else self.target_item["en"]
        en_surf = render_thai_text(en_text, font_size=font_en_size, color=ACCENT_AMBER)
        screen.blit(en_surf, en_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + int(45 + t * 50))))
        
        # Thai Translation
        font_th_size = int(22 + t * 6)
        th_surf = render_thai_text(self.target_item["word"], font_size=font_th_size, color=self.target_item["color"])
        screen.blit(th_surf, th_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + int(70 + t * 60))))
        
        # Top Header & Bottom Subtitle
        if t > 0.5:
            header_surf = render_thai_text("🎯 คำศัพท์ประจำรอบที่ต้องค้นหา (Target Word)", font_size=28, color=ACCENT_AMBER)
            screen.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, 70)))
            
            sub_surf = render_thai_text("🔊 ฟังเสียงอ่านภาษาอังกฤษให้ชัดเจน และจำภาพนี้ไว้ให้ดี!", font_size=22, color=TEXT_WHITE)
            screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT - 65)))

    def draw_voice_verify(self):
        # 1. Background Cards
        for card in self.cards:
            card.draw(screen, show_face=card.is_matched)
            
        # 2. Focus Dim Overlay
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 195))
        screen.blit(dim, (0, 0))
        
        # 3. Voice Verification Modal
        box_w, box_h = 740, 370
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2 - 10
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (20, 30, 48, 252), (0, 0, box_w, box_h), border_radius=26)
        border_col = ACCENT_EMERALD if self.voice_success else ACCENT_AMBER
        pygame.draw.rect(box_surf, border_col, (0, 0, box_w, box_h), width=3, border_radius=26)
        screen.blit(box_surf, (box_x, box_y))
        
        # Modal Header Badge
        header_surf = render_thai_text("🎙️ ตรวจสอบการออกเสียงคำศัพท์ (Voice Verification)", font_size=25, color=ACCENT_AMBER)
        screen.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, box_y + 42)))
        
        # Target English Word
        target_word_str = f"🗣️ \"{self.target_item['en'].upper()}\""
        word_surf = render_thai_text(target_word_str, font_size=42, color=TEXT_WHITE)
        screen.blit(word_surf, word_surf.get_rect(center=(WIDTH // 2, box_y + 110)))
        
        sub_thai = render_thai_text(f"(ความหมาย: {self.target_item['word']})", font_size=20, color=ACCENT_CYAN)
        screen.blit(sub_thai, sub_thai.get_rect(center=(WIDTH // 2, box_y + 155)))
        
        # Pulsing Audio Waveform Animation
        now = time.time()
        wave_cx = WIDTH // 2
        wave_cy = box_y + 215
        num_bars = 13
        for i in range(num_bars):
            offset = (i - num_bars // 2) * 16
            if self.is_listening:
                h = int(12 + math.sin(now * 9 + i * 0.6) * 18 + math.cos(now * 14 + i * 1.1) * 10)
                h = max(8, min(48, h))
            else:
                h = 10
            bar_rect = pygame.Rect(wave_cx + offset - 4, wave_cy - h // 2, 8, h)
            bar_col = ACCENT_EMERALD if self.voice_success else ACCENT_CYAN
            pygame.draw.rect(screen, bar_col, bar_rect, border_radius=4)
            
        # Status / Feedback
        if self.voice_success:
            st_surf = render_thai_text("🎉 ออกเสียงถูกต้อง! ได้รับ +100 คะแนน", font_size=24, color=ACCENT_EMERALD)
        elif self.voice_recognized_text:
            st_surf = render_thai_text(f"ได้ยิน: \"{self.voice_recognized_text}\"...", font_size=22, color=self.feedback_color)
        elif self.is_listening:
            st_surf = render_thai_text("🟢 กำลังรอฟังเสียง... พูดคำศัพท์ภาษาอังกฤษใส่ไมโครโฟนได้เลย", font_size=19, color=TEXT_WHITE)
        else:
            st_surf = render_thai_text("เตรียมพร้อมฟังเสียง...", font_size=19, color=(148, 163, 184))
            
        screen.blit(st_surf, st_surf.get_rect(center=(WIDTH // 2, box_y + 280)))
        
        # Hint Subtitle
        hint_surf = render_thai_text("💡 ออกเสียงภาษาอังกฤษให้ถูกต้องเพื่อปลดล็อกคะแนนประจำรอบ", font_size=16, color=(148, 163, 184))
        screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, box_y + 332)))

    def draw_cursor_and_skeleton(self):
        self.draw_hand_skeleton()
        
        cx, cy = int(self.cursor_pos[0]), int(self.cursor_pos[1])
        if cx < 0 or cy < 0 or cx > WIDTH or cy > HEIGHT:
            return
            
        cursor_col = ACCENT_AMBER if self.is_pinched else (ACCENT_EMERALD if self.current_detected_gesture == "OK" else ACCENT_CYAN)
        
        pygame.draw.circle(screen, cursor_col, (cx, cy), 18, width=3)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 5)
        
        if self.current_detected_gesture != "NONE":
            g_tag = render_thai_text(f"🖐️ {self.current_detected_gesture}", font_size=15, color=cursor_col)
            screen.blit(g_tag, (cx + 20, cy - 12))

    def run(self):
        running = True
        while running:
            self.mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mouse_clicked = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in ["LANDING_MENU", "PODIUM_DASHBOARD"]:
                            running = False
                        else:
                            self.state = "LANDING_MENU"
                    elif self.state == "TEAM_SETUP":
                        if event.key == pygame.K_LEFT and self.num_teams > 2:
                            self.num_teams -= 1
                        elif event.key == pygame.K_RIGHT and self.num_teams < 8:
                            self.num_teams += 1
                        elif event.key == pygame.K_DOWN and self.words_per_team > 1:
                            self.words_per_team -= 1
                        elif event.key == pygame.K_UP and self.words_per_team < len(ITEMS_POOL):
                            self.words_per_team += 1
                        elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                            self.start_team_tournament()

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
