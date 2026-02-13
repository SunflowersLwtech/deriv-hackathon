#!/usr/bin/env python3
"""
TradeIQ Smoke Test — Pre-demo validation.
Hits critical API endpoints and reports pass/fail.
Run: python backend/scripts/smoke_test.py
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000"

TESTS = [
    ("GET", "/healthz/", None, "Health check"),
    ("GET", "/api/market/insights/", None, "Market insights"),
    ("POST", "/api/agents/monitor/", {"instruments": ["BTC/USD"]}, "Agent monitor"),
    ("POST", "/api/agents/chat/", {"message": "What happened to EUR/USD?"}, "Agent chat"),
    ("POST", "/api/agents/copytrading/", {"action": "list"}, "Copy trading list"),
    ("POST", "/api/agents/trading/", {"action": "quote", "instrument": "Volatility 100 Index"}, "Trading quote"),
    ("GET", "/api/demo/scripts/", None, "Demo scripts"),
    ("GET", "/api/demo/scenarios/", None, "Demo scenarios"),
]


def run_smoke_test():
    print("=" * 50)
    print("  TradeIQ Smoke Test")
    print("=" * 50)

    passed = 0
    failed = 0
    total_start = time.time()

    for method, endpoint, body, label in TESTS:
        url = f"{BASE_URL}{endpoint}"
        start = time.time()
        try:
            if method == "GET":
                resp = requests.get(url, timeout=15)
            else:
                resp = requests.post(url, json=body, timeout=30, headers={"Content-Type": "application/json"})

            duration = int((time.time() - start) * 1000)
            if resp.status_code < 400:
                print(f"  PASS  {label:<25} {resp.status_code}  {duration}ms")
                passed += 1
            else:
                print(f"  FAIL  {label:<25} {resp.status_code}  {duration}ms  {resp.text[:100]}")
                failed += 1
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            print(f"  FAIL  {label:<25} ERR    {duration}ms  {str(e)[:80]}")
            failed += 1

    total_ms = int((time.time() - total_start) * 1000)
    print()
    print(f"  Results: {passed} passed, {failed} failed ({total_ms}ms)")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
