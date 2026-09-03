from pathlib import Path
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from .state import CatState
from .animations.animation_player import AnimationPlayer


class CatRenderer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.state = CatState.IDLE
        self._phase = 0

        assets_root = Path(__file__).parent / "assets" / "sprites"
        self.player = AnimationPlayer(assets_root, target_height=120)

        # Refresh paint for bobbing and frame changes
        from PySide6.QtCore import QTimer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.update)
        self._refresh_timer.start(33)  # ~30 FPS
        # Start with idle animation
        self.player.play("idle", loop=True)

        # Set initial size from first frame if available
        frame = self.player.current_frame
        if frame and not frame.isNull():
            self.setFixedSize(frame.width(), frame.height())
        else:
            self.setFixedSize(1, 1)

    def set_state(self, state: CatState):
        if self.state == state:
            return
        self.state = state
        # Map state to animation name, keep current animation for drag
        if state == CatState.DRAGGED:
            self.update()
            return
        anim_map = {
            CatState.IDLE: "idle",
            CatState.SLEEP: "sleep",
        }
        anim_name = anim_map.get(state, "idle")
        if anim_name == "sleep":
            clip = self.player.load_animation("sleep")
            if clip.is_empty():
                anim_name = "idle"
        self.player.play(anim_name, loop=True)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Clear transparent
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        frame = self.player.current_frame
        if frame is None or frame.isNull():
            return

        w = self.width()
        h = self.height()
        pix_w = frame.width()
        pix_h = frame.height()

        # Center pixmap, no artificial translation
        x = (w - pix_w) // 2
        y = (h - pix_h) // 2

        if self.state == CatState.SLEEP:
            painter.setOpacity(0.85)
        else:
            painter.setOpacity(1.0)

        painter.drawPixmap(x, y, frame)
