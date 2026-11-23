import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import Base, get_db
from app.main import app

assert settings.test_database_url, "TEST_DATABASE_URL manque dans le .env"
assert settings.test_database_url != settings.database_url, (
    "La base de test doit être différente de la base de développement"
)

engine = create_engine(settings.test_database_url)


@pytest.fixture(scope="session", autouse=True)
def creer_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()