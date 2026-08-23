from dataclasses import dataclass


@dataclass
class MorningBriefingFacts:
    """Verified information available for a briefing."""

    current_time: str

    time_of_day: str

    weather_summary: str | None = None
    important_tasks: list[str] | None = None
    important_events: list[str] | None = None
    news_summary: str | None = None
    relevant_note: str | None = None


class MorningBriefingComposer:
    """Build a natural briefing from verified facts."""

    def compose(
        self,
        facts: MorningBriefingFacts,
    ) -> str:
        """Compose a concise briefing without inventing facts."""

        if facts.time_of_day == "morning":
            opening = "Good morning."
        elif facts.time_of_day == "afternoon":
            opening = "Good afternoon."
        elif facts.time_of_day == "evening":
            opening = "Good evening."
        else:
            opening = "It's getting late."

        parts: list[str] = [
            f"{opening} It's {facts.current_time}."
        ]

        if facts.weather_summary:
            parts.append(
                f"Weather: {facts.weather_summary}"
            )

        if facts.important_tasks:
            task_text = "; ".join(
                facts.important_tasks[:3]
            )

            parts.append(
                f"Important today: {task_text}."
            )

        if facts.important_events:
            event_text = "; ".join(
                facts.important_events[:3]
            )

            parts.append(
                f"Coming up: {event_text}."
            )

        if facts.news_summary:
            parts.append(
                f"One thing worth knowing: "
                f"{facts.news_summary}."
            )

        if facts.relevant_note:
            parts.append(
                facts.relevant_note
            )

        return " ".join(parts)