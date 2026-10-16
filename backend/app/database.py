import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'kings_grillz.db'}"

DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL

# Accept PostgreSQL URLs supplied by hosting providers.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

engine_options = {
    "hide_parameters": True,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite:"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()