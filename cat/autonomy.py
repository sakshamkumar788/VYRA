import random
from PySide6.QtCore import QObject, QTimer
from .state import CatState


class AutonomyController(QObject):
    def __init__(self, behavior, parent=None):
        super().__init__(parent)
        self.behavior = behavior
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(5000)
        self._idle_timer.timeout.connect(self._try_autonomous_look)
        self._look_duration_timer = QTimer(self)
        self._look_duration_timer.setSingleShot(True)
        self._look_duration_timer.timeout.connect(self._return_to_idle)
        self._autonomous_look_active = False

    def start(self):
        if not self._idle_timer.isActive():
            self._idle_timer.start()

    def stop(self):
        self._idle_timer.stop()
        self._look_duration_timer.stop()
        self._autonomous_look_active = False

    def on_behavior_state_change(self, new_state, old_state):
        # Cancel autonomous LOOK if user interrupted it
        if old_state == CatState.LOOK and new_state != CatState.IDLE:
            # User changed state away from LOOK, cancel pending return
            if self._look_duration_timer.isActive():
                self._look_duration_timer.stop()
            self._autonomous_look_active = False
        # Sleep entered: cancel all autonomy
        if new_state == CatState.SLEEP:
            self.stop()
        # If we left LOOK without returning via autonomy, ensure flag cleared
        if old_state == CatState.LOOK and new_state != CatState.IDLE:
            self._autonomous_look_active = False

    def _try_autonomous_look(self):
        # Sleep safety
        if self.behavior.state == CatState.SLEEP:
            return
        # Only act when truly idle
        if self.behavior.state != CatState.IDLE:
            return
        # Request LOOK
        changed = self.behavior.request_state(CatState.LOOK)
        if changed:
            self._autonomous_look_active = True
            # Wait brief time then return to idle
            duration = random.randint(800, 1500)
            self._look_duration_timer.start(duration)
        else:
            # No change, schedule next check with random jitter
            self._reschedule_idle_timer()

    def _return_to_idle(self):
        # Only return if still in LOOK and autonomous LOOK is active
        if self._autonomous_look_active and self.behavior.state == CatState.LOOK:
            self.behavior.request_state(CatState.IDLE)
            self._autonomous_look_active = False
        # Reschedule next idle check
        self._reschedule_idle_timer()

    def _reschedule_idle_timer(self):
        # Randomize interval to avoid hyperactive behavior
        interval = random.randint(8000, 15000)
        self._idle_timer.setInterval(interval)
        if not self._idle_timer.isActive():
            self._idle_timer.start()
