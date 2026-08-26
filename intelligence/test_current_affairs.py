from intelligence.current_affairs import (
    CurrentAffairsEngine,
)
from intelligence.current_affairs_formatter import (
    CurrentAffairsFormatter,
)
from intelligence.entities import StoryEntity
from intelligence.feedback import FeedbackProfile, FeedbackType
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

    # ---------------------------------------------------------
    # Feedback-aware current affairs
    # ---------------------------------------------------------

    engine_fb = CurrentAffairsEngine()

    # Neutral profile preserves existing output
    neutral_profile = FeedbackProfile()
    brief_neutral = engine_fb.build(stories, max_per_section=3, feedback_profile=neutral_profile)
    # Sections should match baseline
    assert len(brief_neutral.sections) == 5

    # Positive category preference moves AI story ahead
    profile_ai = FeedbackProfile()
    profile_ai.record(FeedbackType.MORE_LIKE_THIS, story_category="ai", persist=False)
    ai_story_high = IntelligenceStory(
        title="AI breakthrough",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
    )
    ai_story_low = IntelligenceStory(
        title="AI minor update",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
    )
    # Add negative feedback to second story via source? Simpler: make stories identical base, rely on feedback to order
    # Create two AI stories with same base scores
    story_a = IntelligenceStory(
        title="AI A",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="SourceA",
    )
    story_b = IntelligenceStory(
        title="AI B",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="SourceB",
    )
    # Give positive feedback to SourceA
    profile_ai.record(FeedbackType.MORE_LIKE_THIS, source="SourceA", persist=False)
    brief_fb = engine_fb.build([story_a, story_b], max_per_section=3, feedback_profile=profile_ai)
    ai_section = next(s for s in brief_fb.sections if s.name == "AI & Technology")
    assert ai_section.stories[0].title == "AI A"

    # Negative category preference lowers ranking
    profile_neg = FeedbackProfile()
    profile_neg.record(FeedbackType.DO_NOT_TELL_ME_THIS, story_category="research", persist=False)
    research1 = IntelligenceStory(
        title="Research A",
        summary="",
        category=StoryCategory.RESEARCH,
        importance=80,
        severity=10,
        novelty=80,
        source="Test",
    )
    research2 = IntelligenceStory(
        title="Research B",
        summary="",
        category=StoryCategory.RESEARCH,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
    )
    brief_neg = engine_fb.build([research1, research2], max_per_section=3, feedback_profile=profile_neg)
    res_section = next(s for s in brief_neg.sections if s.name == "Research & Science")
    # Higher importance still wins despite negative feedback
    assert res_section.stories[0].title == "Research A"

    # Entity preference affects ordering
    profile_ent = FeedbackProfile()
    profile_ent.record(FeedbackType.MORE_LIKE_THIS, entity_names=["Nvidia"], persist=False)
    ent_story1 = IntelligenceStory(
        title="Nvidia news",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
        entities=[StoryEntity(name="Nvidia", entity_type="company", confidence=80, relevance=80)],
    )
    ent_story2 = IntelligenceStory(
        title="Other AI news",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
        entities=[],
    )
    brief_ent = engine_fb.build([ent_story1, ent_story2], max_per_section=3, feedback_profile=profile_ent)
    ent_section = next(s for s in brief_ent.sections if s.name == "AI & Technology")
    assert ent_section.stories[0].title == "Nvidia news"

    # Duplicate entities counted once
    profile_dup = FeedbackProfile()
    profile_dup.record(FeedbackType.MORE_LIKE_THIS, entity_names=["AI"], persist=False)
    dup_story = IntelligenceStory(
        title="Dup entity",
        summary="",
        category=StoryCategory.AI,
        importance=70,
        severity=10,
        novelty=70,
        source="Test",
        entities=[
            StoryEntity(name="AI", entity_type="technology", confidence=80, relevance=80),
            StoryEntity(name="ai", entity_type="technology", confidence=80, relevance=80),
        ],
    )
    # Should not error and ordering works
    brief_dup = engine_fb.build([dup_story], max_per_section=3, feedback_profile=profile_dup)
    assert len(brief_dup.sections) == 1

    print()
    print(
        "All current affairs tests passed."
    )


if __name__ == "__main__":
    main()