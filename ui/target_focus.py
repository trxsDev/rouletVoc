import pygame
import math
import time
from config.constants import WIDTH, HEIGHT, ACCENT_AMBER, ACCENT_CYAN, TEXT_WHITE
from core.audio_engine import sound_engine
from ui.renderer import render_thai_text, get_image

class TargetFocusScreen:
    """
    Cinematic Zoom CTA stage that isolates the target card, zooms it to center,
    pronounces the English word 2 times clearly, and smoothly zooms back to grid!
    """

    @staticmethod
    def update_audio(elapsed, target_item, voice_count_ref):
        # 1st Pronunciation at 0.9s
        if elapsed >= 0.9 and voice_count_ref[0] == 0:
            sound_engine.play_vocab(target_item["id"])
            voice_count_ref[0] = 1
            
        # 2nd Pronunciation at 2.8s
        elif elapsed >= 2.8 and voice_count_ref[0] == 1:
            sound_engine.play_vocab(target_item["id"])
            voice_count_ref[0] = 2

    @staticmethod
    def draw(surface, cards, target_item, elapsed, voice_count):
        # Total lifecycle: 5.5s
        # 0.0s - 0.9s: Zoom In (t: 0.0 -> 1.0)
        # 0.9s - 4.6s: Full Focus & 2-Time Audio Playback (t: 1.0)
        # 4.6s - 5.5s: Zoom Out back to grid (t: 1.0 -> 0.0)
        if elapsed < 0.9:
            p = elapsed / 0.9
            t = math.sin(p * math.pi / 2)
        elif elapsed < 4.6:
            t = 1.0
        else:
            p = min(1.0, (elapsed - 4.6) / 0.9)
            t = 1.0 - math.sin(p * math.pi / 2)

        target_card = next((c for c in cards if c.item["id"] == target_item["id"]), cards[0])

        # 1. Draw other 5 cards in their grid slots
        for card in cards:
            if card.item["id"] != target_item["id"]:
                card.draw(surface, show_face=True)

        # 2. Cinematic Dim Vignette Overlay
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, int(t * 230)))
        surface.blit(dim, (0, 0))

        # 3. Interpolate Target Card Rect (Grid -> Center Stage 600x620)
        orig_r = target_card.rect
        dest_w, dest_h = 600, 620
        dest_x = (WIDTH - dest_w) // 2
        dest_y = (HEIGHT - dest_h) // 2 - 25

        cur_x = int(orig_r.x + (dest_x - orig_r.x) * t)
        cur_y = int(orig_r.y + (dest_y - orig_r.y) * t)
        cur_w = int(orig_r.width + (dest_w - orig_r.width) * t)
        cur_h = int(orig_r.height + (dest_h - orig_r.height) * t)

        # Draw expanding focus card
        card_surf = pygame.Surface((cur_w, cur_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 252), (0, 0, cur_w, cur_h), border_radius=int(24 + t * 14))
        border_col = ACCENT_AMBER
        border_w = int(4 + t * 4)
        pygame.draw.rect(card_surf, border_col, (0, 0, cur_w, cur_h), width=border_w, border_radius=int(24 + t * 14))
        surface.blit(card_surf, (cur_x, cur_y))

        # Card inner art & labels
        draw_rect = pygame.Rect(cur_x, cur_y, cur_w, cur_h)
        art_size = int(150 + t * 110)
        img_surf = get_image(target_item["filename"], target_size=(art_size, art_size))
        img_rect = img_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery - int(36 + t * 65)))
        surface.blit(img_surf, img_rect)

        # English Word (Large, clear gold text)
        font_en_size = int(24 + t * 36)
        en_text = f"\"{target_item['en'].upper()}\"" if t > 0.3 else target_item["en"]
        en_surf = render_thai_text(en_text, font_size=font_en_size, color=ACCENT_AMBER)
        surface.blit(en_surf, en_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + int(60 + t * 75))))

        # Thai Translation
        font_th_size = int(32 + t * 10)
        th_surf = render_thai_text(target_item["word"], font_size=font_th_size, color=target_item["color"])
        surface.blit(th_surf, th_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery + int(96 + t * 85))))

        # Top Header & 2-Time Pronunciation Status
        if t > 0.5:
            header_surf = render_thai_text("คำศัพท์ประจำรอบที่ต้องค้นหา (Target Word)", font_size=40, color=ACCENT_AMBER)
            surface.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, 95)))

            if voice_count >= 2:
                sub_msg = "ฟังซ้ำอีกครั้งให้ชัดเจน (รอบที่ 2/2) และจำภาพนี้ไว้ให้ดี!"
            elif voice_count == 1:
                sub_msg = "กำลังอ่านออกเสียงภาษาอังกฤษ (รอบที่ 1/2)..."
            else:
                sub_msg = "เตรียมพร้อมฟังเสียงอ่านภาษาอังกฤษ..."
                
            sub_surf = render_thai_text(sub_msg, font_size=28, color=TEXT_WHITE)
            surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT - 110)))
