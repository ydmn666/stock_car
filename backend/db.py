from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
SQLITE_FALLBACK_PATH = ROOT_DIR / "stock_data.db"

load_dotenv(ROOT_DIR / ".env")


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_FALLBACK_PATH.as_posix()}")


DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
