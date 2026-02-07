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
import asyncio
import threading
from datetime import datetime, timezone


# Deriv symbol mapping: user-friendly -> Deriv API symbol
DERIV_SYMBOLS = {
    "EUR/USD": "frxEURUSD",
    "GBP/USD": "frxGBPUSD",
    "USD/JPY": "frxUSDJPY",
    "AUD/USD": "frxAUDUSD",
    "USD/CHF": "frxUSDCHF",
    "BTC/USD": "cryBTCUSD",
    "ETH/USD": "cryETHUSD",
    "GOLD": "frxXAUUSD",
    "XAU/USD": "frxXAUUSD",
    "SILVER": "frxXAGUSD",
    "Volatility 75": "R_75",
    "Volatility 75 Index": "R_75",
    "V75": "R_75",
    "Volatility 100": "R_100",
    "V100": "R_100",
    "Volatility 10": "R_10",
    "V10": "R_10",
}


def _get_deriv_symbol(instrument: str) -> str:
    """Convert user-friendly instrument name to Deriv API symbol."""
    if instrument in DERIV_SYMBOLS:
        return DERIV_SYMBOLS[instrument]
    for key, val in DERIV_SYMBOLS.items():
        if key.lower() == instrument.lower():
            return val
    return instrument


async def _fetch_deriv_price_async(instrument: str) -> Dict[str, Any]:
    """Async fetch price from Deriv WebSocket API."""
    try:
        import websockets
    except ImportError:
        return {
            "instrument": instrument,
            "price": None,
            "error": "websockets package not installed",
            "timestamp": datetime.now().isoformat(),
            "source": "deriv"
        }

    app_id = os.environ.get("DERIV_APP_ID", "125489")
    deriv_symbol = _get_deriv_symbol(instrument)
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"

    try:
        async with websockets.connect(ws_url, close_timeout=5) as ws:
            await ws.send(json.dumps({
                "ticks": deriv_symbol,
                "subscribe": 1
            }))
            response = await asyncio.wait_for(ws.recv(), timeout=8)
            data = json.loads(response)

            if "error" in data:
                return {
                    "instrument": instrument,
                    "deriv_symbol": deriv_symbol,
                    "price": None,
                    "error": data["error"].get("message", "Unknown error"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "deriv"
                }

            tick = data.get("tick", {})
            quote = tick.get("quote")
            epoch = tick.get("epoch")

            return {
                "instrument": instrument,
                "deriv_symbol": deriv_symbol,
                "price": float(quote) if quote else None,
                "bid": float(tick.get("bid", 0)) if tick.get("bid") else None,
                "ask": float(tick.get("ask", 0)) if tick.get("ask") else None,
                "timestamp": datetime.fromtimestamp(epoch).isoformat() if epoch else datetime.now().isoformat(),
                "source": "deriv"
            }
    except Exception as e:
        return {
            "instrument": instrument,
            "deriv_symbol": deriv_symbol,
            "price": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "deriv"
        }


def _run_async_in_new_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""
    result = [None]
    exception = [None]

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as e:
            exception[0] = e
        finally:
            loop.close()

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout=12)

    if exception[0]:
        raise exception[0]
    return result[0]


def fetch_price_data(instrument: str) -> Dict[str, Any]:
    """
    Fetch current price data for an instrument from Deriv WebSocket API.

    Args:
        instrument: Trading instrument symbol (e.g., "EUR/USD")

    Returns:
        Dict with price, change, etc.
    """
    try:
        result = _run_async_in_new_thread(_fetch_deriv_price_async(instrument))
        return result
    except Exception as e:
        return {
            "instrument": instrument,
            "price": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "deriv"
        }


def _search_newsapi(query: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI."""
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return []

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": api_key,
                "sortBy": "publishedAt",
                "pageSize": max(limit, 1),
                "language": "en",
            },
            timeout=5,
        )
        if response.status_code != 200:
            return []
        data = response.json()
        return [
            {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
            }
            for article in data.get("articles", [])[:limit]
        ]
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


def _finnhub_category_for_query(query: str) -> str:
    q = query.lower()
    if any(token in q for token in ["eur", "gbp", "usd", "jpy", "forex", "xau"]):
        return "forex"
    if any(token in q for token in ["btc", "eth", "crypto"]):
        return "crypto"
    return "general"


def _search_finnhub_news(query: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch market news from Finnhub category feed."""
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/news",
            params={
                "category": _finnhub_category_for_query(query),
                "token": api_key,
            },
            timeout=5,
        )
        if response.status_code != 200:
            return []

        items = response.json()
        if not isinstance(items, list):
            return []

        query_tokens = [token for token in query.lower().replace("/", " ").split() if len(token) >= 3]
        articles: List[Dict[str, Any]] = []
        for item in items:
            headline = (item.get("headline") or "").strip()
            summary = (item.get("summary") or "").strip()
            text_blob = f"{headline} {summary}".lower()
            if query_tokens and not any(token in text_blob for token in query_tokens):
                continue

            published_at = ""
            epoch = item.get("datetime")
            if isinstance(epoch, (int, float)) and epoch > 0:
                published_at = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()

            articles.append(
                {
                    "title": headline,
                    "description": summary,
                    "url": item.get("url", ""),
                    "publishedAt": published_at,
                    "source": item.get("source", "Finnhub"),
                }
            )
            if len(articles) >= limit:
                break

        return articles
    except Exception as e:
        print(f"Finnhub error: {e}")
        return []


def search_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search news articles related to market query.
    Aggregates NewsAPI + Finnhub.

    Args:
        query: Search query
        limit: Max number of results

    Returns:
        List of news articles
    """
    combined = _search_newsapi(query, limit=limit) + _search_finnhub_news(query, limit=limit)
    if not combined:
        return []

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for article in combined:
        key = (article.get("url") or "").strip() or (article.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(article)

    deduped.sort(key=lambda item: item.get("publishedAt", ""), reverse=True)
    return deduped[:limit]


def analyze_technicals(instrument: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Analyze technical indicators for an instrument using DeepSeek.
    """
    price_data = fetch_price_data(instrument)
    price = price_data.get("price")

    if not price:
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "indicators": {},
            "summary": "Price data unavailable for technical analysis."
        }

    llm = get_llm_client()
    prompt = f"""Based on the current price of {instrument} at {price}, provide a brief technical analysis summary.

Note: Without historical candle data, provide general context about typical technical levels.
Include: general trend context, key psychological levels, and typical volatility.

Return a JSON object:
{{
  "trend": "bullish" | "bearish" | "neutral",
  "key_levels": {{"support": <number>, "resistance": <number>}},
  "volatility": "low" | "medium" | "high",
  "summary": "<1-2 sentence summary>"
}}"""

    try:
        response = llm.simple_chat(
            system_prompt=SYSTEM_PROMPT_MARKET,
            user_message=prompt,
            temperature=0.3,
            max_tokens=300
        )
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        result["instrument"] = instrument
        result["timeframe"] = timeframe
        result["current_price"] = price
        return result
    except Exception as e:
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "indicators": {},
            "summary": f"Technical analysis error: {str(e)}"
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
    price_context = f"Current price: {price_data.get('price', 'N/A')}" if price_data.get('price') else "Price data unavailable"

    news_context = "\n".join([
        f"- {article['title']} ({article['source']}): {article.get('description', '')[:150]}"
        for article in news[:5]
    ]) if news else "No recent news found."

    prompt = f"""Explain why this market move happened: {move_description}

Context:
- Instrument: {instrument}
- {price_context}
- Current sentiment: {sentiment.get('sentiment', 'neutral')} (score: {sentiment.get('score', 0.0)})
- Recent news:
{news_context}

RULES:
- Explain what HAS happened, not what WILL happen
- Reference specific news sources and data points
- Use past tense: "The move occurred because..."
- End with: "This is analysis, not financial advice."

Generate a clear, factual explanation (2-3 sentences max)."""

    try:
        explanation = llm.simple_chat(
            system_prompt=SYSTEM_PROMPT_MARKET,
            user_message=prompt,
            temperature=0.5,
            max_tokens=300
        )

        return {
            "instrument": instrument,
            "move": move_description,
            "explanation": explanation.strip(),
            "price": price_data.get("price"),
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


def generate_market_brief(instruments: List[str] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive market brief covering multiple instruments.

    Args:
        instruments: List of instruments (defaults to major pairs)

    Returns:
        Market brief with summaries
    """
    if not instruments:
        instruments = ["EUR/USD", "GBP/USD", "BTC/USD", "GOLD"]

    instrument_data = []
    for inst in instruments[:6]:  # Max 6
        price = fetch_price_data(inst)
        instrument_data.append({
            "symbol": inst,
            "price": price.get("price"),
            "source": price.get("source", "deriv"),
        })

    # Generate AI summary
    llm = get_llm_client()

    data_summary = "\n".join([
        f"- {d['symbol']}: {d['price'] or 'N/A'}"
        for d in instrument_data
    ])

    prompt = f"""Generate a brief market overview (3-4 sentences) based on current data:

{data_summary}

RULES:
- Describe what IS happening, not what WILL happen
- Reference specific price levels
- Professional, Bloomberg-anchor tone
- End with: "This is analysis, not financial advice."
"""

    try:
        summary = llm.simple_chat(
            system_prompt=SYSTEM_PROMPT_MARKET,
            user_message=prompt,
            temperature=0.5,
            max_tokens=300
        )

        return {
            "summary": summary.strip(),
            "instruments": instrument_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "summary": f"Market brief generation error: {str(e)}",
            "instruments": instrument_data,
            "timestamp": datetime.now().isoformat()
        }
