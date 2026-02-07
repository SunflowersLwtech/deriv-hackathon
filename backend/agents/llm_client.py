"""
Unified DeepSeek LLM Client for TradeIQ
Uses latest DeepSeek-V3.2 with function calling support
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI


class DeepSeekClient:
    """Unified DeepSeek client for all AI agents"""
    
    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment variables")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        # Use latest model: deepseek-reasoner for tool use, deepseek-chat for simple tasks
        self.reasoner_model = "deepseek-reasoner"  # V3.2 with tool use
        self.chat_model = "deepseek-chat"  # Standard chat model
    
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
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to chat_model)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            tools: List of tool definitions for function calling
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
        
        Returns:
            Chat completion response
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
        
        return self.client.chat.completions.create(**params)
    
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
        Convenience method for chat with tools using reasoner model.
        
        Args:
            system_prompt: System message
            user_message: User query
            tools: List of tool definitions
            model: Override model (defaults to reasoner_model)
            temperature: Sampling temperature
            max_tokens: Max tokens
        
        Returns:
            Chat completion response
        """
        model = model or self.reasoner_model
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto"
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
        
        Args:
            system_prompt: System message
            user_message: User query
            temperature: Sampling temperature
            max_tokens: Max tokens
        
        Returns:
            Response text content
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = self.chat(
            messages=messages,
            model=self.chat_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content


# Global singleton instance
_llm_client: Optional[DeepSeekClient] = None


def get_llm_client() -> DeepSeekClient:
    """Get or create the global DeepSeek client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = DeepSeekClient()
    return _llm_client
