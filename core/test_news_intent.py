"""Tests for news/current-affairs intent handling in core.vyra."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
from intelligence.models import IntelligenceStory, StoryCategory
from intelligence.ingestion import IngestedStory

# Mock winrt before importing vyra
winrt_mock = ModuleType("winrt")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", ModuleType("winrt.windows"))
sys.modules.setdefault("winrt.windows.devices", ModuleType("winrt.windows.devices"))
sys.modules.setdefault("winrt.windows.devices.geolocation", ModuleType("winrt.windows.devices.geolocation"))
sys.modules["winrt.windows.devices.geolocation"].Geolocator = object

# Mock ollama
ollama_mock = ModuleType("ollama")
ollama_mock.chat = lambda *a, **k: {}
sys.modules.setdefault("ollama", ollama_mock)

# Mock pynput
pynput_mock = ModuleType("pynput")
pynput_keyboard_mock = ModuleType("pynput.keyboard")
pynput_mouse_mock = ModuleType("pynput.mouse")
sys.modules.setdefault("pynput", pynput_mock)
sys.modules.setdefault("pynput.keyboard", pynput_keyboard_mock)
sys.modules.setdefault("pynput.mouse", pynput_mouse_mock)

from core.vyra import VYRA


def make_vyra():
    # Create instance without __init__
    return VYRA.__new__(VYRA)


def test_intent_recognition():
    vyra = make_vyra()
    patterns = [
        "news",
        "news?",
        "latest news",
        "what's in the news",
        "what is in the news",
        "current affairs",
        "latest current affairs",
        "what's happening",
        "what is happening",
        "what's happening in India",
        "what is happening in India",
        "what's happening in Punjab",
        "what is happening in Punjab",
    ]
    for p in patterns:
        assert vyra.handle_current_affairs_query(p) is True, f"Failed to recognize: {p}"
    # Should not match
    assert vyra.handle_current_affairs_query("how are you?") is False
    assert vyra.handle_current_affairs_query("tell me about happening") is False
    print("Intent recognition OK")


@patch('intelligence.registry.default_source_registry')
@patch('intelligence.setup.build_ingestion_engine')
def test_no_llm_fallback_on_empty(mock_build, mock_registry):
    vyra = make_vyra()

    mock_ingestion = MagicMock()
    mock_ingestion.fetch_all.return_value = []
    mock_build.return_value = mock_ingestion

    # Patch CurrentAffairsFormatter.format to return known message
    with patch('intelligence.current_affairs_formatter.CurrentAffairsFormatter.format', return_value="I couldn't find any current developments worth summarizing right now."):
        handled = vyra.handle_current_affairs_query("news?")
        assert handled is True
    print("Empty source grounded message OK")


@patch('intelligence.registry.default_source_registry')
@patch('intelligence.setup.build_ingestion_engine')
def test_real_story_passed_through(mock_build, mock_registry):
    vyra = make_vyra()

    story = IntelligenceStory(
        title="Test headline",
        summary="Test summary",
        source="Test Source",
        category=StoryCategory.INDIA,
    )
    ingested = IngestedStory(story=story, source_name="TestSource")
    mock_ingestion = MagicMock()
    mock_ingestion.fetch_all.return_value = [ingested]
    mock_build.return_value = mock_ingestion

    # Mock formatter to include title and source
    with patch('intelligence.current_affairs_formatter.CurrentAffairsFormatter.format', return_value="India:\n 1. Test headline (Test Source)\n   Test summary\n") as mock_fmt:
        handled = vyra.handle_current_affairs_query("latest news")
        assert handled is True
        assert mock_fmt.called
    print("Real story pass-through OK")


@patch('intelligence.registry.default_source_registry')
@patch('intelligence.setup.build_ingestion_engine')
def test_generate_reply_not_called(mock_build, mock_registry):
    vyra = make_vyra()
    mock_ingestion = MagicMock()
    mock_ingestion.fetch_all.return_value = []
    mock_build.return_value = mock_ingestion

    called = []
    def spy(*args, **kwargs):
        called.append(True)
        return "LLM"
    vyra.generate_reply = spy

    with patch('intelligence.current_affairs_formatter.CurrentAffairsFormatter.format', return_value="I couldn't find any current developments worth summarizing right now."):
        vyra.handle_current_affairs_query("news?")
    assert len(called) == 0
    print("generate_reply not called OK")


@patch('intelligence.registry.default_source_registry')
@patch('intelligence.setup.build_ingestion_engine')
def test_should_store_memory_not_called(mock_build, mock_registry):
    vyra = make_vyra()
    mock_ingestion = MagicMock()
    mock_ingestion.fetch_all.return_value = []
    mock_build.return_value = mock_ingestion

    called = []
    def spy(*args, **kwargs):
        called.append(True)
    vyra.should_store_memory = spy

    with patch('intelligence.current_affairs_formatter.CurrentAffairsFormatter.format', return_value="I couldn't find any current developments worth summarizing right now."):
        vyra.handle_current_affairs_query("latest news")
    assert len(called) == 0
    print("should_store_memory not called OK")


def test_ordinary_conversation_not_intercepted():
    vyra = make_vyra()
    assert vyra.handle_current_affairs_query("how are you?") is False
    assert vyra.handle_current_affairs_query("tell me a joke") is False
    print("ordinary conversation not intercepted OK")


@patch('intelligence.registry.default_source_registry')
@patch('intelligence.setup.build_ingestion_engine')
def test_source_failure_grounded(mock_build, mock_registry):
    vyra = make_vyra()
    mock_build.side_effect = Exception("boom")
    handled = vyra.handle_current_affairs_query("news?")
    assert handled is True
    print("source failure grounded OK")


if __name__ == "__main__":
    test_intent_recognition()
    test_no_llm_fallback_on_empty()
    test_real_story_passed_through()
    test_generate_reply_not_called()
    test_should_store_memory_not_called()
    test_ordinary_conversation_not_intercepted()
    test_source_failure_grounded()
    print("All news intent tests passed.")
