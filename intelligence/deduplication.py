from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from intelligence.models import (
    IntelligenceStory,
    SourceTrust,
)


@dataclass
class MergedStory:
    """A story after similar source reports have been merged."""

    story: IntelligenceStory
    source_count: int
    sources: list[str]


class StoryDeduplicator:
    """
    Detects stories that likely describe the same underlying event.

    This is intentionally a simple first version.
    Later we can replace it with embeddings/semantic similarity.
    """

    SIMILARITY_THRESHOLD = 0.72

    def _normalize_text(
        self,
        text: str,
    ) -> str:
        """Normalize text for basic similarity comparison."""

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _similarity(
        self,
        first: str,
        second: str,
    ) -> float:
        """Return a basic text similarity score."""

        first_normalized = (
            self._normalize_text(first)
        )

        second_normalized = (
            self._normalize_text(second)
        )

        return SequenceMatcher(
            None,
            first_normalized,
            second_normalized,
        ).ratio()

    def _is_duplicate(
        self,
        first: IntelligenceStory,
        second: IntelligenceStory,
    ) -> bool:
        """Determine whether two stories likely describe the same event."""

        # Different known locations are usually different stories.
        if (
            first.location_name
            and second.location_name
            and first.location_name.lower()
            != second.location_name.lower()
        ):
            return False

        # Compare titles first.
        title_similarity = self._similarity(
            first.title,
            second.title,
        )

        if (
            title_similarity
            >= self.SIMILARITY_THRESHOLD
        ):
            return True

        # Titles can differ greatly while summaries are similar.
        combined_first = (
            f"{first.title} {first.summary}"
        )

        combined_second = (
            f"{second.title} {second.summary}"
        )

        combined_similarity = self._similarity(
            combined_first,
            combined_second,
        )

        return (
            combined_similarity
            >= self.SIMILARITY_THRESHOLD
        )

    def _merge_pair(
        self,
        existing: MergedStory,
        incoming: IntelligenceStory,
        incoming_source: str,
    ) -> None:
        """Merge one incoming report into an existing story."""

        existing.source_count += 1

        if incoming_source not in existing.sources:
            existing.sources.append(
                incoming_source
            )

        # Prefer higher importance.
        existing.story.importance = max(
            existing.story.importance,
            incoming.importance,
        )

        # Prefer higher severity.
        existing.story.severity = max(
            existing.story.severity,
            incoming.severity,
        )

        # Prefer higher personal relevance.
        existing.story.personal_relevance = max(
            existing.story.personal_relevance,
            incoming.personal_relevance,
        )

        # Prefer higher novelty.
        existing.story.novelty = max(
            existing.story.novelty,
            incoming.novelty,
        )

        # Confidence increases when independent sources
        # describe the same story.
        existing.story.confidence = min(
            100,
            max(
                existing.story.confidence,
                incoming.confidence,
            )
            + 5,
        )

        # Prefer the more trusted source.
        if (
            incoming.source_trust
            > existing.story.source_trust
        ):
            existing.story.source = incoming.source
            existing.story.url = incoming.url
            existing.story.source_trust = (
                incoming.source_trust
            )

    def merge(
        self,
        stories: list[
            tuple[IntelligenceStory, str]
        ],
    ) -> list[MergedStory]:
        """
        Merge duplicate/similar reports.

        Input:
            (story, source_name)

        Output:
            merged stories.
        """

        merged: list[MergedStory] = []

        for story, source_name in stories:

            match = None

            for existing in merged:
                if self._is_duplicate(
                    existing.story,
                    story,
                ):
                    match = existing
                    break

            if match is None:
                merged.append(
                    MergedStory(
                        story=story,
                        source_count=1,
                        sources=[source_name],
                    )
                )

            else:
                self._merge_pair(
                    match,
                    story,
                    source_name,
                )

        return merged