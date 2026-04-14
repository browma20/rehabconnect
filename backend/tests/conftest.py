import pytest
from datetime import datetime, date, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base
from backend.app.models.automation_audit_entry import AutomationAuditEntry
from backend.app.models.override_log import OverrideLog
from backend.app.models.patient import Patient
from backend.app.models.predictive_alert import PredictiveAlert
from backend.app.models.session import Session as SessionModel
from backend.app.models.session_audit_log import SessionAuditLog
from backend.app.models.therapist import Therapist as TherapistModel
from backend.app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from backend.app.models.therapy_session import TherapySession
from backend.app.models.physician_evaluation import PhysicianEvaluation
from backend.app.models.functional_score import FunctionalScore
from backend.app.models.idt_meeting import IDTMeeting
from backend.app.models.medical_necessity_record import MedicalNecessityRecord
from backend.app.models.risk_score import RiskScore
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.services.automation_suggestion_service import AutomationSuggestionService


@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite database for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        'patient_id': 'TEST001',
        'mrn': 'MRN001',
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': date(1980, 1, 1),
        'admission_datetime': datetime(2024, 1, 1, 10, 0, 0),
        'discharge_datetime': None,
        'primary_diagnosis': 'Stroke',
        'comorbidities': ['Hypertension', 'Diabetes'],
        'assigned_disciplines': ['PT', 'OT', 'ST']
    }


@pytest.fixture
def sample_patient(db_session, sample_patient_data):
    """Create a sample patient in the database."""
    patient = Patient(**sample_patient_data)
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def sample_therapy_session_data(sample_patient):
    """Sample therapy session data for testing."""
    return {
        'patient_id': sample_patient.patient_id,
        'discipline': 'PT',
        'session_datetime': datetime(2024, 1, 1, 14, 0, 0),
        'duration_minutes': 45,
        'therapist_id': 'THER001',
        'treatment_type': 'Individual',
        'goals_addressed': ['Mobility', 'Strength'],
        'notes': 'Good progress today'
    }


@pytest.fixture
def sample_therapy_session(db_session, sample_patient):
    """Create a sample therapy session in the database."""
    import uuid
    session = TherapySession(
        session_id=f"SESSION-{uuid.uuid4().hex[:12].upper()}",
        patient_id=sample_patient.patient_id,
        discipline='PT',
        delivered_minutes=45,  # Maps to duration_minutes in API
        timestamp=datetime(2024, 1, 1, 14, 0, 0),  # Maps to session_datetime in API
        source='test'
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def sample_therapist(db_session):
    therapist = TherapistModel(
        therapist_id='THER001',
        first_name='Alice',
        last_name='Smith',
        discipline='PT',
        active=True,
    )
    db_session.add(therapist)
    db_session.commit()
    db_session.refresh(therapist)
    return therapist


@pytest.fixture
def alternate_therapist(db_session):
    therapist = TherapistModel(
        therapist_id='THER002',
        first_name='Bob',
        last_name='Jones',
        discipline='PT',
        active=True,
    )
    db_session.add(therapist)
    db_session.commit()
    db_session.refresh(therapist)
    return therapist


@pytest.fixture
def sample_scheduling_session(db_session, sample_patient, sample_therapist):
    session = SessionModel(
        id='SCHED001',
        patient_id=sample_patient.patient_id,
        therapist_id=sample_therapist.therapist_id,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        discipline='PT',
        status='scheduled',
        notes='Tier 1 automation test session',
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def sample_availability(db_session, sample_therapist):
    block = TherapistAvailability(
        therapist_id=sample_therapist.therapist_id,
        day_of_week=date.today().weekday(),
        start_time=time(8, 0),
        end_time=time(17, 0),
        max_sessions=8,
        max_minutes=480,
    )
    db_session.add(block)
    db_session.commit()
    db_session.refresh(block)
    return block


@pytest.fixture
def automation_service(db_session):
    return AutomationSuggestionService(db_session)


@pytest.fixture
def sample_timeoff(db_session, sample_therapist):
    start_dt = datetime.combine(date.today(), time(9, 30))
    entry = TherapistTimeOff(
        therapist_id=sample_therapist.therapist_id,
        start_datetime=start_dt,
        end_datetime=start_dt + timedelta(hours=2),
        reason='PTO',
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


@pytest.fixture
def sample_predictive_alert(db_session, sample_therapist):
    alert = PredictiveAlert(
        type='THERAPIST_OVERLOADED',
        severity='high',
        message=f'{sample_therapist.therapist_id} overload risk',
        effective_date=date.today(),
        resolved=False,
        metadata_json={'therapist_id': sample_therapist.therapist_id},
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


@pytest.fixture
def sample_cancellation_logs(db_session, sample_scheduling_session, sample_therapist):
    logs = []
    for index in range(3):
        log = SessionAuditLog(
            session_id=sample_scheduling_session.id,
            action_type='canceled',
            performed_by=f'therapist:{sample_therapist.therapist_id}',
            timestamp=datetime.utcnow() - timedelta(days=index + 1),
            old_values={'status': 'scheduled'},
            new_values={'status': 'canceled'},
            notes='Cancellation test fixture',
        )
        db_session.add(log)
        logs.append(log)
    db_session.commit()
    return logs