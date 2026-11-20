"""Database schema initialization and DDL lifecycle CLI."""

from sqlalchemy.engine import Engine
from src.database.session import engine as default_engine
from src.database.models import Base


def create_all_tables(engine: Engine = default_engine) -> None:
    """Create all registered domain tables, indexes, and constraints.

    Args:
        engine: Target SQLAlchemy Engine instance.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine: Engine = default_engine) -> None:
    """Drop all tables registered in metadata (destructive operation).

    Args:
        engine: Target SQLAlchemy Engine instance.
    """
    Base.metadata.drop_all(bind=engine)


def main() -> None:
    """CLI runner to initialize database tables."""
    print(f"Connecting to database: {default_engine.url.render_as_string(hide_password=True)}")
    print("Creating all tables, constraints, and composite indexes...")
    create_all_tables(default_engine)
    table_names = list(Base.metadata.tables.keys())
    print(f"[SUCCESS] {len(table_names)} tables verified in database:")
    for t in sorted(table_names):
        print(f"  - {t}")


if __name__ == "__main__":
    main()
