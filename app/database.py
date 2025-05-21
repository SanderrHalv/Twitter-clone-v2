from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.utils.settings import settings  # load DATABASE_URL from .env

# ----------------------------------------------------------------
# ENGINE & BASE
# ----------------------------------------------------------------
# Create the SQLAlchemy engine using the DATABASE_URL from settings.
# pool_pre_ping ensures stale connections are checked before use.
# future=True opts in to SQLAlchemy 2.0 style API.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

# Base class for ORM models; your models should inherit from this.
Base = declarative_base()

# ----------------------------------------------------------------
# SESSION FACTORY
# ----------------------------------------------------------------
# sessionmaker factory bound to the engine.
# expire_on_commit=False prevents attributes from being expired after commit,
# which is useful when returning ORM objects from endpoints.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=Session,    # <-- ensure we instantiate actual Session objects
)

# ----------------------------------------------------------------
# DEPENDENCY
# ----------------------------------------------------------------
def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is closed
    after the request finishes (regardless of exceptions).
    """
    db: Session = SessionLocal()  # <-- create a new Session instance
    try:
        yield db
    finally:
        db.close()
