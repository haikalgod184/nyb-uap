
import time
import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.label import Label

class UAPScanner(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = None
        self.frame = None
        self.last = None
        self.fps = 0.0
        self.prev_t = time.perf_counter()
        self.target = None
        self.target_id = 1
        self.status = "SCANNING"
        self.label = Label(
            text="NYB-UAP // PANOPTICORE\nINITIALIZING CAMERA...",
            font_size="14sp",
            color=(0.5, 1, 0.75, 1),
            size_hint=(1, 1),
            halign="left",
            valign="top",
        )
        self.add_widget(self.label)
        Clock.schedule_interval(self.update, 1/30)

    def on_kv_post(self, *args):
        self.start_camera()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        if self.last is None:
            self.last = gray
            return None
        diff = cv2.absdiff(self.last, gray)
        self.last = gray
        _, mask = cv2.threshold(diff, 28, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
        mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = 0
        h, w = gray.shape
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            area = cw * ch
            if area < 12 or area > w*h*0.08:
                continue
            cx, cy = x + cw/2, y + ch/2
            # Favor small isolated moving objects, especially in the upper sky.
            sky_bonus = max(0.0, 1.0 - cy/h)
            score = min(area / 500.0, 1.0) * 0.7 + sky_bonus * 0.3
            if score > best_score:
                best_score = score
                best = (x, y, cw, ch, score)
        return best

    def update(self, dt):
        if not self.cap:
            return
        ok, frame = self.cap.read()
        if not ok:
            return
        # Intentionally NOT mirrored.
        self.frame = frame
        candidate = self.detect_motion(frame)
        if candidate:
            x, y, w, h, score = candidate
            if self.target is None:
                self.target = [x, y, w, h, score, self.target_id]
            else:
                ox, oy, ow, oh, *_ = self.target
                # Smooth target update instead of jumping between detections.
                a = 0.25
                self.target[0] = ox*(1-a) + x*a
                self.target[1] = oy*(1-a) + y*a
                self.target[2] = ow*(1-a) + w*a
                self.target[3] = oh*(1-a) + h*a
                self.target[4] = score
        elif self.target:
            self.target[4] *= 0.94
            if self.target[4] < 0.08:
                self.target = None

        now = time.perf_counter()
        instant = 1.0 / max(now - self.prev_t, 1e-6)
        self.prev_t = now
        self.fps = self.fps*0.9 + min(instant, 60)*0.1

        if self.target:
            x, y, w, h, score, tid = self.target
            self.status = f"TRACK-{tid:02d}  ANOMALY CANDIDATE"
            self.label.text = (
                "NYB-UAP // PANOPTICORE\n"
                f"STATUS   {self.status}\n"
                f"FPS      {self.fps:04.1f}\n"
                f"TARGET   {x:.0f},{y:.0f}  {w:.0f}x{h:.0f}\n"
                f"MOTION   {score*100:.0f}%\n"
                "TYPE     UNKNOWN\n"
                "YOLO     SNAP-ANALYSIS ONLY"
            )
        else:
            self.status = "SCANNING"
            self.label.text = (
                "NYB-UAP // PANOPTICORE\n"
                "STATUS   SCANNING\n"
                f"FPS      {self.fps:04.1f}\n"
                "TARGET   NONE\n"
                "MODE     MICRO-MOTION"
            )

        self.draw_hud()

    def draw_hud(self):
        self.canvas.after.clear()
        Color(0.25, 1, 0.55, 0.85)
        cx, cy = self.width/2, self.height/2
        Line(circle=(cx, cy, min(self.width, self.height)*0.22), width=1)
        Line(points=[cx-35, cy, cx+35, cy], width=1)
        Line(points=[cx, cy-35, cx, cy+35], width=1)

        if self.target:
            x, y, w, h, score, tid = self.target
            sx = self.width / 640.0
            sy = self.height / 480.0
            bx = x*sx
            by = self.height - (y+h)*sy
            bw = w*sx
            bh = h*sy
            Line(rectangle=(bx, by, bw, bh), width=1.4)
            Line(points=[bx, by+bh, bx+20, by+bh], width=2)
            Line(points=[bx, by+bh, bx, by+bh-20], width=2)

    def on_touch_down(self, touch):
        if self.target:
            self.status = f"LOCKED TRACK-{self.target[5]:02d}"
            return True
        return super().on_touch_down(touch)

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None

class NYBUAP(App):
    def build(self):
        return UAPScanner()

    def on_stop(self):
        self.root.stop()

if __name__ == "__main__":
    NYBUAP().run()
