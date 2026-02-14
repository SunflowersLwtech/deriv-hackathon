"""
DeepSeek Tool Use Router
Routes user queries to appropriate tools via DeepSeek function calling.

Handles a known DeepSeek V3 quirk: the model sometimes emits tool-call XML
(DSML tags) inside the *content* field instead of using the proper tool_calls
API field.  When this happens the router parses the XML, executes the tools,
and does one more LLM round (with tools disabled) to get a plain-text answer.
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
import logging

logger = logging.getLogger("tradeiq.router")

# ── DSML XML helpers ─────────────────────────────────────────────────

_DSML_BLOCK_RE = re.compile(
    r'<[｜|]DSML[｜|]function_calls>(.*?)</[｜|]DSML[｜|]function_calls>',
    re.DOTALL,
)
_DSML_INVOKE_RE = re.compile(
    r'<[｜|]DSML[｜|]invoke\s+name="([^"]+)"[^>]*>(.*?)</[｜|]DSML[｜|]invoke>',
    re.DOTALL,
)
_DSML_PARAM_RE = re.compile(
    r'<[｜|]DSML[｜|]parameter\s+name="([^"]+)"[^>]*>([^<]*)</[｜|]DSML[｜|]parameter>',
)


def _parse_dsml_calls(text: str) -> List[Dict[str, Any]]:
    """Extract tool calls from DSML XML that DeepSeek sometimes leaks into content."""
    calls: List[Dict[str, Any]] = []
    for block_match in _DSML_BLOCK_RE.finditer(text):
        block = block_match.group(1)
        for inv in _DSML_INVOKE_RE.finditer(block):
            name = inv.group(1)
            body = inv.group(2)
            params = {}
            for pm in _DSML_PARAM_RE.finditer(body):
                params[pm.group(1)] = pm.group(2).strip()
            # Coerce numeric-looking values
            for k, v in params.items():
                if v.isdigit():
                    params[k] = int(v)
            calls.append({"name": name, "arguments": params})
    return calls


def _strip_dsml_and_think(text: str) -> str:
    """Remove DSML XML blocks and <think> tags from response text."""
    text = _DSML_BLOCK_RE.sub('', text)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()


# ── Main router ──────────────────────────────────────────────────────

def route_query(
    query: str,
    agent_type: str = "market",
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Route user query to appropriate tools via DeepSeek function calling."""

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
            "error": "Invalid agent_type",
        }

    if context:
        context_str = json.dumps(context, indent=2)
        query = f"Context:\n{context_str}\n\nQuery: {query}"

    try:
        llm = get_llm_client()

        # ── Round 1: LLM with tools ─────────────────────────────────
        response = llm.chat_with_tools(
            system_prompt=system_prompt,
            user_message=query,
            tools=tools,
            temperature=0.7,
            max_tokens=1000,
        )

        message = response.choices[0].message
        tools_used: List[Dict[str, Any]] = []
        final_response = ""

        # Collect tool calls from API field
        pending_tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                pending_tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })

        # ── Execute tool calls (round 1) ─────────────────────────────
        if pending_tool_calls:
            tool_results_for_llm = []
            for tc in pending_tool_calls:
                result = execute_tool(tc["name"], tc["arguments"])
                tools_used.append({"name": tc["name"], "arguments": tc["arguments"], "result": result})
                tool_results_for_llm.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": tc["name"],
                    "content": json.dumps(result),
                })

            any_errors = any("error" in json.loads(tr["content"]) for tr in tool_results_for_llm)

            follow_up = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
                message,
                *tool_results_for_llm,
            ]
            if any_errors:
                follow_up.append({
                    "role": "system",
                    "content": (
                        "Some tools returned errors (e.g. market closed, unsupported instrument). "
                        "Do NOT attempt to call more tools or say 'let me try again'. "
                        "Provide the best analysis you can using general knowledge. "
                        "Be specific and helpful."
                    ),
                })

            resp2 = llm.chat(
                messages=follow_up,
                model=llm.chat_model,
                temperature=0.7,
                max_tokens=1000,
            )
            final_response = resp2.choices[0].message.content or ""

            # ── Handle DSML leak in round-2 response ─────────────────
            dsml_calls = _parse_dsml_calls(final_response)
            if dsml_calls:
                logger.info("DSML leak detected in round-2: %s", [c["name"] for c in dsml_calls])
                # Execute the leaked tool calls
                extra_context_parts = []
                for dc in dsml_calls:
                    result = execute_tool(dc["name"], dc["arguments"])
                    tools_used.append({"name": dc["name"], "arguments": dc["arguments"], "result": result})
                    extra_context_parts.append(
                        f"Tool {dc['name']}({json.dumps(dc['arguments'])}): "
                        f"{json.dumps(result)}"
                    )

                # Round 3: plain-text only (no tools) to force a text response
                resp3 = llm.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": (
                                f"Original question: {query}\n\n"
                                f"Tool results:\n" +
                                "\n".join(
                                    f"- {tu['name']}: {json.dumps(tu['result'])}"
                                    for tu in tools_used
                                ) +
                                "\n\nUsing the tool results above, provide a helpful analysis. "
                                "Do NOT call any tools. Respond in plain text only."
                            ),
                        },
                    ],
                    model=llm.chat_model,
                    temperature=0.7,
                    max_tokens=1000,
                )
                final_response = resp3.choices[0].message.content or ""
        else:
            final_response = message.content or ""

        # ── Clean up ─────────────────────────────────────────────────
        final_response = _strip_dsml_and_think(final_response)

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


# ── Convenience helpers ──────────────────────────────────────────────

def route_market_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return route_query(query, agent_type="market", context=context)

def route_behavior_query(query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return route_query(query, agent_type="behavior", user_id=user_id, context=context)

def route_content_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return route_query(query, agent_type="content", context=context)

def route_copytrading_query(query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return route_query(query, agent_type="copytrading", user_id=user_id, context=context)

def route_trading_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return route_query(query, agent_type="trading", context=context)
