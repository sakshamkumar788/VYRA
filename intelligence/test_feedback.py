"""
Tests for intelligence.feedback.

Run with:
    python -m intelligence.test_feedback
"""

import unittest
from datetime import datetime, timedelta

from intelligence.feedback import (
    FeedbackProfile,
    FeedbackRecord,
    FeedbackType,
    PREFERENCE_HALF_LIFE_DAYS,
)

from memory.database import (
    clear_intelligence_feedback,
)


class TestDefaultBonuses(unittest.TestCase):
    def test_default_bonuses_are_zero(self) -> None:
        profile = FeedbackProfile()

        self.assertEqual(profile.category_bonus("ai"), 0)
        self.assertEqual(profile.entity_bonus("python"), 0)
        self.assertEqual(profile.source_bonus("reuters"), 0)


class TestPositiveFeedback(unittest.TestCase):
    def test_like_increases_preference(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.LIKE,
            story_category="ai",
        )

        self.assertEqual(profile.category_bonus("ai"), 5)

    def test_more_like_this_increases_more_than_like(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.LIKE,
            story_category="ai",
        )
        like_bonus = profile.category_bonus("ai")

        profile.record(
            FeedbackType.MORE_LIKE_THIS,
            story_category="research",
        )
        more_like_this_bonus = profile.category_bonus("research")

        self.assertGreater(
            more_like_this_bonus,
            like_bonus,
        )


class TestNegativeFeedback(unittest.TestCase):
    def test_dislike_decreases_preference(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.DISLIKE,
            story_category="business",
        )

        self.assertEqual(
            profile.category_bonus("business"),
            -5,
        )

    def test_do_not_tell_me_this_strongly_decreases(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.DISLIKE,
            story_category="business",
        )
        mild = profile.category_bonus("business")

        profile.record(
            FeedbackType.DO_NOT_TELL_ME_THIS,
            story_category="politics",
        )
        strong = profile.category_bonus("politics")

        self.assertLess(strong, mild)


class TestBoundedAccumulation(unittest.TestCase):
    def test_repeated_positive_feedback_stays_bounded(self) -> None:
        profile = FeedbackProfile()

        for _ in range(50):
            profile.record(
                FeedbackType.MORE_LIKE_THIS,
                story_category="ai",
            )

        self.assertLessEqual(
            profile.category_bonus("ai"),
            50,
        )

    def test_repeated_negative_feedback_stays_bounded(self) -> None:
        profile = FeedbackProfile()

        for _ in range(50):
            profile.record(
                FeedbackType.DO_NOT_TELL_ME_THIS,
                story_category="crime",
            )

        self.assertGreaterEqual(
            profile.category_bonus("crime"),
            -50,
        )

    def test_decayed_accumulation_also_stays_bounded(self) -> None:
        """Many old + new records together must still respect -50..50."""

        profile = FeedbackProfile()
        now = datetime(2026, 6, 1, 12, 0, 0)

        for day_offset in range(0, 400, 5):
            profile.history.append(
                FeedbackRecord(
                    feedback_type=FeedbackType.DO_NOT_TELL_ME_THIS,
                    story_category="crime",
                    entity_names=(),
                    source=None,
                    created_at=now - timedelta(days=day_offset),
                )
            )

        profile.rebuild_preferences(now=now)

        bonus = profile.category_bonus("crime")

        self.assertGreaterEqual(bonus, -50)
        self.assertLessEqual(bonus, 50)


class TestEntityNormalization(unittest.TestCase):
    def test_entity_matching_is_case_insensitive(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.LIKE,
            entity_names=["AI"],
        )

        self.assertEqual(profile.entity_bonus("ai"), 5)
        self.assertEqual(profile.entity_bonus("Ai"), 5)
        self.assertEqual(profile.entity_bonus("  AI  "), 5)

    def test_mixed_case_feedback_does_not_create_duplicates(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.LIKE,
            entity_names=["AI"],
        )
        profile.record(
            FeedbackType.LIKE,
            entity_names=["ai"],
        )

        # Both events should have accumulated onto the same key.
        self.assertEqual(profile.entity_bonus("Ai"), 10)

    def test_entity_normalization_holds_through_rebuild(self) -> None:
        profile = FeedbackProfile()
        now = datetime(2026, 6, 1, 12, 0, 0)

        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.LIKE,
                story_category=None,
                entity_names=("ai",),
                source=None,
                created_at=now,
            )
        )

        profile.rebuild_preferences(now=now)

        self.assertEqual(profile.entity_bonus("AI"), 5)
        self.assertEqual(profile.entity_bonus(" Ai "), 5)


class TestIndependentPreferences(unittest.TestCase):
    def test_different_categories_are_independent(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.LIKE,
            story_category="ai",
        )
        profile.record(
            FeedbackType.DISLIKE,
            story_category="sports",
        )

        self.assertEqual(profile.category_bonus("ai"), 5)
        self.assertEqual(profile.category_bonus("sports"), -5)

    def test_different_categories_remain_independent_after_decay(self) -> None:
        profile = FeedbackProfile()
        now = datetime(2026, 6, 1, 12, 0, 0)

        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.MORE_LIKE_THIS,
                story_category="ai",
                entity_names=(),
                source=None,
                created_at=now - timedelta(days=30),
            )
        )
        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.LESS_LIKE_THIS,
                story_category="sports",
                entity_names=(),
                source=None,
                created_at=now,
            )
        )

        profile.rebuild_preferences(now=now)

        self.assertGreater(profile.category_bonus("ai"), 0)
        self.assertLess(profile.category_bonus("sports"), 0)

    def test_different_entities_are_independent(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.MORE_LIKE_THIS,
            entity_names=["python"],
        )
        profile.record(
            FeedbackType.LESS_LIKE_THIS,
            entity_names=["javascript"],
        )

        self.assertEqual(profile.entity_bonus("python"), 10)
        self.assertEqual(profile.entity_bonus("javascript"), -10)

    def test_sources_are_independent_of_categories_and_entities(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.TELL_ME_MORE,
            story_category="ai",
            entity_names=["gemma"],
            source="reuters",
        )

        self.assertEqual(profile.category_bonus("ai"), 8)
        self.assertEqual(profile.entity_bonus("gemma"), 8)
        self.assertEqual(profile.source_bonus("reuters"), 8)

        # A second, unrelated source must not be affected.
        self.assertEqual(profile.source_bonus("bbc"), 0)


class TestInvalidFeedbackHandling(unittest.TestCase):
    def test_unknown_feedback_type_fails_safely(self) -> None:
        profile = FeedbackProfile()

        # Should not raise.
        profile.record(
            "not_a_real_feedback_type",
            story_category="ai",
        )

        self.assertEqual(profile.category_bonus("ai"), 0)
        self.assertEqual(len(profile.history), 0)

    def test_none_feedback_type_fails_safely(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            None,  # type: ignore[arg-type]
            story_category="ai",
        )

        self.assertEqual(profile.category_bonus("ai"), 0)
        self.assertEqual(len(profile.history), 0)


class TestFeedbackRecordCreation(unittest.TestCase):
    def test_feedback_record_can_be_created_directly(self) -> None:
        record = FeedbackRecord(
            feedback_type=FeedbackType.LIKE,
            story_category="ai",
            entity_names=("ai", "gemma"),
            source="reuters",
            created_at=datetime(2026, 1, 1, 9, 0, 0),
        )

        self.assertEqual(record.feedback_type, FeedbackType.LIKE)
        self.assertEqual(record.story_category, "ai")
        self.assertEqual(record.entity_names, ("ai", "gemma"))
        self.assertEqual(record.source, "reuters")
        self.assertEqual(
            record.created_at,
            datetime(2026, 1, 1, 9, 0, 0),
        )

    def test_recording_valid_feedback_appends_to_history(self) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.DISMISS,
            story_category="sports",
            entity_names=["Cricket"],
            source="espn",
        )

        self.assertEqual(len(profile.history), 1)

        record = profile.history[0]
        self.assertEqual(record.feedback_type, FeedbackType.DISMISS)
        self.assertEqual(record.story_category, "sports")
        self.assertEqual(record.entity_names, ("cricket",))
        self.assertEqual(record.source, "espn")


class TestPersistentFeedbackLoading(unittest.TestCase):
    def setUp(self) -> None:
        """Start each persistence test with a clean database."""
        clear_intelligence_feedback()

    def tearDown(self) -> None:
        """Remove test feedback from the real database."""
        clear_intelligence_feedback()

    def test_persistent_feedback_can_be_loaded_explicitly(
        self,
    ) -> None:
        profile = FeedbackProfile()

        profile.record(
            FeedbackType.MORE_LIKE_THIS,
            story_category="ai",
            entity_names=["AI"],
            source="testsource",
        )

        loaded = FeedbackProfile()

        loaded.load_persistent_feedback()

        self.assertEqual(
            loaded.category_bonus("ai"),
            10,
        )

        self.assertEqual(
            loaded.entity_bonus("ai"),
            10,
        )

        self.assertEqual(
            loaded.source_bonus("testsource"),
            10,
        )

        self.assertEqual(
            len(loaded.history),
            1,
        )


class TestDecayWeighting(unittest.TestCase):
    """Deterministic decay tests using explicitly constructed records.

    A fixed `now` is always passed to rebuild_preferences()/the
    private decay helper so results never depend on the real clock.
    """

    def setUp(self) -> None:
        self.now = datetime(2026, 6, 1, 12, 0, 0)

    def _record(
        self,
        age_days: int,
        feedback_type: str = FeedbackType.MORE_LIKE_THIS,
        story_category: str | None = "ai",
    ) -> FeedbackRecord:
        return FeedbackRecord(
            feedback_type=feedback_type,
            story_category=story_category,
            entity_names=(),
            source=None,
            created_at=self.now - timedelta(days=age_days),
        )

    def test_brand_new_record_has_full_strength(self) -> None:
        profile = FeedbackProfile()
        profile.history.append(self._record(age_days=0))

        profile.rebuild_preferences(now=self.now)

        # MORE_LIKE_THIS full strength = 10.
        self.assertEqual(profile.category_bonus("ai"), 10)

    def test_thirty_day_old_record_is_about_half_strength(self) -> None:
        profile = FeedbackProfile()
        profile.history.append(
            self._record(age_days=PREFERENCE_HALF_LIFE_DAYS)
        )

        profile.rebuild_preferences(now=self.now)

        # 10 * 0.5 = 5 exactly.
        self.assertEqual(profile.category_bonus("ai"), 5)

    def test_sixty_day_old_record_is_about_quarter_strength(self) -> None:
        profile = FeedbackProfile()
        profile.history.append(
            self._record(age_days=PREFERENCE_HALF_LIFE_DAYS * 2)
        )

        profile.rebuild_preferences(now=self.now)

        # 10 * 0.25 = 2.5, rounds to 2.
        self.assertAlmostEqual(
            profile.category_bonus("ai"),
            2,
            delta=1,
        )

    def test_ninety_day_old_record_is_about_eighth_strength(self) -> None:
        profile = FeedbackProfile()
        profile.history.append(
            self._record(age_days=PREFERENCE_HALF_LIFE_DAYS * 3)
        )

        profile.rebuild_preferences(now=self.now)

        # 10 * 0.125 = 1.25, rounds to 1.
        self.assertAlmostEqual(
            profile.category_bonus("ai"),
            1,
            delta=1,
        )

    def test_recent_feedback_can_outweigh_older_opposite_feedback(
        self,
    ) -> None:
        profile = FeedbackProfile()

        # Strong old dislike, mostly decayed away by now.
        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.DO_NOT_TELL_ME_THIS,
                story_category="ai",
                entity_names=(),
                source=None,
                created_at=self.now
                - timedelta(days=PREFERENCE_HALF_LIFE_DAYS * 3),
            )
        )

        # Fresh, strong like.
        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.MORE_LIKE_THIS,
                story_category="ai",
                entity_names=(),
                source=None,
                created_at=self.now,
            )
        )

        profile.rebuild_preferences(now=self.now)

        # Old: -20 * 0.125 = -2.5 -> rounds to -2 or -3.
        # New: +10 * 1.0 = 10.
        # Net should clearly be positive.
        self.assertGreater(profile.category_bonus("ai"), 0)

    def test_future_timestamp_is_treated_as_full_strength(self) -> None:
        profile = FeedbackProfile()

        profile.history.append(
            FeedbackRecord(
                feedback_type=FeedbackType.LIKE,
                story_category="ai",
                entity_names=(),
                source=None,
                created_at=self.now + timedelta(days=10),
            )
        )

        profile.rebuild_preferences(now=self.now)

        # Must not exceed full strength just because the timestamp
        # is (incorrectly) in the future.
        self.assertEqual(profile.category_bonus("ai"), 5)

    def test_decay_factor_never_exceeds_one(self) -> None:
        profile = FeedbackProfile()

        factor = profile._decay_factor(
            created_at=self.now + timedelta(days=100),
            now=self.now,
        )

        self.assertLessEqual(factor, 1.0)
        self.assertGreater(factor, 0.0)

    def test_rebuild_is_idempotent_for_same_now(self) -> None:
        profile = FeedbackProfile()
        profile.history.append(self._record(age_days=30))

        profile.rebuild_preferences(now=self.now)
        first = profile.category_bonus("ai")

        profile.rebuild_preferences(now=self.now)
        second = profile.category_bonus("ai")

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
