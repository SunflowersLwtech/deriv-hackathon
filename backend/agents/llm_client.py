"""
Unified DeepSeek LLM Client for TradeIQ
Uses DeepSeek-V3 with function calling support.
Falls back to OpenRouter if DeepSeek API has insufficient balance.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI

logger = logging.getLogger("tradeiq.llm")


class DeepSeekClient:
    """Unified DeepSeek client for all AI agents, with OpenRouter fallback"""

    def __init__(self):
        # Try DeepSeek direct first, fallback to OpenRouter
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

        if not deepseek_key and not openrouter_key:
            raise ValueError(
                "Neither DEEPSEEK_API_KEY nor OPENROUTER_API_KEY set in environment"
            )

        # Try OpenRouter first (since DeepSeek balance is depleted)
        if openrouter_key:
            self.client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            )
            self.chat_model = "deepseek/deepseek-chat-v3-0324"
            self.reasoner_model = "deepseek/deepseek-chat-v3-0324"
            self._provider = "openrouter"
        else:
            self.client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
            )
            self.chat_model = "deepseek-chat"
            self.reasoner_model = "deepseek-chat"
            self._provider = "deepseek"

        # Fallback client (if primary fails)
        self._fallback_client = None
        self._fallback_model = None
        if deepseek_key and openrouter_key:
            # Primary is OpenRouter, fallback is DeepSeek direct
            self._fallback_client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
            )
            self._fallback_model = "deepseek-chat"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Any:
        """
        Chat completion with optional tool calling support.
        Tries primary provider, falls back if 402/insufficient balance.
        """
        model = model or self.chat_model

        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens

        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice

        try:
            return self.client.chat.completions.create(**params)
        except Exception as e:
            error_str = str(e)
            # If primary fails with 402 (insufficient balance), try fallback
            if ("402" in error_str or "Insufficient" in error_str) and self._fallback_client:
                fallback_params = params.copy()
                fallback_params["model"] = self._fallback_model or "deepseek-chat"
                return self._fallback_client.chat.completions.create(**fallback_params)
            raise

    def chat_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Convenience method for chat with tools using chat model (supports function calling).
        """
        model = model or self.chat_model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto",
        )

    def simple_chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Simple chat without tools (uses chat_model).
        Returns response text content.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.chat(
            messages=messages,
            model=self.chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream LLM response chunk by chunk.
        Yields text fragments as they arrive.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        params: Dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(**params)
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f"[Error: {exc}]"


# Global singleton instance
_llm_client: Optional[DeepSeekClient] = None


def get_llm_client() -> DeepSeekClient:
    """Get or create the global DeepSeek client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = DeepSeekClient()
    return _llm_client
