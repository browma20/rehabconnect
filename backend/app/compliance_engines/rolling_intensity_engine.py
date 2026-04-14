from datetime import date, timedelta
from typing import List, Dict, Any, Optional


def calculate_rolling_7_day_total(session_history: List[Dict[str, Any]], as_of_date: date = None) -> Dict[str, Any]:
    """Aggregates delivered minutes over rolling 7-day window."""
    today = as_of_date or date.today()
    window_start = today - timedelta(days=6)

    total = sum(item.get('delivered_minutes', 0)
                for item in session_history
                if window_start <= item.get('date') <= today)

    compliance_status = 'Green' if total >= 900 else 'Red'

    return {
        'window_start': window_start,
        'window_end': today,
        'delivered_minutes_7d': total,
        'threshold': 900,
        'status': compliance_status
    }


def estimate_daily_average(session_history: List[Dict[str, Any]], days: int = 7) -> float:
    """Return average delivered minutes per day over window."""
    if not session_history or days <= 0:
        return 0.0

    total = sum(item.get('delivered_minutes', 0) for item in session_history)
    return total / days
