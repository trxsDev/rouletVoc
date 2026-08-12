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
        dim.fill((15, 23, 42, 215))
        surface.blit(dim, (0, 0))

        # 3. Central Voice Verification Modal
        box_w, box_h = 760, 390
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2 - 15

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (18, 28, 48, 252), (0, 0, box_w, box_h), border_radius=28)
        border_col = ACCENT_EMERALD if is_success else ACCENT_AMBER
        pygame.draw.rect(box_surf, border_col, (0, 0, box_w, box_h), width=3, border_radius=28)
        surface.blit(box_surf, (box_x, box_y))

        # Modal Header
        header_surf = render_thai_text("ตรวจสอบการออกเสียงคำศัพท์ (Voice Verification)", font_size=24, color=ACCENT_AMBER)
        surface.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, box_y + 40)))

        # Target English Word & Meaning
        target_word_str = f"\"{target_item['en'].upper()}\""
        word_surf = render_thai_text(target_word_str, font_size=46, color=TEXT_WHITE)
        surface.blit(word_surf, word_surf.get_rect(center=(WIDTH // 2, box_y + 105)))

        sub_thai = render_thai_text(f"(ความหมาย: {target_item['word']})", font_size=22, color=ACCENT_CYAN)
        surface.blit(sub_thai, sub_thai.get_rect(center=(WIDTH // 2, box_y + 155)))

        # 4. Clean Status Box ("Waiting for speak" / Results)
        stat_box_w, stat_box_h = 580, 85
        stat_box_x = (WIDTH - stat_box_w) // 2
        stat_box_y = box_y + 205

        stat_bg = pygame.Surface((stat_box_w, stat_box_h), pygame.SRCALPHA)
        
        if is_success:
            s_bg_col = (6, 78, 59, 220)
            s_border_col = ACCENT_EMERALD
            main_msg = "ออกเสียงถูกต้อง! (+100 คะแนน)"
            msg_color = ACCENT_EMERALD
        elif recognized_text:
            s_bg_col = (120, 53, 15, 180)
            s_border_col = feedback_color
            main_msg = f"ได้ยิน: \"{recognized_text}\""
            msg_color = feedback_color
        elif is_listening:
            # Animated pulse effect for Waiting for speak
            s_bg_col = (12, 22, 40, 230)
            s_border_col = ACCENT_AMBER
            main_msg = "Waiting for speak..."
            msg_color = ACCENT_AMBER
        else:
            s_bg_col = (10, 16, 30, 230)
            s_border_col = (51, 65, 85, 200)
            main_msg = "เตรียมพร้อมฟังเสียง..."
            msg_color = (148, 163, 184)

        pygame.draw.rect(stat_bg, s_bg_col, (0, 0, stat_box_w, stat_box_h), border_radius=20)
        pygame.draw.rect(stat_bg, s_border_col, (0, 0, stat_box_w, stat_box_h), width=2, border_radius=20)
        surface.blit(stat_bg, (stat_box_x, stat_box_y))

        status_text_surf = render_thai_text(main_msg, font_size=26, color=msg_color)
        surface.blit(status_text_surf, status_text_surf.get_rect(center=(WIDTH // 2, stat_box_y + stat_box_h // 2)))

        # 5. Hint Footer
        hint_surf = render_thai_text("ออกเสียงภาษาอังกฤษใส่ไมโครโฟนให้ถูกต้องเพื่อรับคะแนน", font_size=16, color=(148, 163, 184))
        surface.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, box_y + 335)))
