import os
import time
import subprocess
import threading
from config.constants import SOUNDS_DIR, AUDIO_DIR

class SoundEngine:
    def __init__(self):
        self.last_played = {}
        self.min_intervals = {
            "tick": 0.04,
            "countdown_beep": 0.3,
            "countdown_go": 0.5,
            "wheel_win": 0.5,
            "correct": 0.3,
            "wrong": 0.3,
            "lock": 0.2,
            "ok_ready": 0.5,
            "ready_ping": 0.09,
            "podium_fanfare": 1.0
        }

    def play(self, sound_name):
        now = time.time()
        min_int = self.min_intervals.get(sound_name, 0.05)
        if now - self.last_played.get(sound_name, 0.0) < min_int:
            return
        self.last_played[sound_name] = now
        
        file_path = os.path.join(SOUNDS_DIR, f"{sound_name}.wav")
        if os.path.exists(file_path):
            threading.Thread(
                target=lambda: subprocess.run(["afplay", file_path], capture_output=True),
                daemon=True
            ).start()

    def play_vocab(self, word_id):
        """Plays studio-quality English pronunciation of the target word."""
        for ext in [".wav", ".mp3"]:
            filepath = os.path.join(AUDIO_DIR, f"{word_id}{ext}")
            if os.path.exists(filepath):
                threading.Thread(
                    target=lambda: subprocess.run(["afplay", filepath], capture_output=True),
                    daemon=True
                ).start()
                return

sound_engine = SoundEngine()
