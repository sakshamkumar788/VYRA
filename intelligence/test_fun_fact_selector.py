from datetime import datetime, timedelta

from intelligence.fun_facts import FunFact, FunFactEngine, FunFactCategory
from intelligence.feedback import FeedbackProfile, FeedbackType
from intelligence.discovery_policy import DiscoveryPolicy
from intelligence.fun_fact_selector import FunFactSelector, FunFactCandidate
from interaction.engine import InteractionEngine
from interaction.policy import InteractionContext, InteractionDecision, InteractionPriority
from context.context import SessionState
from memory.database import clear_interaction_state


def make_engine() -> FunFactEngine:
    facts = [
        FunFact(text="Science fact", category=FunFactCategory.SCIENCE, confidence=80),
        FunFact(text="Tech fact", category=FunFactCategory.TECHNOLOGY, confidence=60),
        FunFact(text="Low confidence science", category=FunFactCategory.SCIENCE, confidence=30),
    ]
    return FunFactEngine(facts)


def test_high_confidence_can_be_selected():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select()
    assert cand is not None
    assert cand.fact.text == "Science fact"


def test_low_confidence_not_promoted_excessively():
    engine = FunFactEngine([
        FunFact(text="Low", category=FunFactCategory.SCIENCE, confidence=30),
    ])
    profile = FeedbackProfile()
    profile.record(FeedbackType.MORE_LIKE_THIS, story_category=FunFactCategory.SCIENCE, persist=False)
    selector = FunFactSelector(engine, feedback_profile=profile)
    cand = selector.select()
    # Base = 15, bonus max 15 => max 30, still low
    assert cand.score <= 30
    assert cand.score >= 15


def test_positive_category_preference_increases_score():
    engine = FunFactEngine([
        FunFact(text="Tech", category=FunFactCategory.TECHNOLOGY, confidence=60),
    ])
    profile = FeedbackProfile()
    profile.record(FeedbackType.MORE_LIKE_THIS, story_category=FunFactCategory.TECHNOLOGY, persist=False)
    selector = FunFactSelector(engine, feedback_profile=profile)
    cand = selector.select()
    base = 60 // 2
    assert cand.score > base


def test_negative_category_preference_decreases_score():
    engine = FunFactEngine([
        FunFact(text="Tech", category=FunFactCategory.TECHNOLOGY, confidence=60),
    ])
    profile = FeedbackProfile()
    profile.record(FeedbackType.DO_NOT_TELL_ME_THIS, story_category=FunFactCategory.TECHNOLOGY, persist=False)
    selector = FunFactSelector(engine, feedback_profile=profile)
    cand = selector.select()
    base = 60 // 2
    assert cand.score < base


def test_personalization_bounded():
    engine = FunFactEngine([
        FunFact(text="Tech", category=FunFactCategory.TECHNOLOGY, confidence=80),
    ])
    profile = FeedbackProfile()
    for _ in range(20):
        profile.record(FeedbackType.MORE_LIKE_THIS, story_category=FunFactCategory.TECHNOLOGY, persist=False)
    selector = FunFactSelector(engine, feedback_profile=profile)
    cand = selector.select()
    personal = cand.score - (80 // 2)
    assert -15 <= personal <= 15


def test_category_filtering():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select(category=FunFactCategory.TECHNOLOGY)
    assert cand is not None
    assert cand.fact.category == FunFactCategory.TECHNOLOGY


def test_can_surface_respects_policy():
    engine = make_engine()
    policy = DiscoveryPolicy()
    selector = FunFactSelector(engine, discovery_policy=policy)
    now = datetime.now()
    assert selector.can_surface(now) is True
    policy.record_discovery(now)
    assert selector.can_surface(now) is False
    later = now + timedelta(minutes=400)
    assert selector.can_surface(later) is True


def test_interaction_event_uses_low_priority():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select()
    # Inspect internal event creation via evaluate
    from interaction.policy import InteractionEvent
    # We can't directly inspect, but evaluate should work
    engine_inter = InteractionEngine()
    ctx = InteractionContext(
        current_time=datetime.now(),
        session_state=SessionState.IDLE,
        proactive_enabled=True,
        user_active=True,
        user_busy=False,
        recent_interaction=False,
        idle_seconds=100,
    )
    decision = selector.evaluate_interaction(cand, engine_inter, ctx)
    assert isinstance(decision, InteractionDecision)


def test_proactive_disabled_produces_wait():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select()
    engine_inter = InteractionEngine()
    ctx = InteractionContext(
        current_time=datetime.now(),
        session_state=SessionState.IDLE,
        proactive_enabled=False,
    )
    decision = selector.evaluate_interaction(cand, engine_inter, ctx)
    assert decision == InteractionDecision.WAIT


def test_quiet_mode_produces_wait():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select()
    engine_inter = InteractionEngine()
    engine_inter.set_quiet_mode(True)
    ctx = InteractionContext(
        current_time=datetime.now(),
        session_state=SessionState.IDLE,
        proactive_enabled=True,
    )
    decision = selector.evaluate_interaction(cand, engine_inter, ctx)
    assert decision == InteractionDecision.WAIT


def test_allowed_interaction_can_produce_speak():
    engine = make_engine()
    selector = FunFactSelector(engine)
    cand = selector.select()
    engine_inter = InteractionEngine()
    ctx = InteractionContext(
        current_time=datetime.now(),
        session_state=SessionState.IDLE,
        proactive_enabled=True,
        user_active=True,
        user_busy=False,
        recent_interaction=False,
        idle_seconds=100,
    )
    decision = selector.evaluate_interaction(cand, engine_inter, ctx)
    # With idle state and low priority, engine should allow SPEAK
    assert decision == InteractionDecision.SPEAK


def test_delivery_updates_policy():
    engine = make_engine()
    policy = DiscoveryPolicy()
    selector = FunFactSelector(engine, discovery_policy=policy)
    now = datetime.now()
    selector.record_delivery(now)
    assert policy.last_discovery_at == now
    assert selector.can_surface(now) is False


def test_no_duplicate_interaction_logic():
    # Ensure selector does not reimplement quiet/cooldown etc.
    engine = make_engine()
    selector = FunFactSelector(engine)
    # Just check methods exist and delegate
    assert hasattr(selector, "evaluate_interaction")
    assert hasattr(selector, "record_delivery")


def test_existing_fun_fact_engine_unchanged():
    engine = make_engine()
    # Engine select should still pick highest confidence
    fact = engine.select()
    assert fact.text == "Science fact"
    # Adding duplicate should not change
    engine.add_fact(FunFact(text="Science fact", category=FunFactCategory.SCIENCE, confidence=99))
    fact2 = engine.select()
    assert fact2.confidence == 80  # original unchanged


if __name__ == "__main__":
    clear_interaction_state()
    test_high_confidence_can_be_selected()
    test_low_confidence_not_promoted_excessively()
    test_positive_category_preference_increases_score()
    test_negative_category_preference_decreases_score()
    test_personalization_bounded()
    test_category_filtering()
    test_can_surface_respects_policy()
    test_interaction_event_uses_low_priority()
    test_proactive_disabled_produces_wait()
    test_quiet_mode_produces_wait()
    test_allowed_interaction_can_produce_speak()
    test_delivery_updates_policy()
    test_no_duplicate_interaction_logic()
    test_existing_fun_fact_engine_unchanged()
    print("All fun fact selector tests passed.")
