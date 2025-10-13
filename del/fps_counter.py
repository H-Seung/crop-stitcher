import time
import cv2
import numpy as np


class FPSCounter:
    """Single Responsibility: FPS 계산 및 표시"""

    def __init__(self):
        self.fps_counter = 0
        self.start_time = time.time()
        self.current_fps = 0.0

    def update(self) -> None:
        self.fps_counter += 1
        elapsed = time.time() - self.start_time

        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.start_time = time.time()

    def add_fps_to_frame(self, frame: np.ndarray) -> np.ndarray:
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame