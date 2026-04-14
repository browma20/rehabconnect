def check_therapy_start_within_36_hours(session):
    """Rule 1.2/1.3 — First therapy session within 36 hours of admission.
    
    Args:
        session: Session object with patient admission and therapy session data
    
    Returns:
        {
            "compliant": bool,
            "hours_to_first_session": float or None,
            "reasons": []
        }
    """
    # Placeholder for now - full implementation requires database access
    return {
        "compliant": True,
        "hours_to_first_session": 0.0,
        "reasons": []
    }
