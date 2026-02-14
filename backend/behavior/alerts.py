"""
Proactive Behavioral Alert System — fires without user action.

Rules:
1. Overtrading: today's trades > 2x daily average
2. Consecutive losses: 3+ losses in a row
3. Bad time trading: active in historically low win-rate hours
4. Long session: trading for 3+ hours without break
5. Weekly drawdown: cumulative weekly loss exceeds threshold
"""
from typing import Dict, Any, List
from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger("tradeiq.alerts")


def check_all_alerts(user_id: str) -> List[Dict[str, Any]]:
    """Run all alert rules and return triggered alerts."""
    alerts: List[Dict[str, Any]] = []
    alerts.extend(_check_overtrading(user_id))
    alerts.extend(_check_consecutive_losses(user_id))
    alerts.extend(_check_bad_time_trading(user_id))
    alerts.extend(_check_session_duration(user_id))
    alerts.extend(_check_weekly_drawdown(user_id))
    return alerts


def _check_overtrading(user_id: str) -> List[Dict[str, Any]]:
    from behavior.models import Trade
    from django.db.models import Count

    today = timezone.now().date()
    today_count = Trade.objects.filter(user_id=user_id, opened_at__date=today).count()

    thirty_days_ago = today - timedelta(days=30)
    historical = (
        Trade.objects.filter(
            user_id=user_id,
            opened_at__date__gte=thirty_days_ago,
            opened_at__date__lt=today,
        )
        .values("opened_at__date")
        .annotate(count=Count("id"))
    )

    if not historical:
        return []

    avg_daily = sum(h["count"] for h in historical) / max(len(historical), 1)
    if avg_daily == 0:
        return []

    ratio = today_count / avg_daily
    if ratio >= 3:
        severity = "high"
    elif ratio >= 2:
        severity = "medium"
    else:
        return []

    return [{
        "rule": "overtrading",
        "severity": severity,
        "message": (
            f"You've made {today_count} trades today — "
            f"{ratio:.1f}x your average of {avg_daily:.0f}. Consider slowing down."
        ),
        "data": {"today_count": today_count, "avg_daily": round(avg_daily, 1), "ratio": round(ratio, 1)},
    }]


def _check_consecutive_losses(user_id: str) -> List[Dict[str, Any]]:
    from behavior.models import Trade

    recent_trades = Trade.objects.filter(user_id=user_id).order_by("-opened_at")[:10]

    consecutive_losses = 0
    total_loss = 0.0
    for trade in recent_trades:
        if trade.pnl is not None and float(trade.pnl) < 0:
            consecutive_losses += 1
            total_loss += abs(float(trade.pnl))
        else:
            break

    if consecutive_losses >= 3:
        severity = "high" if consecutive_losses >= 5 else "medium"
        return [{
            "rule": "consecutive_losses",
            "severity": severity,
            "message": (
                f"Your last {consecutive_losses} trades were losses "
                f"(total ${total_loss:.2f}). A break might help reset your decision-making."
            ),
            "data": {"count": consecutive_losses, "total_loss": round(total_loss, 2)},
        }]
    return []


def _check_bad_time_trading(user_id: str) -> List[Dict[str, Any]]:
    from behavior.models import Trade
    from datetime import datetime

    current_hour = datetime.now().hour

    # Check win rate at current hour over last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    hour_trades = Trade.objects.filter(
        user_id=user_id,
        opened_at__gte=thirty_days_ago,
        opened_at__hour=current_hour,
    )

    total = hour_trades.count()
    if total < 5:
        return []

    wins = sum(1 for t in hour_trades if t.pnl is not None and float(t.pnl) > 0)
    win_rate = (wins / total) * 100

    if win_rate < 35:
        return [{
            "rule": "bad_time",
            "severity": "medium",
            "message": (
                f"Your win rate at {current_hour}:00 is only {win_rate:.0f}%. "
                f"Consider trading during your stronger hours."
            ),
            "data": {"hour": current_hour, "win_rate": round(win_rate, 1)},
        }]
    return []


def _check_session_duration(user_id: str) -> List[Dict[str, Any]]:
    from behavior.models import Trade

    three_hours_ago = timezone.now() - timedelta(hours=3)
    recent_trades = Trade.objects.filter(
        user_id=user_id, opened_at__gte=three_hours_ago
    ).order_by("opened_at")

    if recent_trades.count() < 3:
        return []

    first_trade = recent_trades.first()
    session_minutes = (timezone.now() - first_trade.opened_at).total_seconds() / 60

    if session_minutes >= 180:
        return [{
            "rule": "long_session",
            "severity": "medium",
            "message": (
                f"You've been trading for {session_minutes:.0f} minutes straight. "
                f"Research shows breaks improve decision quality."
            ),
            "data": {"session_minutes": round(session_minutes)},
        }]
    return []


def _check_weekly_drawdown(user_id: str) -> List[Dict[str, Any]]:
    from behavior.models import Trade
    from django.db.models import Sum

    week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
    weekly_pnl = (
        Trade.objects.filter(user_id=user_id, opened_at__date__gte=week_start)
        .aggregate(total=Sum("pnl"))["total"]
    ) or 0

    if float(weekly_pnl) < -200:
        severity = "high" if float(weekly_pnl) < -500 else "medium"
        return [{
            "rule": "weekly_drawdown",
            "severity": severity,
            "message": (
                f"This week's cumulative loss is ${abs(float(weekly_pnl)):.2f}. "
                f"Consider reviewing your strategy before continuing."
            ),
            "data": {"weekly_pnl": round(float(weekly_pnl), 2)},
        }]
    return []
