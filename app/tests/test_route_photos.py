from unittest.mock import MagicMock
import asyncio
from time import sleep
from datetime import datetime
from fastapi import File
import pytest
import uuid

from src.entity.models import User, Photo
from src.services.auth import auth_service
from src.exceptions.exceptions import RETURN_MSG


def user_token(user: User) -> str:
    access_token = asyncio.run(auth_service.create_access_token(
        data={"sub": user.email}))
    return access_token


def test_create_photo_user0(client, users, mock_redis, mock_cache, monkeypatch):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    body = ["tags", "str, str1"]

    url = "http://"
    mock_upload_photo = MagicMock()
    mock_get_photo_url = MagicMock()
    mock_get_photo_url.return_value = url
    mock_get_unique_file_name = MagicMock()


    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.upload_photo", mock_upload_photo)
    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.get_photo_url", mock_get_photo_url)
    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.get_unique_file_name", mock_get_unique_file_name)


    file_name = "mock_db.py"
    with open(file_name, "rb") as fh:
        file = ("file", fh)

        responce = client.post(
            f"api/photos/", files=[file,], json=body, headers=[header,])


    assert responce.status_code == 201, responce.text
    data = responce.json()
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "url" in data


# @pytest.mark.skip("fail due to event loop close")
def test_read_photos_user0(client, users, mock_redis, mock_cache):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/photos/", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert "id" in data[0]
    assert "created_at" in data[0]
    assert "updated_at" in data[0]
    assert "url" in data[0]

# @pytest.mark.skip("fail due to event loop close")


def test_read_photos_moderator(client, moderator, mock_redis, mock_cache):
    user: User = moderator
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/photos/", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert "id" in data[0]
    assert "created_at" in data[0]
    assert "updated_at" in data[0]
    assert "url" in data[0]

# @pytest.mark.skip("fail due to event loop close")


def test_read_photos_admin(client, admin, mock_redis, mock_cache):
    user: User = admin
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/photos/", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert "id" in data[0]
    assert "created_at" in data[0]
    assert "updated_at" in data[0]
    assert "url" in data[0]


# @pytest.mark.skip("fail due to event loop close")
def test_read_photo_by_id_user0_exist(client, users, photos, mock_redis, mock_cache):
    user: User = users[0]
    photo: Photo = photos[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/photos/{photo.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == str(photo.id)
    assert "created_at" in data
    assert "updated_at" in data
    assert data["url"] == photo.url


# @pytest.meark.skip("fail due to event loop close")
def test_read_photo_by_id_user0_not_exist(client, users, mock_redis, mock_cache):
    user: User = users[0]
    photo: Photo = Photo(id=uuid.uuid4())
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/photos/{photo.id}", headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == "Photo not found"


@pytest.mark.skip("need photos to be created")
def test_read_qr_by_photo_id_user0_exist(client, users, photos, mock_redis, mock_cache):
    user: User = users[0]
    photo: Photo = photos[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/photos/link/{photo.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["detail"] == "Photo not found"
