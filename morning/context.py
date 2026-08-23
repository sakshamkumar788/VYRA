from dataclasses import dataclass, field


@dataclass
class MorningBriefingContext:
    """Structured facts available to VYRA for a morning briefing."""

    current_time: str
    time_of_day: str

    weather: str | None = None

    important_tasks: list[str] = field(
        default_factory=list
    )

    important_events: list[str] = field(
        default_factory=list
    )

    news_items: list[str] = field(
        default_factory=list
    )

    relevant_memories: list[str] = field(
        default_factory=list
    )

    current_goals: list[str] = field(
        default_factory=list
    )

    recently_discussed_topics: list[str] = field(
        default_factory=list
    )

    previously_used_topics: list[str] = field(
        default_factory=list
    )

def with_selected_candidates(
    context: MorningBriefingContext,
    candidates,
) -> MorningBriefingContext:
    """
    Return a copy of the briefing context containing only
    information selected for the final briefing.
    """

    selected_weather = None
    selected_tasks: list[str] = []
    selected_events: list[str] = []
    selected_news: list[str] = []
    selected_memories: list[str] = []
    selected_goals: list[str] = []

    for candidate in candidates:
        if candidate.topic == "weather":
            selected_weather = candidate.content

        elif candidate.topic == "task":
            selected_tasks.append(
                candidate.content
            )

        elif candidate.topic == "event":
            selected_events.append(
                candidate.content
            )

        elif candidate.topic == "news":
            selected_news.append(
                candidate.content
            )

        elif candidate.topic == "memory":
            selected_memories.append(
                candidate.content
            )

        elif candidate.topic == "goal":
            selected_goals.append(
                candidate.content
            )

    return MorningBriefingContext(
        current_time=context.current_time,
        time_of_day=context.time_of_day,
        weather=selected_weather,
        important_tasks=selected_tasks,
        important_events=selected_events,
        news_items=selected_news,
        relevant_memories=selected_memories,
        current_goals=selected_goals,
        recently_discussed_topics=(
            context.recently_discussed_topics
        ),
        previously_used_topics=(
            context.previously_used_topics
        ),
    )