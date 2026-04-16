from app.models.automation_audit_entry import AutomationAuditEntry
from app.models.session import Session as SessionModel
from app.models.therapist_availability import TherapistAvailability


def test_suggest_assignment_never_modifies_session_assignment_fields(
    db_session,
    automation_service,
    sample_scheduling_session,
    alternate_therapist,
    monkeypatch,
):
    availability = TherapistAvailability(
        therapist_id=alternate_therapist.therapist_id,
        day_of_week=sample_scheduling_session.date.weekday(),
        start_time=sample_scheduling_session.start_time,
        end_time=sample_scheduling_session.end_time,
        max_minutes=60,
    )
    db_session.add(availability)
    db_session.commit()

    monkeypatch.setattr(
        automation_service._matching,
        'match_therapists_to_session',
        lambda session_id: {'best_match': {'therapist_id': alternate_therapist.therapist_id}, 'alternatives': []},
    )
    monkeypatch.setattr(automation_service._conflicts, 'detect_conflicts_for_session', lambda session_id: {'has_conflicts': False})
    monkeypatch.setattr(
        automation_service._performance,
        'get_performance_profile',
        lambda therapist_id, weeks=12: {
            'success': True,
            'performance_score': 90.0,
            'reliability': {'reliability_score': 88.0},
        },
    )

    added = []
    original_add = db_session.add

    def add_spy(obj):
        added.append(type(obj).__name__)
        return original_add(obj)

    monkeypatch.setattr(db_session, 'add', add_spy)

    original_therapist_id = sample_scheduling_session.therapist_id
    result = automation_service.suggest_assignment(sample_scheduling_session.id)
    reloaded = db_session.query(SessionModel).filter(SessionModel.id == sample_scheduling_session.id).one()

    assert result['success'] is True
    assert reloaded.therapist_id == original_therapist_id
    assert set(added) == {'AutomationAuditEntry'}
    assert db_session.query(AutomationAuditEntry).count() == 1


def test_suggest_reschedule_never_modifies_session_or_therapist_schedule(
    db_session,
    automation_service,
    sample_scheduling_session,
    sample_availability,
    monkeypatch,
):
    monkeypatch.setattr(automation_service._matching, 'match_therapists_to_session', lambda session_id: None)
    monkeypatch.setattr(automation_service._conflicts, 'detect_conflicts_for_session', lambda session_id: {'has_conflicts': False})
    monkeypatch.setattr(automation_service, '_performance_reliability_scores', lambda therapist_id: (90.0, 85.0))

    availability_count = db_session.query(TherapistAvailability).count()
    added = []
    original_add = db_session.add

    def add_spy(obj):
        added.append(type(obj).__name__)
        return original_add(obj)

    monkeypatch.setattr(db_session, 'add', add_spy)

    original_values = (
        sample_scheduling_session.therapist_id,
        sample_scheduling_session.date,
        sample_scheduling_session.start_time,
        sample_scheduling_session.end_time,
    )

    result = automation_service.suggest_reschedule(sample_scheduling_session.id)
    reloaded = db_session.query(SessionModel).filter(SessionModel.id == sample_scheduling_session.id).one()

    assert result['success'] is True
    assert (
        reloaded.therapist_id,
        reloaded.date,
        reloaded.start_time,
        reloaded.end_time,
    ) == original_values
    assert db_session.query(TherapistAvailability).count() == availability_count
    assert set(added) == set()
    assert db_session.query(AutomationAuditEntry).count() == 0
