from faker import Faker
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.services.patient_service import PatientService

fake = Faker()

def seed_patients(n=20):
    db = SessionLocal()
    service = PatientService(db)

    for i in range(n):
        dob = fake.date_of_birth(minimum_age=20, maximum_age=90).isoformat()
        admission = datetime.utcnow().isoformat()

        data = {
            "patient_id": f"P{100 + i}",
            "mrn": fake.unique.bothify(text="MRN###"),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "dob": dob,
            "admission_datetime": admission,
            "primary_diagnosis": fake.word().title(),
            "comorbidities": [fake.word().title() for _ in range(2)],
            "assigned_disciplines": ["PT", "OT", "ST"][:fake.random_int(1, 3)]
        }

        service.create_patient(data)

    print(f"Seeded {n} patients successfully.")

if __name__ == "__main__":
    seed_patients()
    