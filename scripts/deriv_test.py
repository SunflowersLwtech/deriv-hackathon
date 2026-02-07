#!/usr/bin/env python3
"""
Deriv WebSocket API Test Script
Tests: connection, authorization, balance, account info, and market tick data.
"""

import asyncio
import json
import websockets
import os
from pathlib import Path
from dotenv import load_dotenv

# ─── Configuration ───────────────────────────────────────────────
# Load environment from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

APP_ID = os.getenv("DERIV_APP_ID", "125489")
API_TOKEN = os.getenv("DERIV_TOKEN", "")
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"


async def send_and_receive(ws, request, label=""):
    """Send a JSON request and return the parsed response."""
    await ws.send(json.dumps(request))
    raw = await ws.recv()
    data = json.loads(raw)

    if "error" in data:
        print(f"  [ERROR] {label}: {data['error']['message']}")
    return data


def print_separator(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


async def test_ping(ws):
    """Test 1: Basic connectivity with ping."""
    print_separator("Test 1: Ping")
    resp = await send_and_receive(ws, {"ping": 1}, "Ping")
    if resp.get("ping") == "pong":
        print("  [OK] Server responded with pong")
    else:
        print(f"  [WARN] Unexpected response: {resp}")


async def test_server_time(ws):
    """Test 2: Get server time."""
    print_separator("Test 2: Server Time")
    resp = await send_and_receive(ws, {"time": 1}, "Time")
    if "time" in resp:
        from datetime import datetime, timezone
        t = datetime.fromtimestamp(resp["time"], tz=timezone.utc)
        print(f"  [OK] Server time: {t.strftime('%Y-%m-%d %H:%M:%S UTC')}")


async def test_website_status(ws):
    """Test 3: Check website status."""
    print_separator("Test 3: Website Status")
    resp = await send_and_receive(ws, {"website_status": 1}, "Website Status")
    if "website_status" in resp:
        status = resp["website_status"]
        print(f"  [OK] Site status : {status.get('site_status', 'N/A')}")
        print(f"       Currencies  : {len(status.get('currencies_config', {}))} configured")
        print(f"       API version : {status.get('api_call_limits', {})}")


async def test_authorize(ws):
    """Test 4: Authorize with API token."""
    print_separator("Test 4: Authorize")
    resp = await send_and_receive(ws, {"authorize": API_TOKEN}, "Authorize")
    if "authorize" in resp:
        auth = resp["authorize"]
        print(f"  [OK] Authorized successfully")
        print(f"       Login ID    : {auth.get('loginid', 'N/A')}")
        print(f"       Full Name   : {auth.get('fullname', 'N/A')}")
        print(f"       Email       : {auth.get('email', 'N/A')}")
        print(f"       Currency    : {auth.get('currency', 'N/A')}")
        print(f"       Balance     : {auth.get('balance', 'N/A')} {auth.get('currency', '')}")
        print(f"       Country     : {auth.get('country', 'N/A')}")
        print(f"       Account List:")
        for acc in auth.get("account_list", []):
            print(f"         - {acc.get('loginid')}: {acc.get('currency', 'N/A')} ({'real' if acc.get('is_virtual') == 0 else 'demo'})")
        return True
    return False


async def test_balance(ws):
    """Test 5: Get account balance."""
    print_separator("Test 5: Balance")
    resp = await send_and_receive(ws, {"balance": 1, "account": "current"}, "Balance")
    if "balance" in resp:
        bal = resp["balance"]
        print(f"  [OK] Balance     : {bal.get('balance', 'N/A')} {bal.get('currency', '')}")
        print(f"       Account ID  : {bal.get('loginid', 'N/A')}")


async def test_account_status(ws):
    """Test 6: Get account status."""
    print_separator("Test 6: Account Status")
    resp = await send_and_receive(ws, {"get_account_status": 1}, "Account Status")
    if "get_account_status" in resp:
        status = resp["get_account_status"]
        print(f"  [OK] Risk class  : {status.get('risk_classification', 'N/A')}")
        print(f"       Status flags: {', '.join(status.get('status', []))}")


async def test_active_symbols(ws):
    """Test 7: Get available trading symbols (first 10)."""
    print_separator("Test 7: Active Symbols (sample)")
    resp = await send_and_receive(
        ws,
        {"active_symbols": "brief", "product_type": "basic"},
        "Active Symbols"
    )
    if "active_symbols" in resp:
        symbols = resp["active_symbols"]
        print(f"  [OK] Total active symbols: {len(symbols)}")
        print(f"       First 10:")
        for s in symbols[:10]:
            print(f"         - {s['symbol']:20s} | {s['display_name']}")


async def test_tick(ws):
    """Test 8: Get a single price tick for a popular symbol."""
    print_separator("Test 8: Price Tick (R_100 - Volatility 100)")
    resp = await send_and_receive(ws, {"ticks": "R_100"}, "Tick")
    if "tick" in resp:
        tick = resp["tick"]
        print(f"  [OK] Symbol : {tick.get('symbol', 'N/A')}")
        print(f"       Quote  : {tick.get('quote', 'N/A')}")
        print(f"       Epoch  : {tick.get('epoch', 'N/A')}")


async def test_portfolio(ws):
    """Test 9: Get current portfolio (open contracts)."""
    print_separator("Test 9: Portfolio")
    resp = await send_and_receive(ws, {"portfolio": 1}, "Portfolio")
    if "portfolio" in resp:
        contracts = resp["portfolio"].get("contracts", [])
        print(f"  [OK] Open contracts: {len(contracts)}")
        for c in contracts[:5]:
            print(f"         - {c.get('symbol', 'N/A')}: buy={c.get('buy_price', 'N/A')}, "
                  f"type={c.get('contract_type', 'N/A')}")


async def test_profit_table(ws):
    """Test 10: Get recent profit/loss records."""
    print_separator("Test 10: Profit Table (last 5)")
    resp = await send_and_receive(
        ws,
        {"profit_table": 1, "limit": 5, "sort": "DESC"},
        "Profit Table"
    )
    if "profit_table" in resp:
        trades = resp["profit_table"].get("transactions", [])
        print(f"  [OK] Recent transactions: {len(trades)}")
        for t in trades:
            print(f"         - {t.get('shortcode', 'N/A'):30s} | "
                  f"buy: {t.get('buy_price', 'N/A'):>8} | "
                  f"sell: {t.get('sell_price', 'N/A'):>8} | "
                  f"P/L: {t.get('profit_loss', 'N/A')}")


async def main():
    print("Deriv WebSocket API Test")
    print(f"App ID : {APP_ID}")
    print(f"URL    : {WS_URL}")
    print(f"Token  : {'configured' if API_TOKEN else 'missing (public tests only)'}")

    try:
        async with websockets.connect(WS_URL) as ws:
            print("\n[CONNECTED] WebSocket connection established")

            # Public API tests (no auth needed)
            await test_ping(ws)
            await test_server_time(ws)
            await test_website_status(ws)

            # Authorized API tests
            authorized = False
            if API_TOKEN:
                authorized = await test_authorize(ws)
            else:
                print("\n[SKIP] Auth tests skipped because DERIV_TOKEN is not configured")

            if authorized:
                await test_balance(ws)
                await test_account_status(ws)
                await test_active_symbols(ws)
                await test_tick(ws)
                await test_portfolio(ws)
                await test_profit_table(ws)

            print_separator("All Tests Complete")
            print("  Done!\n")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\n[CLOSED] Connection closed: code={e.code}, reason={e.reason}")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
