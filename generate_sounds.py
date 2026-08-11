import os
import wave
import math
import struct

SOUNDS_DIR = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets/sounds"
os.makedirs(SOUNDS_DIR, exist_ok=True)
SAMPLE_RATE = 44100

def write_wav(filename, samples):
    path = os.path.join(SOUNDS_DIR, filename)
    with wave.open(path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            val = int(max(-32767, min(32767, s * 32767.0)))
            frames.extend(struct.pack("<h", val))
        wav.writeframes(frames)
    print(f"[Sound] Generated {path} ({len(samples)} samples)")

# 1. Mechanical Tick / Wheel Peg Click
def make_tick():
    duration = 0.035
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-i / (SAMPLE_RATE * 0.006))
        freq = 1400.0 - 600.0 * (i / n)
        # Sine + Noise burst
        s = (math.sin(2 * math.pi * freq * t) * 0.7 + ((i * 1337) % 100 / 50.0 - 1.0) * 0.3) * env * 0.45
        samples.append(s)
    write_wav("tick.wav", samples)

# 2. Wheel Win Fanfare (Rising Chime)
def make_wheel_win():
    duration = 0.45
    n = int(SAMPLE_RATE * duration)
    samples = []
    chords = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
    for i in range(n):
        t = i / SAMPLE_RATE
        segment = int(t / (duration / len(chords)))
        freq = chords[min(segment, len(chords) - 1)]
        env = math.exp(-(t % (duration / len(chords))) * 12.0)
        s = math.sin(2 * math.pi * freq * t) * env * 0.4
        samples.append(s)
    write_wav("wheel_win.wav", samples)

# 3. Countdown Beep (3, 2, 1)
def make_countdown_beep():
    duration = 0.12
    n = int(SAMPLE_RATE * duration)
    samples = []
    freq = 660.0
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 18.0)
        s = math.sin(2 * math.pi * freq * t) * env * 0.5
        samples.append(s)
    write_wav("countdown_beep.wav", samples)

# 4. Countdown Go Chime (Start!)
def make_countdown_go():
    duration = 0.35
    n = int(SAMPLE_RATE * duration)
    samples = []
    freq1 = 880.0
    freq2 = 1320.0
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 8.0)
        s = (math.sin(2 * math.pi * freq1 * t) * 0.5 + math.sin(2 * math.pi * freq2 * t) * 0.5) * env * 0.45
        samples.append(s)
    write_wav("countdown_go.wav", samples)

# 5. Correct Card Match Chime (Coin / Magic Jingle)
def make_correct():
    duration = 0.5
    n = int(SAMPLE_RATE * duration)
    samples = []
    notes = [987.77, 1318.51, 1567.98, 1975.53] # B5, E6, G6, B6
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[idx]
        note_t = t - (idx * note_dur)
        env = math.exp(-note_t * 10.0)
        s = (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)) * env * 0.35
        samples.append(s)
    write_wav("correct.wav", samples)

# 6. Wrong Guess Buzzer
def make_wrong():
    duration = 0.28
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 150.0 if t < 0.14 else 120.0
        env = math.exp(-(t % 0.14) * 12.0)
        # Square wave / sawtooth buzz
        s = (1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0) * env * 0.25
        samples.append(s)
    write_wav("wrong.wav", samples)

# 7. Lock-on Trigger Blip
def make_lock():
    duration = 0.08
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 800.0 + 800.0 * (t / duration)
        env = math.exp(-t * 20.0)
        s = math.sin(2 * math.pi * freq * t) * env * 0.35
        samples.append(s)
    write_wav("lock.wav", samples)

make_tick()
make_wheel_win()
make_countdown_beep()
make_countdown_go()
make_correct()
make_wrong()
make_lock()

print("All 7 arcade game audio effects generated successfully!")
