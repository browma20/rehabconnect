import random
import uuid
from datetime import date, timedelta, time, datetime

from faker import Faker

from app.database import SessionLocal
from app.services.patient_service import PatientService
from app.services.session_service import SessionService
from app.services.therapist_service import TherapistService


fake = Faker()


def seed_sessions(min_per_patient=3, max_per_patient=5):
    db = SessionLocal()

    try:
        therapist_service = TherapistService(db)
        patient_service = PatientService(db)
        session_service = SessionService(db)

        therapists = therapist_service.list_therapists()
        patients = patient_service.list_patients()

        if not therapists:
            print("No therapists found. Seed therapists first.")
            return
        if not patients:
            print("No patients found. Seed patients first.")
            return

        created_count = 0
        start_hour_options = [9, 10, 11, 13, 14, 15]

        for patient in patients:
            session_count = random.randint(min_per_patient, max_per_patient)

            for _ in range(session_count):
                therapist = random.choice(therapists)
                session_date = date.today() + timedelta(days=random.randint(0, 13))
                start_hour = random.choice(start_hour_options)
                start_dt = datetime.combine(session_date, time(hour=start_hour, minute=0))
                end_dt = start_dt + timedelta(minutes=30)

                data = {
                    "id": str(uuid.uuid4()),
                    "therapist_id": therapist.therapist_id,
                    "patient_id": patient.patient_id,
                    "date": session_date.isoformat(),
                    "start_time": start_dt.time().isoformat(),
                    "end_time": end_dt.time().isoformat(),
                    "discipline": therapist.discipline,
                    "notes": fake.sentence(nb_words=8)
                }

                session_service.create_session(data)
                created_count += 1

        print(
            f"Seeded {created_count} sessions for {len(patients)} patients "
            f"using {len(therapists)} therapists."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed_sessions()
