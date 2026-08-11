import pygame
from config.constants import CARD_BACK_COLOR, CARD_BORDER, ACCENT_AMBER, ACCENT_EMERALD, ACCENT_CYAN
from ui.renderer import render_thai_text, get_image

class Card:
    def __init__(self, x, y, width, height, item, idx):
        self.rect = pygame.Rect(x, y, width, height)
        self.item = item
        self.idx = idx
        self.is_flipped = False
        self.is_matched = False
        
        # Interactions
        self.hover_progress = 0.0
        self.action_charge = 0.0
        self.shake_offset = 0

    def draw(self, surface, show_face=False):
        if self.shake_offset > 0:
            self.shake_offset = -self.shake_offset + 2 if self.shake_offset > 0 else -self.shake_offset - 2
            if abs(self.shake_offset) < 2:
                self.shake_offset = 0

        draw_x = self.rect.x + self.shake_offset
        draw_y = self.rect.y
        draw_rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)
        
        card_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_col = CARD_BACK_COLOR
        border_color = CARD_BORDER
        
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
