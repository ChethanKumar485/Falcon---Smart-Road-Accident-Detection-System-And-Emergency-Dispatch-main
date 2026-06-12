"""
Accident Detection Engine
Uses motion analysis + optical flow + edge detection
No heavy ML model required - works with pure CV
"""
import cv2
import numpy as np
import time

class AccidentDetector:
    def __init__(self):
        self.prev_frame = None
        self.prev_gray = None
        self.motion_history = []
        self.active = True
        self.fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        self.accident_cooldown = 0
        self.COOLDOWN_SECONDS = 10

    def is_active(self):
        return self.active

    def detect(self, frame):
        if frame is None:
            return {'accident_detected': False, 'confidence': 0.0}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Cooldown check
        if time.time() - self.accident_cooldown < self.COOLDOWN_SECONDS:
            self.prev_gray = gray
            return {'accident_detected': False, 'confidence': 0.0}

        if self.prev_gray is None:
            self.prev_gray = gray
            return {'accident_detected': False, 'confidence': 0.0}

        # Frame difference
        frame_delta = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Motion score
        motion_score = np.sum(thresh) / (frame.shape[0] * frame.shape[1] * 255)
        self.motion_history.append(motion_score)
        if len(self.motion_history) > 30:
            self.motion_history.pop(0)

        # Background subtraction
        fgmask = self.fgbg.apply(frame)
        fg_score = np.sum(fgmask > 200) / (frame.shape[0] * frame.shape[1])

        # Edge change detection
        edges_curr = cv2.Canny(gray, 50, 150)
        edges_prev = cv2.Canny(self.prev_gray, 50, 150)
        edge_diff = cv2.absdiff(edges_curr, edges_prev)
        edge_score = np.sum(edge_diff) / (frame.shape[0] * frame.shape[1] * 255)

        # Sudden motion spike (accident signature)
        avg_motion = np.mean(self.motion_history[:-5]) if len(self.motion_history) > 5 else 0
        recent_motion = np.mean(self.motion_history[-5:]) if len(self.motion_history) >= 5 else 0
        motion_spike = (recent_motion - avg_motion) if avg_motion > 0 else 0

        # Composite score
        confidence = min(1.0, (
            motion_spike * 3.0 +
            fg_score * 2.0 +
            edge_score * 1.5 +
            motion_score * 1.0
        ))

        self.prev_gray = gray

        THRESHOLD = 0.45
        if confidence >= THRESHOLD and motion_score > 0.05:
            self.accident_cooldown = time.time()
            severity = 'CRITICAL' if confidence > 0.8 else 'HIGH' if confidence > 0.6 else 'MODERATE'
            return {
                'accident_detected': True,
                'confidence': round(confidence, 3),
                'severity': severity,
                'motion_score': motion_score,
                'fg_score': fg_score,
                'edge_score': edge_score
            }

        return {'accident_detected': False, 'confidence': round(confidence, 3)}
