"""Unit tests for tools.input_provider."""

import unittest
from unittest.mock import patch

from tools.input_provider import ConsoleInputProvider, get_default_provider


class TestInputProvider(unittest.TestCase):
    def test_console_provider_returns_input(self):
        provider = ConsoleInputProvider()
        with patch("builtins.input", return_value="hello"):
            result = provider.get_text("You: ")
            self.assertEqual(result, "hello")

    def test_prompt_passed_unchanged(self):
        provider = ConsoleInputProvider()
        with patch("builtins.input", return_value="test") as mock_input:
            provider.get_text("Prompt: ")
            mock_input.assert_called_once_with("Prompt: ")

    def test_multiple_calls_behave_normally(self):
        provider = ConsoleInputProvider()
        with patch("builtins.input", side_effect=["first", "second"]):
            self.assertEqual(provider.get_text("P: "), "first")
            self.assertEqual(provider.get_text("P: "), "second")

    def test_get_default_provider_returns_console(self):
        provider = get_default_provider()
        self.assertIsInstance(provider, ConsoleInputProvider)

    def test_empty_input_returned_unchanged(self):
        provider = ConsoleInputProvider()
        with patch("builtins.input", return_value=""):
            self.assertEqual(provider.get_text("> "), "")

    def test_whitespace_input_returned_unchanged(self):
        provider = ConsoleInputProvider()
        with patch("builtins.input", return_value="   "):
            self.assertEqual(provider.get_text("> "), "   ")


if __name__ == "__main__":
    unittest.main()
