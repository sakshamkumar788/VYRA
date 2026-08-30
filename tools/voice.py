import re
import pyttsx3

# Pronunciation overrides for words the TTS engine mispronounces.
# This is plain data — add/remove entries here without touching speak().
# Each value replaces the key ONCE, entirely (not appended alongside it),
# so the spoken text never contains the original word twice.
_PRONUNCIATION_OVERRIDES = {
    "Saksham": "Suck-shum",
}


def _apply_pronunciation_overrides(text: str) -> str:
    """Return a TTS-friendly version of *text* using _PRONUNCIATION_OVERRIDES.

    Only affects what is spoken — the visible/printed text is never touched.
    """
    spoken = text
    for original, override in _PRONUNCIATION_OVERRIDES.items():
        if original in spoken:
            spoken = spoken.replace(original, override, 1)
    return spoken


def _clean_for_speech(text: str) -> str:
    """Strip markdown/formatting artifacts before speaking.

    Only removes structural formatting symbols (bold/italic markers,
    headers, code ticks, bullet/number list markers at the start of a
    line). Never touches numbers or words that are part of the actual
    sentence content.
    """
    cleaned = text

    # Bold/italic markers: **text** / *text* / __text__ / _text_
    # Keep the inner text, drop the symbols.
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.+?)\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.+?)__", r"\1", cleaned)
    cleaned = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", cleaned)

    # Inline code / code fences
    cleaned = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", cleaned)

    # Markdown headers: "# Heading" -> "Heading"
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s+", "", cleaned, flags=re.MULTILINE)

    # Bullet list markers at start of line: "- ", "* ", "+ "
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)

    # Numbered list markers at start of line: "1. ", "2) " etc.
    # Only matches when the number is immediately followed by '.' or ')'
    # at the START of a line — never touches numbers inside a sentence.
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned, flags=re.MULTILINE)

    # Collapse leftover extra whitespace/newlines from stripped lines.
    cleaned = re.sub(r"\n{2,}", ". ", cleaned)
    cleaned = re.sub(r"\n", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    return cleaned


def speak(text: str) -> None:
    """Speak *text* using pyttsx3.

    * No‑op if *text* is empty or whitespace only.
    * A fresh pyttsx3 engine is created for every call (no reuse).
    * The Microsoft Zira voice is selected if it is available on the system.
    * Markdown/formatting symbols and pronunciation overrides are applied
      before speaking; the visible/printed text passed in by the caller
      is never modified — only the spoken copy.
    * Exactly one engine.say() call is made per invocation.
    * Any TTS exception is silently swallowed so VYRA never crashes.
    """
    if not text or not text.strip():
        return

    spoken = _clean_for_speech(text)
    spoken = _apply_pronunciation_overrides(spoken)

    if not spoken:
        return

    # Create a fresh engine for this call – no reuse across calls.
    engine = None
    try:
        engine = pyttsx3.init()

        # Try to select the Microsoft Zira voice if it exists on the system.
        try:
            voices = engine.getProperty("voices")
            zira_voice = None
            for v in voices:
                name = (v.name or "").lower()
                vid = (v.id or "").lower()
                if "zira" in name or "zira" in vid:
                    zira_voice = v
                    break
            if zira_voice is not None:
                engine.setProperty("voice", zira_voice.id)
        except Exception:
            pass

        try:
            engine.say(spoken)
            engine.runAndWait()
        except Exception:
            pass
    finally:
        try:
            if engine is not None:
                engine.stop()
        except Exception:
            pass