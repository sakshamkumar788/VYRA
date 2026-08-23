from datetime import datetime

from vyra_calendar.base import CalendarProvider
from vyra_calendar.models import CalendarEvent


class LocalCalendarProvider(CalendarProvider):
    """Temporary in-memory calendar provider for development/testing."""

    def __init__(
        self,
        events: list[CalendarEvent] | None = None,
    ) -> None:
        self.events = events or []

    def get_events(
        self,
        start: datetime,
        end: datetime,
    ) -> list[CalendarEvent]:
        """Return events overlapping the requested time range."""

        matching: list[CalendarEvent] = []

        for event in self.events:
            event_end = (
                event.end_time
                if event.end_time is not None
                else event.start_time
            )

            if event_end < start:
                continue

            if event.start_time > end:
                continue

            matching.append(event)

        return sorted(
            matching,
            key=lambda event: event.start_time,
        )