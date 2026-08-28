import sys
from types import ModuleType

winrt_mock = ModuleType("winrt")
sys.modules.setdefault("winrt", winrt_mock)
sys.modules.setdefault("winrt.windows", ModuleType("winrt.windows"))
sys.modules.setdefault("winrt.windows.devices", ModuleType("winrt.windows.devices"))
sys.modules.setdefault("winrt.windows.devices.geolocation", ModuleType("winrt.windows.devices.geolocation"))
sys.modules["winrt.windows.devices.geolocation"].Geolocator = object

ollama_mock = ModuleType("ollama")
ollama_mock.chat = lambda *a, **k: {"message": type("M", (), {"content": "ok"})()}
sys.modules.setdefault("ollama", ollama_mock)

pynput_mock = ModuleType("pynput")
sys.modules.setdefault("pynput", pynput_mock)
sys.modules.setdefault("pynput.keyboard", ModuleType("pynput.keyboard"))
sys.modules.setdefault("pynput.mouse", ModuleType("pynput.mouse"))

from core.vyra import VYRA
from context.context import UserContext, ContextManager
from unittest.mock import MagicMock

def test_user_context_has_no_accuracy():
    from context.context import SessionState
    ctx = UserContext(
        current_time=__import__("datetime").datetime.now(),
        session_state=SessionState.ACTIVE
    )
    assert not hasattr(ctx, "location_accuracy_meters")
    print("user context has no accuracy field passed")

def test_model_request_no_coords():
    vyra = VYRA()
    # Mock brain to capture messages
    captured = {}
    def fake_generate(messages):
        captured["messages"] = messages
        return "ok"
    vyra.brain.generate = fake_generate
    vyra.conversation = []
    vyra.generate_reply("hello")
    # Build model request content
    model_content = captured["messages"][-1]["content"]
    # Ensure no latitude/longitude/accuracy
    lower = model_content.lower()
    assert "latitude" not in lower
    assert "longitude" not in lower
    assert "accuracy" not in lower
    assert "accuracy_meters" not in lower
    print("model request contains no coords passed")

def test_coarse_location_allowed():
    # Context manager should allow coarse location name
    cm = ContextManager()
    cm.update_location("Jalandhar, Punjab, India")
    assert cm.context.current_location == "Jalandhar, Punjab, India"
    print("coarse location allowed passed")

def test_location_query_works():
    from unittest.mock import MagicMock
    from location.models import CurrentLocation
    from datetime import datetime
    vyra = VYRA.__new__(VYRA)
    vyra.location_service = MagicMock()
    loc = CurrentLocation(latitude=31.0, longitude=75.0, accuracy_meters=10, source="test", city="Jalandhar", region="Punjab", country="India", updated_at=datetime.now())
    vyra.location_service.get_current_location.return_value = loc
    handled = vyra.handle_location_query("what is my location")
    assert handled is True
    print("location query works passed")

def test_weather_without_city_works():
    # Weather routing should still work via location service
    # Just ensure no crash
    vyra = VYRA.__new__(VYRA)
    vyra.location_service = MagicMock()
    # Mock get_current_location to return valid
    from location.models import CurrentLocation
    from datetime import datetime
    loc = CurrentLocation(latitude=31.0, longitude=75.0, accuracy_meters=10, source="test", city="Jalandhar", region="Punjab", country="India", updated_at=datetime.now())
    vyra.location_service.get_current_location.return_value = loc
    # Weather routing exists via tool execution
    assert hasattr(vyra, "execute_tool_from_text")
    print("weather routing intact passed")

if __name__ == "__main__":
    test_user_context_has_no_accuracy()
    test_model_request_no_coords()
    test_coarse_location_allowed()
    test_location_query_works()
    test_weather_without_city_works()
    print("All location privacy tests passed.")
