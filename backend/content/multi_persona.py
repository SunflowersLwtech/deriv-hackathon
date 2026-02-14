"""
Multi-Persona Collaborative Content Engine

Core scenario: same market event, 3 personas post from different angles.

Example: BTC drops 5%
- Calm Analyst: "BTC retracing to $95k support zone. Volume profile suggests..."
- Data Nerd: "BTC 24h stats: -5.2%, volume $48B, funding rate flipping negative..."
- Trading Coach: "Seeing a lot of panic. Remember: your trading plan was made in calm waters..."

Visually impactful in demo — side-by-side display of 3 distinct styles.
"""
from typing import Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MultiPersonaContent:
    """Three-persona collaborative content."""
    event_summary: str
    calm_analyst_post: str
    data_nerd_post: str
    trading_coach_post: str
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


def generate_multi_persona_content(
    event: Dict[str, Any],
) -> MultiPersonaContent:
    """
    Generate content from 3 personas for the same event.

    Args:
        event: {
            "instrument": "BTC/USD",
            "change_pct": -5.2,
            "price": 95000,
            "news_summary": "Fed hawkish signals...",
            "sentiment": "bearish"
        }
    """
    from content.tools import generate_draft

    instrument = event.get("instrument", "BTC/USD")
    change = event.get("change_pct", 0)
    direction = "dropped" if change < 0 else "gained"
    summary = f"{instrument} {direction} {abs(change):.1f}%"

    posts = {}
    for persona_name in ["calm_analyst", "data_nerd", "trading_coach"]:
        result = generate_draft(
            persona_id=persona_name,
            topic=summary,
            platform="bluesky",
            market_context=event,
            style="insight",
        )
        posts[persona_name] = result.get("content", "")

    return MultiPersonaContent(
        event_summary=summary,
        calm_analyst_post=posts.get("calm_analyst", ""),
        data_nerd_post=posts.get("data_nerd", ""),
        trading_coach_post=posts.get("trading_coach", ""),
    )
