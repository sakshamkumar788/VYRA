from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., str]


class ToolRegistry:
    """Stores and executes tools that VYRA is allowed to use."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def execute(
        self,
        name: str,
        **arguments: str,
    ) -> str:
        """Execute a registered tool."""

        tool = self.get(name)

        if tool is None:
            raise ValueError(
                f"Unknown tool: {name}"
            )

        return tool.function(**arguments)