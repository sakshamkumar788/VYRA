from dataclasses import dataclass
from datetime import datetime

from context.context import SessionState
from interaction.policy import (
    InteractionEvent,
    InteractionEventType,
    InteractionPriority,
)


@dataclass
class EventGenerationContext:
    """Context used to generate candidate proactive events."""

    current_time: datetime
    session_state: SessionState

    idle_seconds: float = 0.0
    activity_count: int = 0

    user_active: bool = True
    user_busy: bool = False

    proactive_enabled: bool = True

    morning_briefing_completed: bool = False
    morning_briefing_needed: bool = False

    user_returned: bool = False


class ProactiveEventGenerator:
    """
    Generates candidate events that VYRA may want to surface.

    IMPORTANT:
    This class does NOT decide whether VYRA should actually speak.

    It only proposes candidate events.
    """

    def generate(
        self,
        context: EventGenerationContext,
    ) -> list[InteractionEvent]:
        """Generate candidate proactive interaction events."""

        if not context.proactive_enabled:
            return []

        events: list[InteractionEvent] = []

        # ---------------------------------------------------------
        # User returned
        # ---------------------------------------------------------

        if context.user_returned:
            events.append(
                InteractionEvent(
                    event_type=(
                        InteractionEventType.USER_RETURNED.value
                    ),
                    message="The user has returned to the computer.",
                    priority=InteractionPriority.NORMAL,
                )
            )

        # ---------------------------------------------------------
        # Morning briefing
        # ---------------------------------------------------------

        if (
            5 <= context.current_time.hour < 12
            and context.morning_briefing_needed
        ):
            events.append(
                InteractionEvent(
                    event_type=(
                        InteractionEventType.MORNING_START.value
                    ),
                    message="A morning briefing may be appropriate.",
                    priority=InteractionPriority.NORMAL,
                )
            )

        # ---------------------------------------------------------
        # Long idle
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.IDLE
            and context.idle_seconds >= 300
        ):
            events.append(
                InteractionEvent(
                    event_type=(
                        InteractionEventType.PROACTIVE_THOUGHT.value
                    ),
                    message=(
                        "The user has been idle for a while."
                    ),
                    priority=InteractionPriority.LOW,
                )
            )

        # ---------------------------------------------------------
        # Long away state
        # ---------------------------------------------------------

        if (
            context.session_state
            == SessionState.AWAY
        ):
            # Do not automatically create a spoken event here.
            # Being away generally means VYRA should stay quiet.
            pass

        return events