# behavior/demo_data.py
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Trade, UserProfile


def load_demo_scenario(user_email='demo@tradeiq.com', scenario='revenge_trading'):
    """Load demo trading scenario for hackathon."""
    
    user, _ = UserProfile.objects.get_or_create(
        email=user_email,
        defaults={'name': 'Demo Trader', 'preferences': {'demo_mode': True}}
    )
    
    # Clear existing mock trades for this user
    Trade.objects.filter(user=user, is_mock=True).delete()
    
    now = timezone.now()
    
    scenarios = {
        'revenge_trading': [
            # Initial loss triggers emotional trading
            {'time': 0, 'pnl': -200, 'instrument': 'BTC/USD'},
            # Rapid trades in next 10 minutes
            {'time': 2, 'pnl': -150, 'instrument': 'BTC/USD'},
            {'time': 4, 'pnl': -180, 'instrument': 'BTC/USD'},
            {'time': 6, 'pnl': -120, 'instrument': 'BTC/USD'},
            {'time': 7, 'pnl': -100, 'instrument': 'BTC/USD'},
        ],
        'overtrading': [
            # 25 trades in a day (way above 8 average)
            {'time': i*15, 'pnl': (-1)**(i%3) * 50, 'instrument': 'Volatility 75'}
            for i in range(25)
        ],
        'loss_chasing': [
            # Consecutive losses with increasing position sizes
            {'time': 0, 'pnl': -100, 'instrument': 'BTC/USD'},
            {'time': 15, 'pnl': -150, 'instrument': 'BTC/USD'},
            {'time': 30, 'pnl': -250, 'instrument': 'BTC/USD'},
            {'time': 45, 'pnl': -350, 'instrument': 'BTC/USD'},
        ],
        'healthy_session': [
            # Well-paced trades with good discipline
            {'time': 0, 'pnl': 85, 'instrument': 'BTC/USD'},
            {'time': 60, 'pnl': -40, 'instrument': 'ETH/USD'},
            {'time': 150, 'pnl': 120, 'instrument': 'Volatility 75'},
            {'time': 240, 'pnl': 60, 'instrument': 'ETH/USD'},
            {'time': 300, 'pnl': -30, 'instrument': 'BTC/USD'},
        ]
    }
    
    trades_data = scenarios.get(scenario, scenarios['healthy_session'])
    
    # Create trades
    for trade_data in trades_data:
        Trade.objects.create(
            user=user,
            instrument=trade_data['instrument'],
            pnl=Decimal(str(trade_data['pnl'])),
            opened_at=now - timedelta(minutes=trade_data['time']),
            closed_at=now - timedelta(minutes=trade_data['time']) + timedelta(minutes=5),
            duration_seconds=300,
            is_mock=True
        )
    
    return user