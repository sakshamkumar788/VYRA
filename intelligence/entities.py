"""
Deterministic rule-based entity/topic extraction for VYRA intelligence.

This is intentionally a small, dependency-free first version.
It can later be replaced with embeddings, NER, or LLM-assisted extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


class EntityType:
    """Supported entity types for intelligence stories."""

    PERSON = "person"
    COMPANY = "company"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    RESEARCH_TOPIC = "research_topic"
    PRODUCT = "product"
    EVENT = "event"
    OTHER = "other"


@dataclass
class StoryEntity:
    """A recognized entity from a story title/summary."""

    name: str
    entity_type: str
    confidence: int
    relevance: int


class EntityExtractor:
    """Rule-based entity extractor for intelligence stories."""

    def __init__(self) -> None:
        self._entity_patterns: list[tuple[str, str, str]] = [
            # Technology / research terms
            ("artificial intelligence", "AI", EntityType.TECHNOLOGY),
            ("ai", "AI", EntityType.TECHNOLOGY),
            ("machine learning", "Machine Learning", EntityType.RESEARCH_TOPIC),
            ("deep learning", "Deep Learning", EntityType.RESEARCH_TOPIC),
            ("large language model", "LLM", EntityType.TECHNOLOGY),
            ("llm", "LLM", EntityType.TECHNOLOGY),
            ("semiconductor", "Semiconductor", EntityType.TECHNOLOGY),
            ("chip", "Chip", EntityType.TECHNOLOGY),
            ("quantum computing", "Quantum", EntityType.RESEARCH_TOPIC),
            ("quantum", "Quantum", EntityType.RESEARCH_TOPIC),
            ("dna data storage", "DNA Data Storage", EntityType.RESEARCH_TOPIC),
            ("robotics", "Robotics", EntityType.TECHNOLOGY),
            ("biotech", "Biotech", EntityType.RESEARCH_TOPIC),
            ("cybersecurity", "Cybersecurity", EntityType.TECHNOLOGY),
            ("cloud computing", "Cloud Computing", EntityType.TECHNOLOGY),

            # Obvious locations
            ("united states", "United States", EntityType.LOCATION),
            ("india", "India", EntityType.LOCATION),
            ("punjab", "Punjab", EntityType.LOCATION),
            ("delhi", "Delhi", EntityType.LOCATION),
            ("jalandhar", "Jalandhar", EntityType.LOCATION),
            ("bengaluru", "Bengaluru", EntityType.LOCATION),
            ("mumbai", "Mumbai", EntityType.LOCATION),
            ("china", "China", EntityType.LOCATION),
            ("europe", "Europe", EntityType.LOCATION),
        ]

    @staticmethod
    def _base_relevance(entity_type: str) -> int:
        """Return a simple base relevance for a matched entity type."""
        if entity_type in (EntityType.TECHNOLOGY, EntityType.RESEARCH_TOPIC):
            return 75
        if entity_type == EntityType.LOCATION:
            return 50
        return 50

    @staticmethod
    def _search_pattern(pattern: str, text: str) -> bool:
        """Return True if pattern appears as a word/phrase in text."""
        return re.search(rf"\b{re.escape(pattern)}\b", text) is not None

    def extract(self, title: str, summary: str) -> list[StoryEntity]:
        """Extract known entities from a story title and summary."""

        title_lower = title.lower()
        summary_lower = summary.lower()
        combined = f"{title_lower} {summary_lower}"

        # key = (canonical_name, entity_type)
        matched: dict[tuple[str, str], StoryEntity] = {}

        for pattern, canonical, entity_type in self._entity_patterns:
            if not self._search_pattern(pattern, combined):
                continue

            in_title = self._search_pattern(pattern, title_lower)

            confidence = 98 if in_title else 90
            relevance = self._base_relevance(entity_type)

            if in_title:
                relevance += 10

            key = (canonical.lower(), entity_type)

            existing = matched.get(key)

            if existing is None:
                matched[key] = StoryEntity(
                    name=canonical,
                    entity_type=entity_type,
                    confidence=confidence,
                    relevance=relevance,
                )
            else:
                existing.confidence = max(existing.confidence, confidence)
                existing.relevance = max(existing.relevance, relevance)

        return sorted(
            matched.values(),
            key=lambda entity: (
                -entity.relevance,
                entity.name.lower(),
            ),
        )


def _run_self_tests() -> None:
    """Small local test/example for the entity extractor."""

    extractor = EntityExtractor()

    cases = [
        (
            "New AI model launch",
            "Machine learning and deep learning are changing cloud computing.",
            {"AI", "Machine Learning", "Deep Learning", "Cloud Computing"},
        ),
        (
            "Heavy rain in Jalandhar",
            "Punjab, Delhi, and Mumbai also affected in India.",
            {"Jalandhar", "Punjab", "Delhi", "Mumbai", "India"},
        ),
        (
            "Breakthrough in DNA data storage",
            "Quantum research and biotech advance semiconductor and robotics.",
            {"DNA Data Storage", "Quantum", "Biotech", "Semiconductor", "Robotics"},
        ),
        (
            "A normal afternoon",
            "Nothing worth noting.",
            set(),
        ),
        (
            "AI and artificial intelligence",
            "Both terms refer to the same entity.",
            {"AI"},
        ),
    ]

    for title, summary, expected in cases:
        entities = extractor.extract(title, summary)
        names = {entity.name for entity in entities}

        print(f"Title: {title!r}")
        print(f"Summary: {summary!r}")
        print(f"Entities: {names}")
        print("-" * 40)

        assert names == expected, f"Expected {expected}, got {names}"

    print("All entity extraction self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()