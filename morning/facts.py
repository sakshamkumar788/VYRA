from news.base import NewsProvider

from datetime import datetime, timedelta

from vyra_calendar.base import CalendarProvider


from datetime import datetime

from memory.database import (
    get_pending_tasks,
    get_recent_briefing_history,
    get_relevant_memories,
)

from tools.weather import get_weather

from morning.context import MorningBriefingContext

def _summarize_weather(
    weather_text: str,
) -> str:
    """Convert the weather tool response into a compact summary."""

    lines = [
        line.strip()
        for line in weather_text.splitlines()
        if line.strip()
    ]

    temperature = None
    conditions = None
    humidity = None
    wind = None

    for line in lines:
        if line.startswith("Temperature:"):
            temperature = line.replace(
                "Temperature:",
                "",
                1,
            ).strip()

        elif line.startswith("Conditions:"):
            conditions = line.replace(
                "Conditions:",
                "",
                1,
            ).strip()

        elif line.startswith("Humidity:"):
            humidity = line.replace(
                "Humidity:",
                "",
                1,
            ).strip()

        elif line.startswith("Wind:"):
            wind = line.replace(
                "Wind:",
                "",
                1,
            ).strip()

    parts: list[str] = []

    if temperature:
        parts.append(temperature)

    if conditions:
        parts.append(conditions)

    if humidity:
        parts.append(
            f"humidity {humidity}"
        )

    if wind:
        parts.append(
            f"wind {wind}"
        )

    if not parts:
        return weather_text.strip()

    return ", ".join(parts)

def _get_previous_briefing_topics() -> list[str]:
    """Return topics used in recent briefings."""

    history = get_recent_briefing_history(
        limit=7
    )

    topics: list[str] = []

    for row in history:
        briefing_date = row[0]
        topic_text = row[1]

        if not topic_text:
            continue

        for topic in topic_text.split(","):
            topic = topic.strip()

            if topic and topic not in topics:
                topics.append(topic)

    return topics

def _get_relevant_briefing_memories() -> list[str]:
    """
    Retrieve memories that may be relevant to the current
    morning/day context.

    Duplicate memory content is removed before it reaches
    the briefing selector.
    """

    query = (
        "today goals priorities study work "
        "learning project schedule"
    )

    memories = get_relevant_memories(
        query
    )

    relevant: list[str] = []
    seen: set[str] = set()

    for memory_type, content in memories:
        if not content:
            continue

        normalized = content.strip()

        if normalized in seen:
            continue

        seen.add(normalized)
        relevant.append(normalized)

    return relevant[:5]

class MorningFactsCollector:
    """Collect verified information for the morning briefing."""

    def __init__(
        self,
        calendar_provider: CalendarProvider | None = None,
        news_provider: NewsProvider | None = None,
    ) -> None:
        self.calendar_provider = calendar_provider
        self.news_provider = news_provider

    def _summarize_weather(
        weather_text: str,
    ) -> str:
        """Convert the weather tool's text response into a short summary."""

        lines = [
            line.strip()
            for line in weather_text.splitlines()
            if line.strip()
        ]

        temperature = None
        conditions = None
        humidity = None
        wind = None

        for line in lines:
            if line.startswith("Temperature:"):
                temperature = line.replace(
                    "Temperature:",
                    "",
                    1,
                ).strip()

            elif line.startswith("Conditions:"):
                conditions = line.replace(
                    "Conditions:",
                    "",
                    1,
                ).strip()

            elif line.startswith("Humidity:"):
                humidity = line.replace(
                    "Humidity:",
                    "",
                1,
                ).strip()

            elif line.startswith("Wind:"):
                wind = line.replace(
                    "Wind:",
                    "",
                1,
                ).strip()

        parts: list[str] = []

        if temperature:
            parts.append(temperature)

        if conditions:
            parts.append(conditions)

        if humidity:
            parts.append(
                f"humidity {humidity}"
            )

        if wind:
            parts.append(
                f"wind {wind}"
            )

        if not parts:
            return weather_text.strip()

        return ", ".join(parts)

    def collect(self) -> MorningBriefingContext:
        """Collect currently available morning facts."""

        now = datetime.now()

        important_events: list[str] = []

        if self.calendar_provider is not None:
            try:
                day_end = (
                    now
                    + timedelta(days=1)
                ).replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=0,
                )

                calendar_events = (
                    self.calendar_provider.get_events(
                        now,
                        day_end,
                    )
                )

                for event in calendar_events[:5]:
                    event_time = event.start_time.strftime(
                        "%I:%M %p"
                    ).lstrip("0")

                    if event.location:
                        important_events.append(
                            f"{event.title} at "
                            f"{event_time} "
                            f"({event.location})"
                        )
                    else:
                        important_events.append(
                            f"{event.title} at "
                            f"{event_time}"
                        )

            except Exception:
                important_events = []

        news_items: list[str] = []

        if self.news_provider is not None:
            try:
                latest_news = self.news_provider.get_latest(
                    limit=5
                )

                for item in latest_news:
                    if item.title:
                        if item.source:
                            news_items.append(
                                f"{item.title} ({item.source})"
                            )
                        else:
                            news_items.append(
                                item.title
                            )

            except Exception:
                news_items = []

        hour = now.hour

        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        tasks = get_pending_tasks()

        important_tasks: list[str] = []

        for task in tasks:
            (
                task_id,
                title,
                due_at,
                status,
                created_at,
                delivered_at,
                completed_at,
                missed_at,
            ) = task

            if status not in {
                "pending",
                "scheduled",
                "due",
            }:
                continue

            if due_at:
                important_tasks.append(
                    f"Reminder scheduled: {title} at {due_at}"
                )
            else:
                important_tasks.append(title)

        weather_summary: str | None = None

        try:
            weather_result = get_weather(
                "Jalandhar, Punjab, India",
            period="current",
        )

            weather_summary = _summarize_weather(
                weather_result
        )
            
        except Exception:
            weather_summary = None

        previously_used_topics = (
            _get_previous_briefing_topics()
        )

        relevant_memories = (
            _get_relevant_briefing_memories()
        )

        return MorningBriefingContext(
            current_time=now.strftime(
                "%I:%M %p"
            ).lstrip("0"),

            time_of_day=time_of_day,

            weather=weather_summary,

            news_items=news_items,

            important_tasks=important_tasks[:3],

            important_events=important_events,

            relevant_memories=relevant_memories,

            previously_used_topics=(
                previously_used_topics
            ),
        )