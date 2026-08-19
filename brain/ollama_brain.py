from ollama import chat


class OllamaBrain:
    def __init__(self, model: str = "gemma3:4b") -> None:
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Send messages to the local Ollama model."""
        response = chat(
            model=self.model,
            messages=messages,
        )

        return response.message.content.strip()