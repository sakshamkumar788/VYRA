"""
D-14 evaluation vs delivery contract tests.
"""
from datetime import datetime
from unittest.mock import MagicMock

from intelligence.engine import IntelligenceEngine
from intelligence.ingestion import IntelligenceIngestionEngine
from intelligence.models import IntelligenceStory, StoryCategory
from intelligence.priority import IntelligencePriority
from intelligence.queue import QueuedIntelligence
from intelligence.fun_facts import FunFact, FunFactEngine, FunFactCategory
from intelligence.fun_fact_selector import FunFactSelector
from intelligence.feedback import FeedbackProfile
from intelligence.humor import HumorCandidate
from memory.database import (
    initialize_database,
    clear_intelligence_delivery_history,
    clear_intelligence_discovery_history,
    get_intelligence_delivery_history,
    clear_interaction_state,
)
from interaction.engine import InteractionEngine
from interaction.policy import InteractionContext, SessionState

def _clean():
    initialize_database()
    clear_intelligence_delivery_history()
    clear_intelligence_discovery_history()
    clear_interaction_state()

def test_evaluation_creates_no_delivery_history():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="Eval", summary="", category=StoryCategory.AI, importance=50, severity=10, novelty=50, source="test")
    # evaluation only
    engine.scorer.score(story, None, [])
    rows = get_intelligence_delivery_history()
    assert len(rows) == 0
    print("evaluation creates no delivery history passed")

def test_evaluation_does_not_mark_discovered():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="Disc", summary="", category=StoryCategory.AI, importance=80, severity=10, novelty=80, source="test", url="http://example.com/d")
    qitem = QueuedIntelligence(story=story, priority=IntelligencePriority.IMPORTANT, added_at=datetime.now())
    candidates = engine.discovery.evaluate([qitem])
    assert len(candidates) >= 1
    # evaluation should not mark discovered
    assert not engine.discovery.has_been_discovered(story)
    print("evaluation does not mark discovered passed")

def test_evaluation_does_not_increment_proactive_state():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="H", summary="", category=StoryCategory.AI, importance=80, severity=10, novelty=80, source="test", url="http://ex.com")
    qitem = QueuedIntelligence(story=story, priority=IntelligencePriority.IMPORTANT, added_at=datetime.now())
    candidates = engine.discovery.evaluate([qitem])
    candidate = candidates[0]
    inter = InteractionEngine()
    before = inter._daily_proactive_count
    before_last = inter.last_proactive_interaction
    ctx = InteractionContext(current_time=datetime.now(), session_state=SessionState.IDLE, proactive_enabled=True, user_active=True, user_busy=False, recent_interaction=False, idle_seconds=100)
    decision = engine.evaluate_discovery(candidate, inter, ctx)
    # decision may be SPEAK/WAIT but no recording
    assert inter._daily_proactive_count == before
    assert inter.last_proactive_interaction == before_last
    print("evaluation does not increment proactive state passed")

def test_actual_discovery_delivery_records_history_and_marks_discovered():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="Del", summary="", category=StoryCategory.AI, importance=80, severity=10, novelty=80, source="test", url="http://ex.com/del")
    qitem = QueuedIntelligence(story=story, priority=IntelligencePriority.INTERESTING, added_at=datetime.now())
    candidates = engine.discovery.evaluate([qitem])
    candidate = candidates[0]
    inter = InteractionEngine()
    before = inter._daily_proactive_count
    now = datetime(2026,1,1,12,0,0)
    engine.deliver_discovery(candidate, inter, now)
    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    assert rows[0][7] == "discovery"
    assert engine.discovery.has_been_discovered(story)
    assert inter._daily_proactive_count == before + 1
    print("actual discovery delivery records history and marks discovered passed")

def test_actual_fun_fact_delivery_records_delivery_history():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    fe = FunFactEngine(facts=[FunFact(text="Test fact", category=FunFactCategory.SCIENCE, source="test")])
    selector = FunFactSelector(fun_fact_engine=fe, feedback_profile=FeedbackProfile())
    engine.fun_fact_selector = selector
    candidate = selector.select()
    now = datetime(2026,1,1,13,0,0)
    engine.deliver_fun_fact(candidate, now)
    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    assert rows[0][7] == "fun_fact"
    print("actual fun-fact delivery records delivery history passed")

def test_actual_humor_delivery_records_delivery_history():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    cand = HumorCandidate(text="Joke", style="playful")
    inter = InteractionEngine()
    before = inter._daily_proactive_count
    now = datetime(2026,1,1,14,0,0)
    engine.deliver_humor(cand, inter, now)
    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    assert rows[0][7] == "humor"
    assert inter._daily_proactive_count == before + 1
    print("actual humor delivery records delivery history passed")

def test_actual_delivery_updates_proactive_state():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="State", summary="", category=StoryCategory.AI, importance=80, severity=10, novelty=80, source="test", url="http://ex.com/state")
    qitem = QueuedIntelligence(story=story, priority=IntelligencePriority.INTERESTING, added_at=datetime.now())
    candidate = engine.discovery.evaluate([qitem])[0]
    inter = InteractionEngine()
    before = inter._daily_proactive_count
    now = datetime(2026,1,1,15,0,0)
    engine.deliver_discovery(candidate, inter, now)
    assert inter.last_proactive_interaction == now
    assert inter._daily_proactive_count == before + 1
    print("actual delivery updates proactive state passed")

def test_repeated_evaluation_no_duplicate_delivery():
    _clean()
    engine = IntelligenceEngine(ingestion=IntelligenceIngestionEngine())
    story = IntelligenceStory(title="Dup", summary="", category=StoryCategory.AI, importance=80, severity=10, novelty=80, source="test", url="http://ex.com/dup")
    qitem = QueuedIntelligence(story=story, priority=IntelligencePriority.IMPORTANT, added_at=datetime.now())
    candidate = engine.discovery.evaluate([qitem])[0]
    inter = InteractionEngine()
    now = datetime(2026,1,1,16,0,0)
    # evaluate multiple times
    for _ in range(3):
        engine.evaluate_discovery(candidate, inter, InteractionContext(current_time=now, session_state=SessionState.IDLE, proactive_enabled=True, user_active=True, user_busy=False, recent_interaction=False, idle_seconds=100))
    # no delivery yet
    rows = get_intelligence_delivery_history()
    assert len(rows) == 0
    # now deliver once
    engine.deliver_discovery(candidate, inter, now)
    rows = get_intelligence_delivery_history()
    assert len(rows) == 1
    # second delivery would create duplicate if called again – delivery is separate
    print("repeated evaluation does not create duplicate delivery records passed")

if __name__ == "__main__":
    test_evaluation_creates_no_delivery_history()
    test_evaluation_does_not_mark_discovered()
    test_evaluation_does_not_increment_proactive_state()
    test_actual_discovery_delivery_records_history_and_marks_discovered()
    test_actual_fun_fact_delivery_records_delivery_history()
    test_actual_humor_delivery_records_delivery_history()
    test_actual_delivery_updates_proactive_state()
    test_repeated_evaluation_no_duplicate_delivery()
    print("All D-14 contract tests passed.")
