"""Tests for compliance module."""
from django.test import TestCase
from agents.compliance import (
    check_compliance,
    check_copytrading_compliance,
    check_demo_trading_compliance,
    append_disclaimer,
    sanitize_token,
)


class ComplianceBlocklistTest(TestCase):
    def test_clean_text_passes(self):
        passed, violations = check_compliance("EUR/USD moved 1.2% today due to CPI data.")
        self.assertTrue(passed)
        self.assertEqual(violations, [])

    def test_guaranteed_blocked(self):
        passed, violations = check_compliance("This is a guaranteed profit strategy.")
        self.assertFalse(passed)
        self.assertTrue(any("guaranteed" in v.lower() for v in violations))

    def test_moon_blocked(self):
        passed, violations = check_compliance("BTC to the moon!")
        self.assertFalse(passed)

    def test_easy_money_blocked(self):
        passed, violations = check_compliance("This is easy money, just follow the signals.")
        self.assertFalse(passed)

    def test_100_percent_win_blocked(self):
        passed, violations = check_compliance("Our system has a 100% win rate.")
        self.assertFalse(passed)

    def test_risk_free_blocked(self):
        passed, violations = check_compliance("A risk-free trading approach.")
        self.assertFalse(passed)


class CompliancePredictionTest(TestCase):
    def test_will_rise_blocked(self):
        passed, _ = check_compliance("BTC will rise to 100K by Friday.")
        self.assertFalse(passed)

    def test_price_will_blocked(self):
        passed, _ = check_compliance("The price will go to 1.10 this week.")
        self.assertFalse(passed)

    def test_you_should_buy_blocked(self):
        passed, _ = check_compliance("You should buy EUR/USD right now.")
        self.assertFalse(passed)

    def test_educational_framing_passes(self):
        passed, _ = check_compliance("Historically, this pattern has been associated with upward moves.")
        self.assertTrue(passed)


class CopyTradingComplianceTest(TestCase):
    def test_guaranteed_returns_blocked(self):
        passed, _ = check_copytrading_compliance("This trader offers guaranteed returns.")
        self.assertFalse(passed)

    def test_clean_copy_text_passes(self):
        passed, _ = check_copytrading_compliance(
            "This trader has a 72% win rate over 6 months. Past performance does not guarantee future results."
        )
        self.assertTrue(passed)


class DemoTradingComplianceTest(TestCase):
    def test_real_money_blocked(self):
        passed, _ = check_demo_trading_compliance("Try this with your real money account.")
        self.assertFalse(passed)

    def test_demo_text_passes(self):
        passed, _ = check_demo_trading_compliance("This is a demo trade with virtual money.")
        self.assertTrue(passed)


class DisclaimerTest(TestCase):
    def test_market_disclaimer(self):
        result = append_disclaimer("Some analysis.", "market")
        self.assertIn("Not financial advice", result)

    def test_copytrading_disclaimer(self):
        result = append_disclaimer("Trader info.", "copytrading")
        self.assertIn("Past performance", result)

    def test_trading_disclaimer(self):
        result = append_disclaimer("Trade executed.", "trading")
        self.assertIn("Demo account", result)


class SanitizeTokenTest(TestCase):
    def test_long_token(self):
        result = sanitize_token("abcdefghijklmnop")
        self.assertEqual(result, "abcd...mnop")

    def test_short_token(self):
        result = sanitize_token("abc")
        self.assertEqual(result, "***")

    def test_empty_token(self):
        result = sanitize_token("")
        self.assertEqual(result, "***")
