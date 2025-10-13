import logging
import time
from typing import List


class PanoramaSystem:
    """
    Dependency Inversion Principle: 구체적인 구현체가 아닌 인터페이스에 의존
    Single Responsibility: 전체 파노라마 시스템의 조율
    """

    def __init__(self,
                 config_provider: ConfigProvider,
                 frame_providers: List[FrameProvider],
                 frame_processor: FrameProcessor,
                 stitcher: FrameStitcher,
                 display_manager: DisplayManager):
        self.config_provider = config_provider
        self.frame_providers = frame_providers
        self.frame_processor = frame_processor
        self.stitcher = stitcher
        self.display_manager = display_manager
        self.fps_counter = FPSCounter()
        self.logger = logging.getLogger("PanoramaSystem")
        logging.basicConfig(level=logging.INFO)

    def initialize(self) -> None:
        """시스템 초기화"""
        CameraSystemInitializer.initialize_camera_system()

        for provider in self.frame_providers:
            provider.start()

        self.display_manager.initialize_display("360 Panorama")

    def run(self) -> None:
        """메인 실행 루프"""
        self.logger.info("파노라마 시스템 시작")

        try:
            while True:
                if not self._process_frame_cycle():
                    continue

                action = self.display_manager.handle_input()
                if action == "quit":
                    break
                elif action == "screenshot":
                    self._save_screenshot()

        finally:
            self._cleanup()

    def _process_frame_cycle(self) -> bool:
        """한 사이클의 프레임 처리"""
        # 프레임 수집
        frames = []
        for i, provider in enumerate(self.frame_providers):
            data = provider.get_frame()
            if data is not None:
                processed_frame = self.frame_processor.process_frame(data.frame, i)
                frames.append(processed_frame)
            else:
                frames.append(None)

        # 유효한 프레임이 없으면 건너뜀
        if all(f is None or f.size == 0 for f in frames):
            return False

        # 스티칭
        panorama = self.stitcher.stitch_frames(frames)
        if panorama is None or panorama.size == 0:
            self.logger.warning("생성된 파노라마가 비어 있음")
            return False

        # FPS 업데이트 및 표시
        self.fps_counter.update()
        panorama_with_fps = self.fps_counter.add_fps_to_frame(panorama)

        # 디스플레이
        self.display_manager.show_frame(panorama_with_fps)

        # 스크린샷용으로 마지막 파노라마 저장
        self.last_panorama = panorama
        return True

    def _save_screenshot(self) -> None:
        """스크린샷 저장"""
        if hasattr(self, 'last_panorama'):
            filename = f"panorama_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, self.last_panorama)
            self.logger.info(f"스크린샷 저장: {filename}")

    def _cleanup(self) -> None:
        """리소스 정리"""
        for provider in self.frame_providers:
            provider.stop()
        self.display_manager.cleanup()
        self.logger.info("종료 완료")