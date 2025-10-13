class PanoramaSystemFactory:
    """Factory Pattern: 의존성 주입을 통한 시스템 생성"""

    @staticmethod
    def create_system(config_path: str = "config.yaml") -> PanoramaSystem:
        # 설정 로드
        config_provider = YamlConfigProvider(config_path)
        config = config_provider.get_config()

        # 해상도 정보
        resolution = (config['camera']['resolution']['width'],
                      config['camera']['resolution']['height'])

        # 카메라 생성
        frame_providers = []
        for i, device_path in enumerate(config['camera']['device_paths']):
            camera = CameraCapture(i, device_path, resolution)
            frame_providers.append(camera)

        # 프레임 처리기 생성
        frame_processor = GPUFrameProcessor(config, resolution)

        # 스티처 생성
        stitcher = HorizontalStitcher(
            camera_count=config['camera']['count'],
            cropped_height=frame_processor.cropped_height,
            resolution=resolution
        )

        # 디스플레이 매니저 생성
        display_manager = OpenCVDisplayManager(config)

        return PanoramaSystem(
            config_provider=config_provider,
            frame_providers=frame_providers,
            frame_processor=frame_processor,
            stitcher=stitcher,
            display_manager=display_manager
        )

if __name__ == '__main__':
    system = PanoramaSystemFactory.create_system()
    system.initialize()
    system.run()