from dataclasses import dataclass

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

    def build(
        self,
        stories: list[IntelligenceStory],
        max_per_section: int = 3,
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