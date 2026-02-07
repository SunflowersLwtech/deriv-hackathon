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


def _load_scenario_from_db(scenario_name: str):
    """Load scenario from demo_scenarios table; return None if unavailable."""
    try:
        if "demo_scenarios" not in connection.introspection.table_names():
            return None
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT trade_sequence, expected_detection, expected_nudge FROM demo_scenarios WHERE scenario_name = %s",
                [scenario_name],
            )
            row = cursor.fetchone()
    except Exception as exc:
        logger.info("demo_scenarios table unavailable: %s", exc)
        return None

    if not row:
        return None

    trade_sequence = row[0] if isinstance(row[0], list) else json.loads(row[0] or "[]")
    return {
        "trade_sequence": trade_sequence,
        "expected_detection": row[1],
        "expected_nudge": row[2],
    }

def _list_scenarios():
    """List scenarios from Supabase/PostgreSQL demo_scenarios table."""
    try:
        if "demo_scenarios" not in connection.introspection.table_names():
            raise RuntimeError("demo_scenarios table not found")
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

    return []


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
