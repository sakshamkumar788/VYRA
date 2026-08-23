from location.geocoder import ReverseGeocoder
from location.models import CurrentLocation
from location.windows import WindowsLocationProvider


class LocationService:
    """Combines Windows location and reverse geocoding."""

    def __init__(
        self,
        provider: WindowsLocationProvider | None = None,
        geocoder: ReverseGeocoder | None = None,
    ) -> None:
        self.provider = (
            provider
            or WindowsLocationProvider()
        )

        self.geocoder = (
            geocoder
            or ReverseGeocoder()
        )

    def get_current_location(
        self,
    ) -> CurrentLocation:
        """Obtain the current location and derive its area."""

        raw = self.provider.get_current_location()

        place = self.geocoder.reverse(
            raw.latitude,
            raw.longitude,
        )

        return CurrentLocation(
            latitude=raw.latitude,
            longitude=raw.longitude,
            accuracy_meters=raw.accuracy_meters,
            source=raw.source,
            city=place.get("city"),
            region=place.get("region"),
            country=place.get("country"),
            updated_at=raw.updated_at,
        )