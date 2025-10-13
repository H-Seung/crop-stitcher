from rectrl import *


class CameraSystemInitializer:
    """Single Responsibility: 카메라 시스템 초기화"""

    @staticmethod
    def initialize_camera_system() -> None:
        RECTRL_Open()
        RECTRL_EnableMasterSyncMode(True, CAM0)
        RECTRL_Close()
