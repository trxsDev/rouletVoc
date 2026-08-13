import time
import difflib
import threading
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from core.audio_engine import sound_engine
from config.constants import ACCENT_EMERALD, ACCENT_AMBER, ACCENT_ROSE

class SpeechVerifier:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 280
        self.recognizer.dynamic_energy_threshold = True
        
        self.is_listening = False
        self.voice_attempts = 0
        self.recognized_text = ""
        self.is_success = False
        self.feedback_msg = ""
        self.feedback_color = ACCENT_AMBER
        
        # Live Mic Audio Waveform & Equalizer Bars
        self.num_bars = 21
        self.live_bars = [0.08] * self.num_bars
        self.wave_buffer = [0.0] * 64
        self.live_volume = 0.0
        self.mic_stream = None
        self._init_mic_stream()

    def _init_mic_stream(self):
        try:
            self.mic_stream = sd.InputStream(
                channels=1,
                samplerate=16000,
                blocksize=512,
                callback=self._mic_stream_callback
            )
            self.mic_stream.start()
        except Exception as e:
            print("[Speech Verifier] Note: Live mic stream init:", e)

    def _mic_stream_callback(self, indata, frames, time_info, status):
        if status or not self.is_listening:
            # Idle smooth falloff
            for i in range(self.num_bars):
                self.live_bars[i] = max(0.06, self.live_bars[i] * 0.90)
            self.live_volume = max(0.0, self.live_volume * 0.90)
            return

        data = indata[:, 0]
        # RMS volume
        rms = float(np.sqrt(np.mean(data**2)))
        self.live_volume = self.live_volume * 0.4 + rms * 0.6
        
        # Raw waveform points for oscilloscope
        step = max(1, len(data) // 64)
        self.wave_buffer = [float(x) for x in data[::step][:64]]
        
        # Compute 21 equalizer bars with peak amplitude
        chunk_size = max(1, len(data) // self.num_bars)
        for i in range(self.num_bars):
            chunk = data[i * chunk_size : (i + 1) * chunk_size]
            if len(chunk) > 0:
                raw_amp = float(np.max(np.abs(chunk))) * 4.2
                amp = max(0.08, min(1.0, raw_amp))
                self.live_bars[i] = self.live_bars[i] * 0.45 + amp * 0.55

    def get_live_audio_data(self):
        return {
            "bars": list(self.live_bars),
            "waveform": list(self.wave_buffer),
            "volume": self.live_volume
        }

    def reset(self, target_item):
        self.is_listening = True
        self.voice_attempts = 0
        self.recognized_text = ""
        self.is_success = False
        self.feedback_msg = f"กรุณาออกเสียง: '{target_item['en'].upper()}' ({target_item['word']})"
        self.feedback_color = ACCENT_AMBER

    def start_listening(self, target_item, on_success_cb, on_retry_cb, on_finish_cb):
        threading.Thread(
            target=self._listen_worker,
            args=(target_item, on_success_cb, on_retry_cb, on_finish_cb),
            daemon=True
        ).start()

    def _listen_worker(self, target_item, on_success_cb, on_retry_cb, on_finish_cb):
        # Stop sounddevice live stream to prevent PyAudio lock contention on Windows
        if self.mic_stream:
            try:
                self.mic_stream.stop()
            except Exception as e:
                print("[Speech Verifier] Error stopping live mic stream:", e)

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                if self.recognizer.energy_threshold > 300:
                    self.recognizer.energy_threshold = 300
                audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=4.0)
                
                text = ""
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                except Exception:
                    pass
                
                if not text:
                    try:
                        text = self.recognizer.recognize_google(audio, language="th-TH")
                    except Exception:
                        text = ""
                        
                self.recognized_text = text
                target_en = target_item["en"].lower()
                aliases = [a.lower().strip() for a in target_item.get("aliases", [target_en])]
                
                def check_match(raw_text):
                    cleaned = raw_text.lower().strip()
                    if not cleaned:
                        return False
                    for t in aliases:
                        if t in cleaned or cleaned in t:
                            return True
                        if difflib.SequenceMatcher(None, t, cleaned).ratio() >= 0.50:
                            return True
                        for w in cleaned.split():
                            if difflib.SequenceMatcher(None, t, w).ratio() >= 0.50:
                                return True
                    return False

                is_correct = check_match(text)
                
                # Dual-pass: If en-US didn't match, test th-TH for Thai-accented phonetic transcription
                if not is_correct and audio:
                    try:
                        thai_text = self.recognizer.recognize_google(audio, language="th-TH")
                        if check_match(thai_text):
                            text = thai_text
                            self.recognized_text = text
                            is_correct = True
                    except Exception:
                        pass
                
                if is_correct:
                    self.is_success = True
                    sound_engine.play("correct")
                    self.feedback_msg = f"ออกเสียงถูกต้อง! '{text}' (+100 คะแนน)"
                    self.feedback_color = ACCENT_EMERALD
                    on_success_cb(text)
                    time.sleep(1.4)
                    on_finish_cb()
                else:
                    self.voice_attempts += 1
                    sound_engine.play("wrong")
                    if self.voice_attempts >= 2:
                        self.feedback_msg = f"ได้ยิน: '{text}' (หมดโควต้าฟังเสียง ข้ามไปรอบถัดไป)"
                        self.feedback_color = ACCENT_ROSE
                        time.sleep(1.6)
                        on_finish_cb()
                    else:
                        self.feedback_msg = f"ได้ยิน: '{text}' (ยังไม่ถูกต้อง ลองออกเสียงใหม่อีกครั้ง!)"
                        self.feedback_color = ACCENT_AMBER
                        time.sleep(0.8)
                        on_retry_cb()
        except sr.WaitTimeoutError:
            self.voice_attempts += 1
            if self.voice_attempts >= 2:
                self.feedback_msg = "หมดเวลาฟังเสียง! ข้ามไปรอบถัดไป"
                self.feedback_color = ACCENT_ROSE
                time.sleep(1.4)
                on_finish_cb()
            else:
                self.feedback_msg = "ไม่ได้ยินเสียง ลองพูดใหม่อีกครั้ง..."
                self.feedback_color = ACCENT_AMBER
                on_retry_cb()
        except Exception as e:
            print("[Speech Verifier] Recognition error:", e)
            self.feedback_msg = "ข้ามการตรวจจับเสียงไปยังรอบถัดไป"
            self.feedback_color = ACCENT_AMBER
            time.sleep(1.0)
            on_finish_cb()
        finally:
            self.is_listening = False
            # Restart sounddevice live stream
            if self.mic_stream:
                try:
                    self.mic_stream.start()
                except Exception as e:
                    print("[Speech Verifier] Error restarting live mic stream:", e)
