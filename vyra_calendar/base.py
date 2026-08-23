from abc import ABC, abstractmethod
from datetime import datetime

from vyra_calendar.models import CalendarEvent


class CalendarProvider(ABC):
    """Base interface for calendar providers."""

    @abstractmethod
    def get_events(
        self,
        start: datetime,
        end: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within the requested range."""

        raise NotImplementedError