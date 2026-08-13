import os
import sys
import pygame
import time

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Full pygame initialization resolves dependency circular imports
pygame.init()
screen = pygame.display.set_mode((1080, 720))

import unittest
from unittest.mock import MagicMock

# Mock speech verifier's sounddevice to prevent actual soundcard usage
from core.speech_verifier import SpeechVerifier
SpeechVerifier._init_mic_stream = MagicMock()

from states.game import GestureMemoryGame

class TestGameTransitions(unittest.TestCase):
    def setUp(self):
        self.game = GestureMemoryGame()
        self.game.tracking_engine.cap = MagicMock()
        self.game.tracking_engine.detector = MagicMock()
        
    def test_state_transitions(self):
        # 1. SETUP_CAMERA
        self.assertEqual(self.game.state, "SETUP_CAMERA")
        self.game.update()
        self.game.draw(screen)

        # Transition to SETUP_WIFI
        self.game.state = "SETUP_WIFI"
        self.game.update()
        self.game.draw(screen)
        
        # Transition to LANDING_MENU
        self.game.state = "LANDING_MENU"
        self.game.update()
        self.game.draw(screen)

        # Test starting freedom mode
        self.game.start_freedom_mode()
        self.assertEqual(self.game.state, "ROULETTE")
        
        # Let's run a few frames of ROULETTE update
        for _ in range(5):
            self.game.update()
            self.game.draw(screen)
            
        # Simulate roulette ending and moving to ANNOUNCE
        self.game.wheel.is_spinning = False
        self.game.state = "ANNOUNCE"
        self.game.state_timer = time.time() - 3.0
        self.game.update()
        self.assertEqual(self.game.state, "TARGET_FOCUS_READ")
        
        # Run TARGET_FOCUS_READ
        self.game.state_timer = time.time() - 6.0
        self.game.update()
        self.assertEqual(self.game.state, "MEMORIZE")
        
        # Run MEMORIZE
        self.game.state_timer = time.time() - 4.0
        self.game.update()
        self.assertEqual(self.game.state, "COUNTDOWN")
        
        # Run COUNTDOWN
        self.game.state_timer = time.time() - 4.0
        self.game.update()
        self.assertEqual(self.game.state, "PLAY")
        
        # Verify card selection and guessing in PLAY mode
        self.assertGreater(len(self.game.cards), 0)
        target_card = next(c for c in self.game.cards if c.item["id"] == self.game.target_item["id"])
        self.game.handle_card_guess(target_card)
        
        # Verify VOICE_VERIFY trigger
        self.assertEqual(self.game.state, "VOICE_VERIFY")
        
        # Test team setup configurations
        self.game.state = "TEAM_SETUP"
        self.game.update()
        self.game.draw(screen)
        
        # Test team tournament start
        self.game.start_team_tournament()
        self.assertEqual(self.game.state, "TEAM_READY")
        self.game.update()
        self.game.draw(screen)

        print("[Test] All state transitions completed without exceptions!")

if __name__ == "__main__":
    unittest.main()
