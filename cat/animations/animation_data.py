from dataclasses import dataclass
from typing import List
from PySide6.QtGui import QPixmap


@dataclass
class AnimationClip:
    name: str
    frames: List[QPixmap]
    fps: int = 12
    loop: bool = True
    durations_ms: List[int] = None

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def is_empty(self) -> bool:
        return len(self.frames) == 0

    def duration_for_index(self, index: int) -> int:
        if self.durations_ms and index < len(self.durations_ms):
            return self.durations_ms[index]
        # fallback to uniform fps
        return int(1000 / max(1, self.fps))
