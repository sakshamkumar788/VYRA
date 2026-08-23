from dataclasses import dataclass
from datetime import datetime


@dataclass
class CalendarEvent:
    """A normalized calendar event."""

    title: str
    start_time: datetime
    end_time: datetime | None = None

    location: str | None = None
    description: str | None = None

    all_day: bool = False