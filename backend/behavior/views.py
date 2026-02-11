# behavior/views.py
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import UserProfile, Trade, BehavioralMetric
from .serializers import UserProfileSerializer, TradeSerializer, BehavioralMetricSerializer
from .tools import (
    analyze_trade_patterns,
    generate_behavioral_nudge_with_ai,
    get_trading_statistics,
    save_behavioral_metric
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
    permission_classes = [AllowAny]  # Demo mode - allow all access
    
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
            print(f"Error in behavioral analysis: {e}")
            # Don't fail the trade creation if analysis fails
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _analyze_and_nudge(self, user):
        """
        Internal method to analyze patterns and send nudge via WebSocket.
        """
        # Analyze recent trades (last 24 hours)
        analysis = analyze_trade_patterns(str(user.id), hours=24)
        
        if analysis['needs_nudge']:
            # Generate AI-powered nudge
            nudge = generate_behavioral_nudge_with_ai(str(user.id), analysis)
            
            # Persist nudge to database
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO nudges (user_id, nudge_type, message, trigger_reason, severity)
                           VALUES (%s, %s, %s, %s, %s)""",
                        [str(user.id), nudge.get('nudge_type', ''), nudge.get('message', ''),
                         analysis.get('summary', ''), nudge.get('severity', 'low')]
                    )
            except Exception as e:
                print(f"Error saving nudge: {e}")

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

            # Also save to daily metrics
            today = timezone.now().date()
            pattern_flags = {
                k: v['detected'] 
                for k, v in analysis['patterns'].items() 
                if isinstance(v, dict) and 'detected' in v
            }
            
            # Calculate emotional state based on patterns
            if analysis['patterns']['highest_severity'] == 'high':
                emotional_state = 'distressed'
            elif analysis['patterns']['highest_severity'] == 'medium':
                emotional_state = 'anxious'
            elif analysis['patterns']['has_any_pattern']:
                emotional_state = 'cautious'
            else:
                emotional_state = 'calm'
            
            metric_data = {
                'total_trades': analysis['trade_count'],
                'pattern_flags': pattern_flags,
                'emotional_state': emotional_state,
                'risk_score': self._calculate_risk_score(analysis['patterns'])
            }
            
            save_behavioral_metric(str(user.id), today, metric_data)
    
    def _calculate_risk_score(self, patterns):
        """Calculate risk score (0-100) based on detected patterns."""
        score = 0
        
        severity_weights = {'high': 30, 'medium': 20, 'low': 10}
        
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, dict) and pattern_data.get('detected'):
                severity = pattern_data.get('severity', 'none')
                score += severity_weights.get(severity, 0)
        
        return min(score, 100)
    
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
        Sync real trades from Deriv API using DERIV_TOKEN.
        POST /api/behavior/trades/sync_deriv/
        {"user_id": "optional-uuid", "days_back": 30}

        Uses the live Deriv API to pull profit_table data and create
        Trade objects in the database, then runs behavioral analysis.
        """
        user_id = request.data.get("user_id", DEMO_USER_ID)
        days_back = int(request.data.get("days_back", 30))

        # Get or create user
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
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

        api_token = os.environ.get("DERIV_TOKEN", "")
        if not api_token:
            return Response(
                {"error": "DERIV_TOKEN not configured in environment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Sync trades from Deriv
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            sync_result = client.sync_trades_to_database(
                user_id=user_id,
                api_token=api_token,
                days_back=days_back,
            )
        except Exception as exc:
            return Response(
                {"error": f"Deriv sync failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Run behavioral analysis on synced trades
        analysis = None
        try:
            analysis = analyze_trade_patterns(user_id, hours=days_back * 24)
        except Exception as exc:
            analysis = {"error": str(exc)}

        return Response({
            "status": "synced",
            "user_id": user_id,
            "trades_synced": sync_result.get("trades_created", 0),
            "trades_updated": sync_result.get("trades_updated", 0),
            "total_trades": Trade.objects.filter(user_id=user_id).count(),
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
                'watchlist': ['EUR/USD', 'BTC/USD', 'GOLD']
            }
        )
        
        return Response({
            'user': UserProfileSerializer(demo_user).data,
            'created': created
        })


# ─── Deriv API Live Data Views ──────────────────────────────────────

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class DerivPortfolioView(APIView):
    """GET /api/behavior/portfolio/ — Real-time Deriv portfolio (open positions)."""
    permission_classes = [AllowAny]

    def get(self, request):
        api_token = os.environ.get("DERIV_TOKEN", "")
        if not api_token:
            return Response({"error": "DERIV_TOKEN not configured"}, status=500)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            portfolio = client.fetch_portfolio(api_token)
            return Response(portfolio)
        except Exception as exc:
            return Response({"error": str(exc)}, status=500)


class DerivBalanceView(APIView):
    """GET /api/behavior/balance/ — Real-time Deriv account balance."""
    permission_classes = [AllowAny]

    def get(self, request):
        api_token = os.environ.get("DERIV_TOKEN", "")
        if not api_token:
            return Response({"error": "DERIV_TOKEN not configured"}, status=500)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            balance = client.fetch_balance(api_token)
            return Response(balance)
        except Exception as exc:
            return Response({"error": str(exc)}, status=500)


class DerivRealityCheckView(APIView):
    """GET /api/behavior/reality-check/ — Deriv official trading session health check."""
    permission_classes = [AllowAny]

    def get(self, request):
        api_token = os.environ.get("DERIV_TOKEN", "")
        if not api_token:
            return Response({"error": "DERIV_TOKEN not configured"}, status=500)
        try:
            from .deriv_client import get_deriv_client
            client = get_deriv_client()
            check = client.fetch_reality_check(api_token)
            return Response(check)
        except Exception as exc:
            return Response({"error": str(exc)}, status=500)
