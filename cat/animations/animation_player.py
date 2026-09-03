from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtGui import QPixmap
from .animation_data import AnimationClip


class AnimationPlayer(QObject):
    def __init__(self, assets_root: Path, target_height: int = 120):
        super().__init__()
        self.assets_root = Path(assets_root)
        self.target_height = target_height
        self._clips: dict[str, AnimationClip] = {}
        self._current: Optional[AnimationClip] = None
        self._index = 0
        self._playing = False
        self._loop = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)

    def load_animation(self, name: str) -> AnimationClip:
        if name in self._clips:
            return self._clips[name]

        folder = self.assets_root / name
        frames = []
        if folder.is_dir():
            # Sort numerically by filename
            png_files = sorted(folder.glob("*.png"), key=lambda p: p.name.lower())
            for f in png_files:
                pix = QPixmap(str(f))
                if pix.isNull():
                    continue
                # Scale with nearest-neighbor for pixel art
                scaled = pix.scaledToHeight(
                    self.target_height,
                    Qt.FastTransformation
                )
                frames.append(scaled)
        fps = 5 if name.lower() == "idle" else 12
        durations_ms = None
        if name.lower() == "idle" and len(frames) == 7:
            # Per-frame timing for natural blink idle
            durations_ms = [1400, 190, 190, 230, 270, 230, 1700]
        # Truncate durations if frame count differs
        if durations_ms and len(durations_ms) > len(frames):
            durations_ms = durations_ms[:len(frames)]
        clip = AnimationClip(name=name, frames=frames, fps=fps, loop=True, durations_ms=durations_ms)
        self._clips[name] = clip
        return clip

    def play(self, name: str, loop: bool = True):
        clip = self.load_animation(name)
        self._current = clip
        self._loop = loop
        self._index = 0
        self._playing = True
        if clip.frame_count > 0:
            interval = clip.duration_for_index(0)
            self._timer.start(interval)
        else:
            self._timer.stop()

    def pause(self):
        self._playing = False
        self._timer.stop()

    def stop(self):
        self.pause()
        self._index = 0

    def reset(self):
        self._index = 0

    def set_loop(self, loop: bool):
        self._loop = loop

    def _advance(self):
        if not self._playing or self._current is None:
            return
        if self._current.frame_count == 0:
            return
        self._index += 1
        if self._index >= self._current.frame_count:
            if self._loop:
                self._index = 0
            else:
                self._playing = False
                self._timer.stop()
                return
        # Update timer interval for next frame
        next_interval = self._current.duration_for_index(self._index)
        self._timer.setInterval(next_interval)

    @property
    def current_frame(self) -> Optional[QPixmap]:
        if self._current is None or self._current.frame_count == 0:
            return None
        return self._current.frames[self._index]

    @property
    def current_animation_name(self) -> Optional[str]:
        return self._current.name if self._current else None
