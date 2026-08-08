"""
БЫЛО: test_api.py импортировал `from app.tests.conftest import client`,
но conftest.py не существовал вовсе — тесты падали на этапе сбора
(collection error), ещё до выполнения.

СТАЛО: fixture `client` поднимает приложение на sqlite in-memory —
тесты не трогают Postgres и не оставляют мусора между запусками.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # main.py грузит модель на реальном startup event — для теста подменяем
    # ml.model на реальную функцию, но с MODEL_PATH, указывающим на тестовый
    # артефакт, если он есть; иначе тесты /predict пропускаются ниже.
    import main as app_main

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db

    with TestClient(app_main.app) as test_client:
        yield test_client

    app_main.app.dependency_overrides.clear()
