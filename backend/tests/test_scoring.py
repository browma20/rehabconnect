from datetime import date, time

from backend.app.models.therapist_availability import TherapistAvailability


def test_availability_score_is_ideal_for_half_block_fit(db_session, automation_service, sample_scheduling_session, sample_therapist):
    block = TherapistAvailability(
        therapist_id=sample_therapist.therapist_id,
        day_of_week=sample_scheduling_session.date.weekday(),
        start_time=time(8, 0),
        end_time=time(10, 0),
        max_minutes=120,
    )
    db_session.add(block)
    db_session.commit()

    score = automation_service._availability_score(sample_therapist.therapist_id, sample_scheduling_session)

    assert score == 100.0


def test_performance_reliability_scores_use_profile_values(automation_service, monkeypatch):
    monkeypatch.setattr(
        automation_service._performance,
        'get_performance_profile',
        lambda therapist_id, weeks=12: {
            'success': True,
            'performance_score': 88.0,
            'reliability': {'reliability_score': 92.0},
        },
    )

    performance_score, reliability_score = automation_service._performance_reliability_scores('THER001')

    assert performance_score == 88.0
    assert reliability_score == 92.0


def test_caseload_balance_score_drops_with_load(automation_service):
    assert automation_service._caseload_balance_score(0) == 100.0
    assert automation_service._caseload_balance_score(10) == 50.0
    assert automation_service._caseload_balance_score(20) == 0.0


def test_score_reschedule_slot_composite_calculation(automation_service, sample_scheduling_session, sample_therapist, monkeypatch):
    slot = {
        'date': date.today(),
        'start_time': time(11, 0),
        'end_time': time(12, 0),
    }

    monkeypatch.setattr(automation_service, '_availability_score', lambda therapist_id, session: 80.0)
    monkeypatch.setattr(automation_service._conflicts, 'has_any_conflict', lambda therapist_id, session: False)
    monkeypatch.setattr(automation_service, '_weekly_session_count', lambda therapist_id, ref_date, exclude_session_id: 4)
    monkeypatch.setattr(automation_service, '_performance_reliability_scores', lambda therapist_id: (90.0, 70.0))

    result = automation_service.score_reschedule_slot(sample_scheduling_session, sample_therapist, slot)

    assert result['availability_fit_score'] == 80.0
    assert result['conflict_risk_score'] == 100.0
    assert result['caseload_balance_score'] == 75.0
    assert result['reliability_performance_score'] == 80.0
    assert result['total_score'] == 85.25


def test_candidate_spread_is_high_when_top_far_exceeds_second(automation_service):
    payload = automation_service.compute_confidence(
        top_score=95.0,
        second_score=10.0,
        data_flags={},
        risk_flags={},
    )

    assert payload['components']['candidate_spread'] > 80.0


def test_candidate_spread_is_low_when_scores_are_close(automation_service):
    payload = automation_service.compute_confidence(
        top_score=95.0,
        second_score=94.0,
        data_flags={},
        risk_flags={},
    )

    assert payload['components']['candidate_spread'] < 2.0
