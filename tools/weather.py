import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _get_json(url: str, params: dict[str, str]) -> dict:
    """Make a GET request and return decoded JSON."""

    full_url = f"{url}?{urlencode(params)}"

    request = Request(
        full_url,
        headers={
            "User-Agent": "VYRA/0.1",
        },
    )

    with urlopen(request, timeout=10) as response:
        return json.load(response)


def _geocode(location: str) -> dict | None:
    """Convert a city/place name into coordinates."""

    data = _get_json(
        GEOCODING_URL,
        {
            "name": location,
            "count": "1",
            "language": "en",
            "format": "json",
        },
    )

    results = data.get("results", [])

    if not results:
        return None

    return results[0]


def get_weather(
    location: str,
    period: str = "current",
) -> str:
    """
    Fetch current or near-term weather.

    period can be:
        current
        tomorrow
    """

    try:
        place = _geocode(location)

        if place is None:
            return f"I couldn't find the location '{location}'."

        latitude = place["latitude"]
        longitude = place["longitude"]
        place_name = place["name"]
        country = place.get("country", "")

        forecast = _get_json(
            FORECAST_URL,
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "relative_humidity_2m,"
                    "wind_speed_10m,"
                    "weather_code"
                ),
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "forecast_days": "2",
                "timezone": "auto",
            },
        )

        current = forecast["current"]
        daily = forecast["daily"]

        if period == "tomorrow":
            tomorrow_code = int(daily["weather_code"][1])

            tomorrow_condition = WEATHER_CODES.get(
                tomorrow_code,
                "Unknown conditions",
            )

            return (
                f"Weather forecast for tomorrow in "
                f"{place_name}, {country}\n"
                f"Temperature: "
                f"{daily['temperature_2m_min'][1]}°C to "
                f"{daily['temperature_2m_max'][1]}°C\n"
                f"Conditions: {tomorrow_condition}\n"
                f"Precipitation probability: "
                f"{daily['precipitation_probability_max'][1]}%."
            )

        current_code = int(
            current["weather_code"]
        )

        current_condition = WEATHER_CODES.get(
            current_code,
            "Unknown conditions",
        )

        return (
            f"Current weather for "
            f"{place_name}, {country}\n"
            f"Temperature: {current['temperature_2m']}°C "
            f"(feels like "
            f"{current['apparent_temperature']}°C)\n"
            f"Conditions: {current_condition}\n"
            f"Humidity: {current['relative_humidity_2m']}%\n"
            f"Wind: {current['wind_speed_10m']} km/h."
        )

    except Exception as error:
        return (
            f"I couldn't fetch the weather right now: "
            f"{error}"
        )