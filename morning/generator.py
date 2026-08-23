from brain.ollama_brain import OllamaBrain
from morning.context import MorningBriefingContext
from morning.prompt import MorningPromptBuilder
from morning.relevance import BriefingRelevanceSelector
from morning.context import with_selected_candidates


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
    ) -> str:
        """Select relevant facts and generate grounded briefing."""

        selected_candidates = (
            self.relevance_selector.select(
                context
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

        return response.strip()