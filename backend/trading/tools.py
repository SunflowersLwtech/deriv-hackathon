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
) -> Dict[str, Any]:
    """
    Get a price quote for a trading contract.

    Educational: shows how contract pricing works with real market data.
    """
    try:
        symbol = _resolve_symbol(instrument)
        client = DerivClient()
        result = client.get_contract_proposal(
            symbol=symbol,
            contract_type=contract_type,
            amount=amount,
            duration=duration,
            duration_unit=duration_unit,
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
) -> Dict[str, Any]:
    """
    Execute a trade on Demo account (virtual money only).

    Important:
    - Only works with Demo account tokens
    - Response always includes compliance disclaimer
    """
    try:
        client = DerivClient()
        result = client.buy_contract(
            proposal_id=proposal_id,
            price=price,
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
) -> Dict[str, Any]:
    """
    Get quote and immediately buy in a single WebSocket session.
    Avoids InvalidContractProposal errors from expired proposal IDs.
    """
    try:
        symbol = _resolve_symbol(instrument)
        client = DerivClient()
        result = client.quote_and_buy(
            symbol=symbol,
            contract_type=contract_type,
            amount=amount,
            duration=duration,
            duration_unit=duration_unit,
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


def close_position(contract_id: int) -> Dict[str, Any]:
    """Close an open contract position."""
    try:
        client = DerivClient()
        result = client.sell_contract(
            contract_id=contract_id,
            price=0,  # 0 = market price sell
        )

        if "error" in result:
            return result

        result["disclaimer"] = DEMO_DISCLAIMER
        return result

    except Exception as e:
        return {"error": str(e)}


def get_positions() -> Dict[str, Any]:
    """Get all currently open contract positions."""
    try:
        client = DerivClient()
        contracts = client.get_open_contracts()

        if isinstance(contracts, dict) and "error" in contracts:
            return contracts

        return {
            "positions": contracts if isinstance(contracts, list) else [],
            "count": len(contracts) if isinstance(contracts, list) else 0,
            "disclaimer": DEMO_DISCLAIMER,
        }

    except Exception as e:
        return {"error": str(e), "positions": []}
