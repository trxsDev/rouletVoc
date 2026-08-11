import os
import cv2
import time
import math
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from config.constants import MODEL_PATH, MODEL_URL, WIDTH, HEIGHT
from core.gesture_classifier import GestureClassifier

class HandTrackingEngine:
    def __init__(self):
        self.detector = None
        self.cap = None
        self._last_timestamp_ms = -1
        
        # Active Player Hand Lock-On Engine
        self.locked_hand_pos = None
        self.locked_palm_size = 0.0
        self.last_player_seen_time = 0.0
        
        # Cursor & Result Cache
        self.cursor_pos = [-1000, -1000]
        self.hand_landmarks_screen = []
        self.current_detected_gesture = "NONE"
        self.is_pinched = False
        self.pinch_dist = 999.0
        
        self.setup_detector()
        self.setup_camera()

    def setup_detector(self):
        if not os.path.exists(MODEL_PATH):
            print(f"[Tracking Engine] Downloading MediaPipe model from {MODEL_URL}...")
            try:
                urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
                print("[Tracking Engine] Download completed successfully!")
            except Exception as e:
                print("[Tracking Engine] Failed to download model:", e)

        try:
            base_options = python.BaseOptions(
                model_asset_path=MODEL_PATH,
                delegate=python.BaseOptions.Delegate.CPU
            )
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=4,  # Detect all hands in frame to filter out background bystanders
                min_hand_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[Tracking Engine] MediaPipe HandLandmarker initialized successfully!")
        except Exception as e:
            print("[Tracking Engine] HandLandmarker init error:", e)

    def setup_camera(self):
        for idx in [1, 0, 2]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.cap = cap
                    print(f"[Tracking Engine] Connected to webcam at index {idx}")
                    return
                cap.release()
        print("[Tracking Engine] Warning: No active webcam found.")

    def reset_player_lock(self):
        self.locked_hand_pos = None
        self.locked_palm_size = 0.0
        self.last_player_seen_time = 0.0

    def process_frame(self, is_gameplay_active=True):
        self.hand_landmarks_screen = []

        if not self.cap or not self.cap.isOpened():
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
            return None

        ret, frame = self.cap.read()
        if not ret:
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
            return None

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # If in menu screens and gameplay is paused -> skip AI inference
        if not is_gameplay_active:
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"
            return cv2.resize(rgb_frame, (WIDTH, HEIGHT))

        timestamp_ms = int(time.time() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        hand_detected = False

        if self.detector:
            try:
                results = self.detector.detect_for_video(mp_image, timestamp_ms)
                if results.hand_landmarks and len(results.hand_landmarks) > 0:
                    candidates = []
                    for h_idx, landmarks in enumerate(results.hand_landmarks):
                        wrist = landmarks[0]
                        mcp = landmarks[9]
                        palm_sz = math.hypot((wrist.x - mcp.x) * WIDTH, (wrist.y - mcp.y) * HEIGHT)
                        center_x = (wrist.x + mcp.x) / 2.0 * WIDTH
                        center_y = (wrist.y + mcp.y) / 2.0 * HEIGHT
                        
                        dist_to_prev = 0.0
                        if self.locked_hand_pos is not None:
                            dist_to_prev = math.hypot(center_x - self.locked_hand_pos[0], center_y - self.locked_hand_pos[1])
                            
                        candidates.append({
                            "landmarks": landmarks,
                            "palm_size": palm_sz,
                            "center": (center_x, center_y),
                            "dist_to_prev": dist_to_prev
                        })
                    
                    now = time.time()
                    chosen_candidate = None
                    
                    if self.locked_hand_pos is not None and (now - self.last_player_seen_time < 1.8):
                        valid_tracks = [c for c in candidates if c["dist_to_prev"] < 280]
                        if valid_tracks:
                            chosen_candidate = min(valid_tracks, key=lambda c: c["dist_to_prev"] - (c["palm_size"] * 0.4))
                    
                    if chosen_candidate is None:
                        chosen_candidate = max(candidates, key=lambda c: c["palm_size"])
                        
                    if chosen_candidate:
                        self.locked_hand_pos = chosen_candidate["center"]
                        self.locked_palm_size = chosen_candidate["palm_size"]
                        self.last_player_seen_time = now
                        
                        lm = chosen_candidate["landmarks"]
                        self.hand_landmarks_screen = [(int(p.x * WIDTH), int(p.y * HEIGHT)) for p in lm]
                        
                        index_tip = lm[8]
                        thumb_tip = lm[4]
                        
                        gesture, pinch_dist, is_pinched = GestureClassifier.classify(lm)
                        self.current_detected_gesture = gesture
                        self.pinch_dist = pinch_dist
                        self.is_pinched = is_pinched
                        
                        if self.is_pinched:
                            target_x = int(((index_tip.x + thumb_tip.x) / 2) * WIDTH)
                            target_y = int(((index_tip.y + thumb_tip.y) / 2) * HEIGHT)
                        else:
                            target_x = int(index_tip.x * WIDTH)
                            target_y = int(index_tip.y * HEIGHT)
                        
                        self.cursor_pos[0] += (target_x - self.cursor_pos[0]) * 0.65
                        self.cursor_pos[1] += (target_y - self.cursor_pos[1]) * 0.65
                        hand_detected = True
            except Exception as e:
                pass

        if not hand_detected:
            self.cursor_pos = [-1000, -1000]
            self.current_detected_gesture = "NONE"

        return cv2.resize(rgb_frame, (WIDTH, HEIGHT))
