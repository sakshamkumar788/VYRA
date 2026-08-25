"""
Tests for intelligence.humor.

Run with:
    python -m intelligence.test_humor
"""

import unittest

from intelligence.humor import (
    HumorCandidate,
    HumorEngine,
    HumorStyle,
)


class TestHumorGeneration(unittest.TestCase):
    def test_generate_returns_candidate(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(
            context="I've been debugging this function for an hour.",
            style=HumorStyle.TECH,
        )

        self.assertIsInstance(candidate, HumorCandidate)
        self.assertTrue(candidate.text)
        self.assertEqual(candidate.style, HumorStyle.TECH)
        self.assertGreater(candidate.confidence, 0)

    def test_generate_with_empty_context_still_returns_something(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(context="", style=HumorStyle.LIGHT)

        self.assertIsNotNone(candidate)
        self.assertIsInstance(candidate.text, str)
        self.assertTrue(candidate.text)


class TestContextSensitivity(unittest.TestCase):
    def test_different_contexts_can_produce_different_topics(self) -> None:
        engine = HumorEngine()

        debugging = engine.generate(
            context="stuck debugging a nasty error",
            style=HumorStyle.PLAYFUL,
        )

        studying = engine.generate(
            context="studying for tomorrow's exam",
            style=HumorStyle.PLAYFUL,
        )

        self.assertIsNotNone(debugging)
        self.assertIsNotNone(studying)
        self.assertNotEqual(debugging.text, studying.text)

    def test_late_night_context_is_detected(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(
            context="still awake at 3am working on this",
            style=HumorStyle.OBSERVATIONAL,
        )

        self.assertIsNotNone(candidate)
        self.assertTrue(candidate.text)


class TestStyleRespected(unittest.TestCase):
    def test_requested_style_is_used_when_valid(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(
            context="compiling my project",
            style=HumorStyle.SELF_AWARE,
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.style, HumorStyle.SELF_AWARE)

    def test_all_supported_styles_can_generate(self) -> None:
        engine = HumorEngine()

        for style in HumorStyle.ALL:
            candidate = engine.generate(
                context="just writing some python code",
                style=style,
            )

            self.assertIsNotNone(candidate)
            self.assertEqual(candidate.style, style)


class TestDuplicatePrevention(unittest.TestCase):
    def test_same_context_does_not_repeat_immediately(self) -> None:
        engine = HumorEngine()

        first = engine.generate(
            context="debugging again",
            style=HumorStyle.LIGHT,
        )
        second = engine.generate(
            context="debugging again",
            style=HumorStyle.LIGHT,
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertNotEqual(first.text, second.text)

    def test_pool_eventually_cycles_without_crashing(self) -> None:
        engine = HumorEngine()

        results = []

        for _ in range(10):
            candidate = engine.generate(
                context="debugging again",
                style=HumorStyle.LIGHT,
            )
            self.assertIsNotNone(candidate)
            results.append(candidate.text)

        # No two consecutive lines should be identical, even after
        # the pool wraps around and starts reusing lines.
        for first, second in zip(results, results[1:]):
            self.assertNotEqual(first, second)

    def test_reset_allows_lines_to_repeat_again(self) -> None:
        engine = HumorEngine()

        first = engine.generate(context="studying", style=HumorStyle.LIGHT)
        engine.reset()
        second = engine.generate(context="studying", style=HumorStyle.LIGHT)

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        # After reset, the cursor restarts from the same position, so
        # the same first line should be produced again.
        self.assertEqual(first.text, second.text)


class TestInvalidStyleHandling(unittest.TestCase):
    def test_unknown_style_falls_back_to_playful(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(
            context="just chilling",
            style="not_a_real_style",
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.style, HumorStyle.PLAYFUL)

    def test_none_style_falls_back_to_playful(self) -> None:
        engine = HumorEngine()

        candidate = engine.generate(
            context="just chilling",
            style=None,  # type: ignore[arg-type]
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.style, HumorStyle.PLAYFUL)


class TestEmptyPoolHandling(unittest.TestCase):
    def test_missing_topic_and_generic_pool_returns_none(self) -> None:
        # A deliberately empty template set: no styles, no lines.
        engine = HumorEngine(templates={HumorStyle.PLAYFUL: {}})

        candidate = engine.generate(
            context="anything at all",
            style=HumorStyle.PLAYFUL,
        )

        self.assertIsNone(candidate)


if __name__ == "__main__":
    unittest.main()
