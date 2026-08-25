from dataclasses import dataclass

from intelligence.models import IntelligenceStory
from intelligence.profile import IntelligenceProfile


@dataclass
class IntelligenceSelection:
    """Additional contextual relevance for one story."""

    bonus: int
    reasons: list[str]


class IntelligenceSelector:
    """Applies personal geography and topic preferences."""

    def __init__(
        self,
        profile: IntelligenceProfile | None = None,
    ) -> None:
        self.profile = (
            profile
            or IntelligenceProfile()
        )

    def evaluate(
        self,
        story: IntelligenceStory,
    ) -> IntelligenceSelection:
        """Calculate contextual selection bonuses."""

        bonus = 0
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Location
        # ---------------------------------------------------------

        if story.location_name:
            location = (
                story.location_name
                .strip()
                .lower()
            )

            if location in self.profile.important_regions:
                bonus += (
                    self.profile.local_importance_bonus
                )

                reasons.append(
                    f"important region: {story.location_name}"
                )

        # ---------------------------------------------------------
        # Technology / research interests
        # ---------------------------------------------------------

        for entity in (
            getattr(story, "entities", None)
            or []
        ):
            name = (
                entity.name
                .strip()
                .lower()
                .replace(" ", "_")
            )

            if name in self.profile.important_topics:
                bonus += (
                    self.profile.personal_topic_bonus
                )

                reasons.append(
                    f"matches interest: {entity.name}"
                )

        # ---------------------------------------------------------
        # Indian technology
        # ---------------------------------------------------------

        category = (
            story.category
            .strip()
            .lower()
        )

        if category == "indian_tech":
            bonus += (
                self.profile.indian_tech_bonus
            )

            reasons.append(
                "Indian technology"
            )

        return IntelligenceSelection(
            bonus=bonus,
            reasons=reasons,
        )