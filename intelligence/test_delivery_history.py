"""
Tests for Persistent Intelligence Delivery History – Step 7.89
"""

from datetime import datetime, timedelta

from intelligence.engine import IntelligenceEngine
from intelligence.ingestion import IntelligenceIngestionEngine
from intelligence.models import IntelligenceStory, StoryCategory
from intelligence.priority import IntelligencePriority
from intelligence.queue import QueuedIntelligence
from intelligence.fun_fact_selector import FunFactSelector
from intelligence.fun_facts import FunFact, FunFactEngine, FunFactCategory
from intelligence.feedback import FeedbackProfile
from memory.database import (
    initialize_database,
    save_intelligence_delivery,
    get_intelligence_delivery_history,
    clear_intelligence_delivery_history,
    clear_intelligence_discovery_history,
)
from interaction.engine import InteractionEngine
from interaction.policy import InteractionContext, SessionState


def _clean_db():
    initialize_database()
    clear_intelligence_delivery_history()
    clear_intelligence_discovery_history()


def test_table_created_and_empty():
    _clean_db()
    rows = get_intelligence_delivery_history()
    assert isinstance(rows, list)
    assert len(rows) == 0


def test_save_and_retrieve():
    _clean_db()
    now = datetime(2026, 1, 1, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="url:http://example.com",
        title="Test",
        category="ai",
        source="test",
        url="http://example.com",
        delivered_at=now,
        delivery_type="intelligence",
        priority="important",
    )
    rows = get_intelligence_delivery_history(limit=10)
    assert len(rows) == 1
    r = rows[0]
    assert r[1] == "url:http://example.com"
    assert r[2] == "Test"
    assert r[7] == "intelligence"


def test_evaluation_does_not_persist():
    _clean_db()
    ingestion = IntelligenceIngestionEngine()
    engine = IntelligenceEngine(ingestion=ingestion)
    story = IntelligenceStory(
        title="Eval only",
        summary="",
        category=StoryCategory.AI,
        importance=50,
        severity=10,
        novelty=50,
        source="test",
    )
    # Scoring only
    engine.scorer.score(story, None, [])
    rows = get_intelligence_delivery_history()
    assert len(rows) == 0


def test_discovery_delivery_persists_and_marks_discovered():
    _clean_db()
    ingestion = IntelligenceIngestionEngine()
    engine = IntelligenceEngine(ingestion=ingestion)
    story = IntelligenceStory(
        title="Discovery story",
        summary="",
        category=StoryCategory.AI,
        importance=80,
        severity=10,
        novelty=80,
        source="test",
        url="http://example.com/disc",
    )
    qitem = QueuedIntelligence(
        story=story,
        priority=IntelligencePriority.IMPORTANT,
        added_at=datetime.now(),
    )
    candidates = engine.discovery.evaluate([qitem])
    assert len(candidates) >= 1
    candidate = candidates[0]
    interaction_engine = InteractionEngine()
    now = datetime(2026, 1, 2, 9, 0, 0)
    engine.deliver_discovery(candidate, interaction_engine, now)

    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    r = rows[0]
    assert r[7] == "discovery"
    assert r[2] == "Discovery story"
    assert engine.discovery.has_been_discovered(story)


def test_fun_fact_delivery_persists():
    _clean_db()
    ingestion = IntelligenceIngestionEngine()
    engine = IntelligenceEngine(ingestion=ingestion)
    # Override selector with deterministic fact
    fe = FunFactEngine(facts=[FunFact(text="Fun fact text", category=FunFactCategory.SCIENCE, source="test")])
    from intelligence.feedback import FeedbackProfile
    selector = FunFactSelector(fun_fact_engine=fe, feedback_profile=FeedbackProfile())
    engine.fun_fact_selector = selector
    candidate = selector.select()
    assert candidate is not None
    now = datetime(2026, 1, 3, 10, 0, 0)
    engine.deliver_fun_fact(candidate, now)

    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    r = rows[0]
    assert r[7] == "fun_fact"
    assert "fun_fact:" in r[1]


def test_humor_delivery_persists():
    _clean_db()
    ingestion = IntelligenceIngestionEngine()
    engine = IntelligenceEngine(ingestion=ingestion)
    from intelligence.humor import HumorCandidate
    cand = HumorCandidate(text="A joke", style="playful")
    interaction_engine = InteractionEngine()
    now = datetime(2026, 1, 4, 11, 0, 0)
    engine.deliver_humor(cand, interaction_engine, now)

    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    r = rows[0]
    assert r[7] == "humor"
    assert r[1].startswith("humor:")


def test_ordering_and_limit():
    _clean_db()
    base = datetime(2026, 1, 1, 0, 0, 0)
    for i in range(5):
        save_intelligence_delivery(
            story_identity=f"id{i}",
            title=f"T{i}",
            category="ai",
            source="s",
            url=None,
            delivered_at=base + timedelta(hours=i),
            delivery_type="intelligence",
            priority=None,
        )
    rows = get_intelligence_delivery_history(limit=3)
    assert len(rows) == 3
    # newest first
    assert rows[0][2] == "T4"
    assert rows[1][2] == "T3"
    assert rows[2][2] == "T2"


def test_clear_history():
    _clean_db()
    save_intelligence_delivery(
        story_identity="x",
        title="X",
        category=None,
        source=None,
        url=None,
        delivered_at=datetime.now(),
        delivery_type="intelligence",
    )
    clear_intelligence_delivery_history()
    assert len(get_intelligence_delivery_history()) == 0


def test_persistence_round_trip():
    _clean_db()
    now = datetime(2026, 1, 5, 12, 0, 0)
    save_intelligence_delivery(
        story_identity="roundtrip",
        title="RT",
        category="ai",
        source="s",
        url=None,
        delivered_at=now,
        delivery_type="intelligence",
    )
    # Simulate new process
    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    assert rows[0][1] == "roundtrip"


if __name__ == "__main__":
    test_table_created_and_empty()
    test_save_and_retrieve()
    test_evaluation_does_not_persist()
    test_discovery_delivery_persists_and_marks_discovered()
    test_fun_fact_delivery_persists()
    test_humor_delivery_persists()
    test_ordering_and_limit()
    test_clear_history()
    test_persistence_round_trip()
    print("All delivery history tests passed.")
