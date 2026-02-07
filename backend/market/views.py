from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import MarketInsight
from .serializers import MarketInsightSerializer
from .tools import (
    fetch_price_data,
    fetch_price_history,
    get_sentiment,
    analyze_technicals,
    generate_market_brief,
)
from agents.router import route_market_query


class MarketInsightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarketInsight.objects.all()
    serializer_class = MarketInsightSerializer


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
    """GET /api/market/headlines/ — NewsAPI top business headlines."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .tools import fetch_top_headlines
        category = request.query_params.get("category", "business")
        limit = int(request.query_params.get("limit", 10))
        return Response({"headlines": fetch_top_headlines(category=category, limit=limit)})


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
