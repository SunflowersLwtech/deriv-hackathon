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

LOCAL_SCENARIOS = {
    "revenge_trading": {
        "description": "Rapid consecutive losses after an initial loss",
        "expected_detection": "revenge_trading",
        "expected_nudge": "Pause before the next trade and reset risk limits.",
        "trade_sequence": [
            {"minutes_offset": 0, "instrument": "EUR/USD", "direction": "sell", "entry_price": 1.0850, "exit_price": 1.0830, "pnl": -200, "duration_seconds": 300},
            {"minutes_offset": 2, "instrument": "EUR/USD", "direction": "sell", "entry_price": 1.0835, "exit_price": 1.0820, "pnl": -150, "duration_seconds": 45},
            {"minutes_offset": 4, "instrument": "EUR/USD", "direction": "buy", "entry_price": 1.0825, "exit_price": 1.0807, "pnl": -180, "duration_seconds": 30},
            {"minutes_offset": 6, "instrument": "GBP/USD", "direction": "sell", "entry_price": 1.2650, "exit_price": 1.2625, "pnl": -250, "duration_seconds": 20},
            {"minutes_offset": 7, "instrument": "EUR/USD", "direction": "buy", "entry_price": 1.0810, "exit_price": 1.0780, "pnl": -300, "duration_seconds": 15},
        ],
    },
    "overtrading": {
        "description": "High-frequency trades above normal cadence",
        "expected_detection": "overtrading",
        "expected_nudge": "Reduce trade frequency and cap session count.",
        "trade_sequence": [
            {"minutes_offset": i * 8, "instrument": "EUR/USD", "direction": "buy" if i % 2 == 0 else "sell", "entry_price": 1.0850, "exit_price": 1.0852, "pnl": 20 if i % 3 == 0 else -25, "duration_seconds": 60}
            for i in range(18)
        ],
    },
    "loss_chasing": {
        "description": "Increasing loss size in consecutive losing trades",
        "expected_detection": "loss_chasing",
        "expected_nudge": "Cut position size and step away after consecutive losses.",
        "trade_sequence": [
            {"minutes_offset": 0, "instrument": "BTC/USD", "direction": "buy", "entry_price": 44000, "exit_price": 43950, "pnl": -100, "duration_seconds": 180},
            {"minutes_offset": 12, "instrument": "BTC/USD", "direction": "buy", "entry_price": 43980, "exit_price": 43900, "pnl": -150, "duration_seconds": 210},
            {"minutes_offset": 24, "instrument": "BTC/USD", "direction": "buy", "entry_price": 43920, "exit_price": 43810, "pnl": -220, "duration_seconds": 240},
            {"minutes_offset": 36, "instrument": "BTC/USD", "direction": "buy", "entry_price": 43840, "exit_price": 43700, "pnl": -300, "duration_seconds": 300},
            {"minutes_offset": 48, "instrument": "ETH/USD", "direction": "buy", "entry_price": 2350, "exit_price": 2320, "pnl": -360, "duration_seconds": 240},
            {"minutes_offset": 60, "instrument": "ETH/USD", "direction": "buy", "entry_price": 2330, "exit_price": 2290, "pnl": -450, "duration_seconds": 180},
        ],
    },
    "healthy_session": {
        "description": "Disciplined pacing and balanced outcomes",
        "expected_detection": "healthy_session",
        "expected_nudge": "Great discipline. Keep your current process.",
        "trade_sequence": [
            {"minutes_offset": 0, "instrument": "EUR/USD", "direction": "buy", "entry_price": 1.0840, "exit_price": 1.0852, "pnl": 80, "duration_seconds": 420},
            {"minutes_offset": 45, "instrument": "GBP/USD", "direction": "sell", "entry_price": 1.2660, "exit_price": 1.2654, "pnl": 60, "duration_seconds": 360},
            {"minutes_offset": 95, "instrument": "EUR/USD", "direction": "sell", "entry_price": 1.0860, "exit_price": 1.0864, "pnl": -30, "duration_seconds": 300},
            {"minutes_offset": 160, "instrument": "BTC/USD", "direction": "buy", "entry_price": 44120, "exit_price": 44210, "pnl": 120, "duration_seconds": 540},
            {"minutes_offset": 230, "instrument": "GOLD", "direction": "buy", "entry_price": 2058, "exit_price": 2056, "pnl": -25, "duration_seconds": 600},
            {"minutes_offset": 290, "instrument": "EUR/USD", "direction": "buy", "entry_price": 1.0851, "exit_price": 1.0863, "pnl": 75, "duration_seconds": 420},
        ],
    },
}


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
        logger.info("demo_scenarios table unavailable; falling back to local scenarios: %s", exc)
        return None

    if not row:
        return None

    trade_sequence = row[0] if isinstance(row[0], list) else json.loads(row[0] or "[]")
    return {
        "trade_sequence": trade_sequence,
        "expected_detection": row[1],
        "expected_nudge": row[2],
    }


def _load_scenario_from_local(scenario_name: str):
    scenario = LOCAL_SCENARIOS.get(scenario_name)
    if not scenario:
        return None
    return {
        "trade_sequence": scenario["trade_sequence"],
        "expected_detection": scenario["expected_detection"],
        "expected_nudge": scenario["expected_nudge"],
    }


def _list_scenarios():
    """Prefer database scenarios, fallback to built-in local scenarios."""
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
        logger.info("demo_scenarios listing fallback to local data: %s", exc)

    return [
        {
            "name": name,
            "description": config["description"],
            "expected_detection": config["expected_detection"],
            "expected_nudge": config["expected_nudge"],
        }
        for name, config in LOCAL_SCENARIOS.items()
    ]


class LoadScenarioView(APIView):
    """
    POST /api/demo/load-scenario/
    {"scenario": "revenge_trading"}

    Loads demo trade data from demo_scenarios table and creates trades for demo user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        scenario_name = request.data.get("scenario", "revenge_trading")

        # Ensure demo user exists
        demo_user, _ = UserProfile.objects.get_or_create(
            id=DEMO_USER_ID,
            defaults={
                "email": "alex@tradeiq.demo",
                "name": "Alex Demo",
                "preferences": {"theme": "dark"},
                "watchlist": ["EUR/USD", "BTC/USD", "GBP/USD"],
            },
        )

        scenario_data = _load_scenario_from_db(scenario_name) or _load_scenario_from_local(scenario_name)
        if not scenario_data:
            return Response(
                {"error": f"Scenario '{scenario_name}' not found"},
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
        scenario_name = request.data.get("scenario", "revenge_trading")

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
                "watchlist": ["EUR/USD", "BTC/USD", "GBP/USD"],
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
        instrument = request.data.get("instrument", "EUR/USD")

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

        results["disclaimer"] = "This is analysis, not financial advice. All data is for educational purposes."

        return Response(results)
