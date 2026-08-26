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

    # ---------------------------------------------------------
    # Personalized discovery frequency
    # ---------------------------------------------------------

    base_now = datetime(2026, 1, 1, 12, 0, 0)

    # default adjustment
    policy_p = DiscoveryPolicy()
    assert policy_p.frequency_adjustment == 0
    assert policy_p.effective_discovery_cooldown_minutes() == 180
    assert policy_p.effective_fun_fact_cooldown_minutes() == 360

    # adjustment -2
    policy_p.set_frequency_adjustment(-2)
    assert policy_p.frequency_adjustment == -2
    assert policy_p.effective_discovery_cooldown_minutes() == 300
    assert policy_p.effective_fun_fact_cooldown_minutes() == 540
    policy_p.record_discovery(base_now)
    assert policy_p.can_discover(base_now + timedelta(minutes=299)) is False
    assert policy_p.can_discover(base_now + timedelta(minutes=300)) is True
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=539)) is False
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=540)) is True

    # adjustment -1
    policy_p.set_frequency_adjustment(-1)
    assert policy_p.effective_discovery_cooldown_minutes() == 240
    assert policy_p.effective_fun_fact_cooldown_minutes() == 450
    policy_p.record_discovery(base_now)
    assert policy_p.can_discover(base_now + timedelta(minutes=239)) is False
    assert policy_p.can_discover(base_now + timedelta(minutes=240)) is True
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=449)) is False
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=450)) is True

    # adjustment 0
    policy_p.set_frequency_adjustment(0)
    assert policy_p.effective_discovery_cooldown_minutes() == 180
    assert policy_p.effective_fun_fact_cooldown_minutes() == 360

    # adjustment +1
    policy_p.set_frequency_adjustment(1)
    assert policy_p.effective_discovery_cooldown_minutes() == 120
    assert policy_p.effective_fun_fact_cooldown_minutes() == 300
    policy_p.record_discovery(base_now)
    assert policy_p.can_discover(base_now + timedelta(minutes=119)) is False
    assert policy_p.can_discover(base_now + timedelta(minutes=120)) is True
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=299)) is False
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=300)) is True

    # adjustment +2
    policy_p.set_frequency_adjustment(2)
    assert policy_p.effective_discovery_cooldown_minutes() == 90
    assert policy_p.effective_fun_fact_cooldown_minutes() == 240
    policy_p.record_discovery(base_now)
    assert policy_p.can_discover(base_now + timedelta(minutes=89)) is False
    assert policy_p.can_discover(base_now + timedelta(minutes=90)) is True
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=239)) is False
    assert policy_p.fun_fact_allowed(base_now + timedelta(minutes=240)) is True

    # clamping
    policy_clamp = DiscoveryPolicy()
    policy_clamp.set_frequency_adjustment(-5)
    assert policy_clamp.frequency_adjustment == -2
    policy_clamp.set_frequency_adjustment(10)
    assert policy_clamp.frequency_adjustment == 2

    print("All discovery policy tests passed.")


if __name__ == "__main__":
    main()