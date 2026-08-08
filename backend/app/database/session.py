"""
БЫЛО: create_engine с connect_args={"check_same_thread": False} —
это флаг, специфичный для SQLite, и он ломает подключение к Postgres
(psycopg2 такого параметра не принимает).

СТАЛО: connect_args применяется условно, только для sqlite — так один
и тот же код работает и с Postgres (в докере), и с sqlite (для быстрых
локальных тестов через .env).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
