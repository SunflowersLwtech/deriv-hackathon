from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MarketInsightViewSet,
    AskMarketAnalystView,
    MarketBriefView,
    LivePriceView,
    PriceHistoryView,
    MarketTechnicalsView,
    MarketSentimentView,
    EconomicCalendarView,
    TopHeadlinesView,
    ActiveSymbolsView,
    PatternRecognitionView,
)

router = DefaultRouter()
router.register(r"insights", MarketInsightViewSet, basename="market-insight")

urlpatterns = [
    path("", include(router.urls)),
    path("ask/", AskMarketAnalystView.as_view(), name="market-ask"),
    path("brief/", MarketBriefView.as_view(), name="market-brief"),
    path("price/", LivePriceView.as_view(), name="market-price"),
    path("history/", PriceHistoryView.as_view(), name="market-history"),
    path("technicals/", MarketTechnicalsView.as_view(), name="market-technicals"),
    path("sentiment/", MarketSentimentView.as_view(), name="market-sentiment"),
    path("calendar/", EconomicCalendarView.as_view(), name="market-calendar"),
    path("headlines/", TopHeadlinesView.as_view(), name="market-headlines"),
    path("instruments/", ActiveSymbolsView.as_view(), name="market-instruments"),
    path("patterns/", PatternRecognitionView.as_view(), name="market-patterns"),
]
