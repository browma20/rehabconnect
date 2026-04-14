# Risk Scoring Configuration
# Weights for composite risk score
RISK_WEIGHTS = {
    'three_hour_rule': 0.20,
    'therapy_start_36h': 0.20,
    'first_day_evaluation': 0.20,
    'weekly_idt': 0.20,
    'functional_assessment': 0.20
}

# Risk category thresholds based on composite score
RISK_CATEGORIES = {
    'Low': (0, 2),      # score <= 2
    'Medium': (2, 4),   # 2 < score <= 4
    'High': (4, 5)      # score > 4
}

# Status to numeric score mapping (for risk calculation)
STATUS_SCORES = {
    'Green': 1,      # Low risk
    'Yellow': 3,     # Medium risk
    'Red': 5         # High risk
}

# Documentation completeness thresholds
DOCUMENTATION_THRESHOLDS = {
    'excellent': 0.95,
    'good': 0.80,
    'needs_improvement': 0.60
}

# Survey readiness thresholds
SURVEY_READINESS_THRESHOLDS = {
    'high': 4,
    'medium': 2,
    'low': 0
}