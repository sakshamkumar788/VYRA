import sys
from unittest.mock import MagicMock

from tools.registry import ToolRegistry, Tool
from tools.router import ToolRouter
from location.models import CurrentLocation
from datetime import datetime

def make_router():
    registry = ToolRegistry()
    router = ToolRouter(registry)
    return router

def test_must_recognize():
    router = make_router()
    must = [
        "weather",
        "weather?",
        "what's the weather",
        "what is the weather",
        "weather in Delhi",
        "weather in Jalandhar",
        "temperature in Mumbai",
        "forecast for Punjab",
    ]
    for inp in must:
        req = router.detect(inp)
        assert req is not None, f"Failed to recognize: {inp}"
        assert req.tool_name == "weather", f"Wrong tool for {inp}"
    print("Must recognize tests passed.")

def test_must_not_recognize():
    router = make_router()
    must_not = [
        "what's in the news",
        "I'm interested in AI",
        "what is in India",
        "I am in Delhi",
        "what happened in India",
        "tell me what's happening",
    ]
    for inp in must_not:
        req = router.detect(inp)
        assert req is None, f"False positive for: {inp}"
    print("Must NOT recognize tests passed.")

def test_location_extraction():
    router = make_router()
    cases = [
        ("weather in Delhi", "Delhi"),
        ("temperature in Mumbai", "Mumbai"),
        ("forecast for Punjab", "Punjab"),
        ("weather at Kolkata", "Kolkata"),
    ]
    for inp, expected in cases:
        req = router.detect(inp)
        assert req is not None
        assert req.arguments["location"] == expected, f"{inp} got {req.arguments['location']}"
    # No city
    req = router.detect("weather")
    assert req is not None
    assert req.arguments.get("location") is None, "Location should be None when not specified"
    print("Location extraction tests passed.")

# Minimal fake VYRA to test execute logic without importing full VYRA
class FakeVYRA:
    def __init__(self, router, location_service):
        self.tool_router = router
        self.location_service = location_service

    def execute_tool_from_text(self, user_input):
        request = self.tool_router.detect(user_input)
        if request is None:
            return None
        if request.tool_name == "weather":
            location = request.arguments.get("location")
            if not location:
                try:
                    current_location = self.location_service.get_current_location()
                    city = getattr(current_location, "city", None)
                    if city:
                        request.arguments["location"] = city
                    else:
                        return (
                            "I couldn't determine your current location. "
                            "Please tell me which city you want the weather for."
                        )
                except Exception:
                    return (
                        "I couldn't determine your current location right now. "
                        "Please tell me which city you want the weather for."
                    )
        return self.tool_router.execute(request)

def test_execute_with_location_service():
    registry = ToolRegistry()
    router = ToolRouter(registry)
    def fake_execute(request):
        loc = request.arguments.get("location")
        period = request.arguments.get("period")
        return f"FAKE_WEATHER:{loc}:{period}"
    router.execute = fake_execute

    location_service = MagicMock()
    fake_loc = CurrentLocation(
        latitude=31.33, longitude=75.58, accuracy_meters=10.0,
        source="test", city="Jalandhar", region="Punjab", country="India",
        updated_at=datetime.now()
    )
    location_service.get_current_location = MagicMock(return_value=fake_loc)

    vyra = FakeVYRA(router, location_service)

    result = vyra.execute_tool_from_text("weather")
    assert result == "FAKE_WEATHER:Jalandhar:current", f"Unexpected result {result}"

    result = vyra.execute_tool_from_text("weather in Delhi")
    assert result == "FAKE_WEATHER:Delhi:current", f"Unexpected result {result}"

    location_service.get_current_location = MagicMock(return_value=CurrentLocation(
        latitude=0, longitude=0, accuracy_meters=None, source=None,
        city=None, region=None, country=None, updated_at=datetime.now()
    ))
    result = vyra.execute_tool_from_text("weather")
    assert "couldn't determine your current location" in result.lower()

    location_service.get_current_location = MagicMock(side_effect=Exception("no permission"))
    result = vyra.execute_tool_from_text("weather")
    assert "couldn't determine your current location" in result.lower()

    print("Execute with location service tests passed.")

if __name__ == "__main__":
    test_must_recognize()
    test_must_not_recognize()
    test_location_extraction()
    test_execute_with_location_service()
    print("All weather tests passed.")
