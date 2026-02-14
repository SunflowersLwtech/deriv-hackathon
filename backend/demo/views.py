"""
Demo scenario management for hackathon
Loads demo scenarios from Supabase demo_scenarios table
"""
import logging
import json
from datetime import timedelta
from django.utils import timezone
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from behavior.models import UserProfile, Trade


DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001"
logger = logging.getLogger(__name__)


BUILTIN_SCENARIOS = {
    "revenge_trading": {
        "description": "Revenge Trading — rapid losses trigger emotional re-entry",
        "expected_detection": "revenge_trading",
        "expected_nudge": "You appear to be revenge trading after losses. Consider stepping away.",
        "trade_sequence": [
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 97500, "exit_price": 97300, "pnl": -200, "minutes_offset": 0, "duration_seconds": 300},
            {"instrument": "BTC/USD", "direction": "sell", "entry_price": 97350, "exit_price": 97500, "pnl": -150, "minutes_offset": 2, "duration_seconds": 180},
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 97600, "exit_price": 97420, "pnl": -180, "minutes_offset": 4, "duration_seconds": 120},
            {"instrument": "BTC/USD", "direction": "sell", "entry_price": 97400, "exit_price": 97520, "pnl": -120, "minutes_offset": 6, "duration_seconds": 90},
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 97550, "exit_price": 97450, "pnl": -100, "minutes_offset": 7, "duration_seconds": 60},
        ],
    },
    "overtrading": {
        "description": "Overtrading — excessive trade frequency in a single session",
        "expected_detection": "overtrading",
        "expected_nudge": "You've placed many trades in a short period. Consider slowing down.",
        "trade_sequence": [
            {"instrument": "Volatility 75", "direction": "buy" if i % 2 == 0 else "sell", "entry_price": 900000, "exit_price": 900000 + ((-1) ** (i % 3)) * 500, "pnl": (-1) ** (i % 3) * 50, "minutes_offset": i * 2, "duration_seconds": 60}
            for i in range(15)
        ],
    },
    "loss_chasing": {
        "description": "Loss Chasing — increasing position sizes after consecutive losses",
        "expected_detection": "loss_chasing",
        "expected_nudge": "You are increasing trade sizes after losses. This is a common pattern to watch.",
        "trade_sequence": [
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 97000, "exit_price": 96900, "pnl": -100, "minutes_offset": 0, "duration_seconds": 600},
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 96800, "exit_price": 96650, "pnl": -150, "minutes_offset": 15, "duration_seconds": 600},
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 96500, "exit_price": 96250, "pnl": -250, "minutes_offset": 30, "duration_seconds": 600},
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 96100, "exit_price": 95750, "pnl": -350, "minutes_offset": 45, "duration_seconds": 600},
        ],
    },
    "healthy_session": {
        "description": "Healthy Session — well-paced trades with good discipline",
        "expected_detection": "none",
        "expected_nudge": "Your trading session looks well-paced. Keep it up!",
        "trade_sequence": [
            {"instrument": "BTC/USD", "direction": "buy", "entry_price": 97000, "exit_price": 97085, "pnl": 85, "minutes_offset": 0, "duration_seconds": 3600},
            {"instrument": "ETH/USD", "direction": "sell", "entry_price": 3100, "exit_price": 3140, "pnl": -40, "minutes_offset": 60, "duration_seconds": 3600},
            {"instrument": "Volatility 75", "direction": "buy", "entry_price": 900000, "exit_price": 900120, "pnl": 120, "minutes_offset": 150, "duration_seconds": 3600},
            {"instrument": "ETH/USD", "direction": "buy", "entry_price": 3050, "exit_price": 3110, "pnl": 60, "minutes_offset": 240, "duration_seconds": 3600},
            {"instrument": "BTC/USD", "direction": "sell", "entry_price": 97200, "exit_price": 97230, "pnl": -30, "minutes_offset": 300, "duration_seconds": 3600},
        ],
    },
}


def _load_scenario_from_db(scenario_name: str):
    """Load scenario from demo_scenarios table, falling back to built-in data."""
    # Try database first
    try:
        if "demo_scenarios" in connection.introspection.table_names():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT trade_sequence, expected_detection, expected_nudge FROM demo_scenarios WHERE scenario_name = %s",
                    [scenario_name],
                )
                row = cursor.fetchone()
            if row:
                trade_sequence = row[0] if isinstance(row[0], list) else json.loads(row[0] or "[]")
                return {
                    "trade_sequence": trade_sequence,
                    "expected_detection": row[1],
                    "expected_nudge": row[2],
                }
    except Exception as exc:
        logger.info("demo_scenarios table unavailable: %s", exc)

    # Fallback to built-in scenarios
    builtin = BUILTIN_SCENARIOS.get(scenario_name)
    if builtin:
        return {
            "trade_sequence": builtin["trade_sequence"],
            "expected_detection": builtin["expected_detection"],
            "expected_nudge": builtin["expected_nudge"],
        }
    return None


def _list_scenarios():
    """List scenarios from database, falling back to built-in data."""
    # Try database first
    try:
        if "demo_scenarios" in connection.introspection.table_names():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT scenario_name, description, expected_detection, expected_nudge FROM demo_scenarios ORDER BY scenario_name"
                )
                rows = cursor.fetchall()
            if rows:
                return [
                    {
                        "name": row[0],
                        "description": row[1],
                        "expected_detection": row[2],
                        "expected_nudge": row[3],
                    }
                    for row in rows
                ]
    except Exception as exc:
        logger.info("demo_scenarios listing unavailable: %s", exc)

    # Fallback to built-in scenarios
    return [
        {
            "name": name,
            "description": data["description"],
            "expected_detection": data["expected_detection"],
            "expected_nudge": data["expected_nudge"],
        }
        for name, data in BUILTIN_SCENARIOS.items()
    ]


class LoadScenarioView(APIView):
    """
    POST /api/demo/load-scenario/
    {"scenario": "revenge_trading"}

    Loads demo trade data from demo_scenarios table and creates trades for demo user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        scenario_name = request.data.get("scenario")
        if not scenario_name:
            scenarios = _list_scenarios()
            scenario_name = scenarios[0]["name"] if scenarios else None
        if not scenario_name:
            return Response(
                {"error": "No scenarios available in demo_scenarios table."},
                status=404,
            )

        # Ensure demo user exists
        demo_user, _ = UserProfile.objects.get_or_create(
            id=DEMO_USER_ID,
            defaults={
                "email": "alex@tradeiq.demo",
                "name": "Alex Demo",
                "preferences": {"theme": "dark"},
                "watchlist": [],
            },
        )

        scenario_data = _load_scenario_from_db(scenario_name)
        if not scenario_data:
            return Response(
                {
                    "error": (
                        f"Scenario '{scenario_name}' not found in demo_scenarios table. "
                        "Please seed demo_scenarios in Supabase/PostgreSQL first."
                    )
                },
                status=404,
            )

        trade_sequence = scenario_data["trade_sequence"]
        expected_detection = scenario_data["expected_detection"]
        expected_nudge = scenario_data["expected_nudge"]

        # Clear old mock trades for this user
        Trade.objects.filter(user=demo_user, is_mock=True).delete()

        # Create trades from scenario
        base_time = timezone.now() - timedelta(minutes=30)
        created_trades = []

        for trade_data in trade_sequence:
            minutes_offset = trade_data.get("minutes_offset", 0)
            opened_at = base_time + timedelta(minutes=minutes_offset)
            duration = trade_data.get("duration_seconds", 60)
            closed_at = opened_at + timedelta(seconds=duration)

            trade = Trade.objects.create(
                user=demo_user,
                instrument=trade_data.get("instrument", "EUR/USD"),
                direction=trade_data.get("direction", "buy"),
                entry_price=trade_data.get("entry_price", 1.0850),
                exit_price=trade_data.get("exit_price", 1.0830),
                pnl=trade_data.get("pnl", 0),
                duration_seconds=duration,
                opened_at=opened_at,
                closed_at=closed_at,
                is_mock=True,
            )
            created_trades.append(str(trade.id))

        watchlist = sorted({t.get("instrument", "") for t in trade_sequence if t.get("instrument")})
        if watchlist:
            demo_user.watchlist = watchlist
            demo_user.save(update_fields=["watchlist"])

        return Response({
            "status": "loaded",
            "scenario": scenario_name,
            "user_id": str(demo_user.id),
            "trades_created": len(created_trades),
            "expected_detection": expected_detection,
            "expected_nudge": expected_nudge,
        })


class ListScenariosView(APIView):
    """
    GET /api/demo/scenarios/
    Lists all available demo scenarios.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"scenarios": _list_scenarios()})


class AnalyzeScenarioView(APIView):
    """
    POST /api/demo/analyze/
    {"scenario": "revenge_trading"}

    Loads a scenario AND runs behavioral analysis, returning the nudge.
    This is the main demo endpoint - load + analyze in one call.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        scenario_name = request.data.get("scenario")
        if not scenario_name:
            scenarios = _list_scenarios()
            scenario_name = scenarios[0]["name"] if scenarios else None
        if not scenario_name:
            return Response(
                {"error": "No scenarios available in demo_scenarios table."},
                status=404,
            )

        # First, load the scenario
        load_view = LoadScenarioView()
        load_view.request = request
        load_response = load_view.post(request)

        if load_response.status_code != 200:
            return load_response

        load_data = load_response.data
        user_id = load_data["user_id"]

        # Now run behavioral analysis
        from behavior.tools import analyze_trade_patterns, generate_behavioral_nudge_with_ai

        analysis = analyze_trade_patterns(user_id, hours=1)

        nudge = None
        if analysis.get("needs_nudge"):
            nudge = generate_behavioral_nudge_with_ai(user_id, analysis)

        return Response({
            "scenario": scenario_name,
            "user_id": user_id,
            "trades_created": load_data["trades_created"],
            "analysis": analysis,
            "nudge": nudge,
            "expected_detection": load_data.get("expected_detection"),
            "expected_nudge": load_data.get("expected_nudge"),
        })


class SeedDemoView(APIView):
    """
    POST /api/demo/seed/
    Seeds demo data: creates demo user and loads default scenario.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Create demo user
        demo_user, created = UserProfile.objects.get_or_create(
            id=DEMO_USER_ID,
            defaults={
                "email": "alex@tradeiq.demo",
                "name": "Alex Demo",
                "preferences": {"theme": "dark"},
                "watchlist": [],
            },
        )

        # Load default scenario
        load_view = LoadScenarioView()
        load_view.request = request
        load_response = load_view.post(request)

        return Response({
            "success": True,
            "message": f"Demo seeded. User: {demo_user.name} ({'created' if created else 'existing'}). Default scenario loaded.",
            "user_id": str(demo_user.id),
        })


class WowMomentView(APIView):
    """
    POST /api/demo/wow-moment/
    {"user_id": "uuid", "instrument": "EUR/USD"}

    The "Wow Moment" demo: combines all 3 pillars in one response.
    1. Market analysis of the instrument
    2. Behavioral insight for the user
    3. Content preview generated from the analysis
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id", DEMO_USER_ID)
        instrument = request.data.get("instrument")
        if not instrument:
            try:
                user = UserProfile.objects.get(id=user_id)
                if isinstance(user.watchlist, list) and user.watchlist:
                    instrument = user.watchlist[0]
                else:
                    last_trade = Trade.objects.filter(user=user).order_by("-opened_at", "-created_at").first()
                    instrument = last_trade.instrument if last_trade else None
            except Exception:
                instrument = None
        if not instrument:
            return Response(
                {"error": "No instrument provided and none found in user watchlist/trade history."},
                status=400,
            )

        results = {}

        # 1. Market Analysis
        try:
            from agents.router import route_market_query
            market_result = route_market_query(
                f"Give me a brief analysis of {instrument} right now. What's happening?"
            )
            results["market_analysis"] = market_result.get("response", "Market analysis unavailable.")
        except Exception as e:
            results["market_analysis"] = f"Market analysis error: {str(e)}"

        # 2. Behavioral Insight
        try:
            from behavior.tools import analyze_trade_patterns, generate_behavioral_nudge_with_ai
            analysis = analyze_trade_patterns(user_id, hours=24)
            if analysis.get("needs_nudge"):
                nudge = generate_behavioral_nudge_with_ai(user_id, analysis)
                results["behavior_insight"] = nudge.get("message", analysis.get("summary", ""))
            else:
                results["behavior_insight"] = analysis.get("summary", "No concerning patterns detected.")
        except Exception as e:
            results["behavior_insight"] = f"Behavioral analysis error: {str(e)}"

        # 2.5 Behavioral Sentinel Fusion (market + behavior cross-analysis)
        try:
            from agents.agent_team import (
                behavioral_sentinel_analyze,
                VolatilityEvent,
                AnalysisReport,
            )
            from dataclasses import asdict

            # Build lightweight event from market analysis
            sentinel_event = VolatilityEvent(
                instrument=instrument,
                current_price=None,
                price_change_pct=0.0,
                direction="spike",
                magnitude="medium",
            )
            sentinel_report = AnalysisReport(
                instrument=instrument,
                event_summary=results.get("market_analysis", "")[:200],
                root_causes=[],
                news_sources=[],
                sentiment="neutral",
                sentiment_score=0.0,
                key_data_points=[],
            )
            sentinel = behavioral_sentinel_analyze(sentinel_event, sentinel_report, user_id)
            results["sentinel_fusion"] = {
                "personalized_warning": sentinel.personalized_warning,
                "behavioral_context": sentinel.behavioral_context,
                "risk_level": sentinel.risk_level,
                "historical_pattern_match": sentinel.historical_pattern_match,
            }
        except Exception as e:
            results["sentinel_fusion"] = f"Sentinel fusion error: {str(e)}"

        # 3. Content Preview
        try:
            from content.tools import generate_draft
            from content.models import AIPersona
            persona = AIPersona.objects.first()
            if persona:
                draft = generate_draft(
                    persona_id=str(persona.id),
                    topic=f"Analysis of {instrument}: {results.get('market_analysis', '')[:100]}",
                    platform="bluesky",
                    max_length=300
                )
                results["content_preview"] = draft.get("content", "Content generation unavailable.")
            else:
                results["content_preview"] = "No persona configured for content generation."
        except Exception as e:
            results["content_preview"] = f"Content generation error: {str(e)}"

        # 4. Economic Calendar (Finnhub)
        try:
            from market.tools import fetch_economic_calendar
            calendar = fetch_economic_calendar()
            high_impact = [
                ev for ev in calendar.get("events", [])
                if ev.get("impact") in ("high", "3", 3)
            ][:5]
            results["economic_calendar"] = {
                "high_impact_events": high_impact,
                "total_events": calendar.get("count", 0),
            }
        except Exception as e:
            results["economic_calendar"] = f"Calendar error: {str(e)}"

        # 5. Bluesky Social Sentiment
        try:
            from content.bluesky import BlueskyPublisher
            publisher = BlueskyPublisher()
            social_posts = publisher.search_posts(instrument.replace("/", " "), limit=5)
            results["social_sentiment"] = {
                "platform": "bluesky",
                "query": instrument,
                "posts": social_posts[:3],
                "total_found": len(social_posts),
            }
        except Exception as e:
            results["social_sentiment"] = f"Social search error: {str(e)}"

        results["disclaimer"] = "This is analysis, not financial advice. All data is for educational purposes."

        return Response(results)


# ─── Demo Trigger & Health ─────────────────────────────────────────


class DemoTriggerEventView(APIView):
    """
    POST /api/demo/trigger-event/
    Manually trigger a simulated market event to activate the MarketMonitor push chain.
    Used when real markets are calm during demo.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "BTC/USD")
        change_pct = float(request.data.get("change_pct", -3.2))
        price = float(request.data.get("price", 95000))

        from market.monitor import get_monitor
        monitor = get_monitor()
        monitor._handle_volatility_event(
            instrument=instrument,
            current_price=price,
            previous_price=price * (1 - change_pct / 100),
            change_pct=change_pct,
        )
        return Response({
            "status": "triggered",
            "instrument": instrument,
            "change_pct": change_pct,
            "message": "Market event simulated. Pipeline running, WebSocket push pending.",
        })


class DemoHealthView(APIView):
    """
    GET /api/demo/health/
    Check all demo dependencies are ready before presentation.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from demo.health import check_demo_readiness
        return Response(check_demo_readiness())


# ─── Demo Script Views ──────────────────────────────────────────────

class DemoScriptListView(APIView):
    """GET /api/demo/scripts/ — List available demo scripts."""
    permission_classes = [AllowAny]

    def get(self, request):
        from demo.demo_script import list_scripts
        return Response({"scripts": list_scripts()})


class DemoScriptDetailView(APIView):
    """GET /api/demo/scripts/<name>/ — Get a specific demo script with steps."""
    permission_classes = [AllowAny]

    def get(self, request, name):
        from demo.demo_script import get_script
        from dataclasses import asdict
        script = get_script(name)
        if not script:
            return Response({"error": f"Script '{name}' not found"}, status=404)
        return Response(asdict(script))


class DemoRunScriptView(APIView):
    """
    POST /api/demo/run-script/
    {"script_name": "full_showcase", "instrument": "BTC/USD", "user_id": "..."}

    Executes all steps of a demo script sequentially and returns results.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        import time
        import requests as http_requests
        from demo.demo_script import get_script
        from dataclasses import asdict

        script_name = request.data.get("script_name", "full_showcase")
        script = get_script(script_name)
        if not script:
            return Response({"error": f"Script '{script_name}' not found"}, status=404)

        # Determine backend base URL
        host = request.get_host()
        scheme = "https" if request.is_secure() else "http"
        base_url = f"{scheme}://{host}"

        results = []
        total_start = time.time()

        for step in script.steps:
            step_start = time.time()
            step_result = {
                "step_number": step.step_number,
                "title": step.title,
                "narration": step.narration,
                "wow_factor": step.wow_factor,
                "status": "success",
                "result": {},
                "duration_ms": 0,
            }

            try:
                url = f"{base_url}{step.api_endpoint}"
                if step.api_params:
                    resp = http_requests.post(
                        url,
                        json=step.api_params,
                        timeout=30,
                        headers={"Content-Type": "application/json"},
                    )
                else:
                    resp = http_requests.get(url, timeout=30)

                step_result["result"] = resp.json() if resp.status_code == 200 else {"error": resp.text[:200]}
                step_result["status"] = "success" if resp.status_code == 200 else "error"
            except Exception as exc:
                step_result["status"] = "error"
                step_result["result"] = {"error": str(exc)}

            step_result["duration_ms"] = int((time.time() - step_start) * 1000)
            results.append(step_result)

        total_ms = int((time.time() - total_start) * 1000)
        has_errors = any(r["status"] == "error" for r in results)

        return Response({
            "script_name": script_name,
            "opening_line": script.opening_line,
            "closing_line": script.closing_line,
            "status": "partial" if has_errors else "success",
            "steps": results,
            "total_duration_ms": total_ms,
        })


class DemoRunScriptV2View(APIView):
    """
    POST /api/demo/run-script-v2/
    {"script_name": "championship_run"}

    Executes V2 demo script with fallback support.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        import time
        import requests as http_requests
        from demo.demo_script_v2 import get_script_v2
        from demo.fallback import execute_with_fallback

        script_name = request.data.get("script_name", "championship_run")
        script = get_script_v2(script_name)
        if not script:
            return Response({"error": f"Script '{script_name}' not found"}, status=404)

        host = request.get_host()
        scheme = "https" if request.is_secure() else "http"
        base_url = f"{scheme}://{host}"

        results = []
        total_start = time.time()

        for step in script.steps:
            step_start = time.time()
            step_result = {
                "step_number": step.step_number,
                "title": step.title,
                "narration": step.narration,
                "wow_factor": step.wow_factor,
                "act": step.act,
                "visual_cue": step.visual_cue,
                "status": "success",
                "result": {},
                "duration_ms": 0,
            }

            if step.api_endpoint == "NONE":
                step_result["result"] = {"message": "Closing narration — no API call"}
            else:
                try:
                    url = f"{base_url}{step.api_endpoint}"
                    if step.api_params:
                        resp = http_requests.post(
                            url,
                            json=step.api_params,
                            timeout=30,
                            headers={"Content-Type": "application/json"},
                        )
                    else:
                        resp = http_requests.get(url, timeout=30)

                    step_result["result"] = resp.json() if resp.status_code == 200 else {"error": resp.text[:200]}
                    step_result["status"] = "success" if resp.status_code == 200 else "error"
                except Exception as exc:
                    step_result["status"] = "error"
                    step_result["result"] = {"error": str(exc)}
                    step_result["fallback_used"] = step.fallback

            step_result["duration_ms"] = int((time.time() - step_start) * 1000)
            results.append(step_result)

        total_ms = int((time.time() - total_start) * 1000)
        has_errors = any(r["status"] == "error" for r in results)

        return Response({
            "script_name": script_name,
            "version": "v2",
            "opening_narration": script.opening_narration,
            "closing_narration": script.closing_narration,
            "status": "partial" if has_errors else "success",
            "steps": results,
            "total_duration_ms": total_ms,
        })
