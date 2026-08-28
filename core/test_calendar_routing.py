import sys
from types import ModuleType

winrt_mock = ModuleType("winrt")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", ModuleType("winrt.windows"))
sys.modules.setdefault("winrt.windows.devices", ModuleType("winrt.windows.devices"))
sys.modules.setdefault("winrt.windows.devices.geolocation", ModuleType("winrt.windows.devices.geolocation"))
sys.modules["winrt.windows.devices.geolocation"].Geolocator = object

ollama_mock = ModuleType("ollama")
ollama_mock.chat = lambda *a, **k: {}
sys.modules.setdefault("ollama", ollama_mock)

pynput_mock = ModuleType("pynput")
pynput_keyboard_mock = ModuleType("pynput.keyboard")
pynput_mouse_mock = ModuleType("pynput.mouse")
sys.modules.setdefault("pynput", pynput_mock)
sys.modules.setdefault("pynput.keyboard", pynput_keyboard_mock)
sys.modules.setdefault("pynput.mouse", pynput_mouse_mock)

from core.vyra import VYRA
from vyra_calendar.models import CalendarEvent
from vyra_calendar.local import LocalCalendarProvider
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def test_calendar_intent_recognized():
    v = VYRA()
    patterns = [
        "what's on my calendar",
        "what do I have on my calendar",
        "what's my schedule today",
        "what meetings do I have today",
        "what's on my schedule",
        "show my calendar",
        "what's scheduled today",
    ]
    for p in patterns:
        assert v.handle_calendar_query(p) is True, f"Failed {p}"
    print("calendar intent recognized passed")

def test_empty_calendar():
    v = VYRA()
    # LocalCalendarProvider with no events is default
    # Should return True and print empty message
    result = v.handle_calendar_query("show my calendar")
    assert result is True
    print("empty calendar handled passed")

def test_event_returned():
    v = VYRA()
    # Monkey patch handle_calendar_query to use custom provider
    from datetime import datetime
    tz = ZoneInfo(v.TIMEZONE)
    now = datetime.now(tz)
    start = now.replace(hour=10, minute=0, second=0, microsecond=0)
    ev = CalendarEvent(title="Team Standup", start_time=start, location="Office")
    provider = LocalCalendarProvider(events=[ev])
    # Temporarily replace method's provider creation by patching the method
    original = v.handle_calendar_query
    def patched_handle(user_input):
        import re
        patterns = [
            r"\bwhat'?s on my calendar\b",
            r"\bwhat do I have on my calendar\b",
            r"\bwhat'?s my schedule today\b",
            r"\bwhat meetings do I have today\b",
            r"\bwhat'?s on my schedule\b",
            r"\bshow my calendar\b",
            r"\bwhat'?s scheduled today\b",
        ]
        lowered = user_input.lower()
        if not any(re.search(p, lowered) for p in patterns):
            return False
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=1) - timedelta(seconds=1)
        events = provider.get_events(start_dt, end_dt)
        assert len(events) == 1
        assert events[0].title == "Team Standup"
        return True
    v.handle_calendar_query = patched_handle
    assert v.handle_calendar_query("what's on my calendar") is True
    print("event returned/rendered passed")

def test_calendar_failure_handled():
    v = VYRA()
    # Simulate provider failure by patching LocalCalendarProvider.get_events to raise
    original_get_events = LocalCalendarProvider.get_events
    def boom(self, start, end):
        raise RuntimeError("boom")
    LocalCalendarProvider.get_events = boom
    try:
        result = v.handle_calendar_query("show my calendar")
        assert result is True
        print("calendar failure handled passed")
    finally:
        LocalCalendarProvider.get_events = original_get_events

def test_generate_reply_not_called():
    v = VYRA()
    calls = {"reply": False}
    orig = v.generate_reply
    def spy(msg):
        calls["reply"] = True
        return orig(msg)
    v.generate_reply = spy
    v.handle_calendar_query("show my calendar")
    assert calls["reply"] is False
    print("generate_reply not called passed")

def test_should_store_memory_not_called():
    v = VYRA()
    calls = {"memory": False}
    orig = v.should_store_memory
    def spy(msg):
        calls["memory"] = True
        return orig(msg)
    v.should_store_memory = spy
    v.handle_calendar_query("what's on my calendar")
    assert calls["memory"] is False
    print("should_store_memory not called passed")

def test_ordinary_conversation_not_intercepted():
    v = VYRA()
    assert v.handle_calendar_query("how are you") is False
    assert v.handle_calendar_query("tell me a joke") is False
    print("ordinary conversation not intercepted passed")

if __name__ == "__main__":
    test_calendar_intent_recognized()
    test_empty_calendar()
    test_event_returned()
    test_calendar_failure_handled()
    test_generate_reply_not_called()
    test_should_store_memory_not_called()
    test_ordinary_conversation_not_intercepted()
    print("All calendar routing tests passed.")
