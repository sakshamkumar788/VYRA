from datetime import datetime, timedelta


class DiscoveryPolicy:
    """Controls how frequently VYRA may proactively surprise the user."""

    DISCOVERY_COOLDOWN_MINUTES = 180
    FUN_FACT_COOLDOWN_MINUTES = 360

    def __init__(self) -> None:
        self.last_discovery_at: datetime | None = None
        self.frequency_adjustment: int = 0

    def set_frequency_adjustment(self, adjustment: int) -> None:
        """Set personalized frequency adjustment, clamped to -2..+2."""
        if adjustment < -2:
            adjustment = -2
        elif adjustment > 2:
            adjustment = 2
        self.frequency_adjustment = adjustment

    def effective_discovery_cooldown_minutes(self) -> int:
        """Return discovery cooldown adjusted for personalization."""
        mapping = {
            -2: 300,
            -1: 240,
            0: 180,
            1: 120,
            2: 90,
        }
        return mapping.get(self.frequency_adjustment, 180)

    def effective_fun_fact_cooldown_minutes(self) -> int:
        """Return fun-fact cooldown adjusted for personalization."""
        mapping = {
            -2: 540,
            -1: 450,
            0: 360,
            1: 300,
            2: 240,
        }
        return mapping.get(self.frequency_adjustment, 360)

    def can_discover(
        self,
        current_time: datetime,
    ) -> bool:
        """Return True when a general discovery is allowed."""

        if self.last_discovery_at is None:
            return True

        next_allowed = (
            self.last_discovery_at
            + timedelta(
                minutes=self.effective_discovery_cooldown_minutes()
            )
        )

        return current_time >= next_allowed

    def fun_fact_allowed(
        self,
        current_time: datetime,
    ) -> bool:
        """Return True when a fun fact is allowed."""

        if self.last_discovery_at is None:
            return True

        next_allowed = (
            self.last_discovery_at
            + timedelta(
                minutes=self.effective_fun_fact_cooldown_minutes()
            )
        )

        return current_time >= next_allowed

    def record_discovery(
        self,
        current_time: datetime,
    ) -> None:
        """Record that a discovery was delivered."""

        self.last_discovery_at = current_time