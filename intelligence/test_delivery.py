from intelligence.delivery import (
    IntelligenceDeliveryPolicy,
)
from intelligence.priority import (
    IntelligencePriority,
    PriorityDecision,
)


def main() -> None:
    policy = IntelligenceDeliveryPolicy()

    urgent = policy.evaluate(
        PriorityDecision(
            priority=IntelligencePriority.URGENT,
            action="consider_interrupt",
            reason="serious local event",
        )
    )

    important = policy.evaluate(
        PriorityDecision(
            priority=IntelligencePriority.IMPORTANT,
            action="tell_at_next_opportunity",
            reason="major India development",
        )
    )

    interesting = policy.evaluate(
        PriorityDecision(
            priority=IntelligencePriority.INTERESTING,
            action="save_for_later",
            reason="interesting research",
        )
    )

    on_demand = policy.evaluate(
        PriorityDecision(
            priority=IntelligencePriority.ON_DEMAND,
            action="available_when_asked",
            reason="general current affairs",
        )
    )

    ignored = policy.evaluate(
        PriorityDecision(
            priority=IntelligencePriority.IGNORE,
            action="ignore",
            reason="not relevant",
        )
    )

    print("Urgent:", urgent)
    print("Important:", important)
    print("Interesting:", interesting)
    print("On demand:", on_demand)
    print("Ignored:", ignored)

    assert urgent.should_surface is True
    assert urgent.action == "interrupt_candidate"

    assert important.should_surface is True
    assert important.action == "next_opportunity"

    assert interesting.should_surface is True
    assert interesting.action == "save_for_later"

    assert on_demand.should_surface is False
    assert ignored.should_surface is False

    print("All delivery policy tests passed.")


if __name__ == "__main__":
    main()