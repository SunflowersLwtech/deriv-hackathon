from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from .models import MarketInsight
from .serializers import MarketInsightSerializer
from .tools import (
    fetch_price_data,
    fetch_price_history,
    get_sentiment,
    analyze_technicals,
    generate_market_brief,
    generate_insights_from_news,
)
from agents.router import route_market_query
from django.utils import timezone as dj_tz
from datetime import timedelta


class MarketInsightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarketInsight.objects.all()
    serializer_class = MarketInsightSerializer

    def list(self, request, *args, **kwargs):
        """Auto-generate fresh insights when none exist or older than 2 hours."""
        two_hours_ago = dj_tz.now() - timedelta(hours=2)
        if MarketInsight.objects.filter(generated_at__gte=two_hours_ago).count() == 0:
            try:
                generate_insights_from_news(limit=8, max_insights=5)
            except Exception as e:
                print(f"Failed to auto-generate insights: {e}")
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def refresh(self, request):
        """POST /api/market/insights/refresh/ — manually trigger insight generation."""
        limit = int(request.data.get("limit", 8))
        max_insights = int(request.data.get("max_insights", 5))
        try:
            insights = generate_insights_from_news(limit=limit, max_insights=max_insights)
            return Response({
                "status": "success",
                "count": len(insights),
                "insights": insights,
                "message": f"Generated {len(insights)} fresh insights from news",
            })
        except Exception as e:
            return Response({"status": "error", "error": str(e)}, status=500)


class AskMarketAnalystView(APIView):
    """
    POST /api/market/ask/
    {"question": "Why did EUR/USD move today?"}

    Routes question to market AI agent for analysis.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        question = request.data.get("question", "")
        if not question:
            return Response({"error": "question is required"}, status=400)

        result = route_market_query(question)

        return Response({
            "answer": result.get("response", ""),
            "disclaimer": "This is analysis, not financial advice.",
            "sources": result.get("tool_details", []),
            "tools_used": result.get("tools_used", []),
        })


class MarketBriefView(APIView):
    """
    POST /api/market/brief/
    {"instruments": ["EUR/USD", "BTC/USD"]}

    Generates AI market brief.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instruments = request.data.get("instruments")
        brief = generate_market_brief(instruments)
        return Response(brief)


class LivePriceView(APIView):
    """
    POST /api/market/price/
    {"instrument": "EUR/USD"}

    Fetches live price from Deriv API.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "")
        if not instrument:
            return Response({"error": "instrument is required"}, status=400)

        price_data = fetch_price_data(instrument)
        return Response(price_data)


class PriceHistoryView(APIView):
    """
    POST /api/market/history/
    {"instrument": "EUR/USD", "timeframe": "1h", "count": 120}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "")
        timeframe = request.data.get("timeframe", "1h")
        count = int(request.data.get("count", 120))

        if not instrument:
            return Response({"error": "instrument is required"}, status=400)

        return Response(fetch_price_history(instrument=instrument, timeframe=timeframe, count=count))


class MarketTechnicalsView(APIView):
    """
    POST /api/market/technicals/
    {"instrument": "EUR/USD", "timeframe": "1h"}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "")
        timeframe = request.data.get("timeframe", "1h")
        if not instrument:
            return Response({"error": "instrument is required"}, status=400)
        return Response(analyze_technicals(instrument=instrument, timeframe=timeframe))


class MarketSentimentView(APIView):
    """
    POST /api/market/sentiment/
    {"instrument": "EUR/USD"}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        instrument = request.data.get("instrument", "")
        if not instrument:
            return Response({"error": "instrument is required"}, status=400)
        return Response(get_sentiment(instrument))


class EconomicCalendarView(APIView):
    """GET /api/market/calendar/ — Finnhub economic calendar."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .tools import fetch_economic_calendar
        return Response(fetch_economic_calendar())


class TopHeadlinesView(APIView):
    """GET /api/market/headlines/ — Trading & finance focused headlines."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .tools import fetch_top_headlines
        limit = int(request.query_params.get("limit", 10))
        return Response({"headlines": fetch_top_headlines(limit=limit)})


class ActiveSymbolsView(APIView):
    """GET /api/market/instruments/ — All available Deriv trading instruments."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .tools import fetch_active_symbols
        market_filter = request.query_params.get("market")
        symbols = fetch_active_symbols()
        if market_filter:
            symbols = [s for s in symbols if s.get("market") == market_filter]
        return Response({"instruments": symbols, "count": len(symbols)})


class PatternRecognitionView(APIView):
    """POST /api/market/patterns/ — Finnhub technical pattern recognition."""
    permission_classes = [AllowAny]

    def post(self, request):
        from .tools import fetch_pattern_recognition
        instrument = request.data.get("instrument", "")
        if not instrument:
            return Response({"error": "instrument is required"}, status=400)
        resolution = request.data.get("resolution", "60")
        return Response(fetch_pattern_recognition(instrument, resolution))
