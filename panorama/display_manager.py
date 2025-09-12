import cv2
import numpy as np
import time
import logging
from typing import Optional, Dict, Any
from .interfaces import DisplayManager


class OpenCVDisplayManager(DisplayManager):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.window_name = ""
        self.window_resized = False # 윈도우 창 크기 조정을 최초 한번만 실행하기 위한 flag
        self.logger = logging.getLogger("OpenCVDisplayManager")

    def initialize_display(self, window_name: str) -> None:
        self.window_name = self.config['display'].get('window_name', window_name)
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def show_frame(self, frame: np.ndarray, fps: float) -> None:
        panorama_height, panorama_width = frame.shape[:2]

        # 윈도우 창 resize
        if not self.window_resized:
            if self.config['display']['fullscreen']:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                display_width = self.config['display']['resolution']['width']
                aspect = panorama_height / panorama_width
                display_height = int(display_width * aspect) # display 가로 기준으로 resize
                cv2.resizeWindow(self.window_name, display_width, display_height)
            self.window_resized = True

        # 파노라마 resize
        if self.config['display']['fullscreen']:
            panorama_resized = frame
        else:
            display_width = self.config['display']['resolution']['width']
            aspect = panorama_height / panorama_width
            display_height = int(display_width * aspect)
            panorama_resized = cv2.resize(frame, (display_width, display_height))

        # FPS 표시
        if fps > 0:
            cv2.putText(panorama_resized, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow(self.window_name, panorama_resized)

    def handle_input(self) -> Optional[str]:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            self.logger.info(f"handle_input : {key} -> quit")
            return "quit"
        elif key == ord('s'):
            self.logger.info(f"handle_input : {key} -> screenshot")
            return "screenshot"
        return None

    def cleanup(self) -> None:
        cv2.destroyAllWindows()