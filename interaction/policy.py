from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from context.context import SessionState


class InteractionEventType(str, Enum):
    """Types of events that may cause VYRA to interact."""

    REMINDER_DUE = "reminder_due"
    REMINDER_MISSED = "reminder_missed"
    MORNING_START = "morning_start"
    USER_RETURNED = "user_returned"
    BREAK_SUGGESTION = "break_suggestion"
    INFORMATION_UPDATE = "information_update"
    PROACTIVE_THOUGHT = "proactive_thought"


class InteractionPriority(str, Enum):
    """Priority levels for VYRA interactions."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class InteractionDecision(str, Enum):
    """Possible decisions made by the interaction policy."""

    SPEAK = "speak"
    WAIT = "wait"


@dataclass
class InteractionEvent:
    """Something that may cause VYRA to speak."""

    event_type: str
    message: str
    priority: InteractionPriority


@dataclass
class InteractionContext:
    """Current context used to decide whether VYRA should speak."""

    current_time: datetime
    session_state: SessionState

    idle_seconds: float = 0.0

    user_active: bool = True
    user_busy: bool = False

    recent_interaction: bool = False

    proactive_enabled: bool = True


class InteractionPolicy:
    """Decides whether VYRA should proactively speak."""

    def should_speak(
        self,
        event: InteractionEvent,
        context: InteractionContext,
    ) -> InteractionDecision:
        """
        Decide whether VYRA should speak right now.

        Priority comes first.

        High/critical events can interrupt normal activity.

        Lower-priority events depend on the user's state.
        """

        # ---------------------------------------------------------
        # Global switch
        # ---------------------------------------------------------

        if not context.proactive_enabled:
            return InteractionDecision.WAIT

        # ---------------------------------------------------------
        # Critical events always speak.
        # ---------------------------------------------------------

        if event.priority == InteractionPriority.CRITICAL:
            return InteractionDecision.SPEAK

        # ---------------------------------------------------------
        # High-priority events are allowed even when busy.
        #
        # Example:
        # explicitly requested reminder
        # ---------------------------------------------------------

        if event.priority == InteractionPriority.HIGH:
            return InteractionDecision.SPEAK

        # ---------------------------------------------------------
        # First-session morning briefing.
        #
        # This is a controlled system event, not a random
        # proactive thought. It is allowed during startup/active
        # morning state as long as proactive behavior is enabled.
        # ---------------------------------------------------------

        if (
            event.event_type
            == InteractionEventType.MORNING_START.value
        ):
            if (
                context.session_state
                in {
                    SessionState.STARTING,
                    SessionState.ACTIVE,
                }
                and not context.recent_interaction
            ):
                return InteractionDecision.SPEAK

            return InteractionDecision.WAIT

        # ---------------------------------------------------------
        # User is explicitly focused/busy.
        #
        # Normal/low-priority proactive interaction should wait.
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.BUSY
        ):
            return InteractionDecision.WAIT

        if context.user_busy:
            return InteractionDecision.WAIT

        # ---------------------------------------------------------
        # AWAY
        #
        # Do not proactively speak to someone who is not
        # currently interacting with the computer.
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.AWAY
        ):
            return InteractionDecision.WAIT

        # ---------------------------------------------------------
        # Recent interaction cooldown.
        #
        # We don't want VYRA to immediately follow a user
        # interaction with another unsolicited message.
        # ---------------------------------------------------------

        if context.recent_interaction:
            return InteractionDecision.WAIT

        # ---------------------------------------------------------
        # IDLE
        #
        # Idle is actually a good opportunity for low/normal
        # proactive interaction.
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.IDLE
        ):
            return InteractionDecision.SPEAK

        # ---------------------------------------------------------
        # RETURNED
        #
        # Returning to the computer can be a reasonable time
        # for a contextual interaction.
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.RETURNED
        ):
            return InteractionDecision.SPEAK

        # ---------------------------------------------------------
        # ACTIVE
        #
        # We don't interrupt an actively used computer unless
        # the event has already passed the priority checks above.
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.ACTIVE
        ):
            return InteractionDecision.WAIT

        return InteractionDecision.WAIT