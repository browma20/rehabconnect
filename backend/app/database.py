from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from .config import DATABASE_URL, DEBUG

# Define Base exactly once - all models inherit from this
Base = declarative_base()

engine = create_engine(DATABASE_URL, echo=DEBUG, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()