import pytest
from datetime import datetime, date
from app.services.patient_service import PatientService
from app.services.therapy_minutes_service import TherapyMinutesService
from app.services.physician_evaluation_service import PhysicianEvaluationService


class TestPatientService:
    """Test cases for PatientService."""

    def test_create_patient(self, db_session, sample_patient_data):
        """Test creating a patient through the service."""
        service = PatientService(db_session)

        patient = service.create_patient(**sample_patient_data)

        assert patient.patient_id == 'TEST001'
        assert patient.mrn == 'MRN001'
        assert patient.first_name == 'John'
        assert patient.last_name == 'Doe'
        assert patient.dob == date(1980, 1, 1)
        assert patient.primary_diagnosis == 'Stroke'
        assert patient.comorbidities == ['Hypertension', 'Diabetes']
        assert patient.assigned_disciplines == ['PT', 'OT', 'ST']

    def test_get_patient(self, db_session, sample_patient):
        """Test retrieving a patient by ID."""
        service = PatientService(db_session)

        patient = service.get_patient('TEST001')

        assert patient is not None
        assert patient.patient_id == 'TEST001'
        assert patient.first_name == 'John'

    def test_get_patient_not_found(self, db_session):
        """Test retrieving a non-existent patient."""
        service = PatientService(db_session)

        patient = service.get_patient('NONEXISTENT')

        assert patient is None

    def test_get_all_patients(self, db_session, sample_patient):
        """Test retrieving all patients."""
        service = PatientService(db_session)

        patients = service.get_all_patients()

        assert len(patients) == 1
        assert patients[0].patient_id == 'TEST001'

    def test_update_patient(self, db_session, sample_patient):
        """Test updating a patient."""
        service = PatientService(db_session)

        updated_patient = service.update_patient(
            'TEST001',
            first_name='Jane',
            primary_diagnosis='Heart Disease'
        )

        assert updated_patient is not None
        assert updated_patient.first_name == 'Jane'
        assert updated_patient.primary_diagnosis == 'Heart Disease'

    def test_update_patient_not_found(self, db_session):
        """Test updating a non-existent patient."""
        service = PatientService(db_session)

        result = service.update_patient('NONEXISTENT', first_name='Jane')

        assert result is None

    def test_create_patient_duplicate_mrn(self, db_session, sample_patient_data):
        """Test creating a patient with duplicate MRN fails."""
        service = PatientService(db_session)

        # Create first patient
        service.create_patient(**sample_patient_data)

        # Try to create second patient with same MRN
        duplicate_data = sample_patient_data.copy()
        duplicate_data['patient_id'] = 'TEST002'

        with pytest.raises(Exception):  # Should raise IntegrityError
            service.create_patient(**duplicate_data)


class TestTherapyMinutesService:
    """Test cases for TherapyMinutesService."""

    def test_record_therapy_session(self, db_session, sample_patient):
        """Test recording a therapy session."""
        service = TherapyMinutesService(db_session)

        session_data = {
            'patient_id': sample_patient.patient_id,
            'discipline': 'PT',
            'session_datetime': datetime(2024, 1, 1, 14, 0, 0),
            'duration_minutes': 45,
            'therapist_id': 'THER001',
            'treatment_type': 'Individual',
            'goals_addressed': ['Mobility', 'Strength'],
            'notes': 'Good progress today'
        }

        session = service.record_therapy_session(**session_data)

        assert session.patient_id == sample_patient.patient_id
        assert session.discipline == 'PT'
        assert session.duration_minutes == 45
        assert session.therapist_id == 'THER001'

    def test_get_patient_sessions(self, db_session, sample_patient, sample_therapy_session):
        """Test retrieving therapy sessions for a patient."""
        service = TherapyMinutesService(db_session)

        sessions = service.get_patient_sessions(sample_patient.patient_id)

        assert len(sessions) == 1
        assert sessions[0].discipline == 'PT'
        assert sessions[0].duration_minutes == 45

    def test_get_patient_sessions_not_found(self, db_session):
        """Test retrieving sessions for non-existent patient."""
        service = TherapyMinutesService(db_session)

        sessions = service.get_patient_sessions('NONEXISTENT')

        assert len(sessions) == 0

    def test_get_daily_minutes(self, db_session, sample_patient, sample_therapy_session):
        """Test calculating daily therapy minutes for a patient."""
        service = TherapyMinutesService(db_session)

        daily_minutes = service.get_daily_minutes(
            sample_patient.patient_id,
            date(2024, 1, 1)
        )

        assert daily_minutes == 45

    def test_get_daily_minutes_no_sessions(self, db_session, sample_patient):
        """Test daily minutes when no sessions exist for the date."""
        service = TherapyMinutesService(db_session)

        daily_minutes = service.get_daily_minutes(
            sample_patient.patient_id,
            date(2024, 1, 2)  # Different date
        )

        assert daily_minutes == 0


class TestPhysicianEvaluationService:
    """Test cases for PhysicianEvaluationService."""

    def test_create_physician_evaluation(self, db_session, sample_patient):
        """Test creating a physician evaluation."""
        service = PhysicianEvaluationService(db_session)

        eval_data = {
            'patient_id': sample_patient.patient_id,
            'physician_id': 'DOC001',
            'physician_name': 'Dr. Smith',
            'evaluation_datetime': datetime(2024, 1, 1, 12, 0, 0),
            'first_day_compliance': True,
            'notes': 'Patient doing well'
        }

        evaluation = service.create_physician_evaluation(**eval_data)

        assert evaluation.patient_id == sample_patient.patient_id
        assert evaluation.physician_id == 'DOC001'
        assert evaluation.physician_name == 'Dr. Smith'
        assert evaluation.first_day_compliance is True
        assert evaluation.notes == 'Patient doing well'

    def test_get_patient_evaluations(self, db_session, sample_patient):
        """Test retrieving physician evaluations for a patient."""
        service = PhysicianEvaluationService(db_session)

        # Create an evaluation first
        service.create_physician_evaluation(
            patient_id=sample_patient.patient_id,
            physician_id='DOC001',
            physician_name='Dr. Smith',
            evaluation_datetime=datetime(2024, 1, 1, 12, 0, 0),
            first_day_compliance=True
        )

        evaluations = service.get_patient_evaluations(sample_patient.patient_id)

        assert len(evaluations) == 1
        assert evaluations[0].physician_id == 'DOC001'
        assert evaluations[0].first_day_compliance is True

    def test_get_patient_evaluations_not_found(self, db_session):
        """Test retrieving evaluations for non-existent patient."""
        service = PhysicianEvaluationService(db_session)

        evaluations = service.get_patient_evaluations('NONEXISTENT')

        assert len(evaluations) == 0

    def test_check_first_day_compliance(self, db_session, sample_patient):
        """Test checking first day compliance for a patient."""
        service = PhysicianEvaluationService(db_session)

        # Create an evaluation within 24 hours
        service.create_physician_evaluation(
            patient_id=sample_patient.patient_id,
            physician_id='DOC001',
            physician_name='Dr. Smith',
            evaluation_datetime=datetime(2024, 1, 1, 12, 0, 0),  # Within 24 hours of admission
            first_day_compliance=True
        )

        compliance = service.check_first_day_compliance(sample_patient.patient_id)

        assert compliance is True

    def test_check_first_day_compliance_no_evaluation(self, db_session, sample_patient):
        """Test first day compliance when no evaluation exists."""
        service = PhysicianEvaluationService(db_session)

        compliance = service.check_first_day_compliance(sample_patient.patient_id)

        assert compliance is False