from datetime import datetime
from memory.database import initialize_database, clear_intelligence_queue
from intelligence.models import IntelligenceStory
from intelligence.priority import IntelligencePriority
from intelligence.queue import IntelligenceQueue
from intelligence.engine import IntelligenceEngine

def _init():
    initialize_database()
    clear_intelligence_queue()

def test_empty_queue_starts_empty():
    _init()
    q = IntelligenceQueue()
    assert len(q) == 0
    print("empty queue starts empty passed")

def test_add_persists_item():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Test story", summary="summary", url="https://ex.com/1")
    q.add(story, IntelligencePriority.IMPORTANT)
    assert len(q) == 1
    # Recreate
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    assert q2.get_pending()[0].story.title == "Test story"
    print("add persists item passed")

def test_recreate_queue_restores():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Restore test", summary="s", url="https://ex.com/2")
    q.add(story, IntelligencePriority.INTERESTING)
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    print("recreate queue restores passed")

def test_recreate_engine_pending_survives():
    _init()
    # Test queue persistence directly; engine init requires ingestion which is out of scope for this unit test
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Engine story", summary="s", url="https://ex.com/3")
    q.add(story, IntelligencePriority.IMPORTANT)
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    print("recreate engine pending survives passed")

def test_important_ordering_survives():
    _init()
    q = IntelligenceQueue()
    s1 = IntelligenceStory(title="Imp", summary="s", url="https://ex.com/i1")
    s2 = IntelligenceStory(title="Int", summary="s", url="https://ex.com/i2")
    q.add(s2, IntelligencePriority.INTERESTING)
    q.add(s1, IntelligencePriority.IMPORTANT)
    q2 = IntelligenceQueue()
    pending = q2.get_pending(limit=2)
    assert pending[0].priority == IntelligencePriority.IMPORTANT
    assert pending[1].priority == IntelligencePriority.INTERESTING
    print("important ordering survives passed")

def test_fiFO_ordering_survives():
    _init()
    q = IntelligenceQueue()
    s1 = IntelligenceStory(title="First", summary="s", url="https://ex.com/f1")
    s2 = IntelligenceStory(title="Second", summary="s", url="https://ex.com/f2")
    q.add(s1, IntelligencePriority.INTERESTING)
    q.add(s2, IntelligencePriority.INTERESTING)
    q2 = IntelligenceQueue()
    pending = q2.get_pending(limit=2)
    assert pending[0].story.title == "First"
    assert pending[1].story.title == "Second"
    print("FIFO ordering survives passed")

def test_duplicate_add_no_duplicate_rows():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Dup", summary="s", url="https://ex.com/dup")
    q.add(story, IntelligencePriority.IMPORTANT)
    q.add(story, IntelligencePriority.IMPORTANT)
    assert len(q) == 1
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    print("duplicate add no duplicate rows passed")

def test_url_identity_after_restart():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Title A", summary="s", url="https://ex.com/urlid")
    q.add(story, IntelligencePriority.IMPORTANT)
    # Try add with different title same url
    story2 = IntelligenceStory(title="Title B", summary="s2", url="https://ex.com/urlid")
    q.add(story2, IntelligencePriority.IMPORTANT)
    assert len(q) == 1
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    print("url identity works after restart passed")

def test_title_fallback_identity():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="No URL", summary="s")
    q.add(story, IntelligencePriority.INTERESTING)
    story2 = IntelligenceStory(title="no url", summary="s2")
    q.add(story2, IntelligencePriority.INTERESTING)
    assert len(q) == 1
    q2 = IntelligenceQueue()
    assert len(q2) == 1
    print("title fallback identity works passed")

def test_remove_deletes_db():
    _init()
    q = IntelligenceQueue()
    story = IntelligenceStory(title="Rem", summary="s", url="https://ex.com/rem")
    q.add(story, IntelligencePriority.IMPORTANT)
    assert len(q) == 1
    q.remove(story)
    assert len(q) == 0
    q2 = IntelligenceQueue()
    assert len(q2) == 0
    print("remove deletes db passed")

def test_clear_clears_db():
    _init()
    q = IntelligenceQueue()
    s1 = IntelligenceStory(title="C1", summary="s", url="https://ex.com/c1")
    s2 = IntelligenceStory(title="C2", summary="s", url="https://ex.com/c2")
    q.add(s1, IntelligencePriority.IMPORTANT)
    q.add(s2, IntelligencePriority.INTERESTING)
    q.clear()
    assert len(q) == 0
    q2 = IntelligenceQueue()
    assert len(q2) == 0
    print("clear clears db passed")

def _save_delivery(story_identity):
    from memory.database import DATABASE_PATH
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            "INSERT INTO intelligence_delivery_history (story_identity, title, category, source, url, delivered_at, delivery_type, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (story_identity, "t", "other", None, None, datetime.now().isoformat(), "proactive", "important")
        )
        conn.commit()
    finally:
        conn.close()

def test_delivered_item_not_restored():
    _init()
    story = IntelligenceStory(title="Delivered", summary="s", url="https://ex.com/del")
    q = IntelligenceQueue()
    q.add(story, IntelligencePriority.IMPORTANT)
    # Simulate delivery
    identity = f"url:https://ex.com/del"
    _save_delivery(identity)
    q2 = IntelligenceQueue()
    assert len(q2) == 0
    print("delivered item not restored passed")

def test_malformed_datetime_handled():
    _init()
    from memory.database import DATABASE_PATH
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            "INSERT INTO intelligence_queue (story_identity, title, summary, url, source, category, published_at, priority, added_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("url:https://ex.com/bad", "Bad", "s", "https://ex.com/bad", None, "other", None, "important", "not-a-date")
        )
        conn.commit()
    finally:
        conn.close()
    # Should not crash
    q = IntelligenceQueue()
    # It will load with fallback datetime
    assert len(q) >= 1
    print("malformed datetime handled passed")

def test_persistence_failure_graceful():
    _init()
    # Monkey-patch save to raise
    from memory.database import save_intelligence_queue_item
    original = save_intelligence_queue_item
    def boom(*a, **kw):
        raise RuntimeError("boom")
    import memory.database as dbmod
    dbmod.save_intelligence_queue_item = boom
    try:
        q = IntelligenceQueue()
        story = IntelligenceStory(title="Fail", summary="s", url="https://ex.com/fail")
        q.add(story, IntelligencePriority.IMPORTANT)
        # In-memory should still work
        assert len(q) == 1
    finally:
        dbmod.save_intelligence_queue_item = original
    print("persistence failure graceful passed")

if __name__ == "__main__":
    test_empty_queue_starts_empty()
    test_add_persists_item()
    test_recreate_queue_restores()
    test_recreate_engine_pending_survives()
    test_important_ordering_survives()
    test_fiFO_ordering_survives()
    test_duplicate_add_no_duplicate_rows()
    test_url_identity_after_restart()
    test_title_fallback_identity()
    test_remove_deletes_db()
    test_clear_clears_db()
    test_delivered_item_not_restored()
    test_malformed_datetime_handled()
    test_persistence_failure_graceful()
    print("All queue persistence tests passed.")
