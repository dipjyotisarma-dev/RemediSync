"""Dependency injection providers for FastAPI route handlers."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.repository import PharmacyRepository
from src.database.session import get_db


def get_repository(db: Session = Depends(get_db)) -> PharmacyRepository:
    """Dependency yielding an initialized PharmacyRepository bound to the current session."""
    return PharmacyRepository(db)
