from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

raw_url = str(settings.database_url).strip()
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

db_url = make_url(raw_url)

engine_kwargs = {}
if "sqlite" in db_url.drivername:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Supabase / Neon connection pool configuration
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_engine(db_url, future=True, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _run_migrations(target_engine) -> None:
    Base.metadata.create_all(bind=target_engine)
    with target_engine.begin() as conn:
        if "postgresql" in target_engine.dialect.name:
            for sql in (
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS audit_summary TEXT DEFAULT '';",
                "ALTER TYPE docstatus ADD VALUE IF NOT EXISTS 'CANCELLED';",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS run_number INTEGER DEFAULT 1;",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS elapsed_ms INTEGER DEFAULT 0;",
            ):
                try:
                    conn.exec_driver_sql(sql)
                except Exception:
                    pass
        elif "sqlite" in target_engine.dialect.name:
            for sql in (
                "ALTER TABLE documents ADD COLUMN audit_summary TEXT DEFAULT '';",
                "ALTER TABLE audit_logs ADD COLUMN run_number INTEGER DEFAULT 1;",
                "ALTER TABLE audit_logs ADD COLUMN elapsed_ms INTEGER DEFAULT 0;",
            ):
                try:
                    conn.exec_driver_sql(sql)
                except Exception:
                    pass


def init_db() -> None:
    global engine
    try:
        with engine.connect() as conn:
            pass
        _run_migrations(engine)
    except Exception as exc:
        logger.warning(
            "Primary database connection failed (%s). Falling back to local SQLite database for resilience.",
            exc,
        )
        fallback_dir = Path(settings.storage_dir)
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_db_path = fallback_dir / "fallback_app.db"
        fallback_url = f"sqlite:///{fallback_db_path.as_posix()}"

        fallback_engine = create_engine(
            fallback_url,
            future=True,
            connect_args={"check_same_thread": False},
        )
        engine = fallback_engine
        SessionLocal.configure(bind=engine)
        _run_migrations(engine)
        logger.info("Fallback SQLite database initialized successfully at %s", fallback_db_path)


def get_db() -> Iterator[Session]:
    """Dependency for FastAPI HTTP routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Scoped context manager for background pipeline agents.
    Ensures DB sessions close cleanly between LLM calls so connection pools aren't held open.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()