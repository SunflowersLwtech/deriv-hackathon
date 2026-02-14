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
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _is_forex_market_closed() -> bool:
    """Check if forex markets are currently closed (weekend).
    Forex closes Friday ~22:00 UTC, reopens Sunday ~22:00 UTC."""
    now = datetime.now(tz=timezone.utc)
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    hour = now.hour
    if weekday == 5:  # Saturday — always closed
        return True
    if weekday == 6 and hour < 22:  # Sunday before 22:00 UTC
        return True
    if weekday == 4 and hour >= 22:  # Friday after 22:00 UTC
        return True
    return False


def _is_forex_instrument(instrument: str) -> bool:
    """Check if an instrument is a forex/commodity that closes on weekends."""
    deriv_symbol = _get_deriv_symbol(instrument)
    return deriv_symbol.startswith("frx")


# Gracefully handle missing Redis — cache is optional
try:
    from .cache import get_cached_price, set_cached_price
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False
    logger.info("Redis cache not available, running without price cache")


# Deriv symbol mapping: user-friendly -> Deriv API symbol
DERIV_SYMBOLS = {
    # Major forex pairs
    "EUR/USD": "frxEURUSD",
    "GBP/USD": "frxGBPUSD",
    "USD/JPY": "frxUSDJPY",
    "AUD/USD": "frxAUDUSD",
    "USD/CHF": "frxUSDCHF",
    "USD/CAD": "frxUSDCAD",
    "NZD/USD": "frxNZDUSD",
    # Cross pairs
    "EUR/GBP": "frxEURGBP",
    "EUR/JPY": "frxEURJPY",
    "GBP/JPY": "frxGBPJPY",
    "AUD/JPY": "frxAUDJPY",
    "EUR/AUD": "frxEURAUD",
    "EUR/CHF": "frxEURCHF",
    "EUR/CAD": "frxEURCAD",
    "GBP/AUD": "frxGBPAUD",
    "GBP/CHF": "frxGBPCHF",
    "GBP/CAD": "frxGBPCAD",
    # Exotic pairs
    "USD/CNH": "frxUSDCNH",
    "USD/CNY": "frxUSDCNH",  # CNH = offshore yuan on Deriv
    "USD/SGD": "frxUSDSGD",
    "USD/HKD": "frxUSDHKD",
    "USD/MXN": "frxUSDMXN",
    "USD/ZAR": "frxUSDZAR",
    "USD/TRY": "frxUSDTRY",
    "USD/SEK": "frxUSDSEK",
    "USD/NOK": "frxUSDNOK",
    "USD/DKK": "frxUSDDKK",
    # Crypto
    "BTC/USD": "cryBTCUSD",
    "ETH/USD": "cryETHUSD",
    # Metals
    "GOLD": "frxXAUUSD",
    "XAU/USD": "frxXAUUSD",
    "SILVER": "frxXAGUSD",
    "XAG/USD": "frxXAGUSD",
    # Synthetic indices
    "Volatility 75": "R_75",
    "Volatility 75 Index": "R_75",
    "V75": "R_75",
    "Volatility 100": "R_100",
    "V100": "R_100",
    "Volatility 10": "R_10",
    "V10": "R_10",
    "Volatility 25": "R_25",
    "V25": "R_25",
    "Volatility 50": "R_50",
    "V50": "R_50",
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


def _parse_currency_pair(instrument: str) -> Optional[tuple]:
    """Try to parse an instrument string into (base, quote) currency codes.
    Returns None if it doesn't look like a forex pair."""
    # Handles: "CNY/MYR", "cny/myr", "CNYMYR", "USD CNY"
    inst = instrument.strip().upper()
    # Explicit separator
    for sep in ("/", "-", "_", " "):
        if sep in inst:
            parts = inst.split(sep, 1)
            if len(parts) == 2 and len(parts[0]) == 3 and len(parts[1]) == 3:
                return parts[0], parts[1]
    # No separator, 6-char string
    if len(inst) == 6 and inst.isalpha():
        return inst[:3], inst[3:]
    return None


def _fetch_open_exchange_rate(base: str, quote: str) -> Dict[str, Any]:
    """Fetch exchange rate from the free Open Exchange Rates API (no key needed).
    Uses https://open.er-api.com which provides ~170 currencies."""
    try:
        resp = requests.get(
            f"https://open.er-api.com/v6/latest/{base}",
            timeout=6,
        )
        if resp.status_code != 200:
            return {"price": None, "error": f"Exchange rate API HTTP {resp.status_code}"}
        data = resp.json()
        if data.get("result") != "success":
            return {"price": None, "error": "Exchange rate API returned failure"}
        rates = data.get("rates", {})
        rate = rates.get(quote)
        if rate is None:
            return {"price": None, "error": f"Currency {quote} not found in exchange rate data"}
        return {
            "instrument": f"{base}/{quote}",
            "price": round(float(rate), 6),
            "timestamp": data.get("time_last_update_utc", datetime.now(tz=timezone.utc).isoformat()),
            "source": "open.er-api.com (ECB/market rates)",
            "note": "Indicative mid-market rate, not a live trading quote.",
        }
    except Exception as e:
        return {"price": None, "error": f"Exchange rate lookup failed: {e}"}


def fetch_price_data(instrument: str) -> Dict[str, Any]:
    """
    Fetch current price data for an instrument.

    Priority:
    1. Deriv WebSocket API (live trading quotes)
    2. Free exchange rate API fallback (indicative mid-market rates for any
       currency pair Deriv doesn't offer, e.g. CNY/MYR, THB/PHP, etc.)

    Args:
        instrument: Trading instrument symbol (e.g., "EUR/USD", "CNY/MYR")

    Returns:
        Dict with price, change, etc.
    """
    # Weekend guard: forex/commodity markets are closed Fri 22:00 – Sun 22:00 UTC
    if _is_forex_instrument(instrument) and _is_forex_market_closed():
        # Even if Deriv is closed, try the free API for indicative rates
        pair = _parse_currency_pair(instrument)
        if pair:
            fallback = _fetch_open_exchange_rate(pair[0], pair[1])
            if fallback.get("price") is not None:
                fallback["market_closed"] = True
                fallback["note"] = (
                    "Forex market is closed on weekends. "
                    "This is an indicative mid-market rate from the last session."
                )
                return fallback
        return {
            "instrument": instrument,
            "price": None,
            "error": (
                f"{instrument} — Forex market is closed on weekends. "
                "Displaying last session data. Live trading resumes Sunday 22:00 UTC."
            ),
            "market_closed": True,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "source": "deriv",
        }

    # Check cache first (short 5s TTL for live prices)
    if _CACHE_AVAILABLE:
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
        if _CACHE_AVAILABLE and result and result.get("price") is not None:
            try:
                set_cached_price(instrument, result["price"], ttl_seconds=5)
            except Exception as exc:
                logger.debug("Redis cache write failed for %s: %s", instrument, exc)

        # If Deriv returned an error, try free exchange rate API as fallback
        if result.get("price") is None and result.get("error"):
            pair = _parse_currency_pair(instrument)
            if pair:
                fallback = _fetch_open_exchange_rate(pair[0], pair[1])
                if fallback.get("price") is not None:
                    return fallback

        return result
    except Exception as e:
        # Last resort: try free exchange rate API
        pair = _parse_currency_pair(instrument)
        if pair:
            fallback = _fetch_open_exchange_rate(pair[0], pair[1])
            if fallback.get("price") is not None:
                return fallback
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
    # Weekend guard for forex/commodity instruments
    if _is_forex_instrument(instrument) and _is_forex_market_closed():
        return {
            "instrument": instrument,
            "timeframe": timeframe,
            "candles": [],
            "change": 0.0,
            "change_percent": 0.0,
            "error": (
                f"{instrument} — Forex market is closed on weekends. "
                "Live data resumes Sunday 22:00 UTC."
            ),
            "market_closed": True,
            "source": "deriv",
        }

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


def _fetch_finnhub_headlines(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fallback: fetch trading-focused market news from Finnhub (forex, crypto, general).
    Aggregates multiple categories to ensure trading relevance.
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        return []

    categories = ["forex", "crypto", "general"]
    all_articles: List[Dict[str, Any]] = []

    for category in categories:
        try:
            response = requests.get(
                "https://finnhub.io/api/v1/news",
                params={"category": category, "token": api_key},
                timeout=5,
            )
            if response.status_code != 200:
                continue
            items = response.json()
            if not isinstance(items, list):
                continue
            for item in items:
                headline = (item.get("headline") or "").strip()
                if not headline:
                    continue
                all_articles.append({
                    "title": headline,
                    "description": (item.get("summary") or "").strip(),
                    "url": item.get("url", ""),
                    "publishedAt": (
                        datetime.fromtimestamp(item["datetime"], tz=timezone.utc).isoformat()
                        if isinstance(item.get("datetime"), (int, float)) and item["datetime"] > 0
                        else ""
                    ),
                    "source": item.get("source", "Finnhub"),
                    "category": category,
                })
        except Exception:
            continue

    # Deduplicate by URL and sort by date
    seen_urls: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for article in all_articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(article)
    deduped.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return deduped[:limit]


# Terms used by fetch_top_headlines and generate_insights_from_news to filter
# articles for trading relevance.
_TRADING_TERMS = {
    "forex", "trading", "crypto", "bitcoin", "ethereum", "btc", "eth",
    "stock", "market", "usd", "eur", "gbp", "jpy", "gold", "xau",
    "currency", "exchange", "trader", "cfd", "options", "futures",
    "commodities", "oil", "silver", "nasdaq", "dow", "s&p",
}


def fetch_top_headlines(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch top trading & finance headlines from NewsAPI, falling back to Finnhub.
    Focuses on forex, crypto, stocks, commodities, and market news relevant to
    Deriv traders.
    """
    api_key = os.environ.get("NEWS_API_KEY", "")

    if api_key:
        trading_keywords = (
            'forex OR cryptocurrency OR "stock market" OR "bitcoin" '
            'OR "EUR/USD" OR "gold prices" OR "oil prices" OR "crypto market"'
        )
        trusted_sources = (
            "bloomberg,reuters,financial-times,"
            "the-wall-street-journal,cnbc,fortune,business-insider"
        )

        for sources_param in (trusted_sources, None):
            try:
                params: Dict[str, Any] = {
                    "q": trading_keywords,
                    "apiKey": api_key,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": limit * 3,
                }
                if sources_param:
                    params["sources"] = sources_param

                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params=params,
                    timeout=5,
                )
                if response.status_code != 200:
                    continue

                articles = response.json().get("articles", [])
                region_blocklist = {"india", "indian rupee", "mumbai", "delhi", "sensex", "nifty"}

                filtered: List[Dict[str, Any]] = []
                for a in articles:
                    combined = f"{(a.get('title') or '').lower()} {(a.get('description') or '').lower()}"
                    if any(t in combined for t in region_blocklist):
                        continue
                    if any(t in combined for t in _TRADING_TERMS):
                        filtered.append({
                            "title": a.get("title", ""),
                            "description": a.get("description", ""),
                            "url": a.get("url", ""),
                            "publishedAt": a.get("publishedAt", ""),
                            "source": a.get("source", {}).get("name", ""),
                        })
                        if len(filtered) >= limit:
                            break
                if filtered:
                    return filtered
            except Exception as e:
                logger.debug(f"NewsAPI trading headlines failed: {e}")

    # Fallback to Finnhub market news
    return _fetch_finnhub_headlines(limit)


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
        # Fallback: prefer 24/7 instruments (crypto + synthetic indices)
        # so the dashboard always has live data, even on weekends.
        instruments = [
            "cryBTCUSD", "cryETHUSD", "R_100",
            "R_75", "R_10", "frxEURUSD",
        ]

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
        except Exception as exc:
            logger.warning("Failed to fetch data for %s: %s", inst, exc)
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
        if response.status_code == 403:
            return {"events": [], "note": "Economic calendar requires Finnhub premium plan"}
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


# ─── News-based insight generation ──────────────────────────────────


def cleanup_old_insights(keep_count: int = 20) -> int:
    """Remove old insights, keeping only the most recent *keep_count*."""
    try:
        total = MarketInsight.objects.count()
        if total <= keep_count:
            return 0
        keep_ids = list(
            MarketInsight.objects.order_by("-generated_at")
            .values_list("id", flat=True)[:keep_count]
        )
        deleted, _ = MarketInsight.objects.exclude(id__in=keep_ids).delete()
        logger.info(f"Cleaned up {deleted} old insights, kept {keep_count}")
        return deleted
    except Exception as e:
        logger.error(f"Failed to cleanup old insights: {e}")
        return 0


def generate_insights_from_news(limit: int = 8, max_insights: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent headlines, run them through the LLM to produce trading
    insights, and persist the results to ``MarketInsight``.
    """
    try:
        cleanup_old_insights(keep_count=15)

        headlines = fetch_top_headlines(limit=limit)
        if not headlines:
            logger.info("No headlines found for insight generation")
            return []

        news_text = "\n\n".join(
            f"Article {i + 1}:\n"
            f"Title: {a.get('title', '')}\n"
            f"Description: {a.get('description', '')}\n"
            f"Source: {a.get('source', 'Unknown')}\n"
            f"Published: {a.get('publishedAt', '')}"
            for i, a in enumerate(headlines[:limit])
        )

        prompt = (
            f"Based on these recent financial news articles, generate {max_insights} "
            "actionable trading insights for traders.\n\n"
            f"{news_text}\n\n"
            "For each insight:\n"
            "1. Focus on market impact and trading implications\n"
            "2. Be specific about instruments/assets (e.g., BTC/USD, EUR/USD, Gold)\n"
            "3. Keep insights concise (1-2 sentences max)\n"
            '4. Classify the insight type as: "news", "technical", or "sentiment"\n'
            "5. Assign a sentiment score from -1.0 (very bearish) to 1.0 (very bullish)\n\n"
            "Return ONLY a JSON array with this exact format:\n"
            "[\n"
            '  {"instrument": "BTC/USD", "insight_type": "news", '
            '"content": "…", "sentiment_score": 0.6},\n'
            "  ...\n"
            "]\n\n"
            "RULES:\n"
            f"- Generate exactly {max_insights} insights\n"
            "- Each insight must have: instrument, insight_type, content, sentiment_score\n"
            '- insight_type must be one of: "news", "technical", "sentiment"\n'
            "- sentiment_score must be between -1.0 and 1.0\n"
            "- Return ONLY the JSON array, no other text"
        )

        saved: List[Dict[str, Any]] = []

        try:
            llm = get_llm_client()
            response_text = llm.simple_chat(
                system_prompt=SYSTEM_PROMPT_MARKET,
                user_message=prompt,
                temperature=0.4,
                max_tokens=800,
            ).strip()

            # Strip markdown fences if present
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            insights_data = json.loads(response_text)

            top_sources = [
                {"title": h.get("title", ""), "source": h.get("source", ""), "url": h.get("url", "")}
                for h in headlines[:3]
            ]

            for insight in insights_data[:max_insights]:
                try:
                    obj = MarketInsight.objects.create(
                        instrument=insight.get("instrument", "GENERAL"),
                        insight_type=insight.get("insight_type", "news"),
                        content=insight.get("content", ""),
                        sentiment_score=float(insight.get("sentiment_score", 0.0)),
                        sources={"news_articles": top_sources},
                    )
                    saved.append({
                        "id": str(obj.id),
                        "instrument": obj.instrument,
                        "insight_type": obj.insight_type,
                        "content": obj.content,
                        "sentiment_score": obj.sentiment_score,
                        "generated_at": obj.generated_at.isoformat(),
                    })
                except Exception as exc:
                    logger.warning(f"Failed to save insight: {exc}")

        except Exception as exc:
            logger.error(f"LLM insight generation failed, falling back: {exc}")
            # Fallback: create basic insights directly from headlines
            for article in headlines[:max_insights]:
                try:
                    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
                    instrument = "GENERAL"
                    for kw, sym in [
                        ("btc", "BTC/USD"), ("bitcoin", "BTC/USD"),
                        ("eth", "ETH/USD"), ("ethereum", "ETH/USD"),
                        ("eur", "EUR/USD"), ("euro", "EUR/USD"),
                        ("gold", "GOLD"), ("xau", "GOLD"),
                    ]:
                        if kw in text:
                            instrument = sym
                            break
                    obj = MarketInsight.objects.create(
                        instrument=instrument,
                        insight_type="news",
                        content=f"{article.get('title', 'Market Update')}: "
                                f"{(article.get('description') or '')[:150]}",
                        sentiment_score=0.0,
                        sources={"news_source": article.get("source", ""), "url": article.get("url", "")},
                    )
                    saved.append({
                        "id": str(obj.id),
                        "instrument": obj.instrument,
                        "insight_type": obj.insight_type,
                        "content": obj.content,
                        "sentiment_score": obj.sentiment_score,
                        "generated_at": obj.generated_at.isoformat(),
                    })
                except Exception as exc:
                    logger.warning(f"Failed to save fallback insight: {exc}")

        logger.info(f"Generated {len(saved)} insights from {len(headlines)} articles")
        return saved

    except Exception as e:
        logger.error(f"Failed to generate insights from news: {e}")
        return []
