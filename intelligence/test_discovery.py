from datetime import datetime, timedelta

from intelligence.discovery import DiscoveryEngine
from intelligence.entities import StoryEntity
from intelligence.feedback import FeedbackProfile, FeedbackType
from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority
from intelligence.queue import QueuedIntelligence


def _queued(
    story: IntelligenceStory,
    priority: str = IntelligencePriority.INTERESTING,
) -> QueuedIntelligence:
    return QueuedIntelligence(
        story=story,
        priority=priority,
        added_at=datetime.now(),
    )


def _strong_story(**overrides) -> IntelligenceStory:
    values = dict(
        title="DNA data storage breakthrough",
        summary=(
            "Researchers report an interesting "
            "development in DNA data storage."
        ),
        importance=80,
        novelty=95,
        personal_relevance=85,
        confidence=90,
        category="research",
    )
    values.update(overrides)
    return IntelligenceStory(**values)


def _entity(name: str) -> StoryEntity:
    return StoryEntity(
        name=name,
        entity_type="technology",
        confidence=80,
        relevance=75,
    )


def _score(engine: DiscoveryEngine, story: IntelligenceStory) -> int:
    candidates = engine.evaluate([_queued(story)])
    assert len(candidates) == 1
    return candidates[0].score


def main() -> None:
    engine = DiscoveryEngine()

    strong_story = IntelligenceStory(
        title="DNA data storage breakthrough",
        summary=(
            "Researchers report an interesting "
            "development in DNA data storage."
        ),
        importance=80,
        novelty=95,
        personal_relevance=85,
        confidence=90,
    )

    weak_story = IntelligenceStory(
        title="Minor routine update",
        summary="A small unimportant update.",
        importance=10,
        novelty=10,
        personal_relevance=0,
        confidence=60,
    )

    items = [
        QueuedIntelligence(
            story=strong_story,
            priority=IntelligencePriority.INTERESTING,
            added_at=datetime.now(),
        ),
        QueuedIntelligence(
            story=weak_story,
            priority=IntelligencePriority.INTERESTING,
            added_at=datetime.now(),
        ),
    ]

    candidates = engine.evaluate(items)

    print("Candidates:", len(candidates))

    for candidate in candidates:
        print()
        print("Title:", candidate.story.title)
        print("Score:", candidate.score)
        print("Reason:", candidate.reason)

    assert len(candidates) == 1

    assert (
        candidates[0].story.title
        == "DNA data storage breakthrough"
    )

    # ---------------------------------------------------------
    # No feedback keeps existing behavior
    # ---------------------------------------------------------

    empty_profile = FeedbackProfile()
    empty_engine = DiscoveryEngine(empty_profile)
    default_engine = DiscoveryEngine()

    baseline_score = _score(default_engine, _strong_story())
    empty_score = _score(empty_engine, _strong_story())

    assert empty_score == baseline_score

    # ---------------------------------------------------------
    # Positive category feedback increases score
    # ---------------------------------------------------------

    liked_category = FeedbackProfile()
    liked_category.record(
        FeedbackType.LIKE,
        story_category="research",
        persist=False,
    )

    liked_category_score = _score(
        DiscoveryEngine(liked_category),
        _strong_story(category="research"),
    )

    assert liked_category_score > baseline_score
    assert (
        "preferred category"
        in DiscoveryEngine(liked_category)
        .evaluate([_queued(_strong_story(category="research"))])[0]
        .reason
    )

    # ---------------------------------------------------------
    # Negative category feedback decreases score
    # ---------------------------------------------------------

    disliked_category = FeedbackProfile()
    disliked_category.record(
        FeedbackType.DISLIKE,
        story_category="research",
        persist=False,
    )

    disliked_category_score = _score(
        DiscoveryEngine(disliked_category),
        _strong_story(category="research"),
    )

    assert disliked_category_score < baseline_score
    assert (
        "learned preference"
        in DiscoveryEngine(disliked_category)
        .evaluate([_queued(_strong_story(category="research"))])[0]
        .reason
    )

    # ---------------------------------------------------------
    # Positive entity feedback increases score
    # ---------------------------------------------------------

    liked_entity = FeedbackProfile()
    liked_entity.record(
        FeedbackType.LIKE,
        entity_names=["AI"],
        persist=False,
    )

    story_with_entity = _strong_story(
        title="AI research note",
        entities=[_entity("AI")],
    )

    entity_baseline = _score(
        DiscoveryEngine(),
        story_with_entity,
    )
    entity_boosted = _score(
        DiscoveryEngine(liked_entity),
        story_with_entity,
    )

    assert entity_boosted > entity_baseline
    assert (
        "preferred entity: AI"
        in DiscoveryEngine(liked_entity)
        .evaluate([_queued(story_with_entity)])[0]
        .reason
    )

    # ---------------------------------------------------------
    # Duplicate entities counted once
    # ---------------------------------------------------------

    duplicate_story = _strong_story(
        title="AI and ai",
        entities=[_entity("AI"), _entity("ai")],
    )

    duplicate_score = _score(
        DiscoveryEngine(liked_entity),
        duplicate_story,
    )

    assert duplicate_score == entity_boosted
    assert (
        DiscoveryEngine(liked_entity)
        .evaluate([_queued(duplicate_story)])[0]
        .reason
        .count("preferred entity:")
        == 1
    )

    # ---------------------------------------------------------
    # Positive source feedback increases score
    # ---------------------------------------------------------

    liked_source = FeedbackProfile()
    liked_source.record(
        FeedbackType.LIKE,
        source="PIB India",
        persist=False,
    )

    sourced_story = _strong_story(source="PIB India")

    source_baseline = _score(DiscoveryEngine(), sourced_story)
    source_boosted = _score(
        DiscoveryEngine(liked_source),
        sourced_story,
    )

    assert source_boosted > source_baseline
    assert (
        "preferred source"
        in DiscoveryEngine(liked_source)
        .evaluate([_queued(sourced_story)])[0]
        .reason
    )

    # ---------------------------------------------------------
    # Positive feedback contribution capped at +30
    # ---------------------------------------------------------

    heavy_positive = FeedbackProfile()

    for _ in range(6):
        heavy_positive.record(
            FeedbackType.MORE_LIKE_THIS,
            story_category="research",
            entity_names=["quantum"],
            source="Nature",
            persist=False,
        )

    capped_positive_story = _strong_story(
        category="research",
        source="Nature",
        entities=[_entity("quantum")],
    )

    positive_delta = (
        _score(
            DiscoveryEngine(heavy_positive),
            capped_positive_story,
        )
        - _score(DiscoveryEngine(), capped_positive_story)
    )

    assert positive_delta == 30

    # ---------------------------------------------------------
    # Negative feedback contribution capped at -30
    # ---------------------------------------------------------

    heavy_negative = FeedbackProfile()

    for _ in range(3):
        heavy_negative.record(
            FeedbackType.DO_NOT_TELL_ME_THIS,
            story_category="research",
            entity_names=["quantum"],
            source="Nature",
            persist=False,
        )

    negative_delta = (
        _score(
            DiscoveryEngine(heavy_negative),
            capped_positive_story,
        )
        - _score(DiscoveryEngine(), capped_positive_story)
    )

    assert negative_delta == -30

    # ---------------------------------------------------------
    # Candidate ordering remains correct
    # ---------------------------------------------------------

    higher_without_feedback = _strong_story(
        title="Broader research note",
        category="science",
        importance=80,
        novelty=80,
        personal_relevance=80,
        confidence=90,
    )
    lower_without_feedback = _strong_story(
        title="AI lab update",
        category="ai",
        importance=70,
        novelty=70,
        personal_relevance=60,
        confidence=90,
    )

    unordered = [
        _queued(lower_without_feedback),
        _queued(higher_without_feedback),
    ]

    default_order = DiscoveryEngine().evaluate(unordered)

    assert len(default_order) == 2
    assert (
        default_order[0].story.title
        == "Broader research note"
    )
    assert default_order[0].score > default_order[1].score

    order_profile = FeedbackProfile()

    for _ in range(3):
        order_profile.record(
            FeedbackType.MORE_LIKE_THIS,
            story_category="ai",
            persist=False,
        )

    feedback_order = DiscoveryEngine(
        order_profile
    ).evaluate(unordered)

    assert (
        feedback_order[0].story.title
        == "AI lab update"
    )
    assert feedback_order[0].score > feedback_order[1].score

    # ---------------------------------------------------------
    # Unrelated story gets no feedback bonus
    # ---------------------------------------------------------

    unrelated_profile = FeedbackProfile()
    unrelated_profile.record(
        FeedbackType.LIKE,
        story_category="ai",
        entity_names=["python"],
        source="Reuters",
        persist=False,
    )

    unrelated_story = _strong_story(
        title="Punjab weather note",
        category="local",
        source="Indian Express",
        entities=[_entity("Punjab")],
    )

    unrelated_baseline = _score(
        DiscoveryEngine(),
        unrelated_story,
    )
    unrelated_with_profile = _score(
        DiscoveryEngine(unrelated_profile),
        unrelated_story,
    )

    assert unrelated_with_profile == unrelated_baseline

    # ---------------------------------------------------------
    # A. Negative category feedback lowers score
    # ---------------------------------------------------------

    sports_story = _strong_story(
        title="Sports roundup",
        category="sports",
    )
    sports_baseline = _score(DiscoveryEngine(), sports_story)

    no_sports = FeedbackProfile()
    no_sports.record(
        FeedbackType.DO_NOT_TELL_ME_THIS,
        story_category="sports",
        persist=False,
    )

    sports_suppressed_score = _score(
        DiscoveryEngine(no_sports),
        sports_story,
    )

    assert sports_suppressed_score < sports_baseline
    assert (
        "learned preference"
        in DiscoveryEngine(no_sports)
        .evaluate([_queued(sports_story)])[0]
        .reason
    )

    # ---------------------------------------------------------
    # B. Negative entity feedback lowers score
    # ---------------------------------------------------------

    cricket_story = _strong_story(
        title="Cricket update",
        category="sports",
        entities=[_entity("cricket")],
    )
    cricket_baseline = _score(DiscoveryEngine(), cricket_story)

    less_cricket = FeedbackProfile()
    less_cricket.record(
        FeedbackType.LESS_LIKE_THIS,
        entity_names=["cricket"],
        persist=False,
    )

    cricket_suppressed_score = _score(
        DiscoveryEngine(less_cricket),
        cricket_story,
    )

    assert cricket_suppressed_score < cricket_baseline
    assert (
        "learned preference"
        in DiscoveryEngine(less_cricket)
        .evaluate([_queued(cricket_story)])[0]
        .reason
    )

    # ---------------------------------------------------------
    # C. Negative source feedback lowers score
    # ---------------------------------------------------------

    sourced_sports = _strong_story(
        title="League recap",
        category="sports",
        source="Sports Daily",
    )
    sourced_baseline = _score(DiscoveryEngine(), sourced_sports)

    dislike_source = FeedbackProfile()
    dislike_source.record(
        FeedbackType.DISLIKE,
        source="Sports Daily",
        persist=False,
    )

    sourced_suppressed_score = _score(
        DiscoveryEngine(dislike_source),
        sourced_sports,
    )

    assert sourced_suppressed_score < sourced_baseline
    assert (
        "learned preference"
        in DiscoveryEngine(dislike_source)
        .evaluate([_queued(sourced_sports)])[0]
        .reason
    )

    # ---------------------------------------------------------
    # D. Strong negative feedback can suppress discovery
    # ---------------------------------------------------------

    # Adjusted moderate story so that it remains above threshold
    # with freshness, but can be suppressed by negative feedback.
    moderate_story = IntelligenceStory(
        title="Minor sports note",
        summary="A moderately interesting sports item.",
        category="sports",
        importance=30,    # was 40
        novelty=40,       # was 50
        personal_relevance=0,
        confidence=70,
    )

    moderate_candidates = DiscoveryEngine().evaluate(
        [_queued(moderate_story)]
    )
    assert len(moderate_candidates) == 1
    assert (
        moderate_candidates[0].score
        >= DiscoveryEngine.MINIMUM_SCORE
    )
    assert moderate_candidates[0].score - 20 < DiscoveryEngine.MINIMUM_SCORE

    suppress_profile = FeedbackProfile()
    suppress_profile.record(
        FeedbackType.DO_NOT_TELL_ME_THIS,
        story_category="sports",
        persist=False,
    )

    suppressed_candidates = DiscoveryEngine(
        suppress_profile
    ).evaluate([_queued(moderate_story)])

    assert suppressed_candidates == []

    # ---------------------------------------------------------
    # E. Feedback remains bounded
    # ---------------------------------------------------------

    many_negative = FeedbackProfile()

    for _ in range(8):
        many_negative.record(
            FeedbackType.DO_NOT_TELL_ME_THIS,
            story_category="research",
            entity_names=["quantum"],
            source="Nature",
            persist=False,
        )

    many_negative_delta = (
        _score(
            DiscoveryEngine(many_negative),
            capped_positive_story,
        )
        - _score(DiscoveryEngine(), capped_positive_story)
    )

    assert many_negative_delta >= -30
    assert many_negative_delta == -30

    # ---------------------------------------------------------
    # F. Positive and negative preferences remain independent
    # ---------------------------------------------------------

    ai_positive = FeedbackProfile()
    ai_positive.record(
        FeedbackType.MORE_LIKE_THIS,
        story_category="ai",
        entity_names=["AI"],
        persist=False,
    )

    independent_sports = _strong_story(
        title="Unrelated sports story",
        category="sports",
        source="Sports Daily",
        entities=[_entity("cricket")],
    )

    independent_baseline = _score(
        DiscoveryEngine(),
        independent_sports,
    )
    independent_with_ai = _score(
        DiscoveryEngine(ai_positive),
        independent_sports,
    )

    assert independent_with_ai == independent_baseline

    # ---------------------------------------------------------
    # Discovery repetition suppression
    # ---------------------------------------------------------

    repetition_engine = DiscoveryEngine()
    fresh_story = _strong_story(
        title="Fresh discovery item",
        url="https://example.com/fresh",
    )

    assert repetition_engine.has_been_discovered(fresh_story) is False

    repetition_engine.mark_discovered(fresh_story)

    assert repetition_engine.has_been_discovered(fresh_story) is True

    assert (
        repetition_engine.evaluate([_queued(fresh_story)])
        == []
    )

    repetition_engine.clear_discovery_history()

    assert repetition_engine.has_been_discovered(fresh_story) is False
    assert len(repetition_engine.evaluate([_queued(fresh_story)])) == 1

    same_url_different_title = _strong_story(
        title="Completely different headline",
        url="https://example.com/fresh",
    )

    repetition_engine.mark_discovered(fresh_story)

    assert (
        repetition_engine.has_been_discovered(
            same_url_different_title
        )
        is True
    )
    assert (
        repetition_engine.evaluate(
            [_queued(same_url_different_title)]
        )
        == []
    )

    title_engine = DiscoveryEngine()
    untitled_url = _strong_story(
        title="  DNA Storage Repeat  ",
    )
    same_title_no_url = _strong_story(
        title="dna storage repeat",
    )

    assert title_engine.has_been_discovered(untitled_url) is False

    title_engine.mark_discovered(untitled_url)

    assert (
        title_engine.has_been_discovered(same_title_no_url)
        is True
    )
    assert title_engine.evaluate([_queued(same_title_no_url)]) == []

    evaluate_only_engine = DiscoveryEngine()
    evaluated_story = _strong_story(
        title="Evaluated but not marked",
        url="https://example.com/not-marked",
    )

    evaluated = evaluate_only_engine.evaluate(
        [_queued(evaluated_story)]
    )

    assert len(evaluated) == 1
    assert (
        evaluate_only_engine.has_been_discovered(evaluated_story)
        is False
    )

    # ---------------------------------------------------------
    # Freshness tests
    # ---------------------------------------------------------

    base_time = datetime(2026, 8, 25, 10, 0, 0)

    fresh_engine = DiscoveryEngine()

    fresh_story = IntelligenceStory(
        title="Fresh story",
        summary="A story to test freshness.",
        importance=80,
        novelty=95,
        personal_relevance=85,
        confidence=90,
        published_at=base_time,
    )

    # 0 hours old
    candidates_0h = fresh_engine.evaluate(
        [_queued(fresh_story)],
        now=base_time,
    )
    assert len(candidates_0h) == 1
    score_0h = candidates_0h[0].score

    # 24 hours old
    candidates_24h = fresh_engine.evaluate(
        [_queued(fresh_story)],
        now=base_time + timedelta(hours=24),
    )
    assert len(candidates_24h) == 1
    score_24h = candidates_24h[0].score

    # 48 hours old
    candidates_48h = fresh_engine.evaluate(
        [_queued(fresh_story)],
        now=base_time + timedelta(hours=48),
    )
    assert len(candidates_48h) == 1
    score_48h = candidates_48h[0].score

    # 72 hours old
    candidates_72h = fresh_engine.evaluate(
        [_queued(fresh_story)],
        now=base_time + timedelta(hours=72),
    )
    assert len(candidates_72h) == 1
    score_72h = candidates_72h[0].score

    # Very old story (e.g., 1000 hours) should have factor ~0
    old_time = base_time + timedelta(hours=1000)
    candidates_old = fresh_engine.evaluate(
        [_queued(fresh_story)],
        now=old_time,
    )
    assert len(candidates_old) == 1
    score_old = candidates_old[0].score

    # Contribution differences relative to old story
    assert (score_0h - score_old) == 20   # max freshness
    assert (score_0h - score_24h) == 10   # half contribution
    assert (score_0h - score_48h) == 15   # remaining 5
    assert (score_0h - score_72h) == 18   # remaining 2 (floor of 2.5)

    # Future timestamp treated as age zero
    future_story = IntelligenceStory(
        title="Future story",
        summary="Timestamp is in the future.",
        importance=80,
        novelty=95,
        personal_relevance=85,
        confidence=90,
        published_at=base_time + timedelta(hours=5),
    )
    candidates_future = fresh_engine.evaluate(
        [_queued(future_story)],
        now=base_time,
    )
    assert len(candidates_future) == 1
    assert candidates_future[0].score == score_0h

    # Missing timestamp gives neutral factor 0.5 → contribution 10
    no_time_story = IntelligenceStory(
        title="No timestamp story",
        summary="No publication time provided.",
        importance=80,
        novelty=95,
        personal_relevance=85,
        confidence=90,
        # published_at is None
    )
    candidates_missing = fresh_engine.evaluate(
        [_queued(no_time_story)],
        now=base_time,
    )
    assert len(candidates_missing) == 1
    assert candidates_missing[0].score == score_0h - 10

    print()
    print("All discovery tests passed.")


if __name__ == "__main__":
    main()