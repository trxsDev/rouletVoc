import time
import difflib
import threading
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

    def reset(self, target_item):
        self.is_listening = True
        self.voice_attempts = 0
        self.recognized_text = ""
        self.is_success = False
        self.feedback_msg = f"🎙️ กรุณาออกเสียง: '{target_item['en'].upper()}' ({target_item['word']})"
        self.feedback_color = ACCENT_AMBER

    def start_listening(self, target_item, on_success_cb, on_retry_cb, on_finish_cb):
        threading.Thread(
            target=self._listen_worker,
            args=(target_item, on_success_cb, on_retry_cb, on_finish_cb),
            daemon=True
        ).start()

    def _listen_worker(self, target_item, on_success_cb, on_retry_cb, on_finish_cb):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                if self.recognizer.energy_threshold > 300:
                    self.recognizer.energy_threshold = 300
                audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=4.0)
                
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                except Exception:
                    try:
                        text = self.recognizer.recognize_google(audio, language="th-TH")
                    except Exception:
                        text = ""
                        
                self.recognized_text = text
                target_en = target_item["en"].lower()
                aliases = target_item.get("aliases", [target_en])
                
                is_correct = any(
                    (t in text.lower()) or 
                    (difflib.SequenceMatcher(None, t, text.lower()).ratio() >= 0.55)
                    for t in aliases
                )
                
                if is_correct:
                    self.is_success = True
                    sound_engine.play("correct")
                    self.feedback_msg = f"🎉 ออกเสียงถูกต้อง! '{text}' (+100 คะแนน)"
                    self.feedback_color = ACCENT_EMERALD
                    on_success_cb(text)
                    time.sleep(1.4)
                    on_finish_cb()
                else:
                    self.voice_attempts += 1
                    sound_engine.play("wrong")
                    if self.voice_attempts >= 2:
                        self.feedback_msg = f"⚠️ ได้ยิน: '{text}' (หมดโควต้าฟังเสียง ข้ามไปรอบถัดไป)"
                        self.feedback_color = ACCENT_ROSE
                        time.sleep(1.6)
                        on_finish_cb()
                    else:
                        self.feedback_msg = f"⚠️ ได้ยิน: '{text}' (ยังไม่ถูกต้อง ลองออกเสียงใหม่อีกครั้ง!)"
                        self.feedback_color = ACCENT_AMBER
                        time.sleep(0.8)
                        on_retry_cb()
        except sr.WaitTimeoutError:
            self.voice_attempts += 1
            if self.voice_attempts >= 2:
                self.feedback_msg = "⏱️ หมดเวลาฟังเสียง! ข้ามไปรอบถัดไป"
                self.feedback_color = ACCENT_ROSE
                time.sleep(1.4)
                on_finish_cb()
            else:
                self.feedback_msg = "⏱️ ไม่ได้ยินเสียง ลองพูดใหม่อีกครั้ง..."
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
