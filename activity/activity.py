import time

from activity.monitor import ActivityMonitor


monitor = ActivityMonitor()

monitor.start()

print("Activity monitor started.")
print()
print("For the first 10 seconds:")
print("Move the mouse and/or type normally.")
print()
print("Then stop interacting and watch the values.")
print()

try:
    for second in range(20):
        time.sleep(1)

        idle_seconds = monitor.get_idle_seconds()

        activity_count = (
            monitor.get_activity_count(
                window_seconds=10
            )
        )

        focused = (
            monitor.is_likely_focused(
                minimum_events=10,
                window_seconds=10,
            )
        )

        print(
            f"{second + 1:02d}s | "
            f"idle={idle_seconds:.1f}s | "
            f"events_10s={activity_count} | "
            f"focused={focused}"
        )

finally:
    monitor.stop()

print()
print("Activity monitor stopped.")