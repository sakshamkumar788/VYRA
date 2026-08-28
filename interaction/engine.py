from datetime import datetime, timedelta

from context.context import SessionState

from interaction.policy import (
    InteractionContext,
    InteractionDecision,
    InteractionEvent,
    InteractionEventType,
    InteractionPolicy,
    InteractionPriority,
)

from memory.database import load_interaction_state, save_interaction_state


class InteractionEngine:
    """
    Controls whether VYRA is allowed to proactively speak.

    Explicit/high-priority events are treated differently from
    ordinary proactive thoughts.
    """

    PROACTIVE_COOLDOWN_MINUTES = 30
    MAX_PROACTIVE_INTERACTIONS_PER_DAY = 6

    def __init__(self) -> None:
        self.policy = InteractionPolicy()

        # Load persisted proactive state
        self.last_proactive_interaction: datetime | None = None
        try:
            persisted_last = load_interaction_state("last_proactive_interaction")
            if persisted_last:
                self.last_proactive_interaction = datetime.fromisoformat(persisted_last)
        except Exception:
            self.last_proactive_interaction = None

        # Daily interaction date
        try:
            persisted_date = load_interaction_state("daily_interaction_date")
            if persisted_date:
                self._daily_interaction_date = datetime.fromisoformat(persisted_date).date()
            else:
                self._daily_interaction_date = datetime.now().date()
        except Exception:
            self._daily_interaction_date = datetime.now().date()

        # Daily proactive count
        try:
            persisted_count = load_interaction_state("daily_proactive_count")
            if persisted_count is not None:
                self._daily_proactive_count = int(persisted_count)
            else:
                self._daily_proactive_count = 0
        except Exception:
            self._daily_proactive_count = 0

        self.quiet_mode = False
        self._recent_event_types: list[str] = []

    # =========================================================
    # DAILY COUNTER
    # =========================================================

    def _reset_daily_counter_if_needed(
        self,
        current_time: datetime,
    ) -> None:
        """Reset the proactive count when a new day begins."""

        if (
            current_time.date()
            != self._daily_interaction_date
        ):
            self._daily_interaction_date = current_time.date()
            self._daily_proactive_count = 0
            self._recent_event_types.clear()
            # Persist reset daily state
            try:
                save_interaction_state("daily_interaction_date", self._daily_interaction_date.isoformat())
                save_interaction_state("daily_proactive_count", str(self._daily_proactive_count))
            except Exception:
                pass

    # =========================================================
    # QUIET MODE
    # =========================================================

    def set_quiet_mode(
        self,
        enabled: bool,
    ) -> None:
        """Enable or disable proactive quiet mode."""

        self.quiet_mode = enabled

    # =========================================================
    # COOLDOWN
    # =========================================================

    def is_in_cooldown(
        self,
        current_time: datetime,
    ) -> bool:
        """Return True when VYRA recently spoke proactively."""

        if self.last_proactive_interaction is None:
            return False

        cooldown_until = (
            self.last_proactive_interaction
            + timedelta(
                minutes=self.PROACTIVE_COOLDOWN_MINUTES
            )
        )

        return current_time < cooldown_until

    # =========================================================
    # EVENT DEDUPLICATION
    # =========================================================

    def has_recent_event(
        self,
        event_type: str,
    ) -> bool:
        """Return True if this event type was recently delivered."""

        return event_type in self._recent_event_types

    # =========================================================
    # EVALUATION
    # =========================================================

    def evaluate(
        self,
        event: InteractionEvent,
        context: InteractionContext,
    ) -> InteractionDecision:
        """
        Decide whether VYRA should speak.

        Order:

        1. Global proactive switch
        2. Critical events
        3. Explicit/high-priority events
        4. Quiet mode
        5. Daily limit
        6. Cooldown
        7. Recently-used event
        8. User state
        """

        self._reset_daily_counter_if_needed(
            context.current_time
        )

        # -----------------------------------------------------
        # Global switch
        # -----------------------------------------------------

        if not context.proactive_enabled:
            return InteractionDecision.WAIT

        # -----------------------------------------------------
        # Critical
        # -----------------------------------------------------

        if (
            event.priority
            == InteractionPriority.CRITICAL
        ):
            return InteractionDecision.SPEAK

        # -----------------------------------------------------
        # Explicit/high priority
        #
        # These bypass normal proactive restrictions.
        # -----------------------------------------------------

        if (
            event.priority
            == InteractionPriority.HIGH
        ):
            return self.policy.should_speak(
                event,
                context,
            )

        # -----------------------------------------------------
        # Quiet mode
        # -----------------------------------------------------

        if self.quiet_mode:
            return InteractionDecision.WAIT

        # -----------------------------------------------------
        # Daily proactive limit
        # -----------------------------------------------------

        if (
            self._daily_proactive_count
            >= self.MAX_PROACTIVE_INTERACTIONS_PER_DAY
        ):
            return InteractionDecision.WAIT

        # -----------------------------------------------------
        # Cooldown
        # -----------------------------------------------------

        if self.is_in_cooldown(
            context.current_time
        ):
            return InteractionDecision.WAIT

        # -----------------------------------------------------
        # Duplicate event suppression
        # -----------------------------------------------------

        if self.has_recent_event(
            event.event_type
        ):
            return InteractionDecision.WAIT

        # -----------------------------------------------------
        # Delegate context decision to policy.
        # -----------------------------------------------------

        decision = self.policy.should_speak(
            event,
            context,
        )

        return decision

    # =========================================================
    # RECORDING
    # =========================================================

    def record_proactive_interaction(
        self,
        event: InteractionEvent,
        current_time: datetime,
    ) -> None:
        """
        Record that a normal proactive interaction was actually
        delivered to the user.
        """

        self._reset_daily_counter_if_needed(
            current_time
        )

        if (
            event.priority
            in {
                InteractionPriority.LOW,
                InteractionPriority.NORMAL,
            }
        ):
            self.last_proactive_interaction = current_time
            self._daily_proactive_count += 1
            self._recent_event_types.append(event.event_type)
            self._recent_event_types = self._recent_event_types[-10:]

            # Persist state
            try:
                save_interaction_state("last_proactive_interaction", self.last_proactive_interaction.isoformat())
                save_interaction_state("daily_proactive_count", str(self._daily_proactive_count))
                save_interaction_state("daily_interaction_date", self._daily_interaction_date.isoformat())
            except Exception:
                pass

    # =========================================================
    # CONTEXT CREATION
    # =========================================================

    def create_context(
        self,
        session_state: SessionState,
        idle_seconds: float,
        user_busy: bool = False,
        user_active: bool = True,
        recent_interaction: bool = False,
        proactive_enabled: bool = True,
    ) -> InteractionContext:
        """Create interaction context from VYRA state."""

        return InteractionContext(
            current_time=datetime.now(),
            session_state=session_state,
            idle_seconds=idle_seconds,
            user_active=user_active,
            user_busy=user_busy,
            recent_interaction=recent_interaction,
            proactive_enabled=proactive_enabled,
        )