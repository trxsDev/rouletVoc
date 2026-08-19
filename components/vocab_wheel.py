import pygame
import math
import random
from core.audio_engine import sound_engine
from ui.renderer import get_image, render_thai_text

WEDGE_PALETTES = [
    {"bg": (30, 58, 138), "border": (96, 165, 250), "text": (255, 255, 255)},   # Blue
    {"bg": (120, 53, 15), "border": (251, 191, 36), "text": (255, 255, 255)},   # Amber
    {"bg": (6, 78, 59), "border": (52, 211, 153), "text": (255, 255, 255)},    # Emerald
    {"bg": (136, 19, 55), "border": (251, 113, 133), "text": (255, 255, 255)}, # Rose
    {"bg": (88, 28, 135), "border": (192, 132, 252), "text": (255, 255, 255)}, # Purple
    {"bg": (14, 116, 144), "border": (34, 211, 238), "text": (255, 255, 255)}, # Cyan
    {"bg": (124, 45, 18), "border": (251, 146, 60), "text": (255, 255, 255)},  # Orange
    {"bg": (15, 23, 42), "border": (148, 163, 184), "text": (255, 255, 255)},  # Slate
]

class VocabWheel:
    def __init__(self, cx, cy, radius=380, items=None):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.items = items if items else []
        self.angle = 0.0
        self.speed = 0.0
        self.deceleration = 0.0
        self.is_spinning = False
        self.target_final_angle = 0.0
        self.target_idx = -1
        
        self.needle_deflection = 0.0
        self.last_passed_wedge = -1
        
        self.pointer_surf = get_image("wheel_pointer.png", target_size=(96, 150))
        self.cached_wheel_surf = None
        self.rebuild_wheel_surface()

    def set_items(self, items):
        self.items = list(items) if items else []
        self.rebuild_wheel_surface()

    def rebuild_wheel_surface(self):
        n = max(1, len(self.items))
        d = self.radius * 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        center = (self.radius, self.radius)
        wedge_angle = 360.0 / n

        # Draw wedges
        for i in range(n):
            item = self.items[i] if i < len(self.items) else {"word": "คำศัพท์", "en": "Word", "filename": "book.png"}
            pal = WEDGE_PALETTES[i % len(WEDGE_PALETTES)]
            
            start_ang = math.radians(i * wedge_angle)
            end_ang = math.radians((i + 1) * wedge_angle)
            
            # Approximate arc using polygon fan
            points = [center]
            num_steps = max(10, int(wedge_angle / 3))
            for s in range(num_steps + 1):
                ang = start_ang + (end_ang - start_ang) * (s / num_steps)
                px = center[0] + (self.radius - 8) * math.cos(ang)
                py = center[1] + (self.radius - 8) * math.sin(ang)
                points.append((px, py))
                
            pygame.draw.polygon(surf, pal["bg"], points)
            pygame.draw.polygon(surf, pal["border"], points, width=3)
            
            # Mid-angle for item icon & text
            mid_ang = (start_ang + end_ang) / 2.0
            mid_deg = math.degrees(mid_ang)
            
            # 1. High-Contrast White Circular Pod for Icon
            icon_dist = self.radius * 0.58
            ix = int(center[0] + icon_dist * math.cos(mid_ang))
            iy = int(center[1] + icon_dist * math.sin(mid_ang))
            
            pod_r = 46 if n > 8 else (54 if n > 4 else 62)
            # Pod drop shadow & solid white fill
            pygame.draw.circle(surf, (15, 23, 42, 160), (ix + 2, iy + 2), pod_r + 3)
            pygame.draw.circle(surf, (255, 255, 255), (ix, iy), pod_r)
            pygame.draw.circle(surf, (254, 240, 138), (ix, iy), pod_r, width=3)
            
            # Draw Item icon (Enlarged and crisp)
            icon_size = (78, 78) if n > 8 else (92, 92)
            icon_img = get_image(item.get("filename", "book.png"), target_size=icon_size)
            rot_icon = pygame.transform.rotozoom(icon_img, -mid_deg + 90, 1.0)
            surf.blit(rot_icon, rot_icon.get_rect(center=(ix, iy)))
            
            # 2. Thai / English label near outer rim
            text_dist = self.radius * 0.86
            tx = center[0] + text_dist * math.cos(mid_ang)
            ty = center[1] + text_dist * math.sin(mid_ang)
            
            f_size = 22 if n > 8 else (26 if n > 4 else 30)
            t_surf = render_thai_text(item["word"], font_size=f_size, color=pal["text"])
            rot_text = pygame.transform.rotozoom(t_surf, -mid_deg + 90, 1.0)
            surf.blit(rot_text, rot_text.get_rect(center=(tx, ty)))

        # Golden Spoke Lines
        for i in range(n):
            spoke_ang = math.radians(i * wedge_angle)
            sx = int(center[0] + (self.radius - 8) * math.cos(spoke_ang))
            sy = int(center[1] + (self.radius - 8) * math.sin(spoke_ang))
            pygame.draw.line(surf, (254, 240, 138), center, (sx, sy), 4)

        # Outer glowing golden metallic rim with LEDs
        pygame.draw.circle(surf, (217, 119, 6), center, self.radius - 4, width=16)
        pygame.draw.circle(surf, (254, 240, 138), center, self.radius - 8, width=4)
        pygame.draw.circle(surf, (15, 23, 42), center, self.radius - 14, width=3)
        
        # Rim LED Bulbs
        num_leds = max(16, n * 2)
        for i in range(num_leds):
            led_ang = math.radians(i * (360.0 / num_leds))
            lx = int(center[0] + (self.radius - 12) * math.cos(led_ang))
            ly = int(center[1] + (self.radius - 12) * math.sin(led_ang))
            pygame.draw.circle(surf, (254, 240, 138), (lx, ly), 5)
            pygame.draw.circle(surf, (255, 255, 255), (lx, ly), 2)
        
        self.cached_wheel_surf = surf

    def spin_to_target(self, target_idx):
        if not self.items:
            return
        self.is_spinning = True
        self.target_idx = target_idx
        n = len(self.items)
        wedge_angle = 360.0 / n
        target_wedge_center = target_idx * wedge_angle + (wedge_angle / 2.0)
        self.target_final_angle = (270.0 - target_wedge_center) % 360.0
        
        extra_rotations = random.randint(4, 6) * 360.0
        current_mod = self.angle % 360.0
        angle_diff = (self.target_final_angle - current_mod) % 360.0
        if angle_diff < 120.0:
            angle_diff += 360.0
            
        total_distance = extra_rotations + angle_diff
        self.speed = math.sqrt(2 * 0.28 * total_distance)
        self.deceleration = (self.speed ** 2) / (2 * total_distance)

    def update(self):
        if self.is_spinning and self.items:
            self.angle += self.speed
            self.speed = max(0.0, self.speed - self.deceleration)
            
            n = len(self.items)
            wedge_angle = 360.0 / n
            pointer_wheel_angle = (270.0 - self.angle) % 360.0
            current_wedge = int(pointer_wheel_angle // wedge_angle) % n
            
            if current_wedge != self.last_passed_wedge:
                self.needle_deflection = -20.0
                self.last_passed_wedge = current_wedge
                sound_engine.play("tick")
                
            if self.speed <= 0.01:
                self.speed = 0.0
                self.angle = self.target_final_angle
                self.is_spinning = False
                sound_engine.play("wheel_win")
                
        self.needle_deflection += (0.0 - self.needle_deflection) * 0.25

    def get_current_selected_item(self):
        if not self.items:
            return None
        if not self.is_spinning and self.target_idx >= 0 and self.target_idx < len(self.items):
            return self.items[self.target_idx]
            
        n = len(self.items)
        wedge_angle = 360.0 / n
        pointer_wheel_angle = (270.0 - self.angle) % 360.0
        idx = int(pointer_wheel_angle // wedge_angle) % n
        return self.items[idx]

    def draw(self, surface):
        if not self.cached_wheel_surf:
            self.rebuild_wheel_surface()

        rotated_wheel = pygame.transform.rotozoom(self.cached_wheel_surf, -self.angle, 1.0)
        wheel_rect = rotated_wheel.get_rect(center=(self.cx, self.cy))
        surface.blit(rotated_wheel, wheel_rect)
        
        # Center gold hub
        pygame.draw.circle(surface, (245, 158, 11), (self.cx, self.cy), 42)
        pygame.draw.circle(surface, (254, 240, 138), (self.cx, self.cy), 22)
        pygame.draw.circle(surface, (15, 23, 42), (self.cx, self.cy), 42, width=4)
        
        # Top pointer with deflection
        pointer_top_y = self.cy - self.radius - 52
        rotated_pointer = pygame.transform.rotozoom(self.pointer_surf, self.needle_deflection, 1.0)
        p_rect = rotated_pointer.get_rect(midtop=(self.cx, pointer_top_y))
        surface.blit(rotated_pointer, p_rect)
