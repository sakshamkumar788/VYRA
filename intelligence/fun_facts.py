from dataclasses import dataclass


class FunFactCategory:
    """Supported fun-fact categories."""

    SCIENCE = "science"
    TECHNOLOGY = "technology"
    HISTORY = "history"
    SPACE = "space"
    NATURE = "nature"
    INDIA = "india"
    RANDOM = "random"


@dataclass
class FunFact:
    """A factual piece of information VYRA may share for fun."""

    text: str
    category: str
    source: str | None = None
    confidence: int = 80


class FunFactEngine:
    """Stores and selects fun facts."""

    def __init__(
        self,
        facts: list[FunFact] | None = None,
    ) -> None:
        self.facts: list[FunFact] = []

        for fact in facts or []:
            self.add_fact(fact)

    def add_fact(
        self,
        fact: FunFact,
    ) -> None:
        """Add a valid fact unless it is already present."""

        if not self._valid_category(
            fact.category
        ):
            return

        if self.contains(fact.text):
            return

        self.facts.append(fact)

    def contains(
        self,
        fact_text: str,
    ) -> bool:
        """Check whether a fact already exists."""

        normalized = (
            fact_text.strip().lower()
        )

        return any(
            fact.text.strip().lower()
            == normalized
            for fact in self.facts
        )

    def select(
        self,
        category: str | None = None,
    ) -> FunFact | None:
        """Return the highest-confidence matching fact."""

        candidates = self.facts

        if category is not None:
            candidates = [
                fact
                for fact in candidates
                if fact.category == category
            ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda fact: fact.confidence,
        )

    def _valid_category(
        self,
        category: str,
    ) -> bool:
        """Check whether a category is supported."""

        return category in {
            FunFactCategory.SCIENCE,
            FunFactCategory.TECHNOLOGY,
            FunFactCategory.HISTORY,
            FunFactCategory.SPACE,
            FunFactCategory.NATURE,
            FunFactCategory.INDIA,
            FunFactCategory.RANDOM,
        }