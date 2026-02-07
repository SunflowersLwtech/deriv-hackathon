"""
Redis client singleton for TradeIQ price caching.
Uses Upstash Redis (TLS required).

Provides helpers for caching instrument prices and computing
real price change percentages for the Market Monitor agent.
"""
import os
import redis
from typing import Optional


_redis_client: Optional[redis.Redis] = None


def _clean_redis_url() -> str:
    """
    Parse REDIS_URL from environment.
    Handles the ``redis-cli --tls -u redis://...`` prefix format
    that Upstash sometimes displays.
    Ensures TLS by converting redis:// to rediss://.
    """
    raw_url = os.environ.get("REDIS_URL", "")

    # Strip 'redis-cli --tls -u ' prefix if present
    if "redis-cli" in raw_url:
        idx = raw_url.find("redis://")
        if idx == -1:
            idx = raw_url.find("rediss://")
        if idx >= 0:
            raw_url = raw_url[idx:]

    # Ensure TLS (Upstash requires it)
    if raw_url.startswith("redis://") and "upstash" in raw_url:
        raw_url = "rediss://" + raw_url[len("redis://"):]

    return raw_url.strip()


def get_redis_client() -> redis.Redis:
    """Get or create singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        url = _clean_redis_url()
        if not url:
            raise ValueError("REDIS_URL not set in environment")
        _redis_client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


def get_cached_price(instrument: str) -> Optional[float]:
    """Get the last cached price for an instrument."""
    try:
        r = get_redis_client()
        key = f"tradeiq:price:{instrument}"
        val = r.get(key)
        return float(val) if val is not None else None
    except Exception as e:
        print(f"[Redis] get_cached_price error: {e}")
        return None


def set_cached_price(instrument: str, price: float, ttl_seconds: int = 300):
    """Store current price in Redis with TTL (default 5 minutes)."""
    try:
        r = get_redis_client()
        key = f"tradeiq:price:{instrument}"
        r.setex(key, ttl_seconds, str(price))
    except Exception as e:
        print(f"[Redis] set_cached_price error: {e}")
