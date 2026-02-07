"""
Resilience tests for endpoints that depend on LLM providers.

These tests ensure the API degrades gracefully (200 + fallback payload)
when DEEPSEEK_API_KEY and OPENROUTER_API_KEY are not configured.
"""

import os
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from agents import llm_client


class LLMResilienceTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _reset_llm_singleton(self):
        llm_client._llm_client = None

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "", "OPENROUTER_API_KEY": ""}, clear=False)
    def test_chat_ask_returns_fallback_message_without_llm_keys(self):
        self._reset_llm_singleton()

        response = self.client.post(
            "/api/chat/ask/",
            data={"message": "hi"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("reply", payload)
        self.assertIn("analysis engine is currently unavailable", payload["reply"].lower())

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "", "OPENROUTER_API_KEY": ""}, clear=False)
    def test_market_brief_returns_snapshot_without_llm_keys(self):
        self._reset_llm_singleton()

        response = self.client.post(
            "/api/market/brief/",
            data={"instruments": ["EUR/USD"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("summary", payload)
        self.assertIn("temporarily unavailable", payload["summary"].lower())
        self.assertIn("instruments", payload)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "", "OPENROUTER_API_KEY": ""}, clear=False)
    def test_market_sentiment_falls_back_to_neutral_without_llm_keys(self):
        self._reset_llm_singleton()

        response = self.client.post(
            "/api/market/sentiment/",
            data={"instrument": "EUR/USD"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("sentiment", payload)
        self.assertEqual(payload["sentiment"], "neutral")
