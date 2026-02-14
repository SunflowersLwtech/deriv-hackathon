"""
Django Channels WebSocket Consumer for TradeIQ Chat
Routes messages to AI agents via DeepSeek function calling.
Supports: streaming responses, market alert push, narrator push.
"""
import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001"

    async def connect(self):
        query_params = parse_qs(self.scope.get("query_string", b"").decode())
        requested_user_id = query_params.get("user_id", [None])[0]
        self.user_id = requested_user_id or self.DEMO_USER_ID
        fallback_group_id = self.channel_name.replace(".", "_").replace("!", "_")
        self.room_group_name = f"chat_user_{requested_user_id or fallback_group_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        # Join global market alerts group
        await self.channel_layer.group_add("market_alerts", self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "system",
            "message": "Connected to TradeIQ AI. Ask me about markets, your trading patterns, or content creation.",
            "agent_type": "system",
            "user_id": self.user_id,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard("market_alerts", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message") or data.get("content", "")
        agent_type = data.get("agent_type", "auto")
        user_id = data.get("user_id") or self.user_id
        use_stream = data.get("stream", True)

        if not message:
            return

        if use_stream:
            await self._stream_response(message, agent_type, user_id)
        else:
            # Legacy non-streaming path
            await self.send(text_data=json.dumps({
                "type": "thinking",
                "message": "Analyzing...",
            }))
            result = await sync_to_async(self._route_message)(message, agent_type, user_id)
            await self.send(text_data=json.dumps({
                "type": "reply",
                "message": result.get("response", "I couldn't process that request."),
                "agent_type": result.get("source", "unknown"),
                "tools_used": result.get("tools_used", []),
            }))

    async def _stream_response(self, user_message: str, agent_type: str, user_id: str):
        """Stream AI response with status updates."""
        # Detect agent type
        resolved_type = await sync_to_async(self._detect_agent_type)(user_message, agent_type)

        # Phase 1: thinking
        await self.send(text_data=json.dumps({
            "type": "stream_status",
            "status": "thinking",
            "agent_type": resolved_type,
        }))

        # Phase 2: route query (tool calls happen here, synchronously)
        result = await sync_to_async(self._route_message)(user_message, resolved_type, user_id)
        tools_used = result.get("tools_used", [])

        if tools_used:
            await self.send(text_data=json.dumps({
                "type": "stream_status",
                "status": "tool_call",
                "tools_used": tools_used,
                "description": f"Used {len(tools_used)} tool(s): {', '.join(tools_used[:3])}",
            }))

        # Phase 3: stream the final response
        response_text = result.get("response", "")
        if response_text:
            # Simulate streaming by chunking the already-generated response.
            # For true LLM streaming, the router would need refactoring;
            # this approach gives the UX benefit without breaking the tool-call loop.
            chunk_size = 12
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                await self.send(text_data=json.dumps({
                    "type": "stream_chunk",
                    "content": chunk,
                }))

        # Phase 4: done
        await self.send(text_data=json.dumps({
            "type": "stream_done",
            "full_content": response_text,
            "agent_type": result.get("source", "unknown"),
            "tools_used": tools_used,
        }))

    def _detect_agent_type(self, message: str, agent_type: str) -> str:
        if agent_type != "auto":
            return agent_type
        msg_lower = message.lower()
        if any(w in msg_lower for w in [
            "pattern", "behavior", "nudge", "revenge", "overtrad",
            "habit", "streak", "discipline", "trading history", "my trades",
        ]):
            return "behavior"
        if any(w in msg_lower for w in [
            "post", "bluesky", "content", "thread", "persona", "publish", "social media",
        ]):
            return "content"
        return "market"

    def _route_message(self, message, agent_type, user_id):
        from agents.router import route_query
        return route_query(query=message, agent_type=agent_type, user_id=user_id)

    # ── Channel layer event handlers ──────────────────────────────

    async def chat_message(self, event):
        """Handle messages from channel layer (e.g., behavioral nudges)."""
        message = event.get("message", {})
        await self.send(text_data=json.dumps(message))

    async def market_alert(self, event):
        """Receive market volatility alerts from MarketMonitor."""
        msg = event.get("message", "{}")
        data = json.loads(msg) if isinstance(msg, str) else msg
        await self.send(text_data=json.dumps(data))

    # Channels translates "market.alert" type to market_alert method
    market__alert = market_alert

    async def narrator_message(self, event):
        """Receive live narration from the Narrator."""
        msg = event.get("message", "{}")
        data = json.loads(msg) if isinstance(msg, str) else msg
        await self.send(text_data=json.dumps(data))

    # Channels translates "narrator.message" to narrator_message
