from datetime import datetime, time, timedelta

from backend.app.models.therapist_availability import TherapistTimeOff


def test_detect_risks_flags_near_capacity(automation_service, sample_scheduling_session, sample_therapist):
    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 95.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
            'match_failure_rate': 0.0,
        },
    )

    assert 'Therapist is near weekly capacity.' in risk_info['risks']
    assert risk_info['risk_penalties']['overload_risk'] == 20


def test_detect_risks_flags_over_capacity(automation_service, sample_scheduling_session, sample_therapist):
    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 101.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
            'match_failure_rate': 0.0,
        },
    )

    assert 'Therapist is over weekly capacity.' in risk_info['risks']
    assert risk_info['risk_penalties']['overload_risk'] == 25


def test_detect_risks_flags_timeoff_overlap(automation_service, sample_scheduling_session, sample_therapist, sample_timeoff):
    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 10.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
            'match_failure_rate': 0.0,
        },
    )

    assert 'Therapist has time off overlapping this session.' in risk_info['risks']
    assert risk_info['risk_penalties']['timeoff_proximity'] == 15


def test_detect_risks_flags_timeoff_proximity(db_session, automation_service, sample_scheduling_session, sample_therapist):
    near_timeoff = TherapistTimeOff(
        therapist_id=sample_therapist.therapist_id,
        start_datetime=datetime.combine(sample_scheduling_session.date + timedelta(days=1), time(12, 0)),
        end_datetime=datetime.combine(sample_scheduling_session.date + timedelta(days=1), time(13, 0)),
        reason='Nearby PTO',
    )
    db_session.add(near_timeoff)
    db_session.commit()

    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 10.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
            'match_failure_rate': 0.0,
        },
    )

    assert 'Therapist has time off within 48 hours.' in risk_info['risks']
    assert risk_info['risk_penalties']['timeoff_proximity'] == 10


def test_detect_risks_flags_low_reliability_and_recent_cancellations(
    automation_service,
    sample_scheduling_session,
    sample_therapist,
    sample_cancellation_logs,
):
    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 10.0,
            'weekly_capacity': 100.0,
            'reliability_score': 70.0,
            'match_failure_rate': 0.0,
        },
    )

    assert any('Low reliability score' in risk for risk in risk_info['risks'])
    assert 'Recent cancellation streak detected.' in risk_info['risks']
    assert risk_info['risk_penalties']['high_cancellation_risk'] == 20


def test_detect_risks_flags_predictive_alert(automation_service, sample_scheduling_session, sample_therapist, sample_predictive_alert):
    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 10.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
            'match_failure_rate': 0.0,
        },
    )

    assert 'Predictive alert: therapist overload risk.' in risk_info['risks']
    assert risk_info['risk_penalties']['predictive_alert'] == 25


def test_detect_risks_flags_marketplace_failure_rate(automation_service, sample_scheduling_session, sample_therapist, monkeypatch):
    monkeypatch.setattr(automation_service, '_marketplace_failure_rate', lambda therapist_id, session_date: 0.25)

    risk_info = automation_service.detect_risks(
        sample_scheduling_session,
        sample_therapist,
        {
            'weekly_minutes': 10.0,
            'weekly_capacity': 100.0,
            'reliability_score': 90.0,
        },
    )

    assert 'Therapist frequently fails auto-assignment.' in risk_info['risks']
    assert risk_info['risk_penalties']['marketplace_failures'] == 10
