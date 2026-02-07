# behavior/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, TradeViewSet, BehavioralMetricViewSet

router = DefaultRouter()
router.register(r"profiles", UserProfileViewSet, basename="userprofile")
router.register(r"trades", TradeViewSet, basename="trade")
router.register(r"metrics", BehavioralMetricViewSet, basename="behavioralmetric")

urlpatterns = [
    path("", include(router.urls)),
]
