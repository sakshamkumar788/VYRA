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

import io
from contextlib import redirect_stdout, redirect_stderr
from morning.facts import MorningFactsCollector

class FailingCalendar:
    def get_events(self, start, end):
        raise RuntimeError("calendar down")

class FailingNews:
    def get_latest(self, limit=5):
        raise RuntimeError("news down")

def test_morning_calendar_failure_logged():
    collector = MorningFactsCollector(calendar_provider=FailingCalendar(), news_provider=None)
    # Mock get_weather to avoid real call
    import tools.weather as weather_mod
    orig = weather_mod.get_weather
    weather_mod.get_weather = lambda *a, **k: "Temperature: 25C\nConditions: Clear"
    try:
        out = io.StringIO()
        with redirect_stdout(out):
            ctx = collector.collect()
        output = out.getvalue()
        assert "MorningFactsCollector warning: calendar provider failed" in output
        assert ctx.important_events == []
    finally:
        weather_mod.get_weather = orig
    print("morning calendar failure logged passed")

def test_morning_news_failure_logged():
    collector = MorningFactsCollector(calendar_provider=None, news_provider=FailingNews())
    import tools.weather as weather_mod
    orig = weather_mod.get_weather
    weather_mod.get_weather = lambda *a, **k: "Temperature: 25C\nConditions: Clear"
    try:
        out = io.StringIO()
        with redirect_stdout(out):
            ctx = collector.collect()
        output = out.getvalue()
        assert "MorningFactsCollector warning: news provider failed" in output
        assert ctx.news_items == []
    finally:
        weather_mod.get_weather = orig
    print("morning news failure logged passed")

def test_morning_weather_failure_logged():
    class GoodCalendar:
        def get_events(self, start, end):
            return []
    collector = MorningFactsCollector(calendar_provider=GoodCalendar(), news_provider=None)
    import morning.facts as facts_mod
    orig = facts_mod.get_weather
    def raise_err(*a, **k):
        raise RuntimeError("weather down")
    facts_mod.get_weather = raise_err
    try:
        out = io.StringIO()
        with redirect_stdout(out):
            ctx = collector.collect()
        output = out.getvalue()
        # Debug
        if "MorningFactsCollector warning: weather provider failed" not in output:
            print("DEBUG output:", output)
        assert "MorningFactsCollector warning: weather provider failed" in output
        assert ctx.weather is None
    finally:
        facts_mod.get_weather = orig
    print("morning weather failure logged passed")

def test_rss_source_download_failure_logged():
    from intelligence.real_sources import RSSIntelligenceSource
    src = RSSIntelligenceSource(feed_url="http://invalid", source_name="test", category="ai", source_trust=1, timeout=1)
    out = io.StringIO()
    with redirect_stdout(out):
        stories = src.fetch()
    output = out.getvalue()
    assert stories == []
    assert "RSSIntelligenceSource warning: download failed" in output
    print("rss download failure logged passed")

def test_rss_source_parse_failure_logged():
    from intelligence.real_sources import RSSIntelligenceSource
    src = RSSIntelligenceSource(feed_url="http://invalid", source_name="test", category="ai", source_trust=1)
    # Monkey patch download to return bad xml
    orig = src._download_feed
    src._download_feed = lambda: b"not xml"
    out = io.StringIO()
    with redirect_stdout(out):
        stories = src.fetch()
    output = out.getvalue()
    assert stories == []
    assert "RSSIntelligenceSource warning: XML parse failed" in output
    print("rss parse failure logged passed")

def test_calculator_safe_error():
    from tools.calculator import calculate
    assert calculate("2+2") == "4"
    assert calculate("import os") == "I couldn't calculate that expression."
    print("calculator safe error passed")

if __name__ == "__main__":
    test_morning_calendar_failure_logged()
    test_morning_news_failure_logged()
    test_morning_weather_failure_logged()
    test_rss_source_download_failure_logged()
    test_rss_source_parse_failure_logged()
    test_calculator_safe_error()
    print("All silent exception tests passed.")
