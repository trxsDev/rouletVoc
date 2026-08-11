import os
import subprocess

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

ITEMS = [
    "backpack", "book", "chair", "clock", "eraser", "fan",
    "notebook", "pen", "pencil", "ruler", "table", "window"
]

print("[TTS Audio Engine] Generating studio-grade English pronunciation audio...")
for word in ITEMS:
    target_wav = os.path.join(AUDIO_DIR, f"{word}.wav")
    temp_aiff = os.path.join(AUDIO_DIR, f"{word}.aiff")
    try:
        subprocess.run(["say", "-v", "Samantha", word, "-o", temp_aiff], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", temp_aiff, target_wav], check=True)
        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)
        print(f"Generated: {word}.wav")
    except Exception as e:
        print(f"Error generating {word}: {e}")

print("[TTS Audio Engine] All 12 vocabulary audio files generated successfully!")
