"""
Market Analysis Tools using DeepSeek LLM
Functions for Market Analyst Agent
"""
from typing import Dict, Any, List, Optional
from agents.llm_client import get_llm_client
from agents.prompts import SYSTEM_PROMPT_MARKET
from .models import MarketInsight
import json
import logging
import os
import math
import requests
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
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

TIMEFRAME_TO_GRANULARITY = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
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
    Uses Redis cache to avoid redundant WebSocket calls (5-second TTL).

    Args:
        instrument: Trading instrument symbol (e.g., "EUR/USD")

    Returns:
        Dict with price, change, etc.
    """
    # Try to import cache helpers (gracefully skip if Redis is not configured)
    _cache_available = False
    try:
        from .cache import get_cached_price, set_cached_price
        _cache_available = True
    except Exception:
        pass

    # Check cache first (short 5s TTL for live prices — deduplicates the burst
    # of concurrent requests that fire when dashboard hooks mount at once.
    # This differs from cache.py's 300s default which is for longer-lived data.)
    if _cache_available:
        try:
            cached = get_cached_price(instrument)
            if cached is not None:
                return {
                    "instrument": instrument,
                    "price": cached,
                    "timestamp": datetime.now().isoformat(),
                    "source": "deriv",
                    "cached": True,
                }
        except Exception as exc:
            logger.debug("Redis cache read failed for %s: %s", instrument, exc)

    try:
        result = _run_async_in_new_thread(_fetch_deriv_price_async(instrument))
        if _cache_available and result and result.get("price") is not None:
            try:
                set_cached_price(instrument, result["price"], ttl_seconds=5)
            except Exception as exc:
                logger.debug("Redis cache write failed for %s: %s", instrument, exc)
        return result
    except Exception as e:
        return {
            "instrument": instrument,
            "price": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "deriv"
        }


async def _fetch_deriv_history_async(
    instrument: str,
    granularity: int,
    count: int,
) -> Dict[str, Any]:
    """Fetch OHLC candle history from Deriv WebSocket API."""
    try:
        import websockets
    except ImportError:
        return {
            "instrument": instrument,
            "candles": [],
            "error": "websockets package not installed",
            "source": "deriv",
        }

    app_id = os.environ.get("DERIV_APP_ID", "125489")
    deriv_symbol = _get_deriv_symbol(instrument)
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"

    request_payload = {
        "ticks_history": deriv_symbol,
        "adjust_start_time": 1,
        "count": max(10, min(count, 500)),
        "end": "latest",
        "style": "candles",
        "granularity": granularity,
    }

    try:
        async with websockets.connect(ws_url, close_timeout=5) as ws:
            await ws.send(json.dumps(request_payload))
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            if "error" in data:
                return {
                    "instrument": instrument,
                    "candles": [],
                    "error": data["error"].get("message", "Unknown error"),
                    "source": "deriv",
                }

            candles = data.get("candles", []) or []
            normalized = []
            for candle in candles:
                epoch = candle.get("epoch")
                if epoch is None:
                    continue
                normalized.append(
                    {
                        "time": datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(),
                        "open": float(candle.get("open", 0.0)),
                        "high": float(candle.get("high", 0.0)),
                        "low": float(candle.get("low", 0.0)),
                        "close": float(candle.get("close", 0.0)),
                    }
                )

            return {
                "instrument": instrument,
                "deriv_symbol": deriv_symbol,
                "candles": normalized,
                "source": "deriv",
            }
    except Exception as exc:
        return {
            "instrument": instrument,
            "candles": [],
            "error": str(exc),
            "source": "deriv",
        }


def fetch_price_history(
    instrument: str,
    timeframe: str = "1h",
    count: int = 120,
) -> Dict[str, Any]:
    """Fetch historical candles for charting and technical analysis."""
    granularity = TIMEFRAME_TO_GRANULARITY.get(timeframe, 3600)
    try:
        result = _run_async_in_new_thread(
            _fetch_deriv_history_async(
                instrument=instrument,
                granularity=granularity,
                count=count,
            )
        )
    except Exception as exc:
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "candles": [],
            "error": str(exc),
            "source": "deriv",
        }

    candles = result.get("candles", []) or []
    if len(candles) >= 2:
        first = candles[0]["close"]
        last = candles[-1]["close"]
        change = last - first
        change_percent = (change / first * 100.0) if first else 0.0
    else:
        change = 0.0
        change_percent = 0.0

    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "candles": candles,
        "change": round(change, 6),
        "change_percent": round(change_percent, 4),
        "source": "deriv",
        "error": result.get("error"),
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


def fetch_top_headlines(category: str = "business", country: str = "us", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch top headlines from NewsAPI /v2/top-headlines."""
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        return []
    try:
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category": category, "country": country, "apiKey": api_key, "pageSize": limit},
            timeout=5,
        )
        if response.status_code != 200:
            return []
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", ""),
            }
            for a in response.json().get("articles", [])[:limit]
        ]
    except Exception as e:
        print(f"NewsAPI headlines error: {e}")
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
    # Fetch from both sources in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        newsapi_future = executor.submit(_search_newsapi, query, limit)
        finnhub_future = executor.submit(_search_finnhub_news, query, limit)
        combined = newsapi_future.result() + finnhub_future.result()
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
    Analyze technical indicators for an instrument using real Deriv candle data.
    """
    history = fetch_price_history(instrument=instrument, timeframe=timeframe, count=120)
    candles = history.get("candles", []) or []
    if len(candles) < 20:
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "indicators": {},
            "summary": history.get("error") or "Insufficient candle history for technical analysis.",
            "source": "deriv",
        }

    closes = [float(c["close"]) for c in candles]
    current_price = closes[-1]
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None

    # RSI(14)
    gains = []
    losses = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    period = 14
    avg_gain = sum(gains[-period:]) / period if len(gains) >= period else 0.0
    avg_loss = sum(losses[-period:]) / period if len(losses) >= period else 0.0
    if avg_loss == 0:
        rsi14 = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi14 = 100 - (100 / (1 + rs))

    # Volatility via standard deviation of returns over last 20 bars
    returns = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev:
            returns.append((closes[i] - prev) / prev)
    recent_returns = returns[-20:] if len(returns) >= 20 else returns
    if recent_returns:
        mean_ret = sum(recent_returns) / len(recent_returns)
        variance = sum((r - mean_ret) ** 2 for r in recent_returns) / len(recent_returns)
        vol = math.sqrt(variance)
    else:
        vol = 0.0

    if vol < 0.0025:
        volatility = "low"
    elif vol < 0.0075:
        volatility = "medium"
    else:
        volatility = "high"

    if sma50 is None:
        trend = "neutral"
    elif current_price > sma20 > sma50:
        trend = "bullish"
    elif current_price < sma20 < sma50:
        trend = "bearish"
    else:
        trend = "neutral"

    recent_window = candles[-20:]
    support = min(float(c["low"]) for c in recent_window)
    resistance = max(float(c["high"]) for c in recent_window)

    summary = (
        f"{instrument} on {timeframe}: trend is {trend} with RSI14 at {rsi14:.1f}. "
        f"Nearest support/resistance from recent candles: {support:.4f} / {resistance:.4f}. "
        f"Observed volatility is {volatility}."
    )

    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "current_price": current_price,
        "trend": trend,
        "volatility": volatility,
        "key_levels": {
            "support": round(support, 6),
            "resistance": round(resistance, 6),
        },
        "indicators": {
            "sma20": round(sma20, 6),
            "sma50": round(sma50, 6) if sma50 is not None else None,
            "rsi14": round(rsi14, 2),
        },
        "summary": summary,
        "source": "deriv",
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
        llm = get_llm_client()
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
        llm = get_llm_client()
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
            "explanation": (
                f"Latest move context for {instrument}: {price_context}. "
                "AI-generated explanation is temporarily unavailable."
            ),
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
        discovered: List[str] = []
        try:
            from behavior.models import UserProfile, Trade

            for profile in UserProfile.objects.all().only("watchlist"):
                watchlist = profile.watchlist if isinstance(profile.watchlist, list) else []
                discovered.extend([item for item in watchlist if isinstance(item, str) and item.strip()])

            recent_trades = (
                Trade.objects.order_by("-opened_at", "-created_at")
                .values_list("instrument", flat=True)[:50]
            )
            discovered.extend([inst for inst in recent_trades if inst])
        except Exception:
            discovered = []

        instruments = list(dict.fromkeys(discovered))

    if not instruments:
        return {
            "summary": "No instruments available from database watchlists or recent trades.",
            "instruments": [],
            "timestamp": datetime.now().isoformat(),
            "source": "database",
        }

    # Fetch all instruments in parallel (preserving input order via executor.map)

    def _fetch_instrument(inst: str) -> Dict[str, Any]:
        try:
            price = fetch_price_data(inst)
            history = fetch_price_history(inst, timeframe="1h", count=24)
            return {
                "symbol": inst,
                "price": price.get("price"),
                "change": history.get("change"),
                "change_percent": history.get("change_percent"),
                "source": price.get("source", "deriv"),
            }
        except Exception:
            return {
                "symbol": inst, "price": None, "change": None,
                "change_percent": None, "source": "deriv",
            }

    with ThreadPoolExecutor(max_workers=6) as executor:
        instrument_data = list(executor.map(_fetch_instrument, instruments[:6]))

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
        llm = get_llm_client()
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
        summary_items = []
        for item in instrument_data:
            price = item.get("price")
            change_pct = item.get("change_percent")
            if change_pct is None:
                summary_items.append(f"{item['symbol']}: {price if price is not None else 'N/A'}")
            else:
                summary_items.append(
                    f"{item['symbol']}: {price if price is not None else 'N/A'} ({change_pct:+.2f}%)"
                )

        return {
            "summary": (
                "AI market brief is temporarily unavailable. "
                f"Latest snapshot: {'; '.join(summary_items)}. "
                "This is analysis, not financial advice."
            ),
            "instruments": instrument_data,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# ─── Finnhub Economic Calendar & Pattern Scan ───────────────────────

def fetch_economic_calendar() -> Dict[str, Any]:
    """
    Fetch economic calendar from Finnhub.
    Returns upcoming and recent economic events (Non-Farm Payrolls, CPI, etc.).
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return {"events": [], "error": "FINNHUB_API_KEY not configured"}

    from datetime import timedelta
    today = datetime.now(tz=timezone.utc)
    from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/calendar/economic",
            params={"from": from_date, "to": to_date, "token": api_key},
            timeout=8,
        )
        if response.status_code != 200:
            return {"events": [], "error": f"Finnhub HTTP {response.status_code}"}

        data = response.json()
        raw_events = data.get("economicCalendar", [])
        if not raw_events:
            raw_events = data.get("result", [])

        events = []
        for ev in raw_events[:30]:
            events.append({
                "country": ev.get("country", ""),
                "event": ev.get("event", ""),
                "impact": ev.get("impact", ""),
                "date": ev.get("date", ""),
                "time": ev.get("time", ""),
                "actual": ev.get("actual"),
                "estimate": ev.get("estimate"),
                "prev": ev.get("prev"),
                "unit": ev.get("unit", ""),
            })

        return {
            "events": events,
            "from_date": from_date,
            "to_date": to_date,
            "count": len(events),
            "source": "finnhub",
        }
    except Exception as e:
        return {"events": [], "error": str(e)}


def fetch_finnhub_quote(instrument: str) -> Dict[str, Any]:
    """
    Fetch real-time quote from Finnhub as fallback for Deriv.
    Maps instruments to Finnhub OANDA format.
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return {}

    # Map to Finnhub forex symbol format
    finnhub_map = {
        "EUR/USD": "OANDA:EUR_USD", "GBP/USD": "OANDA:GBP_USD",
        "USD/JPY": "OANDA:USD_JPY", "AUD/USD": "OANDA:AUD_USD",
        "USD/CHF": "OANDA:USD_CHF", "GOLD": "OANDA:XAU_USD",
        "XAU/USD": "OANDA:XAU_USD",
    }
    symbol = finnhub_map.get(instrument)
    if not symbol:
        return {}

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": symbol, "token": api_key},
            timeout=5,
        )
        if response.status_code != 200:
            return {}
        data = response.json()
        return {
            "instrument": instrument,
            "price": data.get("c"),
            "open": data.get("o"),
            "high": data.get("h"),
            "low": data.get("l"),
            "prev_close": data.get("pc"),
            "change": data.get("d"),
            "change_percent": data.get("dp"),
            "source": "finnhub",
        }
    except Exception:
        return {}


def fetch_pattern_recognition(instrument: str, resolution: str = "60") -> Dict[str, Any]:
    """
    Fetch technical pattern recognition from Finnhub.
    Detects head-and-shoulders, triangles, double tops/bottoms, etc.
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return {"patterns": [], "error": "FINNHUB_API_KEY not configured"}

    finnhub_map = {
        "EUR/USD": "OANDA:EUR_USD", "GBP/USD": "OANDA:GBP_USD",
        "USD/JPY": "OANDA:USD_JPY", "AUD/USD": "OANDA:AUD_USD",
        "GOLD": "OANDA:XAU_USD", "XAU/USD": "OANDA:XAU_USD",
    }
    symbol = finnhub_map.get(instrument)
    if not symbol:
        return {"patterns": [], "note": f"No Finnhub mapping for {instrument}"}

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/scan/pattern",
            params={"symbol": symbol, "resolution": resolution, "token": api_key},
            timeout=8,
        )
        if response.status_code != 200:
            return {"patterns": []}
        data = response.json()
        patterns = data.get("points", [])
        return {
            "instrument": instrument,
            "patterns": patterns[:5],
            "count": len(patterns),
            "source": "finnhub",
        }
    except Exception as e:
        return {"patterns": [], "error": str(e)}


# ─── Deriv Active Symbols ────────────────────────────────────────────

def fetch_active_symbols() -> List[Dict[str, Any]]:
    """
    Fetch all available trading instruments from Deriv API.
    Returns categorized list with display names.
    """
    try:
        from behavior.deriv_client import get_deriv_client
        client = get_deriv_client()
        symbols = client.fetch_active_symbols()

        categorized = []
        for s in symbols:
            categorized.append({
                "symbol": s.get("symbol", ""),
                "display_name": s.get("display_name", ""),
                "market": s.get("market", ""),
                "market_display_name": s.get("market_display_name", ""),
                "submarket": s.get("submarket", ""),
                "submarket_display_name": s.get("submarket_display_name", ""),
                "is_trading_suspended": s.get("is_trading_suspended", 0),
                "pip": s.get("pip"),
            })
        return categorized
    except Exception as e:
        # Fallback to hardcoded list
        return [
            {"symbol": k, "display_name": k, "market": "forex", "deriv_symbol": v}
            for k, v in DERIV_SYMBOLS.items()
        ]
