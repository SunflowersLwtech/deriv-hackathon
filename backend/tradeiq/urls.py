from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", health_check),
    path("admin/", admin.site.urls),
    path("api/market/", include("market.urls")),
    path("api/behavior/", include("behavior.urls")),
    path("api/content/", include("content.urls")),
    path("api/agents/", include("agents.urls")),
    path("api/demo/", include("demo.urls")),
    path("api/chat/", include("chat.urls")),
]

# Serve media files (charts, AI images) in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
