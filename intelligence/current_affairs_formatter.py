from intelligence.current_affairs import (
    CurrentAffairsBrief,
)


class CurrentAffairsFormatter:
    """Formats a structured current-affairs brief for VYRA."""

    def format(
        self,
        brief: CurrentAffairsBrief,
    ) -> str:
        """Return concise plain-text current affairs."""

        if not brief.sections:
            return (
                "I couldn't find any current developments "
                "worth summarizing right now."
            )

        lines: list[str] = []

        for section in brief.sections:
            lines.append(
                f"{section.name}:"
            )

            for index, story in enumerate(
                section.stories,
                start=1,
            ):
                source = (
                    f" ({story.source})"
                    if story.source
                    else ""
                )

                lines.append(
                    f"{index}. "
                    f"{story.title}"
                    f"{source}"
                )

                if story.summary:
                    lines.append(
                        f"   {story.summary}"
                    )

            lines.append("")

        return "\n".join(
            lines
        ).strip()