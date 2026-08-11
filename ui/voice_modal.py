import pygame
import math
import time
from config.constants import WIDTH, HEIGHT, ACCENT_AMBER, ACCENT_EMERALD, ACCENT_CYAN, TEXT_WHITE
from ui.renderer import render_thai_text

class VoiceModal:
    @staticmethod
    def draw(surface, cards, target_item, is_listening, is_success, recognized_text, feedback_msg, feedback_color):
        # 1. Background Cards
        for card in cards:
            card.draw(surface, show_face=card.is_matched)

        # 2. Focus Dim Overlay
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 195))
        surface.blit(dim, (0, 0))

        # 3. Central Voice Verification Modal
        box_w, box_h = 740, 370
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2 - 10
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (20, 30, 48, 252), (0, 0, box_w, box_h), border_radius=26)
        border_col = ACCENT_EMERALD if is_success else ACCENT_AMBER
        pygame.draw.rect(box_surf, border_col, (0, 0, box_w, box_h), width=3, border_radius=26)
        surface.blit(box_surf, (box_x, box_y))

        # Modal Header
        header_surf = render_thai_text("🎙️ ตรวจสอบการออกเสียงคำศัพท์ (Voice Verification)", font_size=25, color=ACCENT_AMBER)
        surface.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, box_y + 42)))

        # Target English Word
        target_word_str = f"🗣️ \"{target_item['en'].upper()}\""
        word_surf = render_thai_text(target_word_str, font_size=42, color=TEXT_WHITE)
        surface.blit(word_surf, word_surf.get_rect(center=(WIDTH // 2, box_y + 110)))

        sub_thai = render_thai_text(f"(ความหมาย: {target_item['word']})", font_size=20, color=ACCENT_CYAN)
        surface.blit(sub_thai, sub_thai.get_rect(center=(WIDTH // 2, box_y + 155)))

        # Pulsing Audio Waveform Animation
        now = time.time()
        wave_cx = WIDTH // 2
        wave_cy = box_y + 215
        num_bars = 13
        for i in range(num_bars):
            offset = (i - num_bars // 2) * 16
            if is_listening:
                h = int(12 + math.sin(now * 9 + i * 0.6) * 18 + math.cos(now * 14 + i * 1.1) * 10)
                h = max(8, min(48, h))
            else:
                h = 10
            bar_rect = pygame.Rect(wave_cx + offset - 4, wave_cy - h // 2, 8, h)
            bar_col = ACCENT_EMERALD if is_success else ACCENT_CYAN
            pygame.draw.rect(surface, bar_col, bar_rect, border_radius=4)

        # Status / Feedback Text
        if is_success:
            st_surf = render_thai_text("🎉 ออกเสียงถูกต้อง! ได้รับ +100 คะแนน", font_size=24, color=ACCENT_EMERALD)
        elif recognized_text:
            st_surf = render_thai_text(f"ได้ยิน: \"{recognized_text}\"...", font_size=22, color=feedback_color)
        elif is_listening:
            st_surf = render_thai_text("🟢 กำลังรอฟังเสียง... พูดคำศัพท์ภาษาอังกฤษใส่ไมโครโฟนได้เลย", font_size=19, color=TEXT_WHITE)
        else:
            st_surf = render_thai_text("เตรียมพร้อมฟังเสียง...", font_size=19, color=(148, 163, 184))

        surface.blit(st_surf, st_surf.get_rect(center=(WIDTH // 2, box_y + 280)))

        # Hint Subtitle
        hint_surf = render_thai_text("💡 ออกเสียงภาษาอังกฤษให้ถูกต้องเพื่อปลดล็อกคะแนนประจำรอบ", font_size=16, color=(148, 163, 184))
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, box_y + 332)))
