"""
Test D-06 stale location clearing
"""
import sys
from types import ModuleType

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
from location.models import CurrentLocation
from datetime import datetime

def make_vyra():
    vyra = VYRA.__new__(VYRA)
    vyra.location_service = MagicMock()
    vyra.context_manager = MagicMock()
    vyra.context_manager.update_location = MagicMock()
    return vyra

def test_update_location_context_clears_on_failure():
    vyra = make_vyra()
    vyra.location_service.get_current_location.side_effect = Exception("permission denied")
    vyra.update_location_context()
    # Should have been called with None values
    args, kwargs = vyra.context_manager.update_location.call_args
    assert kwargs.get("location_name") is None
    assert kwargs.get("accuracy_meters") is None
    print("Stale location cleared on failure test passed.")

def test_update_location_context_sets_on_success():
    vyra = make_vyra()
    fake_loc = CurrentLocation(
        latitude=31.0, longitude=75.0, accuracy_meters=50.0,
        source="test", city="Delhi", region="Delhi", country="India",
        updated_at=datetime.now()
    )
    vyra.location_service.get_current_location.return_value = fake_loc
    vyra.update_location_context()
    args, kwargs = vyra.context_manager.update_location.call_args
    assert kwargs.get("location_name") == "Delhi, Delhi, India"
    assert kwargs.get("accuracy_meters") == 50.0
    print("Location set on success test passed.")

if __name__ == "__main__":
    test_update_location_context_clears_on_failure()
    test_update_location_context_sets_on_success()
    print("All stale location tests passed.")
