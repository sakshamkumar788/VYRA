from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BriefingHistory:
    """Tracks recent briefing topics and wording."""

    recent_messages: list[str] = field(
        default_factory=list
    )

    recent_topics: list[str] = field(
        default_factory=list
    )

    last_briefing_time: datetime | None = None


class BriefingNoveltyFilter:
    """Prevents VYRA from repeatedly producing the same briefing."""

    MAX_HISTORY = 10

    def __init__(self) -> None:
        self.history = BriefingHistory()

    def was_topic_recently_used(
        self,
        topic: str,
    ) -> bool:
        """Check whether a topic was recently used."""

        return topic in self.history.recent_topics

    def record(
        self,
        message: str,
        topics: list[str],
    ) -> None:
        """Record a delivered briefing."""

        self.history.recent_messages.append(
            message
        )

        self.history.recent_topics.extend(
            topics
        )

        self.history.recent_messages = (
            self.history.recent_messages[
                -self.MAX_HISTORY:
            ]
        )

        self.history.recent_topics = (
            self.history.recent_topics[
                -self.MAX_HISTORY:
            ]
        )

        self.history.last_briefing_time = (
            datetime.now()
        )