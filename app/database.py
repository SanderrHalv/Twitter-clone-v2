from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.utils.settings import settings  # load DATABASE_URL from .env

# ----------------------------------------------------------------
# ENGINE & BASE
# ----------------------------------------------------------------
# Create the SQLAlchemy engine using the DATABASE_URL from settings.
# echo=True can be toggled for SQL logging; disable in prod for performance.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # checks connections before using them
    future=True              # use 2.0 style API
)

# Base class for ORM models; models should inherit from this
Base = declarative_base()

# ----------------------------------------------------------------
# SESSION FACTORY
# ----------------------------------------------------------------
# sessionmaker factory bound to the engine; expire_on_commit=False prevents
# attributes from being expired after commit, which helps when returning ORM
# objects from your endpoints.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=sessionmaker
)

# ----------------------------------------------------------------
# DEPENDENCY
# ----------------------------------------------------------------
def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is closed
    after the request finishes (regardless of exceptions).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
