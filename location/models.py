from dataclasses import dataclass
from datetime import datetime


@dataclass
class CurrentLocation:
    """Current coarse-grained location of the user."""

    latitude: float
    longitude: float

    accuracy_meters: float | None
    source: str | None

    city: str | None
    region: str | None
    country: str | None

    updated_at: datetime


@dataclass
class ImportantPlace:
    """A personally meaningful place."""

    name: str
    place_type: str

    city: str | None = None
    region: str | None = None
    country: str | None = None

    importance: int = 50

    notes: str | None = None