import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ReverseGeocoder:
    """Convert coordinates into a coarse human-readable location."""

    API_URL = (
        "https://nominatim.openstreetmap.org/reverse"
    )

    def reverse(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, str | None]:
        """Reverse-geocode coordinates."""

        params = urlencode(
            {
                "lat": str(latitude),
                "lon": str(longitude),
                "format": "jsonv2",
                "addressdetails": "1",
            }
        )

        request = Request(
            f"{self.API_URL}?{params}",
            headers={
                "User-Agent": "VYRA/1.0"
            },
        )

        with urlopen(
            request,
            timeout=10,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        address = data.get(
            "address",
            {}
        )

        return {
            "city": (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            ),
            "region": address.get(
                "state"
            ),
            "country": address.get(
                "country"
            ),
            "postcode": address.get(
                "postcode"
            ),
        }