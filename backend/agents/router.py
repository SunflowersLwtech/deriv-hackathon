"""
DeepSeek Tool Use Router
Routes user queries to appropriate tools via DeepSeek function calling
"""
from typing import Dict, Any, List, Optional
from agents.llm_client import get_llm_client
from agents.prompts import (
    SYSTEM_PROMPT_MARKET,
    SYSTEM_PROMPT_BEHAVIOR,
    SYSTEM_PROMPT_CONTENT,
    SYSTEM_PROMPT_COPYTRADING,
    SYSTEM_PROMPT_TRADING,
)
from agents.tools_registry import (
    get_market_tools,
    get_behavior_tools,
    get_content_tools,
    get_copytrading_tools,
    get_trading_tools,
    execute_tool,
)
from agents.compliance import check_compliance, append_disclaimer
import json
import re


def route_query(
    query: str,
    agent_type: str = "market",  # "market", "behavior", "content"
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Route user query to appropriate tools via DeepSeek function calling.
    
    Args:
        query: User query
        agent_type: Type of agent ("market", "behavior", "content")
        user_id: User UUID (required for behavior agent)
        context: Additional context dict
    
    Returns:
        Response dict with answer and tools used
    """
    # Select tools and system prompt based on agent type
    if agent_type == "market":
        tools = get_market_tools()
        system_prompt = SYSTEM_PROMPT_MARKET
    elif agent_type == "behavior":
        tools = get_behavior_tools()
        system_prompt = SYSTEM_PROMPT_BEHAVIOR
        if user_id:
            query = f"User ID: {user_id}\n\n{query}"
    elif agent_type == "content":
        tools = get_content_tools()
        system_prompt = SYSTEM_PROMPT_CONTENT
    elif agent_type == "copytrading":
        tools = get_copytrading_tools()
        system_prompt = SYSTEM_PROMPT_COPYTRADING
        if user_id:
            query = f"User ID: {user_id}\n\n{query}"
    elif agent_type == "trading":
        tools = get_trading_tools()
        system_prompt = SYSTEM_PROMPT_TRADING
    else:
        return {
            "response": f"Unknown agent type: {agent_type}",
            "source": "router",
            "tools_used": [],
            "error": "Invalid agent_type"
        }
    
    # Add context if provided
    if context:
        context_str = json.dumps(context, indent=2)
        query = f"Context:\n{context_str}\n\nQuery: {query}"
    
    try:
        llm = get_llm_client()

        # Call DeepSeek with tools
        response = llm.chat_with_tools(
            system_prompt=system_prompt,
            user_message=query,
            tools=tools,
            temperature=0.7,
            max_tokens=1000
        )
        
        message = response.choices[0].message
        tools_used = []
        final_response = ""
        
        # Handle tool calls
        if message.tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except:
                    arguments = {}
                
                # Execute tool
                result = execute_tool(tool_name, arguments)
                tools_used.append({
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result
                })
                
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result)
                })
            
            # Get final response with tool results
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
                message,  # Original response with tool calls
                *tool_results  # Tool execution results
            ]
            
            final_response_obj = llm.chat(
                messages=messages,
                model=llm.chat_model,
                temperature=0.7,
                max_tokens=1000
            )
            final_response = final_response_obj.choices[0].message.content
        else:
            # No tool calls, direct response
            final_response = message.content

        final_response = final_response or ""
        # Strip DeepSeek raw function-call XML that sometimes leaks
        # into content instead of using the tool_calls API field
        final_response = re.sub(
            r'<[｜\|]DSML[｜\|]function_calls>.*?</[｜\|]DSML[｜\|]function_calls>',
            '',
            final_response,
            flags=re.DOTALL,
        )
        # Strip <think>...</think> reasoning tags that DeepSeek may include
        final_response = re.sub(
            r'<think>.*?</think>',
            '',
            final_response,
            flags=re.DOTALL,
        ).strip()
        if not final_response:
            final_response = (
                "I wasn't able to generate a complete analysis. "
                "Please try rephrasing your question."
            )
        passed, violations = check_compliance(final_response)
        if not passed:
            final_response = (
                "I'm designed to explain what has happened in markets and trading behavior patterns, "
                "not to provide predictions or signals."
            )

        if "not financial advice" not in final_response.lower():
            final_response = append_disclaimer(final_response)

        return {
            "response": final_response,
            "source": f"agents.router.{agent_type}",
            "tools_used": [t["name"] for t in tools_used],
            "tool_details": tools_used,
            "compliance_violations": violations if not passed else [],
        }
        
    except Exception as e:
        error_text = str(e)
        is_llm_config_error = (
            "DEEPSEEK_API_KEY" in error_text
            and "OPENROUTER_API_KEY" in error_text
        )

        if is_llm_config_error:
            fallback_response = (
                "TradeIQ analysis engine is currently unavailable because no LLM provider "
                "API key is configured. Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY and retry. "
                "This is analysis, not financial advice."
            )
        else:
            fallback_response = f"Error processing query: {error_text}"

        return {
            "response": fallback_response,
            "source": "router",
            "tools_used": [],
            "error": error_text,
        }


def route_market_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for market queries"""
    return route_query(query, agent_type="market", context=context)


def route_behavior_query(query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for behavior queries"""
    return route_query(query, agent_type="behavior", user_id=user_id, context=context)


def route_content_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for content queries"""
    return route_query(query, agent_type="content", context=context)


def route_copytrading_query(query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for copy trading queries"""
    return route_query(query, agent_type="copytrading", user_id=user_id, context=context)


def route_trading_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for trading queries"""
    return route_query(query, agent_type="trading", context=context)
