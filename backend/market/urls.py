from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketInsightViewSet, AskMarketAnalystView, MarketBriefView, LivePriceView

router = DefaultRouter()
router.register(r"insights", MarketInsightViewSet, basename="market-insight")

urlpatterns = [
    path("", include(router.urls)),
    path("ask/", AskMarketAnalystView.as_view(), name="market-ask"),
    path("brief/", MarketBriefView.as_view(), name="market-brief"),
    path("price/", LivePriceView.as_view(), name="market-price"),
]
