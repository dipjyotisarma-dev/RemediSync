"""RemediSync database and relational persistence package.

Exports ORM domain models, database engine, session factory, schema migration,
data access repository, and high-performance database seeder.
"""

from typing import Any

__all__ = [
    "Base",
    "Branch",
    "Supplier",
    "Medicine",
    "Batch",
    "DailySale",
    "InventorySnapshot",
    "ReplenishmentOrder",
    "engine",
    "SessionLocal",
    "get_db",
    "DATABASE_URL",
    "PharmacyRepository",
    "create_all_tables",
    "drop_all_tables",
    "seed_database",
]


def __getattr__(name: str) -> Any:
    """Lazy module attribute loader to prevent circular imports during CLI runs."""
    if name in (
        "Base",
        "Branch",
        "Supplier",
        "Medicine",
        "Batch",
        "DailySale",
        "InventorySnapshot",
        "ReplenishmentOrder",
    ):
        import src.database.models as models
        return getattr(models, name)

    if name in ("engine", "SessionLocal", "get_db", "DATABASE_URL"):
        import src.database.session as session
        return getattr(session, name)

    if name == "PharmacyRepository":
        from src.database.repository import PharmacyRepository
        return PharmacyRepository

    if name in ("create_all_tables", "drop_all_tables"):
        import src.database.schema as schema
        return getattr(schema, name)

    if name == "seed_database":
        from src.database.seed import seed_database
        return seed_database

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
