"""
Trading execution tools — callable by Agent Pipeline via Function Calling.
Demo account only. Every response includes educational disclaimers.
"""
from typing import Dict, Any, List
from behavior.deriv_client import DerivClient


# Reuse the DERIV_SYMBOLS mapping from market tools
INSTRUMENT_TO_SYMBOL = {
    "EUR/USD": "frxEURUSD",
    "GBP/USD": "frxGBPUSD",
    "USD/JPY": "frxUSDJPY",
    "AUD/USD": "frxAUDUSD",
    "USD/CHF": "frxUSDCHF",
    "BTC/USD": "cryBTCUSD",
    "ETH/USD": "cryETHUSD",
    "GOLD": "frxXAUUSD",
    "XAU/USD": "frxXAUUSD",
    "Volatility 75 Index": "R_75",
    "Volatility 75": "R_75",
    "V75": "R_75",
    "Volatility 100 Index": "R_100",
    "Volatility 100": "R_100",
    "V100": "R_100",
    "Volatility 50 Index": "R_50",
    "Volatility 50": "R_50",
    "V50": "R_50",
    "Volatility 25 Index": "R_25",
    "Volatility 25": "R_25",
    "V25": "R_25",
    "Volatility 10 Index": "R_10",
    "Volatility 10": "R_10",
    "V10": "R_10",
}

DEMO_DISCLAIMER = (
    "DEMO account only — virtual money. "
    "This is for educational purposes, not financial advice."
)


def _resolve_symbol(instrument: str) -> str:
    """Convert user-friendly instrument name to Deriv symbol."""
    return INSTRUMENT_TO_SYMBOL.get(instrument, instrument)


def get_contract_quote(
    instrument: str = "Volatility 100 Index",
    contract_type: str = "CALL",
    amount: float = 10,
    duration: int = 5,
    duration_unit: str = "t",
    api_token: str = None,
) -> Dict[str, Any]:
    """
    Get a price quote for a trading contract.

    Educational: shows how contract pricing works with real market data.
    """
    try:
        symbol = _resolve_symbol(instrument)
        client = DerivClient(api_token=api_token)
        result = client.get_contract_proposal(
            symbol=symbol,
            contract_type=contract_type,
            amount=amount,
            duration=duration,
            duration_unit=duration_unit,
            api_token=api_token,
        )

        if "error" in result:
            return result

        result["instrument"] = instrument
        result["duration"] = duration
        result["duration_unit"] = duration_unit
        result["disclaimer"] = DEMO_DISCLAIMER
        result["educational_note"] = (
            f"A '{contract_type}' contract means you "
            f"{'profit if the price goes UP' if contract_type == 'CALL' else 'profit if the price goes DOWN'}. "
            f"Stake: ${amount}, potential payout shown above."
        )
        return result

    except Exception as e:
        return {"error": str(e)}


def execute_demo_trade(
    proposal_id: str,
    price: float,
    api_token: str = None,
) -> Dict[str, Any]:
    """
    Execute a trade on Demo account (virtual money only).

    Important:
    - Only works with Demo account tokens
    - Response always includes compliance disclaimer
    """
    try:
        client = DerivClient(api_token=api_token)
        result = client.buy_contract(
            proposal_id=proposal_id,
            price=price,
            api_token=api_token,
        )

        if "error" in result:
            return result

        result["disclaimer"] = DEMO_DISCLAIMER
        result["educational_note"] = (
            "Trade executed on Demo account with virtual funds. "
            "This demonstrates the full trading cycle for educational purposes."
        )
        return result

    except Exception as e:
        return {"error": str(e)}


def quote_and_buy(
    instrument: str = "Volatility 100 Index",
    contract_type: str = "CALL",
    amount: float = 10,
    duration: int = 5,
    duration_unit: str = "t",
    api_token: str = None,
) -> Dict[str, Any]:
    """
    Get quote and immediately buy in a single WebSocket session.
    Avoids InvalidContractProposal errors from expired proposal IDs.
    """
    try:
        symbol = _resolve_symbol(instrument)
        client = DerivClient(api_token=api_token)
        result = client.quote_and_buy(
            symbol=symbol,
            contract_type=contract_type,
            amount=amount,
            duration=duration,
            duration_unit=duration_unit,
            api_token=api_token,
        )

        if "error" in result:
            return result

        result["instrument"] = instrument
        result["disclaimer"] = DEMO_DISCLAIMER
        result["educational_note"] = (
            "Trade executed on Demo account with virtual funds. "
            "This demonstrates the full trading cycle for educational purposes."
        )
        return result

    except Exception as e:
        return {"error": str(e)}


def close_position(contract_id: int, api_token: str = None) -> Dict[str, Any]:
    """Close an open contract position."""
    try:
        client = DerivClient(api_token=api_token)
        result = client.sell_contract(
            contract_id=contract_id,
            price=0,  # 0 = market price sell
            api_token=api_token,
        )

        if "error" in result:
            return result

        result["disclaimer"] = DEMO_DISCLAIMER
        return result

    except Exception as e:
        return {"error": str(e)}


def get_positions(api_token: str = None) -> Dict[str, Any]:
    """Get all currently open contract positions."""
    try:
        client = DerivClient(api_token=api_token)

        # Use `portfolio` to list open contracts. `proposal_open_contract` is
        # inconsistent across contract types/accounts and has returned empty
        # even when `portfolio` has active positions.
        portfolio = client.fetch_portfolio(api_token=api_token) or {}
        contracts = portfolio.get("contracts") or []

        # Build reverse symbol lookup for display.
        symbol_to_instrument = {}
        for instrument, symbol in INSTRUMENT_TO_SYMBOL.items():
            symbol_to_instrument.setdefault(symbol, instrument)

        positions: List[Dict[str, Any]] = []
        for c in contracts if isinstance(contracts, list) else []:
            if not isinstance(c, dict):
                continue
            symbol = c.get("symbol") or c.get("underlying") or ""
            instrument = symbol_to_instrument.get(symbol, symbol or "UNKNOWN")
            positions.append({
                "contract_id": c.get("contract_id"),
                "instrument": instrument,
                "contract_type": c.get("contract_type", ""),
                "buy_price": float(c.get("buy_price", 0) or 0),
                "current_spot": float(c.get("current_spot", 0) or 0),
                "profit": float(c.get("profit", 0) or 0),
                "is_valid_to_sell": bool(c.get("is_valid_to_sell") in (1, True, "1")),
                "longcode": c.get("longcode", ""),
            })

        return {
            "positions": positions,
            "count": len(positions),
            "disclaimer": DEMO_DISCLAIMER,
        }

    except Exception as e:
        return {"error": str(e), "positions": []}
