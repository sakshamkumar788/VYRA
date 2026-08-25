from dataclasses import dataclass

from intelligence.models import IntelligenceStory


@dataclass
class TechnologyRelevance:
    """Technology/research contribution to story relevance."""

    bonus: int
    reasons: list[str]


class TechnologyRelevanceEngine:
    """Scores technology and research relevance."""

    CATEGORY_BONUSES = {
        "indian_tech": 35,
        "ai": 30,
        "research": 30,
        "science": 25,
        "business": 15,
        "company": 15,
    }

    IMPORTANT_ENTITY_TYPES = {
        "technology",
        "research_topic",
    }

    def evaluate(
        self,
        story: IntelligenceStory,
    ) -> TechnologyRelevance:
        """Calculate technology/research relevance."""

        bonus = 0
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Category relevance
        # ---------------------------------------------------------

        category_bonus = self.CATEGORY_BONUSES.get(
            story.category.lower(),
            0,
        )

        if category_bonus:
            bonus += category_bonus

            reasons.append(
                f"technology category: {story.category}"
            )

        # ---------------------------------------------------------
        # Entity relevance
        # ---------------------------------------------------------

        seen_entities: set[str] = set()

        for entity in (
            getattr(story, "entities", None)
            or []
        ):
            entity_type = (
                entity.entity_type
                .strip()
                .lower()
            )

            if (
                entity_type
                not in self.IMPORTANT_ENTITY_TYPES
            ):
                continue

            entity_name = (
                entity.name
                .strip()
                .lower()
            )

            if entity_name in seen_entities:
                continue

            seen_entities.add(
                entity_name
            )

            entity_bonus = min(
                20,
                max(
                    0,
                    entity.relevance // 5,
                ),
            )

            bonus += entity_bonus

            reasons.append(
                f"technology/research interest: "
                f"{entity.name}"
            )

        # ---------------------------------------------------------
        # Important technology story
        # ---------------------------------------------------------

        if story.importance >= 80:
            bonus += 15
            reasons.append(
                "high technology/research importance"
            )

        return TechnologyRelevance(
            bonus=min(bonus, 80),
            reasons=reasons,
        )