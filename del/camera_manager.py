import cv2
import time
import threading
from queue import Queue
from typing import Tuple, Optional


class CameraCapture(FrameProvider):
    """Single Responsibility: 카메라로부터 프레임 캡처"""

    def __init__(self, camera_id: int, device_path: str, resolution: Tuple[int, int]):
        self.camera_id = camera_id
        self.device_path = device_path
        self.resolution = resolution
        self.cap = None
        self.frame_queue = Queue(maxsize=2)
        self.running = False
        self.thread = None
        self.last_frame: Optional[CameraFrame] = None

    def start(self) -> None:
        print(f"[CameraCapture] Start 카메라 {self.camera_id}: {self.device_path}")

        self.cap = cv2.VideoCapture(self.device_path, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"카메라 {self.camera_id} 열기 실패: {self.device_path}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self) -> None:
        print(f"[CameraCapture] 캡처 루프 시작: 카메라 {self.camera_id}")

        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_obj = CameraFrame(self.camera_id, frame, time.time())
                self.last_frame = frame_obj

                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass

                self.frame_queue.put_nowait(frame_obj)
            else:
                print(f"[CameraCapture] 프레임 캡처 실패: 카메라 {self.camera_id}")

            time.sleep(0.005)  # CPU 과점유 방지

    def get_frame(self) -> Optional[CameraFrame]:
        try:
            return self.frame_queue.get_nowait()
        except:
            return self.last_frame

    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
