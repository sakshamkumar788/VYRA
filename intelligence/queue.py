from dataclasses import dataclass
from datetime import datetime

from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority

from memory.database import (
    save_intelligence_queue_item,
    load_intelligence_queue_items,
    delete_intelligence_queue_item,
    clear_intelligence_queue,
    story_identity_delivered,
)


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
        self._load_from_db()

    def _load_from_db(self) -> None:
        """Load persisted queue items into memory, skipping delivered stories."""
        try:
            rows = load_intelligence_queue_items()
        except Exception:
            return

        items = []
        for row in rows:
            story_identity = row.get("story_identity")
            # Skip if story already delivered
            try:
                if story_identity_delivered(story_identity):
                    # Remove stale queue entry
                    try:
                        delete_intelligence_queue_item(story_identity, row.get("priority"))
                    except Exception:
                        pass
                    continue
            except Exception:
                pass

            # Parse dates safely
            added_at_str = row.get("added_at")
            added_at = None
            try:
                added_at = datetime.fromisoformat(added_at_str) if added_at_str else datetime.now()
            except Exception:
                added_at = datetime.now()

            published_at_str = row.get("published_at")
            published_at = None
            try:
                published_at = datetime.fromisoformat(published_at_str) if published_at_str else None
            except Exception:
                published_at = None

            story = IntelligenceStory(
                title=row.get("title") or "",
                summary=row.get("summary") or "",
                source=row.get("source"),
                url=row.get("url"),
                category=row.get("category") or "other",
                published_at=published_at,
            )
            priority = row.get("priority") or IntelligencePriority.INTERESTING
            items.append(
                QueuedIntelligence(
                    story=story,
                    priority=priority,
                    added_at=added_at,
                )
            )
        # Preserve ordering on load
        priority_order = {
            IntelligencePriority.IMPORTANT: 0,
            IntelligencePriority.INTERESTING: 1,
        }
        items.sort(key=lambda it: (priority_order.get(it.priority, 99), it.added_at))
        self._items = items

    @staticmethod
    def _story_identity(story: IntelligenceStory) -> str:
        if story.url:
            return f"url:{story.url}"
        return f"title:{story.title.strip().lower()}"

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

        added_at_dt = datetime.now()
        queued = QueuedIntelligence(
            story=story,
            priority=priority,
            added_at=added_at_dt,
        )
        self._items.append(queued)

        # Persist with graceful failure
        try:
            story_identity = self._story_identity(story)
            published_at_str = (
                story.published_at.isoformat()
                if story.published_at
                else None
            )
            save_intelligence_queue_item(
                story_identity=story_identity,
                title=story.title,
                summary=story.summary,
                url=story.url,
                source=story.source,
                category=story.category,
                published_at=published_at_str,
                priority=priority,
                added_at=added_at_dt.isoformat(),
            )
        except Exception:
            # Keep in-memory queue correct, do not crash
            pass

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

        identity = self._story_identity(story)
        # Find matching items to know priority
        removed_priorities = []
        kept = []
        for item in self._items:
            if self._same_story(item.story, story):
                removed_priorities.append(item.priority)
            else:
                kept.append(item)
        self._items = kept

        # Delete persisted rows for removed identities
        try:
            for prio in set(removed_priorities):
                delete_intelligence_queue_item(identity, prio)
            # Fallback: try both priorities if we didn't find in memory
            if not removed_priorities:
                for prio in (IntelligencePriority.IMPORTANT, IntelligencePriority.INTERESTING):
                    try:
                        delete_intelligence_queue_item(identity, prio)
                    except Exception:
                        pass
        except Exception:
            pass

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
        try:
            clear_intelligence_queue()
        except Exception:
            pass

    def __len__(self) -> int:
        return len(self._items)