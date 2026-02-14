"""
Real-time Market Monitor — TradeIQ's heartbeat.

Architecture:
1. Background daemon thread scans watchlist every 5 seconds
2. Compares current price to cached previous price
3. On >1% change, triggers 5-Agent Pipeline in a separate thread
4. Pipeline result pushed to all connected WebSocket clients via Django Channels
5. Frontend receives push and renders MarketAlertToast

Startup: MarketConfig.ready() or `python manage.py run_monitor`
"""
import threading
import time
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger("tradeiq.monitor")

SCAN_INTERVAL_SECONDS = 5
VOLATILITY_THRESHOLD_PCT = 1.0
HIGH_VOLATILITY_PCT = 3.0
DEFAULT_WATCHLIST = [
    "BTC/USD", "ETH/USD", "EUR/USD", "GBP/USD",
    "Volatility 100 Index", "Volatility 75 Index",
]

_price_cache: Dict[str, float] = {}
_monitor_instance: Optional["MarketMonitor"] = None


class MarketMonitor:
    """Continuously monitors market prices and triggers alerts on volatility."""

    def __init__(self, watchlist: Optional[List[str]] = None):
        self.watchlist = watchlist or DEFAULT_WATCHLIST
        self.channel_layer = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            logger.warning("Monitor already running")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="market-monitor"
        )
        self._thread.start()
        logger.info(
            "Market monitor started. Watching %d instruments every %ds",
            len(self.watchlist), SCAN_INTERVAL_SECONDS,
        )

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Market monitor stopped")

    def _monitor_loop(self):
        while self._running:
            try:
                self._scan_markets()
            except Exception as exc:
                logger.error("Monitor scan error: %s", exc, exc_info=True)
            time.sleep(SCAN_INTERVAL_SECONDS)

    def _scan_markets(self):
        from market.tools import fetch_price_data

        for instrument in self.watchlist:
            try:
                result = fetch_price_data(instrument)
                if "error" in result or not result.get("price"):
                    continue

                current_price = float(result["price"])
                cached_price = _price_cache.get(instrument)

                if cached_price is not None and cached_price > 0:
                    change_pct = ((current_price - cached_price) / cached_price) * 100
                    if abs(change_pct) >= VOLATILITY_THRESHOLD_PCT:
                        self._handle_volatility_event(
                            instrument=instrument,
                            current_price=current_price,
                            previous_price=cached_price,
                            change_pct=change_pct,
                        )

                _price_cache[instrument] = current_price
            except Exception as exc:
                logger.warning("Error scanning %s: %s", instrument, exc)

    def _handle_volatility_event(
        self,
        instrument: str,
        current_price: float,
        previous_price: float,
        change_pct: float,
    ):
        direction = "spike" if change_pct > 0 else "drop"
        magnitude = "high" if abs(change_pct) >= HIGH_VOLATILITY_PCT else "medium"

        logger.info(
            "VOLATILITY EVENT: %s %s %+.2f%% (%.2f -> %.2f)",
            instrument, direction, change_pct, previous_price, current_price,
        )

        threading.Thread(
            target=self._run_pipeline_and_push,
            args=(instrument, current_price, change_pct, direction, magnitude),
            daemon=True,
            name=f"pipeline-{instrument}",
        ).start()

    def _run_pipeline_and_push(
        self,
        instrument: str,
        price: float,
        change_pct: float,
        direction: str,
        magnitude: str,
    ):
        try:
            from agents.agent_team import run_pipeline

            result = run_pipeline(
                instruments=[instrument],
                custom_event={
                    "instrument": instrument,
                    "price": price,
                    "change_pct": change_pct,
                },
            )

            notification = {
                "type": "market_alert",
                "data": {
                    "instrument": instrument,
                    "price": price,
                    "change_pct": round(change_pct, 2),
                    "direction": direction,
                    "magnitude": magnitude,
                    "timestamp": datetime.now().isoformat(),
                    "analysis_summary": "",
                    "behavioral_warning": "",
                    "content_draft": "",
                },
            }

            # Extract pipeline results safely
            if result:
                r = result if isinstance(result, dict) else {}
                ar = r.get("analysis_report") or {}
                si = r.get("sentinel_insight") or {}
                mc = r.get("market_commentary") or {}
                notification["data"]["analysis_summary"] = (
                    ar.get("event_summary", "") if isinstance(ar, dict) else ""
                )
                notification["data"]["behavioral_warning"] = (
                    si.get("personalized_warning", "") if isinstance(si, dict) else ""
                )
                notification["data"]["content_draft"] = (
                    mc.get("post", "") if isinstance(mc, dict) else ""
                )

            self._push_to_websocket(notification)
        except Exception as exc:
            logger.error("Pipeline error for %s: %s", instrument, exc, exc_info=True)

    def _push_to_websocket(self, notification: dict):
        try:
            if self.channel_layer is None:
                self.channel_layer = get_channel_layer()
            if self.channel_layer:
                async_to_sync(self.channel_layer.group_send)(
                    "market_alerts",
                    {"type": "market.alert", "message": json.dumps(notification)},
                )
                logger.info("Pushed alert for %s", notification["data"]["instrument"])
        except Exception as exc:
            logger.warning("WebSocket push failed: %s", exc)


def get_monitor() -> MarketMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MarketMonitor()
    return _monitor_instance


def start_monitor() -> MarketMonitor:
    monitor = get_monitor()
    monitor.start()
    return monitor
