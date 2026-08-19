import pygame
import math
import random
from config.items import GESTURE_MODES
from core.audio_engine import sound_engine
from ui.renderer import get_image

class RouletteWheel:
    def __init__(self, cx, cy, radius=320):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = 0.0
        self.speed = 0.0
        self.deceleration = 0.0
        self.is_spinning = False
        self.target_final_angle = 0.0
        self.target_idx = 0
        
        self.num_wedges = len(GESTURE_MODES) # 4
        self.wedge_angle_span = 360.0 / self.num_wedges
        
        self.needle_deflection = 0.0
        self.last_passed_wedge = -1
        self.light_timer = 0
        
        self.base_wheel_surf = get_image("roulette_wheel.png", target_size=(self.radius * 2, self.radius * 2))
        self.pointer_surf = get_image("wheel_pointer.png", target_size=(96, 150))

    def spin_to_target(self, target_idx):
        self.is_spinning = True
        self.target_idx = target_idx
        target_wedge_center = target_idx * self.wedge_angle_span + (self.wedge_angle_span / 2.0)
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
        if self.is_spinning:
            self.angle += self.speed
            self.speed = max(0.0, self.speed - self.deceleration)
            
            pointer_wheel_angle = (270.0 - self.angle) % 360.0
            current_wedge = int(pointer_wheel_angle // self.wedge_angle_span) % self.num_wedges
            
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
        self.light_timer += 1

    def get_current_selected_gesture(self):
        if not self.is_spinning and 0 <= self.target_idx < self.num_wedges:
            return GESTURE_MODES[self.target_idx]
            
        pointer_wheel_angle = (270.0 - self.angle) % 360.0
        idx = int(pointer_wheel_angle // self.wedge_angle_span) % self.num_wedges
        return GESTURE_MODES[idx]

    def draw(self, surface):
        rotated_wheel = pygame.transform.rotozoom(self.base_wheel_surf, -self.angle, 1.0)
        wheel_rect = rotated_wheel.get_rect(center=(self.cx, self.cy))
        surface.blit(rotated_wheel, wheel_rect)
        
        # Center gold hub
        pygame.draw.circle(surface, (245, 158, 11), (self.cx, self.cy), 32)
        pygame.draw.circle(surface, (254, 240, 138), (self.cx, self.cy), 16)
        pygame.draw.circle(surface, (15, 23, 42), (self.cx, self.cy), 32, width=4)
        
        # Top pointer with deflection
        pointer_top_y = self.cy - self.radius - 46
        rotated_pointer = pygame.transform.rotozoom(self.pointer_surf, self.needle_deflection, 1.0)
        p_rect = rotated_pointer.get_rect(midtop=(self.cx, pointer_top_y))
        surface.blit(rotated_pointer, p_rect)
