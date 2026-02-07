# behavior/websocket_utils.py
# WebSocket utilities for sending behavioral nudges

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from typing import Dict, Any
import json


def send_behavioral_nudge(user_id: str, nudge_data: Dict[str, Any]) -> bool:
    """
    Send a behavioral nudge to the user via WebSocket.
    
    Args:
        user_id: User UUID
        nudge_data: Nudge dict with type, message, severity, suggested_action
    
    Returns:
        Success boolean
    """
    try:
        channel_layer = get_channel_layer()
        
        message = {
            "type": "behavioral_nudge",
            "nudge_type": nudge_data.get('nudge_type', 'general'),
            "message": nudge_data.get('message', ''),
            "severity": nudge_data.get('severity', 'low'),
            "suggested_action": nudge_data.get('suggested_action', ''),
            "timestamp": timezone.now().isoformat(),
            "user_id": user_id
        }
        
        # Send to the chat group
        async_to_sync(channel_layer.group_send)(
            "chat",
            {
                "type": "chat_message",
                "message": message
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending WebSocket nudge: {e}")
        return False


def send_positive_feedback(user_id: str, message: str) -> bool:
    """
    Send positive reinforcement to the user.
    
    Args:
        user_id: User UUID
        message: Positive feedback message
    
    Returns:
        Success boolean
    """
    nudge_data = {
        'nudge_type': 'positive',
        'message': f'✅ {message}',
        'severity': 'none',
        'suggested_action': 'Keep up the good work!'
    }
    
    return send_behavioral_nudge(user_id, nudge_data)


def send_pattern_alert(user_id: str, pattern_name: str, severity: str, details: str) -> bool:
    """
    Send a specific pattern alert.
    
    Args:
        user_id: User UUID
        pattern_name: Name of the detected pattern
        severity: Severity level (low/medium/high)
        details: Pattern details
    
    Returns:
        Success boolean
    """
    emoji_map = {
        'high': '🚨',
        'medium': '⚠️',
        'low': '📊',
        'none': 'ℹ️'
    }
    
    emoji = emoji_map.get(severity, 'ℹ️')
    
    nudge_data = {
        'nudge_type': pattern_name,
        'message': f'{emoji} {details}',
        'severity': severity,
        'suggested_action': f'Review your {pattern_name.replace("_", " ")} behavior'
    }
    
    return send_behavioral_nudge(user_id, nudge_data)


def send_trading_summary(user_id: str, stats: Dict[str, Any]) -> bool:
    """
    Send a trading session summary.
    
    Args:
        user_id: User UUID
        stats: Trading statistics dict
    
    Returns:
        Success boolean
    """
    try:
        channel_layer = get_channel_layer()
        
        message = {
            "type": "trading_summary",
            "total_trades": stats.get('total_trades', 0),
            "win_rate": stats.get('win_rate', 0),
            "total_pnl": stats.get('total_pnl', 0),
            "timestamp": timezone.now().isoformat(),
            "user_id": user_id
        }
        
        async_to_sync(channel_layer.group_send)(
            "chat",
            {
                "type": "chat_message",
                "message": message
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending trading summary: {e}")
        return False


def send_break_suggestion(user_id: str, reason: str, duration_minutes: int = 15) -> bool:
    """
    Suggest the trader take a break.
    
    Args:
        user_id: User UUID
        reason: Reason for suggesting break
        duration_minutes: Suggested break duration
    
    Returns:
        Success boolean
    """
    nudge_data = {
        'nudge_type': 'break_suggestion',
        'message': f'🧘 {reason}',
        'severity': 'medium',
        'suggested_action': f'Take a {duration_minutes}-minute break and reset'
    }
    
    return send_behavioral_nudge(user_id, nudge_data)


def send_achievement(user_id: str, achievement: str) -> bool:
    """
    Celebrate a positive trading achievement.
    
    Args:
        user_id: User UUID
        achievement: Achievement description
    
    Returns:
        Success boolean
    """
    nudge_data = {
        'nudge_type': 'achievement',
        'message': f'🎉 {achievement}',
        'severity': 'none',
        'suggested_action': 'Keep building on this success!'
    }
    
    return send_behavioral_nudge(user_id, nudge_data)