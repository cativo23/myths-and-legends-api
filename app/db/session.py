from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.
    Used by FastAPI endpoints to get database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
