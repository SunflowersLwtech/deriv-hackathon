from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import MarketInsight
from .serializers import MarketInsightSerializer
from .tools import fetch_price_data, get_sentiment, generate_market_brief
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
