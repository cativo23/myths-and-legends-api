from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Explicit pool sizing (not magic numbers): this deploys to a small,
# resource-constrained VPS (~8GB RAM shared with ~20 other containers,
# single Postgres instance, single uvicorn worker), so pool_size + max_overflow
# are deliberately kept modest, and pool_recycle guards against stale
# connections after any Postgres-side idle-connection reaping.
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
