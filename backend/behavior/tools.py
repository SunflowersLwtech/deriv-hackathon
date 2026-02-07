# behavior/tools.py
# Tool functions for Behavioral Coach Agent using DeepSeek LLM

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from .models import UserProfile, Trade, BehavioralMetric
from .detection import analyze_all_patterns
from agents.llm_client import get_llm_client
import json


def get_recent_trades(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Fetch recent trades for a user.
    
    Args:
        user_id: User UUID
        hours: How many hours back to fetch
    
    Returns:
        List of trade dicts
    """
    try:
        user = UserProfile.objects.get(id=user_id)
        since = timezone.now() - timedelta(hours=hours)
        
        trades = Trade.objects.filter(
            user=user,
            opened_at__gte=since
        ).order_by('-opened_at')
        
        return [
            {
                'id': str(trade.id),
                'instrument': trade.instrument,
                'direction': trade.direction,
                'pnl': float(trade.pnl),
                'entry_price': float(trade.entry_price) if trade.entry_price else None,
                'exit_price': float(trade.exit_price) if trade.exit_price else None,
                'duration_seconds': trade.duration_seconds,
                'opened_at': trade.opened_at.isoformat(),
                'closed_at': trade.closed_at.isoformat() if trade.closed_at else None,
                'is_mock': trade.is_mock
            }
            for trade in trades
        ]
    except UserProfile.DoesNotExist:
        return []


def analyze_trade_patterns(user_id: str, hours: int = 24) -> Dict[str, Any]:
    """
    Analyze trader's behavioral patterns.
    
    Args:
        user_id: User UUID
        hours: Hours of trade history to analyze
    
    Returns:
        {
            'patterns': {...},
            'summary': str,
            'needs_nudge': bool,
            'nudge_message': str
        }
    """
    trades_raw = get_recent_trades(user_id, hours)
    
    if not trades_raw:
        return {
            'patterns': {},
            'summary': 'No recent trades to analyze',
            'needs_nudge': False,
            'nudge_message': '',
            'trade_count': 0
        }
    
    # Convert ISO strings back to datetime for detection algorithms
    trades = []
    for t in trades_raw:
        trade_copy = t.copy()
        trade_copy['opened_at'] = datetime.fromisoformat(t['opened_at'])
        if t['closed_at']:
            trade_copy['closed_at'] = datetime.fromisoformat(t['closed_at'])
        trades.append(trade_copy)
    
    # Get user's average daily trades for overtrading detection
    try:
        user = UserProfile.objects.get(id=user_id)
        recent_metrics = BehavioralMetric.objects.filter(
            user=user,
            trading_date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        if recent_metrics.exists():
            avg_daily = sum(m.total_trades for m in recent_metrics) / recent_metrics.count()
        else:
            avg_daily = 8  # Default assumption
    except:
        avg_daily = 8
    
    # Run all pattern detection algorithms
    patterns = analyze_all_patterns(trades, user_avg_daily_trades=int(avg_daily))
    
    # Generate summary
    detected_patterns = []
    if patterns['revenge_trading']['detected']:
        detected_patterns.append(f"Revenge trading ({patterns['revenge_trading']['severity']})")
    if patterns['overtrading']['detected']:
        detected_patterns.append(f"Overtrading ({patterns['overtrading']['severity']})")
    if patterns['loss_chasing']['detected']:
        detected_patterns.append(f"Loss chasing ({patterns['loss_chasing']['severity']})")
    if patterns['time_patterns']['detected']:
        detected_patterns.append(f"Poor timing patterns ({patterns['time_patterns']['severity']})")
    
    if detected_patterns:
        summary = f"Detected: {', '.join(detected_patterns)}"
    else:
        summary = "No concerning patterns detected. Trading discipline looks good!"
    
    # Determine if nudge is needed
    needs_nudge = patterns['has_any_pattern'] and patterns['highest_severity'] in ['medium', 'high']
    
    return {
        'patterns': patterns,
        'summary': summary,
        'needs_nudge': needs_nudge,
        'trade_count': len(trades),
        'time_window': f"{hours} hours"
    }


def generate_behavioral_nudge_with_ai(user_id: str, pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use DeepSeek LLM to generate personalized, empathetic nudges.
    
    Args:
        user_id: User UUID
        pattern_analysis: Output from analyze_trade_patterns
    
    Returns:
        {
            'nudge_type': str,
            'message': str,
            'severity': str,
            'suggested_action': str
        }
    """
    patterns = pattern_analysis.get('patterns', {})
    
    # Build context for DeepSeek
    detected_issues = []
    
    if patterns.get('revenge_trading', {}).get('detected'):
        rt = patterns['revenge_trading']
        detected_issues.append(f"Revenge Trading: {rt['details']} (Severity: {rt['severity']})")
    
    if patterns.get('overtrading', {}).get('detected'):
        ot = patterns['overtrading']
        detected_issues.append(f"Overtrading: {ot['details']} (Severity: {ot['severity']})")
    
    if patterns.get('loss_chasing', {}).get('detected'):
        lc = patterns['loss_chasing']
        detected_issues.append(f"Loss Chasing: {lc['details']} (Severity: {lc['severity']})")
    
    if patterns.get('time_patterns', {}).get('detected'):
        tp = patterns['time_patterns']
        detected_issues.append(f"Time Pattern: {tp['details']} (Severity: {tp.get('severity', 'low')})")
    
    if not detected_issues:
        return {
            'nudge_type': 'positive',
            'message': '✅ Great discipline! Your trading patterns look healthy.',
            'severity': 'none',
            'suggested_action': 'Keep up the good work'
        }
    
    # DeepSeek prompt for generating nudge
    prompt = f"""You are a supportive trading coach helping a trader recognize unhealthy patterns.

DETECTED BEHAVIORAL ISSUES:
{chr(10).join(f"- {issue}" for issue in detected_issues)}

RULES:
1. Be gentle and empathetic, not preachy or condescending
2. Focus on ONE highest-priority issue
3. Use supportive language ("I notice..." not "You're doing...")
4. Provide ONE concrete action they can take RIGHT NOW
5. Keep the message under 150 characters
6. Use an appropriate emoji (🛑 for high severity, ⚠️ for medium, 📊 for low)
7. NEVER predict future outcomes or give trading advice
8. Frame in past tense: what HAS happened, not what WILL happen

Generate a JSON response with:
{{
  "nudge_type": "<type of pattern>",
  "message": "<short supportive message>",
  "severity": "<high/medium/low>",
  "suggested_action": "<one concrete action>"
}}"""

    try:
        llm = get_llm_client()
        response = llm.simple_chat(
            system_prompt="You are a behavioral trading coach. You help traders recognize patterns without being judgmental.",
            user_message=prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        # Parse response text (simple_chat returns string directly)
        response_text = response.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        nudge_data = json.loads(response_text)
        return nudge_data
        
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        # Fallback to rule-based nudge
        return generate_behavioral_nudge_fallback(patterns)


def generate_behavioral_nudge_fallback(patterns: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback rule-based nudge generation if DeepSeek fails.
    """
    nudges = []
    
    if patterns.get('revenge_trading', {}).get('detected'):
        rt = patterns['revenge_trading']
        nudges.append({
            'nudge_type': 'revenge_trading',
            'message': f"🛑 I notice you've made {rt['trade_count']} trades in {rt['time_window']} after a loss. Take a breath.",
            'severity': rt['severity'],
            'suggested_action': 'Take a 15-minute break before your next trade',
            'priority': 1
        })
    
    if patterns.get('overtrading', {}).get('detected'):
        ot = patterns['overtrading']
        nudges.append({
            'nudge_type': 'overtrading',
            'message': f"⚠️ You're at {ot['today_count']} trades today ({ot['ratio']:.1f}x your average). Quality over quantity.",
            'severity': ot['severity'],
            'suggested_action': 'Set a max trades limit for today',
            'priority': 2
        })
    
    if patterns.get('loss_chasing', {}).get('detected'):
        lc = patterns['loss_chasing']
        nudges.append({
            'nudge_type': 'loss_chasing',
            'message': f"🚨 {lc['consecutive_losses']} losses with increasing sizes. Classic loss-chasing pattern.",
            'severity': lc['severity'],
            'suggested_action': 'Reduce position size to baseline',
            'priority': 1
        })
    
    severity_order = {'high': 3, 'medium': 2, 'low': 1}
    nudges.sort(key=lambda n: (n['priority'], severity_order.get(n['severity'], 0)), reverse=True)
    
    if nudges:
        return nudges[0]
    
    return {
        'nudge_type': 'positive',
        'message': '✅ Great discipline! Your trading patterns look healthy.',
        'severity': 'none',
        'suggested_action': 'Keep up the good work'
    }


def get_trading_statistics(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive trading statistics for a user.
    
    Args:
        user_id: User UUID
        days: Days of history to analyze
    
    Returns:
        Trading stats dict
    """
    try:
        user = UserProfile.objects.get(id=user_id)
        since = timezone.now() - timedelta(days=days)
        
        trades = Trade.objects.filter(user=user, opened_at__gte=since)
        
        if not trades.exists():
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_instrument': None,
                'worst_instrument': None
            }
        
        total_trades = trades.count()
        winning_trades = trades.filter(pnl__gt=0)
        losing_trades = trades.filter(pnl__lt=0)
        
        win_count = winning_trades.count()
        loss_count = losing_trades.count()
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(float(t.pnl) for t in trades)
        avg_win = sum(float(t.pnl) for t in winning_trades) / win_count if win_count > 0 else 0
        avg_loss = sum(float(t.pnl) for t in losing_trades) / loss_count if loss_count > 0 else 0
        
        # Best/worst instruments
        from django.db.models import Sum, Count
        instrument_stats = trades.values('instrument').annotate(
            pnl_sum=Sum('pnl'),
            count=Count('id')
        ).filter(count__gte=3)
        
        if instrument_stats:
            best = max(instrument_stats, key=lambda x: float(x['pnl_sum']))
            worst = min(instrument_stats, key=lambda x: float(x['pnl_sum']))
            best_instrument = best['instrument']
            worst_instrument = worst['instrument']
        else:
            best_instrument = None
            worst_instrument = None
        
        return {
            'total_trades': total_trades,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_instrument': best_instrument,
            'worst_instrument': worst_instrument,
            'period_days': days
        }
        
    except UserProfile.DoesNotExist:
        return {'error': 'User not found'}


def save_behavioral_metric(user_id: str, trading_date: datetime.date, metric_data: Dict[str, Any]) -> bool:
    """
    Save daily behavioral metrics to database.
    
    Args:
        user_id: User UUID
        trading_date: Date for the metrics
        metric_data: Dict with total_trades, win_count, pattern_flags, etc.
    
    Returns:
        Success boolean
    """
    try:
        user = UserProfile.objects.get(id=user_id)
        
        metric, created = BehavioralMetric.objects.update_or_create(
            user=user,
            trading_date=trading_date,
            defaults={
                'total_trades': metric_data.get('total_trades', 0),
                'win_count': metric_data.get('win_count', 0),
                'loss_count': metric_data.get('loss_count', 0),
                'avg_hold_time': metric_data.get('avg_hold_time'),
                'risk_score': metric_data.get('risk_score'),
                'emotional_state': metric_data.get('emotional_state', ''),
                'pattern_flags': metric_data.get('pattern_flags', {})
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error saving behavioral metric: {e}")
        return False