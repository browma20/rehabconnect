import os


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_raw_database_url = os.getenv("DATABASE_URL")
if not _raw_database_url:
    raise RuntimeError("DATABASE_URL is not set")

DATABASE_URL = _normalize_database_url(_raw_database_url)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"