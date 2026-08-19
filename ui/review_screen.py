import pygame
import math
import time
from config.constants import (
    WIDTH, HEIGHT, CARD_BORDER, TEXT_WHITE, ACCENT_AMBER, 
    ACCENT_CYAN, ACCENT_EMERALD, ACCENT_ROSE
)
from ui.renderer import render_thai_text, get_image

class ReviewScreens:
    @staticmethod
    def draw_mode_select(surface, on_freedom_click, on_flashcard_click, on_back_click, mouse_clicked=False, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        surface.fill((15, 23, 42))

        # Title & Subtitle (Safe Top Margin)
        title = render_thai_text("ทบทวนคำศัพท์ (Vocabulary Review)", font_size=52, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 110)))

        sub = render_thai_text("เลือกรูปแบบการฝึกทบทวนและออกเสียงคำศัพท์ภาษาอังกฤษ-ไทย", font_size=24, color=(148, 163, 184))
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 175)))

        # 2 Mode Cards (Centered, elevated from bottom danger zone)
        card_w, card_h = 520, 500
        f_rect = pygame.Rect(WIDTH // 2 - card_w - 30, 240, card_w, card_h)
        fc_rect = pygame.Rect(WIDTH // 2 + 30, 240, card_w, card_h)

        f_hover = f_rect.collidepoint(mouse_pos)
        fc_hover = fc_rect.collidepoint(mouse_pos)

        # 1. Freedom Review Card
        f_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(f_surf, (20, 30, 48, 235) if not f_hover else (30, 45, 75, 245), (0, 0, card_w, card_h), border_radius=32)
        pygame.draw.rect(f_surf, ACCENT_CYAN if f_hover else CARD_BORDER, (0, 0, card_w, card_h), width=4 if f_hover else 2, border_radius=32)
        surface.blit(f_surf, f_rect.topleft)

        star_icon = get_image("icon_star.png", target_size=(96, 96))
        surface.blit(star_icon, star_icon.get_rect(center=(f_rect.centerx, f_rect.top + 90)))

        f_t = render_thai_text("Freedom (สุ่มอิสระ)", font_size=36, color=ACCENT_CYAN)
        surface.blit(f_t, f_t.get_rect(center=(f_rect.centerx, f_rect.top + 175)))
        f_d1 = render_thai_text("สุ่มคำศัพท์ทั้งหมดได้เรื่อยๆ ไม่จำกัดรอบ", font_size=24, color=TEXT_WHITE)
        f_d2 = render_thai_text("เหมาะสำหรับฝึกฟังเสียงและทบทวนอย่างอิสระ", font_size=20, color=(148, 163, 184))
        surface.blit(f_d1, f_d1.get_rect(center=(f_rect.centerx, f_rect.top + 260)))
        surface.blit(f_d2, f_d2.get_rect(center=(f_rect.centerx, f_rect.top + 305)))

        btn_f = pygame.Rect(f_rect.centerx - 140, f_rect.bottom - 80, 280, 56)
        pygame.draw.rect(surface, ACCENT_CYAN if f_hover else (14, 116, 144), btn_f, border_radius=28)
        btn_f_t = render_thai_text("เลือกโหมดนี้", font_size=24, color=(15, 23, 42) if f_hover else TEXT_WHITE)
        surface.blit(btn_f_t, btn_f_t.get_rect(center=btn_f.center))

        # 2. Flashcard Review Card
        fc_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(fc_surf, (20, 30, 48, 235) if not fc_hover else (30, 45, 75, 245), (0, 0, card_w, card_h), border_radius=32)
        pygame.draw.rect(fc_surf, ACCENT_AMBER if fc_hover else CARD_BORDER, (0, 0, card_w, card_h), width=4 if fc_hover else 2, border_radius=32)
        surface.blit(fc_surf, fc_rect.topleft)

        trophy_icon = get_image("icon_trophy.png", target_size=(96, 96))
        surface.blit(trophy_icon, trophy_icon.get_rect(center=(fc_rect.centerx, fc_rect.top + 90)))

        fc_t = render_thai_text("Flashcard (ตัดยอดทีละคำ)", font_size=36, color=ACCENT_AMBER)
        surface.blit(fc_t, fc_t.get_rect(center=(fc_rect.centerx, fc_rect.top + 175)))
        fc_d1 = render_thai_text("สุ่มแล้วตัดคำออกจนครบ 12 คำ", font_size=24, color=TEXT_WHITE)
        fc_d2 = render_thai_text("มีเอฟเฟกต์พลุฉลองเมื่อทบทวนครบทุกคำ!", font_size=20, color=(148, 163, 184))
        surface.blit(fc_d1, fc_d1.get_rect(center=(fc_rect.centerx, fc_rect.top + 260)))
        surface.blit(fc_d2, fc_d2.get_rect(center=(fc_rect.centerx, fc_rect.top + 305)))

        btn_fc = pygame.Rect(fc_rect.centerx - 140, fc_rect.bottom - 80, 280, 56)
        pygame.draw.rect(surface, ACCENT_AMBER if fc_hover else (180, 83, 9), btn_fc, border_radius=28)
        btn_fc_t = render_thai_text("เลือกโหมดนี้", font_size=24, color=(15, 23, 42) if fc_hover else TEXT_WHITE)
        surface.blit(btn_fc_t, btn_fc_t.get_rect(center=btn_fc.center))

        # Bottom Back Button (Elevated from Dock)
        btn_back = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 130, 260, 56)
        bk_hover = btn_back.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (30, 41, 59) if not bk_hover else (51, 65, 85), btn_back, border_radius=28)
        pygame.draw.rect(surface, CARD_BORDER, btn_back, width=2, border_radius=28)
        bk_t = render_thai_text("<< กลับเมนูหลัก", font_size=22, color=TEXT_WHITE)
        surface.blit(bk_t, bk_t.get_rect(center=btn_back.center))

        if clicked:
            if f_hover:
                on_freedom_click()
            elif fc_hover:
                on_flashcard_click()
            elif bk_hover:
                on_back_click()

    @staticmethod
    def draw_wheel_stage(surface, wheel, sub_mode, remaining_items, on_spin_click, on_back_click, mouse_clicked=False, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        surface.fill((15, 23, 42))

        # Header Bar
        mode_label = "โหมดทบทวนอิสระ (Freedom Review)" if sub_mode == "FREEDOM" else f"โหมดแฟลชการ์ด (เหลือคำศัพท์ {len(remaining_items)} คำ)"
        h_col = ACCENT_CYAN if sub_mode == "FREEDOM" else ACCENT_AMBER
        head_t = render_thai_text(mode_label, font_size=34, color=h_col)
        surface.blit(head_t, (50, 40))

        # Back button at top-right
        btn_back = pygame.Rect(WIDTH - 220, 32, 170, 50)
        bk_hover = btn_back.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (30, 41, 59) if not bk_hover else (51, 65, 85), btn_back, border_radius=16)
        pygame.draw.rect(surface, CARD_BORDER, btn_back, width=2, border_radius=16)
        b_txt = render_thai_text("<< ย้อนกลับ", font_size=22, color=TEXT_WHITE)
        surface.blit(b_txt, b_txt.get_rect(center=btn_back.center))

        # Draw Center Wheel
        wheel.draw(surface)

        # Draw Side Deck Panel for FLASHCARD mode
        if sub_mode == "FLASHCARD" and remaining_items:
            deck_x = WIDTH - 340
            deck_y = 120
            deck_w = 290
            deck_h = 740
            deck_surf = pygame.Surface((deck_w, deck_h), pygame.SRCALPHA)
            pygame.draw.rect(deck_surf, (20, 30, 48, 230), (0, 0, deck_w, deck_h), border_radius=20)
            pygame.draw.rect(deck_surf, CARD_BORDER, (0, 0, deck_w, deck_h), width=2, border_radius=20)
            surface.blit(deck_surf, (deck_x, deck_y))

            d_title = render_thai_text(f"คลังคำศัพท์ ({len(remaining_items)}/12)", font_size=24, color=ACCENT_AMBER)
            surface.blit(d_title, d_title.get_rect(center=(deck_x + deck_w // 2, deck_y + 30)))

            for i, item in enumerate(remaining_items):
                pill_y = deck_y + 65 + i * 54
                if pill_y + 44 > deck_y + deck_h:
                    break
                pill_rect = pygame.Rect(deck_x + 16, pill_y, deck_w - 32, 44)
                pygame.draw.rect(surface, (30, 41, 59), pill_rect, border_radius=12)
                p_txt = render_thai_text(f"{item['en']} ({item['word']})", font_size=18, color=TEXT_WHITE)
                surface.blit(p_txt, (pill_rect.x + 14, pill_rect.y + 8))

        # Bottom Action Control (Spin Button - elevated above macOS dock)
        btn_spin = pygame.Rect(WIDTH // 2 - 180, HEIGHT - 140, 360, 64)
        sp_hover = btn_spin.collidepoint(mouse_pos)

        if wheel.is_spinning:
            pygame.draw.rect(surface, (51, 65, 85), btn_spin, border_radius=32)
            sp_txt = render_thai_text("กำลังหมุนวงล้อ...", font_size=26, color=(148, 163, 184))
        else:
            pygame.draw.rect(surface, ACCENT_AMBER if sp_hover else (217, 119, 6), btn_spin, border_radius=32)
            sp_txt = render_thai_text("หมุนวงล้อ [Spacebar]", font_size=26, color=(15, 23, 42))

        surface.blit(sp_txt, sp_txt.get_rect(center=btn_spin.center))

        if clicked:
            if bk_hover:
                on_back_click()
            elif sp_hover and not wheel.is_spinning:
                on_spin_click()

    @staticmethod
    def draw_word_reveal(surface, item, sub_mode, remaining_count, on_repeat_click, on_next_spin_click, on_back_click, mouse_clicked=False, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        surface.fill((15, 23, 42))

        # Dim Card Container (Centered Safe Area)
        card_w, card_h = 780, 560
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2 - 40

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 252), (0, 0, card_w, card_h), border_radius=36)
        pygame.draw.rect(card_surf, ACCENT_AMBER, (0, 0, card_w, card_h), width=4, border_radius=36)
        surface.blit(card_surf, (card_x, card_y))

        # Top Badge
        badge_text = "สุ่มได้คำศัพท์:" if sub_mode == "FREEDOM" else f"สุ่มได้คำศัพท์ (เหลืออีก {remaining_count} คำ):"
        b_surf = render_thai_text(badge_text, font_size=28, color=ACCENT_AMBER)
        surface.blit(b_surf, b_surf.get_rect(center=(WIDTH // 2, card_y + 48)))

        # 3D Icon
        icon_img = get_image(item.get("filename", "book.png"), target_size=(180, 180))
        surface.blit(icon_img, icon_img.get_rect(center=(WIDTH // 2, card_y + 175)))

        # English Word
        en_surf = render_thai_text(f"\"{item['en'].upper()}\"", font_size=60, color=TEXT_WHITE)
        surface.blit(en_surf, en_surf.get_rect(center=(WIDTH // 2, card_y + 315)))

        # Thai Translation
        th_surf = render_thai_text(f"ความหมาย: {item['word']}", font_size=32, color=ACCENT_CYAN)
        surface.blit(th_surf, th_surf.get_rect(center=(WIDTH // 2, card_y + 385)))

        # Action Button Row (Safe elevated above bottom macOS dock)
        btn_y = HEIGHT - 140
        btn_repeat = pygame.Rect(WIDTH // 2 - 360, btn_y, 220, 58)
        btn_next = pygame.Rect(WIDTH // 2 - 110, btn_y, 230, 58)
        btn_menu = pygame.Rect(WIDTH // 2 + 150, btn_y, 210, 58)

        rp_hover = btn_repeat.collidepoint(mouse_pos)
        nx_hover = btn_next.collidepoint(mouse_pos)
        mn_hover = btn_menu.collidepoint(mouse_pos)

        # 1. Repeat Audio Button
        pygame.draw.rect(surface, ACCENT_CYAN if rp_hover else (14, 116, 144), btn_repeat, border_radius=29)
        rp_t = render_thai_text("ฟังซ้ำ 🔊 [R]", font_size=22, color=(15, 23, 42) if rp_hover else TEXT_WHITE)
        surface.blit(rp_t, rp_t.get_rect(center=btn_repeat.center))

        # 2. Next Spin Button
        next_label = "หมุนต่อ 🎡 [Space]" if (sub_mode == "FREEDOM" or remaining_count > 0) else "ดูผลสรุป 🎉"
        pygame.draw.rect(surface, ACCENT_EMERALD if nx_hover else (16, 140, 100), btn_next, border_radius=29)
        nx_t = render_thai_text(next_label, font_size=22, color=(15, 23, 42) if nx_hover else TEXT_WHITE)
        surface.blit(nx_t, nx_t.get_rect(center=btn_next.center))

        # 3. Back / Menu Button
        pygame.draw.rect(surface, (30, 41, 59) if not mn_hover else (51, 65, 85), btn_menu, border_radius=29)
        pygame.draw.rect(surface, CARD_BORDER, btn_menu, width=2, border_radius=29)
        mn_t = render_thai_text("กลับเมนู [ESC]", font_size=22, color=TEXT_WHITE)
        surface.blit(mn_t, mn_t.get_rect(center=btn_menu.center))

        if clicked:
            if rp_hover:
                on_repeat_click()
            elif nx_hover:
                on_next_spin_click()
            elif mn_hover:
                on_back_click()

    @staticmethod
    def draw_congratulations(surface, fireworks, reviewed_items, on_replay_click, on_menu_click, mouse_clicked=False, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        surface.fill((15, 23, 42))

        # 1. Update and draw festive fireworks
        fireworks.update()
        fireworks.draw(surface)

        # 2. Celebration Header Box
        box_w, box_h = 1040, 580
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2 - 40

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (15, 23, 42, 235), (0, 0, box_w, box_h), border_radius=36)
        pygame.draw.rect(box_surf, ACCENT_AMBER, (0, 0, box_w, box_h), width=5, border_radius=36)
        surface.blit(box_surf, (box_x, box_y))

        # Trophy & Banner
        trophy_icon = get_image("icon_trophy.png", target_size=(105, 105))
        surface.blit(trophy_icon, trophy_icon.get_rect(center=(WIDTH // 2, box_y + 75)))

        title = render_thai_text("🎉 CONGRATULATIONS! 🎉", font_size=48, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, box_y + 155)))

        sub = render_thai_text("ยินดีด้วย! คุณได้ทบทวนคำศัพท์ครบทั้งหมด 12 คำเรียบร้อยแล้ว", font_size=26, color=TEXT_WHITE)
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, box_y + 205)))

        # Summary Word Badges (3 rows x 4 cols)
        start_bx = box_x + 60
        start_by = box_y + 260
        for i, item in enumerate(reviewed_items):
            col = i % 4
            row = i // 4
            bx = start_bx + col * 230
            by = start_by + row * 60
            p_rect = pygame.Rect(bx, by, 215, 48)
            pygame.draw.rect(surface, (30, 41, 59), p_rect, border_radius=12)
            pygame.draw.rect(surface, ACCENT_CYAN, p_rect, width=2, border_radius=12)
            p_txt = render_thai_text(f"✓ {item['en']}", font_size=20, color=ACCENT_AMBER)
            surface.blit(p_txt, p_txt.get_rect(center=p_rect.center))

        # Bottom Buttons (Safe Area elevated above Dock)
        btn_y = HEIGHT - 140
        btn_replay = pygame.Rect(WIDTH // 2 - 250, btn_y, 230, 58)
        btn_menu = pygame.Rect(WIDTH // 2 + 20, btn_y, 230, 58)

        rp_hover = btn_replay.collidepoint(mouse_pos)
        mn_hover = btn_menu.collidepoint(mouse_pos)

        pygame.draw.rect(surface, ACCENT_AMBER if rp_hover else (217, 119, 6), btn_replay, border_radius=29)
        t_rp = render_thai_text("เล่นอีกครั้ง [R]", font_size=24, color=(15, 23, 42))
        surface.blit(t_rp, t_rp.get_rect(center=btn_replay.center))

        pygame.draw.rect(surface, (30, 41, 59) if not mn_hover else (51, 65, 85), btn_menu, border_radius=29)
        pygame.draw.rect(surface, CARD_BORDER, btn_menu, width=2, border_radius=29)
        t_mn = render_thai_text("กลับหน้าหลัก [ESC]", font_size=24, color=TEXT_WHITE)
        surface.blit(t_mn, t_mn.get_rect(center=btn_menu.center))

        if clicked:
            if rp_hover:
                on_replay_click()
            elif mn_hover:
                on_menu_click()
