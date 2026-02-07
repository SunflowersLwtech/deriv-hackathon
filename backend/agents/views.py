"""
Agent Query REST API Endpoint
Exposes the DeepSeek function-calling router via HTTP
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .router import route_query
import json


class AgentQueryView(APIView):
    """
    POST /api/agents/query/
    {
        "query": "Why did EUR/USD spike today?",
        "agent_type": "market",  // "market", "behavior", "content"
        "user_id": "optional-uuid",
        "context": {}  // optional additional context
    }
    """
    permission_classes = [AllowAny]  # Demo mode - no auth required

    def post(self, request):
        query = request.data.get("query", "")
        agent_type = request.data.get("agent_type", "market")
        user_id = request.data.get("user_id")
        context = request.data.get("context", {})

        if not query:
            return Response(
                {"error": "query is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = route_query(
            query=query,
            agent_type=agent_type,
            user_id=user_id,
            context=context,
        )

        return Response(result)


class AgentChatView(APIView):
    """
    POST /api/agents/chat/
    Stateless chat - each request is independent.
    {
        "message": "Why did EUR/USD move?",
        "agent_type": "market",
        "user_id": "optional-uuid"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get("message", "")
        agent_type = request.data.get("agent_type", "auto")
        user_id = request.data.get("user_id")

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-detect agent type based on message content
        if agent_type == "auto":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["pattern", "behavior", "nudge", "revenge", "overtrad", "habit", "streak", "discipline"]):
                agent_type = "behavior"
            elif any(w in msg_lower for w in ["post", "bluesky", "content", "thread", "persona", "publish", "social"]):
                agent_type = "content"
            else:
                agent_type = "market"

        result = route_query(
            query=message,
            agent_type=agent_type,
            user_id=user_id,
        )

        return Response({
            "message": result.get("response", ""),
            "agent_type": agent_type,
            "tools_used": result.get("tools_used", []),
            "source": result.get("source", ""),
        })
