import pytest
from datetime import datetime, date
from backend.app.models.patient import Patient
from backend.app.models.therapy_session import TherapySession
from backend.app.models.physician_evaluation import PhysicianEvaluation


class TestPatient:
    """Test cases for Patient model."""

    def test_patient_creation(self, db_session, sample_patient_data):
        """Test creating a patient with valid data."""
        patient = Patient(**sample_patient_data)
        db_session.add(patient)
        db_session.commit()

        assert patient.patient_id == 'TEST001'
        assert patient.mrn == 'MRN001'
        assert patient.first_name == 'John'
        assert patient.last_name == 'Doe'
        assert patient.dob == date(1980, 1, 1)
        assert patient.primary_diagnosis == 'Stroke'
        assert patient.comorbidities == ['Hypertension', 'Diabetes']
        assert patient.assigned_disciplines == ['PT', 'OT', 'ST']
        assert patient.discharge_datetime is None

    def test_patient_repr(self, sample_patient):
        """Test string representation of patient."""
        expected = "<Patient(patient_id=TEST001, name=John Doe)>"
        assert repr(sample_patient) == expected

    def test_patient_relationships(self, sample_patient):
        """Test that patient relationships are properly initialized."""
        assert hasattr(sample_patient, 'physician_evaluations')
        assert hasattr(sample_patient, 'therapy_sessions')
        assert hasattr(sample_patient, 'functional_scores')
        assert hasattr(sample_patient, 'idt_meetings')
        assert hasattr(sample_patient, 'medical_necessity_records')
        assert hasattr(sample_patient, 'risk_scores')
        assert hasattr(sample_patient, 'audit_logs')

    def test_patient_required_fields(self, db_session):
        """Test that required fields cannot be null."""
        # Missing patient_id should fail
        with pytest.raises(Exception):
            patient = Patient(
                mrn='MRN002',
                first_name='Jane',
                last_name='Smith',
                dob=date(1985, 5, 5),
                admission_datetime=datetime(2024, 1, 1, 10, 0, 0),
                assigned_disciplines=['PT']
            )
            db_session.add(patient)
            db_session.commit()

    def test_patient_optional_fields(self, db_session):
        """Test that optional fields can be null."""
        patient = Patient(
            patient_id='TEST002',
            mrn='MRN002',
            first_name='Jane',
            last_name='Smith',
            dob=date(1985, 5, 5),
            admission_datetime=datetime(2024, 1, 1, 10, 0, 0),
            assigned_disciplines=['PT'],
            primary_diagnosis=None,
            comorbidities=None,
            discharge_datetime=None
        )
        db_session.add(patient)
        db_session.commit()

        assert patient.primary_diagnosis is None
        assert patient.comorbidities is None
        assert patient.discharge_datetime is None

    def test_patient_unique_mrn(self, db_session, sample_patient_data):
        """Test that MRN must be unique."""
        # Create first patient
        patient1 = Patient(**sample_patient_data)
        db_session.add(patient1)
        db_session.commit()

        # Try to create second patient with same MRN
        patient2_data = sample_patient_data.copy()
        patient2_data['patient_id'] = 'TEST002'

        with pytest.raises(Exception):  # Should raise IntegrityError
            patient2 = Patient(**patient2_data)
            db_session.add(patient2)
            db_session.commit()


class TestTherapySession:
    """Test cases for TherapySession model."""

    def test_therapy_session_creation(self, db_session, sample_patient):
        """Test creating a therapy session with valid data."""
        session_data = {
            'session_id': 'SESSION001',
            'patient_id': sample_patient.patient_id,
            'discipline': 'PT',
            'delivered_minutes': 45,
            'scheduled_minutes': 60,
            'missed_minutes': 15,
            'reason_code': 'Patient fatigue',
            'timestamp': datetime(2024, 1, 1, 14, 0, 0),
            'source': 'EHR'
        }

        session = TherapySession(**session_data)
        db_session.add(session)
        db_session.commit()

        assert session.session_id == 'SESSION001'
        assert session.patient_id == sample_patient.patient_id
        assert session.discipline == 'PT'
        assert session.delivered_minutes == 45
        assert session.scheduled_minutes == 60
        assert session.missed_minutes == 15
        assert session.reason_code == 'Patient fatigue'
        assert session.source == 'EHR'

    def test_therapy_session_repr(self, db_session, sample_patient):
        """Test string representation of therapy session."""
        session = TherapySession(
            session_id='SESSION001',
            patient_id=sample_patient.patient_id,
            discipline='PT',
            delivered_minutes=45,
            timestamp=datetime(2024, 1, 1, 14, 0, 0),
            source='EHR'
        )
        expected = "<TherapySession(session_id=SESSION001, patient_id=TEST001, discipline=PT)>"
        assert repr(session) == expected

    def test_therapy_session_relationship(self, db_session, sample_patient):
        """Test therapy session patient relationship."""
        session = TherapySession(
            session_id='SESSION001',
            patient_id=sample_patient.patient_id,
            discipline='PT',
            delivered_minutes=45,
            timestamp=datetime(2024, 1, 1, 14, 0, 0),
            source='EHR'
        )
        db_session.add(session)
        db_session.commit()

        # Test relationship from session to patient
        assert session.patient == sample_patient

        # Test relationship from patient to sessions
        assert session in sample_patient.therapy_sessions

    def test_therapy_session_required_fields(self, db_session, sample_patient):
        """Test that required fields cannot be null."""
        # Missing session_id should fail
        with pytest.raises(Exception):
            session = TherapySession(
                patient_id=sample_patient.patient_id,
                discipline='PT',
                delivered_minutes=45,
                timestamp=datetime(2024, 1, 1, 14, 0, 0),
                source='EHR'
            )
            db_session.add(session)
            db_session.commit()

    def test_therapy_session_optional_fields(self, db_session, sample_patient):
        """Test that optional fields can be null."""
        session = TherapySession(
            session_id='SESSION002',
            patient_id=sample_patient.patient_id,
            discipline='PT',
            delivered_minutes=45,
            timestamp=datetime(2024, 1, 1, 14, 0, 0),
            source='EHR',
            scheduled_minutes=None,
            missed_minutes=None,
            reason_code=None
        )
        db_session.add(session)
        db_session.commit()

        assert session.scheduled_minutes is None
        assert session.missed_minutes is None
        assert session.reason_code is None


class TestPhysicianEvaluation:
    """Test cases for PhysicianEvaluation model."""

    def test_physician_evaluation_creation(self, db_session, sample_patient):
        """Test creating a physician evaluation with valid data."""
        eval_data = {
            'evaluation_id': 'EVAL001',
            'patient_id': sample_patient.patient_id,
            'physician_id': 'DOC001',
            'physician_name': 'Dr. Smith',
            'evaluation_datetime': datetime(2024, 1, 1, 12, 0, 0),
            'first_day_compliance': True,
            'notes': 'Patient doing well'
        }

        evaluation = PhysicianEvaluation(**eval_data)
        db_session.add(evaluation)
        db_session.commit()

        assert evaluation.evaluation_id == 'EVAL001'
        assert evaluation.patient_id == sample_patient.patient_id
        assert evaluation.physician_id == 'DOC001'
        assert evaluation.physician_name == 'Dr. Smith'
        assert evaluation.first_day_compliance is True
        assert evaluation.notes == 'Patient doing well'

    def test_physician_evaluation_relationship(self, db_session, sample_patient):
        """Test physician evaluation patient relationship."""
        evaluation = PhysicianEvaluation(
            evaluation_id='EVAL001',
            patient_id=sample_patient.patient_id,
            physician_id='DOC001',
            physician_name='Dr. Smith',
            evaluation_datetime=datetime(2024, 1, 1, 12, 0, 0),
            first_day_compliance=True
        )
        db_session.add(evaluation)
        db_session.commit()

        # Test relationship from evaluation to patient
        assert evaluation.patient == sample_patient

        # Test relationship from patient to evaluations
        assert evaluation in sample_patient.physician_evaluations