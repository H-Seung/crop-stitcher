import cv2
import numpy as np
import time
from typing import Optional, Dict, Any


class OpenCVDisplayManager(DisplayManager):
    """Single Responsibility: OpenCV를 이용한 디스플레이 관리"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.window_name = ""
        self.window_resized = False

    def initialize_display(self, window_name: str) -> None:
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def show_frame(self, frame: np.ndarray) -> None:
        # 윈도우 크기 조정 (최초 한 번만)
        if not self.window_resized:
            self._setup_window_size(frame)
            self.window_resized = True

        # 프레임 리사이즈
        resized_frame = self._resize_frame_for_display(frame)

        cv2.imshow(self.window_name, resized_frame)

    def handle_input(self) -> Optional[str]:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            return "quit"
        elif key == ord('s'):
            return "screenshot"
        return None

    def cleanup(self) -> None:
        cv2.destroyAllWindows()

    def _setup_window_size(self, frame: np.ndarray) -> None:
        if self.config['display']['fullscreen']:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            pano_h, pano_w = frame.shape[:2]
            disp_w = self.config['display']['resolution']['width']
            aspect = pano_h / pano_w
            disp_h = int(disp_w * aspect)
            cv2.resizeWindow(self.window_name, disp_w, disp_h)

    def _resize_frame_for_display(self, frame: np.ndarray) -> np.ndarray:
        if self.config['display']['fullscreen']:
            return frame
        else:
            pano_h, pano_w = frame.shape[:2]
            disp_w = self.config['display']['resolution']['width']
            aspect = pano_h / pano_w
            disp_h = int(disp_w * aspect)
            return cv2.resize(frame, (disp_w, disp_h))