import os
import sys
import unittest
import pygame

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.display_manager import DisplayManager

class TestDisplayManager(unittest.TestCase):
    def setUp(self):
        self.dm = DisplayManager(virtual_w=1080, virtual_h=720)

    def test_probe_and_config(self):
        cfg = self.dm.probe_hardware_display()
        self.assertIn("screen_width", cfg)
        self.assertIn("screen_height", cfg)
        self.assertIn("scale_factor", cfg)
        self.assertIn("safe_margin_x", cfg)
        self.assertIn("safe_margin_y", cfg)
        self.assertGreater(cfg["screen_width"], 0)
        self.assertGreater(cfg["screen_height"], 0)

    def test_screen_to_virtual_coords(self):
        # Suppose viewport is centered 1080x720 (scale=1, offset=0,0)
        self.dm.viewport_rect = pygame.Rect(0, 0, 1080, 720)
        self.dm.scale_factor = 1.0
        vx, vy = self.dm.screen_to_virtual_coords((540, 360))
        self.assertEqual((vx, vy), (540, 360))

        # Suppose 1920x1080 screen with 1.5x scale (1620x1080 viewport, offset_x=150)
        self.dm.viewport_rect = pygame.Rect(150, 0, 1620, 1080)
        self.dm.scale_factor = 1.5
        vx, vy = self.dm.screen_to_virtual_coords((150, 0))
        self.assertEqual((vx, vy), (0, 0))
        vx, vy = self.dm.screen_to_virtual_coords((150 + 810, 540))
        self.assertEqual((vx, vy), (540, 360))

    def test_render_virtual_to_screen(self):
        pygame.init()
        virt = pygame.Surface((1080, 720))
        virt.fill((255, 0, 0))
        disp = pygame.Surface((1920, 1080))
        self.dm.viewport_rect = pygame.Rect(150, 0, 1620, 1080)
        self.dm.render_virtual_to_screen(virt, disp)
        self.assertEqual(disp.get_size(), (1920, 1080))

if __name__ == "__main__":
    unittest.main()
