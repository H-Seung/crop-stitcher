from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
import numpy as np


class FrameProvider(ABC):
    @abstractmethod
    def get_frame(self):
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class FrameProcessor(ABC):
    @abstractmethod
    def preprocess_frame(self, frame: np.ndarray, camera_id: int) -> np.ndarray:
        pass


class FrameStitcher(ABC):
    @abstractmethod
    def stitch_frames(self, frames: List[np.ndarray]) -> Optional[np.ndarray]:
        pass


class ConfigProvider(ABC):
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        pass


class DisplayManager(ABC):
    @abstractmethod
    def initialize_display(self, window_name: str) -> None:
        pass

    @abstractmethod
    def show_frame(self, frame: np.ndarray, fps: float) -> None:
        pass

    @abstractmethod
    def handle_input(self) -> Optional[str]:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass
