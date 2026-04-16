import pytest
from app.risk_engine.risk_scoring import calculate_patient_risk
from app.risk_engine.risk_utils import (
    status_to_score,
    calculate_documentation_completeness,
    calculate_survey_readiness,
    get_top_drivers,
    get_risk_category
)


class TestRiskScoring:
    """Test cases for risk scoring functionality."""

    def test_calculate_patient_risk_all_green(self):
        """Test risk calculation when all components are compliant."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green'},
            'therapy_start_36h': {'status': 'Green'},
            'first_day_evaluation': {'status': 'Green'},
            'weekly_idt': {'status': 'Green'},
            'functional_assessment': {'status': 'Green'}
        }

        result = calculate_patient_risk(compliance_results)

        assert result['risk_score'] < 2.0  # Should be low risk
        assert result['risk_category'] in ['Low', 'Medium']
        assert len(result['top_drivers']) > 0

    def test_calculate_patient_risk_all_red(self):
        """Test risk calculation when all components are non-compliant."""
        compliance_results = {
            'three_hour_rule': {'status': 'Red'},
            'therapy_start_36h': {'status': 'Red'},
            'first_day_evaluation': {'status': 'Red'},
            'weekly_idt': {'status': 'Red'},
            'functional_assessment': {'status': 'Red'}
        }

        result = calculate_patient_risk(compliance_results)

        assert result['risk_score'] > 3.0  # Should be high risk
        assert result['risk_category'] == 'High'
        assert len(result['top_drivers']) > 0

    def test_calculate_patient_risk_mixed_status(self):
        """Test risk calculation with mixed compliance status."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green'},
            'therapy_start_36h': {'status': 'Yellow'},
            'first_day_evaluation': {'status': 'Red'},
            'weekly_idt': {'status': 'Green'},
            'functional_assessment': {'status': 'Yellow'}
        }

        result = calculate_patient_risk(compliance_results)

        assert 2.0 <= result['risk_score'] <= 3.0  # Should be medium risk
        assert result['risk_category'] == 'Medium'
        assert len(result['top_drivers']) > 0

    def test_calculate_patient_risk_empty_results(self):
        """Test risk calculation with no compliance results."""
        compliance_results = {}

        result = calculate_patient_risk(compliance_results)

        assert result['risk_score'] == 0
        assert result['risk_category'] == 'Low'
        assert len(result['top_drivers']) == 0

    def test_calculate_patient_risk_partial_results(self):
        """Test risk calculation with only some compliance results."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green'},
            'first_day_evaluation': {'status': 'Red'}
        }

        result = calculate_patient_risk(compliance_results)

        assert result['risk_score'] > 0
        assert result['risk_category'] in ['Low', 'Medium', 'High']


class TestRiskUtils:
    """Test cases for risk utility functions."""

    def test_status_to_score_green(self):
        """Test status to score conversion for Green status."""
        score = status_to_score('Green')
        assert score == 1

    def test_status_to_score_yellow(self):
        """Test status to score conversion for Yellow status."""
        score = status_to_score('Yellow')
        assert score == 3

    def test_status_to_score_red(self):
        """Test status to score conversion for Red status."""
        score = status_to_score('Red')
        assert score == 5

    def test_status_to_score_unknown(self):
        """Test status to score conversion for unknown status."""
        score = status_to_score('Unknown')
        assert score == 3  # Default to Yellow/Medium

    def test_get_risk_category_low(self):
        """Test risk category classification for low risk scores."""
        category = get_risk_category(1.5)
        assert category == 'Low'

    def test_get_risk_category_medium(self):
        """Test risk category classification for medium risk scores."""
        category = get_risk_category(2.5)
        assert category == 'Medium'

    def test_get_risk_category_high(self):
        """Test risk category classification for high risk scores."""
        category = get_risk_category(3.5)
        assert category == 'High'

    def test_get_top_drivers(self):
        """Test identification of top risk drivers."""
        compliance_results = {
            'three_hour_rule': {'status': 'Red'},
            'therapy_start_36h': {'status': 'Green'},
            'first_day_evaluation': {'status': 'Red'},
            'weekly_idt': {'status': 'Yellow'},
            'functional_assessment': {'status': 'Green'}
        }

        drivers = get_top_drivers(compliance_results)

        assert len(drivers) > 0
        # Should include the Red status items
        assert 'three_hour_rule' in drivers or 'first_day_evaluation' in drivers

    def test_calculate_documentation_completeness_full(self):
        """Test documentation completeness calculation with all components."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green', 'documentation_complete': True},
            'therapy_start_36h': {'status': 'Green', 'documentation_complete': True},
            'first_day_evaluation': {'status': 'Green', 'documentation_complete': True}
        }

        completeness = calculate_documentation_completeness(compliance_results)

        assert completeness == 1.0  # 100% complete

    def test_calculate_documentation_completeness_partial(self):
        """Test documentation completeness calculation with partial completion."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green', 'documentation_complete': True},
            'therapy_start_36h': {'status': 'Green', 'documentation_complete': False},
            'first_day_evaluation': {'status': 'Green', 'documentation_complete': True}
        }

        completeness = calculate_documentation_completeness(compliance_results)

        assert completeness == 2.0 / 3.0  # 2 out of 3 complete

    def test_calculate_documentation_completeness_none(self):
        """Test documentation completeness calculation with no completion."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green', 'documentation_complete': False},
            'therapy_start_36h': {'status': 'Green', 'documentation_complete': False}
        }

        completeness = calculate_documentation_completeness(compliance_results)

        assert completeness == 0.0

    def test_calculate_survey_readiness_high(self):
        """Test survey readiness calculation for high compliance."""
        compliance_results = {
            'three_hour_rule': {'status': 'Green'},
            'therapy_start_36h': {'status': 'Green'},
            'first_day_evaluation': {'status': 'Green'},
            'weekly_idt': {'status': 'Green'},
            'functional_assessment': {'status': 'Green'}
        }

        readiness = calculate_survey_readiness(compliance_results)

        assert readiness > 0.8  # High readiness

    def test_calculate_survey_readiness_low(self):
        """Test survey readiness calculation for low compliance."""
        compliance_results = {
            'three_hour_rule': {'status': 'Red'},
            'therapy_start_36h': {'status': 'Red'},
            'first_day_evaluation': {'status': 'Red'},
            'weekly_idt': {'status': 'Red'},
            'functional_assessment': {'status': 'Red'}
        }

        readiness = calculate_survey_readiness(compliance_results)

        assert readiness < 0.5  # Low readiness