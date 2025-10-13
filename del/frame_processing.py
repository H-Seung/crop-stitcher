import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional


class CropCalculator:
    """Single Responsibility: 크롭 영역 계산"""

    def __init__(self, config: Dict[str, Any], resolution: Tuple[int, int]):
        self.config = config
        self.resolution = resolution

    def calculate_vertical_crop(self) -> Tuple[int, int]:
        """수직 크롭 영역 계산"""
        crop_config = self.config['calibration'].get('vertical_crop', {})

        if (
                'crop_top' in crop_config and crop_config['crop_top'] is not None and
                'crop_bottom' in crop_config and crop_config['crop_bottom'] is not None
        ):
            crop_top = int(crop_config['crop_top'])
            crop_bottom = int(crop_config['crop_bottom'])
            print(f"[INFO] config.yaml 기반 크롭 범위: top={crop_top}, bottom={crop_bottom}")
            return crop_top, crop_bottom

        return self._auto_calculate_vertical_crop()

    def _auto_calculate_vertical_crop(self) -> Tuple[int, int]:
        """자동 수직 크롭 계산"""
        sample_heights = []
        for dev in self.config['camera']['device_paths']:
            cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            ret, frame = cap.read()
            cap.release()

            if ret:
                sample_heights.append(frame.shape[0])
            else:
                print(f"[WARN] 샘플 캡처 실패: {dev}")

        if not sample_heights:
            raise RuntimeError("카메라에서 프레임을 얻지 못해 크롭 계산 불가")

        min_height = min(sample_heights)
        full_height = self.resolution[1]
        top_crop = (full_height - min_height) // 2
        bottom_crop = top_crop + min_height

        print(f"[INFO] 자동 크롭 범위: top={top_crop}, bottom={bottom_crop}")
        return top_crop, bottom_crop

    def calculate_horizontal_crop_from_fov(self, camera_id: int) -> Tuple[int, int]:
        """FOV 기반 수평 크롭 계산"""
        fov = self.config['camera'].get('fov_deg', 90)
        desired = self.config.get('stitching', {}).get('desired_view_angle', 60)
        width = self.resolution[0]
        cut_deg = (fov - desired) / 2
        deg_per_pixel = fov / width
        crop_pixels = int(cut_deg / deg_per_pixel)
        return crop_pixels, crop_pixels


class GPUFrameProcessor(FrameProcessor):
    """Single Responsibility: GPU를 이용한 프레임 처리"""

    def __init__(self, config: Dict[str, Any], resolution: Tuple[int, int]):
        self.config = config
        self.resolution = resolution

        crop_calculator = CropCalculator(config, resolution)
        self.crop_top, self.crop_bottom = crop_calculator.calculate_vertical_crop()
        self.cropped_height = self.crop_bottom - self.crop_top
        self.crop_calculator = crop_calculator

    def process_frame(self, frame: np.ndarray, camera_id: int) -> np.ndarray:
        """Open/Closed Principle: 새로운 처리 방식 추가 시 이 클래스를 확장"""
        calib = self.config['calibration']
        rotate = calib['rotation_correction'].get(f'cam{camera_id}', 0)
        offset = calib['vertical_offset'].get(f'cam{camera_id}', 0)
        scale = calib['horizontal_scale'].get(f'cam{camera_id}', 1.0)
        crop = calib.get('horizontal_crop', {}).get(f'cam{camera_id}', None)

        if crop is None:
            left_crop, right_crop = self.crop_calculator.calculate_horizontal_crop_from_fov(camera_id)
        else:
            left_crop = crop.get('left', 0)
            right_crop = crop.get('right', 0)

        # 보정이 불필요한 경우 빠른 처리
        if self._no_correction_needed(rotate, offset, scale, left_crop, right_crop):
            return frame[self.crop_top:self.crop_bottom, :]

        return self._apply_gpu_corrections(frame, rotate, offset, scale, left_crop, right_crop)

    def _no_correction_needed(self, rotate: float, offset: int, scale: float,
                              left_crop: int, right_crop: int) -> bool:
        return (rotate == 0 and offset == 0 and scale == 1.0 and
                left_crop == 0 and right_crop == 0)

    def _apply_gpu_corrections(self, frame: np.ndarray, rotate: float, offset: int,
                               scale: float, left_crop: int, right_crop: int) -> np.ndarray:
        gpu_frame = cv2.cuda_GpuMat()
        gpu_frame.upload(frame)
        h, w = frame.shape[:2]

        # 회전
        if rotate != 0:
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotate, 1.0).astype(np.float32)
            gpu_frame = cv2.cuda.warpAffine(gpu_frame, M, (w, h))

        # 수직 offset
        if offset != 0:
            M = np.float32([[1, 0, 0], [0, 1, offset]])
            gpu_frame = cv2.cuda.warpAffine(gpu_frame, M, (w, h))

        # 좌우 crop
        if left_crop > 0 or right_crop > 0:
            gpu_frame = gpu_frame.colRange(left_crop, w - right_crop)

        # 상하 crop
        gpu_frame = gpu_frame.rowRange(self.crop_top, self.crop_bottom)

        # 리사이즈
        if scale != 1.0:
            new_w = int(gpu_frame.size()[1] * scale)
            new_h = gpu_frame.size()[0]
            gpu_frame = cv2.cuda.resize(gpu_frame, (new_w, new_h))

        return gpu_frame.download()
