# behavior/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, TradeViewSet, BehavioralMetricViewSet,
    TradingTwinView,
    DerivPortfolioView, DerivBalanceView, DerivRealityCheckView,
)

router = DefaultRouter()
router.register(r"profiles", UserProfileViewSet, basename="userprofile")
router.register(r"trades", TradeViewSet, basename="trade")
router.register(r"metrics", BehavioralMetricViewSet, basename="behavioralmetric")

urlpatterns = [
    path("", include(router.urls)),
    path("trading-twin/", TradingTwinView.as_view(), name="trading-twin"),
    path("portfolio/", DerivPortfolioView.as_view(), name="deriv-portfolio"),
    path("balance/", DerivBalanceView.as_view(), name="deriv-balance"),
    path("reality-check/", DerivRealityCheckView.as_view(), name="deriv-reality-check"),
]
