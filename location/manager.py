from memory.database import get_important_places
from location.models import ImportantPlace

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

    def load_important_places_from_database(self) -> None:
        """Load persistent important places into memory."""

        rows = get_important_places()

        self.important_places = []

        for row in rows:
            (
                place_id,
                name,
                place_type,
                city,
                region,
                country,
                importance,
                notes,
                created_at,
            ) = row

            self.important_places.append(
                ImportantPlace(
                    name=name,
                    place_type=place_type,
                    city=city,
                    region=region,
                    country=country,
                    importance=importance,
                    notes=notes,
                )
            )

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