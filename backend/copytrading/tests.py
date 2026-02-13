from unittest.mock import patch

from django.test import SimpleTestCase

from copytrading.tools import DEMO_TRADERS, get_top_traders


class CopyTradingToolsSchemaTests(SimpleTestCase):
    @patch("copytrading.tools.DerivCopyTradingClient")
    def test_get_top_traders_fallback_uses_consistent_schema(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_copytrading_list.return_value = {"error": "auth failed"}

        result = get_top_traders(limit=2)

        self.assertEqual(result["source"], "demo_fallback")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["total_count"], len(DEMO_TRADERS))
        self.assertEqual(len(result["traders"]), 2)

        trader = result["traders"][0]
        for key in [
            "loginid",
            "token",
            "avg_profit",
            "total_trades",
            "copiers",
            "performance_probability",
            "min_trade_stake",
            "trade_types",
            "balance",
            "currency",
            "win_rate",
            "avg_loss",
            "active_since",
            "_demo",
        ]:
            self.assertIn(key, trader)

    @patch("copytrading.tools.DerivCopyTradingClient")
    def test_get_top_traders_stats_error_still_returns_required_fields(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_copytrading_list.return_value = {
            "traders": [
                {
                    "loginid": "CR12345",
                    "token": "tok_123",
                    "balance": 1000.0,
                    "currency": "USD",
                }
            ]
        }
        mock_client.get_copytrading_statistics.return_value = {"error": "stats unavailable"}

        result = get_top_traders(limit=10)

        self.assertEqual(result["source"], "deriv_api")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total_count"], 1)

        trader = result["traders"][0]
        self.assertEqual(trader["loginid"], "CR12345")
        self.assertEqual(trader["avg_profit"], 0.0)
        self.assertEqual(trader["total_trades"], 0)
        self.assertEqual(trader["copiers"], 0)
        self.assertEqual(trader["performance_probability"], 0.0)
        self.assertEqual(trader["win_rate"], 0.0)
        self.assertEqual(trader["avg_loss"], 0.0)
