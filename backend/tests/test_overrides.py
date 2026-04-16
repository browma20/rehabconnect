from app.models.automation_audit_entry import AutomationAuditEntry
from app.models.override_log import OverrideLog
from app.models.session import Session as SessionModel


def test_log_override_creates_override_and_automation_audit_entries(
    db_session,
    automation_service,
    sample_scheduling_session,
    sample_therapist,
    alternate_therapist,
):
    original_therapist_id = sample_scheduling_session.therapist_id
    original_date = sample_scheduling_session.date
    original_start = sample_scheduling_session.start_time
    original_end = sample_scheduling_session.end_time

    result = automation_service.log_override(
        session_id=sample_scheduling_session.id,
        recommended_therapist_id=sample_therapist.therapist_id,
        chosen_therapist_id=alternate_therapist.therapist_id,
        reason='Clinical continuity',
        metadata={
            'recommended_score': 91.5,
            'chosen_score': 84.0,
            'confidence': 0.82,
            'confidence_components': {'match_quality': 90.0},
            'risks': ['Near weekly capacity'],
            'data_gaps': ['Reliability data is missing'],
            'overridden_by': 'scheduler:test',
        },
    )

    override_row = db_session.query(OverrideLog).one()
    audit_row = db_session.query(AutomationAuditEntry).filter(AutomationAuditEntry.event_type == 'override').one()
    reloaded_session = db_session.query(SessionModel).filter(SessionModel.id == sample_scheduling_session.id).one()

    assert result['success'] is True
    assert override_row.session_id == sample_scheduling_session.id
    assert override_row.recommended_therapist_id == sample_therapist.therapist_id
    assert override_row.chosen_therapist_id == alternate_therapist.therapist_id
    assert override_row.override_reason == 'Clinical continuity'
    assert override_row.confidence_score == 0.82
    assert override_row.risk_summary == ['Near weekly capacity']
    assert override_row.data_gaps == ['Reliability data is missing']

    assert audit_row.event_type == 'override'
    assert audit_row.recommended_option['therapist_id'] == sample_therapist.therapist_id
    assert audit_row.human_choice['therapist_id'] == alternate_therapist.therapist_id
    assert audit_row.override_reason == 'Clinical continuity'
    assert audit_row.risks == ['Near weekly capacity']
    assert audit_row.confidence_score == 0.82

    assert reloaded_session.therapist_id == original_therapist_id
    assert reloaded_session.date == original_date
    assert reloaded_session.start_time == original_start
    assert reloaded_session.end_time == original_end
