from intelligence.models import (
    IntelligenceStory,
)
from intelligence.priority import (
    IntelligencePriority,
)
from intelligence.queue import (
    IntelligenceQueue,
)


def main() -> None:
    queue = IntelligenceQueue()

    important = IntelligenceStory(
        title="Major India development",
        summary="Important development.",
        url="https://example.com/india",
    )

    interesting = IntelligenceStory(
        title="Interesting AI research",
        summary="Interesting research.",
        url="https://example.com/ai",
    )

    ignored = IntelligenceStory(
        title="Unimportant story",
        summary="Ignore this.",
    )

    queue.add(
        important,
        IntelligencePriority.IMPORTANT,
    )

    queue.add(
        interesting,
        IntelligencePriority.INTERESTING,
    )

    queue.add(
        ignored,
        IntelligencePriority.IGNORE,
    )

    print("Queue length:", len(queue))

    assert len(queue) == 2

    pending = queue.get_pending()

    print()

    for item in pending:
        print(
            item.priority,
            "|",
            item.story.title,
        )

    assert (
        pending[0].priority
        == IntelligencePriority.IMPORTANT
    )

    assert (
        pending[1].priority
        == IntelligencePriority.INTERESTING
    )

    # ---------------------------------------------------------
    # Duplicate protection
    # ---------------------------------------------------------

    queue.add(
        important,
        IntelligencePriority.IMPORTANT,
    )

    assert len(queue) == 2

    # ---------------------------------------------------------
    # Remove
    # ---------------------------------------------------------

    queue.remove(important)

    assert len(queue) == 1

    assert (
        queue.get_pending()[0].story.title
        == "Interesting AI research"
    )

    print()
    print("All intelligence queue tests passed.")


if __name__ == "__main__":
    main()