from datetime import datetime, timedelta, time, timezone

from sqlalchemy import inspect, text

from backend.app.database import SessionLocal
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.models.therapy_session import TherapySession
from backend.app.models.functional_score import FunctionalScore
from backend.app.models.idt_meeting import IDTMeeting
from backend.app.models.medical_necessity_record import MedicalNecessityRecord


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
