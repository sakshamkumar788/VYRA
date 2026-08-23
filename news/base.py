from abc import ABC, abstractmethod

from news.models import NewsItem


class NewsProvider(ABC):
    """Base interface for news providers."""

    @abstractmethod
    def get_latest(
        self,
        limit: int = 5,
    ) -> list[NewsItem]:
        """Return the latest available news items."""

        raise NotImplementedError