import cv2
import numpy as np
import time
import threading
from queue import Queue
from typing import Tuple, Optional
from .interfaces import FrameProvider
from .data_models import CameraFrame


class CameraCapture(FrameProvider):
    def __init__(self, camera_id: int, device_path: str, resolution: Tuple[int, int]):
        self.camera_id = camera_id
        self.device_path = device_path
        self.resolution = resolution
        self.cap = None
        self.frame_queue = Queue(maxsize=2)
        self.running = False
        self.thread = None
        self.last_frame: Optional[CameraFrame] = None # 마지막 유효 프레임 기억하기 위함

    def start(self):
        print(f"[CameraCapture] Start 카메라 {self.camera_id}: {self.device_path}")
        self.cap = cv2.VideoCapture(self.device_path, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"카메라 {self.camera_id} 열기 실패: {self.device_path}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True) # 각 카메라가 별도 스레드로 실시간 프레임 획득
        self.thread.start()

    def _capture_loop(self):
        print(f"[CameraCapture] 캡처 루프 시작: 카메라 {self.camera_id}")
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_obj = CameraFrame(self.camera_id, frame, time.time())
                self.last_frame = frame_obj # 항상 마지막 유효 프레임은 저장
                if self.frame_queue.full(): # 큐가 가득 차면 오래된 프레임 제거
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                self.frame_queue.put_nowait(frame_obj) # 새 프레임 큐에 추가
            else:
                print(f"[CameraCapture] 프레임 캡처 실패: 카메라 {self.camera_id}")
            time.sleep(0.005) # CPU 과점유 방지

    def get_frame(self) -> Optional[CameraFrame]:
        """프레임 큐가 비었을 땐 마지막 프레임 유지"""
        try:
            return self.frame_queue.get_nowait() # 큐가 비어 있으면 즉시 예외 발생
        except:
            return self.last_frame  # 마지막 프레임 반환 (캐시)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
