"""
TradeIQ Demo Script V2 — Audit Fix Edition

Goal: 2-minute demo showcasing all core value
Prerequisite: Market monitor running, demo data loaded

Judge Psychology Model:
- First 15s: decide whether to keep watching
- 30s: form first impression
- 60s: judge Insight and Usefulness
- 90s: judge Craft and Ambition
- 120s: finalize impression
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class DemoStepV2:
    step_number: int
    title: str
    narration: str
    api_endpoint: str
    api_params: Dict[str, Any] = field(default_factory=dict)
    expected_duration_sec: int = 10
    visual_cue: str = ""
    wow_factor: str = ""
    fallback: str = ""
    act: str = ""


@dataclass
class DemoScriptV2:
    name: str
    description: str
    total_duration_sec: int
    opening_narration: str
    closing_narration: str
    steps: List[DemoStepV2] = field(default_factory=list)


DEMO_V2_SCRIPTS: Dict[str, DemoScriptV2] = {
    "championship_run": DemoScriptV2(
        name="championship_run",
        description="TradeIQ Championship Demo — 2 minutes, 7 steps, 4 acts",
        total_duration_sec=120,
        opening_narration=(
            "Every day, millions of retail traders make decisions based on emotion, "
            "not intelligence. TradeIQ changes that. Watch."
        ),
        closing_narration=(
            "TradeIQ: Understand markets. Understand yourself. Share with the world."
        ),
        steps=[
            # ═══ ACT 1: THE HOOK (0:00 - 0:30) ═══
            DemoStepV2(
                step_number=1,
                title="Real-Time Detection",
                narration=(
                    "(No talking — let the system speak) "
                    "Market monitor auto-detects BTC volatility. "
                    "Toast notification appears in top-right corner."
                ),
                api_endpoint="/api/demo/trigger-event/",
                api_params={
                    "instrument": "BTC/USD",
                    "change_pct": -3.2,
                },
                expected_duration_sec=5,
                visual_cue="MarketAlertToast: 'BTC/USD -3.2% | AI Analysis Ready'",
                wow_factor="System discovered the event by itself, not user-triggered",
                fallback="Click demo trigger button to simulate event",
                act="ACT 1: THE HOOK",
            ),
            DemoStepV2(
                step_number=2,
                title="AI Analysis (Streaming)",
                narration=(
                    "(Click notification) TradeIQ's AI analyst is already working. "
                    "Watch it think in real time."
                ),
                api_endpoint="/api/agents/analyst/",
                api_params={
                    "instrument": "BTC/USD",
                    "current_price": 95000,
                    "price_change_pct": -3.2,
                    "direction": "drop",
                    "magnitude": "medium",
                },
                expected_duration_sec=10,
                visual_cue=(
                    "ThinkingProcess shows AI reasoning:\n"
                    "Fetching BTC price... Searching news... Analyzing sentiment...\n"
                    "Then streaming text output"
                ),
                wow_factor="AI thinking process fully transparent + streaming like ChatGPT",
                fallback="Pre-cached analysis result",
                act="ACT 1: THE HOOK",
            ),

            # ═══ ACT 2: THE WOW (0:30 - 1:00) ═══
            DemoStepV2(
                step_number=3,
                title="Behavioral Sentinel",
                narration=(
                    "But here's where TradeIQ is truly different. "
                    "It doesn't just tell you what happened in the market — "
                    "it tells you what YOU are about to do."
                ),
                api_endpoint="/api/agents/sentinel/",
                api_params={
                    "instrument": "BTC/USD",
                    "price_change_pct": -3.2,
                    "direction": "drop",
                    "event_summary": "BTC/USD dropped 3.2% in 2 hours due to Fed signals",
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                },
                expected_duration_sec=8,
                visual_cue=(
                    "Sentinel output: personal behavioral warning\n"
                    "NarratorBar appears at bottom"
                ),
                wow_factor="AI analyzes YOU, not just the market",
                fallback="Pre-loaded demo user behavioral data",
                act="ACT 2: THE WOW",
            ),
            DemoStepV2(
                step_number=4,
                title="Trading Twin Visualization",
                narration=(
                    "(Point at dual curve chart) "
                    "This is your Trading Twin. The red line is you — "
                    "with all your impulse trades. The green line is the you "
                    "who followed discipline. The gap is $1,247."
                ),
                api_endpoint="/api/behavior/trading-twin/",
                api_params={
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                    "days": 30,
                    "starting_equity": 10000,
                },
                expected_duration_sec=12,
                visual_cue=(
                    "TradingTwinChart:\n"
                    "- Two lines animate left-to-right\n"
                    "- Red (impulsive) below green (disciplined)\n"
                    "- Gap area filled green\n"
                    "- Difference counter: $0 -> $1,247\n"
                    "- AI narrative appears"
                ),
                wow_factor="Visual impact + personalization + never-seen feature = peak moment",
                fallback="Pre-computed demo twin data",
                act="ACT 2: THE WOW",
            ),

            # ═══ ACT 3: THE COMPLETE PICTURE (1:00 - 1:40) ═══
            DemoStepV2(
                step_number=5,
                title="Multi-Persona Content Generation",
                narration=(
                    "And while all this is happening, TradeIQ's content engine "
                    "has already turned this market event into social media content. "
                    "Three AI personas, three different voices, same event."
                ),
                api_endpoint="/api/content/multi-persona/",
                api_params={
                    "event": {
                        "instrument": "BTC/USD",
                        "change_pct": -3.2,
                        "price": 95000,
                        "news_summary": "Fed hawkish signals triggered BTC selloff",
                        "sentiment": "bearish",
                    }
                },
                expected_duration_sec=10,
                visual_cue=(
                    "Side-by-side 3 persona posts:\n"
                    "Left: Calm Analyst | Center: Data Nerd | Right: Trading Coach"
                ),
                wow_factor="Same event, 3 personalized interpretations — stunning visual",
                fallback="Pre-generated 3-persona content templates",
                act="ACT 3: THE COMPLETE PICTURE",
            ),
            DemoStepV2(
                step_number=6,
                title="Live Publish to Bluesky",
                narration=(
                    "And this isn't just a mock-up. "
                    "(Click Publish button) "
                    "This post is now live on Bluesky. You can check it right now."
                ),
                api_endpoint="/api/content/publish-bluesky/",
                api_params={
                    "type": "single",
                    "content": "",  # Uses Step 5's generated content
                },
                expected_duration_sec=5,
                visual_cue="Publish button animation -> success state -> Bluesky post link",
                wow_factor="Not demo data — real publish to the public internet",
                fallback="Show previously published post screenshot",
                act="ACT 3: THE COMPLETE PICTURE",
            ),

            # ═══ ACT 4: THE CLOSE (1:40 - 2:00) ═══
            DemoStepV2(
                step_number=7,
                title="The Complete Loop",
                narration=(
                    "In under 2 minutes, TradeIQ detected a market event, "
                    "analyzed why it happened, warned a trader about their specific bias, "
                    "showed them what discipline looks like, "
                    "and published expert commentary to the world. "
                    "That's not a trading tool. That's an AI trading coach. "
                    "Thank you."
                ),
                api_endpoint="NONE",
                api_params={},
                expected_duration_sec=15,
                visual_cue=(
                    "Dashboard panoramic view:\n"
                    "- Market monitor (green pulse)\n"
                    "- Behavior summary\n"
                    "- Trading Twin mini chart\n"
                    "- NarratorBar final line\n"
                    "- 'This system is always running' feel"
                ),
                wow_factor="Complete loop + lingering impression + 'this is real'",
                fallback="Just deliver closing narration",
                act="ACT 4: THE CLOSE",
            ),
        ],
    ),
}


def get_script_v2(name: str) -> Optional[DemoScriptV2]:
    return DEMO_V2_SCRIPTS.get(name)


def list_scripts_v2() -> List[Dict[str, Any]]:
    return [
        {
            "name": s.name,
            "description": s.description,
            "total_duration_sec": s.total_duration_sec,
            "step_count": len(s.steps),
        }
        for s in DEMO_V2_SCRIPTS.values()
    ]
