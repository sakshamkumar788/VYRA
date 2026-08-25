from intelligence.feedback import (
    FeedbackProfile,
    FeedbackType,
)
from intelligence.models import IntelligenceStory


class IntelligenceFeedbackHandler:
    """Records user feedback about real intelligence stories."""

    def __init__(
        self,
        feedback_profile: FeedbackProfile,
    ) -> None:
        self.feedback_profile = feedback_profile

    def record_story_feedback(
        self,
        story: IntelligenceStory,
        feedback_type: str,
    ) -> None:
        """Record feedback using metadata from the story."""

        entity_names = [
            entity.name
            for entity in (
                getattr(story, "entities", None)
                or []
            )
        ]

        self.feedback_profile.record(
            feedback_type=feedback_type,
            story_category=story.category,
            entity_names=entity_names,
            source=story.source,
        )

        self.feedback_profile.rebuild_preferences()