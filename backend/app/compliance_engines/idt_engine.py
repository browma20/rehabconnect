from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional


def idt_timeliness(last_idt_date: date, as_of_date: date = None):
    """Rule 3.1 — Weekly IDT Meeting."""
    ref_date = as_of_date or date.today()
    if not last_idt_date:
        return {'status': 'Red', 'days_since_last': None, 'notes': 'No IDT on record'}

    days_since = (ref_date - last_idt_date).days
    if days_since <= 7:
        status = 'Green'
    elif days_since <= 8:
        status = 'Yellow'
    else:
        status = 'Red'

    return {'status': status, 'days_since_last': days_since}


def attendance_compliance(attendance: Dict[str, bool], slp_involved: bool = False):
    """Rule 3.2 — Required disciplines present."""
    required = ['physician', 'rn', 'pt', 'ot']
    if slp_involved:
        required.append('slp')

    missing = [d for d in required if not attendance.get(d)]

    if not missing:
        status = 'Green'
    elif len(missing) == 1 and attendance.get('proxy', False):
        status = 'Yellow'
    else:
        status = 'Red'

    return {
        'required_disciplines': required,
        'missing_disciplines': missing,
        'proxy_used': bool(attendance.get('proxy', False)),
        'status': status
    }


def documentation_completeness(fields: Dict[str, Any]):
    """Rule 3.3 — All required fields completed."""
    required_fields = ['patient_progress', 'barriers', 'goals_updated', 'medical_necessity', 'discipline_notes']
    missing = [f for f in required_fields if not fields.get(f)]

    status = 'Green' if not missing else 'Red'
    return {
        'required_fields': required_fields,
        'missing_fields': missing,
        'percent_complete': (len(required_fields)-len(missing))/len(required_fields)*100,
        'status': status
    }


def check_idt_compliance(admission_date, idt_dates):
    """Rule 3.1 — Weekly IDT meetings required.
    
    Args:
        admission_date: date of patient admission
        idt_dates: list of dates when IDT meetings occurred
    
    Returns:
        {
            "compliant": bool,
            "weeks_without_meeting": int,
            "total_meetings": int,
            "reasons": []
        }
    """
    total_meetings = len(idt_dates)
    
    if not idt_dates:
        return {
            "compliant": False,
            "weeks_without_meeting": 0,
            "total_meetings": 0,
            "reasons": ["No IDT meetings recorded"]
        }
    
    # Sort dates and check gaps
    sorted_dates = sorted(idt_dates)
    max_gap_days = 0
    prev_date = admission_date
    
    for idt_date in sorted_dates:
        gap_days = (idt_date - prev_date).days
        max_gap_days = max(max_gap_days, gap_days)
        prev_date = idt_date
    
    # weeks_without_meeting = how many weeks beyond the allowable 7-day gap
    weeks_without_meeting = max(0, (max_gap_days - 7 + 6) // 7)
    compliant = max_gap_days <= 7
    
    return {
        "compliant": compliant,
        "weeks_without_meeting": weeks_without_meeting,
        "total_meetings": total_meetings,
        "reasons": [] if compliant else [f"Gap of {max_gap_days} days exceeds 7 days"]
    }
