import pygame
import math
import time
from config.constants import (
    WIDTH, HEIGHT, CARD_BORDER, TEXT_WHITE, ACCENT_AMBER, 
    ACCENT_CYAN, ACCENT_EMERALD, ACCENT_ROSE, TEAM_PALETTES
)
from config.items import ITEMS_POOL
from ui.renderer import render_thai_text, get_image

class Screens:
    @staticmethod
    def draw_setup_camera(surface, tracking_engine, on_switch_cam_cb, on_next_cb, bg_cam=None, mouse_clicked=False):
        mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        # 1. Background Sleek Fill
        surface.fill((15, 23, 42))

        # 2. Main Card Container
        card_w, card_h = 820, 520
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2 - 10

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 245), (0, 0, card_w, card_h), border_radius=26)
        pygame.draw.rect(card_surf, (51, 65, 85, 200), (0, 0, card_w, card_h), width=2, border_radius=26)
        surface.blit(card_surf, (card_x, card_y))

        # Title & Subtitle
        title = render_thai_text("ขั้นตอนที่ 1/2: เลือกและปรับตำแหน่งกล้อง (Camera Setup)", font_size=26, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, card_y + 36)))

        sub = render_thai_text("โปรดตรวจสอบภาพจากกล้องและเลือกอุปกรณ์กล้องที่ต้องการใช้", font_size=17, color=(148, 163, 184))
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, card_y + 70)))

        # 3. Live Video Feed Preview Bay
        prev_w, prev_h = 440, 275
        prev_x = WIDTH // 2 - prev_w // 2
        prev_y = card_y + 105

        # Draw frame if available from main loop (Zero duplicate cap.read())
        if bg_cam is not None:
            import cv2
            frame_resized = cv2.resize(bg_cam, (prev_w, prev_h))
            cam_surf = pygame.image.frombuffer(frame_resized.tobytes(), (prev_w, prev_h), "RGB")
            surface.blit(cam_surf, (prev_x, prev_y))
        else:
            prev_bg = pygame.Surface((prev_w, prev_h), pygame.SRCALPHA)
            pygame.draw.rect(prev_bg, (10, 15, 28, 250), (0, 0, prev_w, prev_h), border_radius=16)
            surface.blit(prev_bg, (prev_x, prev_y))
            no_cam = render_thai_text("กำลังเปิดกล้อง...", font_size=20, color=(148, 163, 184))
            surface.blit(no_cam, no_cam.get_rect(center=(WIDTH // 2, prev_y + prev_h // 2)))

        # Frame border
        pygame.draw.rect(surface, ACCENT_CYAN, (prev_x, prev_y, prev_w, prev_h), width=3, border_radius=16)

        # 4. Camera Selection Options
        cams = tracking_engine.available_cams if tracking_engine else [0]
        cur_cam = tracking_engine.cam_index if tracking_engine else 0
        
        btn_y = prev_y + prev_h + 16
        total_cams_w = len(cams) * 170 + (len(cams) - 1) * 14
        start_bx = WIDTH // 2 - total_cams_w // 2

        for i, c_idx in enumerate(cams):
            bx = start_bx + i * (170 + 14)
            b_rect = pygame.Rect(bx, btn_y, 170, 42)
            is_active = (c_idx == cur_cam)
            b_hover = b_rect.collidepoint(mouse_pos)

            if b_hover and clicked and not is_active:
                on_switch_cam_cb(c_idx)

            if is_active:
                b_col = ACCENT_AMBER
                t_col = (15, 23, 42)
            elif b_hover:
                b_col = (30, 58, 95)
                t_col = TEXT_WHITE
            else:
                b_col = (20, 35, 55)
                t_col = (148, 163, 184)

            pygame.draw.rect(surface, b_col, b_rect, border_radius=12)
            pygame.draw.rect(surface, ACCENT_AMBER if is_active else CARD_BORDER, b_rect, width=2 if is_active else 1, border_radius=12)
            
            c_label = f"กล้อง {c_idx} {'(เลือกอยู่)' if is_active else ''}"
            c_surf = render_thai_text(c_label, font_size=16, color=t_col)
            surface.blit(c_surf, c_surf.get_rect(center=b_rect.center))

        # 5. Next Button
        next_w, next_h = 240, 48
        next_rect = pygame.Rect(WIDTH // 2 - next_w // 2, card_y + card_h - 60, next_w, next_h)
        next_hover = next_rect.collidepoint(mouse_pos)
        if next_hover and clicked:
            on_next_cb()

        pygame.draw.rect(surface, ACCENT_EMERALD if next_hover else (16, 140, 100), next_rect, border_radius=24)
        next_text = render_thai_text("ถัดไป: ตรวจสอบ WiFi >>", font_size=18, color=(15, 23, 42) if next_hover else TEXT_WHITE)
        surface.blit(next_text, next_text.get_rect(center=next_rect.center))

    @staticmethod
    def draw_setup_wifi(surface, wifi_info, on_recheck_cb, on_back_cb, on_next_cb, mouse_clicked=False):
        mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        # 1. Background Sleek Fill
        surface.fill((15, 23, 42))

        # 2. Main Card Container
        card_w, card_h = 820, 500
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2 - 10

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (20, 30, 48, 245), (0, 0, card_w, card_h), border_radius=26)
        pygame.draw.rect(card_surf, (51, 65, 85, 200), (0, 0, card_w, card_h), width=2, border_radius=26)
        surface.blit(card_surf, (card_x, card_y))

        # Title & Subtitle
        title = render_thai_text("ขั้นตอนที่ 2/2: ตรวจสอบการเชื่อมต่อ WiFi / Internet", font_size=26, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, card_y + 40)))

        sub = render_thai_text("ตรวจสอบอินเทอร์เน็ตสำหรับการประมวลผลเสียง Google Speech Recognition", font_size=17, color=(148, 163, 184))
        surface.blit(sub, sub.get_rect(center=(WIDTH // 2, card_y + 76)))

        # 3. Connection Status Card Box
        is_online = wifi_info.get("online", True)
        detail_msg = wifi_info.get("detail", "เชื่อมต่ออินเทอร์เน็ตสำเร็จ (Online)")
        ping_ms = wifi_info.get("ping", 15)

        box_w, box_h = 680, 210
        box_x = WIDTH // 2 - box_w // 2
        box_y = card_y + 120

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (12, 20, 36, 240), (0, 0, box_w, box_h), border_radius=20)
        box_border = ACCENT_EMERALD if is_online else ACCENT_AMBER
        pygame.draw.rect(box_surf, box_border, (0, 0, box_w, box_h), width=2, border_radius=20)
        surface.blit(box_surf, (box_x, box_y))

        # Status Header
        stat_header = render_thai_text(f"สถานะอินเทอร์เน็ต: {'เชื่อมต่อสมบูรณ์ (Online)' if is_online else 'โหมดออฟไลน์ (Offline)'}", font_size=22, color=box_border)
        surface.blit(stat_header, (box_x + 35, box_y + 25))

        # Details
        d1 = render_thai_text(f"- สถานะระบบ: {detail_msg}", font_size=18, color=TEXT_WHITE)
        d2 = render_thai_text(f"- ความเร็วการตอบสนอง (Ping): ~{ping_ms} ms", font_size=17, color=ACCENT_CYAN if is_online else (148, 163, 184))
        d3 = render_thai_text("- ระบบถอดความเสียง: Google Cloud Speech Engine พร้อมใช้งาน", font_size=17, color=TEXT_WHITE if is_online else (148, 163, 184))
        surface.blit(d1, (box_x + 35, box_y + 75))
        surface.blit(d2, (box_x + 35, box_y + 115))
        surface.blit(d3, (box_x + 35, box_y + 155))

        # Recheck Button
        recheck_rect = pygame.Rect(box_x + box_w - 200, box_y + 25, 170, 36)
        re_hover = recheck_rect.collidepoint(mouse_pos)
        if re_hover and clicked:
            on_recheck_cb()
        pygame.draw.rect(surface, (30, 58, 95) if re_hover else (20, 35, 55), recheck_rect, border_radius=10)
        pygame.draw.rect(surface, ACCENT_CYAN, recheck_rect, width=1, border_radius=10)
        re_surf = render_thai_text("ตรวจสอบใหม่", font_size=15, color=TEXT_WHITE)
        surface.blit(re_surf, re_surf.get_rect(center=recheck_rect.center))

        # 4. Navigation Buttons: Back & Start Game
        btn_y = card_y + card_h - 75

        # Back Button
        back_rect = pygame.Rect(card_x + 50, btn_y, 190, 48)
        back_hover = back_rect.collidepoint(mouse_pos)
        if back_hover and clicked:
            on_back_cb()
        pygame.draw.rect(surface, (30, 41, 59) if back_hover else (20, 30, 48), back_rect, border_radius=24)
        pygame.draw.rect(surface, CARD_BORDER, back_rect, width=2, border_radius=24)
        back_surf = render_thai_text("<< ย้อนกลับ (กล้อง)", font_size=17, color=TEXT_WHITE)
        surface.blit(back_surf, back_surf.get_rect(center=back_rect.center))

        # Next / Enter Game Button
        enter_rect = pygame.Rect(card_x + card_w - 290, btn_y, 240, 48)
        enter_hover = enter_rect.collidepoint(mouse_pos)
        if enter_hover and clicked:
            on_next_cb()
        pygame.draw.rect(surface, ACCENT_EMERALD if enter_hover else (16, 140, 100), enter_rect, border_radius=24)
        enter_surf = render_thai_text("เริ่มต้นเข้าสู่เกม >>", font_size=18, color=(15, 23, 42) if enter_hover else TEXT_WHITE)
        surface.blit(enter_surf, enter_surf.get_rect(center=enter_rect.center))

    @staticmethod
    def draw_landing_menu(surface, on_freedom_click, on_tournament_click, mouse_clicked=False):
        mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        # Sleek Title Card
        title_surf = render_thai_text("ROULETVOC", font_size=58, color=ACCENT_AMBER)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 100)))

        sub_surf = render_thai_text("เกมรูเล็ตต์ท่าทางและฝึกออกเสียงคำศัพท์ AR", font_size=24, color=TEXT_WHITE)
        surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 150)))

        # Mode Selection Cards
        card_w, card_h = 360, 360
        f_rect = pygame.Rect(WIDTH // 2 - card_w - 20, 210, card_w, card_h)
        t_rect = pygame.Rect(WIDTH // 2 + 20, 210, card_w, card_h)

        f_hover = f_rect.collidepoint(mouse_pos)
        t_hover = t_rect.collidepoint(mouse_pos)

        # 1. Freedom Mode Card
        f_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(f_surf, (20, 30, 48, 230) if not f_hover else (30, 45, 75, 245), (0, 0, card_w, card_h), border_radius=24)
        pygame.draw.rect(f_surf, ACCENT_CYAN if f_hover else CARD_BORDER, (0, 0, card_w, card_h), width=3 if f_hover else 1, border_radius=24)
        surface.blit(f_surf, f_rect.topleft)

        # 3D Star Icon
        star_icon = get_image("icon_star.png", target_size=(74, 74))
        surface.blit(star_icon, star_icon.get_rect(center=(f_rect.centerx, f_rect.top + 70)))
        
        f_title = render_thai_text("Freedom Mode", font_size=28, color=ACCENT_CYAN)
        surface.blit(f_title, f_title.get_rect(center=(f_rect.centerx, f_rect.top + 130)))
        f_desc1 = render_thai_text("เล่นอิสระ สะสมคะแนนคนเดียว", font_size=18, color=TEXT_WHITE)
        f_desc2 = render_thai_text("ไม่มีจำกัดรอบ ฝึกท่าทางและสำเนียง", font_size=16, color=(148, 163, 184))
        surface.blit(f_desc1, f_desc1.get_rect(center=(f_rect.centerx, f_rect.top + 195)))
        surface.blit(f_desc2, f_desc2.get_rect(center=(f_rect.centerx, f_rect.top + 230)))

        btn_f = pygame.Rect(f_rect.centerx - 100, f_rect.bottom - 65, 200, 44)
        pygame.draw.rect(surface, ACCENT_CYAN if f_hover else (14, 116, 144), btn_f, border_radius=22)
        btn_f_text = render_thai_text("เริ่มเล่นทันที", font_size=18, color=(15, 23, 42) if f_hover else TEXT_WHITE)
        surface.blit(btn_f_text, btn_f_text.get_rect(center=btn_f.center))

        # 2. Team Tournament Mode Card
        t_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(t_surf, (20, 30, 48, 230) if not t_hover else (30, 45, 75, 245), (0, 0, card_w, card_h), border_radius=24)
        pygame.draw.rect(t_surf, ACCENT_AMBER if t_hover else CARD_BORDER, (0, 0, card_w, card_h), width=3 if t_hover else 1, border_radius=24)
        surface.blit(t_surf, t_rect.topleft)

        # 3D Trophy Icon
        trophy_icon = get_image("icon_trophy.png", target_size=(74, 74))
        surface.blit(trophy_icon, trophy_icon.get_rect(center=(t_rect.centerx, t_rect.top + 70)))
        
        t_title = render_thai_text("Team Battle", font_size=28, color=ACCENT_AMBER)
        surface.blit(t_title, t_title.get_rect(center=(t_rect.centerx, t_rect.top + 130)))
        t_desc1 = render_thai_text("โหมดแข่งขันจัดอันดับเป็นทีม", font_size=18, color=TEXT_WHITE)
        t_desc2 = render_thai_text("กำหนด 2-8 ทีม แข่งเปิดคำศัพท์สะสมแต้ม", font_size=16, color=(148, 163, 184))
        surface.blit(t_desc1, t_desc1.get_rect(center=(t_rect.centerx, t_rect.top + 195)))
        surface.blit(t_desc2, t_desc2.get_rect(center=(t_rect.centerx, t_rect.top + 230)))

        btn_t = pygame.Rect(t_rect.centerx - 100, t_rect.bottom - 65, 200, 44)
        pygame.draw.rect(surface, ACCENT_AMBER if t_hover else (180, 83, 9), btn_t, border_radius=22)
        btn_t_text = render_thai_text("ตั้งค่าทีมและแข่งขัน", font_size=18, color=(15, 23, 42) if t_hover else TEXT_WHITE)
        surface.blit(btn_t_text, btn_t_text.get_rect(center=btn_t.center))

        if clicked:
            if f_hover:
                on_freedom_click()
            elif t_hover:
                on_tournament_click()

    @staticmethod
    def draw_team_setup(surface, num_teams, words_per_team, on_teams_change, on_words_change, on_start_click, on_back_click, mouse_clicked=False):
        mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        title = render_thai_text("ตั้งค่าการแข่งขันแบบทีม (Team Battle Setup)", font_size=32, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 70)))

        # 1. Number of Teams Control
        row1_y = 150
        lbl1 = render_thai_text("จำนวนทีมแข่งขัน (2 - 8 ทีม):", font_size=22, color=TEXT_WHITE)
        surface.blit(lbl1, (WIDTH // 2 - 320, row1_y + 10))

        btn_dec_t = pygame.Rect(WIDTH // 2 + 80, row1_y, 44, 44)
        btn_inc_t = pygame.Rect(WIDTH // 2 + 230, row1_y, 44, 44)

        t_val = render_thai_text(f"{num_teams} ทีม", font_size=24, color=ACCENT_CYAN)
        surface.blit(t_val, t_val.get_rect(center=(WIDTH // 2 + 177, row1_y + 22)))

        for btn, label, delta in [(btn_dec_t, "<", -1), (btn_inc_t, ">", 1)]:
            hov = btn.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (51, 65, 85) if not hov else (71, 85, 105), btn, border_radius=12)
            pygame.draw.rect(surface, CARD_BORDER, btn, width=1, border_radius=12)
            t_b = render_thai_text(label, font_size=24, color=TEXT_WHITE)
            surface.blit(t_b, t_b.get_rect(center=btn.center))
            if clicked and hov:
                on_teams_change(delta)

        # 2. Words per Team Control
        row2_y = 220
        lbl2 = render_thai_text(f"จำนวนคำศัพท์ต่อทีม (1 - {len(ITEMS_POOL)} คำ):", font_size=22, color=TEXT_WHITE)
        surface.blit(lbl2, (WIDTH // 2 - 320, row2_y + 10))

        btn_dec_w = pygame.Rect(WIDTH // 2 + 80, row2_y, 44, 44)
        btn_inc_w = pygame.Rect(WIDTH // 2 + 230, row2_y, 44, 44)

        w_val = render_thai_text(f"{words_per_team} คำ", font_size=24, color=ACCENT_CYAN)
        surface.blit(w_val, w_val.get_rect(center=(WIDTH // 2 + 177, row2_y + 22)))

        for btn, label, delta in [(btn_dec_w, "<", -1), (btn_inc_w, ">", 1)]:
            hov = btn.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (51, 65, 85) if not hov else (71, 85, 105), btn, border_radius=12)
            pygame.draw.rect(surface, CARD_BORDER, btn, width=1, border_radius=12)
            t_b = render_thai_text(label, font_size=24, color=TEXT_WHITE)
            surface.blit(t_b, t_b.get_rect(center=btn.center))
            if clicked and hov:
                on_words_change(delta)

        # Team Roster Badges
        roster_y = 295
        r_title = render_thai_text("รายชื่อทีมที่จะลงแข่งขัน:", font_size=18, color=(148, 163, 184))
        surface.blit(r_title, (WIDTH // 2 - 320, roster_y))

        for i in range(num_teams):
            p = TEAM_PALETTES[i]
            col = i % 4
            row = i // 4
            bx = WIDTH // 2 - 320 + col * 165
            by = roster_y + 32 + row * 45
            b_rect = pygame.Rect(bx, by, 155, 38)
            pygame.draw.rect(surface, p["bg_col"], b_rect, border_radius=10)
            pygame.draw.rect(surface, p["color"], b_rect, width=2, border_radius=10)
            
            # Draw Color Dot
            pygame.draw.circle(surface, p["color"], (bx + 20, by + 19), 6)
            b_text = render_thai_text(p["name"], font_size=16, color=TEXT_WHITE)
            surface.blit(b_text, b_text.get_rect(center=(bx + 85, by + 19)))

        # Bottom Buttons
        btn_start = pygame.Rect(WIDTH // 2 - 190, HEIGHT - 90, 180, 52)
        btn_back = pygame.Rect(WIDTH // 2 + 10, HEIGHT - 90, 180, 52)

        st_hov = btn_start.collidepoint(mouse_pos)
        bk_hov = btn_back.collidepoint(mouse_pos)

        pygame.draw.rect(surface, ACCENT_EMERALD if st_hov else (5, 150, 105), btn_start, border_radius=26)
        t_st = render_thai_text("เริ่มแข่งขัน", font_size=20, color=(15, 23, 42) if st_hov else TEXT_WHITE)
        surface.blit(t_st, t_st.get_rect(center=btn_start.center))

        pygame.draw.rect(surface, (30, 41, 59) if not bk_hov else (51, 65, 85), btn_back, border_radius=26)
        pygame.draw.rect(surface, CARD_BORDER, btn_back, width=1, border_radius=26)
        t_bk = render_thai_text("ย้อนกลับ", font_size=20, color=TEXT_WHITE)
        surface.blit(t_bk, t_bk.get_rect(center=btn_back.center))

        if clicked:
            if st_hov:
                on_start_click()
            elif bk_hov:
                on_back_click()

    @staticmethod
    def draw_team_ready(surface, current_team, charge):
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 225))
        surface.blit(dim, (0, 0))

        # Team Banner
        b_surf = render_thai_text(f"ถึงตาของ {current_team['name']} ({current_team['thai']})!", font_size=38, color=current_team["color"])
        surface.blit(b_surf, b_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 140)))

        inst1 = render_thai_text("ให้ตัวแทนทีมยืนหน้ากล้อง", font_size=24, color=TEXT_WHITE)
        surface.blit(inst1, inst1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

        inst2 = render_thai_text("ทำมือท่า 'OK' ค้างไว้เพื่อยืนยันความพร้อมและเริ่มเล่น", font_size=26, color=ACCENT_AMBER)
        surface.blit(inst2, inst2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))

        # 3D OK Gesture Icon
        ok_img = get_image("gesture_ok.png", target_size=(120, 120))
        surface.blit(ok_img, ok_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        # Circular Charge Gauge
        cx, cy = WIDTH // 2, HEIGHT // 2 + 165
        gauge_w = 400
        bar_rect = pygame.Rect(cx - gauge_w // 2, cy, gauge_w, 22)
        pygame.draw.rect(surface, (30, 41, 59), bar_rect, border_radius=11)
        pygame.draw.rect(surface, CARD_BORDER, bar_rect, width=2, border_radius=11)

        fill_w = int(gauge_w * charge)
        if fill_w > 0:
            fill_rect = pygame.Rect(cx - gauge_w // 2, cy, fill_w, 22)
            pygame.draw.rect(surface, ACCENT_EMERALD, fill_rect, border_radius=11)

        pct_surf = render_thai_text(f"ความพร้อม: {int(charge * 100)}%", font_size=18, color=ACCENT_EMERALD if charge > 0.5 else TEXT_WHITE)
        surface.blit(pct_surf, pct_surf.get_rect(center=(cx, cy + 38)))

    @staticmethod
    def draw_podium_dashboard(surface, ranked_teams, on_replay_click, on_menu_click, mouse_clicked=False):
        mouse_pos = pygame.mouse.get_pos()
        clicked = mouse_clicked

        ranked_teams = sorted(ranked_teams, key=lambda t: (t["score"], -t["time_spent"]), reverse=True)

        title = render_thai_text("สรุปผลการแข่งขัน (Tournament Podium)", font_size=36, color=ACCENT_AMBER)
        surface.blit(title, title.get_rect(center=(WIDTH // 2, 55)))

        # Top 3 Podium Cards
        podium_y = 110
        top_count = min(3, len(ranked_teams))
        col_w = 210
        gap = 20
        start_x = (WIDTH - (top_count * col_w + (top_count - 1) * gap)) // 2

        podium_order = [1, 0, 2] if top_count >= 3 else ([0, 1] if top_count == 2 else [0])
        rank_labels = ["2nd Place", "1st WINNER", "3rd Place"] if top_count >= 3 else (["1st WINNER", "2nd Place"] if top_count == 2 else ["1st WINNER"])
        heights = [190, 220, 175] if top_count >= 3 else ([220, 190] if top_count == 2 else [220])

        for pos_idx, team_idx in enumerate(podium_order):
            if team_idx >= len(ranked_teams):
                continue
            team = ranked_teams[team_idx]
            card_x = start_x + pos_idx * (col_w + gap)
            card_h = heights[pos_idx]
            card_y = podium_y + (220 - card_h)

            p_surf = pygame.Surface((col_w, card_h), pygame.SRCALPHA)
            bg = (245, 158, 11, 45) if team_idx == 0 else (30, 41, 59, 230)
            b_col = ACCENT_AMBER if team_idx == 0 else CARD_BORDER
            pygame.draw.rect(p_surf, bg, (0, 0, col_w, card_h), border_radius=18)
            pygame.draw.rect(p_surf, b_col, (0, 0, col_w, card_h), width=3 if team_idx == 0 else 1, border_radius=18)
            surface.blit(p_surf, (card_x, card_y))

            r_label = render_thai_text(rank_labels[pos_idx], font_size=18, color=ACCENT_AMBER if team_idx == 0 else TEXT_WHITE)
            surface.blit(r_label, r_label.get_rect(center=(card_x + col_w // 2, card_y + 24)))

            t_name = render_thai_text(team["name"], font_size=20, color=team["color"])
            surface.blit(t_name, t_name.get_rect(center=(card_x + col_w // 2, card_y + 60)))

            s_text = render_thai_text(f"{team['score']} คะแนน", font_size=22, color=ACCENT_AMBER)
            surface.blit(s_text, s_text.get_rect(center=(card_x + col_w // 2, card_y + 100)))

            tm_text = render_thai_text(f"เวลา {team['time_spent']:.1f} วินาที", font_size=16, color=(148, 163, 184))
            surface.blit(tm_text, tm_text.get_rect(center=(card_x + col_w // 2, card_y + 135)))

        # Full Leaderboard Table
        table_y = 355
        th_surf = pygame.Surface((700, 32), pygame.SRCALPHA)
        th_surf.fill((30, 41, 59, 240))
        surface.blit(th_surf, (WIDTH // 2 - 350, table_y))

        th1 = render_thai_text("อันดับ", font_size=16, color=(148, 163, 184))
        th2 = render_thai_text("ทีม", font_size=16, color=(148, 163, 184))
        th3 = render_thai_text("คะแนน", font_size=16, color=(148, 163, 184))
        th4 = render_thai_text("เวลาที่ใช้", font_size=16, color=(148, 163, 184))

        surface.blit(th1, (WIDTH // 2 - 320, table_y + 4))
        surface.blit(th2, (WIDTH // 2 - 190, table_y + 4))
        surface.blit(th3, (WIDTH // 2 + 40, table_y + 4))
        surface.blit(th4, (WIDTH // 2 + 210, table_y + 4))

        for i, team in enumerate(ranked_teams):
            row_y = table_y + 38 + i * 34
            row_surf = pygame.Surface((700, 30), pygame.SRCALPHA)
            bg = (245, 158, 11, 35) if i == 0 else (20, 30, 48, 200)
            pygame.draw.rect(row_surf, bg, (0, 0, 700, 30), border_radius=6)
            surface.blit(row_surf, (WIDTH // 2 - 350, row_y))

            r_label = f"#{i+1}" if i >= 3 else ["1st", "2nd", "3rd"][i]
            td1 = render_thai_text(r_label, font_size=16, color=TEXT_WHITE)
            td2 = render_thai_text(team["name"], font_size=16, color=team["color"])
            td3 = render_thai_text(f"{team['score']} คะแนน", font_size=16, color=ACCENT_AMBER)
            td4 = render_thai_text(f"{team['time_spent']:.1f} วินาที", font_size=16, color=(148, 163, 184))

            surface.blit(td1, (WIDTH // 2 - 320, row_y + 2))
            surface.blit(td2, (WIDTH // 2 - 190, row_y + 2))
            surface.blit(td3, (WIDTH // 2 + 40, row_y + 2))
            surface.blit(td4, (WIDTH // 2 + 210, row_y + 2))

        # Bottom Action Buttons
        btn_replay = pygame.Rect(WIDTH // 2 - 200, HEIGHT - 70, 185, 48)
        btn_menu = pygame.Rect(WIDTH // 2 + 15, HEIGHT - 70, 185, 48)

        rep_hover = btn_replay.collidepoint(mouse_pos)
        men_hover = btn_menu.collidepoint(mouse_pos)

        pygame.draw.rect(surface, ACCENT_AMBER if rep_hover else (217, 119, 6), btn_replay, border_radius=24)
        t_rep = render_thai_text("แข่งอีกครั้ง", font_size=18, color=(15, 23, 42))
        surface.blit(t_rep, t_rep.get_rect(center=btn_replay.center))

        pygame.draw.rect(surface, (30, 41, 59) if not men_hover else (51, 65, 85), btn_menu, border_radius=24)
        pygame.draw.rect(surface, CARD_BORDER, btn_menu, width=1, border_radius=24)
        t_men = render_thai_text("กลับหน้าหลัก", font_size=18, color=TEXT_WHITE)
        surface.blit(t_men, t_men.get_rect(center=btn_menu.center))

        if clicked:
            if rep_hover:
                on_replay_click()
            elif men_hover:
                on_menu_click()
