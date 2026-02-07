"""
Market Analysis Tools using DeepSeek LLM
Functions for Market Analyst Agent
"""
from typing import Dict, Any, List, Optional
from agents.llm_client import get_llm_client
from agents.prompts import SYSTEM_PROMPT_MARKET
from .models import MarketInsight
import json
import os
import requests
from datetime import datetime


def fetch_price_data(instrument: str) -> Dict[str, Any]:
    """
    Fetch current price data for an instrument.
    Uses Deriv API or Finnhub as fallback.
    
    Args:
        instrument: Trading instrument symbol (e.g., "EUR/USD")
    
    Returns:
        Dict with price, change, etc.
    """
    # TODO: Implement Deriv API integration
    # For now, return mock data structure
    return {
        "instrument": instrument,
        "price": None,
        "change": None,
        "change_percent": None,
        "timestamp": datetime.now().isoformat(),
        "source": "deriv"
    }


def search_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search news articles related to market query.
    Uses NewsAPI.
    
    Args:
        query: Search query
        limit: Max number of results
    
    Returns:
        List of news articles
    """
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "sortBy": "publishedAt",
            "pageSize": limit,
            "language": "en"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", "")
                }
                for article in data.get("articles", [])[:limit]
            ]
    except Exception as e:
        print(f"NewsAPI error: {e}")
    
    return []


def analyze_technicals(instrument: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Analyze technical indicators for an instrument.
    
    Args:
        instrument: Trading instrument
        timeframe: Timeframe for analysis
    
    Returns:
        Technical analysis results
    """
    # TODO: Implement technical analysis
    # For now, return structure
    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "indicators": {},
        "summary": ""
    }


def get_sentiment(instrument: str) -> Dict[str, Any]:
    """
    Get market sentiment for an instrument.
    
    Args:
        instrument: Trading instrument
    
    Returns:
        Sentiment analysis results
    """
    # Use DeepSeek to analyze sentiment from news
    news = search_news(instrument, limit=10)
    
    if not news:
        return {
            "instrument": instrument,
            "sentiment": "neutral",
            "score": 0.0,
            "sources": []
        }
    
    # Use DeepSeek to analyze sentiment
    llm = get_llm_client()
    
    news_summary = "\n".join([
        f"- {article['title']}: {article.get('description', '')[:100]}"
        for article in news[:5]
    ])
    
    prompt = f"""Analyze the sentiment of news articles about {instrument}.

News Articles:
{news_summary}

Return a JSON object with:
{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "score": -1.0 to 1.0 (negative=bearish, positive=bullish),
  "key_points": ["point1", "point2", "point3"],
  "confidence": 0.0 to 1.0
}}"""
    
    try:
        response = llm.simple_chat(
            system_prompt=SYSTEM_PROMPT_MARKET,
            user_message=prompt,
            temperature=0.3,
            max_tokens=300
        )
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        sentiment_data = json.loads(response_text)
        sentiment_data["instrument"] = instrument
        sentiment_data["sources"] = [n["source"] for n in news[:5]]
        return sentiment_data
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return {
            "instrument": instrument,
            "sentiment": "neutral",
            "score": 0.0,
            "sources": [n["source"] for n in news[:5]]
        }


def explain_market_move(instrument: str, move_description: str) -> Dict[str, Any]:
    """
    Use DeepSeek to explain why a market move happened.
    Combines price data, news, and technical analysis.
    
    Args:
        instrument: Trading instrument
        move_description: Description of the move (e.g., "EUR/USD spiked 1.2%")
    
    Returns:
        Explanation with sources
    """
    llm = get_llm_client()
    
    # Gather data
    price_data = fetch_price_data(instrument)
    news = search_news(instrument, limit=5)
    sentiment = get_sentiment(instrument)
    
    # Build context
    news_context = "\n".join([
        f"- {article['title']} ({article['source']}): {article.get('description', '')[:150]}"
        for article in news[:5]
    ]) if news else "No recent news found."
    
    prompt = f"""Explain why this market move happened: {move_description}

Context:
- Instrument: {instrument}
- Current sentiment: {sentiment.get('sentiment', 'neutral')} (score: {sentiment.get('score', 0.0)})
- Recent news:
{news_context}

RULES:
- Explain what HAS happened, not what WILL happen
- Reference specific news sources and data points
- Use past tense: "The move occurred because..."
- End with: "📊 Analysis by TradeIQ | Not financial advice"

Generate a clear, factual explanation (2-3 sentences max)."""
    
    try:
        explanation = llm.simple_chat(
            system_prompt=SYSTEM_PROMPT_MARKET,
            user_message=prompt,
            temperature=0.5,
            max_tokens=200
        )
        
        return {
            "instrument": instrument,
            "move": move_description,
            "explanation": explanation.strip(),
            "sources": {
                "news": [n["url"] for n in news[:3]],
                "sentiment": sentiment
            },
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Market explanation error: {e}")
        return {
            "instrument": instrument,
            "move": move_description,
            "explanation": "Unable to generate explanation at this time.",
            "sources": {},
            "error": str(e)
        }
