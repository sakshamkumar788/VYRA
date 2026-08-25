from dataclasses import dataclass

from intelligence.entities import EntityType, StoryEntity

from intelligence.feedback import FeedbackProfile

from intelligence.models import (
    IntelligenceStory,
    StoryUrgency,
)
from location.models import ImportantPlace



@dataclass
class StoryScore:
    """Final evaluation of an intelligence story."""

    score: int
    reason: str
    recommended_action: str


class IntelligenceScorer:
    """Scores information against VYRA's personal context."""

    def __init__(
        self,
        feedback_profile: FeedbackProfile | None = None,
    ) -> None:
        self.feedback_profile = (
            feedback_profile
            or FeedbackProfile()
        )

    INTEREST_ENTITY_TYPES = {
        EntityType.TECHNOLOGY,
        EntityType.RESEARCH_TOPIC,
    }

    ENTITY_MAX_BONUS = 40

    def _entity_bonus(
        self,
        story: IntelligenceStory,
    ) -> tuple[int, list[str]]:
        """
        Calculate a bounded bonus from user-interest entities.

        Technology and research entities are treated as personally
        interesting, but location entities are deliberately ignored here
        because location relevance is already handled elsewhere.
        """

        entities = getattr(story, "entities", None) or []

        relevant_entities: list[StoryEntity] = []
        seen: set[tuple[str, str]] = set()

        for entity in entities:
            if entity.entity_type not in self.INTEREST_ENTITY_TYPES:
                continue

            key = (
                entity.name.strip().lower(),
                entity.entity_type,
            )

            if key in seen:
                # Avoid double-counting duplicate/aliased entities.
                for index, existing in enumerate(
                    relevant_entities
                ):
                    existing_key = (
                        existing.name.strip().lower(),
                        existing.entity_type,
                    )

                    if existing_key == key:
                        if (
                            entity.relevance
                            > existing.relevance
                        ):
                            relevant_entities[index] = entity

                        break

                continue

            seen.add(key)
            relevant_entities.append(entity)

        if not relevant_entities:
            return 0, []

        max_relevance = max(
            entity.relevance
            for entity in relevant_entities
        )

        distinct_bonus = (
            min(len(relevant_entities), 3) * 5
        )

        bonus = min(
            self.ENTITY_MAX_BONUS,
            (max_relevance // 2) + distinct_bonus,
        )

        names = [
            entity.name
            for entity in relevant_entities[:3]
        ]

        reason = (
            "matches user tech/research interest: "
            + ", ".join(names)
        )

        return bonus, [reason]
    
    def _feedback_bonus(
        self,
        story: IntelligenceStory,
    ) -> tuple[int, list[str]]:
        """Calculate bounded personalization from user feedback."""

        bonus = 0
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Category preference
        # ---------------------------------------------------------

        category = (
            story.category.strip().lower()
        )

        category_bonus = (
            self.feedback_profile
            .category_bonus(category)
        )

        if category_bonus:
            bonus += category_bonus

            reasons.append(
                f"user category preference: "
                f"{category_bonus:+d}"
            )

        # ---------------------------------------------------------
        # Entity preferences
        # ---------------------------------------------------------

        seen_entities: set[str] = set()

        for entity in (
            getattr(story, "entities", None)
            or []
        ):
            entity_name = (
                entity.name.strip().lower()
            )

            if not entity_name:
                continue

            if entity_name in seen_entities:
                continue

            seen_entities.add(entity_name)

            entity_bonus = (
                self.feedback_profile
                .entity_bonus(entity_name)
            )

            if entity_bonus:
                bonus += entity_bonus

                reasons.append(
                    f"user entity preference: "
                    f"{entity.name} "
                    f"{entity_bonus:+d}"
                )

        # ---------------------------------------------------------
        # Source preference
        # ---------------------------------------------------------

        if story.source:
            source_bonus = (
                self.feedback_profile
                .source_bonus(story.source)
            )

            if source_bonus:
                bonus += source_bonus

                reasons.append(
                    f"user source preference: "
                    f"{source_bonus:+d}"
                )

        # ---------------------------------------------------------
        # Keep personalization bounded.
        # ---------------------------------------------------------

        bonus = max(
            -50,
            min(50, bonus),
        )

        return bonus, reasons

    def score(
        self,
        story: IntelligenceStory,
        current_location: str | None,
        important_places: list[ImportantPlace],
    ) -> StoryScore:
        """Calculate a first-pass intelligence score."""

        score = 0
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Base importance
        # ---------------------------------------------------------

        score += story.importance

        if story.importance >= 80:
            reasons.append("high importance")

        # ---------------------------------------------------------
        # Severity
        # ---------------------------------------------------------

        score += story.severity

        if story.severity >= 70:
            reasons.append("high severity")

        # ---------------------------------------------------------
        # Source trust
        # ---------------------------------------------------------

        if story.source_trust < 50:
            score -= 25
            reasons.append("low source trust")

        elif story.source_trust >= 85:
            score += 15
            reasons.append("high source trust")

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        if story.confidence < 50:
            score -= 30
            reasons.append("low confidence")

        elif story.confidence >= 80:
            score += 10
            reasons.append("high confidence")

        # ---------------------------------------------------------
        # Current location
        # ---------------------------------------------------------

        if (
            current_location
            and story.location_name
            and story.location_name.lower()
            == current_location.lower()
        ):
            score += 80
            reasons.append(
                "affects current location"
            )

        # ---------------------------------------------------------
        # Personally important locations
        # ---------------------------------------------------------

        for place in important_places:
            if (
                place.city
                and story.location_name
                and place.city.lower()
                == story.location_name.lower()
            ):
                score += place.importance

                reasons.append(
                    f"affects important place: "
                    f"{place.place_type}"
                )

        # ---------------------------------------------------------
        # Personal relevance
        # ---------------------------------------------------------

        score += story.personal_relevance

        if story.personal_relevance >= 60:
            reasons.append("personally relevant")

        # ---------------------------------------------------------
        # Learned user preferences
        # ---------------------------------------------------------

        feedback_bonus, feedback_reasons = (
            self._feedback_bonus(story)
        )

        score += feedback_bonus
        reasons.extend(feedback_reasons)

        # ---------------------------------------------------------
        # Recognized user-interest entities
        # ---------------------------------------------------------

        entity_bonus, entity_reasons = (
            self._entity_bonus(story)
        )

        score += entity_bonus
        reasons.extend(entity_reasons)

        # ---------------------------------------------------------
        # Novelty
        # ---------------------------------------------------------

        score += story.novelty

        # ---------------------------------------------------------
        # Urgency
        # ---------------------------------------------------------

        if story.urgency == StoryUrgency.IMMEDIATE:
            score += 100
            reasons.append("immediate urgency")

        elif story.urgency == StoryUrgency.SOON:
            score += 50
            reasons.append("time-sensitive")

        # ---------------------------------------------------------
        # Final action
        # ---------------------------------------------------------

        if score >= 250:
            action = "tell_now"

        elif score >= 170:
            action = "tell_soon"

        elif score >= 100:
            action = "mention_later"

        elif score >= 50:
            action = "on_demand"

        else:
            action = "ignore"

        return StoryScore(
            score=score,
            reason="; ".join(reasons),
            recommended_action=action,
        )


if __name__ == "__main__":
    from types import SimpleNamespace

    from intelligence.entities import EntityType, StoryEntity
    from intelligence.models import IntelligenceStory, StoryUrgency

    scorer = IntelligenceScorer()

    # ---------------------------------------------------------
    # a. AI/research story gets extra relevance
    # ---------------------------------------------------------

    base_story = IntelligenceStory(
        title="Some story",
        summary="Nothing specific",
        source="test",
        importance=40,
        severity=10,
        confidence=60,
        personal_relevance=30,
        novelty=50,
        source_trust=75,
        urgency=StoryUrgency.NORMAL,
        entities=[],
    )

    ai_story = IntelligenceStory(
        title="AI model breakthrough",
        summary="Machine learning improves cloud computing",
        source="test",
        importance=40,
        severity=10,
        confidence=60,
        personal_relevance=30,
        novelty=50,
        source_trust=75,
        urgency=StoryUrgency.NORMAL,
        entities=[
            StoryEntity(
                name="AI",
                entity_type=EntityType.TECHNOLOGY,
                confidence=98,
                relevance=85,
            ),
            StoryEntity(
                name="Machine Learning",
                entity_type=EntityType.RESEARCH_TOPIC,
                confidence=90,
                relevance=75,
            ),
        ],
    )

    base_score = scorer.score(base_story, None, [])
    ai_score = scorer.score(ai_story, None, [])

    print("a. Base story score:", base_score.score)
    print("   AI story score:", ai_score.score)
    print("   AI action:", ai_score.recommended_action)
    print()

    assert ai_score.score > base_score.score

    # ---------------------------------------------------------
    # b. Normal unrelated story does not get entity bonus
    # ---------------------------------------------------------

    unrelated_story = IntelligenceStory(
        title="Local fair",
        summary="Small event in Paris",
        source="test",
        importance=10,
        severity=0,
        confidence=50,
        personal_relevance=0,
        novelty=50,
        source_trust=55,
        urgency=StoryUrgency.NORMAL,
        location_name="Paris",
        entities=[
            StoryEntity(
                name="Paris",
                entity_type=EntityType.LOCATION,
                confidence=95,
                relevance=60,
            )
        ],
    )

    unrelated_score = scorer.score(
        unrelated_story,
        "Jalandhar",
        [],
    )

    print("b. Unrelated story score:", unrelated_score.score)
    print("   Unrelated action:", unrelated_score.recommended_action)
    print()

    assert unrelated_score.recommended_action in {
        "ignore",
        "on_demand",
        "mention_later",
    }

    # ---------------------------------------------------------
    # c. Serious Jalandhar story still becomes highly important
    # ---------------------------------------------------------

    home = SimpleNamespace(
        city="Jalandhar",
        importance=100,
        place_type="home",
    )

    jalandhar_story = IntelligenceStory(
        title="Flood warning in Jalandhar",
        summary="Severe flooding near home",
        source="NDMA",
        importance=70,
        severity=80,
        confidence=80,
        personal_relevance=70,
        novelty=60,
        source_trust=85,
        urgency=StoryUrgency.SOON,
        location_name="Jalandhar",
        entities=[
            StoryEntity(
                name="Jalandhar",
                entity_type=EntityType.LOCATION,
                confidence=95,
                relevance=50,
            )
        ],
    )

    jalandhar_score = scorer.score(
        jalandhar_story,
        "Delhi",
        [home],
    )

    print("c. Jalandhar story score:", jalandhar_score.score)
    print("   Jalandhar action:", jalandhar_score.recommended_action)
    print()

    assert jalandhar_score.recommended_action in {
        "tell_now",
        "tell_soon",
    }

    # ---------------------------------------------------------
    # d. Random location mention does not automatically
    #    become highly important
    # ---------------------------------------------------------

    random_location_story = IntelligenceStory(
        title="Festival in Paris",
        summary="Minor local event",
        source="community",
        importance=10,
        severity=0,
        confidence=50,
        personal_relevance=0,
        novelty=50,
        source_trust=55,
        urgency=StoryUrgency.NORMAL,
        location_name="Paris",
        entities=[
            StoryEntity(
                name="Paris",
                entity_type=EntityType.LOCATION,
                confidence=90,
                relevance=50,
            )
        ],
    )

    random_score = scorer.score(
        random_location_story,
        "Jalandhar",
        [],
    )

    print("d. Random location score:", random_score.score)
    print("   Random location action:", random_score.recommended_action)
    print()

    assert random_score.recommended_action in {
        "ignore",
        "on_demand",
        "mention_later",
    }

    print("All scoring tests passed.")