"""Plain data passed from the vision module to the focus logic (no cv2 here)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisionSignals:
    face_present: bool
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    ear: float = 0.30          # average eye aspect ratio
    face_size: float = 0.0     # face bbox height / frame height
    face_y: float = 0.0        # face bbox center y / frame height


NO_FACE = VisionSignals(face_present=False)
