from dataclasses import dataclass
from datetime import datetime

from intelligence.feedback import FeedbackProfile
from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority
from intelligence.queue import QueuedIntelligence


@dataclass
class DiscoveryCandidate:
    """A queued story that may be worth spontaneously surfacing."""

    story: IntelligenceStory
    score: int
    reason: str


class DiscoveryEngine:
    """Selects interesting queued stories for spontaneous discovery."""

    MINIMUM_SCORE = 70

    INTERESTING_BASE_SCORE = 40
    IMPORTANT_BASE_SCORE = 60

    MAX_CANDIDATES = 3

    MIN_FEEDBACK_CONTRIBUTION = -30
    MAX_FEEDBACK_CONTRIBUTION = 30

    MIN_ENTITY_CONTRIBUTION = -20
    MAX_ENTITY_CONTRIBUTION = 20

    DISCOVERY_FRESHNESS_HALF_LIFE_HOURS = 24

    def __init__(
        self,
        feedback_profile: FeedbackProfile | None = None,
    ) -> None:
        self.feedback_profile = (
            feedback_profile
            if feedback_profile is not None
            else FeedbackProfile()
        )
        self._discovered_ids: set[str] = set()

    def _story_identity(
        self,
        story: IntelligenceStory,
    ) -> str:
        """Return a stable identity for repetition suppression."""

        url = (story.url or "").strip()

        if url:
            return f"url:{url}"

        return f"title:{story.title.strip().lower()}"

    def mark_discovered(
        self,
        story: IntelligenceStory,
    ) -> None:
        """Record that a story has already been surfaced."""

        self._discovered_ids.add(
            self._story_identity(story)
        )

    def has_been_discovered(
        self,
        story: IntelligenceStory,
    ) -> bool:
        """Return True if this story was already surfaced."""

        return (
            self._story_identity(story)
            in self._discovered_ids
        )

    def clear_discovery_history(self) -> None:
        """Forget recently surfaced discovery identities."""

        self._discovered_ids.clear()

    def _freshness_factor(
        self,
        published_at: datetime | None,
        now: datetime,
    ) -> float:
        """
        Return a decay factor based on story age.

        Uses exponential half-life decay:
            0 hours   → 1.0
            24 hours  → 0.5
            48 hours  → 0.25
            72 hours  → 0.125

        Future timestamps are treated as age zero.
        Missing timestamps are treated as neutral (0.5).
        """

        if published_at is None:
            return 0.5

        age_seconds = max(
            0.0,
            (now - published_at).total_seconds(),
        )

        age_hours = age_seconds / 3600.0

        factor = 0.5 ** (
            age_hours
            / self.DISCOVERY_FRESHNESS_HALF_LIFE_HOURS
        )

        return max(0.0, min(1.0, factor))

    def evaluate(
        self,
        items: list[QueuedIntelligence],
        now: datetime | None = None,
    ) -> list[DiscoveryCandidate]:
        """Evaluate queued stories for discovery."""

        if now is None:
            now = datetime.now()

        candidates: list[DiscoveryCandidate] = []

        for item in items:
            story = item.story

            if self.has_been_discovered(story):
                continue

            score = 0
            reasons: list[str] = []

            # Priority
            if item.priority == IntelligencePriority.IMPORTANT:
                score += self.IMPORTANT_BASE_SCORE

            elif item.priority == IntelligencePriority.INTERESTING:
                score += self.INTERESTING_BASE_SCORE

            # Importance
            score += story.importance // 2

            if story.importance >= 70:
                reasons.append("high importance")

            # Novelty
            score += story.novelty // 2

            if story.novelty >= 80:
                reasons.append("high novelty")

            # Personal relevance
            score += story.personal_relevance // 2

            if story.personal_relevance >= 60:
                reasons.append("personally relevant")

            # Confidence
            if story.confidence >= 80:
                score += 10
                reasons.append("high confidence")

            elif story.confidence < 50:
                score -= 20
                reasons.append("low confidence")

            feedback_score, feedback_reasons = (
                self._feedback_contribution(story)
            )
            score += feedback_score
            reasons.extend(feedback_reasons)

            # Freshness
            freshness_factor = self._freshness_factor(
                story.published_at,
                now,
            )
            freshness_contribution = int(
                20 * freshness_factor
            )
            score += freshness_contribution

            if freshness_contribution >= 15:
                reasons.append("fresh")

            # Minimum threshold
            if score < self.MINIMUM_SCORE:
                continue

            if not reasons:
                reasons.append("interesting discovery")

            candidates.append(
                DiscoveryCandidate(
                    story=story,
                    score=score,
                    reason="; ".join(reasons),
                )
            )

        candidates.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        return candidates[: self.MAX_CANDIDATES]

    def _feedback_contribution(
        self,
        story: IntelligenceStory,
    ) -> tuple[int, list[str]]:
        """Return a bounded feedback adjustment and concise reasons."""

        contribution = 0
        reasons: list[str] = []

        category_bonus = self.feedback_profile.category_bonus(
            story.category
        )
        contribution += category_bonus

        if category_bonus > 0:
            reasons.append("preferred category")
        elif category_bonus < 0:
            reasons.append(
                f"learned preference: category {category_bonus}"
            )

        entity_total = 0
        seen_entities: set[str] = set()

        for entity in story.entities or []:
            name = getattr(entity, "name", None)

            if not name or not str(name).strip():
                continue

            key = str(name).strip().lower()

            if key in seen_entities:
                continue

            seen_entities.add(key)

            entity_bonus = self.feedback_profile.entity_bonus(
                str(name)
            )
            entity_total += entity_bonus

            if entity_bonus > 0:
                reasons.append(
                    f"preferred entity: {name}"
                )
            elif entity_bonus < 0:
                reasons.append(
                    "learned preference: "
                    f"disliked entity: {name}"
                )

        entity_total = max(
            self.MIN_ENTITY_CONTRIBUTION,
            min(self.MAX_ENTITY_CONTRIBUTION, entity_total),
        )
        contribution += entity_total

        if story.source:
            source_bonus = self.feedback_profile.source_bonus(
                story.source
            )
            contribution += source_bonus

            if source_bonus > 0:
                reasons.append("preferred source")
            elif source_bonus < 0:
                reasons.append(
                    f"learned preference: source {source_bonus}"
                )

        contribution = max(
            self.MIN_FEEDBACK_CONTRIBUTION,
            min(
                self.MAX_FEEDBACK_CONTRIBUTION,
                contribution,
            ),
        )

        if contribution == 0:
            return 0, []

        return contribution, reasons