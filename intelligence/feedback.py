"""
User feedback subsystem for VYRA's intelligence pipeline.

This module is intentionally narrow in scope. It records feedback
signals (like/dislike/etc.) and turns them into small, bounded
preference adjustments per category/entity/source. It does NOT touch
IntelligenceScorer directly - it only produces preference numbers.

Future integration (not implemented here):

    story
    ↓
    base intelligence score  (IntelligenceScorer)
    ↓
    feedback profile         (this module)
    ↓
    personalized adjustment

Feedback is persisted to SQLite (via memory.database) so it survives
restarts, but the *strength* of old feedback decays over time - a
dislike from three months ago should matter less than one from
yesterday. Nothing is ever deleted from SQLite because of decay;
decay only affects the calculated current preference.

No LLM, no internet, no external packages, no PyTorch/TensorFlow, no
embeddings. Just plain Python data structures and a simple exponential
decay formula.
"""

from dataclasses import dataclass, field
from datetime import datetime

from memory.database import (
    get_intelligence_feedback,
    save_intelligence_feedback,
)


class FeedbackType:
    """Supported feedback signals."""

    LIKE = "like"
    DISLIKE = "dislike"
    MORE_LIKE_THIS = "more_like_this"
    LESS_LIKE_THIS = "less_like_this"
    TELL_ME_MORE = "tell_me_more"
    DO_NOT_TELL_ME_THIS = "do_not_tell_me_this"
    DISMISS = "dismiss"

    ALL = {
        LIKE,
        DISLIKE,
        MORE_LIKE_THIS,
        LESS_LIKE_THIS,
        TELL_ME_MORE,
        DO_NOT_TELL_ME_THIS,
        DISMISS,
    }


# Conservative, bounded per-event adjustments. These are the deltas at
# full (undecayed) strength - the running total is what gets clamped.
_FEEDBACK_DELTAS: dict[str, int] = {
    FeedbackType.LIKE: 5,
    FeedbackType.MORE_LIKE_THIS: 10,
    FeedbackType.TELL_ME_MORE: 8,
    FeedbackType.DISLIKE: -5,
    FeedbackType.LESS_LIKE_THIS: -10,
    FeedbackType.DO_NOT_TELL_ME_THIS: -20,
    FeedbackType.DISMISS: -8,
}

_MIN_PREFERENCE = -50
_MAX_PREFERENCE = 50

# Number of days for a feedback event's influence to fall to half its
# original strength. 30 days -> ~50%, 60 days -> ~25%, 90 -> ~12.5%.
PREFERENCE_HALF_LIFE_DAYS = 30


def _clamp(value: int) -> int:
    """Bound a preference score to the allowed range."""

    return max(
        _MIN_PREFERENCE,
        min(_MAX_PREFERENCE, value),
    )


def _normalize(value: str) -> str:
    """Normalize a category/entity/source key for consistent lookup.

    "AI" and "ai" (and surrounding whitespace) must resolve to the
    same preference key.
    """

    return value.strip().lower()


def _parse_timestamp(value: str) -> datetime:
    """Parse a timestamp string as stored/returned by SQLite.

    SQLite's CURRENT_TIMESTAMP produces strings like
    "2026-08-25 10:00:00". datetime.fromisoformat handles that
    directly on modern Python; the strptime fallback exists in case
    an older-format string ever shows up.
    """

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


@dataclass
class FeedbackRecord:
    """A single piece of feedback the user gave about a story."""

    feedback_type: str
    story_category: str | None
    entity_names: tuple[str, ...]
    source: str | None
    created_at: datetime = field(
        default_factory=datetime.now
    )


class FeedbackProfile:
    """Maintains in-memory, bounded, time-decayed preference adjustments.

    This is a first-pass preference model. A single dislike does not
    mean the user hates an entire topic forever - adjustments are
    small, reversible, and fade with age, so repeated or more recent
    opposite feedback can move the score back the other way.
    """

    def __init__(self) -> None:
        self._category_scores: dict[str, int] = {}
        self._entity_scores: dict[str, int] = {}
        self._source_scores: dict[str, int] = {}

        # Full history of feedback this profile knows about, whether
        # recorded live this session or loaded from SQLite. Preference
        # scores are always derived from this list, never mutated
        # directly, so they can be recomputed at any time.
        self.history: list[FeedbackRecord] = []

    # -----------------------------------------------------------
    # Recording new feedback
    # -----------------------------------------------------------

    def record(
        self,
        feedback_type: str,
        story_category: str | None = None,
        entity_names: list[str] | None = None,
        source: str | None = None,
        persist: bool = True,
    ) -> None:
        """Record a feedback event and apply it at full current weight.

        A brand-new event is, by definition, zero days old, so it is
        applied at (essentially) full strength immediately. Unknown
        feedback types are ignored rather than raising, so a
        malformed or future signal can never crash the caller.
        """

        if feedback_type not in FeedbackType.ALL:
            return

        now = datetime.now()

        normalized_entities = tuple(
            _normalize(entity_name)
            for entity_name in (entity_names or [])
            if entity_name and entity_name.strip()
        )

        normalized_category = (
            _normalize(story_category)
            if story_category
            else None
        )

        normalized_source = (
            _normalize(source)
            if source
            else None
        )

        record = FeedbackRecord(
            feedback_type=feedback_type,
            story_category=normalized_category,
            entity_names=normalized_entities,
            source=normalized_source,
            created_at=now,
        )

        self.history.append(record)

        # A freshly created record has ~zero age relative to `now`,
        # so this applies (essentially) the full, undecayed delta.
        self._apply_record(record, now)

        if persist:
            save_intelligence_feedback(
                feedback_type=feedback_type,
                story_category=normalized_category,
                entity_names=normalized_entities,
                source=normalized_source,
            )

    # -----------------------------------------------------------
    # Loading persisted feedback
    # -----------------------------------------------------------

    def load_persistent_feedback(self) -> None:
        """Load stored feedback from SQLite and rebuild preferences.

        Each stored record contributes an age-weighted adjustment
        based on its original `created_at` timestamp, rather than
        being replayed at full strength.
        """

        rows = get_intelligence_feedback()

        for (
            _feedback_id,
            feedback_type,
            story_category,
            entity_names,
            source,
            created_at,
        ) in rows:

            if feedback_type not in FeedbackType.ALL:
                continue

            names: tuple[str, ...] = ()

            if entity_names:
                names = tuple(
                    _normalize(name)
                    for name in entity_names.split(",")
                    if name.strip()
                )

            created_at_value = (
                _parse_timestamp(created_at)
                if isinstance(created_at, str)
                else created_at
            )

            self.history.append(
                FeedbackRecord(
                    feedback_type=feedback_type,
                    story_category=(
                        _normalize(story_category)
                        if story_category
                        else None
                    ),
                    entity_names=names,
                    source=(
                        _normalize(source)
                        if source
                        else None
                    ),
                    created_at=created_at_value,
                )
            )

        self.rebuild_preferences()

    # -----------------------------------------------------------
    # Rebuilding / decay
    # -----------------------------------------------------------

    def rebuild_preferences(
        self,
        now: datetime | None = None,
    ) -> None:
        """Recompute all preference scores from `history`, with decay.

        This clears the current category/entity/source scores and
        reapplies every historical record, weighted by how old it is
        relative to `now`. Nothing in SQLite or `history` is deleted;
        this only changes the calculated current preference.
        """

        reference_time = now or datetime.now()

        self._category_scores = {}
        self._entity_scores = {}
        self._source_scores = {}

        for record in self.history:
            self._apply_record(record, reference_time)

    def _decay_factor(
        self,
        created_at: datetime,
        now: datetime,
    ) -> float:
        """Return how much strength a feedback event still has.

        Exponential decay with a configurable half-life:

            age = 0 days   -> 1.0
            age = 30 days  -> 0.5
            age = 60 days  -> 0.25
            age = 90 days  -> 0.125

        Timestamps in the future (e.g. clock skew) are treated as
        age zero rather than producing a factor above 1.0.
        """

        age_days = (
            now - created_at
        ).total_seconds() / 86400

        if age_days < 0:
            age_days = 0.0

        return 0.5 ** (
            age_days / PREFERENCE_HALF_LIFE_DAYS
        )

    def _apply_record(
        self,
        record: FeedbackRecord,
        now: datetime,
    ) -> None:
        """Apply one age-weighted feedback record to the score maps."""

        base_delta = _FEEDBACK_DELTAS.get(
            record.feedback_type
        )

        if base_delta is None:
            # Defensive: history should never contain an unknown
            # feedback type, but never let a bad row crash a rebuild.
            return

        factor = self._decay_factor(
            record.created_at,
            now,
        )

        weighted_delta = round(base_delta * factor)

        if record.story_category:
            self._adjust(
                self._category_scores,
                record.story_category,
                weighted_delta,
            )

        for entity_key in record.entity_names:
            self._adjust(
                self._entity_scores,
                entity_key,
                weighted_delta,
            )

        if record.source:
            self._adjust(
                self._source_scores,
                record.source,
                weighted_delta,
            )

    def _adjust(
        self,
        scores: dict[str, int],
        key: str,
        delta: int,
    ) -> None:
        """Apply a bounded delta to one preference key."""

        current = scores.get(key, 0)
        scores[key] = _clamp(current + delta)

    # -----------------------------------------------------------
    # Reading current preferences
    # -----------------------------------------------------------

    def category_bonus(self, category: str) -> int:
        """Return the current preference adjustment for a category."""

        return self._category_scores.get(
            _normalize(category),
            0,
        )

    def entity_bonus(self, entity_name: str) -> int:
        """Return the current preference adjustment for an entity."""

        return self._entity_scores.get(
            _normalize(entity_name),
            0,
        )

    def source_bonus(self, source: str) -> int:
        """Return the current preference adjustment for a source."""

        return self._source_scores.get(
            _normalize(source),
            0,
        )
