from brain.ollama_brain import OllamaBrain
from morning.context import MorningBriefingContext
from morning.prompt import MorningPromptBuilder
from morning.relevance import BriefingRelevanceSelector
from morning.context import with_selected_candidates

from intelligence.trends import build_trend_context, format_trend_context, TrendContext
from intelligence.feedback import FeedbackProfile


class MorningBriefingGenerator:
    """Generates a natural VYRA morning briefing from verified facts."""

    def __init__(
        self,
        brain: OllamaBrain | None = None,
    ) -> None:
        self.brain = brain or OllamaBrain()
        self.prompt_builder = MorningPromptBuilder()
        self.relevance_selector = (
            BriefingRelevanceSelector()
        )

    def generate(
        self,
        context: MorningBriefingContext,
        feedback_profile: FeedbackProfile | None = None,
        trend_ctx: TrendContext | None = None,
    ) -> str:
        """Select relevant facts and generate grounded briefing."""

        selected_candidates = (
            self.relevance_selector.select(
                context,
                feedback_profile=feedback_profile,
            )
        )

        selected_context = (
            with_selected_candidates(
                context,
                selected_candidates,
            )
        )

        prompt = self.prompt_builder.build(
            selected_context
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are VYRA, a personal AI companion. "
                    "You speak naturally, warmly, intelligently, "
                    "and without sounding scripted. "
                    "You must use only the verified facts supplied "
                    "in the user message. Never invent facts."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = self.brain.generate(
            messages
        )

        briefing = response.strip()

        # Append deterministic trend section if provided.
        if trend_ctx is not None:
            trend_str = format_trend_context(trend_ctx)
            if trend_str:
                briefing += " " + trend_str

        return briefing