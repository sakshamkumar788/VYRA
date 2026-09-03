from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt
from .renderer import CatRenderer
from .state import CatState
from .behavior import CatBehavior
from .interaction import InteractionHandler, InteractionEvent
from .autonomy import AutonomyController


class CatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.move(200, 200)

        self.renderer = CatRenderer(self)
        # Size window tightly around renderer sprite
        self.resize(self.renderer.width(), self.renderer.height())
        self.renderer.setGeometry(0, 0, self.width(), self.height())

        self._drag_pos = None
        self._prev_state = CatState.IDLE

        def _on_state_change(new_state, old_state):
            self.state = new_state
            self.renderer.set_state(new_state)
            if hasattr(self, 'autonomy'):
                self.autonomy.on_behavior_state_change(new_state, old_state)

        self.behavior = CatBehavior(initial_state=CatState.IDLE, on_state_change=_on_state_change)
        self.state = self.behavior.state

        self.interaction = InteractionHandler(on_event=self._handle_interaction)

        self.autonomy = AutonomyController(self.behavior, parent=self)
        self.autonomy.start()

        # Toggle sleep for testing with 'S' key
        # Close with Escape

    def set_state(self, state: CatState):
        # Request state transition via behavior controller
        self.behavior.request_state(state)

    def _handle_interaction(self, event: InteractionEvent, data):
        # Map interaction events to CatBehavior state requests
        # Sleep safety: do not allow any interaction to wake a sleeping CAT
        if self.behavior.state == CatState.SLEEP:
            return

        if event == InteractionEvent.CURSOR_ENTER:
            self.behavior.request_state(CatState.LOOK)

        elif event == InteractionEvent.CURSOR_LEAVE:
            if self.behavior.state == CatState.LOOK:
                self.behavior.request_state(CatState.IDLE)

        elif event == InteractionEvent.PET:
            self.behavior.request_state(CatState.PET)

        # DRAG_START / DRAG_END / MOUSE_PRESS / MOUSE_RELEASE are handled
        # by existing window drag logic; events are emitted for future use.
        # No additional state changes here to preserve existing dragging.

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.interaction.emit(InteractionEvent.MOUSE_PRESS, event)
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._prev_state = self.state
            self.set_state(CatState.DRAGGED)
            self.interaction.emit(InteractionEvent.DRAG_START, event)
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.interaction.emit(InteractionEvent.DRAG_MOVE, event)
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_pos is not None:
            self.interaction.emit(InteractionEvent.MOUSE_RELEASE, event)
            self.interaction.emit(InteractionEvent.DRAG_END, event)
            self._drag_pos = None
            # return to previous non-drag state
            self.set_state(self._prev_state if self._prev_state != CatState.DRAGGED else CatState.IDLE)
            event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            QApplication.instance().quit()
        elif key == Qt.Key_S:
            # Toggle sleep for manual test
            if self.state == CatState.SLEEP:
                self.set_state(CatState.IDLE)
            else:
                self.set_state(CatState.SLEEP)
        elif key == Qt.Key_R:
            # Right-click style close via key
            QApplication.instance().quit()
        super().keyPressEvent(event)

    def enterEvent(self, event):
        self.interaction.emit(InteractionEvent.CURSOR_ENTER, event)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.interaction.emit(InteractionEvent.CURSOR_LEAVE, event)
        super().leaveEvent(event)

    def closeEvent(self, event):
        if hasattr(self, 'autonomy'):
            self.autonomy.stop()
        super().closeEvent(event)

    def contextMenuEvent(self, event):
        # Right click to close
        QApplication.instance().quit()
