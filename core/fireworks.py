import pygame
import math
import random
import time

FIREWORK_COLORS = [
    (245, 158, 11),  # Amber/Gold
    (6, 182, 212),   # Cyan
    (244, 63, 94),   # Rose / Crimson
    (16, 185, 129),  # Emerald
    (168, 85, 247),  # Purple
    (251, 146, 60),  # Orange
    (255, 255, 255)  # Sparkle White
]

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.5, 9.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.alpha = 255
        self.decay = random.uniform(3.0, 5.5)
        self.radius = random.uniform(2.5, 4.5)
        self.gravity = 0.14
        self.friction = 0.96

    def update(self):
        self.vx *= self.friction
        self.vy = (self.vy * self.friction) + self.gravity
        self.x += self.vx
        self.y += self.vy
        self.alpha = max(0, self.alpha - self.decay)
        self.radius = max(0.5, self.radius - 0.04)

    def is_alive(self):
        return self.alpha > 0 and self.radius > 0.5

class FireworkRocket:
    def __init__(self, x, target_y):
        self.x = x
        self.y = 720
        self.target_y = target_y
        self.vy = -random.uniform(9.0, 13.0)
        self.color = random.choice(FIREWORK_COLORS)
        self.exploded = False

    def update(self):
        self.y += self.vy
        self.vy += 0.08  # slight deceleration
        if self.y <= self.target_y or self.vy >= -1.0:
            self.exploded = True

class FireworksEngine:
    def __init__(self, width=1080, height=720):
        self.width = width
        self.height = height
        self.rockets = []
        self.particles = []
        self.last_launch_time = time.time()
        self.launch_interval = 0.35

    def trigger_burst(self, x=None, y=None, count=75):
        cx = x if x is not None else random.randint(150, self.width - 150)
        cy = y if y is not None else random.randint(100, self.height - 280)
        color = random.choice(FIREWORK_COLORS)
        for _ in range(count):
            self.particles.append(Particle(cx, cy, color))

    def update(self):
        now = time.time()
        # Automatic ongoing festive burst launches
        if now - self.last_launch_time >= self.launch_interval:
            self.last_launch_time = now
            rx = random.randint(180, self.width - 180)
            ty = random.randint(110, self.height - 300)
            self.rockets.append(FireworkRocket(rx, ty))
            self.launch_interval = random.uniform(0.25, 0.55)

        # Update rockets
        for r in self.rockets[:]:
            r.update()
            if r.exploded:
                self.trigger_burst(r.x, r.y, count=random.randint(60, 95))
                self.rockets.remove(r)

        # Update particles
        for p in self.particles[:]:
            p.update()
            if not p.is_alive():
                self.particles.remove(p)

    def draw(self, surface):
        # Draw rockets trail
        for r in self.rockets:
            pygame.draw.circle(surface, (255, 255, 255), (int(r.x), int(r.y)), 3)
            pygame.draw.line(surface, r.color, (int(r.x), int(r.y)), (int(r.x), int(r.y + 12)), 2)

        # Draw particles with alpha glow
        for p in self.particles:
            color_with_alpha = (p.color[0], p.color[1], p.color[2], int(p.alpha))
            p_surf = pygame.Surface((int(p.radius * 4), int(p.radius * 4)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, color_with_alpha, (int(p.radius * 2), int(p.radius * 2)), int(p.radius))
            surface.blit(p_surf, (int(p.x - p.radius * 2), int(p.y - p.radius * 2)))

    def clear(self):
        self.rockets.clear()
        self.particles.clear()
