import asyncio
from dataclasses import dataclass
from datetime import datetime

from winrt.windows.devices.geolocation import Geolocator


@dataclass
class CurrentLocation:
    """Current device location."""

    latitude: float
    longitude: float
    accuracy_meters: float | None
    source: str | None
    updated_at: datetime


class WindowsLocationProvider:
    """Obtains the current location from Windows."""

    async def _get_location_async(
        self,
    ) -> CurrentLocation:
        access = await (
            Geolocator.request_access_async()
        )

        if access.name != "ALLOWED":
            raise PermissionError(
                f"Windows location access is {access.name}."
            )

        locator = Geolocator()

        position = await (
            locator.get_geoposition_async()
        )

        coordinate = position.coordinate

        source = None

        if coordinate.position_source is not None:
            source = str(
                coordinate.position_source
            )

        return CurrentLocation(
            latitude=coordinate.latitude,
            longitude=coordinate.longitude,
            accuracy_meters=coordinate.accuracy,
            source=source,
            updated_at=datetime.now(),
        )

    def get_current_location(
        self,
    ) -> CurrentLocation:
        """Return the current Windows-derived location."""

        return asyncio.run(
            self._get_location_async()
        )