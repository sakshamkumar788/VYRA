from dataclasses import dataclass

from location.models import ImportantPlace


@dataclass
class LocationRelevance:
    """How relevant a location is to the user."""

    score: int
    reason: str


class LocationRelevanceEngine:
    """Determines why a location may matter to the user."""

    def evaluate(
        self,
        location_name: str,
        current_location: str | None,
        important_places: list[ImportantPlace],
    ) -> LocationRelevance:
        """Evaluate location significance."""

        score = 0
        reasons: list[str] = []

        if (
            current_location
            and location_name.lower()
            == current_location.lower()
        ):
            score += 80
            reasons.append(
                "user is currently there"
            )

        for place in important_places:
            if (
                place.city
                and place.city.lower()
                == location_name.lower()
            ):
                score += place.importance
                reasons.append(
                    f"personally important: {place.place_type}"
                )

        if score == 0:
            return LocationRelevance(
                score=0,
                reason="no known personal relevance",
            )

        return LocationRelevance(
            score=score,
            reason="; ".join(reasons),
        )