from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def calculate_functional_change(baseline_score: float, latest_score: float):
    """Rule 4.1 — Functional improvement tracking."""
    return latest_score - baseline_score


def improvement_rate(baseline_score: float, latest_score: float, days_since_admission: int):
    if days_since_admission <= 0:
        return 0.0

    change = calculate_functional_change(baseline_score, latest_score)
    return change / days_since_admission


def plateau_detection(score_history: List[Dict[str, Any]], plateau_days: int = 3):
    """Rule 4.2 — Plateau detection (no change >= 3 consecutive days)."""
    if len(score_history) < plateau_days:
        return {'plateau': False, 'consecutive_days': 0}

    flat_days = 1
    for i in range(len(score_history)-1, 0, -1):
        if score_history[i]['score_value'] == score_history[i-1]['score_value']:
            flat_days += 1
        else:
            break

    return {'plateau': flat_days >= plateau_days, 'consecutive_days': flat_days}


def medical_necessity_daily_checks(records: List[Dict[str, Any]], days_in_period: int = 7):
    """Rule 4.3 — Daily medical necessity documentation required."""
    unique_days = set(r['timestamp'].date() for r in records if r.get('timestamp'))
    is_compliant = len(unique_days) >= days_in_period

    return {
        'recorded_days': len(unique_days),
        'period_days': days_in_period,
        'compliant': is_compliant,
        'missing_days': max(days_in_period - len(unique_days), 0)
    }


def check_functional_improvement(admission_date, assessment_dates):
    """Rule 4.1 — Functional assessments performed regularly (max 14 days apart).
    
    Args:
        admission_date: date of patient admission
        assessment_dates: list of dates when functional assessments occurred
    
    Returns:
        {
            "compliant": bool,
            "days_since_last_assessment": int,
            "total_assessments": int,
            "reasons": []
        }
    """
    total_assessments = len(assessment_dates)
    
    if not assessment_dates:
        return {
            "compliant": False,
            "days_since_last_assessment": None,
            "total_assessments": 0,
            "reasons": ["No functional assessments recorded"]
        }
    
    # Sort dates and check gaps
    sorted_dates = sorted(assessment_dates)
    max_gap_days = 0
    prev_date = admission_date
    
    for assess_date in sorted_dates:
        gap_days = (assess_date - prev_date).days
        max_gap_days = max(max_gap_days, gap_days)
        prev_date = assess_date
    
    # days_since_last_assessment = the maximum gap between consecutive assessments
    days_since_last_assessment = max_gap_days
    compliant = max_gap_days <= 14
    
    return {
        "compliant": compliant,
        "days_since_last_assessment": days_since_last_assessment,
        "total_assessments": total_assessments,
        "reasons": [] if compliant else [f"Gap of {max_gap_days} days exceeds 14 days"]
    }
