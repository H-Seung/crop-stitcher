from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class CameraFrame:
    camera_id: int
    frame: np.ndarray
    timestamp: float


class FrameProvider(ABC):
    """Single Responsibility: 프레임 제공 인터페이스"""

    @abstractmethod
    def get_frame(self) -> Optional[CameraFrame]:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class FrameProcessor(ABC):
    """Single Responsibility: 프레임 처리 인터페이스"""

    @abstractmethod
    def process_frame(self, frame: np.ndarray, camera_id: int) -> np.ndarray:
        pass


class FrameStitcher(ABC):
    """Single Responsibility: 프레임 스티칭 인터페이스"""

    @abstractmethod
    def stitch_frames(self, frames: List[np.ndarray]) -> Optional[np.ndarray]:
        pass


class ConfigProvider(ABC):
    """Single Responsibility: 설정 제공 인터페이스"""

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        pass


class DisplayManager(ABC):
    """Single Responsibility: 디스플레이 관리 인터페이스"""

    @abstractmethod
    def initialize_display(self, window_name: str) -> None:
        pass

    @abstractmethod
    def show_frame(self, frame: np.ndarray) -> None:
        pass

    @abstractmethod
    def handle_input(self) -> Optional[str]:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass