"""
Trade Sync — Pull real trades from Deriv and save to the Trade model.

Idempotent: uses (user, instrument, direction, opened_at, entry_price) as
a natural key to avoid duplicates.  Real trades are always saved with
is_mock=False and never overwrite or delete existing real trades.
"""

from typing import Dict, Any, Optional
from .models import Trade, UserProfile
from .deriv_client import DerivClient, DerivAPIError
import logging

logger = logging.getLogger("tradeiq.trade_sync")


def sync_trades_for_user(
    user_id: str,
    api_token: str,
    days_back: int = 30,
) -> Dict[str, Any]:
    """
    Fetch trades from Deriv and upsert into Trade table.

    Args:
        user_id: UserProfile UUID
        api_token: Deriv API token for this user
        days_back: how many days of history to pull

    Returns:
        {
            'success': bool,
            'trades_fetched': int,
            'trades_created': int,
            'trades_updated': int,
            'errors': list[str],
        }
    """
    try:
        user = UserProfile.objects.get(id=user_id)
    except UserProfile.DoesNotExist:
        return {
            "success": False,
            "trades_fetched": 0,
            "trades_created": 0,
            "trades_updated": 0,
            "errors": [f"User {user_id} not found"],
        }

    # Fetch from Deriv
    try:
        client = DerivClient()
        raw_trades = client._run_async(_fetch(client, api_token, days_back))
    except DerivAPIError as exc:
        return {
            "success": False,
            "trades_fetched": 0,
            "trades_created": 0,
            "trades_updated": 0,
            "errors": [str(exc)],
        }
    except Exception as exc:
        return {
            "success": False,
            "trades_fetched": 0,
            "trades_created": 0,
            "trades_updated": 0,
            "errors": [f"Unexpected error: {exc}"],
        }

    created = 0
    updated = 0
    errors = []

    for td in raw_trades:
        try:
            # Build natural-key filter
            qs = Trade.objects.filter(
                user=user,
                instrument=td.get("instrument", ""),
                direction=td.get("direction", ""),
                is_mock=False,
            )
            if td.get("opened_at") is not None:
                qs = qs.filter(opened_at=td["opened_at"])
            if td.get("entry_price") is not None:
                qs = qs.filter(entry_price=td["entry_price"])

            existing = qs.first()

            if existing:
                existing.pnl = td["pnl"]
                existing.exit_price = td.get("exit_price")
                existing.closed_at = td.get("closed_at")
                existing.duration_seconds = td.get("duration_seconds")
                existing.save()
                updated += 1
            else:
                Trade.objects.create(
                    user=user,
                    instrument=td.get("instrument", "UNKNOWN"),
                    direction=td.get("direction", "UNKNOWN"),
                    pnl=td["pnl"],
                    entry_price=td.get("entry_price"),
                    exit_price=td.get("exit_price"),
                    opened_at=td.get("opened_at"),
                    closed_at=td.get("closed_at"),
                    duration_seconds=td.get("duration_seconds"),
                    is_mock=False,
                )
                created += 1
        except Exception as exc:
            cid = td.get("contract_id", "?")
            errors.append(f"Error saving trade {cid}: {exc}")
            continue

    return {
        "success": True,
        "trades_fetched": len(raw_trades),
        "trades_created": created,
        "trades_updated": updated,
        "errors": errors,
    }


async def _fetch(client: DerivClient, api_token: str, days_back: int):
    """Internal coroutine — fetch all trades in a fresh WS connection."""
    fresh = DerivClient(client.app_id)
    try:
        return await fresh.fetch_all_trades(api_token=api_token, days_back=days_back)
    finally:
        await fresh.disconnect()
