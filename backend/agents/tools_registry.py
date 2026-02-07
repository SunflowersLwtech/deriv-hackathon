"""
Tool Registry for DeepSeek Function Calling
Registers all available tools for Market, Behavior, and Content agents
"""
from typing import Dict, Any, List

# Import tool functions
from market.tools import (
    fetch_price_data,
    search_news,
    analyze_technicals,
    get_sentiment,
    explain_market_move
)
from behavior.tools import (
    get_recent_trades,
    analyze_trade_patterns,
    generate_behavioral_nudge_with_ai,
    get_trading_statistics
)
from content.tools import (
    generate_draft,
    generate_thread,
    format_for_platform
)


def get_market_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for Market Analyst Agent"""
    return [
        {
            "type": "function",
            "function": {
                "name": "fetch_price_data",
                "description": "Fetch current price data for a trading instrument",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument symbol (e.g., EUR/USD, BTC/USD)"
                        }
                    },
                    "required": ["instrument"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_news",
                "description": "Search news articles related to a market query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for news"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explain_market_move",
                "description": "Explain why a market move happened using data, news, and analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument"
                        },
                        "move_description": {
                            "type": "string",
                            "description": "Description of the market move (e.g., 'EUR/USD spiked 1.2%')"
                        }
                    },
                    "required": ["instrument", "move_description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_sentiment",
                "description": "Get market sentiment analysis for an instrument",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument"
                        }
                    },
                    "required": ["instrument"]
                }
            }
        }
    ]


def get_behavior_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for Behavioral Coach Agent"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_recent_trades",
                "description": "Get recent trades for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Hours of history to fetch",
                            "default": 24
                        }
                    },
                    "required": ["user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_trade_patterns",
                "description": "Analyze trader's behavioral patterns (revenge trading, overtrading, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Hours of trade history to analyze",
                            "default": 24
                        }
                    },
                    "required": ["user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_trading_statistics",
                "description": "Get comprehensive trading statistics for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Days of history",
                            "default": 30
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
    ]


def get_content_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for Content Creator Agent"""
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_draft",
                "description": "Generate a social media post draft",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "persona_id": {
                            "type": "string",
                            "description": "AI Persona UUID"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic or insight to post about"
                        },
                        "platform": {
                            "type": "string",
                            "description": "Platform (bluesky, twitter, etc.)",
                            "default": "bluesky"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Max character length",
                            "default": 300
                        }
                    },
                    "required": ["persona_id", "topic"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_thread",
                "description": "Generate a thread (multiple connected posts)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "persona_id": {
                            "type": "string",
                            "description": "AI Persona UUID"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Main topic"
                        },
                        "num_posts": {
                            "type": "integer",
                            "description": "Number of posts in thread",
                            "default": 3
                        },
                        "platform": {
                            "type": "string",
                            "description": "Platform",
                            "default": "bluesky"
                        }
                    },
                    "required": ["persona_id", "topic"]
                }
            }
        }
    ]


# Tool execution mapping
TOOL_FUNCTIONS = {
    # Market tools
    "fetch_price_data": fetch_price_data,
    "search_news": search_news,
    "explain_market_move": explain_market_move,
    "get_sentiment": get_sentiment,
    "analyze_technicals": analyze_technicals,
    # Behavior tools
    "get_recent_trades": get_recent_trades,
    "analyze_trade_patterns": analyze_trade_patterns,
    "get_trading_statistics": get_trading_statistics,
    # Content tools
    "generate_draft": generate_draft,
    "generate_thread": generate_thread,
    "format_for_platform": format_for_platform,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a tool function by name.
    
    Args:
        tool_name: Name of the tool function
        arguments: Arguments to pass to the function
    
    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_FUNCTIONS:
        return {"error": f"Tool {tool_name} not found"}
    
    try:
        func = TOOL_FUNCTIONS[tool_name]
        return func(**arguments)
    except Exception as e:
        return {"error": str(e)}
