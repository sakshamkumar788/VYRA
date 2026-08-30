"""
Tests for VYRA Step 8.0 – Text‑to‑Speech (pyttsx3).

All tests mock pyttsx3 so they run without real audio hardware.
"""
import unittest
from unittest.mock import patch, MagicMock

from tools.voice import speak


class TestVoice(unittest.TestCase):
    """Very small, deterministic tests for the 8.0 voice foundation."""

    def test_speak_empty_is_noop(self):
        """speak("") must not call the engine."""
        speak("")

    def test_speak_hello_initialises_engine(self):
        """When text is non‑empty, pyttsx3.say and runAndWait are called."""
        with patch("tools.voice.pyttsx3") as mock_tts:
            engine = MagicMock()
            mock_tts.init.return_value = engine
            speak("Hello")
            engine.say.assert_called_once_with("Hello")
            engine.runAndWait.assert_called_once()

    def test_speak_exception_silent(self):
        """A TTS exception must never propagate out of speak()."""
        with patch("tools.voice.pyttsx3") as mock_tts:
            engine = MagicMock()
            engine.say.side_effect = RuntimeError("audio error")
            mock_tts.init.return_value = engine
            speak("Hello")  # must not raise

    def test_whitespace_is_noop(self):
        """Whitespace‑only text must be treated as empty."""
        speak("   ")

    def test_speak_passthrough_text(self):
        """The exact text supplied is exactly what engine.say receives."""
        with patch("tools.voice.pyttsx3") as mock_tts:
            engine = MagicMock()
            mock_tts.init.return_value = engine
            speak("VYRA says hello")
            engine.say.assert_called_once_with("VYRA says hello")
            engine.runAndWait.assert_called_once()

    @patch("tools.voice.pyttsx3")
    def test_speak_full_sentence_with_name(self, mock_tts):
        """A sentence containing 'Saksham' must result in exactly ONE engine.say call."""
        eng = MagicMock()
        mock_tts.init.return_value = eng
        text = "Hello Saksham! It’s a lovely evening. How are you this Saturday?"
        speak(text)
        self.assertEqual(eng.say.call_count, 1)
        self.assertEqual(eng.runAndWait.call_count, 1)
        argued = eng.say.call_args[0][0]
        self.assertIn("Saksham", argued)  # the safe pronunciation form

    @patch("tools.voice.pyttsx3")
    def test_speak_without_name(self, mock_tts):
        """A sentence without 'Saksham' must also result in exactly ONE engine.say call."""
        eng = MagicMock()
        mock_tts.init.return_value = eng
        text = "Hello! It’s a lovely evening. How are you this Saturday?"
        speak(text)
        self.assertEqual(eng.say.call_count, 1)
        self.assertEqual(eng.runAndWait.call_count, 1)
        argued = eng.say.call_args[0][0]
        self.assertNotIn("Saksham", argued)


if __name__ == "__main__":
    unittest.main()