# behavior/tests.py
# Unit tests for Behavioral Coach Agent

from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import UserProfile, Trade, BehavioralMetric
from .detection import (
    detect_revenge_trading,
    detect_overtrading,
    detect_loss_chasing,
    detect_time_based_patterns,
    analyze_all_patterns
)
from .tools import (
    analyze_trade_patterns,
    get_trading_statistics,
    save_behavioral_metric
)


class RevengeTradinDetectionTest(TestCase):
    """Test revenge trading detection algorithm."""
    
    def setUp(self):
        self.now = timezone.now()
    
    def test_no_revenge_trading_with_few_trades(self):
        """Should not detect with less than 3 trades."""
        trades = [
            {'opened_at': self.now, 'pnl': -100, 'instrument': 'EUR/USD'},
            {'opened_at': self.now + timedelta(minutes=2), 'pnl': -50, 'instrument': 'EUR/USD'}
        ]
        
        result = detect_revenge_trading(trades)
        
        self.assertFalse(result['detected'])
        self.assertEqual(result['severity'], 'none')
    
    def test_detect_revenge_trading_low_severity(self):
        """Should detect low severity revenge trading (3 trades in 10 min)."""
        trades = [
            {'opened_at': self.now, 'pnl': -100, 'instrument': 'EUR/USD'},
            {'opened_at': self.now + timedelta(minutes=2), 'pnl': -50, 'instrument': 'EUR/USD'},
            {'opened_at': self.now + timedelta(minutes=5), 'pnl': -75, 'instrument': 'EUR/USD'}
        ]
        
        result = detect_revenge_trading(trades)
        
        self.assertTrue(result['detected'])
        self.assertEqual(result['severity'], 'low')
        self.assertEqual(result['trade_count'], 3)
    
    def test_detect_revenge_trading_high_severity(self):
        """Should detect high severity revenge trading (5+ trades)."""
        base_time = self.now
        trades = [
            {'opened_at': base_time, 'pnl': -200, 'instrument': 'EUR/USD'},
            {'opened_at': base_time + timedelta(minutes=1), 'pnl': -150, 'instrument': 'EUR/USD'},
            {'opened_at': base_time + timedelta(minutes=3), 'pnl': -100, 'instrument': 'EUR/USD'},
            {'opened_at': base_time + timedelta(minutes=5), 'pnl': -80, 'instrument': 'EUR/USD'},
            {'opened_at': base_time + timedelta(minutes=8), 'pnl': -120, 'instrument': 'EUR/USD'}
        ]
        
        result = detect_revenge_trading(trades)
        
        self.assertTrue(result['detected'])
        self.assertEqual(result['severity'], 'high')
        self.assertGreaterEqual(result['trade_count'], 5)
    
    def test_no_revenge_trading_after_win(self):
        """Should not detect if rapid trades follow a win."""
        trades = [
            {'opened_at': self.now, 'pnl': 100, 'instrument': 'EUR/USD'},  # Win
            {'opened_at': self.now + timedelta(minutes=2), 'pnl': 50, 'instrument': 'EUR/USD'},
            {'opened_at': self.now + timedelta(minutes=5), 'pnl': 75, 'instrument': 'EUR/USD'}
        ]
        
        result = detect_revenge_trading(trades)
        
        self.assertFalse(result['detected'])


class OvertradingDetectionTest(TestCase):
    """Test overtrading detection algorithm."""
    
    def test_no_overtrading_below_threshold(self):
        """Should not detect when trades are below 2x average."""
        trades = [{'pnl': 50}] * 10  # 10 trades
        
        result = detect_overtrading(trades, avg_daily_trades=8)
        
        self.assertFalse(result['detected'])
    
    def test_detect_overtrading_low_severity(self):
        """Should detect low severity (2-2.5x average)."""
        trades = [{'pnl': 50}] * 17  # 2.1x of 8
        
        result = detect_overtrading(trades, avg_daily_trades=8)
        
        self.assertTrue(result['detected'])
        self.assertEqual(result['severity'], 'low')
        self.assertEqual(result['today_count'], 17)
    
    def test_detect_overtrading_high_severity(self):
        """Should detect high severity (3x+ average)."""
        trades = [{'pnl': 50}] * 25  # 3.1x of 8
        
        result = detect_overtrading(trades, avg_daily_trades=8)
        
        self.assertTrue(result['detected'])
        self.assertEqual(result['severity'], 'high')
        self.assertGreaterEqual(result['ratio'], 3.0)


class LossChasingDetectionTest(TestCase):
    """Test loss chasing detection algorithm."""
    
    def setUp(self):
        self.now = timezone.now()
    
    def test_no_loss_chasing_with_few_trades(self):
        """Should not detect with only 1 trade."""
        trades = [
            {'opened_at': self.now, 'pnl': -100, 'entry_price': 1.1000, 'exit_price': 1.0900}
        ]
        
        result = detect_loss_chasing(trades)
        
        self.assertFalse(result['detected'])
    
    def test_detect_loss_chasing(self):
        """Should detect consecutive losses with increasing sizes."""
        trades = [
            {
                'opened_at': self.now,
                'pnl': -100,
                'entry_price': 1.1000,
                'exit_price': 1.0900
            },
            {
                'opened_at': self.now + timedelta(minutes=10),
                'pnl': -150,  # Larger loss
                'entry_price': 1.0900,
                'exit_price': 1.0750
            },
            {
                'opened_at': self.now + timedelta(minutes=20),
                'pnl': -200,  # Even larger loss
                'entry_price': 1.0750,
                'exit_price': 1.0550
            }
        ]
        
        result = detect_loss_chasing(trades)
        
        self.assertTrue(result['detected'])
        self.assertGreaterEqual(result['consecutive_losses'], 2)
        self.assertGreater(result['size_increase'], 0)
    
    def test_no_loss_chasing_with_wins(self):
        """Should reset on wins."""
        trades = [
            {'opened_at': self.now, 'pnl': -100, 'entry_price': 1.1000, 'exit_price': 1.0900},
            {'opened_at': self.now + timedelta(minutes=10), 'pnl': 50, 'entry_price': 1.0900, 'exit_price': 1.0950},  # Win
            {'opened_at': self.now + timedelta(minutes=20), 'pnl': -80, 'entry_price': 1.0950, 'exit_price': 1.0870}
        ]
        
        result = detect_loss_chasing(trades)
        
        # Should not detect because win breaks the streak
        self.assertFalse(result['detected'])


class TimeBasedPatternsTest(TestCase):
    """Test time-based pattern detection."""
    
    def setUp(self):
        self.base_time = timezone.now().replace(hour=10, minute=0, second=0)
    
    def test_detect_poor_performing_hours(self):
        """Should detect hours with <35% win rate."""
        trades = []
        
        # Hour 14: 1 win, 9 losses (10% win rate)
        for i in range(10):
            pnl = 50 if i == 0 else -50
            trades.append({
                'opened_at': self.base_time.replace(hour=14, minute=i*5),
                'pnl': pnl
            })
        
        # Hour 15: 8 wins, 2 losses (80% win rate - good)
        for i in range(10):
            pnl = 50 if i < 8 else -50
            trades.append({
                'opened_at': self.base_time.replace(hour=15, minute=i*5),
                'pnl': pnl
            })
        
        result = detect_time_based_patterns(trades, min_trades_per_hour=3)
        
        self.assertTrue(result['detected'])
        self.assertIn(14, result['worst_hours'])
        self.assertNotIn(15, result['worst_hours'])
    
    def test_no_pattern_with_insufficient_data(self):
        """Should not detect with too few trades per hour."""
        trades = [
            {'opened_at': self.base_time.replace(hour=14), 'pnl': -50},
            {'opened_at': self.base_time.replace(hour=14, minute=30), 'pnl': -50}
        ]
        
        result = detect_time_based_patterns(trades, min_trades_per_hour=3)
        
        self.assertFalse(result['detected'])


class TradePatternAnalysisTest(TestCase):
    """Test integrated pattern analysis."""
    
    def setUp(self):
        # Create demo user
        self.user = UserProfile.objects.create(
            email='test@tradeiq.com',
            name='Test Trader'
        )
    
    def test_analyze_all_patterns(self):
        """Test comprehensive pattern analysis."""
        now = timezone.now()
        
        # Create revenge trading scenario
        trades = []
        for i in range(5):
            trade = Trade.objects.create(
                user=self.user,
                instrument='EUR/USD',
                pnl=Decimal('-100'),
                opened_at=now + timedelta(minutes=i*2),
                is_mock=True
            )
            trades.append({
                'opened_at': trade.opened_at,
                'pnl': float(trade.pnl),
                'entry_price': None,
                'exit_price': None
            })
        
        result = analyze_all_patterns(trades, user_avg_daily_trades=8)
        
        self.assertTrue(result['has_any_pattern'])
        self.assertTrue(result['revenge_trading']['detected'])
        self.assertIn(result['highest_severity'], ['low', 'medium', 'high'])


class TradingStatisticsTest(TestCase):
    """Test trading statistics calculation."""
    
    def setUp(self):
        self.user = UserProfile.objects.create(
            email='stats@tradeiq.com',
            name='Stats Trader'
        )
    
    def test_calculate_statistics(self):
        """Test statistics calculation with trades."""
        now = timezone.now()
        
        # Create winning trades
        for i in range(5):
            Trade.objects.create(
                user=self.user,
                instrument='EUR/USD',
                pnl=Decimal('100'),
                opened_at=now - timedelta(days=i),
                is_mock=True
            )
        
        # Create losing trades
        for i in range(3):
            Trade.objects.create(
                user=self.user,
                instrument='EUR/USD',
                pnl=Decimal('-50'),
                opened_at=now - timedelta(days=i),
                is_mock=True
            )
        
        stats = get_trading_statistics(str(self.user.id), days=30)
        
        self.assertEqual(stats['total_trades'], 8)
        self.assertEqual(stats['win_count'], 5)
        self.assertEqual(stats['loss_count'], 3)
        self.assertEqual(stats['win_rate'], 62.5)
        self.assertEqual(stats['total_pnl'], 350.0)


class BehavioralMetricTest(TestCase):
    """Test behavioral metric saving."""
    
    def setUp(self):
        self.user = UserProfile.objects.create(
            email='metric@tradeiq.com',
            name='Metric Trader'
        )
    
    def test_save_behavioral_metric(self):
        """Test saving behavioral metrics."""
        today = timezone.now().date()
        
        metric_data = {
            'total_trades': 10,
            'win_count': 6,
            'loss_count': 4,
            'avg_hold_time': 1800.0,
            'risk_score': 25.0,
            'emotional_state': 'calm',
            'pattern_flags': {'revenge_trading': False, 'overtrading': False}
        }
        
        success = save_behavioral_metric(str(self.user.id), today, metric_data)
        
        self.assertTrue(success)
        
        # Verify saved
        metric = BehavioralMetric.objects.get(user=self.user, trading_date=today)
        self.assertEqual(metric.total_trades, 10)
        self.assertEqual(metric.win_count, 6)
        self.assertEqual(metric.emotional_state, 'calm')
        self.assertEqual(metric.risk_score, 25.0)
    
    def test_update_existing_metric(self):
        """Test updating existing metric for same day."""
        today = timezone.now().date()
        
        # Create initial metric
        BehavioralMetric.objects.create(
            user=self.user,
            trading_date=today,
            total_trades=5,
            win_count=3,
            loss_count=2
        )
        
        # Update with new data
        metric_data = {
            'total_trades': 10,
            'win_count': 6,
            'loss_count': 4
        }
        
        save_behavioral_metric(str(self.user.id), today, metric_data)
        
        # Should only be one metric for today
        metrics = BehavioralMetric.objects.filter(user=self.user, trading_date=today)
        self.assertEqual(metrics.count(), 1)
        
        # Should have updated values
        metric = metrics.first()
        self.assertEqual(metric.total_trades, 10)
        self.assertEqual(metric.win_count, 6)