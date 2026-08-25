from intelligence.current_affairs import (
    CurrentAffairsEngine,
)
from intelligence.current_affairs_formatter import (
    CurrentAffairsFormatter,
)
from intelligence.models import (
    IntelligenceStory,
    StoryCategory,
)


def main() -> None:
    stories = [
        IntelligenceStory(
            title="Major Punjab development",
            summary="Important local development.",
            source="Test Local",
            category=StoryCategory.LOCAL,
            importance=90,
            severity=80,
            novelty=90,
        ),
        IntelligenceStory(
            title="Major India development",
            summary="Important national development.",
            source="Test India",
            category=StoryCategory.INDIA,
            importance=85,
            severity=70,
            novelty=80,
        ),
        IntelligenceStory(
            title="Indian AI company expands",
            summary="Important Indian technology news.",
            source="Test Tech",
            category=StoryCategory.INDIAN_TECH,
            importance=80,
            severity=20,
            novelty=90,
        ),
        IntelligenceStory(
            title="DNA data storage research",
            summary="Interesting research development.",
            source="Test Research",
            category=StoryCategory.RESEARCH,
            importance=75,
            severity=10,
            novelty=95,
        ),
        IntelligenceStory(
            title="Major global event",
            summary="Important international development.",
            source="Test World",
            category=StoryCategory.WORLD,
            importance=95,
            severity=90,
            novelty=95,
        ),
        IntelligenceStory(
            title="Entertainment item",
            summary="Should not enter current affairs.",
            source="Test",
            category=StoryCategory.FUN,
            importance=90,
            severity=10,
            novelty=90,
        ),
    ]

    engine = CurrentAffairsEngine()

    brief = engine.build(
        stories,
        max_per_section=3,
    )

    print("Sections:")
    for section in brief.sections:
        print(
            section.name,
            "->",
            len(section.stories),
        )

    assert len(brief.sections) == 5

    section_names = [
        section.name
        for section in brief.sections
    ]

    assert "Local" in section_names
    assert "India" in section_names
    assert "Indian Tech" in section_names
    assert "Research & Science" in section_names
    assert "World" in section_names

    formatted = (
        CurrentAffairsFormatter().format(
            brief
        )
    )

    print()
    print("FORMATTED:")
    print(formatted)

    assert "Major Punjab development" in formatted
    assert "Major India development" in formatted
    assert "Indian AI company expands" in formatted
    assert "DNA data storage research" in formatted
    assert "Major global event" in formatted

    assert "Entertainment item" not in formatted

    print()
    print(
        "All current affairs tests passed."
    )


if __name__ == "__main__":
    main()