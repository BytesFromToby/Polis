"""
db/session.py — SQLAlchemy engine and session factory.

Database URL defaults to a local SQLite file (polis.db) in the working
directory. Override by setting the POLIS_DB_URL environment variable.

Usage in FastAPI routes:
    from db.session import get_db
    from sqlalchemy.orm import Session

    def my_route(db: Session = Depends(get_db)):
        ...
"""
from __future__ import annotations
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

_DEFAULT_DB_URL = "sqlite:///polis.db"
DATABASE_URL: str = os.environ.get("POLIS_DB_URL", _DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it on exit."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist. Call once at server startup."""
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate() -> None:
    """Add columns/tables that existing DBs may be missing (forward-only migrations)."""
    _add_column_if_missing("cities",    "llm_config_json",  "TEXT")
    _add_column_if_missing("sim_runs",  "llm_profile_id",   "TEXT")


def _add_column_if_missing(table: str, column: str, col_type: str) -> None:
    with engine.connect() as conn:
        from sqlalchemy import text
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        existing = {row[1] for row in rows}
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            conn.commit()
