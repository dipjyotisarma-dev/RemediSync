"""Database connection engine and session factory for RemediSync.

Supports PostgreSQL with production connection pooling (pool_size=20, max_overflow=10)
and automatic fallback to SQLite for local development and test execution.
"""

import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load local .env if available
load_dotenv()

DEFAULT_DB_PATH = Path("data/remedisync.db").resolve()
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

# Resolve DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# SQLAlchemy 1.4+ compatibility: postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_engine(url: str = DATABASE_URL):
    """Create a configured SQLAlchemy engine based on target dialect.

    Args:
        url: Database connection URL.

    Returns:
        Configured SQLAlchemy Engine instance.
    """
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    # Production PostgreSQL connection pool configuration
    return create_engine(
        url,
        pool_size=20,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True,  # Test connection liveness before checking out from pool
        echo=False,
    )


engine = get_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency provider yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
