from collections import deque
from datetime import datetime
from threading import Lock
from typing import Callable

from pynput import keyboard, mouse


class ActivityMonitor:
    """
    Monitors keyboard/mouse activity.

    This monitor records only activity timestamps.
    It does NOT store:
    - actual keystrokes
    - mouse coordinates
    - typed text
    - clicked content
    """

    ACTIVITY_WINDOW_SECONDS = 60

    def __init__(
        self,
        on_activity: Callable[[], None] | None = None,
    ) -> None:
        self.on_activity = on_activity

        self._lock = Lock()

        self._last_activity = datetime.now()

        self._activity_events: deque[datetime] = deque()

        self._running = False

        self._keyboard_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None

    def _record_activity(self, *args) -> None:
        """Record that keyboard/mouse activity occurred."""

        now = datetime.now()

        with self._lock:
            self._last_activity = now
            self._activity_events.append(now)

            self._remove_old_events(now)

        if self.on_activity is not None:
            self.on_activity()

    def _remove_old_events(
        self,
        now: datetime,
    ) -> None:
        """Remove activity events outside the tracking window."""

        cutoff = (
            now.timestamp()
            - self.ACTIVITY_WINDOW_SECONDS
        )

        while self._activity_events:
            oldest = self._activity_events[0]

            if oldest.timestamp() >= cutoff:
                break

            self._activity_events.popleft()

    def start(self) -> None:
        """Start keyboard and mouse monitoring."""

        if self._running:
            return

        self._running = True

        self._keyboard_listener = keyboard.Listener(
            on_press=self._record_activity,
        )

        self._mouse_listener = mouse.Listener(
            on_move=self._record_activity,
            on_click=self._record_activity,
            on_scroll=self._record_activity,
        )

        self._keyboard_listener.start()
        self._mouse_listener.start()

    def stop(self) -> None:
        """Stop keyboard and mouse monitoring."""

        self._running = False

        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def get_last_activity(self) -> datetime:
        """Return the time of the most recent input activity."""

        with self._lock:
            return self._last_activity

    def get_idle_seconds(self) -> float:
        """Return seconds since the last detected input."""

        last_activity = self.get_last_activity()

        return (
            datetime.now() - last_activity
        ).total_seconds()

    def get_activity_count(
        self,
        window_seconds: int = 60,
    ) -> int:
        """Return the number of input events in the recent window."""

        now = datetime.now()

        cutoff = (
            now.timestamp()
            - window_seconds
        )

        with self._lock:
            self._remove_old_events(now)

            return sum(
                1
                for event_time
                in self._activity_events
                if event_time.timestamp() >= cutoff
            )

    def is_idle(
        self,
        threshold_seconds: int = 300,
    ) -> bool:
        """Return True when input inactivity exceeds the threshold."""

        return (
            self.get_idle_seconds()
            >= threshold_seconds
        )

    def is_likely_focused(
        self,
        minimum_events: int = 20,
        window_seconds: int = 60,
    ) -> bool:
        """
        Return True when there has been sustained input activity.

        This is only a behavioral estimate.
        It does not claim to know the user's actual mental state.
        """

        if self.is_idle(10):
            return False

        activity_count = self.get_activity_count(
            window_seconds
        )

        return activity_count >= minimum_events