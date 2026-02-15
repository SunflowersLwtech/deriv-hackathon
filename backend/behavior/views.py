# behavior/views.py
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

logger = logging.getLogger(__name__)

from .models import UserProfile, Trade, BehavioralMetric
from .serializers import UserProfileSerializer, TradeSerializer, BehavioralMetricSerializer
from .tools import (
    analyze_trade_patterns,
    generate_behavioral_nudge_with_ai,
    get_trading_statistics,
)
from rest_framework.permissions import AllowAny
from tradeiq.permissions import IsAuthenticatedOrReadOnly

DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001"


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by("-created_at")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Get trading statistics for a user.
        GET /api/behavior/profiles/{id}/statistics/?days=30
        """
        user = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        stats = get_trading_statistics(str(user.id), days=days)
        
        return Response(stats)


class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    # Keep reads public while requiring auth for writes.
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter trades by user if user_id provided."""
        queryset = Trade.objects.all()
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-opened_at', '-created_at')
    
    def create(self, request, *args, **kwargs):
        """
        Override create to trigger behavioral analysis after each trade.
        This is the key integration point - every trade triggers pattern detection.
        """
        # Create the trade first
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        trade = serializer.instance
        
        # Trigger behavioral analysis for this user
        try:
            self._analyze_and_nudge(trade.user)
        except Exception as e:
            logger.warning("Error in behavioral analysis: %s", e)
            # Don't fail the trade creation if analysis fails

        # Trigger live narrator
        try:
            from behavior.narrator import narrate_trade_event
            narrate_trade_event(
                user_id=str(trade.user_id),
                trade_data={
                    "instrument": trade.instrument,
                    "direction": trade.direction,
                    "entry_price": str(trade.entry_price) if trade.entry_price else None,
                    "pnl": str(trade.pnl) if trade.pnl else None,
                },
                event_type="new_trade",
            )
        except Exception as e:
            logger.debug("Narrator event failed (non-blocking): %s", e)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _analyze_and_nudge(self, user):
        """
        Internal method to analyze patterns and send nudge via WebSocket.
        Metric saving is handled by the post_save signal in signals.py
        which includes the full dataset (win_count, loss_count, avg_hold_time).
        """
        # Analyze recent trades (last 24 hours)
        analysis = analyze_trade_patterns(str(user.id), hours=24)

        if analysis['needs_nudge']:
            # Generate AI-powered nudge
            nudge = generate_behavioral_nudge_with_ai(str(user.id), analysis)

            # Send nudge via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_user_{user.id}",
                {
                    "type": "chat_message",
                    "message": {
                        "type": "behavioral_nudge",
                        "nudge_type": nudge['nudge_type'],
                        "message": nudge['message'],
                        "severity": nudge['severity'],
                        "suggested_action": nudge['suggested_action'],
                        "timestamp": timezone.now().isoformat(),
                        "user_id": str(user.id)
                    }
                }
            )
    
    @action(detail=False, methods=['post'])
    def analyze_batch(self, request):
        """
        Analyze a batch of trades for demo purposes.
        POST /api/behavior/trades/analyze_batch/
        {
            "user_id": "uuid",
            "hours": 24
        }
        """
        user_id = request.data.get('user_id')
        hours = request.data.get('hours', 24)
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Run analysis
        analysis = analyze_trade_patterns(user_id, hours=hours)
        
        # Generate nudge if needed
        nudge = None
        if analysis['needs_nudge']:
            nudge = generate_behavioral_nudge_with_ai(user_id, analysis)
        
        return Response({
            'analysis': analysis,
            'nudge': nudge
        })
    
    @action(detail=False, methods=['post'])
    def sync_deriv(self, request):
        """
        Sync real trades from Deriv API.
        POST /api/behavior/trades/sync_deriv/
        {"user_id": "optional-uuid", "days_back": 30}

        Uses per-user Deriv token (from deriv_auth) with env DERIV_TOKEN fallback.
        """
        from deriv_auth.middleware import get_deriv_token
        from .trade_sync import sync_trades_for_user

        # Prefer authenticated user's profile ID over request body / demo fallback
        req_user = getattr(request, "user", None)
        if req_user and getattr(req_user, "is_authenticated", False):
            user_id = str(req_user.id)
        else:
            user_id = request.data.get("user_id", DEMO_USER_ID)
        days_back = int(request.data.get("days_back", 30))

        # Get or create user profile — use the authenticated user's ID, never
        # silently fall back to DEMO_USER which causes real trades to sync to
        # the wrong account.
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            if req_user and getattr(req_user, "is_authenticated", False):
                # Authenticated user without a profile yet — create one
                user = UserProfile.objects.create(
                    id=user_id,
                    email=getattr(req_user, "email", ""),
                    name=getattr(req_user, "user_metadata", {}).get("full_name", "")
                         if hasattr(req_user, "user_metadata") else "",
                    preferences={"theme": "dark"},
                    watchlist=[],
                )
            else:
                user, _ = UserProfile.objects.get_or_create(
                    id=DEMO_USER_ID,
                    defaults={
                        "email": "alex@tradeiq.demo",
                        "name": "Alex Demo",
                        "preferences": {"theme": "dark"},
                        "watchlist": [],
                    },
                )
                user_id = str(user.id)

        api_token = get_deriv_token(request)
        if not api_token:
            return Response(
                {"error": "No Deriv token available. Connect your Deriv account or set DERIV_TOKEN."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sync_result = sync_trades_for_user(
            user_id=user_id,
            api_token=api_token,
            days_back=days_back,
        )

        if not sync_result["success"]:
            return Response(
                {"error": "; ".join(sync_result["errors"])},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Run behavioral analysis on synced trades
        analysis = None
        try:
            analysis = analyze_trade_patterns(user_id, hours=days_back * 24)
        except Exception as exc:
            analysis = {"error": str(exc)}

        real_count = Trade.objects.filter(user_id=user_id, is_mock=False).count()
        demo_count = Trade.objects.filter(user_id=user_id, is_mock=True).count()

        return Response({
            "status": "synced",
            "user_id": user_id,
            "trades_synced": sync_result.get("trades_created", 0),
            "trades_updated": sync_result.get("trades_updated", 0),
            "total_trades": real_count + demo_count,
            "real_trades": real_count,
            "demo_trades": demo_count,
            "is_demo": real_count == 0,
            "analysis_summary": analysis,
        })

    @action(detail=False, methods=['post'])
    def load_demo_scenario(self, request):
        """
        Load demo scenario for hackathon.
        POST /api/behavior/trades/load_demo_scenario/
        {"scenario": "revenge_trading"}
        """
        from .demo_data import load_demo_scenario
        
        scenario = request.data.get('scenario', 'revenge_trading')
        user = load_demo_scenario(scenario=scenario)
        
        return Response({
            'success': True,
            'user_id': str(user.id),
            'scenario': scenario,
            'trades_loaded': Trade.objects.filter(user=user, is_mock=True).count()
        })


class BehavioralMetricViewSet(viewsets.ModelViewSet):
    queryset = BehavioralMetric.objects.all()
    serializer_class = BehavioralMetricSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter metrics by user if user_id provided."""
        queryset = BehavioralMetric.objects.all()
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-trading_date')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get behavioral summary for a user over time.
        GET /api/behavior/metrics/summary/?user_id=uuid&days=30
        """
        user_id = request.query_params.get('user_id')
        days = int(request.query_params.get('days', 30))
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        since = timezone.now().date() - timedelta(days=days)
        metrics = BehavioralMetric.objects.filter(
            user=user,
            trading_date__gte=since
        ).order_by('trading_date')
        
        if not metrics.exists():
            return Response({
                'user_id': user_id,
                'period_days': days,
                'metrics_count': 0,
                'summary': {}
            })
        
        # Aggregate data
        total_trades = sum(m.total_trades for m in metrics)
        total_wins = sum(m.win_count for m in metrics)
        total_losses = sum(m.loss_count for m in metrics)
        
        # Count pattern occurrences
        pattern_counts = {
            'revenge_trading': 0,
            'overtrading': 0,
            'loss_chasing': 0,
            'time_patterns': 0
        }
        
        emotional_states = []
        risk_scores = []
        
        for m in metrics:
            for pattern, detected in m.pattern_flags.items():
                if detected and pattern in pattern_counts:
                    pattern_counts[pattern] += 1
            
            if m.emotional_state:
                emotional_states.append(m.emotional_state)
            
            if m.risk_score:
                risk_scores.append(m.risk_score)
        
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Most common emotional state
        if emotional_states:
            most_common_emotion = max(set(emotional_states), key=emotional_states.count)
        else:
            most_common_emotion = 'unknown'
        
        return Response({
            'user_id': user_id,
            'period_days': days,
            'metrics_count': metrics.count(),
            'summary': {
                'total_trades': total_trades,
                'total_wins': total_wins,
                'total_losses': total_losses,
                'win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 0,
                'pattern_occurrences': pattern_counts,
                'avg_risk_score': round(avg_risk_score, 2),
                'most_common_emotion': most_common_emotion
            },
            'daily_metrics': BehavioralMetricSerializer(metrics, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def create_demo_user(self, request):
        """
        Create a demo user for hackathon.
        POST /api/behavior/metrics/create_demo_user/
        """
        demo_user, created = UserProfile.objects.get_or_create(
            email='demo@tradeiq.com',
            defaults={
                'name': 'Demo Trader',
                'preferences': {'demo_mode': True},
                'watchlist': ['BTC/USD', 'ETH/USD', 'Volatility 75']
            }
        )
        
        return Response({
            'user': UserProfileSerializer(demo_user).data,
            'created': created
        })


# ─── Deriv API Live Data Views ──────────────────────────────────────

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from dataclasses import asdict


class TradingTwinView(APIView):
    """
    POST /api/behavior/trading-twin/
    Generate user's Trading Twin analysis.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from behavior.trading_twin import generate_trading_twin
        from deriv_auth.middleware import has_real_deriv_account

        # Prefer authenticated user's profile ID
        req_user = getattr(request, "user", None)
        if req_user and getattr(req_user, "is_authenticated", False):
            user_id = str(req_user.id)
        else:
            user_id = request.data.get("user_id", DEMO_USER_ID)
        days = int(request.data.get("days", 30))
        starting_equity = float(request.data.get("starting_equity", 10000))

        # Prefer real data when user has a connected Deriv account
        prefer_real = has_real_deriv_account(request) or Trade.objects.filter(
            user_id=user_id, is_mock=False
        ).exists()

        result = generate_trading_twin(user_id, days, starting_equity, prefer_real=prefer_real)
        return Response(asdict(result))


class DerivPortfolioView(APIView):
    """GET /api/behavior/portfolio/ — Real-time Deriv portfolio (open positions)."""
    permission_classes = [AllowAny]

    def get(self, request):
        from deriv_auth.middleware import get_deriv_token as _get_token
        api_token = _get_token(request)
        if not api_token:
            return Response({"error": "No Deriv token available"}, status=400)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            portfolio = client.fetch_portfolio(api_token)
            return Response(portfolio)
        except Exception as exc:
            logger.exception("Portfolio fetch failed")
            return Response({"error": "Failed to fetch portfolio. Please try again."}, status=500)


class DerivBalanceView(APIView):
    """GET /api/behavior/balance/ — Real-time Deriv account balance."""
    permission_classes = [AllowAny]

    def get(self, request):
        from deriv_auth.middleware import get_deriv_token as _get_token
        api_token = _get_token(request)
        if not api_token:
            return Response({"error": "No Deriv token available"}, status=400)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            balance = client.fetch_balance(api_token)
            return Response(balance)
        except Exception as exc:
            logger.exception("Balance fetch failed")
            return Response({"error": "Failed to fetch balance. Please try again."}, status=500)


class DerivRealityCheckView(APIView):
    """GET /api/behavior/reality-check/ — Deriv official trading session health check."""
    permission_classes = [AllowAny]

    def get(self, request):
        from deriv_auth.middleware import get_deriv_token as _get_token
        api_token = _get_token(request)
        if not api_token:
            return Response({"error": "No Deriv token available"}, status=400)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            check = client.fetch_reality_check(api_token)
            return Response(check)
        except Exception as exc:
            logger.exception("Reality check fetch failed")
            return Response({"error": "Failed to fetch reality check. Please try again."}, status=500)


class SyncTradesView(APIView):
    """
    POST /api/behavior/sync-trades/
    Dedicated endpoint to sync real trades from a user's connected Deriv account.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from deriv_auth.middleware import get_deriv_token
        from .trade_sync import sync_trades_for_user

        # Prefer authenticated user's profile ID over request body / demo fallback
        req_user = getattr(request, "user", None)
        if req_user and getattr(req_user, "is_authenticated", False):
            user_id = str(req_user.id)
        else:
            user_id = request.data.get("user_id", DEMO_USER_ID)
        days_back = int(request.data.get("days_back", 30))

        # Resolve user — create profile for authenticated users, only fall
        # back to demo for unauthenticated requests.
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            if req_user and getattr(req_user, "is_authenticated", False):
                user = UserProfile.objects.create(
                    id=user_id,
                    email=getattr(req_user, "email", ""),
                    name=getattr(req_user, "user_metadata", {}).get("full_name", "")
                         if hasattr(req_user, "user_metadata") else "",
                    preferences={"theme": "dark"},
                    watchlist=[],
                )
            else:
                user, _ = UserProfile.objects.get_or_create(
                    id=DEMO_USER_ID,
                    defaults={
                        "email": "alex@tradeiq.demo",
                        "name": "Alex Demo",
                        "preferences": {"theme": "dark"},
                        "watchlist": [],
                    },
                )
                user_id = str(user.id)

        api_token = get_deriv_token(request)
        if not api_token:
            return Response(
                {"error": "No Deriv token available. Connect your Deriv account or set DERIV_TOKEN."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sync_result = sync_trades_for_user(
            user_id=user_id,
            api_token=api_token,
            days_back=days_back,
        )

        if not sync_result["success"]:
            return Response(
                {"error": "; ".join(sync_result["errors"])},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        real_count = Trade.objects.filter(user_id=user_id, is_mock=False).count()
        demo_count = Trade.objects.filter(user_id=user_id, is_mock=True).count()

        return Response({
            "status": "synced",
            "user_id": user_id,
            "trades_synced": sync_result.get("trades_created", 0),
            "trades_updated": sync_result.get("trades_updated", 0),
            "total_trades": real_count + demo_count,
            "real_trades": real_count,
            "demo_trades": demo_count,
            "is_demo": real_count == 0,
        })
