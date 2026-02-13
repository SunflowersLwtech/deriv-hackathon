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
    explain_market_move,
    fetch_economic_calendar,
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
from copytrading.tools import (
    get_top_traders,
    get_trader_stats,
    recommend_trader,
    start_copy_trade,
    stop_copy_trade,
)
from trading.tools import (
    get_contract_quote,
    execute_demo_trade,
    close_position,
    get_positions,
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
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_technicals",
                "description": "Analyze technical indicators and trend context for an instrument",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument"
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "Analysis timeframe",
                            "default": "1h"
                        }
                    },
                    "required": ["instrument"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_economic_calendar",
                "description": "Fetch economic calendar events (Non-Farm Payrolls, CPI, interest rate decisions) that may explain market moves",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
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


def get_copytrading_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for Copy Trading Agent"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_top_traders",
                "description": "Get a list of top traders available for copy trading with their statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of traders to return",
                            "default": 10
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_trader_stats",
                "description": "Get detailed statistics for a specific trader (win rate, avg profit, copiers count)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trader_id": {
                            "type": "string",
                            "description": "The trader's login ID"
                        }
                    },
                    "required": ["trader_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recommend_trader",
                "description": "AI-powered recommendation: find the best trader match based on user's trading style and risk profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User UUID for behavioral profile matching"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "start_copy_trade",
                "description": "Start copying a trader on Demo account. Educational: lets users learn how copy trading works.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trader_id": {
                            "type": "string",
                            "description": "Trader to copy"
                        },
                        "api_token": {
                            "type": "string",
                            "description": "User's Deriv API token (Demo account only)"
                        }
                    },
                    "required": ["trader_id", "api_token"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "stop_copy_trade",
                "description": "Stop copying a trader",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trader_id": {
                            "type": "string",
                            "description": "Trader to stop copying"
                        },
                        "api_token": {
                            "type": "string",
                            "description": "User's Deriv API token"
                        }
                    },
                    "required": ["trader_id", "api_token"]
                }
            }
        }
    ]


def get_trading_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for Trading Execution Agent (Demo only)"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_contract_quote",
                "description": "Get a price quote for a trading contract (educational demo). Shows how contracts work with real market data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument (e.g., 'Volatility 100 Index', 'EUR/USD')"
                        },
                        "contract_type": {
                            "type": "string",
                            "description": "Contract type: CALL (up), PUT (down)",
                            "default": "CALL"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Stake amount in USD",
                            "default": 10
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Contract duration",
                            "default": 5
                        },
                        "duration_unit": {
                            "type": "string",
                            "description": "Duration unit: t(ticks), s(seconds), m(minutes), h(hours), d(days)",
                            "default": "t"
                        }
                    },
                    "required": ["instrument"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_demo_trade",
                "description": "Execute a trade on Demo account (virtual money only). For educational demonstration of the full trading cycle.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {
                            "type": "string",
                            "description": "Proposal ID from get_contract_quote"
                        },
                        "price": {
                            "type": "number",
                            "description": "Maximum price willing to pay"
                        }
                    },
                    "required": ["proposal_id", "price"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "close_position",
                "description": "Close an open contract position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contract_id": {
                            "type": "integer",
                            "description": "Contract ID to close"
                        }
                    },
                    "required": ["contract_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_positions",
                "description": "Get all currently open contract positions",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
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
    "fetch_economic_calendar": fetch_economic_calendar,
    # Behavior tools
    "get_recent_trades": get_recent_trades,
    "analyze_trade_patterns": analyze_trade_patterns,
    "get_trading_statistics": get_trading_statistics,
    # Content tools
    "generate_draft": generate_draft,
    "generate_thread": generate_thread,
    "format_for_platform": format_for_platform,
    # Copy Trading tools
    "get_top_traders": get_top_traders,
    "get_trader_stats": get_trader_stats,
    "recommend_trader": recommend_trader,
    "start_copy_trade": start_copy_trade,
    "stop_copy_trade": stop_copy_trade,
    # Trading tools
    "get_contract_quote": get_contract_quote,
    "execute_demo_trade": execute_demo_trade,
    "close_position": close_position,
    "get_positions": get_positions,
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
