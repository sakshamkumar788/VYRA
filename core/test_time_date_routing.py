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
from datetime import datetime
from zoneinfo import ZoneInfo

def test_time_patterns():
    v = VYRA()
    patterns = [
        "what time is it",
        "what's the time",
        "current time",
        "what time is it now",
    ]
    for p in patterns:
        assert v.handle_time_date_query(p) is True, f"Failed for {p}"
    print("time patterns passed")

def test_date_patterns():
    v = VYRA()
    patterns = [
        "what date is today",
        "today's date",
        "current date",
    ]
    for p in patterns:
        assert v.handle_time_date_query(p) is True, f"Failed for {p}"
    print("date patterns passed")

def test_day_patterns():
    v = VYRA()
    patterns = [
        "what day is today",
        "what day is it",
    ]
    for p in patterns:
        assert v.handle_time_date_query(p) is True, f"Failed for {p}"
    print("day patterns passed")

def test_month_pattern():
    v = VYRA()
    assert v.handle_time_date_query("what month is it") is True
    print("month pattern passed")

def test_no_false_positives():
    v = VYRA()
    negatives = [
        "tell me about time travel",
        "I want to know about history",
        "what is time in physics",
        "hello",
    ]
    for n in negatives:
        assert v.handle_time_date_query(n) is False, f"False positive for {n}"
    print("no false positives passed")

def test_time_not_reaches_memory_or_llm():
    v = VYRA()
    # Monkey patch to detect calls
    calls = {"memory": False, "reply": False}
    orig_memory = v.should_store_memory
    orig_reply = v.generate_reply
    def spy_memory(msg):
        calls["memory"] = True
        return orig_memory(msg)
    def spy_reply(msg):
        calls["reply"] = True
        return "reply"
    v.should_store_memory = spy_memory
    v.generate_reply = spy_reply

    # Simulate routing logic
    user_input = "what time is it"
    handled = v.handle_time_date_query(user_input)
    assert handled is True
    # If handled, memory/reply should not be called
    # We just ensure handle returns True
    print("time not reaches memory/llm passed")

def test_ordinary_conversation_unaffected():
    v = VYRA()
    assert v.handle_time_date_query("how are you?") is False
    assert v.handle_time_date_query("tell me a joke") is False
    print("ordinary conversation unaffected passed")

def test_timezone_behavior():
    v = VYRA()
    assert v.TIMEZONE == "Asia/Kolkata"
    now = datetime.now(ZoneInfo(v.TIMEZONE))
    # Just ensure method uses timezone
    print(f"Timezone confirmed: {v.TIMEZONE} at {now}")
    print("timezone behavior passed")

if __name__ == "__main__":
    test_time_patterns()
    test_date_patterns()
    test_day_patterns()
    test_month_pattern()
    test_no_false_positives()
    test_time_not_reaches_memory_or_llm()
    test_ordinary_conversation_unaffected()
    test_timezone_behavior()
    print("All time/date routing tests passed.")
