from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def medical_necessity_documented_today(records: List[Dict[str, Any]], target_date: datetime = None):
    ref_date = target_date.date() if target_date else datetime.utcnow().date()
    has_document = any(r.get('timestamp') and r['timestamp'].date() == ref_date for r in records)
    return {'date': ref_date, 'documented': has_document}


def medical_necessity_collection_compliance(records: List[Dict[str, Any]], days_span: int = 7):
    if not records:
        return {'compliant': False, 'note': 'No records'}

    min_date = min(r['timestamp'] for r in records if r.get('timestamp'))
    max_date = max(r['timestamp'] for r in records if r.get('timestamp'))
    unique_days = set(r['timestamp'].date() for r in records if r.get('timestamp'))

    expected_period = (max_date.date() - min_date.date()).days + 1
    required_days = min(days_span, expected_period)

    compliant = len(unique_days) >= required_days

    return {
        'min_date': min_date,
        'max_date': max_date,
        'unique_documented_days': len(unique_days),
        'required_days': required_days,
        'compliant': compliant,
        'missing_days': max(required_days - len(unique_days), 0)
    }


def check_medical_necessity(session):
    """Rule 4.3 — All components present: evaluation, therapy, assessments.
    
    Args:
        session: Session object with patient data
    
    Returns:
        {
            "compliant": bool,
            "missing_components": list,
            "reasons": []
        }
    """
    # Placeholder for now - full implementation requires database access
    return {
        "compliant": True,
        "missing_components": [],
        "reasons": []
    }
