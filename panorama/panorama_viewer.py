import cv2
import logging
import time
from typing import List
from rectrl import *
from .interfaces import FrameProvider, FrameProcessor, FrameStitcher, DisplayManager


class PanoramaViewer:
    def __init__(self,
                 frame_providers: List[FrameProvider],
                 frame_processor: FrameProcessor,
                 stitcher: FrameStitcher,
                 display_manager: DisplayManager):
        self.frame_providers = frame_providers
        self.frame_processor = frame_processor
        self.stitcher = stitcher
        self.display_manager = display_manager
        self.logger = logging.getLogger("PanoramaViewer")
        logging.basicConfig(level=logging.INFO)

    def initialize(self):
        RECTRL_Open()
        RECTRL_EnableMasterSyncMode(True, CAM0)
        RECTRL_Close()

        for provider in self.frame_providers:
            provider.start()

        self.display_manager.initialize_display("Panorama")

    def run(self):
        self.logger.info("파노라마 뷰어 시작")
        fps_counter = 0
        start_time = time.time()
        current_fps = 0.0  # 현재 FPS 값을 저장하는 변수

        # 프레임 처리
        try:
            while True:
                frames = []
                for i, provider in enumerate(self.frame_providers):
                    data = provider.get_frame()
                    if data is not None:
                        processed_frame = self.frame_processor.preprocess_frame(data.frame, i)
                        frames.append(processed_frame)
                    else:
                        frames.append(None)

                if all(f is None or f.size == 0 for f in frames): # 전부 invalid일 경우,
                    continue

                # 스티칭
                panorama = self.stitcher.stitch_frames(frames)
                if panorama is None or panorama.size == 0:
                    self.logger.warning("생성된 파노라마가 비어 있음")
                    continue

                # FPS 계산
                fps_counter += 1
                elapsed = time.time() - start_time
                if elapsed >= 0.5:  # 0.5초마다 FPS를 계산하여 업데이트
                    current_fps  = fps_counter / elapsed
                    fps_counter = 0
                    start_time = time.time()

                self.display_manager.show_frame(panorama, current_fps)

                action = self.display_manager.handle_input()
                if action == "quit":
                    break
                elif action == "screenshot":
                    filename = f"panorama_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(filename, panorama)
                    self.logger.info(f"스크린샷 저장: {filename}")

        finally:
            for provider in self.frame_providers:
                provider.stop()
            self.display_manager.cleanup()
            self.logger.info("종료 완료")
