from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIPersonaViewSet, SocialPostViewSet, PublishToBlueskyView,
    GenerateContentView, BlueskySearchView,
    BlueskyCommunityView, MultiPersonaView,
)

router = DefaultRouter()
router.register(r"personas", AIPersonaViewSet, basename="aipersona")
router.register(r"posts", SocialPostViewSet, basename="socialpost")
urlpatterns = [
    path("", include(router.urls)),
    path("generate/", GenerateContentView.as_view(), name="content-generate"),
    path("publish-bluesky/", PublishToBlueskyView.as_view(), name="publish-bluesky"),
    path("bluesky-search/", BlueskySearchView.as_view(), name="bluesky-search"),
    path("community/", BlueskyCommunityView.as_view(), name="bluesky-community"),
    path("multi-persona/", MultiPersonaView.as_view(), name="multi-persona"),
]
