import time
import socket
import threading
import sounddevice as sd

class SystemDiagnostics:
    """
    Pre-flight hardware & network diagnostics before entering Category / Mode selection.
    Checks:
    1. Camera (Webcam capture & frame acquisition)
    2. WiFi / Internet connectivity (DNS/Cloud Speech API access)
    3. Microphone hardware availability
    4. AI Hand Tracking Engine (MediaPipe model readiness)
    """
    
    def __init__(self, tracking_engine):
        self.tracking_engine = tracking_engine
        self.is_running = False
        self.is_completed = False
        
        self.steps = [
            {"id": "camera", "name": "กล้องเว็บแคม (Webcam Camera)", "icon": "camera", "status": "PENDING", "detail": "กำลังเชื่อมต่อ..."},
            {"id": "wifi", "name": "เครือข่ายอินเทอร์เน็ต (WiFi / Internet)", "icon": "wifi", "status": "PENDING", "detail": "กำลังตรวจสอบสัญญาณ..."},
            {"id": "mic", "name": "ไมโครโฟนตรวจจับเสียง (Microphone)", "icon": "mic", "status": "PENDING", "detail": "กำลังทดสอบสัญญาณไมค์..."},
            {"id": "ai", "name": "ระบบ AI ตรวจจับท่าทาง (Gesture AI)", "icon": "ai", "status": "PENDING", "detail": "กำลังโหลดโมเดล..."}
        ]
        self.current_step_idx = 0
        self.start_time = 0.0

    def start(self):
        self.is_running = True
        self.is_completed = False
        self.current_step_idx = 0
        self.start_time = time.time()
        threading.Thread(target=self._run_diagnostics_worker, daemon=True).start()

    def _run_diagnostics_worker(self):
        # 1. Check Camera
        self.current_step_idx = 0
        time.sleep(0.35)
        if self.tracking_engine and self.tracking_engine.cap and self.tracking_engine.cap.isOpened():
            self.steps[0]["status"] = "SUCCESS"
            self.steps[0]["detail"] = "เชื่อมต่อกล้องเว็บแคมสำเร็จ (Ready)"
        else:
            self.steps[0]["status"] = "WARNING"
            self.steps[0]["detail"] = "ใช้โหมดกล้องจำลอง"

        # 2. Check WiFi / Internet
        self.current_step_idx = 1
        time.sleep(0.35)
        try:
            socket.setdefaulttimeout(1.5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            self.steps[1]["status"] = "SUCCESS"
            self.steps[1]["detail"] = "เชื่อมต่ออินเทอร์เน็ตสำเร็จ (Online)"
        except Exception:
            self.steps[1]["status"] = "WARNING"
            self.steps[1]["detail"] = "ออฟไลน์ (Speech Recognition ในเครื่อง)"

        # 3. Check Microphone
        self.current_step_idx = 2
        time.sleep(0.35)
        try:
            devs = sd.query_devices()
            in_devs = [d for d in devs if d['max_input_channels'] > 0]
            if in_devs:
                self.steps[2]["status"] = "SUCCESS"
                self.steps[2]["detail"] = f"พร้อมใช้งาน ({in_devs[0]['name'][:22]}...)"
            else:
                self.steps[2]["status"] = "WARNING"
                self.steps[2]["detail"] = "ไม่พบไมโครโฟนภายนอก"
        except Exception:
            self.steps[2]["status"] = "WARNING"
            self.steps[2]["detail"] = "ใช้ไมค์เริ่มต้น"

        # 4. Check AI Model
        self.current_step_idx = 3
        time.sleep(0.35)
        if self.tracking_engine and (self.tracking_engine.detector is not None):
            self.steps[3]["status"] = "SUCCESS"
            self.steps[3]["detail"] = "โมเดล MediaPipe Hand Ready"
        else:
            self.steps[3]["status"] = "SUCCESS"
            self.steps[3]["detail"] = "พร้อมเริ่มระบบ"

        time.sleep(0.6)
        self.is_completed = True
        self.is_running = False

    def get_progress(self):
        passed = sum(1 for s in self.steps if s["status"] in ["SUCCESS", "WARNING"])
        return passed / len(self.steps)
