from threading import Event, Thread


class ProactiveLoop:
    """
    Background loop for VYRA's proactive interaction system.

    This loop does NOT directly decide what VYRA should say.
    It asks the owner callback to evaluate the current context
    and candidate events.
    """

    def __init__(
        self,
        callback,
        interval_seconds: int = 15,
    ) -> None:
        self.callback = callback
        self.interval_seconds = interval_seconds

        self._stop_event = Event()
        self._thread: Thread | None = None

    def _run(self) -> None:
        """Continuously evaluate proactive candidates."""

        while not self._stop_event.is_set():
            try:
                self.callback()

            except Exception as error:
                print(
                    f"\nVYRA proactive loop error: {error}\n"
                )

            self._stop_event.wait(
                self.interval_seconds
            )

    def start(self) -> None:
        """Start the proactive loop."""

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            name="VYRA-Proactive",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """Stop the proactive loop."""

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            self._thread.join(
                timeout=1
            )