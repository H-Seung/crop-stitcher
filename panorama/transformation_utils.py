import cv2
import numpy as np
from typing import Dict, Any

class TransformationUtils:
    """공통 변환 로직(회전, 수직 offset)을 담는 유틸리티 클래스"""
    @staticmethod
    def apply_cpu_transformations(frame: np.ndarray, h, w, config: Dict[str, Any], camera_id: int) -> np.ndarray:
        """CPU에서 변환 적용 (크롭 계산에 쓰이는 샘플 프레임 처리 시 사용)"""
        calib = config['calibration']
        rotate = calib['rotation_correction'].get(f'cam{camera_id}', 0)
        offset = calib['vertical_offset'].get(f'cam{camera_id}', 0)

        # 회전
        if rotate != 0:
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotate, 1.0)
            frame = cv2.warpAffine(frame, M, (w, h))

        # 수직 offset
        if offset != 0:
            M = np.float32([[1, 0, 0], [0, 1, -offset]])
            frame = cv2.warpAffine(frame, M, (w, h))

        return frame

    @staticmethod
    def apply_gpu_transformations(gpu_frame: cv2.cuda_GpuMat, h, w,
                                  rotate: float, offset: float) -> cv2.cuda_GpuMat:
        """GPU에서 변환 적용 (실시간 대량 프레임 처리 시 사용)"""
        # 회전
        if rotate != 0:
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotate, 1.0).astype(np.float32)
            gpu_frame = cv2.cuda.warpAffine(gpu_frame, M, (w, h))

        # 수직 offset
        if offset != 0:
            M = np.float32([[1, 0, 0], [0, 1, -offset]])
            gpu_frame = cv2.cuda.warpAffine(gpu_frame, M, (w, h))

        return gpu_frame