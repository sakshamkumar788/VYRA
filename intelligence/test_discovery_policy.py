from datetime import datetime, timedelta

from intelligence.discovery_policy import DiscoveryPolicy


def main() -> None:
    policy = DiscoveryPolicy()

    now = datetime.now()

    # ---------------------------------------------------------
    # Initial state
    # ---------------------------------------------------------

    assert policy.can_discover(now) is True
    assert policy.fun_fact_allowed(now) is True

    # ---------------------------------------------------------
    # Record a discovery
    # ---------------------------------------------------------

    policy.record_discovery(now)

    # General discovery cooldown = 180 minutes
    assert (
        policy.can_discover(
            now + timedelta(minutes=30)
        )
        is False
    )

    assert (
        policy.can_discover(
            now + timedelta(minutes=179)
        )
        is False
    )

    assert (
        policy.can_discover(
            now + timedelta(minutes=180)
        )
        is True
    )

    # ---------------------------------------------------------
    # Fun-fact cooldown = 360 minutes
    # ---------------------------------------------------------

    assert (
        policy.fun_fact_allowed(
            now + timedelta(minutes=180)
        )
        is False
    )

    assert (
        policy.fun_fact_allowed(
            now + timedelta(minutes=359)
        )
        is False
    )

    assert (
        policy.fun_fact_allowed(
            now + timedelta(minutes=360)
        )
        is True
    )

    print("All discovery policy tests passed.")


if __name__ == "__main__":
    main()