import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import mss
import time
import json
import os
import pygetwindow as gw

CONFIG_FILE = "detector_config.json"

class ChimeDetector:
    def __init__(self, log_callback=None):
        self.roi = None
        self._log_callback = log_callback
        self.load_config()

    def log(self, msg):
        if self._log_callback:
            self._log_callback(msg)
        else:
            print(msg)

    def get_roblox_window_rect(self):
        try:
            rblx_window = gw.getWindowsWithTitle("Roblox")[0]
            return {
                "top": rblx_window.top,
                "left": rblx_window.left,
                "width": rblx_window.width,
                "height": rblx_window.height
            }
        except IndexError:
            #focus on monitor 1
            with mss.mss() as sct:
                return sct.monitors[1]

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.roi = data.get('roi')

    def save_config(self):
        if self.roi:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'roi': self.roi}, f)

    def calibrate(self):
        self.log("taking screenshot")
        
        rect = self.get_roblox_window_rect()
        with mss.mss() as sct:
            screenshot = np.array(sct.grab(rect))
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        cv2.putText(screenshot, "draw a box around the chimes and press enter", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.namedWindow("select wind chimes", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("select wind chimes", cv2.WND_PROP_TOPMOST, 1)
        roi = cv2.selectROI("select wind chimes", screenshot, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()
        
        if roi[2] > 0 and roi[3] > 0:
            self.roi = roi
            self.save_config()
            self.log(f"Calibration successful! ROI saved: {roi}")
            return True
        else:
            self.log("Calibration cancelled.")
            return False

    def detect_movement(self, duration=3):
        if not self.roi:
            self.log("ROI not set. Please calibrate first.")
            return False

        rect = self.get_roblox_window_rect()
        
        # Adjust rect based on ROI
        x, y, w, h = self.roi
        monitor = {
            "top": rect["top"] + y,
            "left": rect["left"] + x,
            "width": w,
            "height": h
        }

        self.log("Detecting movement...")
        time.sleep(0.5)

        with mss.mss() as sct:
            initial_img = np.array(sct.grab(monitor))
            initial_gray = cv2.cvtColor(initial_img, cv2.COLOR_BGRA2GRAY)
            variance = np.var(initial_gray)

            self.log(f"ROI Texture Variance: {variance:.2f}")
            if variance < 100: 
                self.log("Chimes not found in ROI (variance too low). Probably facing the wrong way.")
                return "missing"

            end_time = time.time() + duration
            frames = []

            while time.time() < end_time:
                # Grab the region of interest
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                frames.append(gray)
                time.sleep(0.1)

        if len(frames) < 2:
            return False

        # Calculate Structural Similarity Index between the first frame and all subsequent frames
        min_ssim = 1.0
        
        for i in range(1, len(frames)):
            # compute SSIM between the first frame and the current frame
            # This captures the maximum displacement during the 3 second window
            score, diff = ssim(frames[0], frames[i], full=True)
            if score < min_ssim:
                min_ssim = score

        # SSIM is 1.0 for identical images, so lower means more movement.
        self.log(f"Minimum SSIM Score: {min_ssim:.4f}")
        
        # If the minimum structural similarity drops below a certain threshold, it's moving
        if min_ssim < 0.985:
            self.log("something is moving. probably chimes.")
            return True
        else:
            self.log("wind chimes are static.")
            return False

if __name__ == "__main__":
    detector = ChimeDetector()
    if not detector.roi:
        detector.calibrate()
    detector.detect_movement()
