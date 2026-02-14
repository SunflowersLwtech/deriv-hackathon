"""
Demo Health Check — Run 5 minutes before the demo.
Ensures all dependency services are operational.
"""
import time
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("tradeiq.demo")


def check_demo_readiness() -> Dict[str, Any]:
    """
    Check all demo dependencies are ready.

    Returns:
        {
            "ready": true/false,
            "checks": { service: {status, latency_ms}, ... },
            "warnings": [...]
        }
    """
    checks = {}
    warnings = []

    # 1. Database
    checks["database"] = _check_database()

    # 2. DeepSeek LLM
    checks["deepseek_llm"] = _check_llm()
    if checks["deepseek_llm"].get("latency_ms", 0) > 5000:
        warnings.append("LLM latency >5s — streaming may feel slow")

    # 3. Redis / channel layer
    checks["redis"] = _check_redis()

    # 4. Demo data
    checks["demo_data"] = _check_demo_data()

    # 5. Bluesky
    checks["bluesky"] = _check_bluesky()
    if checks["bluesky"]["status"] == "error":
        warnings.append("Bluesky unavailable — live publish step will use fallback")

    # 6. Demo cache
    checks["demo_cache"] = _check_demo_cache()

    all_ok = all(
        c.get("status") == "ok"
        for key, c in checks.items()
        if key not in ("bluesky", "demo_cache")  # Non-critical
    )

    return {
        "ready": all_ok,
        "checks": checks,
        "warnings": warnings,
    }


def _check_database() -> Dict[str, Any]:
    try:
        start = time.time()
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = int((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_llm() -> Dict[str, Any]:
    try:
        start = time.time()
        from agents.llm_client import get_llm_client
        llm = get_llm_client()
        llm.simple_chat("You are a test.", "Say OK.", max_tokens=5)
        latency = int((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_redis() -> Dict[str, Any]:
    try:
        start = time.time()
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        if layer is None:
            return {"status": "error", "error": "No channel layer configured"}
        latency = int((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_demo_data() -> Dict[str, Any]:
    try:
        from behavior.models import Trade
        count = Trade.objects.filter(
            user_id="d1000000-0000-0000-0000-000000000001"
        ).count()
        return {"status": "ok", "trades_count": count}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_bluesky() -> Dict[str, Any]:
    try:
        bsky_handle = os.environ.get("BSKY_HANDLE", "")
        bsky_password = os.environ.get("BSKY_APP_PASSWORD", "")
        if not bsky_handle or not bsky_password:
            return {"status": "error", "error": "BSKY credentials not configured"}
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_demo_cache() -> Dict[str, Any]:
    try:
        from demo.fallback import _demo_cache
        cached_keys = list(_demo_cache.keys())
        return {"status": "ok", "cached_steps": len(cached_keys), "keys": cached_keys}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
