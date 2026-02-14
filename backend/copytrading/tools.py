"""Copy Trading tools — callable by Agent Pipeline via Function Calling."""
import logging
from typing import Dict, Any, List
from .deriv_copy import DerivCopyTradingClient

logger = logging.getLogger(__name__)

def _generate_demo_traders(n: int = 30) -> List[Dict[str, Any]]:
    """
    Deterministic demo traders so the Copy page always has enough rows for demos.

    These are only used when Deriv returns empty / partial results for demo users.
    """
    traders: List[Dict[str, Any]] = []
    for i in range(1, max(int(n), 0) + 1):
        # CR90000001 ... CR90000030 (matches the original style)
        loginid = f"CR{90000000 + i:08d}"

        # Create stable, plausible metrics without RNG.
        performance_probability = round(0.55 + ((i * 7) % 31) / 100, 2)  # 0.55 - 0.85
        total_trades = 80 + ((i * 73) % 1400)  # 80 - 1479
        copiers = 2 + ((i * 11) % 95)  # 2 - 96
        avg_profit = round(4.5 + ((i * 19) % 380) / 10, 2)  # 4.5 - 42.4
        avg_loss = round(-3.5 - ((i * 17) % 260) / 10, 2)  # -3.5 - -29.5
        win_rate = round(52 + ((i * 9) % 34) + (performance_probability - 0.55) * 20, 1)
        min_trade_stake = round(max(0.35, ((i % 12) + 1) * 0.25), 2)

        year = 2022 + (i % 4)  # 2022-2025
        month = (i % 12) + 1
        day = (i % 28) + 1
        active_since = f"{year:04d}-{month:02d}-{day:02d}"

        traders.append({
            "loginid": loginid,
            "token": f"demo_token_{i}",
            "avg_profit": avg_profit,
            "total_trades": total_trades,
            "copiers": copiers,
            "performance_probability": performance_probability,
            "min_trade_stake": min_trade_stake,
            "trade_types": ["CALL", "PUT"],
            "active_since": active_since,
            "win_rate": win_rate,
            "avg_loss": avg_loss,
            "_demo": True,
        })
    return traders


# Fallback demo traders shown when Deriv returns empty/partial list.
DEMO_TRADERS = _generate_demo_traders(30)


def _demo_fill(limit: int, exclude_loginids: set[str] | None = None) -> List[Dict[str, Any]]:
    exclude = exclude_loginids or set()
    filled: List[Dict[str, Any]] = []
    for t in DEMO_TRADERS:
        if t.get("loginid") in exclude:
            continue
        filled.append(_normalize_trader(t))
        if len(filled) >= limit:
            break
    return filled


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


def get_top_traders(limit: int = 10, api_token: str = None) -> Dict[str, Any]:
    """Get list of traders available for copy trading with basic statistics."""
    safe_limit = _safe_limit(limit)
    try:
        client = DerivCopyTradingClient(api_token=api_token)
        result = client.get_copytrading_list()

        if "error" in result:
            demo_traders = [_normalize_trader(t) for t in DEMO_TRADERS[:safe_limit]]
            logger.warning("Deriv copytrading_list error: %s — using demo data", result["error"])
            return {
                "traders": demo_traders,
                "count": len(demo_traders),
                "total_count": len(DEMO_TRADERS),
                "source": "demo_fallback",
                "api_error": result["error"],
                "disclaimer": "Demo data shown due to API error. Connect your Deriv account for live data.",
            }

        traders = result.get("traders", [])

        if not traders:
            demo_traders = _demo_fill(safe_limit)
            logger.info("Deriv copytrading_list returned empty — using demo data")
            return {
                "traders": demo_traders,
                "count": len(demo_traders),
                "total_count": len(DEMO_TRADERS),
                "source": "demo_fallback",
                "disclaimer": "No live traders found. Showing demo data for reference.",
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

        # For demos, Deriv can legitimately return partial lists (e.g. user only copies 1 trader).
        # Fill the remaining rows with deterministic demo traders so the UI isn't empty/sparse.
        if len(enriched) < safe_limit:
            exclude = {t.get("loginid", "") for t in enriched}
            demo_traders = _demo_fill(safe_limit - len(enriched), exclude_loginids=exclude)
            enriched = enriched + demo_traders
            source = "mixed_fallback"
            disclaimer = (
                "Showing live Deriv copy-trading data plus demo sample traders for UI demonstration. "
                "Past performance is not indicative of future results."
            )
            total_count = len(enriched)
        else:
            source = "deriv_api"
            disclaimer = "Past performance is not indicative of future results. This is educational information."
            total_count = len(traders)

        return {
            "traders": enriched,
            "count": len(enriched),
            "total_count": total_count,
            "source": source,
            "disclaimer": disclaimer,
        }

    except Exception as e:
        demo_traders = _demo_fill(safe_limit)
        logger.exception("Copy trading get_top_traders failed: %s", e)
        return {
            "traders": demo_traders,
            "count": len(demo_traders),
            "total_count": len(DEMO_TRADERS),
            "source": "demo_fallback",
            "api_error": str(e),
            "disclaimer": "Demo data shown due to connection error. Connect your Deriv account for live data.",
        }


def get_trader_stats(trader_id: str, api_token: str = None) -> Dict[str, Any]:
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
        client = DerivCopyTradingClient(api_token=api_token)
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


def recommend_trader(user_id: str, api_token: str = None) -> Dict[str, Any]:
    """AI-powered trader recommendation based on user's trading style."""
    try:
        client = DerivCopyTradingClient(api_token=api_token)

        # Get available traders
        traders_result = get_top_traders(limit=5, api_token=api_token)
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


def start_copy_trade(trader_id: str, api_token: str = None) -> Dict[str, Any]:
    """Start copying a trader."""
    try:
        client = DerivCopyTradingClient(api_token=api_token)
        result = client.start_copy(trader_id=trader_id)
        return result
    except Exception as e:
        return {"error": str(e)}


def stop_copy_trade(trader_id: str, api_token: str = None) -> Dict[str, Any]:
    """Stop copying a trader."""
    try:
        client = DerivCopyTradingClient(api_token=api_token)
        result = client.stop_copy(trader_id=trader_id)
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
