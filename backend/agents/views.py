"""
Agent Query REST API Endpoint
Exposes the DeepSeek function-calling router via HTTP
+ Agent Team pipeline endpoints (5-agent architecture)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .router import route_query
from .agent_team import (
    run_pipeline,
    market_monitor_detect,
    analyst_analyze,
    portfolio_advisor_interpret,
    content_creator_generate,
    behavioral_sentinel_analyze,
    VolatilityEvent,
    AnalysisReport,
    BehavioralSentinelInsight,
)
from copytrading.tools import (
    get_top_traders,
    get_trader_stats,
    recommend_trader,
    start_copy_trade,
    stop_copy_trade,
)
from trading.tools import (
    get_contract_quote,
    execute_demo_trade,
    quote_and_buy,
    close_position,
    get_positions,
)
from dataclasses import asdict
import json


class AgentQueryView(APIView):
    """
    POST /api/agents/query/
    {
        "query": "Why did EUR/USD spike today?",
        "agent_type": "market",  // "market", "behavior", "content"
        "user_id": "optional-uuid",
        "context": {}  // optional additional context
    }
    """
    permission_classes = [AllowAny]  # Demo mode - no auth required

    def post(self, request):
        query = request.data.get("query", "")
        agent_type = request.data.get("agent_type", "market")
        user_id = request.data.get("user_id")
        context = request.data.get("context", {})

        if not query:
            return Response(
                {"error": "query is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = route_query(
            query=query,
            agent_type=agent_type,
            user_id=user_id,
            context=context,
        )

        return Response(result)


class AgentChatView(APIView):
    """
    POST /api/agents/chat/
    Stateless chat - each request is independent.
    {
        "message": "Why did EUR/USD move?",
        "agent_type": "market",
        "user_id": "optional-uuid"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get("message", "")
        agent_type = request.data.get("agent_type", "auto")
        user_id = request.data.get("user_id")
        history = request.data.get("history", [])

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-detect agent type based on message content
        if agent_type == "auto":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["pattern", "behavior", "nudge", "revenge", "overtrad", "habit", "streak", "discipline"]):
                agent_type = "behavior"
            elif any(w in msg_lower for w in ["post", "bluesky", "content", "thread", "persona", "publish", "social"]):
                agent_type = "content"
            elif any(w in msg_lower for w in ["copy", "copier", "trader to follow", "mirror", "top trader", "copy trad"]):
                agent_type = "copytrading"
            elif any(w in msg_lower for w in ["trade", "contract", "buy", "sell", "position", "quote", "call", "put", "stake"]):
                agent_type = "trading"
            else:
                agent_type = "market"

        # Build context from conversation history
        context = {}
        if history:
            context["conversation_history"] = history[-6:]

        result = route_query(
            query=message,
            agent_type=agent_type,
            user_id=user_id,
            context=context if context else None,
        )

        return Response({
            "message": result.get("response", ""),
            "agent_type": agent_type,
            "tools_used": result.get("tools_used", []),
            "source": result.get("source", ""),
        })


# ─── Agent Team Pipeline Endpoints ────────────────────────────────────

class AgentTeamPipelineView(APIView):
    """
    POST /api/agents/pipeline/
    Run the full 5-agent pipeline:
      Monitor -> Analyst -> Advisor -> Sentinel -> Content Creator

    Body:
    {
        "instruments": ["BTC/USD"],        // optional - defaults to major pairs
        "custom_event": {                  // optional - manual trigger
            "instrument": "BTC/USD",
            "price": 97500,
            "change_pct": 5.2
        },
        "user_portfolio": [...],           // optional - user positions
        "skip_content": false,             // optional - skip tweet generation
        "user_id": "uuid"                  // optional - enables Behavioral Sentinel
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instruments = request.data.get("instruments")
        custom_event = request.data.get("custom_event")
        user_portfolio = request.data.get("user_portfolio")
        skip_content = request.data.get("skip_content", False)
        user_id = request.data.get("user_id")

        result = run_pipeline(
            instruments=instruments,
            custom_event=custom_event,
            user_portfolio=user_portfolio,
            skip_content=skip_content,
            user_id=user_id,
        )
        return Response(asdict(result))


class AgentMonitorView(APIView):
    """
    POST /api/agents/monitor/
    Run only the Market Monitor agent.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instruments = request.data.get("instruments")
        custom_event = request.data.get("custom_event")

        event = market_monitor_detect(
            instruments=instruments,
            custom_event=custom_event,
        )
        if event is None:
            return Response({"status": "no_event", "message": "No significant volatility detected."})

        return Response({"status": "detected", "event": asdict(event)})


class AgentAnalystView(APIView):
    """
    POST /api/agents/analyst/
    Run only the Analyst agent on a given event.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            event = VolatilityEvent(
                instrument=request.data.get("instrument", "BTC/USD"),
                current_price=request.data.get("current_price"),
                price_change_pct=request.data.get("price_change_pct", 0.0),
                direction=request.data.get("direction", "spike"),
                magnitude=request.data.get("magnitude", "medium"),
            )
            report = analyst_analyze(event)
            return Response(asdict(report))
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentAdvisorView(APIView):
    """
    POST /api/agents/advisor/
    Run only the Portfolio Advisor agent.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        report_data = request.data.get("analysis_report", {})
        user_portfolio = request.data.get("user_portfolio")

        try:
            report = AnalysisReport(
                instrument=report_data.get("instrument", ""),
                event_summary=report_data.get("event_summary", ""),
                root_causes=report_data.get("root_causes", []),
                news_sources=report_data.get("news_sources", []),
                sentiment=report_data.get("sentiment", "neutral"),
                sentiment_score=report_data.get("sentiment_score", 0.0),
                key_data_points=report_data.get("key_data_points", []),
            )
            insight = portfolio_advisor_interpret(report, user_portfolio)
            return Response(asdict(insight))
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentSentinelView(APIView):
    """
    POST /api/agents/sentinel/
    Run only the Behavioral Sentinel agent.

    Fuses a market event with user behavioral history to produce
    a personalised warning: "The market did X, and you tend to Y."

    Body:
    {
        "instrument": "BTC/USD",
        "price_change_pct": 5.2,
        "direction": "spike",
        "event_summary": "BTC surged 5.2%...",
        "user_id": "d1000000-0000-0000-0000-000000000001"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "BTC/USD")
        price_change_pct = float(request.data.get("price_change_pct", 0.0))
        direction = request.data.get("direction", "spike")
        event_summary = request.data.get("event_summary", "")
        user_id = request.data.get("user_id", "d1000000-0000-0000-0000-000000000001")

        try:
            event = VolatilityEvent(
                instrument=instrument,
                current_price=request.data.get("current_price"),
                price_change_pct=price_change_pct,
                direction=direction,
                magnitude="high" if abs(price_change_pct) >= 3.0 else "medium",
            )

            report = AnalysisReport(
                instrument=instrument,
                event_summary=event_summary or f"{instrument} moved {price_change_pct:+.2f}%",
                root_causes=request.data.get("root_causes", []),
                news_sources=[],
                sentiment=request.data.get("sentiment", "neutral"),
                sentiment_score=float(request.data.get("sentiment_score", 0.0)),
                key_data_points=[],
            )

            sentinel = behavioral_sentinel_analyze(event, report, user_id)
            return Response(asdict(sentinel))
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentContentView(APIView):
    """
    POST /api/agents/content-gen/
    Run only the Content Creator agent.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        report_data = request.data.get("analysis_report", {})
        insight_data = request.data.get("personalized_insight")

        try:
            report = AnalysisReport(
                instrument=report_data.get("instrument", ""),
                event_summary=report_data.get("event_summary", ""),
                root_causes=report_data.get("root_causes", []),
                news_sources=report_data.get("news_sources", []),
                sentiment=report_data.get("sentiment", "neutral"),
                sentiment_score=report_data.get("sentiment_score", 0.0),
                key_data_points=report_data.get("key_data_points", []),
            )

            from .agent_team import PersonalizedInsight
            insight = None
            if insight_data:
                insight = PersonalizedInsight(
                    instrument=insight_data.get("instrument", ""),
                    impact_summary=insight_data.get("impact_summary", ""),
                    affected_positions=insight_data.get("affected_positions", []),
                    risk_assessment=insight_data.get("risk_assessment", "medium"),
                    suggestions=insight_data.get("suggestions", []),
                )

            commentary = content_creator_generate(report, insight)
            return Response(asdict(commentary))
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentCopyTradingView(APIView):
    """
    POST /api/agents/copytrading/
    {
        "action": "list" | "stats" | "recommend" | "start" | "stop",
        "trader_id": "...",
        "user_id": "...",
        "api_token": "...",
        "limit": 10
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        action = request.data.get("action", "list")
        trader_id = request.data.get("trader_id")
        user_id = request.data.get("user_id")
        api_token = request.data.get("api_token")
        limit = request.data.get("limit", 10)

        try:
            if action == "list":
                result = get_top_traders(limit=limit)
            elif action == "stats":
                if not trader_id:
                    return Response({"error": "trader_id is required"}, status=status.HTTP_400_BAD_REQUEST)
                result = get_trader_stats(trader_id)
            elif action == "recommend":
                if not user_id:
                    return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
                result = recommend_trader(user_id)
            elif action == "start":
                if not trader_id or not api_token:
                    return Response({"error": "trader_id and api_token are required"}, status=status.HTTP_400_BAD_REQUEST)
                result = start_copy_trade(trader_id, api_token)
            elif action == "stop":
                if not trader_id or not api_token:
                    return Response({"error": "trader_id and api_token are required"}, status=status.HTTP_400_BAD_REQUEST)
                result = stop_copy_trade(trader_id, api_token)
            else:
                return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentTradingView(APIView):
    """
    POST /api/agents/trading/
    {
        "action": "quote" | "buy" | "sell" | "positions",
        "instrument": "...",
        "contract_type": "CALL",
        "amount": 10,
        "duration": 5,
        "duration_unit": "t",
        "proposal_id": "...",
        "price": 10.5,
        "contract_id": 123
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        action = request.data.get("action", "quote")

        try:
            if action == "quote":
                instrument = request.data.get("instrument")
                if not instrument:
                    return Response({"error": "instrument is required"}, status=status.HTTP_400_BAD_REQUEST)
                result = get_contract_quote(
                    instrument=instrument,
                    contract_type=request.data.get("contract_type", "CALL"),
                    amount=request.data.get("amount", 10),
                    duration=request.data.get("duration", 5),
                    duration_unit=request.data.get("duration_unit", "t"),
                )
            elif action == "buy":
                # Use quote_and_buy to avoid InvalidContractProposal from expired proposals
                instrument = request.data.get("instrument")
                if not instrument:
                    return Response({"error": "instrument is required for buy"}, status=status.HTTP_400_BAD_REQUEST)
                result = quote_and_buy(
                    instrument=instrument,
                    contract_type=request.data.get("contract_type", "CALL"),
                    amount=request.data.get("amount", 10),
                    duration=request.data.get("duration", 5),
                    duration_unit=request.data.get("duration_unit", "t"),
                )
            elif action == "sell":
                contract_id = request.data.get("contract_id")
                if contract_id is None:
                    return Response({"error": "contract_id is required"}, status=status.HTTP_400_BAD_REQUEST)
                result = close_position(contract_id)
            elif action == "positions":
                result = get_positions()
            else:
                return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
