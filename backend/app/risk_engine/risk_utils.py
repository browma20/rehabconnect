from typing import List, Dict, Any, Optional
from .risk_config import STATUS_SCORES, RISK_WEIGHTS, DOCUMENTATION_THRESHOLDS, SURVEY_READINESS_THRESHOLDS, RISK_CATEGORIES


def status_to_score(status: str) -> int:
    """Convert compliance status to numeric risk score.
    
    Returns:
        int: Score value (1 for Green, 3 for Yellow, 5 for Red, 3 default for unknown)
    """
    return STATUS_SCORES.get(status, 3)  # Default to Yellow (medium) if unknown


def get_risk_category(score: float) -> str:
    """Determine risk category based on composite score.
    
    Args:
        score: Float score value
    
    Returns:
        str: One of "Low", "Medium", "High"
    """
    if score <= 2:
        return "Low"
    elif score <= 3:
        return "Medium"
    else:
        return "High"


def calculate_documentation_completeness(compliance_results: Dict[str, Any]) -> float:
    """Calculate documentation completeness as a percentage.
    
    Args:
        compliance_results: Dict where each value has a 'documentation_complete' key (boolean)
    
    Returns:
        float: Percentage of items with documentation_complete=True (0.0 to 1.0)
    """
    if not compliance_results:
        return 0.0
    
    # Extract documentation_complete values
    completeness_flags = [
        item.get('documentation_complete', False)
        for item in compliance_results.values()
        if isinstance(item, dict)
    ]
    
    if not completeness_flags:
        return 0.0
    
    # Calculate percentage of completed items
    completed_count = sum(1 for flag in completeness_flags if flag is True)
    return completed_count / len(completeness_flags)


def calculate_survey_readiness(compliance_results: Dict[str, Any]) -> float:
    """Calculate survey readiness score based on compliance results.
    
    Args:
        compliance_results: Dict where each value has a 'status' key
    
    Returns:
        float: Survey readiness score (0.0 to 1.0)
    """
    if not compliance_results:
        return 0.0
    
    # Calculate average score from all components
    scores = []
    for component, result in compliance_results.items():
        if isinstance(result, dict):
            status = result.get('status', 'Green')
            score = status_to_score(status)
            scores.append(score)
    
    if not scores:
        return 0.0
    
    # Average score (1-5 range), convert to 0-1 range
    avg_score = sum(scores) / len(scores)
    # Normalize to 0-1 range: Green(1)->1.0, Yellow(3)->0.5, Red(5)->0.0
    normalized = 1.0 - ((avg_score - 1) / 4.0)
    return max(0.0, min(1.0, normalized))  # Clamp to 0-1


def get_top_drivers(compliance_results: Dict[str, Any], max_drivers: int = 3) -> List[str]:
    """Identify top risk drivers based on high-risk components.
    
    Args:
        compliance_results: Dict of compliance check results with 'status' key
        max_drivers: Maximum number of drivers to return (default 3)
    
    Returns:
        List of driver component names (keys from the dict)
    """
    drivers = []
    
    # Collect high-risk components (Red or Yellow)
    high_risk = []
    for component, result in compliance_results.items():
        if isinstance(result, dict):
            status = result.get('status', 'Green')
            if status in ['Red', 'Yellow']:
                high_risk.append((component, status))
    
    # Sort by severity (Red first, then Yellow)
    high_risk.sort(key=lambda x: (0 if x[1] == 'Red' else 1))
    
    # Get top driver component names (not descriptions)
    for component, _ in high_risk[:max_drivers]:
        drivers.append(component)
    
    return drivers