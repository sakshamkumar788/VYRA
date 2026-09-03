from enum import Enum
from typing import Callable, Any, Dict, List


class InteractionEvent(Enum):
    CURSOR_ENTER = "cursor_enter"
    CURSOR_LEAVE = "cursor_leave"
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    DRAG_START = "drag_start"
    DRAG_MOVE = "drag_move"
    DRAG_END = "drag_end"
    PET = "pet"


class InteractionHandler:
    def __init__(self, on_event: Callable[[InteractionEvent, Any], None] = None):
        self._on_event = on_event
        self._listeners: Dict[InteractionEvent, List[Callable]] = {e: [] for e in InteractionEvent}

    def emit(self, event: InteractionEvent, data: Any = None):
        if callable(self._on_event):
            try:
                self._on_event(event, data)
            except Exception:
                pass
        for cb in self._listeners.get(event, []):
            try:
                cb(event, data)
            except Exception:
                pass

    def add_listener(self, event: InteractionEvent, callback: Callable[[InteractionEvent, Any], None]):
        if event in self._listeners:
            self._listeners[event].append(callback)
