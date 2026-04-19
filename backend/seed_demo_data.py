"""
Comprehensive demo data seeding system for RehabConnect.
Populates all major models with realistic synthetic demo data.
Idempotent -- safe to run multiple times.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, time
from random import randint, choice, random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import (
    Patient, Therapist, Session, TherapySession, TherapistAvailability,
    TherapistTimeOff, RiskScore, FunctionalScore, Notification, PredictiveAlert,
    IDTMeeting, MedicalNecessityRecord, OverrideLog, SessionAuditLog
)

# Try to import faker for realistic names; fall back to manual generation if not available
try:
    from faker import Faker
    faker = Faker()
    USE_FAKER = True
except ImportError:
    USE_FAKER = False

# Sample data for manual generation if Faker is not available
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer",
    "William", "Linda", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore"
]

DIAGNOSES = [
    "Stroke (CVA)", "Hip Fracture", "Knee Surgery Recovery", "Pneumonia",
    "Cardiac Event", "COPD", "Diabetes (Type 2)", "CHF",
    "Parkinson's Disease", "Multiple Sclerosis", "Total Knee Replacement",
    "Total Hip Replacement", "ACL Tear", "Rotator Cuff Repair"
]

COMORBIDITIES = [
    ["Hypertension", "Diabetes"],
    ["COPD", "Hypertension"],
    ["Diabetes", "Obesity"],
    ["Arthritis", "Hypertension"],
    ["Sleep Apnea"],
    ["Atrial Fibrillation"],
    ["Chronic Pain"],
    []
]

DISCIPLINES = ["PT", "OT", "ST"]

RISK_CATEGORIES = ["Low", "Medium", "High", "Critical"]

FUNCTIONAL_SCORE_TYPES = ["FIM", "Berg Balance", "Gait Speed", "Grip Strength", "ROM"]

NOTIFICATION_TYPES = [
    "SESSION_ASSIGNED", "SESSION_CANCELED", "SESSION_COMPLETED",
    "SESSION_RESCHEDULED", "ALERT_TRIGGERED", "GOAL_UPDATED"
]

PREDICTIVE_ALERT_TYPES = [
    "READMISSION_RISK", "DISCHARGE_DELAY", "THERAPY_INTENSITY_DECREASE",
    "COMPLIANCE_RISK", "FUNCTIONAL_PLATEAU"
]

ALERT_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

MRN_PREFIX = "MRN"


def get_random_name():
    """Generate a random name."""
    if USE_FAKER:
        return faker.first_name(), faker.last_name()
    return choice(FIRST_NAMES), choice(LAST_NAMES)


def generate_mrn():
    """Generate a unique MRN."""
    return f"{MRN_PREFIX}{randint(100000, 999999)}"


def clear_table(db, model):
    """Safely clear a table before seeding."""
    try:
        db.query(model).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not clear {model.__tablename__}: {e}")


def seed_patients(db, count=25):
    """Seed realistic patient data."""
    print("Seeding patients...", end=" ")
    clear_table(db, Patient)
    patients = []
    for i in range(count):
        first_name, last_name = get_random_name()
        dob = datetime.now() - timedelta(days=randint(20*365, 85*365))  # 20-85 years old
        admission_datetime = datetime.now() - timedelta(days=randint(1, 30))
        discharge_datetime = None if random() > 0.3 else admission_datetime + timedelta(days=randint(5, 60))
        
        patient = Patient(
            patient_id=f"PAT{str(uuid.uuid4())[:8].upper()}",
            mrn=generate_mrn(),
            first_name=first_name,
            last_name=last_name,
            dob=dob.date(),
            admission_datetime=admission_datetime,
            discharge_datetime=discharge_datetime,
            primary_diagnosis=choice(DIAGNOSES),
            comorbidities=choice(COMORBIDITIES),
            assigned_disciplines=["PT", "OT"] if random() > 0.3 else ["PT"] if random() > 0.5 else ["OT"]
        )
        patients.append(patient)
        db.add(patient)
    
    db.commit()
    print(f"✓ Created {len(patients)} patients")
    return patients


def seed_therapists(db, count=12):
    """Seed therapist data."""
    print("Seeding therapists...", end=" ")
    clear_table(db, Therapist)
    therapists = []
    for i in range(count):
        first_name, last_name = get_random_name()
        therapist = Therapist(
            therapist_id=f"THR{str(uuid.uuid4())[:8].upper()}",
            first_name=first_name,
            last_name=last_name,
            discipline=choice(DISCIPLINES),
            active=True if random() > 0.1 else False
        )
        therapists.append(therapist)
        db.add(therapist)
    
    db.commit()
    print(f"✓ Created {len(therapists)} therapists")
    return therapists


def seed_availability(db, therapists):
    """Seed weekly therapist availability."""
    print("Seeding therapist availability...", end=" ")
    clear_table(db, TherapistAvailability)
    availability_entries = []
    
    # Create Mon-Fri 8am-4pm availability for each therapist
    for therapist in therapists:
        for day_of_week in range(5):  # Mon-Fri (0-4)
            availability = TherapistAvailability(
                id=str(uuid.uuid4()),
                therapist_id=therapist.therapist_id,
                day_of_week=day_of_week,
                start_time=time(8, 0),
                end_time=time(16, 0),
                max_sessions=randint(4, 8),
                max_minutes=randint(240, 480)
            )
            availability_entries.append(availability)
            db.add(availability)
    
    db.commit()
    print(f"✓ Created {len(availability_entries)} availability entries")


def seed_time_off(db, therapists):
    """Seed therapist time off."""
    print("Seeding therapist time off...", end=" ")
    clear_table(db, TherapistTimeOff)
    time_off_entries = []
    
    # Create a few time off entries
    for i in range(min(5, len(therapists))):
        therapist = choice(therapists)
        start_dt = datetime.now() + timedelta(days=randint(10, 60))
        end_dt = start_dt + timedelta(days=randint(1, 10))
        
        time_off = TherapistTimeOff(
            id=str(uuid.uuid4()),
            therapist_id=therapist.therapist_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            reason=choice(["Vacation", "Training", "Medical Leave", "Conference"])
        )
        time_off_entries.append(time_off)
        db.add(time_off)
    
    db.commit()
    print(f"✓ Created {len(time_off_entries)} time off entries")


def seed_sessions(db, patients, therapists, count=75):
    """Seed therapy sessions."""
    print("Seeding therapy sessions...", end=" ")
    clear_table(db, Session)
    sessions = []
    
    for i in range(count):
        patient = choice(patients)
        therapist = choice(therapists)
        session_date = datetime.now().date() - timedelta(days=randint(-30, 30))
        start_dt = datetime.combine(session_date, time(randint(8, 15), choice([0, 30])))
        end_dt = start_dt + timedelta(minutes=randint(30, 120))
        
        session = Session(
            id=str(uuid.uuid4()),
            therapist_id=therapist.therapist_id,
            patient_id=patient.patient_id,
            date=session_date,
            start_time=start_dt.time(),
            end_time=end_dt.time(),
            discipline=choice(DISCIPLINES),
            notes=choice([f"Session with {therapist.first_name}", "Progress noted", "Continue current plan", ""]),
            status=choice(["scheduled", "completed", "canceled"]),
            completed_at=start_dt if random() > 0.3 else None,
            canceled_at=start_dt if random() > 0.8 else None,
            cancellation_reason=choice(["Patient unavailable", "Weather", "No reason given"]) if random() > 0.8 else None
        )
        sessions.append(session)
        db.add(session)
    
    db.commit()
    print(f"✓ Created {len(sessions)} sessions")
    return sessions


def seed_therapy_sessions(db, patients, count=50):
    """Seed therapy session records."""
    print("Seeding therapy session records...", end=" ")
    clear_table(db, TherapySession)
    therapy_sessions = []
    
    for i in range(count):
        patient = choice(patients)
        delivered_min = randint(15, 120)
        
        therapy_session = TherapySession(
            session_id=f"TS{str(uuid.uuid4())[:8].upper()}",
            patient_id=patient.patient_id,
            discipline=choice(DISCIPLINES),
            delivered_minutes=delivered_min,
            scheduled_minutes=delivered_min if random() > 0.2 else randint(15, 120),
            missed_minutes=0 if random() > 0.1 else randint(5, 60),
            reason_code=choice(["COMPLETED", "PARTIAL", "CANCELED"]),
            timestamp=datetime.now() - timedelta(days=randint(1, 30)),
            source="EHR",
            therapist_id=None
        )
        therapy_sessions.append(therapy_session)
        db.add(therapy_session)
    
    db.commit()
    print(f"✓ Created {len(therapy_sessions)} therapy session records")


def seed_risk_scores(db, patients):
    """Seed risk scores for each patient."""
    print("Seeding risk scores...", end=" ")
    clear_table(db, RiskScore)
    risk_scores = []
    
    for patient in patients:
        score = randint(10, 95)
        risk_score = RiskScore(
            risk_id=f"RSK{str(uuid.uuid4())[:8].upper()}",
            patient_id=patient.patient_id,
            score=score,
            risk_category=RISK_CATEGORIES[min(3, score // 25)],
            top_drivers=["Age", "Comorbidities", "Functional Status"]
        )
        risk_scores.append(risk_score)
        db.add(risk_score)
    
    db.commit()
    print(f"✓ Created {len(risk_scores)} risk scores")


def seed_functional_scores(db, patients, count=None):
    """Seed functional scores for patients."""
    print("Seeding functional scores...", end=" ")
    clear_table(db, FunctionalScore)
    functional_scores = []
    
    if count is None:
        count = len(patients) * 3
    
    for i in range(count):
        patient = choice(patients)
        functional_score = FunctionalScore(
            score_id=f"FS{str(uuid.uuid4())[:8].upper()}",
            patient_id=patient.patient_id,
            discipline=choice(DISCIPLINES),
            score_type=choice(FUNCTIONAL_SCORE_TYPES),
            score_value=randint(0, 10),
            timestamp=datetime.now() - timedelta(days=randint(1, 30)),
            notes=choice(["Improving", "Stable", "Needs attention", ""]),
            source="Assessment"
        )
        functional_scores.append(functional_score)
        db.add(functional_score)
    
    db.commit()
    print(f"✓ Created {len(functional_scores)} functional scores")


def seed_notifications(db, sessions, therapists, count=20):
    """Seed notifications."""
    print("Seeding notifications...", end=" ")
    clear_table(db, Notification)
    notifications = []
    
    session_list = list(db.query(Session).limit(min(count, 50)).all()) if not sessions else sessions[:min(count, 50)]
    
    for i in range(min(count, len(session_list))):
        session = session_list[i] if session_list else choice(sessions) if sessions else None
        if not session:
            continue
            
        notification = Notification(
            user_id=choice(therapists).therapist_id if therapists else f"THR{str(uuid.uuid4())[:8]}",
            session_id=session.id,
            type=choice(NOTIFICATION_TYPES),
            message=f"Session update: {choice(['assigned', 'canceled', 'completed', 'rescheduled'])}",
            created_at=datetime.now() - timedelta(hours=randint(1, 168)),
            read=True if random() > 0.3 else False
        )
        notifications.append(notification)
        db.add(notification)
    
    db.commit()
    print(f"✓ Created {len(notifications)} notifications")


def seed_predictive_alerts(db, patients, count=8):
    """Seed predictive alerts."""
    print("Seeding predictive alerts...", end=" ")
    clear_table(db, PredictiveAlert)
    alerts = []
    
    for i in range(count):
        alert = PredictiveAlert(
            type=choice(PREDICTIVE_ALERT_TYPES),
            severity=choice(ALERT_SEVERITIES),
            message=f"Alert: Patient may be at risk for {choice(['readmission', 'discharge delay', 'decreased compliance'])}",
            effective_date=datetime.now().date() - timedelta(days=randint(-10, 10)),
            created_at=datetime.now() - timedelta(days=randint(1, 30)),
            resolved=True if random() > 0.4 else False,
            metadata_json={"patient_id": choice(patients).patient_id if patients else None, "confidence": round(random(), 2)}
        )
        alerts.append(alert)
        db.add(alert)
    
    db.commit()
    print(f"✓ Created {len(alerts)} predictive alerts")


def seed_idt_meetings(db, patients, count=4):
    """Seed IDT meetings."""
    print("Seeding IDT meetings...", end=" ")
    clear_table(db, IDTMeeting)
    meetings = []
    
    for i in range(min(count, len(patients))):
        patient = patients[i] if patients else choice(patients) if patients else None
        if not patient:
            continue
            
        meeting = IDTMeeting(
            idt_id=f"IDT{str(uuid.uuid4())[:8].upper()}",
            patient_id=patient.patient_id,
            meeting_datetime=datetime.now() - timedelta(days=randint(1, 14)),
            physician_present=random() > 0.2,
            rn_present=True,
            pt_present=random() > 0.3,
            ot_present=random() > 0.3,
            slp_present=random() > 0.6,
            goals_updated=random() > 0.4,
            barriers=choice(["Financial constraints", "Transportation issues", "Compliance concerns", ""]),
            physician_signoff=datetime.now() - timedelta(days=randint(1, 10)) if random() > 0.4 else None
        )
        meetings.append(meeting)
        db.add(meeting)
    
    db.commit()
    print(f"✓ Created {len(meetings)} IDT meetings")


def seed_medical_necessity(db, patients, count=None):
    """Seed medical necessity records."""
    print("Seeding medical necessity records...", end=" ")
    clear_table(db, MedicalNecessityRecord)
    records = []
    
    if count is None:
        count = len(patients) // 2
    
    for i in range(count):
        patient = choice(patients) if patients else None
        if not patient:
            continue
            
        record = MedicalNecessityRecord(
            record_id=f"MN{str(uuid.uuid4())[:8].upper()}",
            patient_id=patient.patient_id,
            statement=choice([
                "Patient requires skilled therapy to improve functional mobility",
                "Therapy needed to prevent complications and maintain function",
                "Skilled intervention necessary to address safety concerns",
                "Medical complexity requires professional oversight"
            ]),
            barriers=choice(["Pain", "Fatigue", "Cognitive limitations", ""]),
            clinical_reasoning=choice([
                "Patient demonstrates potential for functional improvement",
                "High risk of deconditioning without therapy",
                "Specialized techniques required for condition"
            ]),
            timestamp=datetime.now() - timedelta(days=randint(1, 30)),
            discipline=choice(DISCIPLINES)
        )
        records.append(record)
        db.add(record)
    
    db.commit()
    print(f"✓ Created {len(records)} medical necessity records")


def seed_override_logs(db, sessions, therapists, count=5):
    """Seed override logs."""
    print("Seeding override logs...", end=" ")
    clear_table(db, OverrideLog)
    logs = []
    
    session_list = list(db.query(Session).limit(min(count * 2, 50)).all()) if not sessions else sessions[:min(count * 2, 50)]
    
    for i in range(min(count, len(session_list))):
        session = session_list[i] if session_list else None
        if not session:
            continue
            
        log = OverrideLog(
            session_id=session.id,
            recommended_therapist_id=choice(therapists).therapist_id if therapists else f"THR{str(uuid.uuid4())[:8]}",
            chosen_therapist_id=session.therapist_id or choice(therapists).therapist_id if therapists else f"THR{str(uuid.uuid4())[:8]}",
            recommended_score=round(random() * 100, 2),
            chosen_score=round(random() * 100, 2),
            confidence_score=round(random(), 2),
            risk_summary={"readmission_risk": 0.35, "functional_decline_risk": 0.22},
            data_gaps=["Recent imaging results", "Family support status"],
            override_reason=choice([
                "Therapist availability",
                "Patient preference",
                "Geographic proximity",
                "Specialized skills needed"
            ]),
            overridden_by="scheduler@rehab.local",
            timestamp=datetime.now() - timedelta(hours=randint(1, 168))
        )
        logs.append(log)
        db.add(log)
    
    db.commit()
    print(f"✓ Created {len(logs)} override logs")


def seed_session_audit_logs(db, sessions, count=None):
    """Seed session audit logs."""
    print("Seeding session audit logs...", end=" ")
    clear_table(db, SessionAuditLog)
    audit_logs = []
    
    session_list = list(db.query(Session).all()) if not sessions else sessions
    if count is None:
        count = len(session_list)
    
    for i in range(min(count, len(session_list))):
        session = session_list[i] if session_list else None
        if not session:
            continue
            
        audit_log = SessionAuditLog(
            session_id=session.id,
            action_type=choice(["CREATED", "UPDATED", "COMPLETED", "CANCELED"]),
            performed_by="system@rehab.local",
            timestamp=datetime.now() - timedelta(hours=randint(1, 336)),
            old_values={"status": "scheduled"},
            new_values={"status": session.status},
            notes=choice(["Routine update", "Manual override", "System adjustment", ""])
        )
        audit_logs.append(audit_log)
        db.add(audit_log)
    
    db.commit()
    print(f"✓ Created {len(audit_logs)} session audit logs")


def main():
    """Main seeding orchestration."""
    print("\n" + "="*80)
    print("RehabConnect Demo Data Seeding System")
    print("="*80 + "\n")
    
    db = SessionLocal()
    try:
        # Seed in dependency order
        patients = seed_patients(db, count=25)
        therapists = seed_therapists(db, count=12)
        seed_availability(db, therapists)
        seed_time_off(db, therapists)
        sessions = seed_sessions(db, patients, therapists, count=75)
        seed_therapy_sessions(db, patients, count=50)
        seed_risk_scores(db, patients)
        seed_functional_scores(db, patients, count=70)
        seed_notifications(db, sessions, therapists, count=20)
        seed_predictive_alerts(db, patients, count=8)
        seed_idt_meetings(db, patients, count=4)
        seed_medical_necessity(db, patients, count=12)
        seed_override_logs(db, sessions, therapists, count=5)
        seed_session_audit_logs(db, sessions, count=50)
        
        print("\n" + "="*80)
        print("✓ Demo data seeded successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
from datetime import datetime, timedelta, time, timezone

from sqlalchemy import inspect, text

from app.database import SessionLocal
from app.models.patient import Patient
from app.models.user import User
from app.models.therapy_session import TherapySession
from app.models.functional_score import FunctionalScore
from app.models.idt_meeting import IDTMeeting
from app.models.medical_necessity_record import MedicalNecessityRecord


SEED_SOURCE = "demo_seed_v1"


def dt_on(day, hour, minute=0):
    today = datetime.now(timezone.utc).date()
    return datetime.combine(today + timedelta(days=day), time(hour=hour, minute=minute, tzinfo=timezone.utc))


DEMO_PATIENTS = [
    {
        "patient_id": "DEMO-P001",
        "mrn": "RC-MRN-1001",
        "first_name": "Emma",
        "last_name": "Carter",
        "dob": datetime(1948, 5, 17).date(),
        "admission_datetime": dt_on(-10, 9),
        "primary_diagnosis": "Stroke",
        "comorbidities": ["Hypertension", "Type 2 Diabetes"],
        "assigned_disciplines": ["PT", "OT", "ST"],
        "sessions": [
            {"idx": 1, "day": -10, "discipline": "PT", "minutes": 60, "scheduled": 60, "missed": 0, "reason": None, "hour": 11},
            {"idx": 2, "day": -3, "discipline": "OT", "minutes": 200, "scheduled": 210, "missed": 10, "reason": "patient_break", "hour": 10},
            {"idx": 3, "day": -1, "discipline": "ST", "minutes": 150, "scheduled": 180, "missed": 30, "reason": "fatigue", "hour": 14},
            {"idx": 4, "day": 0, "discipline": "PT", "minutes": 185, "scheduled": 185, "missed": 0, "reason": None, "hour": 9},
        ],
        "evaluations": [
            {"idx": 1, "hours_after_admit": 20, "physician_id": "PHY-100", "physician_name": "Dr. Rachel Nguyen", "first_day": True, "notes": "Admit evaluation within window."},
            {"idx": 2, "hours_after_admit": 96, "physician_id": "PHY-100", "physician_name": "Dr. Rachel Nguyen", "first_day": None, "notes": "Follow-up evaluation."},
        ],
        "functional_scores": [
            {"idx": 1, "discipline": "PT", "score_type": "FIM", "score": 42, "day": -9},
            {"idx": 2, "discipline": "PT", "score_type": "FIM", "score": 50, "day": -5},
            {"idx": 3, "discipline": "PT", "score_type": "FIM", "score": 57, "day": -1},
        ],
        "idt_days_ago": 3,
        "medical_days": [-2, -1, 0],
    },
    {
        "patient_id": "DEMO-P002",
        "mrn": "RC-MRN-1002",
        "first_name": "Noah",
        "last_name": "Ramirez",
        "dob": datetime(1956, 9, 2).date(),
        "admission_datetime": dt_on(-16, 10),
        "primary_diagnosis": "Debility",
        "comorbidities": ["COPD"],
        "assigned_disciplines": ["PT", "OT"],
        "sessions": [
            {"idx": 1, "day": -15, "discipline": "PT", "minutes": 45, "scheduled": 60, "missed": 15, "reason": "shortness_of_breath", "hour": 12},
            {"idx": 2, "day": -7, "discipline": "OT", "minutes": 160, "scheduled": 180, "missed": 20, "reason": "pain", "hour": 9},
            {"idx": 3, "day": -2, "discipline": "PT", "minutes": 140, "scheduled": 160, "missed": 20, "reason": "pain", "hour": 11},
            {"idx": 4, "day": 0, "discipline": "OT", "minutes": 95, "scheduled": 130, "missed": 35, "reason": "fatigue", "hour": 13},
        ],
        "evaluations": [
            {"idx": 1, "hours_after_admit": 22, "physician_id": "PHY-101", "physician_name": "Dr. Michael Lee", "first_day": True, "notes": "Initial physician assessment complete."},
        ],
        "functional_scores": [
            {"idx": 1, "discipline": "OT", "score_type": "FIM", "score": 35, "day": -14},
            {"idx": 2, "discipline": "OT", "score_type": "FIM", "score": 40, "day": -7},
            {"idx": 3, "discipline": "OT", "score_type": "FIM", "score": 43, "day": -1},
        ],
        "idt_days_ago": 12,
        "medical_days": [-1],
    },
    {
        "patient_id": "DEMO-P003",
        "mrn": "RC-MRN-1003",
        "first_name": "Ava",
        "last_name": "Thompson",
        "dob": datetime(1942, 1, 21).date(),
        "admission_datetime": dt_on(-20, 8),
        "primary_diagnosis": "Complex orthopedic recovery",
        "comorbidities": ["CHF", "CKD"],
        "assigned_disciplines": ["PT", "OT"],
        "sessions": [
            {"idx": 1, "day": -19, "discipline": "PT", "minutes": 50, "scheduled": 70, "missed": 20, "reason": "pain", "hour": 10},
            {"idx": 2, "day": -5, "discipline": "OT", "minutes": 110, "scheduled": 150, "missed": 40, "reason": None, "hour": 12},
            {"idx": 3, "day": -2, "discipline": "PT", "minutes": 100, "scheduled": 140, "missed": 40, "reason": "patient_refused", "hour": 11},
            {"idx": 4, "day": 0, "discipline": "OT", "minutes": 80, "scheduled": 120, "missed": 40, "reason": None, "hour": 9},
        ],
        "evaluations": [
            {"idx": 1, "hours_after_admit": 30, "physician_id": "PHY-102", "physician_name": "Dr. Sara Patel", "first_day": False, "notes": "Late first-day evaluation."},
            {"idx": 2, "hours_after_admit": 120, "physician_id": "PHY-102", "physician_name": "Dr. Sara Patel", "first_day": None, "notes": "Follow-up after decline."},
        ],
        "functional_scores": [
            {"idx": 1, "discipline": "PT", "score_type": "FIM", "score": 48, "day": -15},
            {"idx": 2, "discipline": "PT", "score_type": "FIM", "score": 44, "day": -7},
            {"idx": 3, "discipline": "PT", "score_type": "FIM", "score": 40, "day": -1},
        ],
        "idt_days_ago": 16,
        "medical_days": [-6, -2],
    },
    {
        "patient_id": "DEMO-P004",
        "mrn": "RC-MRN-1004",
        "first_name": "Liam",
        "last_name": "Brooks",
        "dob": datetime(1960, 11, 5).date(),
        "admission_datetime": dt_on(-8, 9),
        "primary_diagnosis": "Post-surgical debility",
        "comorbidities": ["Obesity"],
        "assigned_disciplines": ["PT", "OT", "ST"],
        "sessions": [
            {"idx": 1, "day": -8, "discipline": "PT", "minutes": 70, "scheduled": 70, "missed": 0, "reason": None, "hour": 10},
            {"idx": 2, "day": -4, "discipline": "OT", "minutes": 180, "scheduled": 190, "missed": 10, "reason": "rest_break", "hour": 9},
            {"idx": 3, "day": -1, "discipline": "ST", "minutes": 175, "scheduled": 180, "missed": 5, "reason": "fatigue", "hour": 14},
            {"idx": 4, "day": 0, "discipline": "PT", "minutes": 182, "scheduled": 182, "missed": 0, "reason": None, "hour": 11},
            {"idx": 5, "day": 0, "discipline": "OT", "minutes": 15, "scheduled": 20, "missed": 5, "reason": "patient_break", "hour": 15},
        ],
        "evaluations": [
            {"idx": 1, "hours_after_admit": 12, "physician_id": "PHY-103", "physician_name": "Dr. Kevin Scott", "first_day": True, "notes": "Rapid admission evaluation."},
        ],
        "functional_scores": [
            {"idx": 1, "discipline": "PT", "score_type": "FIM", "score": 52, "day": -7},
            {"idx": 2, "discipline": "PT", "score_type": "FIM", "score": 56, "day": -3},
            {"idx": 3, "discipline": "PT", "score_type": "FIM", "score": 60, "day": 0},
        ],
        "idt_days_ago": 2,
        "medical_days": [-2, -1, 0],
    },
    {
        "patient_id": "DEMO-P005",
        "mrn": "RC-MRN-1005",
        "first_name": "Sophia",
        "last_name": "Diaz",
        "dob": datetime(1952, 3, 14).date(),
        "admission_datetime": dt_on(-13, 9),
        "primary_diagnosis": "Neuromuscular weakness",
        "comorbidities": ["Anemia", "Peripheral neuropathy"],
        "assigned_disciplines": ["PT", "OT"],
        "sessions": [
            {"idx": 1, "day": -12, "discipline": "PT", "minutes": 55, "scheduled": 70, "missed": 15, "reason": "fatigue", "hour": 10},
            {"idx": 2, "day": -6, "discipline": "OT", "minutes": 130, "scheduled": 160, "missed": 30, "reason": "pain", "hour": 11},
            {"idx": 3, "day": -1, "discipline": "PT", "minutes": 200, "scheduled": 200, "missed": 0, "reason": None, "hour": 9},
            {"idx": 4, "day": 0, "discipline": "OT", "minutes": 185, "scheduled": 190, "missed": 5, "reason": "rest_break", "hour": 13},
        ],
        "evaluations": [
            {"idx": 1, "hours_after_admit": 18, "physician_id": "PHY-104", "physician_name": "Dr. Maria Alvarez", "first_day": True, "notes": "Admit evaluation complete."},
            {"idx": 2, "hours_after_admit": 60, "physician_id": "PHY-104", "physician_name": "Dr. Maria Alvarez", "first_day": None, "notes": "Follow-up for progression review."},
        ],
        "functional_scores": [
            {"idx": 1, "discipline": "OT", "score_type": "FIM", "score": 46, "day": -11},
            {"idx": 2, "discipline": "OT", "score_type": "FIM", "score": 43, "day": -4},
            {"idx": 3, "discipline": "OT", "score_type": "FIM", "score": 40, "day": 0},
        ],
        "idt_days_ago": 10,
        "medical_days": [-3],
    },
]


def upsert_patient(db, payload):
    patient = db.query(Patient).filter(Patient.patient_id == payload["patient_id"]).first()
    if patient is None:
        patient = Patient(patient_id=payload["patient_id"])
        db.add(patient)

    patient.mrn = payload["mrn"]
    patient.first_name = payload["first_name"]
    patient.last_name = payload["last_name"]
    patient.dob = payload["dob"]
    patient.admission_datetime = payload["admission_datetime"]
    patient.discharge_datetime = None
    patient.primary_diagnosis = payload["primary_diagnosis"]
    patient.comorbidities = payload["comorbidities"]
    patient.assigned_disciplines = payload["assigned_disciplines"]


def upsert_physician_user(db, physician_id, physician_name):
    user = db.query(User).filter(User.user_id == physician_id).first()
    if user is not None:
        return

    cleaned = physician_name.replace("Dr. ", "").strip()
    parts = cleaned.split(" ", 1)
    first_name = parts[0] if parts else "Physician"
    last_name = parts[1] if len(parts) > 1 else "User"

    db.add(
        User(
            user_id=physician_id,
            first_name=first_name,
            last_name=last_name,
            role="Physician",
            status="active",
        )
    )


def clear_seeded_child_records(db, patient_id, physician_eval_columns):
    db.query(TherapySession).filter(
        TherapySession.patient_id == patient_id,
        TherapySession.source == SEED_SOURCE,
    ).delete(synchronize_session=False)

    if "source" in physician_eval_columns:
        db.execute(
            text(
                "DELETE FROM physician_evaluations "
                "WHERE patient_id = :patient_id AND source = :source"
            ),
            {"patient_id": patient_id, "source": SEED_SOURCE},
        )
    else:
        db.execute(
            text(
                "DELETE FROM physician_evaluations "
                "WHERE patient_id = :patient_id AND evaluation_id LIKE :prefix"
            ),
            {"patient_id": patient_id, "prefix": f"PE-{patient_id}-%"},
        )

    db.query(FunctionalScore).filter(
        FunctionalScore.patient_id == patient_id,
        FunctionalScore.source == SEED_SOURCE,
    ).delete(synchronize_session=False)

    db.query(IDTMeeting).filter(
        IDTMeeting.patient_id == patient_id,
        IDTMeeting.idt_id.like(f"IDT-{patient_id}-%"),
    ).delete(synchronize_session=False)

    db.query(MedicalNecessityRecord).filter(
        MedicalNecessityRecord.patient_id == patient_id,
        MedicalNecessityRecord.record_id.like(f"MNR-{patient_id}-%"),
    ).delete(synchronize_session=False)


def insert_physician_evaluation(db, patient, evaluation, physician_eval_columns):
    evaluation_time = patient["admission_datetime"] + timedelta(hours=evaluation["hours_after_admit"])

    row = {
        "evaluation_id": f"PE-{patient['patient_id']}-{evaluation['idx']:02d}",
        "patient_id": patient["patient_id"],
        "physician_id": evaluation["physician_id"],
        "notes": evaluation["notes"],
    }

    if "evaluation_datetime" in physician_eval_columns:
        row["evaluation_datetime"] = evaluation_time
    elif "evaluation_timestamp" in physician_eval_columns:
        row["evaluation_timestamp"] = evaluation_time
    elif "timestamp" in physician_eval_columns:
        row["timestamp"] = evaluation_time

    if "physician_name" in physician_eval_columns:
        row["physician_name"] = evaluation["physician_name"]
    elif "physician" in physician_eval_columns:
        row["physician"] = evaluation["physician_name"]

    if "first_day_compliance" in physician_eval_columns:
        row["first_day_compliance"] = evaluation["first_day"]

    if "source" in physician_eval_columns:
        row["source"] = SEED_SOURCE

    column_names = ", ".join(row.keys())
    bind_names = ", ".join(f":{name}" for name in row.keys())
    db.execute(
        text(f"INSERT INTO physician_evaluations ({column_names}) VALUES ({bind_names})"),
        row,
    )


def insert_therapy_session(db, patient_id, session, therapy_session_columns):
    row = {
        "session_id": f"TS-{patient_id}-{session['idx']:02d}",
        "patient_id": patient_id,
        "discipline": session["discipline"],
        "delivered_minutes": session["minutes"],
        "scheduled_minutes": session["scheduled"],
        "missed_minutes": session["missed"],
        "reason_code": session["reason"],
        "timestamp": dt_on(session["day"], session["hour"]),
        "source": SEED_SOURCE,
    }

    if "therapist_id" in therapy_session_columns:
        row["therapist_id"] = f"THER-{patient_id[-3:]}-{session['discipline']}"

    column_names = ", ".join(row.keys())
    bind_names = ", ".join(f":{name}" for name in row.keys())
    db.execute(
        text(f"INSERT INTO therapy_sessions ({column_names}) VALUES ({bind_names})"),
        row,
    )


def seed_demo_data():
    db = SessionLocal()
    therapy_session_columns = {
        c["name"] for c in inspect(db.bind).get_columns("therapy_sessions")
    }
    physician_eval_columns = {
        c["name"] for c in inspect(db.bind).get_columns("physician_evaluations")
    }

    try:
        for patient in DEMO_PATIENTS:
            patient_id = patient["patient_id"]
            upsert_patient(db, patient)
            db.flush()
            clear_seeded_child_records(db, patient_id, physician_eval_columns)

            for session in patient["sessions"]:
                insert_therapy_session(db, patient_id, session, therapy_session_columns)

            for evaluation in patient["evaluations"]:
                upsert_physician_user(db, evaluation["physician_id"], evaluation["physician_name"])
                db.flush()
                insert_physician_evaluation(db, patient, evaluation, physician_eval_columns)

            for score in patient["functional_scores"]:
                db.add(
                    FunctionalScore(
                        score_id=f"FS-{patient_id}-{score['idx']:02d}",
                        patient_id=patient_id,
                        discipline=score["discipline"],
                        score_type=score["score_type"],
                        score_value=score["score"],
                        timestamp=dt_on(score["day"], 10),
                        notes="Seeded functional assessment trend",
                        source=SEED_SOURCE,
                    )
                )

            db.add(
                IDTMeeting(
                    idt_id=f"IDT-{patient_id}-01",
                    patient_id=patient_id,
                    meeting_datetime=dt_on(-patient["idt_days_ago"], 13),
                    physician_present=True,
                    rn_present=True,
                    pt_present=True,
                    ot_present=True,
                    slp_present=("ST" in patient["assigned_disciplines"]),
                    goals_updated=(patient_id != "DEMO-P003"),
                    barriers="Pain and fatigue" if patient_id in {"DEMO-P002", "DEMO-P003", "DEMO-P005"} else "None",
                    physician_signoff=dt_on(-patient["idt_days_ago"], 17),
                )
            )

            for idx, day in enumerate(patient["medical_days"], start=1):
                db.add(
                    MedicalNecessityRecord(
                        record_id=f"MNR-{patient_id}-{idx:02d}",
                        patient_id=patient_id,
                        statement="Skilled therapy remains medically necessary due to ongoing deficits.",
                        barriers="Activity tolerance limitation",
                        clinical_reasoning="Requires skilled intervention to prevent decline and improve function.",
                        timestamp=dt_on(day, 16),
                        discipline="PT",
                    )
                )

        db.commit()

        print("Demo seed complete.")
        print("Patients: 5")
        print("Therapy sessions: 3-6 per patient with mixed compliance patterns")
        print("Physician evaluations: 1-2 per patient")
        print("Functional trends: improving and declining cases included")
        print("Expected risk profile mix: Low, Medium, High")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
