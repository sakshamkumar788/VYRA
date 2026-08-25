from dataclasses import dataclass

from location.models import ImportantPlace


@dataclass
class PlaceRelevance:
    """Relevance contribution from a personally important place."""

    bonus: int
    reason: str


class PlaceRelationshipRelevance:
    """Scores why a personally important place matters."""

    RELATIONSHIP_BONUSES = {
        "home": 100,
        "family": 95,
        "friend": 80,
        "college": 65,
        "work": 65,
        "frequent": 50,
        "other": 40,
    }

    def evaluate(
        self,
        place: ImportantPlace,
    ) -> PlaceRelevance:
        """Return relevance based on the place relationship."""

        base_bonus = self.RELATIONSHIP_BONUSES.get(
            place.place_type.lower(),
            self.RELATIONSHIP_BONUSES["other"],
        )

        importance_bonus = min(
            max(place.importance, 0),
            100,
        )

        bonus = min(
            120,
            base_bonus
            + (importance_bonus // 5),
        )

        return PlaceRelevance(
            bonus=bonus,
            reason=(
                f"personally important place: "
                f"{place.place_type}"
            ),
        )