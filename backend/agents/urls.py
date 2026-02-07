from django.urls import path
from .views import AgentQueryView, AgentChatView

urlpatterns = [
    path("query/", AgentQueryView.as_view(), name="agent-query"),
    path("chat/", AgentChatView.as_view(), name="agent-chat"),
]
