from dataclasses import dataclass, field
from datetime import datetime


class StoryCategory:
    LOCAL = "local"
    INDIA = "india"
    INDIAN_TECH = "indian_tech"
    AI = "ai"
    RESEARCH = "research"
    BUSINESS = "business"
    COMPANY = "company"
    SCIENCE = "science"
    WORLD = "world"
    FUN = "fun"
    OTHER = "other"


class StoryUrgency:
    IMMEDIATE = "immediate"
    SOON = "soon"
    NORMAL = "normal"
    ON_DEMAND = "on_demand"


class SourceTrust:
    OFFICIAL = 100
    HIGH = 85
    REPUTABLE = 75
    COMMUNITY = 55
    UNKNOWN = 30


@dataclass
class IntelligenceStory:
    """A normalized piece of information VYRA may consider surfacing."""

    title: str
    summary: str

    source: str | None = None
    url: str | None = None

    category: str = StoryCategory.OTHER

    published_at: datetime | None = None

    location_name: str | None = None

    severity: int = 0
    importance: int = 0
    confidence: int = 50
    personal_relevance: int = 0
    novelty: int = 50

    source_trust: int = SourceTrust.UNKNOWN

    urgency: str = StoryUrgency.NORMAL

    entities: list = field(
        default_factory=list
    )