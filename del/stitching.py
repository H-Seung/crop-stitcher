import cv2
import numpy as np
import logging
from typing import List, Optional, Dict, Any


class HorizontalStitcher(FrameStitcher):
    """Single Responsibility: 수평으로 프레임들을 스티칭"""

    def __init__(self, camera_count: int, cropped_height: int, resolution: Tuple[int, int]):
        self.camera_count = camera_count
        self.cropped_height = cropped_height
        self.resolution = resolution

    def stitch_frames(self, frames: List[np.ndarray]) -> Optional[np.ndarray]:
        if len(frames) != self.camera_count:
            return None

        try:
            # 첫 번째 프레임부터 시작
            stitched = frames[0] if frames[0] is not None else self._create_empty_frame()

            for i in range(1, len(frames)):
                right = frames[i] if frames[i] is not None else self._create_empty_frame()
                stitched = self._combine_frames(stitched, right)

            return stitched

        except Exception as e:
            logging.warning(f"[Stitcher] 스티칭 실패: {e}")
            return None

    def _create_empty_frame(self) -> np.ndarray:
        return np.zeros((self.cropped_height, self.resolution[0], 3), dtype=np.uint8)

    def _combine_frames(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        # 높이가 다르면 맞춤
        if left.shape[0] != right.shape[0]:
            min_h = min(left.shape[0], right.shape[0])
            left = cv2.resize(left, (left.shape[1], min_h))
            right = cv2.resize(right, (right.shape[1], min_h))

        return np.hstack((left, right))