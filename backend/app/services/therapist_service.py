from sqlalchemy.orm import Session
from backend.app.models.therapist import Therapist

class TherapistService:
    def __init__(self, db: Session):
        self.db = db

    def create_therapist(self, data):
        therapist = Therapist(
            therapist_id=data["therapist_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            discipline=data["discipline"],
            active=data.get("active", True)
        )
        self.db.add(therapist)
        self.db.commit()
        self.db.refresh(therapist)
        return therapist

    def get_therapist(self, therapist_id: str):
        return self.db.query(Therapist).filter(Therapist.therapist_id == therapist_id).first()

    def get_therapist_by_id(self, therapist_id: str):
        return self.get_therapist(therapist_id)

    def list_therapists(self):
        return self.db.query(Therapist).all()

    def update_therapist(self, therapist_id: str, **updates):
        therapist = self.get_therapist(therapist_id)
        if not therapist:
            return None

        for key, value in updates.items():
            if hasattr(therapist, key):
                setattr(therapist, key, value)

        self.db.commit()
        self.db.refresh(therapist)
        return therapist

    def delete_therapist(self, therapist_id: str):
        therapist = self.get_therapist(therapist_id)
        if not therapist:
            return False

        self.db.delete(therapist)
        self.db.commit()
        return True