from dataclasses import dataclass
import re

from intelligence.feedback import FeedbackProfile, FeedbackType


@dataclass
class UserPreferenceCommand:
    feedback_type: str
    category: str | None = None
    entity: str | None = None
    source: str | None = None


# Small deterministic vocabularies
CATEGORIES = {
    "ai",
    "artificial intelligence",
    "sports",
    "startup",
    "business",
    "company",
    "technology",
    "research",
    "news",
}

ENTITIES = {
    "nvidia",
    "openai",
    "gemma",
    "tesla",
}

SOURCES = {
    "reuters",
    "bbc",
    "pib india",
    "indian express",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _clean_target(target: str) -> str:
    target = _normalize_text(target)
    # Remove trailing 'news'
    target = re.sub(r"\s+news$", "", target)
    return target.strip()


def _map_target(feedback_type: str, target: str, prefer_entity: bool = False) -> UserPreferenceCommand | None:
    target = _clean_target(target)
    if not target:
        return None

    # Source check first
    if target in SOURCES:
        return UserPreferenceCommand(feedback_type=feedback_type, source=target)

    # Entity check
    if target in ENTITIES or prefer_entity:
        # If prefer_entity, still verify it's a known entity for safety
        if target in ENTITIES:
            return UserPreferenceCommand(feedback_type=feedback_type, entity=target)
        # Fallback to category if not known entity
        if target in CATEGORIES:
            return UserPreferenceCommand(feedback_type=feedback_type, category=target)

    # Category check
    if target in CATEGORIES:
        return UserPreferenceCommand(feedback_type=feedback_type, category=target)

    # Unknown target -> no command
    return None


class UserPreferenceParser:
    def parse(self, text: str) -> UserPreferenceCommand | None:
        if not text or not text.strip():
            return None

        lower = _normalize_text(text)

        # More from source
        m = re.match(r"^(more|show me more)\s+from\s+(.+)$", lower)
        if m:
            source = _clean_target(m.group(2))
            if source in SOURCES:
                return UserPreferenceCommand(feedback_type=FeedbackType.MORE_LIKE_THIS, source=source)
            return None

        # Less from source
        m = re.match(r"^(less|show me less)\s+from\s+(.+)$", lower)
        if m:
            source = _clean_target(m.group(2))
            if source in SOURCES:
                return UserPreferenceCommand(feedback_type=FeedbackType.LESS_LIKE_THIS, source=source)
            return None

        # Suppress from source
        m = re.match(r"^(don't tell me|don't show me|stop showing me)\s+from\s+(.+)$", lower)
        if m:
            source = _clean_target(m.group(2))
            if source in SOURCES:
                return UserPreferenceCommand(feedback_type=FeedbackType.DO_NOT_TELL_ME_THIS, source=source)
            return None

        # Tell me more about
        m = re.match(r"^tell me more about\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.TELL_ME_MORE, m.group(1))

        # More/less/don't about entity
        m = re.match(r"^(more|show me more)\s+about\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.MORE_LIKE_THIS, m.group(2), prefer_entity=True)

        m = re.match(r"^(less|show me less)\s+about\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.LESS_LIKE_THIS, m.group(2), prefer_entity=True)

        m = re.match(r"^(don't tell me|don't show me|stop showing me)\s+about\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.DO_NOT_TELL_ME_THIS, m.group(2), prefer_entity=True)

        # Simple more/less/don't commands
        m = re.match(r"^(more|show me more)\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.MORE_LIKE_THIS, m.group(2))

        m = re.match(r"^(less|show me less)\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.LESS_LIKE_THIS, m.group(2))

        m = re.match(r"^(don't tell me|don't show me|stop showing me)\s+(.+)$", lower)
        if m:
            return _map_target(FeedbackType.DO_NOT_TELL_ME_THIS, m.group(2))

        return None


class UserPreferenceManager:
    def __init__(self, profile: FeedbackProfile) -> None:
        self.profile = profile

    def apply(self, command: UserPreferenceCommand) -> None:
        if command is None:
            return

        kwargs = {}
        if command.category:
            kwargs["story_category"] = command.category
        if command.entity:
            kwargs["entity_names"] = [command.entity]
        if command.source:
            kwargs["source"] = command.source

        self.profile.record(
            feedback_type=command.feedback_type,
            persist=True,
            **kwargs,
        )
