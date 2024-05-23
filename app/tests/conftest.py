import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.entity.models import Base
from src.database.db import get_db
from tests.mock_db import MockDB, USERS, PHOTOS


@pytest.fixture(scope="module")
def session():
    # Create the database

    Mock_db = MockDB(users=USERS, photos=PHOTOS)
    local_session = Mock_db()
    
    try:
        yield local_session
    finally:
        local_session.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


# @pytest.fixture(scope="module")
# def user():
#     return {"username": "deadpool", "email": "deadpool@example.com", "password": "123456789"}
