from typing import List, Dict, Any, Optional
from .risk_config import RISK_WEIGHTS
from .risk_utils import status_to_score, calculate_documentation_completeness, calculate_survey_readiness, get_top_drivers, get_risk_category


def calculate_patient_risk(compliance_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate composite risk score for a patient based on compliance results.

    Args:
        compliance_results: Dict where each key is a metric name and each value is a dict
                           with 'status' key containing 'Green', 'Yellow', or 'Red'.

    Returns:
        Dict with 'risk_score' (float), 'risk_category' (str), 'top_drivers' (list).
    """
    # Handle empty results
    if not compliance_results:
        return {
            'risk_score': 0,
            'risk_category': 'Low',
            'top_drivers': []
        }
    
    # Calculate simple average of scores (no weighting for simplicity)
    scores = []
    for component, result in compliance_results.items():
        if isinstance(result, dict):
            status = result.get('status', 'Green')
            score = status_to_score(status)
            scores.append(score)
    
    # Calculate average score
    if scores:
        risk_score = sum(scores) / len(scores)
    else:
        risk_score = 0
    
    # Determine risk category
    risk_category = get_risk_category(risk_score)
    
    # Get top risk drivers (Red/Yellow components)
    top_drivers = get_top_drivers(compliance_results)
    
    # If no Red/Yellow drivers but we have results, include all component keys
    # (they all contributed to the overall compliance picture)
    if not top_drivers and compliance_results:
        top_drivers = list(compliance_results.keys())
    
    return {
        'risk_score': risk_score,
        'risk_category': risk_category,
        'top_drivers': top_drivers
    }


def calculate_unit_risk_summary(patient_risks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate patient-level risks into unit-level summary.

    Args:
        patient_risks: List of patient risk dicts from calculate_patient_risk.

    Returns:
        Unit-level summary with counts by category, average risk, etc.
    """
    if not patient_risks:
        return {
            'total_patients': 0,
            'low_count': 0,
            'medium_count': 0,
            'high_count': 0,
            'average_risk_score': 0
        }

    total_patients = len(patient_risks)
    low_count = sum(1 for r in patient_risks if r['risk_category'] == 'Low')
    medium_count = sum(1 for r in patient_risks if r['risk_category'] == 'Medium')
    high_count = sum(1 for r in patient_risks if r['risk_category'] == 'High')

    average_risk_score = sum(r['risk_score'] for r in patient_risks) / total_patients

    return {
        'total_patients': total_patients,
        'low_count': low_count,
        'medium_count': medium_count,
        'high_count': high_count,
        'average_risk_score': average_risk_score
    }