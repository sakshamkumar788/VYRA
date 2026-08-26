from morning.context import MorningBriefingContext
from morning.relevance import BriefingRelevanceSelector, BriefingCandidate
from intelligence.feedback import FeedbackProfile, FeedbackType


def test_empty_profile_preserves_baseline():
    selector = BriefingRelevanceSelector()
    context = MorningBriefingContext(
        current_time="08:00 AM",
        time_of_day="morning",
        weather="Sunny 25C",
        important_tasks=["Task A"],
        important_events=["Event A"],
        news_items=["News 1 (SourceA)", "News 2 (SourceB)"],
        relevant_memories=[],
        current_goals=[],
    )
    baseline = selector.select(context, feedback_profile=None)
    profile = FeedbackProfile()
    with_profile = selector.select(context, feedback_profile=profile)
    # Scores should be identical
    assert [c.content for c in baseline] == [c.content for c in with_profile]


def test_positive_category_preference_increases_relevance():
    selector = BriefingRelevanceSelector()
    # Directly test adjustment logic with synthetic candidate
    profile = FeedbackProfile()
    profile.record(FeedbackType.MORE_LIKE_THIS, story_category="ai", persist=False)

    candidate = BriefingCandidate(
        topic="news",
        content="AI breakthrough",
        score=40,
        reason="test",
        category="ai",
    )
    adj = selector._feedback_adjustment(candidate, profile)
    assert adj > 0

    # Negative category
    profile2 = FeedbackProfile()
    profile2.record(FeedbackType.DO_NOT_TELL_ME_THIS, story_category="research", persist=False)
    candidate2 = BriefingCandidate(
        topic="news",
        content="Research paper",
        score=40,
        reason="test",
        category="research",
    )
    adj2 = selector._feedback_adjustment(candidate2, profile2)
    assert adj2 < 0


def test_entity_preference_affects_relevance():
    selector = BriefingRelevanceSelector()
    profile = FeedbackProfile()
    profile.record(FeedbackType.MORE_LIKE_THIS, entity_names=["Nvidia"], persist=False)

    candidate = BriefingCandidate(
        topic="news",
        content="Nvidia news",
        score=40,
        reason="test",
        entities=["Nvidia", "AI"],
    )
    adj = selector._feedback_adjustment(candidate, profile)
    assert adj > 0

    # Duplicate entities counted once
    candidate_dup = BriefingCandidate(
        topic="news",
        content="Dup",
        score=40,
        reason="test",
        entities=["Nvidia", "nvidia"],
    )
    adj_dup = selector._feedback_adjustment(candidate_dup, profile)
    # Should not double count
    assert adj_dup == adj


def test_source_preference_affects_relevance():
    selector = BriefingRelevanceSelector()
    context = MorningBriefingContext(
        current_time="08:00 AM",
        time_of_day="morning",
        news_items=["Story A (SourceA)", "Story B (SourceB)"],
    )
    profile = FeedbackProfile()
    profile.record(FeedbackType.MORE_LIKE_THIS, source="sourcea", persist=False)

    selected = selector.select(context, feedback_profile=profile)
    # Story A should be ranked before Story B
    contents = [c.content for c in selected]
    assert contents[0].startswith("Story A")


def test_feedback_bounded():
    selector = BriefingRelevanceSelector()
    profile = FeedbackProfile()
    # Apply many positive feedbacks to push beyond bounds
    for _ in range(10):
        profile.record(FeedbackType.MORE_LIKE_THIS, story_category="ai", persist=False)
        profile.record(FeedbackType.MORE_LIKE_THIS, source="sourcex", persist=False)
        profile.record(FeedbackType.MORE_LIKE_THIS, entity_names=["Entity"], persist=False)

    candidate = BriefingCandidate(
        topic="news",
        content="Test",
        score=40,
        reason="test",
        category="ai",
        entities=["Entity", "Entity"],  # duplicate
        source="sourcex",
    )
    adj = selector._feedback_adjustment(candidate, profile)
    assert -15 <= adj <= 15


def test_critical_candidate_not_eliminated_by_negative_feedback():
    selector = BriefingRelevanceSelector()
    context = MorningBriefingContext(
        current_time="08:00 AM",
        time_of_day="morning",
        important_tasks=["Critical task"],
        news_items=["Irrelevant (BadSource)"],
    )
    profile = FeedbackProfile()
    profile.record(FeedbackType.DO_NOT_TELL_ME_THIS, source="badsource", persist=False)

    selected = selector.select(context, feedback_profile=profile)
    # Critical task should still appear
    topics = [c.topic for c in selected]
    assert "task" in topics


def test_existing_relevance_still_passes():
    selector = BriefingRelevanceSelector()
    context = MorningBriefingContext(
        current_time="08:00 AM",
        time_of_day="morning",
        weather="Rainy",
        important_tasks=["Task 1", "Task 2"],
        important_events=["Event 1"],
        news_items=["News 1", "News 2", "News 3"],
        relevant_memories=["Memory 1"],
        current_goals=["Goal 1"],
    )
    selected = selector.select(context)
    # Max items
    assert len(selected) <= selector.MAX_SELECTED_ITEMS
    # Event should be highest due to score 80
    assert selected[0].topic == "event"


if __name__ == "__main__":
    test_empty_profile_preserves_baseline()
    test_positive_category_preference_increases_relevance()
    test_entity_preference_affects_relevance()
    test_source_preference_affects_relevance()
    test_feedback_bounded()
    test_critical_candidate_not_eliminated_by_negative_feedback()
    test_existing_relevance_still_passes()
    print("All morning relevance tests passed.")
