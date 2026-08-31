from typing import Protocol


class InputProvider(Protocol):
    def get_text(self, prompt: str) -> str:
        ...


class ConsoleInputProvider:
    def get_text(self, prompt: str) -> str:
        return input(prompt)


def get_default_provider() -> InputProvider:
    return ConsoleInputProvider()
