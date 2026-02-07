# behavior/signals.py
# Django signals for automatic behavioral analysis

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Trade, BehavioralMetric
from .tools import analyze_trade_patterns, save_behavioral_metric


@receiver(post_save, sender=Trade)
def update_daily_metrics(sender, instance, created, **kwargs):
    """
    Automatically update BehavioralMetric when a trade is saved.
    This ensures metrics are always up-to-date.
    """
    if not created:
        # Only process new trades, not updates
        return
    
    user = instance.user
    trading_date = instance.opened_at.date() if instance.opened_at else timezone.now().date()
    
    # Get all trades for this user on this date
    day_trades = Trade.objects.filter(
        user=user,
        opened_at__date=trading_date
    )
    
    total_trades = day_trades.count()
    winning_trades = day_trades.filter(pnl__gt=0)
    losing_trades = day_trades.filter(pnl__lt=0)
    
    win_count = winning_trades.count()
    loss_count = losing_trades.count()
    
    # Calculate average hold time
    trades_with_duration = day_trades.exclude(duration_seconds__isnull=True)
    if trades_with_duration.exists():
        avg_hold_time = sum(t.duration_seconds for t in trades_with_duration) / trades_with_duration.count()
    else:
        avg_hold_time = None
    
    # Run pattern analysis on today's trades
    try:
        analysis = analyze_trade_patterns(str(user.id), hours=24)
        
        pattern_flags = {
            k: v['detected'] 
            for k, v in analysis.get('patterns', {}).items() 
            if isinstance(v, dict) and 'detected' in v
        }
        
        # Determine emotional state
        highest_severity = analysis.get('patterns', {}).get('highest_severity', 'none')
        if highest_severity == 'high':
            emotional_state = 'distressed'
        elif highest_severity == 'medium':
            emotional_state = 'anxious'
        elif analysis.get('patterns', {}).get('has_any_pattern', False):
            emotional_state = 'cautious'
        else:
            emotional_state = 'calm'
        
        # Calculate risk score
        risk_score = calculate_risk_score(analysis.get('patterns', {}))
        
    except Exception as e:
        print(f"Error in pattern analysis: {e}")
        pattern_flags = {}
        emotional_state = 'unknown'
        risk_score = None
    
    # Update or create metric for this day
    metric_data = {
        'total_trades': total_trades,
        'win_count': win_count,
        'loss_count': loss_count,
        'avg_hold_time': avg_hold_time,
        'risk_score': risk_score,
        'emotional_state': emotional_state,
        'pattern_flags': pattern_flags
    }
    
    save_behavioral_metric(str(user.id), trading_date, metric_data)


def calculate_risk_score(patterns):
    """Calculate risk score (0-100) based on detected patterns."""
    score = 0
    
    severity_weights = {'high': 30, 'medium': 20, 'low': 10}
    
    for pattern_name, pattern_data in patterns.items():
        if isinstance(pattern_data, dict) and pattern_data.get('detected'):
            severity = pattern_data.get('severity', 'none')
            score += severity_weights.get(severity, 0)
    
    return min(score, 100)