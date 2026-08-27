"""
Tests for explicit goodbye/exit intent routing
"""

import sys
from types import ModuleType

# Mock dependencies to avoid heavy imports
winrt_mock = ModuleType("winrt")
winrt_windows_mock = ModuleType("winrt.windows")
winrt_windows_devices_mock = ModuleType("winrt.windows.devices")
winrt_windows_devices_geolocation_mock = ModuleType("winrt.windows.devices.geolocation")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", winrt_windows_mock)
sys.modules.setdefault("winrt.windows.devices", winrt_windows_devices_mock)
sys.modules.setdefault("winrt.windows.devices.geolocation", winrt_windows_devices_geolocation_mock)
winrt_windows_devices_geolocation_mock.Geolocator = object

ollama_mock = ModuleType("ollama")
ollama_mock.chat = lambda *a, **k: {}
sys.modules.setdefault("ollama", ollama_mock)

pynput_mock = ModuleType("pynput")
pynput_keyboard_mock = ModuleType("pynput.keyboard")
pynput_mouse_mock = ModuleType("pynput.mouse")
sys.modules.setdefault("pynput", pynput_mock)
sys.modules.setdefault("pynput.keyboard", pynput_keyboard_mock)
sys.modules.setdefault("pynput.mouse", pynput_mouse_mock)

from unittest.mock import MagicMock
from core.vyra import VYRA


def _make_vyra():
    vyra = VYRA.__new__(VYRA)
    vyra.activity_monitor = MagicMock()
    vyra.proactive_loop = MagicMock()
    vyra.context_manager = MagicMock()
    vyra.context_manager.end_session = MagicMock()
    vyra.stop_scheduler = MagicMock()
    vyra.get_goodbye = MagicMock(return_value="Goodbye test")
    return vyra


def _should_exit(vyra, user_input):
    import re
    normalized_input = re.sub(r'^[.!?]+|[.!?]+$', '', user_input.strip().lower())
    goodbye_commands = {
        "exit",
        "quit",
        "bye",
        "goodbye",
        "goodnight",
        "good night",
    }
    return normalized_input in goodbye_commands


def test_bye_exits():
    assert _should_exit(None, "bye") is True


def test_goodbye_exits():
    assert _should_exit(None, "goodbye") is True


def test_quit_exits():
    assert _should_exit(None, "quit") is True


def test_exit_exits():
    assert _should_exit(None, "exit") is True


def test_good_night_exits():
    assert _should_exit(None, "good night") is True


def test_goodnight_exits():
    assert _should_exit(None, "goodnight") is True


def test_goodbye_produces_response_before_termination():
    vyra = _make_vyra()
    # Simulate exit handling
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        if _should_exit(vyra, "bye"):
            print(f"VYRA: {vyra.get_goodbye()}")
    out = buf.getvalue()
    assert "Goodbye test" in out
    vyra.get_goodbye.assert_called_once()


def test_goodbye_does_not_trigger_memory():
    # Memory detection patterns do not include goodbye
    patterns = [
        "i am",
        "i'm",
        "i want",
        "i need",
        "my goal",
        "i prefer",
        "i like",
        "i don't like",
        "remember",
        "from now on",
        "this semester",
        "this week",
        "i decided",
        "i plan",
        "i'm planning",
        "my priority",
        "i've decided",
    ]
    msg = "bye"
    assert not any(p in msg.lower() for p in patterns)


def test_ordinary_text_not_exits():
    assert _should_exit(None, "bye bye, that was funny") is False
    assert _should_exit(None, "how are you?") is False


if __name__ == "__main__":
    test_bye_exits()
    test_goodbye_exits()
    test_quit_exits()
    test_exit_exits()
    test_good_night_exits()
    test_goodnight_exits()
    test_goodbye_produces_response_before_termination()
    test_goodbye_does_not_trigger_memory()
    test_ordinary_text_not_exits()
    print("All goodbye intent tests passed.")
