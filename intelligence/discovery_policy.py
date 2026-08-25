from datetime import datetime, timedelta


class DiscoveryPolicy:
    """Controls how frequently VYRA may proactively surprise the user."""

    DISCOVERY_COOLDOWN_MINUTES = 180
    FUN_FACT_COOLDOWN_MINUTES = 360

    def __init__(self) -> None:
        self.last_discovery_at: datetime | None = None

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
                minutes=self.DISCOVERY_COOLDOWN_MINUTES
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
                minutes=self.FUN_FACT_COOLDOWN_MINUTES
            )
        )

        return current_time >= next_allowed

    def record_discovery(
        self,
        current_time: datetime,
    ) -> None:
        """Record that a discovery was delivered."""

        self.last_discovery_at = current_time