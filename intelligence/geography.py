from intelligence.place_relevance import (
    PlaceRelationshipRelevance,
)

from dataclasses import dataclass

from intelligence.models import IntelligenceStory
from location.models import ImportantPlace


@dataclass
class GeographicRelevance:
    """Geographic contribution to story relevance."""

    bonus: int
    reasons: list[str]


class GeographicRelevanceEngine:
    """
    Evaluates how geographically relevant a story is.

    Order of importance:
        current location
        important personal places
        Punjab
        India
        rest of world

    Severe/urgent stories are allowed to override geography
    elsewhere in the main scoring system.
    """
    def __init__(self) -> None:
        self.place_relationship = (
            PlaceRelationshipRelevance()
        )


    CURRENT_LOCATION_BONUS = 80
    IMPORTANT_PLACE_BONUS = 70
    HOME_BONUS = 20
    REGION_BONUS = 20
    INDIA_BONUS = 10

    def evaluate(
        self,
        story: IntelligenceStory,
        current_location: str | None,
        important_places: list[ImportantPlace],
    ) -> GeographicRelevance:
        """Calculate geographic relevance."""

        if not story.location_name:
            return GeographicRelevance(
                bonus=0,
                reasons=[],
            )

        story_location = (
            story.location_name.strip().lower()
        )

        bonus = 0
        reasons: list[str] = []

        # ---------------------------------------------------------
        # Current location
        # ---------------------------------------------------------

        if current_location:
            current = current_location.strip().lower()

            if story_location == current:
                bonus += self.CURRENT_LOCATION_BONUS
                reasons.append(
                    "matches current location"
                )

        # ---------------------------------------------------------
        # Personally important places
        # ---------------------------------------------------------

        for place in important_places:
            if not place.city:
                continue

            place_city = (
                place.city.strip().lower()
            )

            if place_city != story_location:
                continue

            relationship = (
                self.place_relationship.evaluate(
                    place
                )
            )

            bonus += relationship.bonus

            reasons.append(
                relationship.reason
            )

        # ---------------------------------------------------------
        # Punjab
        # ---------------------------------------------------------

        if story_location == "punjab":
            bonus += self.REGION_BONUS
            reasons.append(
                "matches Punjab"
            )

        # ---------------------------------------------------------
        # India
        # ---------------------------------------------------------

        if story_location == "india":
            bonus += self.INDIA_BONUS
            reasons.append(
                "matches India"
            )

        return GeographicRelevance(
            bonus=bonus,
            reasons=reasons,
        )
    