"""
Tests for explicit location intent routing – D-01 fix
"""

import sys
from types import ModuleType

# Mock winrt before importing vyra to avoid Windows-specific import errors in tests
winrt_mock = ModuleType("winrt")
winrt_windows_mock = ModuleType("winrt.windows")
winrt_windows_devices_mock = ModuleType("winrt.windows.devices")
winrt_windows_devices_geolocation_mock = ModuleType("winrt.windows.devices.geolocation")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", winrt_windows_mock)
sys.modules.setdefault("winrt.windows.devices", winrt_windows_devices_mock)
sys.modules.setdefault("winrt.windows.devices.geolocation", winrt_windows_devices_geolocation_mock)
winrt_windows_devices_geolocation_mock.Geolocator = object

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

from unittest.mock import MagicMock

from core.vyra import VYRA
from location.models import CurrentLocation


def _make_vyra_with_fake_location(city="Jalandhar", region="Punjab", country="India", fail=False):
    # Create VYRA instance without running init side effects where possible
    # We'll monkeypatch location_service after creation
    vyra = VYRA.__new__(VYRA)
    vyra.location_service = MagicMock()
    if fail:
        vyra.location_service.get_current_location.side_effect = Exception("permission denied")
    else:
        fake_loc = CurrentLocation(
            latitude=31.0,
            longitude=75.0,
            accuracy_meters=50.0,
            source="test",
            city=city,
            region=region,
            country=country,
            updated_at=None,
        )
        vyra.location_service.get_current_location.return_value = fake_loc
    return vyra


def test_where_am_i_triggers_location():
    vyra = _make_vyra_with_fake_location()
    handled = vyra.handle_location_query("where am I")
    assert handled is True
    vyra.location_service.get_current_location.assert_called_once()


def test_what_is_my_location_triggers():
    vyra = _make_vyra_with_fake_location()
    handled = vyra.handle_location_query("What is my location")
    assert handled is True


def test_where_am_i_right_now_triggers():
    vyra = _make_vyra_with_fake_location()
    handled = vyra.handle_location_query("where am i right now")
    assert handled is True


def test_what_city_am_i_in_triggers():
    vyra = _make_vyra_with_fake_location()
    handled = vyra.handle_location_query("what city am i in")
    assert handled is True


def test_non_location_does_not_trigger():
    vyra = _make_vyra_with_fake_location()
    handled = vyra.handle_location_query("how are you?")
    assert handled is False
    vyra.location_service.get_current_location.assert_not_called()


def test_location_unavailable_returns_failure():
    vyra = _make_vyra_with_fake_location(fail=True)
    handled = vyra.handle_location_query("where am i")
    assert handled is True
    # No exception propagated
    assert vyra.location_service.get_current_location.called


def test_raw_coordinates_not_exposed():
    # Ensure handle_location_query prints city/region/country only
    vyra = _make_vyra_with_fake_location(city="Delhi", region="Delhi", country="India")
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        vyra.handle_location_query("what's my location")
    output = buf.getvalue()
    assert "Delhi" in output
    assert "31.0" not in output
    assert "75.0" not in output


def test_empty_parts_fallback():
    vyra = _make_vyra_with_fake_location(city="", region="", country="")
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        vyra.handle_location_query("where am i")
    output = buf.getvalue()
    assert "can't determine" in output.lower()


if __name__ == "__main__":
    test_where_am_i_triggers_location()
    test_what_is_my_location_triggers()
    test_where_am_i_right_now_triggers()
    test_what_city_am_i_in_triggers()
    test_non_location_does_not_trigger()
    test_location_unavailable_returns_failure()
    test_raw_coordinates_not_exposed()
    test_empty_parts_fallback()
    print("All location intent tests passed.")
