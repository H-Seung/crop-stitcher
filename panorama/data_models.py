from dataclasses import dataclass
import numpy as np


@dataclass
class CameraFrame:
    camera_id: int
    frame: np.ndarray
    timestamp: float