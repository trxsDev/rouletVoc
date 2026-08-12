import pygame
import math
import time
from config.constants import WIDTH, HEIGHT, ACCENT_AMBER, ACCENT_EMERALD, ACCENT_CYAN, TEXT_WHITE
from ui.renderer import render_thai_text

class VoiceModal:
    @staticmethod
    def draw(surface, cards, target_item, is_listening, is_success, recognized_text, feedback_msg, feedback_color, audio_data=None):
        # 1. Background Cards
        for card in cards:
            card.draw(surface, show_face=card.is_matched)

        # 2. Focus Dim Overlay
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 205))
        surface.blit(dim, (0, 0))

        # 3. Central Voice Verification Modal
        box_w, box_h = 780, 420
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2 - 15

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (18, 28, 48, 252), (0, 0, box_w, box_h), border_radius=28)
        border_col = ACCENT_EMERALD if is_success else ACCENT_AMBER
        pygame.draw.rect(box_surf, border_col, (0, 0, box_w, box_h), width=3, border_radius=28)
        surface.blit(box_surf, (box_x, box_y))

        # Modal Header
        header_surf = render_thai_text("ตรวจสอบการออกเสียงคำศัพท์ (Voice Verification)", font_size=24, color=ACCENT_AMBER)
        surface.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, box_y + 38)))

        # Target English Word
        target_word_str = f"\"{target_item['en'].upper()}\""
        word_surf = render_thai_text(target_word_str, font_size=40, color=TEXT_WHITE)
        surface.blit(word_surf, word_surf.get_rect(center=(WIDTH // 2, box_y + 95)))

        sub_thai = render_thai_text(f"(ความหมาย: {target_item['word']})", font_size=20, color=ACCENT_CYAN)
        surface.blit(sub_thai, sub_thai.get_rect(center=(WIDTH // 2, box_y + 138)))

        # 4. Live Microphone Waveform & Equalizer Display Area
        wave_box_w, wave_box_h = 660, 95
        wave_box_x = (WIDTH - wave_box_w) // 2
        wave_box_y = box_y + 170

        # Background display bay
        wave_bay = pygame.Surface((wave_box_w, wave_box_h), pygame.SRCALPHA)
        pygame.draw.rect(wave_bay, (10, 16, 30, 230), (0, 0, wave_box_w, wave_box_h), border_radius=16)
        pygame.draw.rect(wave_bay, (51, 65, 85, 180), (0, 0, wave_box_w, wave_box_h), width=2, border_radius=16)
        surface.blit(wave_bay, (wave_box_x, wave_box_y))

        # Extract live audio data
        bars = audio_data.get("bars", []) if audio_data else []
        waveform = audio_data.get("waveform", []) if audio_data else []
        volume = audio_data.get("volume", 0.0) if audio_data else 0.0

        if not bars:
            bars = [0.08] * 21

        # A. Draw 21 Live Equalizer Bars
        num_bars = len(bars)
        bar_gap = 26
        start_bx = WIDTH // 2 - ((num_bars - 1) * bar_gap) // 2
        bay_cy = wave_box_y + wave_box_h // 2

        for i, val in enumerate(bars):
            bx = start_bx + i * bar_gap
            max_h = 70
            h = int(max(8, min(max_h, val * max_h)))
            
            # Color gradient based on state and amplitude
            if is_success:
                b_col = ACCENT_EMERALD
            elif val > 0.45:
                b_col = ACCENT_AMBER
            else:
                b_col = ACCENT_CYAN

            b_rect = pygame.Rect(bx - 5, bay_cy - h // 2, 10, h)
            pygame.draw.rect(surface, b_col, b_rect, border_radius=5)

        # B. Draw Real-Time Live Oscilloscope Waveform Line
        if is_listening and waveform and len(waveform) >= 10:
            wave_pts = []
            num_pts = len(waveform)
            for idx, sample in enumerate(waveform):
                px = wave_box_x + int((idx / (num_pts - 1)) * wave_box_w)
                py = bay_cy + int(sample * 42.0)
                py = max(wave_box_y + 8, min(wave_box_y + wave_box_h - 8, py))
                wave_pts.append((px, py))

            if len(wave_pts) >= 2:
                pygame.draw.lines(surface, (254, 240, 138, 220), False, wave_pts, width=2)

        # 5. Status / Feedback Text
        if is_success:
            st_surf = render_thai_text("ออกเสียงถูกต้อง! ได้รับ +100 คะแนน", font_size=23, color=ACCENT_EMERALD)
        elif recognized_text:
            st_surf = render_thai_text(f"ได้ยิน: \"{recognized_text}\"...", font_size=22, color=feedback_color)
        elif is_listening:
            st_surf = render_thai_text("กำลังรอฟังเสียง... พูดคำศัพท์ภาษาอังกฤษใส่ไมโครโฟนได้เลย", font_size=19, color=TEXT_WHITE)
        else:
            st_surf = render_thai_text("เตรียมพร้อมฟังเสียง...", font_size=19, color=(148, 163, 184))

        surface.blit(st_surf, st_surf.get_rect(center=(WIDTH // 2, box_y + 300)))

        # 6. Hint Subtitle & Voice Level Indicator
        hint_str = f"ระดับสัญญาณไมค์: {int(volume * 100)}% | ออกเสียงภาษาอังกฤษให้ถูกต้องเพื่อปลดล็อกคะแนน" if is_listening else "ออกเสียงภาษาอังกฤษให้ถูกต้องเพื่อปลดล็อกคะแนนประจำรอบ"
        hint_surf = render_thai_text(hint_str, font_size=15, color=(148, 163, 184))
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, box_y + 365)))
