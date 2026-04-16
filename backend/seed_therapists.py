from faker import Faker
from app.database import SessionLocal
from app.services.therapist_service import TherapistService

fake = Faker()

DISCIPLINES = ["PT", "OT", "ST"]

def seed_therapists(n=20):
    db = SessionLocal()
    service = TherapistService(db)

    for i in range(n):
        data = {
            "therapist_id": f"T{100 + i}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "discipline": fake.random_element(DISCIPLINES),
            "active": True
        }

        service.create_therapist(data)

    print(f"Seeded {n} therapists successfully.")

if __name__ == "__main__":
    seed_therapists()
