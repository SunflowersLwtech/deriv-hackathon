# behavior/deriv_client.py
# Deriv API WebSocket client for fetching trade history

import json
import asyncio
import websockets
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
import os

from .models import Trade, UserProfile


class DerivAPIError(Exception):
    """Custom exception for Deriv API errors."""
    pass


class DerivClient:
    """
    WebSocket client for Deriv API.
    
    Handles:
    - User authentication
    - Fetching trade history (profit table)
    - Real-time trade updates
    - Syncing trades to database
    """
    
    def __init__(self, app_id: Optional[str] = None):
        """
        Initialize Deriv client.
        
        Args:
            app_id: Deriv app ID (from https://developers.deriv.com/)
        """
        self.app_id = app_id or os.environ.get('DERIV_APP_ID', '')
        if not self.app_id:
            raise ValueError("DERIV_APP_ID is required. Get it from https://developers.deriv.com/")
        self.default_api_token = os.environ.get('DERIV_TOKEN', '')
        
        # Deriv WebSocket endpoints
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
        self.ws_url_demo = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}&l=en&brand=deriv"
        
        self.websocket = None

    def _resolve_api_token(self, api_token: Optional[str]) -> str:
        """Resolve explicit token or fallback to DERIV_TOKEN from environment."""
        token = (api_token or self.default_api_token or "").strip()
        if not token:
            raise DerivAPIError("Deriv API token is required (pass api_token or set DERIV_TOKEN).")
        return token
    
    async def connect(self, demo: bool = False):
        """
        Establish WebSocket connection.
        
        Args:
            demo: Use demo account endpoint
        """
        url = self.ws_url_demo if demo else self.ws_url
        self.websocket = await websockets.connect(url)
        return self.websocket
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request and wait for response.
        
        Args:
            request: Request payload dict
        
        Returns:
            Response dict
        
        Raises:
            DerivAPIError: If API returns error
        """
        if not self.websocket:
            raise DerivAPIError("WebSocket not connected. Call connect() first.")
        
        await self.websocket.send(json.dumps(request))
        response_text = await self.websocket.recv()
        response = json.loads(response_text)
        
        # Check for errors
        if 'error' in response:
            error_msg = response['error'].get('message', 'Unknown error')
            error_code = response['error'].get('code', 'N/A')
            raise DerivAPIError(f"Deriv API Error [{error_code}]: {error_msg}")
        
        return response
    
    async def authorize(self, api_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Authorize user with API token.
        
        Args:
            api_token: User's Deriv API token
        
        Returns:
            Authorization response with user info
        """
        request = {
            "authorize": self._resolve_api_token(api_token)
        }
        
        response = await self.send_request(request)
        
        if 'authorize' not in response:
            raise DerivAPIError("Authorization failed")
        
        return response['authorize']
    
    async def fetch_profit_table(
        self,
        api_token: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's profit table (completed trades).
        
        Args:
            api_token: User's Deriv API token (optional if DERIV_TOKEN is set)
            limit: Max number of trades to fetch (max 500)
            offset: Pagination offset
            date_from: Unix timestamp (optional)
            date_to: Unix timestamp (optional)
        
        Returns:
            List of trade dicts
        """
        # Connect if not already connected
        if not self.websocket:
            await self.connect()
        
        # Authorize first
        await self.authorize(api_token)
        
        # Build request
        request = {
            "profit_table": 1,
            "description": 1,
            "limit": min(limit, 500),  # Deriv max is 500
            "offset": offset,
            "sort": "DESC"  # Most recent first
        }
        
        if date_from:
            request["date_from"] = date_from
        if date_to:
            request["date_to"] = date_to
        
        response = await self.send_request(request)
        
        if 'profit_table' not in response:
            return []
        
        transactions = response['profit_table'].get('transactions', [])
        
        # Parse transactions into our format
        trades = []
        for t in transactions:
            try:
                trade = self._parse_transaction(t)
                trades.append(trade)
            except Exception as e:
                print(f"Error parsing transaction {t.get('transaction_id')}: {e}")
                continue
        
        return trades
    
    def _parse_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Deriv transaction into our trade format.
        
        Args:
            transaction: Raw transaction from Deriv API
        
        Returns:
            Parsed trade dict
        """
        # Extract instrument from contract shortcode
        # Example shortcode: "CALL_R_100_19.54_1234567890_1234567900_S0P_0"
        shortcode = transaction.get('shortcode', '')
        parts = shortcode.split('_')
        
        # Try to extract instrument symbol
        if len(parts) >= 2:
            instrument = parts[1]  # e.g., "R_100", "frxEURUSD"
        else:
            instrument = transaction.get('underlying_symbol', 'UNKNOWN')
        
        # Clean up instrument name
        if instrument.startswith('frx'):
            instrument = instrument[3:]  # Remove 'frx' prefix
        
        # Calculate PnL
        buy_price = Decimal(str(transaction.get('buy_price', 0)))
        sell_price = Decimal(str(transaction.get('sell_price', 0)))
        pnl = sell_price - buy_price
        
        # Parse timestamps
        purchase_time = transaction.get('purchase_time')
        sell_time = transaction.get('sell_time')
        
        opened_at = None
        closed_at = None
        duration_seconds = None
        
        if purchase_time:
            opened_at = datetime.fromtimestamp(purchase_time, tz=timezone.utc)
        
        if sell_time:
            closed_at = datetime.fromtimestamp(sell_time, tz=timezone.utc)
        
        if purchase_time and sell_time:
            duration_seconds = sell_time - purchase_time
        
        # Determine direction from shortcode
        direction = 'UNKNOWN'
        if shortcode.startswith('CALL'):
            direction = 'LONG'
        elif shortcode.startswith('PUT'):
            direction = 'SHORT'
        
        return {
            'contract_id': transaction.get('contract_id'),
            'transaction_id': transaction.get('transaction_id'),
            'instrument': instrument,
            'direction': direction,
            'pnl': pnl,
            'entry_price': buy_price,
            'exit_price': sell_price,
            'opened_at': opened_at,
            'closed_at': closed_at,
            'duration_seconds': duration_seconds,
            'shortcode': shortcode,
            'app_id': transaction.get('app_id'),
            'longcode': transaction.get('longcode', '')
        }
    
    async def fetch_all_trades(
        self,
        api_token: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch all trades from the last N days (handles pagination).
        
        Args:
            api_token: User's Deriv API token (optional if DERIV_TOKEN is set)
            days_back: How many days of history to fetch
        
        Returns:
            Complete list of trades
        """
        from datetime import timedelta
        
        date_from = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        all_trades = []
        offset = 0
        limit = 500  # Max per request
        
        while True:
            trades = await self.fetch_profit_table(
                api_token=api_token,
                limit=limit,
                offset=offset,
                date_from=date_from
            )
            
            if not trades:
                break
            
            all_trades.extend(trades)
            
            # If we got less than limit, we're done
            if len(trades) < limit:
                break
            
            offset += limit
        
        return all_trades
    
    def sync_trades_to_database(
        self,
        user_id: str,
        api_token: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Sync user's Deriv trades to our database.
        
        Args:
            user_id: Our UserProfile UUID
            api_token: User's Deriv API token (optional if DERIV_TOKEN is set)
            days_back: Days of history to sync
        
        Returns:
            {
                'success': bool,
                'trades_fetched': int,
                'trades_created': int,
                'trades_updated': int,
                'errors': List[str]
            }
        """
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return {
                'success': False,
                'error': f'User {user_id} not found',
                'trades_fetched': 0,
                'trades_created': 0,
                'trades_updated': 0,
                'errors': ['User not found']
            }
        
        # Fetch trades from Deriv (use fresh client in dedicated thread)
        try:
            async def _fetch_trades():
                client = DerivClient(self.app_id)
                try:
                    return await client.fetch_all_trades(api_token, days_back)
                finally:
                    await client.disconnect()
            trades = self._run_async(_fetch_trades())
        except DerivAPIError as e:
            return {
                'success': False,
                'error': str(e),
                'trades_fetched': 0,
                'trades_created': 0,
                'trades_updated': 0,
                'errors': [str(e)]
            }
        
        trades_created = 0
        trades_updated = 0
        errors = []
        
        # Save to database
        for trade_data in trades:
            try:
                # Use contract_id as unique identifier to avoid duplicates
                contract_id = trade_data.get('contract_id')
                
                if not contract_id:
                    errors.append(f"Missing contract_id for transaction {trade_data.get('transaction_id')}")
                    continue
                
                # No contract_id column exists in Trade, so dedupe by a natural key
                # derived from Deriv trade payload fields.
                existing_qs = Trade.objects.filter(
                    user=user,
                    instrument=trade_data.get('instrument'),
                    direction=trade_data.get('direction'),
                )

                opened_at = trade_data.get('opened_at')
                if opened_at is not None:
                    existing_qs = existing_qs.filter(opened_at=opened_at)

                closed_at = trade_data.get('closed_at')
                if closed_at is not None:
                    existing_qs = existing_qs.filter(closed_at=closed_at)

                entry_price = trade_data.get('entry_price')
                if entry_price is not None:
                    existing_qs = existing_qs.filter(entry_price=entry_price)

                existing = existing_qs.first()
                
                if existing:
                    # Update existing
                    existing.pnl = trade_data['pnl']
                    existing.closed_at = trade_data['closed_at']
                    existing.duration_seconds = trade_data['duration_seconds']
                    existing.save()
                    trades_updated += 1
                else:
                    # Create new
                    Trade.objects.create(
                        user=user,
                        instrument=trade_data['instrument'],
                        direction=trade_data['direction'],
                        pnl=trade_data['pnl'],
                        entry_price=trade_data['entry_price'],
                        exit_price=trade_data['exit_price'],
                        opened_at=trade_data['opened_at'],
                        closed_at=trade_data['closed_at'],
                        duration_seconds=trade_data['duration_seconds'],
                        is_mock=False
                    )
                    trades_created += 1
                    
            except Exception as e:
                errors.append(f"Error saving trade {contract_id}: {str(e)}")
                continue
        
        return {
            'success': True,
            'trades_fetched': len(trades),
            'trades_created': trades_created,
            'trades_updated': trades_updated,
            'errors': errors
        }
    
    @staticmethod
    def _run_async(coro):
        """Run an async coroutine safely from sync Django context.
        Uses a dedicated thread with its own event loop to avoid
        conflicts with Django Channels' running loop."""
        import concurrent.futures, threading

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

    def fetch_portfolio(self, api_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch user's open positions (portfolio)."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({"portfolio": 1})
                return resp.get("portfolio", {})
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def fetch_balance(self, api_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch user's account balance."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({"balance": 1})
                return resp.get("balance", {})
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def fetch_reality_check(self, api_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch Deriv official trading session health check."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({"reality_check": 1})
                return resp.get("reality_check", {})
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    # ─── Contract Trading Methods (Demo only) ─────────────────────────

    def get_contract_proposal(
        self,
        symbol: str = "R_100",
        contract_type: str = "CALL",
        amount: float = 10,
        basis: str = "stake",
        duration: int = 5,
        duration_unit: str = "t",
        api_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a contract price quote. Returns proposal_id for buying."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({
                    "proposal": 1,
                    "amount": amount,
                    "basis": basis,
                    "contract_type": contract_type,
                    "currency": "USD",
                    "duration": duration,
                    "duration_unit": duration_unit,
                    "symbol": symbol,
                })
                proposal = resp.get("proposal", {})
                return {
                    "proposal_id": proposal.get("id", ""),
                    "ask_price": float(proposal.get("ask_price", 0)),
                    "payout": float(proposal.get("payout", 0)),
                    "spot": float(proposal.get("spot", 0)),
                    "spot_time": proposal.get("spot_time"),
                    "date_expiry": proposal.get("date_expiry"),
                    "longcode": proposal.get("longcode", ""),
                    "display_value": proposal.get("display_value", ""),
                    "contract_type": contract_type,
                    "symbol": symbol,
                }
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def buy_contract(
        self,
        proposal_id: str,
        price: float,
        api_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Buy a contract using a proposal id."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({
                    "buy": proposal_id,
                    "price": price,
                })
                buy_data = resp.get("buy", {})
                return {
                    "contract_id": buy_data.get("contract_id"),
                    "buy_price": float(buy_data.get("buy_price", 0)),
                    "balance_after": float(buy_data.get("balance_after", 0)),
                    "longcode": buy_data.get("longcode", ""),
                    "start_time": buy_data.get("start_time"),
                    "transaction_id": buy_data.get("transaction_id"),
                }
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def quote_and_buy(
        self,
        symbol: str = "R_100",
        contract_type: str = "CALL",
        amount: float = 10,
        basis: str = "stake",
        duration: int = 5,
        duration_unit: str = "t",
        api_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a proposal and immediately buy it in the SAME WebSocket session."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                # Step 1: get proposal
                resp = await client.send_request({
                    "proposal": 1,
                    "amount": amount,
                    "basis": basis,
                    "contract_type": contract_type,
                    "currency": "USD",
                    "duration": duration,
                    "duration_unit": duration_unit,
                    "symbol": symbol,
                })
                proposal = resp.get("proposal", {})
                proposal_id = proposal.get("id", "")
                ask_price = float(proposal.get("ask_price", 0))

                if not proposal_id:
                    return {"error": "Failed to get proposal ID from Deriv API"}

                # Step 2: buy immediately on the same connection
                buy_resp = await client.send_request({
                    "buy": proposal_id,
                    "price": ask_price,
                })
                buy_data = buy_resp.get("buy", {})
                return {
                    "contract_id": buy_data.get("contract_id"),
                    "buy_price": float(buy_data.get("buy_price", 0)),
                    "balance_after": float(buy_data.get("balance_after", 0)),
                    "longcode": buy_data.get("longcode", ""),
                    "start_time": buy_data.get("start_time"),
                    "transaction_id": buy_data.get("transaction_id"),
                    "payout": float(proposal.get("payout", 0)),
                    "spot": float(proposal.get("spot", 0)),
                    "contract_type": contract_type,
                    "symbol": symbol,
                }
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def sell_contract(
        self,
        contract_id: int,
        price: float = 0,
        api_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sell/close an open contract. price=0 means market price."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({
                    "sell": contract_id,
                    "price": price,
                })
                sell_data = resp.get("sell", {})
                return {
                    "contract_id": contract_id,
                    "sold_for": float(sell_data.get("sold_for", 0)),
                    "balance_after": float(sell_data.get("balance_after", 0)),
                    "transaction_id": sell_data.get("transaction_id"),
                }
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    def get_open_contracts(
        self, api_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all currently open (unsettled) contracts."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                await client.authorize(api_token)
                resp = await client.send_request({"proposal_open_contract": 1})
                contracts = resp.get("proposal_open_contract", {}).get("open_contracts", [])
                result = []
                for c in contracts:
                    result.append({
                        "contract_id": c.get("contract_id"),
                        "contract_type": c.get("contract_type", ""),
                        "symbol": c.get("underlying", ""),
                        "buy_price": float(c.get("buy_price", 0)),
                        "current_spot": float(c.get("current_spot", 0)),
                        "profit": float(c.get("profit", 0)),
                        "payout": float(c.get("payout", 0)),
                        "is_valid_to_sell": c.get("is_valid_to_sell", 0) == 1,
                        "is_expired": c.get("is_expired", 0) == 1,
                        "longcode": c.get("longcode", ""),
                        "date_expiry": c.get("date_expiry"),
                    })
                return result
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    # ─── Active Symbols ──────────────────────────────────────────────

    def fetch_active_symbols(self) -> List[Dict[str, Any]]:
        """Fetch all available trading instruments (no auth required)."""
        async def _fetch():
            client = DerivClient(self.app_id)
            try:
                await client.connect()
                resp = await client.send_request({
                    "active_symbols": "brief",
                    "product_type": "basic"
                })
                return resp.get("active_symbols", [])
            finally:
                await client.disconnect()
        return self._run_async(_fetch())

    async def subscribe_to_transactions(
        self,
        callback: callable,
        api_token: Optional[str] = None,
    ):
        """
        Subscribe to real-time transaction updates.
        
        Args:
            api_token: User's Deriv API token (optional if DERIV_TOKEN is set)
            callback: Function to call when new transaction arrives
        """
        if not self.websocket:
            await self.connect()
        
        # Authorize
        await self.authorize(api_token)
        
        # Subscribe to transactions
        request = {
            "transaction": 1,
            "subscribe": 1
        }
        
        response = await self.send_request(request)
        
        # Listen for updates
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if 'transaction' in data:
                    transaction = data['transaction']
                    parsed_trade = self._parse_transaction(transaction)
                    await callback(parsed_trade)
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")


# Singleton instance
_deriv_client = None

def get_deriv_client() -> DerivClient:
    """Get or create singleton Deriv client instance."""
    global _deriv_client
    if _deriv_client is None:
        _deriv_client = DerivClient()
    return _deriv_client
