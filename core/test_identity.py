"""Tests for assistant identity handling."""

import unittest
from unittest.mock import patch

from core.vyra import VYRA


class TestIdentity(unittest.TestCase):
    def setUp(self):
        # Use __new__ to avoid full init
        self.vyra = VYRA.__new__(VYRA)
        # Provide minimal attributes needed by handle_identity_query
        self.vyra.input_provider = None
        # Mock speak_user_response to avoid TTS
        self.vyra.speak_user_response = lambda text: None

    def test_assistant_identity_queries(self):
        queries = [
            "what is your name",
            "what's your name",
            "who are you",
            "what should I call you",
            "what do I call you",
            "who am I talking to",
            "are you vyra",
            "is your name vyra",
        ]
        for q in queries:
            with self.subTest(q=q):
                handled = self.vyra.handle_identity_query(q)
                self.assertTrue(handled, f"Identity query not handled: {q}")

    def test_user_identity_not_intercepted(self):
        queries = [
            "what is my name",
            "where do I live",
            "where am I",
        ]
        for q in queries:
            with self.subTest(q=q):
                handled = self.vyra.handle_identity_query(q)
                self.assertFalse(handled, f"User query incorrectly intercepted: {q}")

    @patch('memory.database.get_relevant_memories')
    def test_user_identity_queries_handled(self, mock_memories):
        mock_memories.return_value = [('user_note', 'My name is Saksham.')]
        queries = [
            "what is my name",
            "what's my name",
            "who am i",
            "tell me my name",
            "what do you call me",
            "what name do you call me",
            "what is the name you call me with",
        ]
        for q in queries:
            with self.subTest(q=q):
                handled = self.vyra.handle_user_identity_query(q)
                self.assertTrue(handled, f"User identity query not handled: {q}")
                # Verify memory was queried
                self.assertTrue(mock_memories.called)

    @patch('memory.database.get_relevant_memories')
    def test_assistant_not_intercepted_by_user_handler(self, mock_memories):
        mock_memories.return_value = [('user_note', 'My name is Saksham.')]
        queries = [
            "what is your name",
            "who are you",
            "what do I call you",
            "what should I call you",
        ]
        for q in queries:
            with self.subTest(q=q):
                handled = self.vyra.handle_user_identity_query(q)
                self.assertFalse(handled, f"Assistant query incorrectly intercepted: {q}")


if __name__ == "__main__":
    unittest.main()
