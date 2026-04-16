import pytest
from datetime import date, timedelta
from app.compliance_engines.three_hour_rule_engine import (
    daily_3hour_rule,
    seven_day_rolling_intensity,
    missed_minutes_compliance
)
from app.compliance_engines.first_day_engine import check_first_day_compliance
from app.compliance_engines.idt_engine import check_idt_compliance
from app.compliance_engines.functional_improvement_engine import check_functional_improvement


class TestThreeHourRuleEngine:
    """Test cases for three hour rule compliance engine."""

    def test_daily_3hour_rule_green(self):
        """Test 3-hour rule with sufficient minutes (Green status)."""
        result = daily_3hour_rule(delivered_minutes=200)

        assert result['status'] == 'Green'
        assert result['delivered_minutes'] == 200
        assert result['remaining_minutes'] == 0

    def test_daily_3hour_rule_yellow(self):
        """Test 3-hour rule with partial minutes (Yellow status)."""
        result = daily_3hour_rule(delivered_minutes=150)

        assert result['status'] == 'Yellow'
        assert result['delivered_minutes'] == 150
        assert result['remaining_minutes'] == 30

    def test_daily_3hour_rule_red(self):
        """Test 3-hour rule with insufficient minutes (Red status)."""
        result = daily_3hour_rule(delivered_minutes=100)

        assert result['status'] == 'Red'
        assert result['delivered_minutes'] == 100
        assert result['remaining_minutes'] == 80

    def test_daily_3hour_rule_with_missed_minutes_no_reason(self):
        """Test 3-hour rule with missed minutes but no reason code."""
        result = daily_3hour_rule(
            delivered_minutes=150,
            missed_minutes=30,
            reason_code=None
        )

        assert result['status'] == 'Yellow'
        assert result['missed_minutes_documented'] is False
        assert result['reason_code_required'] is True

    def test_daily_3hour_rule_with_missed_minutes_with_reason(self):
        """Test 3-hour rule with missed minutes and reason code."""
        result = daily_3hour_rule(
            delivered_minutes=150,
            missed_minutes=30,
            reason_code='Patient fatigue'
        )

        assert result['status'] == 'Yellow'
        assert result['missed_minutes_documented'] is True
        assert result['reason_code_required'] is True

    def test_seven_day_rolling_intensity_green(self):
        """Test 7-day rolling intensity with sufficient minutes."""
        session_history = [
            {'date': date.today() - timedelta(days=i), 'delivered_minutes': 150}
            for i in range(7)
        ]

        result = seven_day_rolling_intensity(session_history)

        assert result['status'] == 'Green'
        assert result['delivered_7d'] >= 900
        assert result['threshold_7d'] == 900

    def test_seven_day_rolling_intensity_red(self):
        """Test 7-day rolling intensity with insufficient minutes."""
        session_history = [
            {'date': date.today() - timedelta(days=i), 'delivered_minutes': 50}
            for i in range(7)
        ]

        result = seven_day_rolling_intensity(session_history)

        assert result['status'] == 'Red'
        assert result['delivered_7d'] < 900

    def test_seven_day_rolling_intensity_empty_history(self):
        """Test 7-day rolling intensity with no session history."""
        result = seven_day_rolling_intensity([])

        assert result['status'] == 'Red'
        assert result['delivered_7d'] == 0

    def test_missed_minutes_compliance_all_documented(self):
        """Test missed minutes compliance when all are documented."""
        sessions = [
            {'missed_minutes': 0, 'reason_code': None},
            {'missed_minutes': 15, 'reason_code': 'Patient fatigue'},
            {'missed_minutes': 0, 'reason_code': None}
        ]

        result = missed_minutes_compliance(sessions)

        assert result['all_missed_documented'] is True
        assert result['total_missed_minutes'] == 15
        assert result['undocumented_missed_minutes'] == 0

    def test_missed_minutes_compliance_missing_documentation(self):
        """Test missed minutes compliance when some are not documented."""
        sessions = [
            {'missed_minutes': 0, 'reason_code': None},
            {'missed_minutes': 15, 'reason_code': None},  # Missing reason code
            {'missed_minutes': 0, 'reason_code': None}
        ]

        result = missed_minutes_compliance(sessions)

        assert result['all_missed_documented'] is False
        assert result['total_missed_minutes'] == 15
        assert result['undocumented_missed_minutes'] == 15


class TestFirstDayEngine:
    """Test cases for first day compliance engine."""

    def test_first_day_compliance_met(self):
        """Test first day compliance when evaluation is within 24 hours."""
        admission_datetime = date(2024, 1, 1)
        evaluation_datetime = date(2024, 1, 1)  # Same day

        result = check_first_day_compliance(admission_datetime, evaluation_datetime)

        assert result['compliant'] is True
        assert result['hours_to_evaluation'] == 0

    def test_first_day_compliance_not_met(self):
        """Test first day compliance when evaluation is after 24 hours."""
        admission_datetime = date(2024, 1, 1)
        evaluation_datetime = date(2024, 1, 2)  # Next day

        result = check_first_day_compliance(admission_datetime, evaluation_datetime)

        assert result['compliant'] is False
        assert result['hours_to_evaluation'] == 24

    def test_first_day_compliance_no_evaluation(self):
        """Test first day compliance when no evaluation exists."""
        admission_datetime = date(2024, 1, 1)
        evaluation_datetime = None

        result = check_first_day_compliance(admission_datetime, evaluation_datetime)

        assert result['compliant'] is False
        assert result['hours_to_evaluation'] is None


class TestIDTEngine:
    """Test cases for IDT compliance engine."""

    def test_idt_compliance_met(self):
        """Test IDT compliance when meetings are scheduled weekly."""
        admission_date = date(2024, 1, 1)
        idt_dates = [
            date(2024, 1, 5),  # Within first week
            date(2024, 1, 12), # Week 2
            date(2024, 1, 19), # Week 3
        ]

        result = check_idt_compliance(admission_date, idt_dates)

        assert result['compliant'] is True
        assert result['weeks_without_meeting'] == 0

    def test_idt_compliance_gap(self):
        """Test IDT compliance when there's a gap longer than 1 week."""
        admission_date = date(2024, 1, 1)
        idt_dates = [
            date(2024, 1, 5),  # Within first week
            date(2024, 1, 20), # More than 1 week gap
        ]

        result = check_idt_compliance(admission_date, idt_dates)

        assert result['compliant'] is False
        assert result['weeks_without_meeting'] >= 1

    def test_idt_compliance_no_meetings(self):
        """Test IDT compliance when no meetings are scheduled."""
        admission_date = date(2024, 1, 1)
        idt_dates = []

        result = check_idt_compliance(admission_date, idt_dates)

        assert result['compliant'] is False
        assert result['total_meetings'] == 0


class TestFunctionalImprovementEngine:
    """Test cases for functional improvement compliance engine."""

    def test_functional_improvement_compliant(self):
        """Test functional improvement compliance with regular assessments."""
        admission_date = date(2024, 1, 1)
        assessment_dates = [
            date(2024, 1, 1),  # Admission
            date(2024, 1, 7),  # Week 1
            date(2024, 1, 14), # Week 2
            date(2024, 1, 21), # Week 3
        ]

        result = check_functional_improvement(admission_date, assessment_dates)

        assert result['compliant'] is True
        assert result['days_since_last_assessment'] <= 7

    def test_functional_improvement_non_compliant(self):
        """Test functional improvement compliance with gaps."""
        admission_date = date(2024, 1, 1)
        assessment_dates = [
            date(2024, 1, 1),  # Admission
            date(2024, 1, 20), # More than 2 weeks later
        ]

        result = check_functional_improvement(admission_date, assessment_dates)

        assert result['compliant'] is False
        assert result['days_since_last_assessment'] > 14

    def test_functional_improvement_no_assessments(self):
        """Test functional improvement compliance with no assessments."""
        admission_date = date(2024, 1, 1)
        assessment_dates = []

        result = check_functional_improvement(admission_date, assessment_dates)

        assert result['compliant'] is False
        assert result['total_assessments'] == 0