"""
Demo Script Engine for TradeIQ Hackathon Pitch
Pre-defined demo scripts that execute pipeline steps sequentially.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class DemoStep:
    step_number: int
    title: str
    narration: str
    api_endpoint: str
    api_params: Dict[str, Any] = field(default_factory=dict)
    expected_duration_sec: int = 10
    wow_factor: str = ""


@dataclass
class DemoScript:
    name: str
    description: str
    total_duration_sec: int
    opening_line: str
    closing_line: str
    steps: List[DemoStep] = field(default_factory=list)


DEMO_SCRIPTS: Dict[str, DemoScript] = {
    "full_showcase": DemoScript(
        name="full_showcase",
        description="Complete 5-agent pipeline: Detection -> Analysis -> Sentinel -> Copy Trading -> Content",
        total_duration_sec=300,
        opening_line="Watch TradeIQ's 5 AI agents work together in real-time — from detecting a market event to generating content, in under 60 seconds.",
        closing_line="That's TradeIQ: 5 AI agents, real Deriv data, one seamless pipeline. Built for the next generation of smart traders.",
        steps=[
            DemoStep(
                step_number=1,
                title="Market Monitor — Volatility Detection",
                narration="Agent 1 scans 7 instruments via Deriv WebSocket API, comparing Redis-cached prices to detect real volatility events.",
                api_endpoint="/api/agents/monitor/",
                api_params={"instruments": ["BTC/USD", "ETH/USD", "Volatility 75"]},
                expected_duration_sec=8,
                wow_factor="Real Deriv API price data, not mocked",
            ),
            DemoStep(
                step_number=2,
                title="Analyst — Root Cause Analysis",
                narration="Agent 2 gathers news, sentiment, and technicals to explain WHY the move happened. Uses DeepSeek-V3 with function calling.",
                api_endpoint="/api/agents/pipeline/",
                api_params={
                    "custom_event": {
                        "instrument": "BTC/USD",
                        "price": 97500,
                        "change_pct": 4.2,
                    },
                    "skip_content": True,
                },
                expected_duration_sec=15,
                wow_factor="LLM + real news + Deriv data fusion",
            ),
            DemoStep(
                step_number=3,
                title="Behavioral Sentinel — Personalized Warning",
                narration="Agent 3.5 fuses the market event with YOUR trading history. 'BTC spiked 4.2%, and 3 out of 5 times you revenge-traded after similar events.'",
                api_endpoint="/api/agents/sentinel/",
                api_params={
                    "instrument": "BTC/USD",
                    "price_change_pct": 4.2,
                    "direction": "spike",
                    "event_summary": "BTC/USD surged 4.2% — largest move in 48 hours",
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                },
                expected_duration_sec=12,
                wow_factor="The 'wow moment' — market + behavior fusion",
            ),
            DemoStep(
                step_number=4,
                title="Copy Trading — AI Trader Matching",
                narration="Agent 6 queries Deriv's Copy Trading API, finds top traders, and runs AI compatibility scoring against your risk profile.",
                api_endpoint="/api/agents/copytrading/",
                api_params={
                    "action": "recommend",
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                },
                expected_duration_sec=10,
                wow_factor="Real Deriv Copy Trading API integration",
            ),
            DemoStep(
                step_number=5,
                title="Content Creator — Bluesky Post",
                narration="Agent 4 generates compliant market commentary, then publishes directly to Bluesky via AT Protocol. Not financial advice — always.",
                api_endpoint="/api/demo/wow-moment/",
                api_params={
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                    "instrument": "BTC/USD",
                },
                expected_duration_sec=15,
                wow_factor="Auto-published to Bluesky with compliance check",
            ),
        ],
    ),
    "behavioral_focus": DemoScript(
        name="behavioral_focus",
        description="Behavioral coaching flow: Deriv Sync -> Pattern Detection -> AI Coaching",
        total_duration_sec=180,
        opening_line="TradeIQ doesn't just analyze markets — it analyzes YOU. Let's see the behavioral coaching pipeline in action.",
        closing_line="That's the future of trading: AI that knows your patterns and helps you trade smarter, not harder.",
        steps=[
            DemoStep(
                step_number=1,
                title="Deriv Trade Sync",
                narration="Loading your recent trading history from Deriv. Every trade is analyzed for behavioral patterns.",
                api_endpoint="/api/demo/load-scenario/",
                api_params={"scenario": "revenge_trading"},
                expected_duration_sec=5,
                wow_factor="Real trade data integration",
            ),
            DemoStep(
                step_number=2,
                title="Pattern Detection",
                narration="AI scans for revenge trading, overtrading, loss chasing, and time-based patterns across your last 7 days of activity.",
                api_endpoint="/api/demo/analyze/",
                api_params={"scenario": "revenge_trading"},
                expected_duration_sec=10,
                wow_factor="Multi-pattern behavioral analysis",
            ),
            DemoStep(
                step_number=3,
                title="AI Coaching Nudge",
                narration="Based on detected patterns, TradeIQ generates a personalized coaching message. Warm, supportive, never preachy.",
                api_endpoint="/api/demo/wow-moment/",
                api_params={
                    "user_id": "d1000000-0000-0000-0000-000000000001",
                    "instrument": "BTC/USD",
                },
                expected_duration_sec=15,
                wow_factor="AI behavioral coaching with empathy",
            ),
        ],
    ),
}


def get_script(name: str) -> Optional[DemoScript]:
    return DEMO_SCRIPTS.get(name)


def list_scripts() -> List[Dict[str, Any]]:
    return [
        {
            "name": s.name,
            "description": s.description,
            "total_duration_sec": s.total_duration_sec,
            "step_count": len(s.steps),
        }
        for s in DEMO_SCRIPTS.values()
    ]
