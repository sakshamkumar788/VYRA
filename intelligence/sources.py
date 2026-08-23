from abc import ABC, abstractmethod

from intelligence.models import IntelligenceStory


class IntelligenceSource(ABC):
    """Base interface for all VYRA intelligence sources."""

    @abstractmethod
    def fetch(
        self,
    ) -> list[IntelligenceStory]:
        """Fetch normalized intelligence stories."""

        raise NotImplementedError