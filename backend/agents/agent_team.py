"""
Agent Team Pipeline for TradeIQ
5 Agents working in sequence:
  1. Market Monitor       → detects volatility events (Redis-cached price delta)
  2. Analyst              → root-cause analysis of the event
  3. Portfolio Advisor     → personalised interpretation for user holdings
  3.5 Behavioral Sentinel → fuses market event + user's behavioral history (WOW MOMENT)
  4. Content Creator       → generates English market commentary for Bluesky

Each agent has a clear input/output contract so they can be tested
independently or chained via `run_pipeline()`.
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.llm_client import get_llm_client
from agents.prompts import MASTER_COMPLIANCE_RULES
from market.tools import (
    fetch_price_data,
    fetch_price_history,
    search_news,
    get_sentiment,
)
from market.cache import get_cached_price, set_cached_price


# ─── Data contracts between agents ───────────────────────────────────

@dataclass
class VolatilityEvent:
    """Output of Market Monitor Agent."""
    instrument: str
    current_price: Optional[float]
    price_change_pct: float
    direction: str  # "spike" | "drop"
    magnitude: str  # "high" | "medium"
    detected_at: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()


@dataclass
class AnalysisReport:
    """Output of Analyst Agent."""
    instrument: str
    event_summary: str
    root_causes: List[str]
    news_sources: List[Dict[str, str]]
    sentiment: str          # "bullish" | "bearish" | "neutral"
    sentiment_score: float  # -1.0 to 1.0
    key_data_points: List[str]
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class PersonalizedInsight:
    """Output of Portfolio Advisor Agent."""
    instrument: str
    impact_summary: str
    affected_positions: List[Dict[str, Any]]
    risk_assessment: str    # "high" | "medium" | "low"
    suggestions: List[str]  # educational, never predictive
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class BehavioralSentinelInsight:
    """Output of Behavioral Sentinel Agent (Stage 3.5) – fuses market + behavior."""
    instrument: str
    market_event_summary: str
    behavioral_context: str       # summary of user's relevant behavioral patterns
    risk_level: str               # "high" | "medium" | "low"
    personalized_warning: str     # the "wow" message combining both
    historical_pattern_match: str # e.g. "3 out of 5 times you revenge-traded after BTC spikes"
    user_stats_snapshot: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class MarketCommentary:
    """Output of Content Creator Agent."""
    post: str
    hashtags: List[str]
    data_points: List[str]
    platform: str = "bluesky"
    published: bool = False
    bluesky_uri: str = ""
    bluesky_url: str = ""
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class CopyTradingRecommendation:
    """Output of Copy Trading Recommendation stage."""
    top_traders: List[Dict[str, Any]]
    ai_recommendation: Optional[Dict[str, Any]] = None
    compatibility_scores: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class PipelineResult:
    """Full pipeline output – every stage's result bundled together."""
    status: str  # "success" | "partial" | "error"
    volatility_event: Optional[Dict[str, Any]] = None
    analysis_report: Optional[Dict[str, Any]] = None
    personalized_insight: Optional[Dict[str, Any]] = None
    sentinel_insight: Optional[Dict[str, Any]] = None
    market_commentary: Optional[Dict[str, Any]] = None
    copytrading_recommendation: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    pipeline_started_at: str = ""
    pipeline_finished_at: str = ""

    def __post_init__(self):
        if not self.pipeline_started_at:
            self.pipeline_started_at = datetime.now().isoformat()


# ─── Agent 1: Market Monitor ─────────────────────────────────────────

MONITOR_INSTRUMENTS = [
    "BTC/USD", "ETH/USD", "Volatility 75", "Volatility 100",
    "EUR/USD", "GBP/USD", "GOLD",
]

# Threshold (%) for volatility detection per asset class
_THRESHOLDS = {
    "BTC/USD": 3.0,
    "ETH/USD": 4.0,
    "Volatility 75": 2.0,
    "Volatility 100": 2.0,
    "default": 0.5,
}


def _threshold(instrument: str) -> float:
    return _THRESHOLDS.get(instrument, _THRESHOLDS["default"])


def market_monitor_detect(
    instruments: Optional[List[str]] = None,
    custom_event: Optional[Dict[str, Any]] = None,
) -> Optional[VolatilityEvent]:
    """
    Agent 1 – Market Monitor.

    Scans instruments for significant price movements using Redis-cached
    price comparison for real delta detection.
    Can also accept a *custom_event* dict for manual/demo triggers.

    Returns the most significant VolatilityEvent found, or None.
    """
    # ── Manual / demo trigger ──
    if custom_event:
        return VolatilityEvent(
            instrument=custom_event.get("instrument", "BTC/USD"),
            current_price=custom_event.get("price"),
            price_change_pct=custom_event.get("change_pct", 5.0),
            direction="spike" if custom_event.get("change_pct", 5.0) > 0 else "drop",
            magnitude="high" if abs(custom_event.get("change_pct", 5.0)) >= 3.0 else "medium",
            raw_data=custom_event,
        )

    # ── Automatic scan with Redis price caching ──
    instruments = instruments or MONITOR_INSTRUMENTS
    events: List[VolatilityEvent] = []
    # Track all scanned instruments so we can fallback to the largest mover
    all_scanned: List[VolatilityEvent] = []

    for inst in instruments:
        try:
            price_data = fetch_price_data(inst)
            price = price_data.get("price")
            if price is None:
                continue

            # Get previous price from Redis cache
            previous_price = get_cached_price(inst)

            if previous_price is not None and previous_price > 0:
                # Real price change calculation
                change_pct = ((price - previous_price) / previous_price) * 100
            else:
                # First run fallback: use recent price history
                history = fetch_price_history(inst, timeframe="5m", count=12)
                change_pct = history.get("change_percent", 0.0)

            # Always update the cached price
            set_cached_price(inst, price, ttl_seconds=300)

            ve = VolatilityEvent(
                instrument=inst,
                current_price=price,
                price_change_pct=round(change_pct, 2),
                direction="spike" if change_pct > 0 else "drop",
                magnitude="medium",
                raw_data={
                    **price_data,
                    "previous_price": previous_price,
                    "source": "redis_delta",
                },
            )
            all_scanned.append(ve)

            threshold = _threshold(inst)
            if abs(change_pct) >= threshold:
                ve.magnitude = "high" if abs(change_pct) >= threshold * 2 else "medium"
                events.append(ve)
        except Exception as exc:
            print(f"[MarketMonitor] Error scanning {inst}: {exc}")

    if events:
        # Return the most significant event above threshold
        events.sort(key=lambda e: abs(e.price_change_pct), reverse=True)
        return events[0]

    # Fallback: no instrument exceeded its threshold, but we still want
    # the pipeline to run in auto-scan mode. Pick the largest mover and
    # flag it as a low-magnitude observation so the rest of the pipeline
    # can still produce useful analysis.
    if all_scanned:
        all_scanned.sort(key=lambda e: abs(e.price_change_pct), reverse=True)
        best = all_scanned[0]
        best.magnitude = "medium"
        best.raw_data["source"] = "auto_fallback"
        return best

    return None


# ─── Agent 2: Analyst ─────────────────────────────────────────────────

_ANALYST_SYSTEM = f"""You are TradeIQ's Senior Market Analyst.
Given a volatility event, determine the ROOT CAUSES using news, sentiment,
and market context. Be specific and cite sources.

{MASTER_COMPLIANCE_RULES}

Output a JSON object:
{{
  "event_summary": "<1 sentence describing what happened>",
  "root_causes": ["cause 1", "cause 2", ...],
  "key_data_points": ["data point 1", "data point 2", ...],
  "sentiment": "bullish" | "bearish" | "neutral",
  "sentiment_score": <float -1.0 to 1.0>
}}
"""


def analyst_analyze(event: VolatilityEvent) -> AnalysisReport:
    """
    Agent 2 – Analyst.

    Takes a VolatilityEvent and produces a structured AnalysisReport
    by combining news search, sentiment analysis, and LLM reasoning.
    """
    # Gather context data
    news = search_news(event.instrument, limit=5)
    sentiment = get_sentiment(event.instrument)

    news_context = "\n".join(
        f"- [{a.get('source', '?')}] {a.get('title', 'N/A')}: {(a.get('description') or '')[:120]}"
        for a in news[:5]
    ) or "No recent news found."

    prompt = f"""Volatility Event detected:
- Instrument: {event.instrument}
- Current Price: {event.current_price}
- Change: {event.price_change_pct:+.2f}%
- Direction: {event.direction}
- Magnitude: {event.magnitude}

Sentiment Data: {json.dumps(sentiment, default=str)}

Recent News:
{news_context}

Analyze the root causes of this volatility event. Return JSON only."""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=_ANALYST_SYSTEM,
            user_message=prompt,
            temperature=0.4,
            max_tokens=600,
        )
        parsed = _parse_json(response)

        return AnalysisReport(
            instrument=event.instrument,
            event_summary=parsed.get("event_summary", f"{event.instrument} moved {event.price_change_pct:+.2f}%"),
            root_causes=parsed.get("root_causes", ["Unable to determine specific causes"]),
            news_sources=[{"title": a.get("title", ""), "url": a.get("url", ""), "source": a.get("source", "")} for a in news[:5]],
            sentiment=parsed.get("sentiment", sentiment.get("sentiment", "neutral")),
            sentiment_score=float(parsed.get("sentiment_score", sentiment.get("score", 0.0))),
            key_data_points=parsed.get("key_data_points", []),
        )
    except Exception as exc:
        print(f"[Analyst] Error: {exc}")
        return AnalysisReport(
            instrument=event.instrument,
            event_summary=f"{event.instrument} experienced a {event.magnitude} {event.direction} of {event.price_change_pct:+.2f}%",
            root_causes=["Analysis unavailable – LLM error"],
            news_sources=[{"title": a.get("title", ""), "url": a.get("url", "")} for a in news[:3]],
            sentiment=sentiment.get("sentiment", "neutral"),
            sentiment_score=float(sentiment.get("score", 0.0)),
            key_data_points=[f"Price: {event.current_price}"],
        )


# ─── Agent 3: Portfolio Advisor ────────────────────────────────────────

_ADVISOR_SYSTEM = f"""You are TradeIQ's Portfolio Advisor.
Given a market analysis report AND a user's portfolio, provide a
personalised impact assessment. Be educational, not predictive.

{MASTER_COMPLIANCE_RULES}

Output a JSON object:
{{
  "impact_summary": "<1-2 sentences on how this event relates to the user's positions>",
  "risk_assessment": "high" | "medium" | "low",
  "suggestions": ["educational suggestion 1", "suggestion 2", ...]
}}
"""


def portfolio_advisor_interpret(
    report: AnalysisReport,
    user_portfolio: Optional[List[Dict[str, Any]]] = None,
) -> PersonalizedInsight:
    """
    Agent 3 – Portfolio Advisor.

    Takes an AnalysisReport + user portfolio and produces a
    PersonalizedInsight with impact assessment and educational suggestions.
    """
    # Default demo portfolio if none provided
    if not user_portfolio:
        user_portfolio = [
            {"instrument": "EUR/USD", "direction": "long", "size": 1.0, "entry_price": 1.0830, "pnl": 12.50},
            {"instrument": "BTC/USD", "direction": "long", "size": 0.1, "entry_price": 95000, "pnl": 250.00},
            {"instrument": "GOLD", "direction": "short", "size": 0.5, "entry_price": 2860, "pnl": -15.00},
        ]

    # Find positions related to the event instrument
    affected = [
        p for p in user_portfolio
        if p.get("instrument", "").upper() == report.instrument.upper()
        or report.instrument.upper() in p.get("instrument", "").upper()
    ]

    portfolio_context = json.dumps(user_portfolio, indent=2)
    affected_context = json.dumps(affected, indent=2) if affected else "No directly affected positions."

    prompt = f"""Market Analysis Report:
- Instrument: {report.instrument}
- Event: {report.event_summary}
- Root Causes: {'; '.join(report.root_causes)}
- Sentiment: {report.sentiment} (score: {report.sentiment_score})
- Key Data Points: {'; '.join(report.key_data_points)}

User Portfolio:
{portfolio_context}

Directly Affected Positions:
{affected_context}

Provide a personalised impact assessment. Return JSON only."""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=_ADVISOR_SYSTEM,
            user_message=prompt,
            temperature=0.5,
            max_tokens=500,
        )
        parsed = _parse_json(response)

        return PersonalizedInsight(
            instrument=report.instrument,
            impact_summary=parsed.get("impact_summary", "Impact assessment unavailable."),
            affected_positions=affected,
            risk_assessment=parsed.get("risk_assessment", "medium"),
            suggestions=parsed.get("suggestions", ["Review your position sizing."]),
        )
    except Exception as exc:
        print(f"[PortfolioAdvisor] Error: {exc}")
        return PersonalizedInsight(
            instrument=report.instrument,
            impact_summary=f"The {report.instrument} event may relate to your current positions.",
            affected_positions=affected,
            risk_assessment="medium",
            suggestions=["Consider reviewing your exposure to this instrument."],
        )


# ─── Agent 3.5: Behavioral Sentinel ────────────────────────────────────

_SENTINEL_SYSTEM = f"""You are TradeIQ's Behavioral Sentinel — a unique AI that combines
real-time market events with a trader's personal behavioral history.

Your job: When a market event happens, tell the trader what THEY specifically
tend to do in these situations, based on THEIR actual trading data.

{MASTER_COMPLIANCE_RULES}

Additional rules:
- Reference the trader's specific patterns with data ("3 out of 5 times...")
- Be warm but direct about behavioral risks
- Never shame — frame as awareness
- Connect the market event to the behavioral pattern explicitly
- If no patterns are detected, provide encouraging feedback

Output a JSON object:
{{
  "behavioral_context": "<summary of relevant behavioral patterns>",
  "risk_level": "high" | "medium" | "low",
  "personalized_warning": "<the key message connecting market event + behavior>",
  "historical_pattern_match": "<specific pattern with numbers>"
}}
"""


def behavioral_sentinel_analyze(
    event: VolatilityEvent,
    report: AnalysisReport,
    user_id: Optional[str] = None,
) -> BehavioralSentinelInsight:
    """
    Agent 3.5 – Behavioral Sentinel.

    Fuses a market volatility event with the user's behavioral history
    to produce a personalized, context-aware warning.

    This is the WOW MOMENT: "The market just did X, and based on your
    history, you tend to Y in these situations."
    """
    from behavior.tools import analyze_trade_patterns, get_trading_statistics

    # Default demo user if none specified
    demo_user_id = user_id or "d1000000-0000-0000-0000-000000000001"

    # Fetch behavioral data
    try:
        patterns = analyze_trade_patterns(demo_user_id, hours=168)  # 7 days
        stats = get_trading_statistics(demo_user_id, days=30)
    except Exception as exc:
        print(f"[Sentinel] Error fetching behavioral data: {exc}")
        patterns = {"patterns": {}, "summary": "No data available", "trade_count": 0}
        stats = {"total_trades": 0, "win_rate": 0}

    # Build the fusion prompt
    behavioral_summary = patterns.get("summary", "No patterns detected")
    pattern_details = []
    p = patterns.get("patterns", {})
    for pattern_name in ["revenge_trading", "overtrading", "loss_chasing", "time_patterns"]:
        pd = p.get(pattern_name, {})
        if isinstance(pd, dict) and pd.get("detected"):
            pattern_details.append(
                f"- {pattern_name}: {pd.get('details', 'detected')} "
                f"(severity: {pd.get('severity', 'unknown')})"
            )

    pattern_context = "\n".join(pattern_details) if pattern_details else "No concerning patterns in recent history."

    prompt = f"""MARKET EVENT:
- Instrument: {event.instrument}
- Price Change: {event.price_change_pct:+.2f}% ({event.direction})
- Magnitude: {event.magnitude}
- Analysis: {report.event_summary}
- Root Causes: {'; '.join(report.root_causes[:3])}

USER'S BEHAVIORAL PROFILE (last 30 days):
- Total trades: {stats.get('total_trades', 0)}
- Win rate: {stats.get('win_rate', 0):.1f}%
- Total P&L: ${stats.get('total_pnl', 0):.2f}
- Best instrument: {stats.get('best_instrument', 'N/A')}
- Worst instrument: {stats.get('worst_instrument', 'N/A')}

RECENT BEHAVIORAL PATTERNS (7 days):
{behavioral_summary}
{pattern_context}

Given this market event and this trader's behavioral profile, generate a
personalized behavioral warning. Connect the dots between what's happening
in the market and what this trader tends to do in these situations.
Return JSON only."""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=_SENTINEL_SYSTEM,
            user_message=prompt,
            temperature=0.5,
            max_tokens=500,
        )
        parsed = _parse_json(response)

        return BehavioralSentinelInsight(
            instrument=event.instrument,
            market_event_summary=report.event_summary,
            behavioral_context=parsed.get("behavioral_context", behavioral_summary),
            risk_level=parsed.get("risk_level", "medium"),
            personalized_warning=parsed.get(
                "personalized_warning",
                f"Market event on {event.instrument}: check your recent patterns.",
            ),
            historical_pattern_match=parsed.get(
                "historical_pattern_match",
                "Insufficient data for pattern matching.",
            ),
            user_stats_snapshot=stats,
        )
    except Exception as exc:
        print(f"[Sentinel] LLM Error: {exc}")
        return BehavioralSentinelInsight(
            instrument=event.instrument,
            market_event_summary=report.event_summary,
            behavioral_context=behavioral_summary,
            risk_level="medium",
            personalized_warning=(
                f"{event.instrument} moved {event.price_change_pct:+.2f}%. "
                f"Review your trading patterns."
            ),
            historical_pattern_match="Analysis unavailable.",
            user_stats_snapshot=stats,
        )


# ─── Agent 4: Content Creator ─────────────────────────────────────────

_CONTENT_SYSTEM = f"""You are TradeIQ's Social Content Creator.
Create English Bluesky market commentary posts.

{MASTER_COMPLIANCE_RULES}

Requirements:
- Each post MUST be <= 300 characters
- Include specific data points (prices, percentages)
- Use 1-2 relevant emojis
- Include 2-3 hashtags
- End with "📊 Analysis by TradeIQ | Not financial advice"
- NEVER predict or recommend

Output a JSON object:
{{
  "post": "<English post <= 300 chars>",
  "hashtags": ["#tag1", "#tag2"],
  "data_points": ["point1", "point2"]
}}
"""


def content_creator_generate(
    report: AnalysisReport,
    insight: Optional[PersonalizedInsight] = None,
) -> MarketCommentary:
    """
    Agent 4 – Content Creator.

    Takes an AnalysisReport (and optionally a PersonalizedInsight)
    and produces English Bluesky market commentary posts.
    """
    insight_context = ""
    if insight:
        insight_context = f"""
Personalised Context:
- Impact: {insight.impact_summary}
- Risk: {insight.risk_assessment}
"""

    prompt = f"""Create Bluesky market commentary post based on:

Analysis Report:
- Instrument: {report.instrument}
- Event: {report.event_summary}
- Root Causes: {'; '.join(report.root_causes[:3])}
- Sentiment: {report.sentiment} (score: {report.sentiment_score})
- Key Data: {'; '.join(report.key_data_points[:3])}
- Sources: {', '.join(s.get('source', '') for s in report.news_sources[:3])}
{insight_context}

Generate an English Bluesky post <= 300 chars. Return JSON only."""

    compliance_tag = "📊 Analysis by TradeIQ | Not financial advice"

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt=_CONTENT_SYSTEM,
            user_message=prompt,
            temperature=0.7,
            max_tokens=500,
        )
        parsed = _parse_json(response)

        post = parsed.get("post", "")

        # Ensure compliance tag (check core text without emoji)
        if "Analysis by TradeIQ" not in post:
            if len(post) + len(compliance_tag) + 2 <= 300:
                post = post.rstrip() + f"\n{compliance_tag}"

        # Truncate to 300 chars (Bluesky limit)
        if len(post) > 300:
            post = post[:297] + "..."

        return MarketCommentary(
            post=post,
            hashtags=parsed.get("hashtags", ["#TradeIQ", "#Markets"]),
            data_points=parsed.get("data_points", []),
        )
    except Exception as exc:
        print(f"[ContentCreator] Error: {exc}")
        return MarketCommentary(
            post=f"📊 {report.instrument} moved {report.sentiment}. {compliance_tag}",
            hashtags=["#TradeIQ", "#Markets"],
            data_points=[report.event_summary],
        )


# ─── Bluesky Publisher ────────────────────────────────────────────────

def publish_to_bluesky(commentary: MarketCommentary) -> Dict[str, Any]:
    """
    Publish a MarketCommentary post to Bluesky via AT Protocol.

    Returns dict with published/bluesky_uri/bluesky_url fields.
    """
    from content.bluesky import BlueskyPublisher

    publisher = BlueskyPublisher()
    result = publisher.post(commentary.post)

    return {
        "published": True,
        "bluesky_uri": result.get("uri", ""),
        "bluesky_url": result.get("url", ""),
    }


# ─── Pipeline Orchestrator ────────────────────────────────────────────

def run_pipeline(
    instruments: Optional[List[str]] = None,
    custom_event: Optional[Dict[str, Any]] = None,
    user_portfolio: Optional[List[Dict[str, Any]]] = None,
    skip_content: bool = False,
    user_id: Optional[str] = None,
) -> PipelineResult:
    """
    Run the full Agent Team pipeline:
      Monitor -> Analyst -> Advisor -> Sentinel -> Content Creator

    Args:
        instruments: Instruments to scan (default: major pairs)
        custom_event: Manual event trigger (bypasses monitor scan)
        user_portfolio: User positions for personalised insight
        skip_content: If True, skip content generation step
        user_id: User UUID for behavioral sentinel (enables Stage 3.5)

    Returns:
        PipelineResult with all stages' outputs
    """
    result = PipelineResult(status="in_progress")

    # ── Stage 1: Market Monitor ──
    try:
        event = market_monitor_detect(
            instruments=instruments,
            custom_event=custom_event,
        )
        if event is None:
            result.status = "no_event"
            result.errors.append("No significant volatility detected.")
            result.pipeline_finished_at = datetime.now().isoformat()
            return result

        result.volatility_event = asdict(event)
    except Exception as exc:
        result.status = "error"
        result.errors.append(f"Monitor error: {exc}")
        result.pipeline_finished_at = datetime.now().isoformat()
        return result

    # ── Stage 2: Analyst ──
    try:
        report = analyst_analyze(event)
        result.analysis_report = asdict(report)
    except Exception as exc:
        result.status = "partial"
        result.errors.append(f"Analyst error: {exc}")
        result.pipeline_finished_at = datetime.now().isoformat()
        return result

    # ── Stage 3: Portfolio Advisor ──
    try:
        insight = portfolio_advisor_interpret(report, user_portfolio)
        result.personalized_insight = asdict(insight)
    except Exception as exc:
        result.status = "partial"
        result.errors.append(f"Advisor error: {exc}")
        # Continue to sentinel/content even if advisor fails
        insight = None

    # ── Stage 3.5: Behavioral Sentinel ──
    sentinel = None
    if user_id:
        try:
            sentinel = behavioral_sentinel_analyze(event, report, user_id)
            result.sentinel_insight = asdict(sentinel)
        except Exception as exc:
            result.errors.append(f"Sentinel error: {exc}")

    # ── Stage 4: Content Creator ──
    if not skip_content:
        try:
            commentary = content_creator_generate(report, insight)
            result.market_commentary = asdict(commentary)
        except Exception as exc:
            result.status = "partial"
            result.errors.append(f"Content error: {exc}")

    # ── Stage 5: Copy Trading Recommendation (optional) ──
    if user_id:
        try:
            recommendation = copytrading_recommend(user_id)
            result.copytrading_recommendation = asdict(recommendation)
        except Exception as exc:
            result.errors.append(f"CopyTrading error: {exc}")

    # ── Stage 6: Publish to Bluesky ──
    if not skip_content and result.market_commentary:
        try:
            publish_result = publish_to_bluesky(commentary)
            result.market_commentary.update(publish_result)
        except Exception as exc:
            result.errors.append(f"Publish error: {exc}")

    # Finalise
    if not result.errors:
        result.status = "success"
    elif result.analysis_report and result.market_commentary:
        result.status = "success"  # all critical stages passed
    else:
        result.status = "partial"

    result.pipeline_finished_at = datetime.now().isoformat()
    return result


# ─── Copy Trading Recommendation ─────────────────────────────────────

def copytrading_recommend(user_id: str) -> CopyTradingRecommendation:
    """
    Stage 5 – Copy Trading Recommendation.

    Fetches top traders and runs AI compatibility analysis
    against the user's trading profile.
    """
    from copytrading.tools import get_top_traders, recommend_trader

    try:
        traders_result = get_top_traders(limit=5)
        top_traders = traders_result.get("traders", [])
    except Exception:
        top_traders = []

    ai_rec = None
    try:
        ai_rec = recommend_trader(user_id)
    except Exception as exc:
        print(f"[CopyTrading] Recommendation error: {exc}")

    return CopyTradingRecommendation(
        top_traders=top_traders,
        ai_recommendation=ai_rec,
    )


# ─── Helpers ──────────────────────────────────────────────────────────

def _parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, stripping markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(cleaned)
