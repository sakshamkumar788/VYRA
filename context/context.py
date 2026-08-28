from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo


class SessionState(str, Enum):
    """Current state of the VYRA session/user."""

    STARTING = "starting"
    ACTIVE = "active"
    INPUT_ACTIVE = "input_active"
    BUSY = "busy"
    IDLE = "idle"
    AWAY = "away"
    RETURNED = "returned"
    ENDING = "ending"


@dataclass
class UserContext:
    """Information VYRA knows about the user's current state."""

    current_time: datetime
    session_state: SessionState

    last_user_interaction: datetime | None = None
    last_vyra_interaction: datetime | None = None

    user_active: bool = True
    user_busy: bool = False

    idle_seconds: float = 0.0
    activity_count: int = 0

    current_location: str | None = None

@dataclass
class DailySessionState:
    """State that resets when a new calendar day begins."""

    date: str
    morning_briefing_completed: bool = False
    first_meaningful_session_started: bool = False

class ContextManager:
    """Maintains VYRA's current interaction context."""

    def __init__(
        self,
        timezone: str = "Asia/Kolkata",
        idle_threshold_seconds: int = 300,
        away_threshold_seconds: int = 1800,
    ) -> None:
        self.timezone = timezone

        self.idle_threshold_seconds = (
            idle_threshold_seconds
        )

        self.away_threshold_seconds = (
            away_threshold_seconds
        )

        now = self.now()

        self.context = UserContext(
            current_time=now,
            session_state=SessionState.STARTING,
        )

        self.daily_state = DailySessionState(
            date=now.date().isoformat()
        )

    def update_daily_state(self) -> None:
        """Reset daily session flags when a new day begins."""

        today = self.now().date().isoformat()

        if today != self.daily_state.date:
            self.daily_state.date = today
            self.daily_state.morning_briefing_completed = False
            self.daily_state.first_meaningful_session_started = False

    # =========================================================
    # TIME
    # =========================================================

    def now(self) -> datetime:
        """Return the current time in VYRA's timezone."""

        return datetime.now(
            ZoneInfo(self.timezone)
        )

    def update_time(self) -> None:
        """Refresh time and daily session state."""

        self.context.current_time = self.now()

        self.update_daily_state()

    def update_location(
        self,
        location_name: str | None,
    ) -> None:
        """Update the current coarse location."""

        self.update_time()

        self.context.current_location = location_name

    def start_meaningful_session(self) -> None:
        """Mark that the user has meaningfully started VYRA for today."""

        self.update_daily_state()

        self.daily_state.first_meaningful_session_started = True

    def is_morning_briefing_needed(self) -> bool:
        """Return whether today's morning briefing is still pending."""

        self.update_daily_state()

        return (
            not self.daily_state.morning_briefing_completed
            and not self.daily_state.first_meaningful_session_started
        )

    def mark_morning_briefing_completed(self) -> None:
        """Mark today's morning briefing as completed."""

        self.update_daily_state()

        self.daily_state.morning_briefing_completed = True
        self.daily_state.first_meaningful_session_started = True

    # =========================================================
    # USER / VYRA INTERACTION
    # =========================================================

    def mark_user_interaction(self) -> None:
        """Record that the user directly interacted with VYRA."""

        now = self.now()

        self.context.current_time = now
        self.context.last_user_interaction = now
        self.context.user_active = True
        self.context.idle_seconds = 0.0
        self.context.session_state = SessionState.ACTIVE

    def mark_vyra_interaction(self) -> None:
        """Record that VYRA proactively interacted."""

        now = self.now()

        self.context.current_time = now
        self.context.last_vyra_interaction = now

    # =========================================================
    # SESSION
    # =========================================================

    def start_session(self) -> None:
        """Start a VYRA session."""

        now = self.now()

        self.context.current_time = now
        self.context.session_state = SessionState.ACTIVE
        self.context.user_active = True
        self.context.user_busy = False
        self.context.idle_seconds = 0.0
        self.context.activity_count = 0

    def end_session(self) -> None:
        """End the current VYRA session."""

        self.update_time()

        self.context.session_state = SessionState.ENDING

    # =========================================================
    # ACTIVITY
    # =========================================================

    def update_activity(
        self,
        idle_seconds: float,
        activity_count: int = 0,
        focused: bool = False,
    ) -> None:
        """
        Update the user's current state from activity signals.

        State priority:

        AWAY
        IDLE
        BUSY
        INPUT_ACTIVE
        ACTIVE
        """

        self.update_time()

        previous_state = (
            self.context.session_state
        )

        self.context.idle_seconds = idle_seconds
        self.context.activity_count = activity_count

        # -----------------------------------------------------
        # AWAY
        # -----------------------------------------------------

        if (
            idle_seconds
            >= self.away_threshold_seconds
        ):
            new_state = SessionState.AWAY

            self.context.user_active = False
            self.context.user_busy = False

        # -----------------------------------------------------
        # IDLE
        # -----------------------------------------------------

        elif (
            idle_seconds
            >= self.idle_threshold_seconds
        ):
            new_state = SessionState.IDLE

            self.context.user_active = False
            self.context.user_busy = False

        # -----------------------------------------------------
        # BUSY
        # -----------------------------------------------------

        elif focused:
            new_state = SessionState.BUSY

            self.context.user_active = True
            self.context.user_busy = True

        # -----------------------------------------------------
        # INPUT ACTIVE
        # -----------------------------------------------------

        elif activity_count > 0:
            new_state = SessionState.INPUT_ACTIVE

            self.context.user_active = True
            self.context.user_busy = False

        # -----------------------------------------------------
        # NORMAL ACTIVE
        # -----------------------------------------------------

        else:
            new_state = SessionState.ACTIVE

            self.context.user_active = True
            self.context.user_busy = False

        # -----------------------------------------------------
        # RETURNED
        #
        # If the user was away/idle and becomes active again,
        # expose that transition as RETURNED.
        # -----------------------------------------------------

        if (
            previous_state
            in {
                SessionState.IDLE,
                SessionState.AWAY,
            }
            and new_state
            in {
                SessionState.ACTIVE,
                SessionState.INPUT_ACTIVE,
                SessionState.BUSY,
            }
        ):
            new_state = SessionState.RETURNED

        self.context.session_state = new_state

    # =========================================================
    # MANUAL STATE CONTROLS
    # =========================================================

    def mark_idle(self) -> None:
        """Manually mark the user as idle."""

        self.update_time()

        self.context.user_active = False
        self.context.user_busy = False
        self.context.session_state = SessionState.IDLE

    def set_busy(
        self,
        busy: bool,
    ) -> None:
        """Set the user's focused/busy state explicitly."""

        self.context.user_busy = busy

        if busy:
            self.context.user_active = True
            self.context.session_state = SessionState.BUSY

        elif self.context.user_active:
            self.context.session_state = (
                SessionState.ACTIVE
            )

    def set_focus_state(
        self,
        focused: bool,
    ) -> None:
        """
        Set the user's focus state.

        This remains available for testing and future
        higher-confidence focus signals.
        """

        self.context.user_busy = focused

        if focused:
            self.context.user_active = True
            self.context.session_state = SessionState.BUSY

        elif self.context.user_active:
            self.context.session_state = (
                SessionState.ACTIVE
            )