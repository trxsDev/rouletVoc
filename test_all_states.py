import os
import sys
import pygame
import time

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Full pygame initialization resolves dependency circular imports
pygame.init()
screen = pygame.display.set_mode((1920, 1080))

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

        # ----------------------------------------------------
        # Test Review Mode (Freedom & Flashcard)
        # ----------------------------------------------------
        # 1. Review Mode Select
        self.game.start_review_mode_select()
        self.assertEqual(self.game.state, "REVIEW_MODE_SELECT")
        self.game.update()
        self.game.draw(screen)

        # 2. Start Freedom Review
        self.game.start_review_submode("FREEDOM")
        self.assertEqual(self.game.state, "REVIEW_WHEEL")
        self.assertEqual(len(self.game.review_deck), 12)
        self.game.update()
        self.game.draw(screen)

        # 3. Spin Review Wheel
        self.game.spin_review_wheel()
        self.assertTrue(self.game.review_wheel.is_spinning)
        self.assertIsNotNone(self.game.review_target_item)
        
        # Simulate Wheel Stop
        self.game.review_wheel.is_spinning = False
        self.game.state_timer = time.time() - 3.0
        self.game.update()
        self.assertEqual(self.game.state, "REVIEW_RESULT")
        self.game.draw(screen)

        # 4. Start Flashcard Review
        self.game.start_review_submode("FLASHCARD")
        self.assertEqual(self.game.state, "REVIEW_WHEEL")
        self.assertEqual(len(self.game.review_deck), 12)

        # Spin and transition to REVIEW_RESULT
        self.game.spin_review_wheel()
        self.game.review_wheel.is_spinning = False
        self.game.state_timer = time.time() - 3.0
        self.game.update()
        self.assertEqual(self.game.state, "REVIEW_RESULT")
        self.game.draw(screen)

        # Simulate user advancing to next word (deck decrements on advance)
        if self.game.review_target_item in self.game.review_deck:
            self.game.review_deck.remove(self.game.review_target_item)
            self.game.review_completed_items.append(self.game.review_target_item)
        self.assertEqual(len(self.game.review_deck), 11)
        self.assertEqual(len(self.game.review_completed_items), 1)

        # Simulate Flashcard complete -> Congrats stage with Fireworks
        self.game.review_deck = []
        self.game.review_completed_items = list(self.game.review_completed_items)
        self.game.state = "REVIEW_CONGRATS"
        self.game.fireworks.trigger_burst()
        self.game.update()
        self.game.draw(screen)
        self.assertGreater(len(self.game.fireworks.particles), 0)

        print("[Test] All state transitions and Review mode tests completed without exceptions!")

if __name__ == "__main__":
    unittest.main()
