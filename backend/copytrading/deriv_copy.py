"""
Deriv Copy Trading API Client
Integrates: copy_start, copy_stop, copytrading_list, copytrading_statistics
"""
import json
import asyncio
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
import os


class DerivCopyTradingClient:
    """
    Deriv Copy Trading WebSocket client.

    API endpoints:
    - copytrading_list: list copiers/traders
    - copytrading_statistics: trader performance stats
    - copy_start: start copying a trader
    - copy_stop: stop copying a trader
    """

    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id or os.environ.get("DERIV_APP_ID", "")
        self.default_api_token = os.environ.get("DERIV_TOKEN", "")
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"

    def _resolve_api_token(self, api_token: Optional[str] = None) -> str:
        token = (api_token or self.default_api_token or "").strip()
        if not token:
            raise ValueError("Deriv API token is required (pass api_token or set DERIV_TOKEN).")
        return token

    @staticmethod
    def _run_async(coro):
        """Run an async coroutine from sync Django context (dedicated thread)."""
        result = [None]
        exception = [None]

        def _thread_target():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result[0] = loop.run_until_complete(coro)
            except Exception as e:
                exception[0] = e
            finally:
                loop.close()

        t = threading.Thread(target=_thread_target)
        t.start()
        t.join(timeout=30)
        if exception[0]:
            raise exception[0]
        return result[0]

    def get_copytrading_list(self, api_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of copiers and traders.

        Returns:
            {"copiers": [...], "traders": [...]}
        """
        async def _fetch():
            import websockets
            token = self._resolve_api_token(api_token)
            async with websockets.connect(self.ws_url, close_timeout=10) as ws:
                # Authorize
                await ws.send(json.dumps({"authorize": token}))
                auth_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if "error" in auth_resp:
                    return {"error": auth_resp["error"].get("message", "Authorization failed")}

                # Get copytrading list
                await ws.send(json.dumps({"copytrading_list": 1}))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if "error" in resp:
                    return {"error": resp["error"].get("message", "Failed to fetch copytrading list")}

                ct_list = resp.get("copytrading_list", {})
                return {
                    "copiers": ct_list.get("copiers", []),
                    "traders": ct_list.get("traders", []),
                }

        try:
            return self._run_async(_fetch())
        except Exception as e:
            return {"error": str(e)}

    def get_copytrading_statistics(
        self, trader_id: str, api_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific trader.

        Returns performance data: win rate, avg profit/loss, copiers count, etc.
        """
        async def _fetch():
            import websockets
            token = self._resolve_api_token(api_token)
            async with websockets.connect(self.ws_url, close_timeout=10) as ws:
                await ws.send(json.dumps({"authorize": token}))
                auth_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if "error" in auth_resp:
                    return {"error": auth_resp["error"].get("message", "Authorization failed")}

                await ws.send(json.dumps({
                    "copytrading_statistics": 1,
                    "trader_id": trader_id,
                }))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if "error" in resp:
                    return {"error": resp["error"].get("message", "Failed to fetch statistics")}

                stats = resp.get("copytrading_statistics", {})
                return {
                    "trader_id": trader_id,
                    "active_since": stats.get("active_since"),
                    "avg_duration": stats.get("avg_duration"),
                    "avg_loss": stats.get("avg_loss"),
                    "avg_profit": stats.get("avg_profit"),
                    "copiers": stats.get("copiers", 0),
                    "last_12months_profitable_trades": stats.get("last_12months_profitable_trades", 0),
                    "monthly_profitable_trades": stats.get("monthly_profitable_trades", {}),
                    "performance_probability": stats.get("performance_probability", 0),
                    "total_trades": stats.get("total_trades", 0),
                    "trades_breakdown": stats.get("trades_breakdown", {}),
                    "trades_profitable": stats.get("trades_profitable", 0),
                    "yearly_profitable_trades": stats.get("yearly_profitable_trades", {}),
                }

        try:
            return self._run_async(_fetch())
        except Exception as e:
            return {"error": str(e)}

    def start_copy(
        self,
        trader_id: str,
        api_token: Optional[str] = None,
        assets: Optional[List[str]] = None,
        max_trade_stake: Optional[float] = None,
        min_trade_stake: Optional[float] = None,
        trade_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Start copying a trader (Demo account only).

        Note: trader_id here should be the trader's copy token, not loginid.
        """
        async def _fetch():
            import websockets
            token = self._resolve_api_token(api_token)
            async with websockets.connect(self.ws_url, close_timeout=10) as ws:
                await ws.send(json.dumps({"authorize": token}))
                auth_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if "error" in auth_resp:
                    return {"error": auth_resp["error"].get("message", "Authorization failed")}

                request = {"copy_start": trader_id}
                if assets:
                    request["assets"] = assets
                if max_trade_stake is not None:
                    request["max_trade_stake"] = max_trade_stake
                if min_trade_stake is not None:
                    request["min_trade_stake"] = min_trade_stake
                if trade_types:
                    request["trade_types"] = trade_types

                await ws.send(json.dumps(request))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if "error" in resp:
                    return {"error": resp["error"].get("message", "Failed to start copy trading")}

                return {
                    "success": True,
                    "copy_start": resp.get("copy_start", 1),
                    "trader_id": trader_id,
                    "disclaimer": "DEMO account only. Copy trading involves risk. Past performance is not indicative of future results.",
                }

        try:
            return self._run_async(_fetch())
        except Exception as e:
            return {"error": str(e)}

    def stop_copy(
        self, trader_id: str, api_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Stop copying a trader."""
        async def _fetch():
            import websockets
            token = self._resolve_api_token(api_token)
            async with websockets.connect(self.ws_url, close_timeout=10) as ws:
                await ws.send(json.dumps({"authorize": token}))
                auth_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if "error" in auth_resp:
                    return {"error": auth_resp["error"].get("message", "Authorization failed")}

                await ws.send(json.dumps({"copy_stop": trader_id}))
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

                if "error" in resp:
                    return {"error": resp["error"].get("message", "Failed to stop copy trading")}

                return {
                    "success": True,
                    "copy_stop": resp.get("copy_stop", 1),
                    "trader_id": trader_id,
                }

        try:
            return self._run_async(_fetch())
        except Exception as e:
            return {"error": str(e)}

    def analyze_trader_compatibility(
        self, trader_stats: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI analysis: match trader style with user profile.

        Dimensions:
        - Risk preference (avg_loss/avg_profit ratio)
        - Trading frequency
        - Win rate alignment
        - Profitability assessment
        """
        try:
            # Trader metrics
            t_win_rate = 0
            if trader_stats.get("total_trades", 0) > 0:
                t_win_rate = (
                    trader_stats.get("trades_profitable", 0)
                    / trader_stats["total_trades"]
                    * 100
                )
            t_avg_profit = abs(float(trader_stats.get("avg_profit", 0)))
            t_avg_loss = abs(float(trader_stats.get("avg_loss", 1)))
            t_risk_ratio = t_avg_profit / t_avg_loss if t_avg_loss > 0 else 0

            # User metrics
            u_win_rate = float(user_profile.get("win_rate", 50))
            u_avg_win = abs(float(user_profile.get("avg_win", 5)))
            u_avg_loss = abs(float(user_profile.get("avg_loss", 5)))
            u_risk_ratio = u_avg_win / u_avg_loss if u_avg_loss > 0 else 0

            # Scoring (0-100)
            # Win rate similarity (closer = better)
            wr_diff = abs(t_win_rate - u_win_rate)
            wr_score = max(0, 100 - wr_diff * 2)

            # Risk ratio compatibility
            rr_diff = abs(t_risk_ratio - u_risk_ratio)
            rr_score = max(0, 100 - rr_diff * 20)

            # Profitability bonus
            perf_score = min(100, float(trader_stats.get("performance_probability", 0)) * 100)

            # Copiers trust signal
            copier_score = min(100, trader_stats.get("copiers", 0) * 10)

            compatibility_score = int(
                wr_score * 0.3 + rr_score * 0.25 + perf_score * 0.3 + copier_score * 0.15
            )

            strengths = []
            risks = []

            if t_win_rate > 60:
                strengths.append(f"High win rate ({t_win_rate:.0f}%)")
            if t_risk_ratio > 1.5:
                strengths.append(f"Good risk/reward ratio ({t_risk_ratio:.1f})")
            if trader_stats.get("copiers", 0) > 5:
                strengths.append(f"{trader_stats['copiers']} active copiers")
            if perf_score > 70:
                strengths.append("Strong historical performance")

            if t_win_rate < 45:
                risks.append(f"Low win rate ({t_win_rate:.0f}%)")
            if t_risk_ratio < 0.8:
                risks.append("Average losses exceed average profits")
            if rr_diff > 1.5:
                risks.append("Risk style differs significantly from yours")
            if trader_stats.get("total_trades", 0) < 50:
                risks.append("Limited trading history")

            return {
                "compatibility_score": compatibility_score,
                "strengths": strengths or ["Active trader with documented history"],
                "risks": risks or ["As with all trading, past performance is not indicative of future results"],
                "recommendation": (
                    f"Based on historical data, this trader's style shows "
                    f"a {compatibility_score}% compatibility with your profile. "
                    f"This is educational analysis, not financial advice."
                ),
            }

        except Exception as e:
            return {
                "compatibility_score": 0,
                "strengths": [],
                "risks": [str(e)],
                "recommendation": "Unable to analyze compatibility at this time.",
            }
