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
from interaction.policy import InteractionDecision
from context.context import SessionState
from interaction.engine import InteractionEngine


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


class TestIntelligenceHumorIntegration(unittest.TestCase):
    def _make_intelligence_engine(self):
        from intelligence.engine import IntelligenceEngine
        from intelligence.ingestion import IntelligenceIngestionEngine

        class DummyIngestion(IntelligenceIngestionEngine):
            def fetch_all(self):
                return []

        return IntelligenceEngine(ingestion=DummyIngestion())

    def test_get_humor_candidate_returns_candidate(self):
        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging code")
        self.assertIsNotNone(cand)
        self.assertIsInstance(cand.text, str)

    def test_get_humor_candidate_uses_humor_engine(self):
        intel = self._make_intelligence_engine()
        # Ensure get_humor_candidate delegates to the same engine instance
        cand = intel.get_humor_candidate(context="studying", style=HumorStyle.LIGHT)
        self.assertIsNotNone(cand)
        self.assertEqual(cand.style, HumorStyle.LIGHT)

    def test_requested_style_is_preserved(self):
        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="compiling", style=HumorStyle.TECH)
        self.assertEqual(cand.style, HumorStyle.TECH)

    def test_invalid_style_falls_back_via_humor_engine(self):
        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="anything", style="bogus")
        self.assertIsNotNone(cand)
        self.assertEqual(cand.style, HumorStyle.PLAYFUL)

    def test_evaluate_humor_interaction_creates_low_priority(self):
        from intelligence.engine import IntelligenceEngine
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext, InteractionDecision
        from context.context import SessionState
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="late night coding")
        engine_inter = InteractionEngine()
        ctx = InteractionContext(
            current_time=datetime.now(),
            session_state=SessionState.IDLE,
            proactive_enabled=True,
            user_active=True,
            user_busy=False,
            recent_interaction=False,
            idle_seconds=100,
        )
        decision = intel.evaluate_humor_interaction(cand, engine_inter, ctx)
        self.assertEqual(decision, InteractionDecision.SPEAK)

    def test_proactive_disabled_returns_wait(self):
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext
        from context.context import SessionState
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        ctx = InteractionContext(
            current_time=datetime.now(),
            session_state=SessionState.IDLE,
            proactive_enabled=False,
        )
        decision = intel.evaluate_humor_interaction(cand, engine_inter, ctx)
        self.assertEqual(decision, InteractionDecision.WAIT)

    def test_quiet_mode_returns_wait(self):
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext
        from context.context import SessionState
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        engine_inter.set_quiet_mode(True)
        ctx = InteractionContext(
            current_time=datetime.now(),
            session_state=SessionState.IDLE,
            proactive_enabled=True,
        )
        decision = intel.evaluate_humor_interaction(cand, engine_inter, ctx)
        self.assertEqual(decision, InteractionDecision.WAIT)

    def test_evaluate_does_not_increment_daily_count(self):
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext
        from context.context import SessionState
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        before = engine_inter._daily_proactive_count
        ctx = InteractionContext(
            current_time=datetime.now(),
            session_state=SessionState.IDLE,
            proactive_enabled=True,
        )
        intel.evaluate_humor_interaction(cand, engine_inter, ctx)
        self.assertEqual(engine_inter._daily_proactive_count, before)

    def test_evaluate_does_not_update_last_interaction(self):
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext
        from context.context import SessionState
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        before = engine_inter.last_proactive_interaction
        ctx = InteractionContext(
            current_time=datetime.now(),
            session_state=SessionState.IDLE,
            proactive_enabled=True,
        )
        intel.evaluate_humor_interaction(cand, engine_inter, ctx)
        self.assertEqual(engine_inter.last_proactive_interaction, before)

    def test_deliver_humor_increments_daily_count(self):
        from interaction.engine import InteractionEngine
        from datetime import datetime, timedelta

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        before = engine_inter._daily_proactive_count
        now = datetime.now()
        intel.deliver_humor(cand, engine_inter, now)
        self.assertEqual(engine_inter._daily_proactive_count, before + 1)

    def test_deliver_humor_updates_last_interaction(self):
        from interaction.engine import InteractionEngine
        from datetime import datetime

        intel = self._make_intelligence_engine()
        cand = intel.get_humor_candidate(context="debugging")
        engine_inter = InteractionEngine()
        now = datetime.now()
        intel.deliver_humor(cand, engine_inter, now)
        self.assertEqual(engine_inter.last_proactive_interaction, now)

    def test_no_duplicate_policy_implemented(self):
        # IntelligenceEngine should not contain its own quiet/cooldown logic.
        from intelligence.engine import IntelligenceEngine
        import inspect
        src = inspect.getsource(IntelligenceEngine.evaluate_humor_interaction)
        self.assertNotIn("quiet_mode", src)
        self.assertNotIn("cooldown", src.lower())


class TestHumorPolicyGuardrails(unittest.TestCase):
    def _make_engine_and_context(self, now, session_state=SessionState.IDLE, proactive=True, user_busy=False):
        from intelligence.engine import IntelligenceEngine
        from intelligence.ingestion import IntelligenceIngestionEngine
        from interaction.policy import InteractionContext

        class DummyIngestion(IntelligenceIngestionEngine):
            def fetch_all(self):
                return []

        intel = IntelligenceEngine(ingestion=DummyIngestion())
        ctx = InteractionContext(
            current_time=now,
            session_state=session_state,
            proactive_enabled=proactive,
            user_busy=user_busy,
        )
        return intel, ctx

    def test_default_cooldown_is_120_minutes(self):
        from intelligence.humor import HumorPolicy
        self.assertEqual(HumorPolicy.HUMOR_COOLDOWN_MINUTES, 120)

    def test_default_daily_limit_is_3(self):
        from intelligence.humor import HumorPolicy
        self.assertEqual(HumorPolicy.MAX_HUMOR_INTERACTIONS_PER_DAY, 3)

    def test_fresh_policy_allows_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        ctx = InteractionContext(current_time=now, session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        self.assertTrue(policy.can_surface(now, ctx))

    def test_cooldown_blocks_less_than_120_minutes(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime, timedelta
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        policy.record_delivery(now)
        ctx = InteractionContext(current_time=now + timedelta(minutes=60), session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        self.assertFalse(policy.can_surface(ctx.current_time, ctx))

    def test_cooldown_allows_at_120_minutes(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime, timedelta
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        policy.record_delivery(now)
        ctx = InteractionContext(current_time=now + timedelta(minutes=120), session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        self.assertTrue(policy.can_surface(ctx.current_time, ctx))

    def test_daily_limit_blocks_fourth_delivery(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime, timedelta
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        base = datetime(2025, 1, 1, 10, 0, 0)
        for i in range(3):
            policy.record_delivery(base + timedelta(minutes=i*130))
        ctx = InteractionContext(current_time=base + timedelta(minutes=400), session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        self.assertFalse(policy.can_surface(ctx.current_time, ctx))

    def test_proactive_disabled_blocks_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        from interaction.policy import InteractionContext
        ctx = InteractionContext(current_time=now, session_state=SessionState.IDLE, proactive_enabled=False, user_busy=False)
        self.assertFalse(policy.can_surface(now, ctx))

    def test_busy_user_blocks_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        from interaction.policy import InteractionContext
        ctx = InteractionContext(current_time=now, session_state=SessionState.IDLE, proactive_enabled=True, user_busy=True)
        self.assertFalse(policy.can_surface(now, ctx))

    def test_starting_blocks_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        ctx = InteractionContext(current_time=now, session_state=SessionState.STARTING, proactive_enabled=True, user_busy=False)
        self.assertFalse(policy.can_surface(now, ctx))

    def test_ending_blocks_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        ctx = InteractionContext(current_time=now, session_state=SessionState.ENDING, proactive_enabled=True, user_busy=False)
        self.assertFalse(policy.can_surface(now, ctx))

    def test_away_blocks_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        ctx = InteractionContext(current_time=now, session_state=SessionState.AWAY, proactive_enabled=True, user_busy=False)
        self.assertFalse(policy.can_surface(now, ctx))

    def test_idle_allows_humor(self):
        from intelligence.humor import HumorPolicy
        from datetime import datetime
        from context.context import SessionState
        from interaction.policy import InteractionContext

        policy = HumorPolicy()
        now = datetime(2025, 1, 1, 12, 0, 0)
        ctx = InteractionContext(current_time=now, session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        self.assertTrue(policy.can_surface(now, ctx))

    def test_evaluation_does_not_increment_humor_daily_count(self):
        from datetime import datetime
        from context.context import SessionState
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext

        intel, ctx = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        before = intel.humor_policy.daily_count
        intel.evaluate_humor_interaction(cand, engine, ctx)
        self.assertEqual(intel.humor_policy.daily_count, before)

    def test_evaluation_does_not_update_last_delivered_timestamp(self):
        from datetime import datetime
        from context.context import SessionState

        intel, ctx = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        before = intel.humor_policy.last_delivered_at
        intel.evaluate_humor_interaction(cand, engine, ctx)
        self.assertEqual(intel.humor_policy.last_delivered_at, before)

    def test_delivery_increments_humor_daily_count(self):
        from datetime import datetime
        from interaction.engine import InteractionEngine

        intel, _ = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        now = datetime(2025,1,1,12,0,0)
        before = intel.humor_policy.daily_count
        intel.deliver_humor(cand, engine, now)
        self.assertEqual(intel.humor_policy.daily_count, before + 1)

    def test_delivery_updates_last_delivered_timestamp(self):
        from datetime import datetime
        from interaction.engine import InteractionEngine

        intel, _ = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        now = datetime(2025,1,1,12,0,0)
        intel.deliver_humor(cand, engine, now)
        self.assertEqual(intel.humor_policy.last_delivered_at, now)

    def test_general_interaction_engine_cooldown_still_works(self):
        from datetime import datetime, timedelta
        from context.context import SessionState
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext

        intel, ctx = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        now = ctx.current_time
        intel.deliver_humor(cand, engine, now)
        # InteractionEngine cooldown is 30 min
        ctx2 = InteractionContext(current_time=now + timedelta(minutes=10), session_state=SessionState.IDLE, proactive_enabled=True, user_busy=False)
        decision = intel.evaluate_humor_interaction(cand, engine, ctx2)
        from interaction.policy import InteractionDecision
        self.assertEqual(decision, InteractionDecision.WAIT)

    def test_quiet_mode_still_works(self):
        from datetime import datetime
        from context.context import SessionState
        from interaction.engine import InteractionEngine
        from interaction.policy import InteractionContext

        intel, ctx = self._make_engine_and_context(datetime(2025,1,1,12,0,0))
        cand = intel.get_humor_candidate("debugging")
        engine = InteractionEngine()
        engine.set_quiet_mode(True)
        decision = intel.evaluate_humor_interaction(cand, engine, ctx)
        from interaction.policy import InteractionDecision
        self.assertEqual(decision, InteractionDecision.WAIT)


if __name__ == "__main__":
    unittest.main()
