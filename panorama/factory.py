from typing import List
from .config_manager import YamlConfigProvider
from .camera_capture import CameraCapture
from .frame_processing import PanoramaFrameProcessor
from .crop_stitching import HorizontalStitcher
from .display_manager import OpenCVDisplayManager
from .panorama_viewer import PanoramaViewer


class PanoramaViewerFactory:
    @staticmethod
    def create_viewer(config_path: str = "config.yaml") -> PanoramaViewer:
        # 설정 로드
        config_provider = YamlConfigProvider(config_path)
        config = config_provider.get_config()

        # 해상도 정보
        resolution = (config['camera']['resolution']['width'],
                      config['camera']['resolution']['height'])

        # 카메라들 생성
        frame_providers = []
        for i, device_path in enumerate(config['camera']['device_paths']):
            camera = CameraCapture(i, device_path, resolution)
            frame_providers.append(camera)

        # 프레임 처리기 생성
        frame_processor = PanoramaFrameProcessor(config, resolution)

        # 스티처 생성
        stitcher = HorizontalStitcher(
            camera_count=config['camera']['count'],
            cropped_height=frame_processor.cropped_height,
            resolution=resolution
        )

        # 디스플레이 매니저 생성
        display_manager = OpenCVDisplayManager(config)

        return PanoramaViewer(
            frame_providers=frame_providers,
            frame_processor=frame_processor,
            stitcher=stitcher,
            display_manager=display_manager
        )
