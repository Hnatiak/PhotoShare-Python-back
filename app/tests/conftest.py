import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from main import app
from src.entity.models import Base
from src.database.db import get_db
from src.entity.models import User, Photo, Role
from tests.mock_db import MockDB, USERS, PHOTOS


@pytest.fixture(scope="module")
def Mock_db():
    # Create the database
    init_db = MockDB(users=USERS, photos=PHOTOS)
    
    return init_db


@pytest.fixture(scope="module")
def session(Mock_db):

    session = Mock_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client(Mock_db):

    def override_get_db():
        session = Mock_db()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope='module')
def new_user():
    return {'username': 'new_test_user', 'email': 'user@test.com', 'password': 'secret78'}


@pytest.fixture(scope='function')
def users(session):
    users = session.query(User).filter_by(role=Role.user).all()
    return users


@pytest.fixture(scope='module')
def moderator(session):
    user = session.query(User).filter_by(role=Role.moderator).first()
    return user


@pytest.fixture(scope='module')
def admin(session):
    user = session.query(User).filter_by(role=Role.admin).first()
    return user


@pytest.fixture(scope='module')
def photos(session):
    photos = session.query(Photo).all()
    return photos

@pytest.fixture(scope='function')
def mock_redis(monkeypatch):
    monkeypatch.setattr(
        "fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr(
        "fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr(
        "fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())


@pytest.fixture(scope='function')
def mock_cache(monkeypatch):
    monkeypatch.setattr(
        "src.repository.photos.query_executor.client", None)
    monkeypatch.setattr(
        "src.repository.qrcode.query_executor.client", None)
