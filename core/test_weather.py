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


def test_geocode_validation():
    # Mock _get_json to return controlled results without network
    from tools import weather as weather_mod
    original_get_json = weather_mod._get_json

    def fake_get_json(url, params):
        name = params.get("name", "").lower()
        # Valid exact match
        if name == "delhi":
            return {"results": [{"name": "Delhi", "latitude": 28.6, "longitude": 77.2}]}
        # Name contains request
        if name == "new york":
            return {"results": [{"name": "New York City", "latitude": 40.7, "longitude": -74.0}]}
        # Request contains name
        if name == "london uk":
            return {"results": [{"name": "London", "latitude": 51.5, "longitude": -0.1}]}
        # Poor match: request "Paris" returns "Pariss" (typo) -> should be rejected
        if name == "paris":
            return {"results": [{"name": "Pariss", "latitude": 48.8, "longitude": 2.3}]}
        # No results
        if name == "xyznonexistentcity":
            return {"results": []}
        # Unrelated city: request "Tokyo" returns "Toki" -> reject
        if name == "tokyo":
            return {"results": [{"name": "Toki", "latitude": 0, "longitude": 0}]}
        return {"results": []}

    weather_mod._get_json = fake_get_json
    try:
        # Valid exact match accepted
        res = weather_mod._geocode("Delhi")
        assert res is not None and res["name"] == "Delhi"

        # Request is substring of result name accepted
        res = weather_mod._geocode("New York")
        assert res is not None and res["name"] == "New York City"

        # Result name is substring of request accepted
        res = weather_mod._geocode("London UK")
        assert res is not None and res["name"] == "London"

        # Poor match rejected
        res = weather_mod._geocode("Paris")
        assert res is None, "Poor match should be rejected"

        # No results rejected
        res = weather_mod._geocode("xyzNonExistentCity")
        assert res is None

        # Unrelated city rejected
        res = weather_mod._geocode("Tokyo")
        assert res is None, "Unrelated city should be rejected"

        print("Geocode validation tests passed.")
    finally:
        weather_mod._get_json = original_get_json

if __name__ == "__main__":
    test_must_recognize()
    test_must_not_recognize()
    test_location_extraction()
    test_execute_with_location_service()
    test_geocode_validation()
    print("All weather tests passed.")
