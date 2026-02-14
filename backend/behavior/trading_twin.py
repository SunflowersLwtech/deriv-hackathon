"""
Trading Twin — Behavioral Twin Simulation Engine

Core approach:
1. Extract behavioral features from user's real trade history
2. Identify "impulsive trades" (matching detection.py patterns)
3. Simulate two paths:
   - Impulsive Path: keep all trades' real PnL
   - Disciplined Path: remove impulsive trades, keep only disciplined PnL
4. Generate dual equity curves
5. Use AI to generate comparative narrative

No price prediction — this is a what-if retrospective analysis of past trades.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger("tradeiq.twin")


@dataclass
class TwinPoint:
    """A single point on the equity curve."""
    timestamp: str
    impulsive_equity: float
    disciplined_equity: float
    trade_id: Optional[str] = None
    is_impulsive: bool = False
    pattern: Optional[str] = None


@dataclass
class TwinResult:
    """Complete Trading Twin result."""
    equity_curve: List[TwinPoint]

    impulsive_final_equity: float
    disciplined_final_equity: float
    equity_difference: float
    equity_difference_pct: float

    total_trades: int
    impulsive_trades: int
    disciplined_trades: int
    impulsive_loss: float
    disciplined_gain: float

    pattern_breakdown: Dict[str, int]

    narrative: str
    key_insight: str

    analysis_period_days: int
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


def generate_trading_twin(
    user_id: str,
    days: int = 30,
    starting_equity: float = 10000.0,
) -> TwinResult:
    """
    Generate Trading Twin analysis.

    Steps:
    1. Fetch user trades for the last N days
    2. Tag each trade as impulsive or disciplined
    3. Build dual equity curves
    4. Compute summary statistics
    5. Generate AI narrative
    """
    from behavior.models import Trade

    cutoff = timezone.now() - timedelta(days=days)
    trades = list(
        Trade.objects.filter(
            user_id=user_id,
            opened_at__gte=cutoff,
        ).order_by("opened_at").values(
            "id", "instrument", "direction", "pnl",
            "entry_price", "exit_price", "opened_at",
            "duration_seconds",
        )
    )

    if len(trades) < 5:
        return _generate_insufficient_data_result(len(trades), days)

    tagged_trades = _tag_impulsive_trades(trades, user_id)
    equity_curve = _build_equity_curves(tagged_trades, starting_equity)

    impulsive_trades = [t for t in tagged_trades if t["is_impulsive"]]
    disciplined_trades = [t for t in tagged_trades if not t["is_impulsive"]]

    impulsive_final = equity_curve[-1].impulsive_equity if equity_curve else starting_equity
    disciplined_final = equity_curve[-1].disciplined_equity if equity_curve else starting_equity
    difference = disciplined_final - impulsive_final
    difference_pct = (difference / starting_equity) * 100 if starting_equity > 0 else 0

    impulsive_loss = sum(
        float(t["pnl"]) for t in impulsive_trades
        if t.get("pnl") and float(t["pnl"]) < 0
    )
    disciplined_gain = sum(
        float(t["pnl"]) for t in disciplined_trades if t.get("pnl")
    )

    pattern_breakdown: Dict[str, int] = {}
    for t in impulsive_trades:
        pattern = t.get("pattern", "unknown")
        pattern_breakdown[pattern] = pattern_breakdown.get(pattern, 0) + 1

    narrative, key_insight = _generate_narrative(
        total_trades=len(trades),
        impulsive_count=len(impulsive_trades),
        impulsive_final=impulsive_final,
        disciplined_final=disciplined_final,
        difference=difference,
        pattern_breakdown=pattern_breakdown,
        starting_equity=starting_equity,
    )

    return TwinResult(
        equity_curve=equity_curve,
        impulsive_final_equity=round(impulsive_final, 2),
        disciplined_final_equity=round(disciplined_final, 2),
        equity_difference=round(difference, 2),
        equity_difference_pct=round(difference_pct, 2),
        total_trades=len(trades),
        impulsive_trades=len(impulsive_trades),
        disciplined_trades=len(disciplined_trades),
        impulsive_loss=round(impulsive_loss, 2),
        disciplined_gain=round(disciplined_gain, 2),
        pattern_breakdown=pattern_breakdown,
        narrative=narrative,
        key_insight=key_insight,
        analysis_period_days=days,
    )


def _tag_impulsive_trades(
    trades: List[Dict],
    user_id: str,
) -> List[Dict]:
    """
    Tag each trade as impulsive or disciplined.

    Detection logic:
    - Trade opened within 10 min of a loss -> revenge_trading
    - Increasing loss size after consecutive losses -> loss_chasing
    """
    tagged = []
    prev_trade = None

    for i, trade in enumerate(trades):
        is_impulsive = False
        pattern = None
        pnl = float(trade.get("pnl") or 0)

        # Revenge trading: trade opened within 10 minutes of a loss
        if prev_trade and prev_trade.get("pnl") and float(prev_trade["pnl"]) < 0:
            prev_time = prev_trade["opened_at"]
            curr_time = trade["opened_at"]
            if hasattr(prev_time, "timestamp") and hasattr(curr_time, "timestamp"):
                gap_minutes = (curr_time - prev_time).total_seconds() / 60
                if gap_minutes < 10:
                    is_impulsive = True
                    pattern = "revenge_trading"

        # Loss chasing: consecutive losses with increasing size
        if not is_impulsive and i >= 2:
            recent_losses = [
                t for t in trades[max(0, i - 3):i]
                if float(t.get("pnl") or 0) < 0
            ]
            if len(recent_losses) >= 2:
                prev_sizes = [abs(float(t.get("pnl") or 0)) for t in recent_losses]
                curr_size = abs(pnl) if pnl else 0
                if prev_sizes and curr_size > max(prev_sizes) * 1.2:
                    is_impulsive = True
                    pattern = "loss_chasing"

        tagged.append({
            **trade,
            "is_impulsive": is_impulsive,
            "pattern": pattern,
        })
        prev_trade = trade

    return tagged


def _build_equity_curves(
    tagged_trades: List[Dict],
    starting_equity: float,
) -> List[TwinPoint]:
    """
    Build dual equity curves.

    Impulsive Path: includes PnL from ALL trades
    Disciplined Path: excludes PnL from impulsive trades
    """
    curve = []
    imp_equity = starting_equity
    disc_equity = starting_equity

    if tagged_trades:
        first_ts = tagged_trades[0]["opened_at"]
        ts_str = first_ts.isoformat() if hasattr(first_ts, "isoformat") else str(first_ts)
        curve.append(TwinPoint(
            timestamp=ts_str,
            impulsive_equity=imp_equity,
            disciplined_equity=disc_equity,
        ))

    for trade in tagged_trades:
        pnl = float(trade.get("pnl") or 0)
        ts = trade["opened_at"]
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

        imp_equity += pnl

        if not trade["is_impulsive"]:
            disc_equity += pnl

        curve.append(TwinPoint(
            timestamp=ts_str,
            impulsive_equity=round(imp_equity, 2),
            disciplined_equity=round(disc_equity, 2),
            trade_id=str(trade.get("id", "")),
            is_impulsive=trade["is_impulsive"],
            pattern=trade.get("pattern"),
        ))

    return curve


def _generate_narrative(
    total_trades: int,
    impulsive_count: int,
    impulsive_final: float,
    disciplined_final: float,
    difference: float,
    pattern_breakdown: Dict[str, int],
    starting_equity: float,
) -> Tuple[str, str]:
    """Generate AI narrative for Trading Twin comparison."""
    from agents.llm_client import get_llm_client

    patterns_str = ", ".join(f"{k}: {v} times" for k, v in pattern_breakdown.items()) or "none"
    imp_return = ((impulsive_final - starting_equity) / starting_equity) * 100
    disc_return = ((disciplined_final - starting_equity) / starting_equity) * 100

    system_prompt = """You are TradeIQ's Trading Twin narrator. You explain the difference
between a trader's impulsive behavior and their disciplined potential.

RULES:
- Be warm, not judgmental. This is coaching, not scolding.
- Use specific numbers from the data provided.
- Never predict future performance.
- Frame as learning opportunity, not failure.
- Keep it concise (3-4 sentences max for narrative, 1 sentence for key insight).
- This is NOT financial advice.

Respond in JSON:
{"narrative": "...", "key_insight": "..."}"""

    user_prompt = f"""Trading Twin Analysis:
- Total trades: {total_trades}
- Impulsive trades identified: {impulsive_count} ({impulsive_count / total_trades * 100:.0f}% of total)
- Behavioral patterns detected: {patterns_str}
- Starting equity: ${starting_equity:,.2f}
- Impulsive path result: ${impulsive_final:,.2f} ({imp_return:+.1f}%)
- Disciplined path result: ${disciplined_final:,.2f} ({disc_return:+.1f}%)
- Difference: ${difference:+,.2f}

Generate a warm, insightful narrative explaining what the Trading Twin reveals."""

    try:
        llm = get_llm_client()
        raw = llm.simple_chat(system_prompt, user_prompt, max_tokens=300)

        import json
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.split("```")[1]
            if raw_clean.startswith("json"):
                raw_clean = raw_clean[4:]
        data = json.loads(raw_clean)
        return data.get("narrative", ""), data.get("key_insight", "")
    except Exception as exc:
        logger.warning("Narrative generation failed: %s", exc)
        return (
            f"Over {total_trades} trades, {impulsive_count} were identified as impulsive "
            f"(triggered by {patterns_str}). Without those trades, your equity would be "
            f"${disciplined_final:,.2f} instead of ${impulsive_final:,.2f} — "
            f"a difference of ${abs(difference):,.2f}.",
            f"Your Trading Twin suggests that removing impulsive trades could improve results by ${abs(difference):,.2f}."
        )


def _generate_insufficient_data_result(trade_count: int, days: int) -> TwinResult:
    """Return a friendly result when trade data is insufficient."""
    return TwinResult(
        equity_curve=[],
        impulsive_final_equity=0,
        disciplined_final_equity=0,
        equity_difference=0,
        equity_difference_pct=0,
        total_trades=trade_count,
        impulsive_trades=0,
        disciplined_trades=0,
        impulsive_loss=0,
        disciplined_gain=0,
        pattern_breakdown={},
        narrative=f"Need at least 5 trades to generate your Trading Twin. You have {trade_count} trades in the last {days} days.",
        key_insight="Keep trading on your demo account, and your Twin will have enough data to reveal your patterns.",
        analysis_period_days=days,
    )
