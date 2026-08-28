import re
from dataclasses import dataclass
from typing import Any

from tools.registry import ToolRegistry


@dataclass
class ToolRequest:
    """A validated request to execute a tool."""

    tool_name: str
    arguments: dict[str, Any]


class ToolRouter:
    """
    Central routing layer for VYRA tools.

    The router:
    1. Detects whether a user message requires a tool.
    2. Extracts the tool arguments.
    3. Creates a structured ToolRequest.
    4. Executes the request through ToolRegistry.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def detect(self, user_input: str) -> ToolRequest | None:
        """
        Detect a tool request from natural language.

        Current supported tools:
        - weather
        - calculator

        More tools will be added later.
        """

        weather_request = self._detect_weather(user_input)

        if weather_request is not None:
            return weather_request

        calculator_request = self._detect_calculator(user_input)

        if calculator_request is not None:
            return calculator_request

        return None

    def execute(self, request: ToolRequest) -> str:
        """Execute a validated tool request."""

        return self.registry.execute(
            request.tool_name,
            **request.arguments,
        )

    def _detect_weather(
        self,
        user_input: str,
    ) -> ToolRequest | None:
        """Detect and structure a weather request."""

        message = user_input.strip()

        weather_patterns = [
            r"\bweather\b",
            r"\btemperature\b",
            r"\bforecast\b",
        ]

        is_weather_request = any(
            re.search(
                pattern,
                message,
                re.IGNORECASE,
            )
            for pattern in weather_patterns
        )

        if not is_weather_request:
            return None

        # Determine requested time period.
        if re.search(
            r"\btomorrow\b",
            message,
            re.IGNORECASE,
        ):
            period = "tomorrow"
        else:
            period = "current"

        # Try to extract location.
        location_patterns = [
            r"\bweather\s+(?:in|at|for)\s+(.+)",
            r"\btemperature\s+(?:in|at|for)\s+(.+)",
            r"\bforecast\s+(?:in|at|for)\s+(.+)",
        ]

        location: str | None = None

        for pattern in location_patterns:
            match = re.search(
                pattern,
                message,
                re.IGNORECASE,
            )

            if match:
                location = match.group(1).strip()
                break

        # Remove time words that are not part of the location.
        if location:
            location = re.sub(
                r"\b(today|tomorrow|tonight|now)\b",
                "",
                location,
                flags=re.IGNORECASE,
            )

            location = location.strip(
                " ?!.,"
            )

        return ToolRequest(
            tool_name="weather",
            arguments={
                "location": location,
                "period": period,
            },
        )

    def _detect_calculator(
        self,
        user_input: str,
    ) -> ToolRequest | None:
        """Detect and structure a basic arithmetic request."""

        message = user_input.lower().strip()

        calculator_phrases = [
            "calculate",
            "what is",
            "how much is",
        ]

        expression: str | None = None

        for phrase in calculator_phrases:
            if message.startswith(phrase):
                expression = message[
                    len(phrase):
                ].strip()
                break

        if expression is None:
            return None

        expression = expression.replace(
            "×",
            "*",
        )

        expression = expression.replace(
            "÷",
            "/",
        )

        expression = re.sub(
            r"\?$",
            "",
            expression,
        ).strip()

        # Only allow arithmetic characters.
        if not re.fullmatch(
            r"[0-9+\-*/().%\s]+",
            expression,
        ):
            return None

        if not expression:
            return None

        return ToolRequest(
            tool_name="calculator",
            arguments={
                "expression": expression,
            },
        )