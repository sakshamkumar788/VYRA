from intelligence.entities import (
    EntityType,
    StoryEntity,
)
from intelligence.feedback import (
    FeedbackProfile,
    FeedbackType,
)
from intelligence.feedback_handler import (
    IntelligenceFeedbackHandler,
)
from intelligence.models import (
    IntelligenceStory,
)


def main() -> None:
    profile = FeedbackProfile()

    handler = IntelligenceFeedbackHandler(
        profile
    )

    story = IntelligenceStory(
        title="AI research breakthrough",
        summary="New AI research development.",
        category="research",
        source="TestSource",
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
                relevance=80,
            ),
        ],
    )

    handler.record_story_feedback(
        story,
        FeedbackType.MORE_LIKE_THIS,
    )

    print(
        "Category:",
        profile.category_bonus("research"),
    )

    print(
        "AI:",
        profile.entity_bonus("ai"),
    )

    print(
        "Machine Learning:",
        profile.entity_bonus("machine learning"),
    )

    print(
        "Source:",
        profile.source_bonus("testsource"),
    )

    assert (
        profile.category_bonus("research")
        == 10
    )

    assert (
        profile.entity_bonus("ai")
        == 10
    )

    assert (
        profile.entity_bonus(
            "machine learning"
        )
        == 10
    )

    assert (
        profile.source_bonus("testsource")
        == 10
    )

    assert len(profile.history) == 1

    print()
    print(
        "All feedback handler tests passed."
    )


if __name__ == "__main__":
    main()