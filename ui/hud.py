import pygame
from config.constants import (
    WIDTH, HEIGHT, CARD_BORDER, TEXT_WHITE, ACCENT_CYAN, 
    ACCENT_AMBER, ACCENT_ROSE, ACCENT_EMERALD, HAND_CONNECTIONS
)
from ui.renderer import render_thai_text

class HUD:
    @staticmethod
    def draw_in_game_header(surface, mode, freedom_score, team_scores, current_team_idx, words_per_team, chances_left, mouse_pos=None):
        hud_h = 74
        header_surf = pygame.Surface((WIDTH, hud_h), pygame.SRCALPHA)
        header_surf.fill((15, 23, 42, 235))
        pygame.draw.line(header_surf, CARD_BORDER, (0, hud_h - 1), (WIDTH, hud_h - 1), 2)
        surface.blit(header_surf, (0, 0))
        
        # Menu Button
        menu_btn = pygame.Rect(18, 14, 110, 46)
        m_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
        m_hover = menu_btn.collidepoint(m_pos)
        pygame.draw.rect(surface, (30, 41, 59) if not m_hover else (51, 65, 85), menu_btn, border_radius=16)
        pygame.draw.rect(surface, CARD_BORDER, menu_btn, width=1, border_radius=16)
        m_text = render_thai_text("เมนูหลัก", font_size=18, color=TEXT_WHITE)
        surface.blit(m_text, m_text.get_rect(center=menu_btn.center))
        
        # Mode & Score Badges
        if mode == "FREEDOM":
            m_badge = render_thai_text("Freedom Mode", font_size=20, color=ACCENT_CYAN)
            surface.blit(m_badge, (145, 24))
            
            score_text = render_thai_text(f"คะแนน: {freedom_score}", font_size=24, color=ACCENT_AMBER)
            surface.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
        else:
            team = team_scores[current_team_idx]
            # Draw Color Dot
            pygame.draw.circle(surface, team["color"], (155, 37), 8)
            m_badge = render_thai_text(f"{team['name']} - คำที่ {team['words_done'] + 1}/{words_per_team}", font_size=22, color=team["color"])
            surface.blit(m_badge, (170, 24))
            
            score_text = render_thai_text(f"แต้มทีม: {team['score']}", font_size=24, color=ACCENT_AMBER)
            surface.blit(score_text, score_text.get_rect(midright=(WIDTH - 24, 37)))
            
        chances_surf = render_thai_text(f"โอกาส: {chances_left} ครั้ง", font_size=22, color=ACCENT_ROSE)
        surface.blit(chances_surf, chances_surf.get_rect(center=(WIDTH // 2, 37)))

        return menu_btn

    @staticmethod
    def draw_skeleton_and_cursor(surface, landmarks_screen, cursor_pos, current_gesture, is_pinched):
        # 1. Draw Skeleton Lines
        if landmarks_screen and len(landmarks_screen) >= 21:
            for p1_idx, p2_idx in HAND_CONNECTIONS:
                p1 = landmarks_screen[p1_idx]
                p2 = landmarks_screen[p2_idx]
                pygame.draw.line(surface, (15, 23, 42), p1, p2, 5)
                pygame.draw.line(surface, (56, 189, 248), p1, p2, 2)
                
            for pt in landmarks_screen:
                pygame.draw.circle(surface, (15, 23, 42), pt, 5)
                pygame.draw.circle(surface, (255, 255, 255), pt, 3)

        # 2. Draw Active Cursor
        cx, cy = int(cursor_pos[0]), int(cursor_pos[1])
        if cx < 0 or cy < 0 or cx > WIDTH or cy > HEIGHT:
            return
            
        cursor_col = ACCENT_AMBER if is_pinched else (ACCENT_EMERALD if current_gesture == "OK" else ACCENT_CYAN)
        
        pygame.draw.circle(surface, cursor_col, (cx, cy), 18, width=3)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5)
        
        if current_gesture != "NONE":
            g_tag = render_thai_text(f"ท่า: {current_gesture}", font_size=15, color=cursor_col)
            surface.blit(g_tag, (cx + 20, cy - 12))
