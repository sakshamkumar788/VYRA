from intelligence.feedback import FeedbackProfile, FeedbackType
from intelligence.user_preferences import UserPreferenceParser, UserPreferenceManager, UserPreferenceCommand
from memory.database import clear_intelligence_feedback


def main() -> None:
    parser = UserPreferenceParser()

    # 1. more AI news -> MORE_LIKE_THIS + category ai
    cmd = parser.parse("more AI news")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.MORE_LIKE_THIS
    assert cmd.category == "ai"
    assert cmd.entity is None
    assert cmd.source is None

    # 2. more about Nvidia -> MORE_LIKE_THIS + entity Nvidia
    cmd = parser.parse("more about Nvidia")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.MORE_LIKE_THIS
    assert cmd.entity == "nvidia"
    assert cmd.category is None

    # 3. less sports -> LESS_LIKE_THIS + category sports
    cmd = parser.parse("less sports")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.LESS_LIKE_THIS
    assert cmd.category == "sports"

    # 4. don't tell me sports -> DO_NOT_TELL_ME_THIS + category sports
    cmd = parser.parse("don't tell me sports")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.DO_NOT_TELL_ME_THIS
    assert cmd.category == "sports"

    # 5. tell me more about AI -> TELL_ME_MORE + category ai
    cmd = parser.parse("tell me more about AI")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.TELL_ME_MORE
    assert cmd.category == "ai"

    # 6. more from Reuters -> MORE_LIKE_THIS + source reuters
    cmd = parser.parse("more from Reuters")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.MORE_LIKE_THIS
    assert cmd.source == "reuters"

    # 7. less from Reuters -> LESS_LIKE_THIS + source reuters
    cmd = parser.parse("less from Reuters")
    assert cmd is not None
    assert cmd.feedback_type == FeedbackType.LESS_LIKE_THIS
    assert cmd.source == "reuters"

    # 8. ambiguous input returns None
    cmd = parser.parse("I don't like sports today")
    assert cmd is None

    # 9. applying command modifies FeedbackProfile correctly
    clear_intelligence_feedback()
    profile = FeedbackProfile()
    manager = UserPreferenceManager(profile)
    cmd = parser.parse("more AI news")
    assert cmd is not None
    manager.apply(cmd)
    assert profile.category_bonus("ai") == 10  # MORE_LIKE_THIS = 10

    # Normalization preserved
    cmd2 = parser.parse("  More   AI NEWS  ")
    assert cmd2 is not None
    assert cmd2.category == "ai"

    # 10. unsupported arbitrary text does not create preference
    cmd = parser.parse("random chat about the weather")
    assert cmd is None

    # Clean up
    clear_intelligence_feedback()

    print("All user preference tests passed.")


if __name__ == "__main__":
    main()
