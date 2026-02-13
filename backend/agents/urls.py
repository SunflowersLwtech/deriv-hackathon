from django.urls import path
from .views import (
    AgentQueryView,
    AgentChatView,
    AgentTeamPipelineView,
    AgentMonitorView,
    AgentAnalystView,
    AgentAdvisorView,
    AgentSentinelView,
    AgentContentView,
    AgentCopyTradingView,
    AgentTradingView,
)

urlpatterns = [
    path("query/", AgentQueryView.as_view(), name="agent-query"),
    path("chat/", AgentChatView.as_view(), name="agent-chat"),
    # Agent Team Pipeline
    path("pipeline/", AgentTeamPipelineView.as_view(), name="agent-pipeline"),
    path("monitor/", AgentMonitorView.as_view(), name="agent-monitor"),
    path("analyst/", AgentAnalystView.as_view(), name="agent-analyst"),
    path("advisor/", AgentAdvisorView.as_view(), name="agent-advisor"),
    path("sentinel/", AgentSentinelView.as_view(), name="agent-sentinel"),
    path("content-gen/", AgentContentView.as_view(), name="agent-content-gen"),
    # Copy Trading & Trading
    path("copytrading/", AgentCopyTradingView.as_view(), name="agent-copytrading"),
    path("trading/", AgentTradingView.as_view(), name="agent-trading"),
]
