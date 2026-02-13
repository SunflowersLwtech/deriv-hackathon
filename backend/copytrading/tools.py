"""Copy Trading tools — callable by Agent Pipeline via Function Calling."""
import logging
from typing import Dict, Any, List
from .deriv_copy import DerivCopyTradingClient

logger = logging.getLogger(__name__)

# Fallback demo traders shown when Deriv API returns empty list
# (e.g. account hasn't started copying anyone, or token lacks permissions)
DEMO_TRADERS = [
    {
        "loginid": "CR90000001",
        "token": "demo_token_1",
        "avg_profit": 12.50,
        "total_trades": 342,
        "copiers": 18,
        "performance_probability": 0.72,
        "min_trade_stake": 1.00,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2024-03-15",
        "win_rate": 68.4,
        "avg_loss": -8.30,
        "_demo": True,
    },
    {
        "loginid": "CR90000002",
        "token": "demo_token_2",
        "avg_profit": 8.75,
        "total_trades": 891,
        "copiers": 45,
        "performance_probability": 0.65,
        "min_trade_stake": 0.50,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2023-11-01",
        "win_rate": 61.2,
        "avg_loss": -6.10,
        "_demo": True,
    },
    {
        "loginid": "CR90000003",
        "token": "demo_token_3",
        "avg_profit": 22.30,
        "total_trades": 156,
        "copiers": 7,
        "performance_probability": 0.81,
        "min_trade_stake": 5.00,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2024-08-20",
        "win_rate": 74.1,
        "avg_loss": -15.20,
        "_demo": True,
    },
    {
        "loginid": "CR90000004",
        "token": "demo_token_4",
        "avg_profit": 5.40,
        "total_trades": 1247,
        "copiers": 92,
        "performance_probability": 0.58,
        "min_trade_stake": 0.35,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2022-06-10",
        "win_rate": 55.8,
        "avg_loss": -4.80,
        "_demo": True,
    },
    {
        "loginid": "CR90000005",
        "token": "demo_token_5",
        "avg_profit": 18.90,
        "total_trades": 423,
        "copiers": 31,
        "performance_probability": 0.69,
        "min_trade_stake": 2.00,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2024-01-05",
        "win_rate": 65.7,
        "avg_loss": -11.40,
        "_demo": True,
    },
    {
        "loginid": "CR90000006",
        "token": "demo_token_6",
        "avg_profit": 31.20,
        "total_trades": 89,
        "copiers": 4,
        "performance_probability": 0.85,
        "min_trade_stake": 10.00,
        "trade_types": ["CALL", "PUT"],
        "active_since": "2025-02-01",
        "win_rate": 78.7,
        "avg_loss": -22.50,
        "_demo": True,
    },
]


def _normalize_trader(trader: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize trader payload so frontend receives a stable schema."""
    return {
        "loginid": trader.get("loginid", ""),
        "token": trader.get("token", ""),
        "avg_profit": float(trader.get("avg_profit", 0) or 0),
        "total_trades": int(trader.get("total_trades", 0) or 0),
        "copiers": int(trader.get("copiers", 0) or 0),
        "performance_probability": float(trader.get("performance_probability", 0) or 0),
        "min_trade_stake": trader.get("min_trade_stake"),
        "trade_types": trader.get("trade_types") or [],
        "balance": trader.get("balance"),
        "currency": trader.get("currency", "USD") or "USD",
        "win_rate": float(trader.get("win_rate", 0) or 0),
        "avg_loss": float(trader.get("avg_loss", 0) or 0),
        "active_since": trader.get("active_since"),
        "_demo": bool(trader.get("_demo", False)),
    }


def _safe_limit(limit: int) -> int:
    try:
        return max(int(limit), 0)
    except (TypeError, ValueError):
        return 10


def get_top_traders(limit: int = 10) -> Dict[str, Any]:
    """Get list of traders available for copy trading with basic statistics."""
    safe_limit = _safe_limit(limit)
    try:
        client = DerivCopyTradingClient()
        result = client.get_copytrading_list()

        if "error" in result:
            demo_traders = [_normalize_trader(t) for t in DEMO_TRADERS[:safe_limit]]
            logger.warning("Deriv copytrading_list error: %s — using demo data", result["error"])
            return {
                "traders": demo_traders,
                "count": len(demo_traders),
                "total_count": len(DEMO_TRADERS),
                "source": "demo_fallback",
                "disclaimer": "Demo data shown. Past performance is not indicative of future results.",
            }

        traders = result.get("traders", [])

        if not traders:
            demo_traders = [_normalize_trader(t) for t in DEMO_TRADERS[:safe_limit]]
            logger.info("Deriv copytrading_list returned empty — using demo data")
            return {
                "traders": demo_traders,
                "count": len(demo_traders),
                "total_count": len(DEMO_TRADERS),
                "source": "demo_fallback",
                "disclaimer": "Demo data shown. Past performance is not indicative of future results.",
            }

        # Enrich with stats for top traders (limit API calls)
        enriched = []
        for trader in traders[:safe_limit]:
            trader_info = _normalize_trader({
                "loginid": trader.get("loginid", ""),
                "token": trader.get("token", ""),
                "balance": trader.get("balance"),
                "currency": trader.get("currency", "USD"),
                "min_trade_stake": trader.get("min_trade_stake"),
                "trade_types": trader.get("trade_types"),
            })

            # Try to get stats for this trader
            stats = client.get_copytrading_statistics(trader_info["loginid"])
            if "error" not in stats:
                trader_info.update({
                    "win_rate": round(
                        stats.get("trades_profitable", 0) / max(stats.get("total_trades", 1), 1) * 100,
                        1,
                    ),
                    "total_trades": stats.get("total_trades", 0),
                    "copiers": stats.get("copiers", 0),
                    "avg_profit": stats.get("avg_profit", 0),
                    "avg_loss": stats.get("avg_loss", 0),
                    "performance_probability": stats.get("performance_probability", 0),
                    "active_since": stats.get("active_since"),
                })
            else:
                logger.info(
                    "copytrading_statistics unavailable for %s: %s",
                    trader_info["loginid"],
                    stats.get("error"),
                )

            enriched.append(_normalize_trader(trader_info))

        return {
            "traders": enriched,
            "count": len(enriched),
            "total_count": len(traders),
            "source": "deriv_api",
            "disclaimer": "Past performance is not indicative of future results. This is educational information.",
        }

    except Exception as e:
        demo_traders = [_normalize_trader(t) for t in DEMO_TRADERS[:safe_limit]]
        logger.exception("Copy trading get_top_traders failed: %s", e)
        return {
            "traders": demo_traders,
            "count": len(demo_traders),
            "total_count": len(DEMO_TRADERS),
            "source": "demo_fallback",
            "error": str(e),
            "disclaimer": "Demo data shown due to API error. Past performance is not indicative of future results.",
        }


def get_trader_stats(trader_id: str) -> Dict[str, Any]:
    """Get detailed statistics for a specific trader."""
    # Check if this is a demo trader
    demo = next((t for t in DEMO_TRADERS if t["loginid"] == trader_id), None)
    if demo:
        return {
            "trader_id": trader_id,
            "stats": {
                "avg_profit": demo["avg_profit"],
                "total_trades": demo["total_trades"],
                "copiers": demo["copiers"],
                "performance_probability": demo["performance_probability"],
                "monthly_profitable_trades": int(demo["total_trades"] * demo["win_rate"] / 100 / 12),
                "active_since": demo.get("active_since", ""),
            },
            "source": "demo_fallback",
            "disclaimer": "Demo data. Past performance is not indicative of future results.",
        }

    try:
        client = DerivCopyTradingClient()
        stats = client.get_copytrading_statistics(trader_id)

        if "error" in stats:
            return stats

        # Calculate additional metrics
        total = stats.get("total_trades", 0)
        profitable = stats.get("trades_profitable", 0)
        win_rate = round(profitable / max(total, 1) * 100, 1)
        return {
            "trader_id": trader_id,
            "stats": {
                "avg_profit": stats.get("avg_profit", 0),
                "total_trades": total,
                "copiers": stats.get("copiers", 0),
                "performance_probability": stats.get("performance_probability", 0),
                "monthly_profitable_trades": profitable,
                "active_since": stats.get("active_since", ""),
                "win_rate": win_rate,
                "avg_loss": stats.get("avg_loss", 0),
            },
            "source": "deriv_api",
            "disclaimer": (
                "Past performance is not indicative of future results. "
                "This is educational information, not financial advice."
            ),
        }

    except Exception as e:
        return {"error": str(e)}


def recommend_trader(user_id: str) -> Dict[str, Any]:
    """AI-powered trader recommendation based on user's trading style."""
    try:
        client = DerivCopyTradingClient()

        # Get available traders
        traders_result = get_top_traders(limit=5)
        if "error" in traders_result and not traders_result.get("traders"):
            return {"error": traders_result["error"], "recommendations": []}

        traders = traders_result.get("traders", [])
        if not traders:
            return {"recommendations": [], "message": "No traders available for copy trading at this time."}

        # Get user profile for matching
        user_profile = _get_user_profile(user_id)

        # Analyze compatibility for each trader
        recommendations = []
        for trader in traders:
            # Build trader stats dict for compatibility analysis
            trader_stats = {
                "total_trades": trader.get("total_trades", 0),
                "trades_profitable": int(
                    trader.get("total_trades", 0) * trader.get("win_rate", 50) / 100
                ),
                "avg_profit": trader.get("avg_profit", 0),
                "avg_loss": trader.get("avg_loss", 0),
                "copiers": trader.get("copiers", 0),
                "performance_probability": trader.get("performance_probability", 0),
            }

            compat = client.analyze_trader_compatibility(trader_stats, user_profile)

            recommendations.append({
                "trader": trader,
                "trader_id": trader.get("loginid", ""),
                "compatibility_score": compat.get("compatibility_score", 0) / 100,
                "reasons": compat.get("strengths", []) + compat.get("risks", []),
                "strengths": compat.get("strengths", []),
                "risks": compat.get("risks", []),
                "recommendation": compat.get("recommendation", ""),
                "win_rate": trader.get("win_rate", 0),
                "total_trades": trader.get("total_trades", 0),
                "copiers": trader.get("copiers", 0),
            })

        # Sort by compatibility score
        recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return {
            "recommendations": recommendations[:3],
            "disclaimer": (
                "These recommendations are based on historical data analysis. "
                "Past performance is not indicative of future results. "
                "This is educational information, not financial advice."
            ),
        }

    except Exception as e:
        return {"error": str(e), "recommendations": []}


def start_copy_trade(trader_id: str, api_token: str) -> Dict[str, Any]:
    """Start copying a trader (Demo account only)."""
    try:
        client = DerivCopyTradingClient()
        result = client.start_copy(trader_id=trader_id, api_token=api_token)
        return result
    except Exception as e:
        return {"error": str(e)}


def stop_copy_trade(trader_id: str, api_token: str) -> Dict[str, Any]:
    """Stop copying a trader."""
    try:
        client = DerivCopyTradingClient()
        result = client.stop_copy(trader_id=trader_id, api_token=api_token)
        return result
    except Exception as e:
        return {"error": str(e)}


def _get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user trading profile for compatibility matching."""
    try:
        from behavior.tools import get_trading_statistics
        stats = get_trading_statistics(user_id, days=30)
        return {
            "win_rate": stats.get("win_rate", 50),
            "avg_win": stats.get("avg_win", 5),
            "avg_loss": stats.get("avg_loss", 5),
            "total_trades": stats.get("total_trades", 0),
        }
    except Exception:
        # Fallback profile for demo
        return {
            "win_rate": 50,
            "avg_win": 5.0,
            "avg_loss": 5.0,
            "total_trades": 20,
        }
