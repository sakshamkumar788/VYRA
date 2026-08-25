from intelligence.fun_facts import (
    FunFact,
    FunFactCategory,
    FunFactEngine,
)


def main() -> None:
    engine = FunFactEngine()

    science_fact = FunFact(
        text=(
            "DNA can be used as a medium for "
            "storing digital information."
        ),
        category=FunFactCategory.SCIENCE,
        source="test",
        confidence=95,
    )

    space_fact = FunFact(
        text=(
            "A day on Venus is longer than "
            "a year on Venus."
        ),
        category=FunFactCategory.SPACE,
        source="test",
        confidence=90,
    )

    weak_fact = FunFact(
        text="A weaker science fact.",
        category=FunFactCategory.SCIENCE,
        source="test",
        confidence=60,
    )

    engine.add_fact(science_fact)
    engine.add_fact(space_fact)
    engine.add_fact(weak_fact)

    # ---------------------------------------------------------
    # General selection
    # ---------------------------------------------------------

    best = engine.select()

    assert best is not None
    assert best.confidence == 95

    # ---------------------------------------------------------
    # Category selection
    # ---------------------------------------------------------

    science = engine.select(
        FunFactCategory.SCIENCE
    )

    assert science is not None
    assert science.text == science_fact.text

    space = engine.select(
        FunFactCategory.SPACE
    )

    assert space is not None
    assert space.text == space_fact.text

    # ---------------------------------------------------------
    # Unknown category
    # ---------------------------------------------------------

    unknown = engine.select(
        "music"
    )

    assert unknown is None

    # ---------------------------------------------------------
    # Duplicate protection
    # ---------------------------------------------------------

    engine.add_fact(
        FunFact(
            text=science_fact.text.upper(),
            category=FunFactCategory.SCIENCE,
            confidence=100,
        )
    )

    assert len(engine.facts) == 3

    # ---------------------------------------------------------
    # Invalid category
    # ---------------------------------------------------------

    engine.add_fact(
        FunFact(
            text="This should not be stored.",
            category="invalid",
            confidence=100,
        )
    )

    assert len(engine.facts) == 3

    print(
        "Best:",
        best.text,
    )

    print(
        "Science:",
        science.text,
    )

    print(
        "Space:",
        space.text,
    )

    print(
        "All fun-fact tests passed.",
    )


if __name__ == "__main__":
    main()