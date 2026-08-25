from dataclasses import dataclass
from datetime import datetime

from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority


@dataclass
class QueuedIntelligence:
    """A story waiting for an appropriate delivery moment."""

    story: IntelligenceStory
    priority: str
    added_at: datetime


class IntelligenceQueue:
    """In-memory queue for intelligence VYRA may surface later."""

    def __init__(self) -> None:
        self._items: list[
            QueuedIntelligence
        ] = []

    def add(
        self,
        story: IntelligenceStory,
        priority: str,
    ) -> None:
        """Add a story to the queue."""

        if priority not in {
            IntelligencePriority.IMPORTANT,
            IntelligencePriority.INTERESTING,
        }:
            return

        if self.contains(story):
            return

        self._items.append(
            QueuedIntelligence(
                story=story,
                priority=priority,
                added_at=datetime.now(),
            )
        )

    def contains(
        self,
        story: IntelligenceStory,
    ) -> bool:
        """Return True if the story is already queued."""

        if story.url:
            return any(
                item.story.url == story.url
                for item in self._items
                if item.story.url
            )

        return any(
            item.story.title.strip().lower()
            == story.title.strip().lower()
            for item in self._items
        )

    def get_pending(
        self,
        limit: int = 5,
    ) -> list[QueuedIntelligence]:
        """Return queued stories by priority."""

        priority_order = {
            IntelligencePriority.IMPORTANT: 0,
            IntelligencePriority.INTERESTING: 1,
        }

        ordered = sorted(
            self._items,
            key=lambda item: (
                priority_order.get(
                    item.priority,
                    99,
                ),
                item.added_at,
            ),
        )

        return ordered[:limit]

    def remove(
        self,
        story: IntelligenceStory,
    ) -> None:
        """Remove one story from the queue."""

        self._items = [
            item
            for item in self._items
            if not self._same_story(
                item.story,
                story,
            )
        ]

    def _same_story(
        self,
        first: IntelligenceStory,
        second: IntelligenceStory,
    ) -> bool:
        """Compare two stories."""

        if first.url and second.url:
            return first.url == second.url

        return (
            first.title.strip().lower()
            == second.title.strip().lower()
        )

    def clear(self) -> None:
        """Clear the queue."""

        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)