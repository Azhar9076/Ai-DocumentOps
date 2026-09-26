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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        if "postgresql" in engine.dialect.name:
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
        elif "sqlite" in engine.dialect.name:
            for sql in (
                "ALTER TABLE documents ADD COLUMN audit_summary TEXT DEFAULT '';",
                "ALTER TABLE audit_logs ADD COLUMN run_number INTEGER DEFAULT 1;",
                "ALTER TABLE audit_logs ADD COLUMN elapsed_ms INTEGER DEFAULT 0;",
            ):
                try:
                    conn.exec_driver_sql(sql)
                except Exception:
                    pass


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