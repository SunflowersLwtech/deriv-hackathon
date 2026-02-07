"""
REST fallback for chat - used when WebSocket is not available.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from agents.router import route_query


class ChatAskView(APIView):
    """
    POST /api/chat/ask/
    {
        "message": "Why did EUR/USD move today?",
        "conversation_history": [...]  (optional)
    }

    Stateless REST fallback for the AI chat.
    Routes to appropriate agent based on message content.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get("message", "")
        if not message:
            return Response({"error": "message is required"}, status=400)

        # Auto-detect agent type
        msg_lower = message.lower()
        if any(w in msg_lower for w in [
            "pattern", "behavior", "nudge", "revenge", "overtrad",
            "habit", "streak", "discipline", "trading history", "my trades"
        ]):
            agent_type = "behavior"
        elif any(w in msg_lower for w in [
            "post", "bluesky", "content", "thread", "persona",
            "publish", "social media", "generate", "draft"
        ]):
            agent_type = "content"
        else:
            agent_type = "market"

        # Route to agent
        result = route_query(
            query=message,
            agent_type=agent_type,
            user_id=request.data.get("user_id", "d1000000-0000-0000-0000-000000000001"),
        )

        response_data = {
            "reply": result.get("response", "I couldn't process that request."),
            "disclaimer": "This is analysis, not financial advice.",
        }

        # Add nudge for behavior queries
        if agent_type == "behavior" and result.get("tool_details"):
            for tool in result.get("tool_details", []):
                if tool.get("name") == "analyze_trade_patterns":
                    tool_result = tool.get("result", {})
                    if tool_result.get("needs_nudge"):
                        response_data["nudge"] = tool_result.get("summary", "")

        return response_data and Response(response_data)
