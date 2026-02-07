"""
Django Channels WebSocket Consumer for TradeIQ Chat
Routes messages to AI agents via DeepSeek function calling
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # Send welcome message
        await self.send(text_data=json.dumps({
            "type": "system",
            "message": "Connected to TradeIQ AI. Ask me about markets, your trading patterns, or content creation.",
            "agent_type": "system"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        agent_type = data.get("agent_type", "auto")
        user_id = data.get("user_id")

        if not message:
            return

        # Send "thinking" indicator
        await self.send(text_data=json.dumps({
            "type": "thinking",
            "message": "Analyzing...",
        }))

        # Route to agent system (run sync code in thread)
        result = await sync_to_async(self._route_message)(message, agent_type, user_id)

        # Send response
        await self.send(text_data=json.dumps({
            "type": "reply",
            "message": result.get("response", "I couldn't process that request."),
            "agent_type": result.get("source", "unknown"),
            "tools_used": result.get("tools_used", []),
        }))

    def _route_message(self, message, agent_type, user_id):
        """Synchronous routing to agent system."""
        from agents.router import route_query

        # Auto-detect agent type
        if agent_type == "auto":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["pattern", "behavior", "nudge", "revenge", "overtrad", "habit", "streak", "discipline", "trading history", "my trades"]):
                agent_type = "behavior"
            elif any(w in msg_lower for w in ["post", "bluesky", "content", "thread", "persona", "publish", "social media"]):
                agent_type = "content"
            else:
                agent_type = "market"

        return route_query(
            query=message,
            agent_type=agent_type,
            user_id=user_id,
        )

    async def chat_message(self, event):
        """Handle messages from channel layer (e.g., behavioral nudges)."""
        message = event.get("message", {})
        await self.send(text_data=json.dumps(message))
