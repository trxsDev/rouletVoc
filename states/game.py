import time
import math
import random
import pygame
import numpy as np

from config.constants import (
    WIDTH, HEIGHT, BG_COLOR, ACCENT_AMBER, ACCENT_EMERALD, 
    ACCENT_ROSE, ACCENT_CYAN, TEXT_WHITE, TEAM_PALETTES
)
from config.items import GESTURE_MODES, ITEMS_POOL
from core.audio_engine import sound_engine
from core.tracking_engine import HandTrackingEngine
from core.speech_verifier import SpeechVerifier
from components.card import Card
from components.roulette import RouletteWheel
from core.system_diagnostics import SystemDiagnostics
from ui.renderer import render_thai_text
from ui.hud import HUD
from ui.screens import Screens
from ui.target_focus import TargetFocusScreen
from ui.voice_modal import VoiceModal

class GestureMemoryGame:
    def __init__(self):
        # Game Mode & State (2-Step Setup Wizard: Camera -> WiFi -> Mode Selection)
        self.mode = "FREEDOM"  # "FREEDOM" or "TOURNAMENT"
        self.state = "SETUP_CAMERA"
        self.wifi_info = {
            "online": True,
            "detail": "เชื่อมต่ออินเทอร์เน็ตสำเร็จ (Online)",
            "ping": 15
        }
        
        # Freedom & Tournament Scores
        self.freedom_score = 0
        self.num_teams = 2
        self.words_per_team = 4
        self.current_team_idx = 0
        self.team_scores = []
        self.team_ready_charge = 0.0
        self.team_start_time = 0.0
        
        # Round Data
        self.score = 0
        self.chances_left = 3
        self.target_item = None
        self.cards = []
        self.state_timer = time.time()
        self.play_grace_until = 0.0
        self.countdown_num = 3
        self.feedback_msg = ""
        self.feedback_color = TEXT_WHITE
        
        # Target Focus 2-Time Voice Audio State
        self.voice_read_count = [0]
        
        # Roulette Wheel Component
        self.wheel = RouletteWheel(WIDTH // 2, HEIGHT // 2 + 10, radius=185)
        self.selected_gesture = GESTURE_MODES[0]
        
        # Core Engines
        self.tracking_engine = HandTrackingEngine()
        self.speech_verifier = SpeechVerifier()
        
        # Exhaustive Decks
        self.unplayed_vocab_deck = []
        self.unplayed_gesture_deck = []

    def check_wifi_connection(self):
        import socket
        t0 = time.time()
        try:
            socket.setdefaulttimeout(1.5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            ping_ms = int((time.time() - t0) * 1000)
            self.wifi_info = {
                "online": True,
                "detail": "เชื่อมต่ออินเทอร์เน็ตสำเร็จ (Online)",
                "ping": max(5, ping_ms)
            }
        except Exception:
            self.wifi_info = {
                "online": False,
                "detail": "ออฟไลน์ (Speech Recognition ในเครื่อง)",
                "ping": 999
            }

    def get_next_target_item(self):
        if not self.unplayed_vocab_deck:
            self.unplayed_vocab_deck = random.sample(ITEMS_POOL, len(ITEMS_POOL))
        return self.unplayed_vocab_deck.pop(0)

    def get_next_gesture_target(self):
        if not self.unplayed_gesture_deck:
            self.unplayed_gesture_deck = random.sample(list(range(len(GESTURE_MODES))), len(GESTURE_MODES))
        return self.unplayed_gesture_deck.pop(0)

    def start_freedom_mode(self):
        self.mode = "FREEDOM"
        self.freedom_score = 0
        self.unplayed_vocab_deck = []
        self.unplayed_gesture_deck = []
        self.tracking_engine.reset_player_lock()
        self.start_new_round()

    def start_team_tournament(self):
        self.mode = "TOURNAMENT"
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
                "score": 0,
                "words_done": 0,
                "time_spent": 0.0
            })
        self.current_team_idx = 0
        self.team_ready_charge = 0.0
        self.tracking_engine.reset_player_lock()
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
        self.voice_read_count = [0]
        
        # 1. Target Gesture
        target_gesture_idx = self.get_next_gesture_target()
        self.wheel.spin_to_target(target_gesture_idx)
        
        # 2. Target Vocabulary
        self.target_item = self.get_next_target_item()
        
        # 3. 5 Distractors
        distractors = [item for item in ITEMS_POOL if item["id"] != self.target_item["id"]]
        chosen_distractors = random.sample(distractors, 5)
        
        # 4. 6 Cards Grid
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

    def update(self):
        now = time.time()
        elapsed = now - self.state_timer
        
        if self.state in ["SETUP_CAMERA", "SETUP_WIFI", "LANDING_MENU", "TEAM_SETUP", "PODIUM_DASHBOARD"]:
            pass
            
        elif self.state == "TEAM_READY":
            if (self.tracking_engine.current_detected_gesture in ["OK", "PINCH"]) or self.tracking_engine.is_pinched:
                self.team_ready_charge = min(1.0, self.team_ready_charge + 0.07)
                sound_engine.play("ready_ping")
                if self.team_ready_charge >= 1.0:
                    sound_engine.play("ok_ready")
                    self.start_team_turn()
            else:
                self.team_ready_charge = max(0.0, self.team_ready_charge - 0.03)
                
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
                self.voice_read_count = [0]
                
        elif self.state == "TARGET_FOCUS_READ":
            TargetFocusScreen.update_audio(elapsed, self.target_item, self.voice_read_count)
            if elapsed > 5.5:
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
            cursor_rect = pygame.Rect(self.tracking_engine.cursor_pos[0] - 14, self.tracking_engine.cursor_pos[1] - 14, 28, 28)
            req_gesture = self.selected_gesture["id"]
            is_armed = (now >= self.play_grace_until)
            
            for card in self.cards:
                if card.rect.colliderect(cursor_rect) and not card.is_matched and not card.is_flipped:
                    card.hover_progress = min(1.0, card.hover_progress + 0.08)
                    
                    gesture_matches = (
                        (self.tracking_engine.current_detected_gesture == req_gesture) or 
                        (req_gesture == "PINCH" and (self.tracking_engine.is_pinched or self.tracking_engine.current_detected_gesture in ["PINCH", "OK"]))
                    )
                    if is_armed and gesture_matches:
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
            # Handled asynchronously by SpeechVerifier worker
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
                            self.tracking_engine.reset_player_lock()
                            self.state = "TEAM_READY"
                            self.state_timer = now
                        else:
                            sound_engine.play("podium_fanfare")
                            self.tracking_engine.reset_player_lock()
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
            self.speech_verifier.reset(self.target_item)
            
            def on_success(spoken_text):
                if self.mode == "FREEDOM":
                    self.freedom_score += 100
                    self.score = self.freedom_score
                else:
                    self.team_scores[self.current_team_idx]["score"] += 100
                    self.score = self.team_scores[self.current_team_idx]["score"]
                    
            def on_retry():
                self.state_timer = time.time()
                if self.state == "VOICE_VERIFY":
                    self.speech_verifier.start_listening(self.target_item, on_success, on_retry, on_finish)
                    
            def on_finish():
                self.state = "ROUND_END"
                self.state_timer = time.time()
                self.feedback_msg = self.speech_verifier.feedback_msg
                self.feedback_color = self.speech_verifier.feedback_color
                
            self.speech_verifier.start_listening(self.target_item, on_success, on_retry, on_finish)
        else:
            self.chances_left -= 1
            card.shake_offset = 14
            sound_engine.play("wrong")
            self.feedback_msg = f"ยังไม่ใช่ '{self.target_item['word']}' (เหลืออีก {self.chances_left} ครั้ง)"
            self.feedback_color = ACCENT_ROSE
            
            if self.chances_left <= 0:
                for c in self.cards:
                    if c.item["id"] == self.target_item["id"]:
                        c.is_flipped = True
                self.feedback_msg = f"หมดโอกาสแล้ว! คำตอบคือ '{self.target_item['word']}'"
                self.state = "ROUND_END"
                self.state_timer = time.time()

    def draw(self, screen, bg_cam=None):
        screen.fill(BG_COLOR)
        
        # During COUNTDOWN: Hide camera feed completely to prevent pre-position cheating!
        if bg_cam is not None and self.state != "COUNTDOWN":
            surf_cam = pygame.surfarray.make_surface(np.transpose(bg_cam, (1, 0, 2)))
            screen.blit(surf_cam, (0, 0))
            
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((15, 23, 42, 110))
            screen.blit(dim, (0, 0))
        elif self.state == "COUNTDOWN":
            # Solid dark background for countdown stage
            screen.fill((15, 23, 42))
        
        # 1. Step 1/2: Camera Selection & Preview Setup
        if self.state == "SETUP_CAMERA":
            Screens.draw_setup_camera(
                screen,
                self.tracking_engine,
                on_switch_cam_cb=self.tracking_engine.switch_camera,
                on_next_cb=lambda: (setattr(self, "state", "SETUP_WIFI"), self.check_wifi_connection())
            )
            return

        # 2. Step 2/2: WiFi & Network Diagnostics Setup
        if self.state == "SETUP_WIFI":
            Screens.draw_setup_wifi(
                screen,
                self.wifi_info,
                on_recheck_cb=self.check_wifi_connection,
                on_back_cb=lambda: setattr(self, "state", "SETUP_CAMERA"),
                on_next_cb=lambda: setattr(self, "state", "LANDING_MENU")
            )
            return

        # 3. Landing Menu
        if self.state == "LANDING_MENU":
            Screens.draw_landing_menu(
                screen,
                on_freedom_click=self.start_freedom_mode,
                on_tournament_click=lambda: setattr(self, "state", "TEAM_SETUP")
            )
            return

        # 2. Team Setup
        if self.state == "TEAM_SETUP":
            def change_teams(d):
                self.num_teams = max(2, min(8, self.num_teams + d))
            def change_words(d):
                self.words_per_team = max(1, min(len(ITEMS_POOL), self.words_per_team + d))
            Screens.draw_team_setup(
                screen,
                self.num_teams,
                self.words_per_team,
                on_teams_change=change_teams,
                on_words_change=change_words,
                on_start_click=self.start_team_tournament,
                on_back_click=lambda: setattr(self, "state", "LANDING_MENU")
            )
            return

        # 3. Team Ready
        if self.state == "TEAM_READY":
            team = self.team_scores[self.current_team_idx]
            Screens.draw_team_ready(screen, team, self.team_ready_charge)
            HUD.draw_skeleton_and_cursor(
                screen,
                self.tracking_engine.hand_landmarks_screen,
                self.tracking_engine.cursor_pos,
                self.tracking_engine.current_detected_gesture,
                self.tracking_engine.is_pinched
            )
            return

        # 4. Podium Dashboard
        if self.state == "PODIUM_DASHBOARD":
            Screens.draw_podium_dashboard(
                screen,
                self.team_scores,
                on_replay_click=lambda: setattr(self, "state", "TEAM_SETUP"),
                on_menu_click=lambda: setattr(self, "state", "LANDING_MENU")
            )
            return

        # 5. In-Game HUD Header
        menu_btn = HUD.draw_in_game_header(
            screen,
            self.mode,
            self.freedom_score,
            self.team_scores,
            self.current_team_idx,
            self.words_per_team,
            self.chances_left
        )
        if pygame.mouse.get_pressed()[0] and menu_btn.collidepoint(pygame.mouse.get_pos()):
            self.state = "LANDING_MENU"
            return

        # In-Game State Sub-Screens
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
            
            t1 = render_thai_text(f"ท่าที่ต้องใช้: {self.selected_gesture['name']}", font_size=28, color=self.selected_gesture["color"])
            t2 = render_thai_text(self.selected_gesture["desc"], font_size=20, color=TEXT_WHITE)
            screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT - 100)))
            screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
            
        elif self.state == "TARGET_FOCUS_READ":
            elapsed = time.time() - self.state_timer
            TargetFocusScreen.draw(screen, self.cards, self.target_item, elapsed, self.voice_read_count[0])
            
        elif self.state == "MEMORIZE":
            t_banner = pygame.Surface((640, 80), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 640, 80), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_AMBER, (0, 0, 640, 80), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 320, 100))
            
            w_text = render_thai_text(f"จำตำแหน่งการ์ด! หาคำว่า: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_AMBER)
            screen.blit(w_text, w_text.get_rect(center=(WIDTH // 2, 140)))
            
            for card in self.cards:
                card.draw(screen, show_face=True)
                
        elif self.state == "COUNTDOWN":
            # 1. Hide cards completely (Do not draw cards during countdown)
            cd_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            cd_overlay.fill((15, 23, 42, 225))
            screen.blit(cd_overlay, (0, 0))
            
            # 2. Glowing Circular Countdown Stage
            now = time.time()
            pulse = 1.0 + (math.sin(now * 14) * 0.12)
            cx, cy = WIDTH // 2, HEIGHT // 2 - 20
            
            # Outer expanding glow rings
            pygame.draw.circle(screen, (245, 158, 11, 40), (cx, cy), int(130 * pulse), width=4)
            pygame.draw.circle(screen, (245, 158, 11, 80), (cx, cy), int(105 * pulse), width=6)
            pygame.draw.circle(screen, (30, 41, 59), (cx, cy), 85)
            pygame.draw.circle(screen, ACCENT_AMBER, (cx, cy), 85, width=4)
            
            # Big Dynamic Number (3, 2, 1)
            cd_text = str(self.countdown_num) if self.countdown_num > 0 else "GO!"
            cd_size = int(88 * pulse) if self.countdown_num > 0 else int(72 * pulse)
            cd_color = ACCENT_AMBER if self.countdown_num > 0 else ACCENT_EMERALD
            cd_surf = render_thai_text(cd_text, font_size=cd_size, color=cd_color)
            screen.blit(cd_surf, cd_surf.get_rect(center=(cx, cy)))
            
            # Subtitle Message
            sub_cd = render_thai_text("เตรียมพร้อม... การ์ดกำลังจะสลับปิด!", font_size=28, color=TEXT_WHITE)
            screen.blit(sub_cd, sub_cd.get_rect(center=(cx, cy + 130)))
            
            # Gesture Ready Badge
            g_badge = render_thai_text(f"เตรียมทำท่า: {self.selected_gesture['name']}", font_size=22, color=self.selected_gesture["color"])
            screen.blit(g_badge, g_badge.get_rect(center=(cx, cy + 175)))
            
        elif self.state == "PLAY":
            t_banner = pygame.Surface((680, 85), pygame.SRCALPHA)
            pygame.draw.rect(t_banner, (15, 23, 42, 240), (0, 0, 680, 85), border_radius=20)
            pygame.draw.rect(t_banner, ACCENT_CYAN, (0, 0, 680, 85), width=3, border_radius=20)
            screen.blit(t_banner, (WIDTH // 2 - 340, 100))
            
            target_surf = render_thai_text(f"จงหา: '{self.target_item['word']}' ({self.target_item['en']})", font_size=26, color=ACCENT_AMBER)
            screen.blit(target_surf, target_surf.get_rect(center=(WIDTH // 2, 126)))
            
            inst_surf = render_thai_text(f"ใช้ท่า: {self.selected_gesture['name']} ค้างบนการ์ดเพื่อเปิด", font_size=18, color=self.selected_gesture["color"])
            screen.blit(inst_surf, inst_surf.get_rect(center=(WIDTH // 2, 158)))
            
            for card in self.cards:
                card.draw(screen, show_face=False)
                
            if self.feedback_msg:
                fb_surf = render_thai_text(self.feedback_msg, font_size=24, color=self.feedback_color)
                screen.blit(fb_surf, fb_surf.get_rect(center=(WIDTH // 2, HEIGHT - 35)))
                
        elif self.state == "VOICE_VERIFY":
            VoiceModal.draw(
                screen,
                self.cards,
                self.target_item,
                self.speech_verifier.is_listening,
                self.speech_verifier.is_success,
                self.speech_verifier.recognized_text,
                self.speech_verifier.feedback_msg,
                self.speech_verifier.feedback_color,
                audio_data=self.speech_verifier.get_live_audio_data()
            )
            
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

        # Draw hand skeleton and cursor during active gameplay states (Hidden during setup/menu/countdown)
        if self.state not in ["SETUP_CAMERA", "SETUP_WIFI", "LANDING_MENU", "TEAM_SETUP", "PODIUM_DASHBOARD", "COUNTDOWN"]:
            HUD.draw_skeleton_and_cursor(
                screen,
                self.tracking_engine.hand_landmarks_screen,
                self.tracking_engine.cursor_pos,
                self.tracking_engine.current_detected_gesture,
                self.tracking_engine.is_pinched
            )
