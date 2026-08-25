from dataclasses import dataclass, field


@dataclass
class IntelligenceProfile:
    """Personal context used to rank intelligence."""

    important_topics: set[str] = field(
        default_factory=lambda: {
            "ai",
            "machine_learning",
            "data_science",
            "dsa",
            "technology",
            "research",
            "deep_tech",
            "indian_tech",
        }
    )

    important_regions: set[str] = field(
        default_factory=lambda: {
            "india",
            "punjab",
            "jalandhar",
        }
    )

    world_importance_threshold: int = 80

    local_importance_bonus: int = 25

    personal_topic_bonus: int = 20

    indian_tech_bonus: int = 25