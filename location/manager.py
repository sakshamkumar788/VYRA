from location.models import (
    CurrentLocation,
    ImportantPlace,
)


class LocationManager:
    """
    Maintains current location and personally important places.

    Current location and important places are intentionally
    separate concepts.
    """

    def __init__(self) -> None:
        self.current_location: CurrentLocation | None = None

        self.important_places: list[
            ImportantPlace
        ] = []

    def update_current_location(
        self,
        location: CurrentLocation,
    ) -> None:
        """Update the user's current device-derived location."""

        self.current_location = location

    def add_important_place(
        self,
        place: ImportantPlace,
    ) -> None:
        """Add a personally meaningful place."""

        self.important_places.append(place)

    def get_important_places(
        self,
    ) -> list[ImportantPlace]:
        """Return important places sorted by importance."""

        return sorted(
            self.important_places,
            key=lambda place: place.importance,
            reverse=True,
        )

    def get_current_area(self) -> str | None:
        """Return a human-readable current area."""

        if self.current_location is None:
            return None

        location = self.current_location

        parts = [
            location.city,
            location.region,
            location.country,
        ]

        return ", ".join(
            part
            for part in parts
            if part
        )