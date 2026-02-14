# behavior/detection.py
# Pattern detection algorithms for Behavioral Coach Agent

from datetime import timedelta
from typing import List, Dict, Any
from decimal import Decimal


def detect_revenge_trading(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect revenge trading pattern: 3+ trades within 10 minutes after a loss.
    
    Args:
        trades: List of trade dicts with 'opened_at', 'pnl', 'instrument'
    
    Returns:
        {
            'detected': bool,
            'severity': str,  # 'low', 'medium', 'high'
            'details': str,
            'trade_count': int,
            'time_window': str
        }
    """
    if not trades or len(trades) < 3:
        return {
            'detected': False,
            'severity': 'none',
            'details': '',
            'trade_count': 0,
            'time_window': ''
        }
    
    # Sort trades by time (oldest first) so we find a loss then look forward
    sorted_trades = sorted(trades, key=lambda t: t['opened_at'])

    # Look for pattern: initial loss followed by rapid trades
    for i in range(len(sorted_trades)):
        first_trade = sorted_trades[i]

        # Check if this trade was a loss
        if float(first_trade.get('pnl', 0)) >= 0:
            continue

        # Count trades within 10 minutes AFTER this loss
        rapid_trades = [first_trade]
        time_threshold = first_trade['opened_at'] + timedelta(minutes=10)

        for j in range(i + 1, len(sorted_trades)):
            next_trade = sorted_trades[j]
            if next_trade['opened_at'] <= time_threshold:
                rapid_trades.append(next_trade)
            else:
                break
        
        # If 3+ trades in 10 minutes after a loss, it's revenge trading
        if len(rapid_trades) >= 3:
            total_pnl = sum(float(t.get('pnl', 0)) for t in rapid_trades)
            
            # Determine severity
            if len(rapid_trades) >= 5:
                severity = 'high'
            elif len(rapid_trades) >= 4:
                severity = 'medium'
            else:
                severity = 'low'
            
            time_span = (rapid_trades[-1]['opened_at'] - rapid_trades[0]['opened_at']).total_seconds() / 60
            trigger_time = first_trade['opened_at'].strftime("%b %d, %H:%M UTC")

            return {
                'detected': True,
                'severity': severity,
                'details': (
                    f"{len(rapid_trades)} trades in {time_span:.1f} min after a "
                    f"${abs(float(first_trade['pnl'])):.2f} loss ({trigger_time})"
                ),
                'trade_count': len(rapid_trades),
                'time_window': f"{time_span:.1f} minutes",
                'total_pnl': total_pnl,
                'trigger_loss': float(first_trade['pnl'])
            }
    
    return {
        'detected': False,
        'severity': 'none',
        'details': '',
        'trade_count': 0,
        'time_window': ''
    }


def detect_overtrading(trades: List[Dict[str, Any]], avg_daily_trades: int = 8) -> Dict[str, Any]:
    """
    Detect overtrading: trades count > 2x average.
    
    Args:
        trades: List of trade dicts (assumed to be from today)
        avg_daily_trades: User's historical daily average
    
    Returns:
        {
            'detected': bool,
            'severity': str,
            'details': str,
            'today_count': int,
            'average': int
        }
    """
    if not trades:
        return {
            'detected': False,
            'severity': 'none',
            'details': '',
            'today_count': 0,
            'average': avg_daily_trades
        }
    
    today_count = len(trades)
    threshold = avg_daily_trades * 2
    
    if today_count <= threshold:
        return {
            'detected': False,
            'severity': 'none',
            'details': '',
            'today_count': today_count,
            'average': avg_daily_trades
        }
    
    # Determine severity
    ratio = today_count / avg_daily_trades
    if ratio >= 3:
        severity = 'high'
    elif ratio >= 2.5:
        severity = 'medium'
    else:
        severity = 'low'
    
    return {
        'detected': True,
        'severity': severity,
        'details': f"{today_count} trades today vs {avg_daily_trades} average ({ratio:.1f}x normal)",
        'today_count': today_count,
        'average': avg_daily_trades,
        'ratio': ratio
    }


def detect_loss_chasing(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect loss chasing: consecutive losses with increasing position sizes.
    
    Args:
        trades: List of trade dicts with 'pnl', 'entry_price', 'exit_price'
    
    Returns:
        {
            'detected': bool,
            'severity': str,
            'details': str,
            'consecutive_losses': int,
            'size_increase': float
        }
    """
    if not trades or len(trades) < 2:
        return {
            'detected': False,
            'severity': 'none',
            'details': '',
            'consecutive_losses': 0,
            'size_increase': 0
        }
    
    # Sort trades by time
    sorted_trades = sorted(trades, key=lambda t: t['opened_at'])
    
    # Find sequences of consecutive losses with increasing sizes
    max_consecutive = 0
    current_consecutive = 0
    max_size_increase = 0
    last_size = None
    first_loss_size = None
    last_loss_size = None
    # Track dates/sizes of the worst sequence for the details string
    best_first_date = None
    best_last_date = None
    best_first_size = None
    best_last_size = None
    cur_first_date = None
    cur_last_date = None
    cur_first_size = None
    cur_last_size = None

    for trade in sorted_trades:
        pnl = float(trade.get('pnl', 0))

        # We do not store true position size in Trade.
        # Using abs(pnl) is a more stable proxy than inferring from entry/exit
        # deltas, which can mask size escalation when the price move also grows.
        size = abs(pnl)

        # Check if this is a loss
        if pnl < 0:
            current_consecutive += 1

            if first_loss_size is None:
                first_loss_size = size
                cur_first_date = trade['opened_at']
                cur_first_size = size

            cur_last_date = trade['opened_at']
            cur_last_size = size

            # Check if size is increasing
            if last_size is not None and size > last_size:
                size_increase = ((size - first_loss_size) / first_loss_size) * 100 if first_loss_size > 0 else 0
                max_size_increase = max(max_size_increase, size_increase)

            last_size = size
        else:
            # Reset on win — save best sequence info first
            if current_consecutive > max_consecutive:
                max_consecutive = current_consecutive
                best_first_date = cur_first_date
                best_last_date = cur_last_date
                best_first_size = cur_first_size
                best_last_size = cur_last_size
            current_consecutive = 0
            first_loss_size = None
            last_size = None
            cur_first_date = None
            cur_last_date = None
            cur_first_size = None
            cur_last_size = None

    # Check final sequence
    if current_consecutive > max_consecutive:
        max_consecutive = current_consecutive
        best_first_date = cur_first_date
        best_last_date = cur_last_date
        best_first_size = cur_first_size
        best_last_size = cur_last_size

    # Detection criteria: 2+ consecutive losses with 20%+ size increase
    detected = max_consecutive >= 2 and max_size_increase >= 20

    if not detected:
        return {
            'detected': False,
            'severity': 'none',
            'details': '',
            'consecutive_losses': max_consecutive,
            'size_increase': max_size_increase
        }

    # Determine severity
    if max_consecutive >= 4 or max_size_increase >= 50:
        severity = 'high'
    elif max_consecutive >= 3 or max_size_increase >= 35:
        severity = 'medium'
    else:
        severity = 'low'

    # Build a details string with dates and sizes
    date_range = ""
    size_range = ""
    if best_first_date and best_last_date:
        d1 = best_first_date.strftime("%b %d")
        d2 = best_last_date.strftime("%b %d")
        date_range = f", {d1}-{d2}" if d1 != d2 else f", {d1}"
    if best_first_size is not None and best_last_size is not None:
        size_range = f" (${best_first_size:.2f} -> ${best_last_size:.2f})"

    return {
        'detected': True,
        'severity': severity,
        'details': (
            f"{max_consecutive} consecutive losses with {max_size_increase:.1f}% "
            f"position size increase{size_range}{date_range}"
        ),
        'consecutive_losses': max_consecutive,
        'size_increase': max_size_increase
    }


def detect_time_based_patterns(trades: List[Dict[str, Any]], min_trades_per_hour: int = 3) -> Dict[str, Any]:
    """
    Detect time-based patterns: hours with consistently poor performance.
    
    Args:
        trades: List of historical trades with 'opened_at', 'pnl'
        min_trades_per_hour: Minimum trades needed for statistical significance
    
    Returns:
        {
            'detected': bool,
            'worst_hours': List[int],  # Hours of day (0-23)
            'details': str,
            'win_rate_by_hour': Dict[int, float]
        }
    """
    if not trades or len(trades) < min_trades_per_hour:
        return {
            'detected': False,
            'worst_hours': [],
            'details': '',
            'win_rate_by_hour': {}
        }
    
    # Group trades by hour of day
    trades_by_hour = {}
    for trade in trades:
        hour = trade['opened_at'].hour
        if hour not in trades_by_hour:
            trades_by_hour[hour] = []
        trades_by_hour[hour].append(trade)
    
    # Calculate win rate for each hour
    win_rate_by_hour = {}
    for hour, hour_trades in trades_by_hour.items():
        if len(hour_trades) >= min_trades_per_hour:
            wins = sum(1 for t in hour_trades if float(t.get('pnl', 0)) > 0)
            win_rate = (wins / len(hour_trades)) * 100
            win_rate_by_hour[hour] = win_rate
    
    if not win_rate_by_hour:
        return {
            'detected': False,
            'worst_hours': [],
            'details': '',
            'win_rate_by_hour': {}
        }
    
    # Find hours with <35% win rate
    worst_hours = [hour for hour, rate in win_rate_by_hour.items() if rate < 35]
    
    if not worst_hours:
        return {
            'detected': False,
            'worst_hours': [],
            'details': '',
            'win_rate_by_hour': win_rate_by_hour
        }
    
    worst_hours_sorted = sorted(worst_hours, key=lambda h: win_rate_by_hour[h])
    worst_rate = win_rate_by_hour[worst_hours_sorted[0]]
    
    # Format hours nicely
    def format_hour(h):
        return f"{h:02d}:00-{(h+1)%24:02d}:00"
    
    hours_str = ", ".join(format_hour(h) for h in worst_hours_sorted[:3])
    
    return {
        'detected': True,
        'worst_hours': worst_hours_sorted,
        'details': f"Poor performance during {hours_str} (win rate: {worst_rate:.1f}%)",
        'win_rate_by_hour': win_rate_by_hour,
        'severity': 'medium' if worst_rate < 25 else 'low'
    }


def analyze_all_patterns(
    trades: List[Dict[str, Any]],
    user_avg_daily_trades: int = 8,
    data_source: str = "demo",
) -> Dict[str, Any]:
    """
    Run all detection algorithms and return comprehensive analysis.

    Args:
        trades: List of trade dicts
        user_avg_daily_trades: User's historical daily average
        data_source: "real" or "demo" — passed through to the result

    Returns:
        {
            'revenge_trading': {...},
            'overtrading': {...},
            'loss_chasing': {...},
            'time_patterns': {...},
            'has_any_pattern': bool,
            'highest_severity': str,
            'data_source': str
        }
    """
    revenge = detect_revenge_trading(trades)
    overtrading = detect_overtrading(trades, user_avg_daily_trades)
    loss_chasing = detect_loss_chasing(trades)
    time_patterns = detect_time_based_patterns(trades)

    patterns = {
        'revenge_trading': revenge,
        'overtrading': overtrading,
        'loss_chasing': loss_chasing,
        'time_patterns': time_patterns
    }

    # Check if any pattern detected
    has_any = any(p['detected'] for p in patterns.values())

    # Find highest severity
    severities = ['none', 'low', 'medium', 'high']
    max_severity = 'none'
    for pattern in patterns.values():
        severity = pattern.get('severity', 'none')
        if severities.index(severity) > severities.index(max_severity):
            max_severity = severity

    return {
        **patterns,
        'has_any_pattern': has_any,
        'highest_severity': max_severity,
        'data_source': data_source,
    }
