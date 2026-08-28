"""
Tests for InteractionEngine persistence across restarts – D-07
"""
import sys
from types import ModuleType
from datetime import datetime, timedelta
from unittest.mock import patch

# Mock dependencies to avoid heavy imports
winrt_mock = ModuleType("winrt")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", ModuleType("winrt.windows"))
sys.modules.setdefault("winrt.windows.devices", ModuleType("winrt.windows.devices"))
sys.modules.setdefault("winrt.windows.devices.geolocation", ModuleType("winrt.windows.devices.geolocation"))

from interaction.engine import InteractionEngine
from interaction.policy import InteractionEvent, InteractionPriority
from memory.database import initialize_database, save_interaction_state, load_interaction_state

def clear_state():
    # Clear interaction_state table for test isolation
    import sqlite3
    from memory.database import DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("DELETE FROM interaction_state")
        conn.commit()
    finally:
        conn.close()

def test_fresh_engine():
    clear_state()
    engine = InteractionEngine()
    assert engine.last_proactive_interaction is None
    assert engine._daily_proactive_count == 0
    print("Fresh engine test passed.")

def test_persistence_after_interaction():
    clear_state()
    engine = InteractionEngine()
    fixed_time = datetime(2025, 1, 1, 12, 0, 0)
    event = InteractionEvent(event_type="test", message="hi", priority=InteractionPriority.NORMAL)
    engine.record_proactive_interaction(event, fixed_time)
    # Recreate
    engine2 = InteractionEngine()
    assert engine2.last_proactive_interaction == fixed_time
    assert engine2._daily_proactive_count == 1
    print("Persistence after interaction test passed.")

def test_cooldown_survives_restart():
    clear_state()
    engine = InteractionEngine()
    now = datetime(2025, 1, 1, 12, 0, 0)
    event = InteractionEvent(event_type="test", message="hi", priority=InteractionPriority.NORMAL)
    engine.record_proactive_interaction(event, now)
    engine2 = InteractionEngine()
    assert engine2.is_in_cooldown(now + timedelta(minutes=10)) is True
    print("Cooldown survives restart test passed.")

def test_daily_count_survives_restart():
    clear_state()
    engine = InteractionEngine()
    # Manually persist count 2
    save_interaction_state("daily_proactive_count", "2")
    save_interaction_state("daily_interaction_date", datetime.now().date().isoformat())
    engine2 = InteractionEngine()
    assert engine2._daily_proactive_count == 2
    print("Daily count survives restart test passed.")

def test_daily_reset_after_restart():
    clear_state()
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    save_interaction_state("daily_interaction_date", yesterday)
    save_interaction_state("daily_proactive_count", "5")
    engine = InteractionEngine()
    # Trigger reset via evaluate
    from interaction.policy import InteractionContext
    from context.context import SessionState
    ctx = InteractionContext(current_time=datetime.now(), session_state=SessionState.IDLE)
    engine._reset_daily_counter_if_needed(ctx.current_time)
    assert engine._daily_proactive_count == 0
    assert engine._daily_interaction_date == datetime.now().date()
    print("Daily reset after restart test passed.")

def test_last_proactive_survives_daily_reset():
    clear_state()
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    now = datetime.now()
    save_interaction_state("daily_interaction_date", yesterday)
    save_interaction_state("daily_proactive_count", "5")
    save_interaction_state("last_proactive_interaction", now.isoformat())
    engine = InteractionEngine()
    # Force reset
    from interaction.policy import InteractionContext
    from context.context import SessionState
    ctx = InteractionContext(current_time=datetime.now(), session_state=SessionState.IDLE)
    engine._reset_daily_counter_if_needed(ctx.current_time)
    assert engine._daily_proactive_count == 0
    assert engine.last_proactive_interaction == now
    print("Last proactive survives daily reset test passed.")

def test_recent_events_ephemeral():
    clear_state()
    engine = InteractionEngine()
    event = InteractionEvent(event_type="test", message="hi", priority=InteractionPriority.NORMAL)
    engine.record_proactive_interaction(event, datetime.now())
    assert "test" in engine._recent_event_types
    engine2 = InteractionEngine()
    assert engine2._recent_event_types == []
    print("Recent events ephemeral test passed.")

def test_quiet_mode_ephemeral():
    clear_state()
    engine = InteractionEngine()
    engine.set_quiet_mode(True)
    assert engine.quiet_mode is True
    engine2 = InteractionEngine()
    assert engine2.quiet_mode is False
    print("Quiet mode ephemeral test passed.")

def test_persistence_failure_graceful():
    clear_state()
    # Patch save to raise
    with patch("memory.database.save_interaction_state", side_effect=Exception("db error")):
        engine = InteractionEngine()
        event = InteractionEvent(event_type="test", message="hi", priority=InteractionPriority.NORMAL)
        try:
            engine.record_proactive_interaction(event, datetime.now())
        except Exception as e:
            assert False, f"Engine crashed on persistence failure: {e}"
    print("Persistence failure graceful test passed.")

if __name__ == "__main__":
    initialize_database()
    test_fresh_engine()
    test_persistence_after_interaction()
    test_cooldown_survives_restart()
    test_daily_count_survives_restart()
    test_daily_reset_after_restart()
    test_last_proactive_survives_daily_reset()
    test_recent_events_ephemeral()
    test_quiet_mode_ephemeral()
    test_persistence_failure_graceful()
    print("All interaction persistence tests passed.")
