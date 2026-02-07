from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/market/", include("market.urls")),
    path("api/behavior/", include("behavior.urls")),
    path("api/content/", include("content.urls")),
    path("api/agents/", include("agents.urls")),
    path("api/demo/", include("demo.urls")),
    path("api/chat/", include("chat.urls")),
]
