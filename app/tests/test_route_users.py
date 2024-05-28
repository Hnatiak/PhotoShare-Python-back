from unittest.mock import MagicMock
import asyncio
from time import sleep
from datetime import datetime
from fastapi import File
from pathlib import Path

from src.entity.models import User, Role, Isbanned
from src.services.auth import auth_service
from src.exceptions.exceptions import RETURN_MSG


def user_token(user: User) -> str:
    access_token = asyncio.run(auth_service.create_access_token(
        data={"sub": user.email}))
    return access_token


def test_me_user0(client, users, mock_redis):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/users/me", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["phone"] == user.phone
    assert data["birthday"] == user.birthday
    assert data["avatar"] == user.avatar
    assert data["role"] == user.role.value


def test_me_unregistered_user(client, new_user, mock_redis):
    user = MagicMock(email=new_user['email'])
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/users/me", headers=[header,])

    assert responce.status_code == 401, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.credentials_error


def test_update_user0(client, users, mock_redis):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    body = {"username": "new_name", 
            "phone": "1234567890", 
            "birthday": str(datetime.today().date())}

    responce = client.put(
        f"api/users/", json=body, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == user.id
    assert data["username"] == body["username"]
    assert data["email"] == user.email
    assert data["phone"] == body["phone"]
    assert data["birthday"] == body["birthday"]
    assert data["avatar"] == user.avatar
    assert data["role"] == user.role.value


def test_update_avatar_user0(client, users, mock_redis, monkeypatch):
    sleep(1)
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    avatar_url = "http://"
    mock_upload_photo = MagicMock()
    mock_get_photo_url = MagicMock()
    mock_transformate_photo = MagicMock()
    mock_transformate_photo.return_value = avatar_url

    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.upload_photo", mock_upload_photo)
    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.get_photo_url", mock_get_photo_url)
    monkeypatch.setattr(
        "src.routes.users.CloudPhotoService.transformate_photo", mock_transformate_photo)

    file_name = Path(__file__).parent.joinpath("mock_db.py")
    with open(file_name, "rb") as fh:
        file = ("file", fh)

        responce = client.put(
            f"api/users/avatar", files=[file,], headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == user.id
    assert data["avatar"] == avatar_url
    assert data["created_at"] != data["updated_at"]
    mock_upload_photo.assert_called_once()
    mock_get_photo_url.assert_called_once()
    mock_transformate_photo.assert_called_once()


def test_get_all_admin(client, admin, mock_redis):
    user: User = admin
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/users/all", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert "id" in data[0]
    assert "username" in data[0]
    assert "email" in data[0]
    assert "phone" in data[0]
    assert "birthday" in data[0]
    assert "avatar" in data[0]
    assert "role" in data[0]

def test_get_all_moderator(client, moderator, mock_redis):
    user: User = moderator
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/users/all", params=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_get_all_user0(client, users, mock_redis):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("skip", "0"), ("limit", "10")]

    responce = client.get(
        f"api/users/all", params=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_get_user_by_id_user0_self(client, users, mock_redis):
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/users/{user.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["phone"] == user.phone
    assert data["avatar"] == user.avatar
    assert data["role"] == user.role.value

def test_get_user_by_id_user0_other(client, users, mock_redis):
    user: User = users[0]
    target: User = users[1]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/users/{target.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == target.id
    assert data["username"] == target.username
    assert data["email"] == target.email
    assert data["phone"] == target.phone
    assert data["avatar"] == target.avatar
    assert data["role"] == target.role.value

def test_get_user_by_id_user0_not_exist(client, users, mock_redis):
    user: User = users[0]
    target: User = User(id=1000)
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/users/{target.id}", headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.record_not_found

def test_change_role_admin_user_exist(client, admin, users, mock_redis):
    user: User = admin
    target: User = users[0]
    new_role = Role.moderator.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"role": new_role}
    responce = client.put(
        f"api/users/role/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == target.id
    assert data["username"] == target.username
    assert data["email"] == target.email
    assert data["role"] == new_role

def test_change_role_admin_user_not_exist(client, admin, users, mock_redis):
    user: User = admin
    target: User = User(id=1000)
    new_role = Role.moderator.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"role": new_role}
    responce = client.put(
        f"api/users/role/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.record_not_found

def test_change_role_moderator(client, moderator, users, mock_redis):
    user: User = moderator
    target: User = users[0]
    new_role = Role.user.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"role": new_role}
    responce = client.put(
        f"api/users/role/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_change_role_user0(client, users, mock_redis):
    user: User = users[0]
    target: User = users[1]
    new_role = Role.user.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"role": new_role}
    responce = client.put(
        f"api/users/role/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_ban_admin_user_exist(client, admin, users, mock_redis):
    user: User = admin
    target: User = users[0]
    isbanned = Isbanned.banned.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"isbanned": isbanned}
    responce = client.put(
        f"api/users/ban/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == target.id
    assert data["username"] == target.username
    assert data["email"] == target.email
    assert data["isbanned"] == True
    assert data["isbanned"] != target.isbanned

def test_unban_admin_user_exist(client, admin, users, mock_redis):
    user: User = admin
    target: User = users[0]
    isbanned = Isbanned.unbanned.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"isbanned": isbanned}
    responce = client.put(
        f"api/users/ban/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert data["id"] == target.id
    assert data["username"] == target.username
    assert data["email"] == target.email
    assert data["isbanned"] == False
    assert data["isbanned"] != target.isbanned

def test_ban_admin_user_not_exist(client, admin, users, mock_redis):
    user: User = admin
    target: User = User(id=1000)
    isbanned = Isbanned.banned.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = {"isbanned": isbanned}
    responce = client.put(
        f"api/users/ban/{target.id}", data=params, headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.record_not_found

def test_ban_moderator_user_exist(client, moderator, users, mock_redis):
    user: User = moderator
    target: User = users[0]
    isbanned = Isbanned.banned.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("isbanned", isbanned), ]
    responce = client.put(
        f"api/users/ban/{target.id}", params=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_ban_user0_user_exist(client, users, mock_redis):
    user: User = users[0]
    target: User = users[1]
    isbanned = Isbanned.banned.value
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("isbanned", isbanned), ]
    responce = client.put(
        f"api/users/ban/{target.id}", params=params, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden
