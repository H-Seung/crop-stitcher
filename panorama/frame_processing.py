import cv2
import numpy as np
import logging
from typing import Tuple, Dict, Any
from .interfaces import FrameProcessor
from .transformation_utils import TransformationUtils


class CropCalculator:
    def __init__(self, config: Dict[str, Any], resolution: Tuple[int, int]):
        self.config = config
        self.resolution = resolution
        self.logger = logging.getLogger("CropCalculator")

    def calculate_vertical_crop(self) -> Tuple[int, int]:
        """config 값으로 상하 크롭"""
        crop_config = self.config['calibration'].get('vertical_crop', {})
        if crop_config is None:
            crop_config = {}
        self.logger.info(f"crop_config : {crop_config}")

        if (
                crop_config and
                'crop_top' in crop_config and crop_config['crop_top'] is not None and
                'crop_bottom' in crop_config and crop_config['crop_bottom'] is not None
        ):
            crop_top = int(crop_config['crop_top'])
            crop_bottom = int(crop_config['crop_bottom'])
            self.logger.info(f"config.yaml 기반 크롭 범위: top={crop_top}, bottom={crop_bottom}")
            return crop_top, crop_bottom

        return self._auto_calculate_vertical_crop()

    def _auto_calculate_vertical_crop(self) -> Tuple[int, int]:
        """
        (config 값 없을 시) 상하 자동 계산 크롭 (샘플 프레임 임시로 하나 캡쳐해 crop 기준 잡음)
        회전 및 정렬 보정이 적용된 각 카메라 프레임들을 처리한 후,
        모든 프레임에서 유효한 최소 영역을 찾아 크롭 범위를 계산
        """
        self.logger.info(f"config.yaml 내 vertical_crop 값이 없으므로 _auto_calculate_vertical_crop 실행")
        processed_frames = []

        # 각 카메라별로 샘플 프레임을 캡처하고 실제 전처리 과정을 거침
        for camera_id, dev in enumerate(self.config['camera']['device_paths']):
            cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            ret, frame = cap.read()
            h, w = frame.shape[:2]
            self.logger.info(f"camera_id={camera_id}, h={h}, w={w}")
            cap.release()

            if ret:
                # 실제 전처리 과정 적용 (회전, 오프셋)
                processed_frame = TransformationUtils.apply_cpu_transformations(
                    frame, h, w, self.config, camera_id
                )
                if processed_frame is not None:
                    processed_frames.append(processed_frame)
                else:
                    self.logger.warning(f"카메라 {camera_id} 프레임 처리 실패")
            else:
                self.logger.warning(f"샘플 캡처 실패: {dev}")

        if not processed_frames:
            raise RuntimeError("카메라에서 처리된 프레임을 얻지 못해 크롭 계산 불가")

        # 모든 처리된 프레임에서 유효한(검은색이 아닌) 영역 찾기
        valid_regions = []
        for frame in processed_frames:
            # 그레이스케일로 변환하여 유효 영역 찾기
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 0이 아닌 픽셀들의 위치 찾기
            non_zero_rows = np.where(np.any(gray > 0, axis=1))[0] # y축으로 내려가면서 하나라도 black이 아닌 행 번호들
            if len(non_zero_rows) > 0:
                valid_top = non_zero_rows[0]
                valid_bottom = non_zero_rows[-1] + 1
                valid_regions.append((valid_top, valid_bottom))

        if not valid_regions:
            # 유효 영역을 찾지 못한 경우 전체 영역 사용
            self.logger.warning("유효 영역을 찾지 못함, 전체 영역 사용")
            return 0, self.resolution[1]

        # self.logger.info("==> valid_regions : ", valid_regions)
        print("==> valid_regions : ", valid_regions)

        # 모든 프레임에서 공통으로 유효한 영역 계산
        max_top = max(region[0] for region in valid_regions)
        min_bottom = min(region[1] for region in valid_regions)

        # 안전 마진 추가 (프레임 높이의 config 내 margin(%) 만큼)
        margin = self.config['calibration']['vertical_crop']['margin']
        margin_px = int(self.resolution[1] * margin)
        crop_top = max(0, max_top + margin_px)
        crop_bottom = min(self.resolution[1], min_bottom - margin_px)

        self.logger.info(f"자동 크롭 범위 (처리된 프레임 기준): top={crop_top}, bottom={crop_bottom}")
        return crop_top, crop_bottom

    def calculate_horizontal_crop_from_fov(self, camera_id: int) -> Tuple[int, int]:
        # 카메라 가로 최대화각을 바탕으로 좌우 보고싶은 각도만큼 크롭
        fov = self.config['camera'].get('fov_deg', 90) # 기본값 90도
        desired_angle = self.config.get('stitching', {}).get('desired_view_angle', 60)
        width = self.resolution[0]
        cut_degree = (fov - desired_angle) / 2
        deg_per_pixel = fov / width
        crop_pixels = int(cut_degree / deg_per_pixel)
        return crop_pixels, crop_pixels


class PanoramaFrameProcessor(FrameProcessor):
    def __init__(self, config: Dict[str, Any], resolution: Tuple[int, int]):
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)
        self.config = config
        self.resolution = resolution
        crop_calculator = CropCalculator(config, resolution)
        self.crop_top, self.crop_bottom = crop_calculator.calculate_vertical_crop()
        self.cropped_height = self.crop_bottom - self.crop_top
        self.crop_calculator = crop_calculator
        self.logger = logging.getLogger("PanoramaFrameProcessor")

    def preprocess_frame(self, frame: np.ndarray, camera_id: int) -> np.ndarray:
        """프레임 전처리 과정, crop and align"""
        calib = self.config['calibration']
        rotate = calib['rotation_correction'].get(f'cam{camera_id}', 0)
        offset = calib['vertical_offset'].get(f'cam{camera_id}', 0)
        scale = calib['horizontal_scale'].get(f'cam{camera_id}', 1.0)
        hcrop = calib.get('horizontal_crop', {}).get(f'cam{camera_id}', None)

        if hcrop is None: # horizontal_crop 값이 없을 때 fov 기반 자동 계산 (config에서 horizontal~right 주석처리)
            left_crop, right_crop = self.crop_calculator.calculate_horizontal_crop_from_fov(camera_id)
        else:
            left_crop = hcrop.get('left', 0)
            right_crop = hcrop.get('right', 0)

        # 보정이 필요없는 경우 CPU에서 간단히 크롭만 처리
        if rotate == 0 and offset == 0 and scale == 1.0 and left_crop == 0 and right_crop == 0: # 보정 불필요할 경우 바로 crop만 수행하고 return (GPU 사용 안함)
            return frame[self.crop_top:self.crop_bottom, :]

        # GPU 처리가 필요한 경우
        return self._preprocess_with_gpu(frame, rotate, offset, scale, left_crop, right_crop)

    def _preprocess_with_gpu(self, frame: np.ndarray,
                          rotate: float, offset: float, scale: float,
                          left_crop: int, right_crop: int) -> np.ndarray:
        """GPU를 사용한 프레임 처리"""
        # GPU에 프레임 업로드
        gpu_frame = cv2.cuda_GpuMat()
        gpu_frame.upload(frame)

        h = gpu_frame.size()[1]
        w = gpu_frame.size()[0]

        # 전처리 과정 (회전, 수직 offset)
        gpu_frame = TransformationUtils.apply_gpu_transformations(
            gpu_frame, h, w, rotate, offset)

        # 좌우 crop
        if left_crop > 0 or right_crop > 0:
            gpu_frame = gpu_frame.colRange(left_crop, w - right_crop)

        # 상하 crop
        gpu_frame = gpu_frame.rowRange(self.crop_top, self.crop_bottom)

        # 리사이즈
        if scale != 1.0:
            new_w = int(w * scale)
            new_h = h
            gpu_frame = cv2.cuda.resize(gpu_frame, (new_w, new_h))

        return gpu_frame.download()