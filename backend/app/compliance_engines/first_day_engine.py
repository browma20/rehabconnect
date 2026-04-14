from datetime import datetime, timedelta


def physician_evaluation_compliance(admission_datetime: datetime, evaluation_datetime: datetime):
    """Rule 1.1 — Physician Post‑Admission Evaluation within 24 hours."""
    if not admission_datetime or not evaluation_datetime:
        return {'status': 'Red', 'hours_from_admission': None, 'notes': 'Missing timestamps'}

    delta = evaluation_datetime - admission_datetime
    hours = delta.total_seconds() / 3600.0

    status = 'Green' if hours <= 24 else 'Red'
    return {
        'status': status,
        'hours_from_admission': hours,
        'threshold_hours': 24,
        'evaluation_timestamp': evaluation_datetime,
        'admission_timestamp': admission_datetime,
        'notes': None if status == 'Green' else 'Overdue'
    }


def first_therapy_compliance(admission_datetime: datetime, first_therapy_datetime: datetime, local_24h_threshold=False):
    """Rule 1.2 + 1.3 — First therapy treatment within 36 hours (CMS) and optional local 24h."""
    if not admission_datetime or not first_therapy_datetime:
        return {'cms_status': 'Red', 'local_status': 'Red', 'notes': 'Missing timestamps'}

    delta = first_therapy_datetime - admission_datetime
    hours = delta.total_seconds() / 3600.0

    cms_status = 'Green' if hours <= 36 else 'Red'
    if local_24h_threshold:
        if hours <= 24:
            local_status = 'Green'
        elif hours <= 36:
            local_status = 'Yellow'
        else:
            local_status = 'Red'
    else:
        local_status = 'Not Applicable'

    return {
        'cms_status': cms_status,
        'local_status': local_status,
        'hours_from_admission': hours,
        'threshold_hours_cms': 36,
        'threshold_hours_local': 24,
        'notes': None if cms_status == 'Green' else 'Overdue'
    }


def check_first_day_compliance(admission_datetime, evaluation_datetime):
    """Rule 1.1 — Physician Post-Admission Evaluation within 24 hours.
    
    Args:
        admission_datetime: datetime of patient admission (date or datetime)
        evaluation_datetime: datetime of physician evaluation (date or datetime, or None)
    
    Returns:
        {
            "compliant": bool,
            "hours_to_evaluation": float or None,
            "reasons": []
        }
    """
    hours_to_evaluation = None
    compliant = False
    
    if evaluation_datetime is None:
        compliant = False
        hours_to_evaluation = None
    else:
        # Convert to datetime if needed for hour calculation
        from datetime import datetime as dt
        if isinstance(admission_datetime, dt):
            adm = admission_datetime
        else:
            adm = dt.combine(admission_datetime, dt.min.time())
        
        if isinstance(evaluation_datetime, dt):
            eval_dt = evaluation_datetime
        else:
            eval_dt = dt.combine(evaluation_datetime, dt.min.time())
        
        delta = eval_dt - adm
        hours_to_evaluation = delta.total_seconds() / 3600.0
        compliant = hours_to_evaluation < 24
    
    return {
        "compliant": compliant,
        "hours_to_evaluation": hours_to_evaluation,
        "reasons": []
    }
