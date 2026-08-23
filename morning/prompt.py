from morning.context import MorningBriefingContext


class MorningPromptBuilder:
    """Builds a grounded prompt for VYRA's language model."""

    def build(
        self,
        context: MorningBriefingContext,
    ) -> str:
        """Build a prompt that prevents factual invention."""

        sections: list[str] = []

        sections.append(
            f"Current time: {context.current_time}"
        )

        sections.append(
            f"Time of day: {context.time_of_day}"
        )

        if context.weather:
            sections.append(
                f"Weather: {context.weather}"
            )

        if context.important_tasks:
            sections.append(
                "Important tasks:\n"
                + "\n".join(
                    f"- {task}"
                    for task in context.important_tasks
                )
            )

        if context.important_events:
            sections.append(
                "Important events:\n"
                + "\n".join(
                    f"- {event}"
                    for event in context.important_events
                )
            )

        if context.news_items:
            sections.append(
                "News:\n"
                + "\n".join(
                    f"- {item}"
                    for item in context.news_items
                )
            )

        if context.relevant_memories:
            sections.append(
                "Relevant memories:\n"
                + "\n".join(
                    f"- {memory}"
                    for memory in context.relevant_memories
                )
            )

        if context.current_goals:
            sections.append(
                "Current goals:\n"
                + "\n".join(
                    f"- {goal}"
                    for goal in context.current_goals
                )
            )

        if context.recently_discussed_topics:
            sections.append(
                "Recently discussed topics:\n"
                + "\n".join(
                    f"- {topic}"
                    for topic in context.recently_discussed_topics
                )
            )

        if context.previously_used_topics:
            sections.append(
                "Topics used recently in briefings:\n"
                + "\n".join(
                    f"- {topic}"
                    for topic in context.previously_used_topics
                )
            )

        facts = "\n\n".join(sections)

        return f"""
You are VYRA, a personal AI companion.

Create a natural, concise daily briefing using ONLY the
verified information provided below.

The briefing should match the current time of day.

Rules:
- Do not invent facts.
- Do not claim that something is happening unless it appears
  in the provided information.
- A scheduled task or reminder does not mean the user actually performed the task.
- Do not mention every available fact.
- Select only information that is genuinely useful.
- Avoid repeating recently used topics unless the information
  has materially changed or is important.
- Avoid generic filler.
- Do not sound like a checklist.
- Vary wording naturally.
- Maintain VYRA's warm, intelligent, slightly playful personality.
- Do not repeatedly use the same greeting structure.
- Keep the briefing conversational.
- Never say "good morning" when the current time is not morning.
- Never describe the briefing as a morning briefing unless the
  time of day is actually morning.

Verified information:

{facts}
""".strip()