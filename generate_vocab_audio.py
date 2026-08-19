import os
import subprocess

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

ITEMS = [
    "bag", "book", "chair", "clock", "eraser", "fan",
    "notebook", "pen", "pencil", "ruler", "table", "window"
]

print("[TTS Audio Engine] Generating child-friendly slow & clear English pronunciation (115 wpm)...")
for word in ITEMS:
    target_wav = os.path.join(AUDIO_DIR, f"{word}.wav")
    temp_aiff = os.path.join(AUDIO_DIR, f"{word}.aiff")
    try:
        # Rate: 115 words per minute for clear child articulation
        subprocess.run(["say", "-r", "115", "-v", "Samantha", word, "-o", temp_aiff], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", temp_aiff, target_wav], check=True)
        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)
        print(f"Generated slow & clear audio: {word}.wav")
    except Exception as e:
        print(f"Error generating {word}: {e}")

print("[TTS Audio Engine] All 12 child-friendly audio files generated successfully!")
