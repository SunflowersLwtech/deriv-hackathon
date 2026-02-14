"""
Live Narrator — real-time trade commentary like a sports commentator.

When a user trades, the narrator generates a one-liner and pushes it
to the frontend via WebSocket.
"""
from typing import Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

logger = logging.getLogger("tradeiq.narrator")


def narrate_trade_event(
    user_id: str,
    trade_data: Dict[str, Any],
    event_type: str = "new_trade",
) -> Dict[str, Any]:
    """Generate and push a one-line narration for a trade event."""
    from behavior.tools import get_recent_trades, get_trading_statistics
    from behavior.alerts import check_all_alerts
    from agents.llm_client import get_llm_client

    try:
        recent = get_recent_trades(user_id, hours=4)
        stats = get_trading_statistics(user_id, days=7)
    except Exception:
        recent = {"trades": []}
        stats = {}

    try:
        alerts = check_all_alerts(user_id)
    except Exception:
        alerts = []

    system_prompt = (
        "You are a live trading narrator — think sports commentator meets trading coach.\n\n"
        "Rules:\n"
        "- One sentence only (max 80 characters)\n"
        "- Casual, conversational tone\n"
        "- Point out patterns the trader might not notice\n"
        "- Be supportive for good decisions, gently concerned for risky ones\n"
        "- NEVER give advice or predictions\n"
        "- Use present tense\n\n"
        "Respond with ONLY the narration text, nothing else."
    )

    context = (
        f"Event: {event_type}\n"
        f"Trade: {json.dumps(trade_data)}\n"
        f"Recent trades: {len(recent.get('trades', []))} in last 4 hours\n"
        f"Today's trade count: {stats.get('total_trades', 0)}\n"
        f"Active alerts: {', '.join(a['rule'] for a in alerts) if alerts else 'none'}\n"
        f"Win rate (7d): {stats.get('win_rate', 0):.0f}%"
    )

    try:
        llm = get_llm_client()
        narration = llm.simple_chat(system_prompt, context, max_tokens=50)
        narration = narration.strip().strip('"')
        _push_narration(user_id, narration, event_type, trade_data)
        return {"narration": narration, "event_type": event_type}
    except Exception as exc:
        logger.warning("Narration failed: %s", exc)
        return {"narration": "", "error": str(exc)}


def _push_narration(user_id: str, text: str, event_type: str, trade_data: Dict):
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{user_id}",
                {
                    "type": "narrator.message",
                    "message": json.dumps({
                        "type": "narration",
                        "text": text,
                        "event_type": event_type,
                        "instrument": trade_data.get("instrument", ""),
                        "timestamp": trade_data.get("timestamp", ""),
                    }),
                },
            )
    except Exception as exc:
        logger.warning("Narration push failed: %s", exc)
