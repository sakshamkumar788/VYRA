from dataclasses import dataclass

from intelligence.feedback import FeedbackProfile
from intelligence.models import IntelligenceStory


@dataclass
class CurrentAffairsSection:
    """One section of a current-affairs response."""

    name: str
    stories: list[IntelligenceStory]


@dataclass
class CurrentAffairsBrief:
    """Structured current-affairs result."""

    sections: list[CurrentAffairsSection]


class CurrentAffairsEngine:
    """
    Builds an on-demand current-affairs brief from already
    evaluated intelligence stories.

    This engine does not fetch news itself.
    Fetching belongs to the intelligence ingestion layer.
    """

    SECTION_ORDER = [
        "local",
        "india",
        "indian_tech",
        "ai",
        "research",
        "business",
        "world",
    ]

    SECTION_NAMES = {
        "local": "Local",
        "india": "India",
        "indian_tech": "Indian Tech",
        "ai": "AI & Technology",
        "research": "Research & Science",
        "business": "Business & Companies",
        "world": "World",
    }

    def _feedback_score(self, story: IntelligenceStory, profile: FeedbackProfile | None) -> int:
        if not profile:
            return 0
        score = 0
        cat = story.category.strip().lower()
        score += profile.category_bonus(cat)

        # Entity feedback, avoid duplicates
        seen = set()
        entity_total = 0
        for ent in story.entities or []:
            name = getattr(ent, "name", None)
            if not name:
                continue
            key = name.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            entity_total += profile.entity_bonus(key)
        # Bound entity contribution
        entity_total = max(-20, min(20, entity_total))
        score += entity_total

        # Source feedback, bounded to avoid domination
        if story.source:
            src_bonus = profile.source_bonus(story.source.strip().lower())
            src_bonus = max(-10, min(10, src_bonus))
            score += src_bonus

        return score

    def build(
        self,
        stories: list[IntelligenceStory],
        max_per_section: int = 3,
        feedback_profile: FeedbackProfile | None = None,
    ) -> CurrentAffairsBrief:
        """Group relevant stories into current-affairs sections."""

        grouped: dict[
            str,
            list[IntelligenceStory]
        ] = {
            category: []
            for category in self.SECTION_ORDER
        }

        for story in stories:
            category = (
                story.category
                .strip()
                .lower()
            )

            if category not in grouped:
                continue

            grouped[category].append(story)

        sections: list[CurrentAffairsSection] = []

        for category in self.SECTION_ORDER:
            section_stories = grouped[category]

            if not section_stories:
                continue

            section_stories = sorted(
                section_stories,
                key=lambda story: (
                    story.importance,
                    story.severity,
                    story.novelty,
                    self._feedback_score(story, feedback_profile),
                ),
                reverse=True,
            )

            sections.append(
                CurrentAffairsSection(
                    name=self.SECTION_NAMES[category],
                    stories=section_stories[
                        :max_per_section
                    ],
                )
            )

        return CurrentAffairsBrief(
            sections=sections
        )