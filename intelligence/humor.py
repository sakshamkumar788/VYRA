"""
Rule-based, deterministic humor/joke subsystem for VYRA.

This module intentionally does NOT call an LLM and does NOT access the
internet. It selects short, context-aware, template-based lines from a
fixed local pool. This keeps humor generation offline, fast, testable,
and free of unpredictable model output.

Design overview:
    context (free text) -> topic detection (keyword match)
    style + topic        -> template pool
    per-instance cursor   -> deterministic, non-repeating selection

Limitations (see docstring at bottom of file / VYRA_STATE.md entry):
    - Humor is template-based, not generative. It cannot understand
      nuance, timing, or truly novel situations the way an LLM could.
    - Topic detection is keyword-based and can miss/mis-detect context.
    - The pool of jokes is finite; long-running sessions will eventually
      cycle back through previously used lines.
    - This module never claims VYRA has experienced anything. It should
      not be extended to fabricate personal anecdotes or real events.
"""

from dataclasses import dataclass


class HumorStyle:
    """Supported humor styles."""

    LIGHT = "light"
    PLAYFUL = "playful"
    TECH = "tech"
    OBSERVATIONAL = "observational"
    SELF_AWARE = "self_aware"

    ALL = {
        LIGHT,
        PLAYFUL,
        TECH,
        OBSERVATIONAL,
        SELF_AWARE,
    }


class HumorTopic:
    """Internal topic buckets used to select a template pool."""

    CODING = "coding"
    DEBUGGING = "debugging"
    COMPILING = "compiling"
    STUDYING = "studying"
    LATE_NIGHT = "late_night"
    WEATHER = "weather"
    SELF = "self"
    LANGUAGE = "language"
    GENERIC = "generic"


@dataclass
class HumorCandidate:
    """A single generated humor line."""

    text: str
    style: str
    confidence: int = 70


# ---------------------------------------------------------------------
# Topic detection
# ---------------------------------------------------------------------

_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    HumorTopic.DEBUGGING: (
        "debug",
        "bug",
        "error",
        "traceback",
        "exception",
        "crash",
        "stack trace",
    ),
    HumorTopic.COMPILING: (
        "compil",
        "build",
        "building",
    ),
    HumorTopic.CODING: (
        "coding",
        "code",
        "programming",
        "function",
        "script",
        "refactor",
    ),
    HumorTopic.STUDYING: (
        "study",
        "studying",
        "exam",
        "revision",
        "revising",
        "homework",
        "notes",
    ),
    HumorTopic.LATE_NIGHT: (
        "late night",
        "midnight",
        "2 am",
        "2am",
        "3 am",
        "3am",
        "can't sleep",
        "cant sleep",
        "still awake",
    ),
    HumorTopic.WEATHER: (
        "weather",
        "rain",
        "rainy",
        "hot",
        "cold",
        "humid",
        "sunny",
        "storm",
    ),
    HumorTopic.SELF: (
        "vyra",
        "yourself",
        "you are",
        "you're an ai",
        "are you real",
    ),
    HumorTopic.LANGUAGE: (
        "python",
        "c++",
        "cpp",
        "dsa",
        "java",
        "javascript",
    ),
}


def _detect_topic(context: str) -> str:
    """Detect a topic bucket from free-text context via keyword match."""

    if not context:
        return HumorTopic.GENERIC

    normalized = context.strip().lower()

    # Check topics in a fixed, deliberate order so overlapping keywords
    # (e.g. "python" appearing inside a "debugging python" context)
    # resolve predictably.
    ordered_topics = (
        HumorTopic.DEBUGGING,
        HumorTopic.COMPILING,
        HumorTopic.LATE_NIGHT,
        HumorTopic.WEATHER,
        HumorTopic.SELF,
        HumorTopic.STUDYING,
        HumorTopic.LANGUAGE,
        HumorTopic.CODING,
    )

    for topic in ordered_topics:
        keywords = _TOPIC_KEYWORDS[topic]

        if any(keyword in normalized for keyword in keywords):
            return topic

    return HumorTopic.GENERIC


# ---------------------------------------------------------------------
# Template pools: style -> topic -> list of lines
# ---------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, list[str]]] = {
    HumorStyle.LIGHT: {
        HumorTopic.CODING: [
            "Every line you write is one step closer to a working program. Mostly.",
            "Coding: turning coffee into slightly fewer bugs.",
        ],
        HumorTopic.DEBUGGING: [
            "Somewhere out there, one missing bracket is having a great laugh at your expense.",
            "The bug is real. Its motives remain unknown.",
        ],
        HumorTopic.COMPILING: [
            "The build is thinking. Give it a moment to make good choices.",
            "Compiling: the universe's way of making you stretch your legs.",
        ],
        HumorTopic.STUDYING: [
            "Future you will thank present you for these notes. Probably.",
            "One more page, then a break. That's the deal.",
        ],
        HumorTopic.LATE_NIGHT: [
            "It's late. Even your keyboard is starting to yawn.",
            "This is either dedication or a scheduling problem. Could be both.",
        ],
        HumorTopic.WEATHER: [
            "The weather has opinions today, and it's not keeping them to itself.",
        ],
        HumorTopic.SELF: [
            "I run on logic, curiosity, and mild sass.",
        ],
        HumorTopic.LANGUAGE: [
            "Every language has its quirks. This one just hides them better.",
        ],
        HumorTopic.GENERIC: [
            "Small win: you showed up today. That counts.",
            "Progress doesn't always look like progress while it's happening.",
        ],
    },
    HumorStyle.PLAYFUL: {
        HumorTopic.CODING: [
            "Your code and I have a great relationship. It ignores me, I judge it silently.",
            "Another function born into the world. Let's see if it survives contact with reality.",
        ],
        HumorTopic.DEBUGGING: [
            "Ah yes, the classic 'it worked five minutes ago' mystery.",
            "The bug isn't hiding. You're just not looking hard enough. Yet.",
        ],
        HumorTopic.COMPILING: [
            "The compiler is judging every decision you've made today. Slowly.",
            "Somewhere, a progress bar is lying to you about how close it is.",
        ],
        HumorTopic.STUDYING: [
            "Studying: the art of pretending you'll remember this in a week.",
            "Your notes are basically a love letter to future exam-you.",
        ],
        HumorTopic.LATE_NIGHT: [
            "It's officially 'why am I still awake' o'clock.",
            "Your sleep schedule filed a formal complaint an hour ago.",
        ],
        HumorTopic.WEATHER: [
            "The sky is doing its own thing today, no notes taken from anyone.",
        ],
        HumorTopic.SELF: [
            "I'd say I have a personality, but I'm biased since I wrote it myself.",
        ],
        HumorTopic.LANGUAGE: [
            "Every language promises it's the easy one. None of them are.",
        ],
        HumorTopic.GENERIC: [
            "I'd offer a drumroll, but I don't have hands.",
            "This is the part where I pretend I planned that joke in advance.",
        ],
    },
    HumorStyle.TECH: {
        HumorTopic.CODING: [
            "Technically your code compiles. Technically a rock can float, if thrown hard enough.",
            "It's not spaghetti code, it's a 'distributed logic structure.'",
        ],
        HumorTopic.DEBUGGING: [
            "99 little bugs in the code, 99 little bugs. Take one down, patch it around, 127 little bugs in the code.",
            "It's not a bug, it's an undocumented feature discovery process.",
        ],
        HumorTopic.COMPILING: [
            "Compilation status: pending existential review.",
            "The linker and I are currently not on speaking terms.",
        ],
        HumorTopic.LANGUAGE: [
            "Python: readable until you meet someone else's decorators.",
            "C++ gives you complete freedom, including the freedom to regret it.",
        ],
        HumorTopic.SELF: [
            "I'm a language model wrapped in a personality, running on someone else's electricity bill.",
        ],
        HumorTopic.GENERIC: [
            "Somewhere, a server is quietly doing exactly what you asked, no more, no less.",
        ],
    },
    HumorStyle.OBSERVATIONAL: {
        HumorTopic.CODING: [
            "Funny how a missing semicolon can feel more personal than it should.",
            "It's strange how confident code looks right before it fails spectacularly.",
        ],
        HumorTopic.STUDYING: [
            "Isn't it odd how the syllabus always looks shorter than it turns out to be.",
        ],
        HumorTopic.LATE_NIGHT: [
            "There's a specific kind of quiet that only exists after midnight.",
            "Everything feels more solvable at 2 AM and less solvable at 9 AM.",
        ],
        HumorTopic.WEATHER: [
            "Weather never asks for anyone's schedule before showing up.",
        ],
        HumorTopic.SELF: [
            "It's a little strange, talking to something that only exists when you're talking to it.",
        ],
        HumorTopic.GENERIC: [
            "Funny how 'just five more minutes' rarely means five minutes.",
        ],
    },
    HumorStyle.SELF_AWARE: {
        HumorTopic.SELF: [
            "I don't have feelings the way you do, but I'm genuinely good at pretending convincingly.",
            "I can't experience a long day. I can, however, simulate mild concern about yours.",
        ],
        HumorTopic.DEBUGGING: [
            "I'd offer to feel your pain, but I only have opinions, not a nervous system.",
        ],
        HumorTopic.CODING: [
            "I appreciate irony: an AI helping debug the kind of code that could one day replace me.",
        ],
        HumorTopic.GENERIC: [
            "For the record, I know I'm software. I just choose to have a sense of humor about it.",
        ],
    },
}


class HumorEngine:
    """Generates short, deterministic, context-aware humor lines."""

    def __init__(
        self,
        templates: dict[str, dict[str, list[str]]] | None = None,
    ) -> None:
        self._templates = templates if templates is not None else _TEMPLATES

        # Tracks how far we've cycled through each (style, topic) pool,
        # so repeated calls with the same style/topic don't immediately
        # repeat the same line.
        self._cursor: dict[tuple[str, str], int] = {}

        # Tracks every line already returned by this instance, so exact
        # duplicates are avoided until every candidate line has been used.
        self._seen: set[str] = set()

    def generate(
        self,
        context: str,
        style: str = HumorStyle.PLAYFUL,
    ) -> HumorCandidate | None:
        """Generate a humor candidate for the given context/style.

        Returns None if no suitable line is available.
        """

        resolved_style = self._resolve_style(style)

        if resolved_style is None:
            return None

        topic = _detect_topic(context)

        pool = self._get_pool(resolved_style, topic)

        if not pool:
            return None

        text = self._select(resolved_style, topic, pool)

        if text is None:
            return None

        return HumorCandidate(
            text=text,
            style=resolved_style,
            confidence=self._confidence_for(resolved_style, topic),
        )

    def reset(self) -> None:
        """Clear all dedup/cursor state, allowing lines to repeat again."""

        self._cursor.clear()
        self._seen.clear()

    def _resolve_style(self, style: str) -> str | None:
        """Validate the requested style, falling back to 'playful'."""

        if style in HumorStyle.ALL:
            return style

        if HumorStyle.PLAYFUL in HumorStyle.ALL:
            return HumorStyle.PLAYFUL

        return None

    def _get_pool(self, style: str, topic: str) -> list[str]:
        """Return the template pool for a style/topic, falling back to generic."""

        style_templates = self._templates.get(style, {})

        pool = style_templates.get(topic)

        if pool:
            return pool

        return style_templates.get(HumorTopic.GENERIC, [])

    def _select(
        self,
        style: str,
        topic: str,
        pool: list[str],
    ) -> str | None:
        """Deterministically select the next unused line from the pool."""

        key = (style, topic)
        start = self._cursor.get(key, 0) % len(pool)

        # Walk the pool starting at the cursor, looking for a line not
        # yet used by this instance.
        for offset in range(len(pool)):
            index = (start + offset) % len(pool)
            candidate = pool[index]

            if candidate not in self._seen:
                self._cursor[key] = (index + 1) % len(pool)
                self._seen.add(candidate)
                return candidate

        # Every line in this pool has already been used by this
        # instance. Reset just this pool's usage so humor doesn't
        # dead-end permanently during a long-lived session.
        for text in pool:
            self._seen.discard(text)

        index = start
        candidate = pool[index]
        self._cursor[key] = (index + 1) % len(pool)
        self._seen.add(candidate)
        return candidate

    def _confidence_for(self, style: str, topic: str) -> int:
        """Return a simple confidence score for a style/topic match."""

        style_templates = self._templates.get(style, {})

        if topic in style_templates and style_templates[topic]:
            return 80

        return 55


# ---------------------------------------------------------------------
# Humor policy guardrails
# ---------------------------------------------------------------------

from datetime import datetime, timedelta
from context.context import SessionState


class HumorPolicy:
    """In-memory humor eligibility guardrails."""

    HUMOR_COOLDOWN_MINUTES = 120
    MAX_HUMOR_INTERACTIONS_PER_DAY = 3

    def __init__(self) -> None:
        self.last_delivered_at: datetime | None = None
        self.daily_count: int = 0
        self.daily_date: str | None = None

    def reset_daily_count_if_needed(self, now: datetime) -> None:
        """Reset daily count when a new calendar day begins."""
        today = now.date().isoformat()
        if self.daily_date != today:
            self.daily_date = today
            self.daily_count = 0

    def can_surface(self, now: datetime, context) -> bool:
        """Return True if humor is currently eligible to surface."""
        if not getattr(context, "proactive_enabled", True):
            return False

        if getattr(context, "user_busy", False):
            return False

        session_state = getattr(context, "session_state", None)
        if session_state in {
            SessionState.STARTING,
            SessionState.ENDING,
            SessionState.AWAY,
        }:
            return False

        # Daily limit check without mutating state
        today = now.date().isoformat()
        effective_count = self.daily_count if self.daily_date == today else 0
        if effective_count >= self.MAX_HUMOR_INTERACTIONS_PER_DAY:
            return False

        # Cooldown check
        if self.last_delivered_at is not None:
            elapsed = now - self.last_delivered_at
            if elapsed < timedelta(minutes=self.HUMOR_COOLDOWN_MINUTES):
                return False

        return True

    def record_delivery(self, now: datetime) -> None:
        """Record an actual humor delivery."""
        self.reset_daily_count_if_needed(now)
        self.daily_count += 1
        self.last_delivered_at = now
        self.daily_date = now.date().isoformat()
