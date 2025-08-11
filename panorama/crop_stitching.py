import cv2
import numpy as np
import logging
from typing import List, Optional, Tuple
from .interfaces import FrameStitcher


class HorizontalStitcher(FrameStitcher):
    def __init__(self, camera_count: int, cropped_height: int, resolution: Tuple[int, int]):
        self.camera_count = camera_count
        self.cropped_height = cropped_height
        self.resolution = resolution

    def stitch_frames(self, frames: List[np.ndarray]) -> Optional[np.ndarray]:
        if len(frames) != self.camera_count:
            return None

        processed = []
        for i, frame in enumerate(frames):
            # 프레임이 유효하면 보정 수행, 아니면 빈 이미지로 대체
            if frame is not None and frame.size > 0:
                processed.append(frame)
            else:
                cropped = np.zeros((self.cropped_height, self.resolution[0], 3), dtype=np.uint8)
                processed.append(cropped)

        # 좌우 스티칭
        try:
            stitched = processed[0]
            for i in range(1, len(processed)):
                left = stitched
                right = processed[i]

                # 높이가 다르면 resize로 맞춤
                if left.shape[0] != right.shape[0]:
                    min_h = min(left.shape[0], right.shape[0])
                    left = cv2.resize(left, (left.shape[1], min_h))
                    right = cv2.resize(right, (right.shape[1], min_h))

                stitched = np.hstack((left, right))
            return stitched

        except Exception as e:
            logging.warning(f"[Stitcher] 스티칭 실패: {e}")
            return None