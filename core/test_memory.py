"""
Deterministic tests for memory detection D-03.
"""

import sys
from types import ModuleType

# Mock external deps before importing VYRA
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
from unittest.mock import patch


def make_vyra():
    return VYRA.__new__(VYRA)


def test_must_not_trigger():
    vyra = make_vyra()
    must_not = [
        "I am talking to you.",
        "How are you?",
        "I want to know the weather.",
        "I want to ask you something.",
        "I want to know the news.",
        "I like this joke.",
        "I like this answer.",
        "I'm planning to ask about Python.",
        "Where am I?",
        "What's the news?",
        "Tell me a fun fact.",
        "Goodbye.",
        "Bye.",
    ]
    for s in must_not:
        assert vyra.should_store_memory(s) is False, f"False positive: {s}"
    print("Must NOT trigger tests passed.")


def test_should_trigger():
    vyra = make_vyra()
    should = [
        "Remember that I prefer morning briefings at 8 AM.",
        "I live in Jalandhar.",
        "My birthday is March 12.",
        "I don't like cricket news.",
        "From now on, call me Ashu.",
        "My name is Ashu.",
        "I study computer science.",
        "I am studying data science.",
        "My goal this semester is to finish DSA.",
        "My priority is DSA.",
        "I prefer morning briefings.",
        "I decided to focus on data science.",
    ]
    for s in should:
        assert vyra.should_store_memory(s) is True, f"False negative: {s}"
    print("Should trigger tests passed.")


def test_explicit_remember_unchanged():
    vyra = make_vyra()
    saved = []
    def fake_save(memory_type, content):
        saved.append((memory_type, content))
    with patch('core.vyra.save_memory', side_effect=fake_save):
        handled = vyra.handle_remember_command("/remember I live in Jalandhar")
        assert handled is True
        assert len(saved) == 1
        assert saved[0] == ("user_note", "I live in Jalandhar")
    print("Explicit /remember unchanged test passed.")


def test_confirmation_flow_yes():
    vyra = make_vyra()
    saved = []
    def fake_save(memory_type, content):
        saved.append((memory_type, content))
    with patch('core.vyra.save_memory', side_effect=fake_save):
        with patch('builtins.input', return_value='yes'):
            vyra.save_memory_with_confirmation("My name is Ashu.")
    assert len(saved) == 1
    print("Confirmation yes test passed.")


def test_confirmation_flow_no():
    vyra = make_vyra()
    saved = []
    def fake_save(memory_type, content):
        saved.append((memory_type, content))
    with patch('core.vyra.save_memory', side_effect=fake_save):
        with patch('builtins.input', return_value='no'):
            vyra.save_memory_with_confirmation("My name is Ashu.")
    assert len(saved) == 0
    print("Confirmation no test passed.")


if __name__ == "__main__":
    test_must_not_trigger()
    test_should_trigger()
    test_explicit_remember_unchanged()
    test_confirmation_flow_yes()
    test_confirmation_flow_no()
    print("All memory detection tests passed.")
