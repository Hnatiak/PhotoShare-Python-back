from unittest.mock import MagicMock
import asyncio
import uuid
from time import sleep

from src.entity.models import User, Photo, Comment
from src.services.auth import auth_service
from src.exceptions.exceptions import RETURN_MSG


def user_token(user: User) -> str:
    access_token = asyncio.run(auth_service.create_access_token(
        data={"sub": user.email}))
    return access_token

def test_create_comment_user0(client, users, photos):
    user: User = users[0]
    token = user_token(user)
    photo: Photo = photos[0]
    comment = "user0 comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.post(
        f"api/comments/{photo.id}", json=comment, headers=[header,])

    assert responce.status_code == 201, responce.text
    data = responce.json()
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["user_id"] == user.id
    assert data["photo_id"] == str(photo.id)
    assert data["text"] == comment


def test_create_comment_user1(client, users, photos):
    user: User = users[1]
    token = user_token(user)
    photo: Photo = photos[0]
    comment = "user1 comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.post(
        f"api/comments/{photo.id}", json=comment, headers=[header,])

    assert responce.status_code == 201, responce.text
    data = responce.json()
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["user_id"] == user.id
    assert data["photo_id"] == str(photo.id)
    assert data["text"] == comment

def test_create_comment_invalid_photo_id(client, users):
    user: User = users[0]
    token = user_token(user)
    # photo: Photo = photos[0]
    photo = MagicMock(id=uuid.uuid4())
    comment = "user comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.post(
        f"api/comments/{photo.id}", json=comment, headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.record_not_found

def test_edit_own_comment_user0(client, users, session):
    sleep(1)
    user: User = users[0]
    author: User = user
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    comment = "edited user0 comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.put(
        f"api/comments/record/{comment_record.id}", json=comment, headers=[header,])

    assert responce.status_code == 202, responce.text
    data = responce.json()
    assert data["id"] == comment_record.id
    assert data["created_at"] != data["updated_at"]
    assert data["user_id"] == user.id
    assert data["text"] == comment

def test_edit_other_comment_user0(client, users, session):
    # sleep(1)
    user: User = users[0]
    author: User = users[1]
    token = user_token(user)
    comment_record = session.query(Comment).filter_by(user_id=author.id).first()
    comment = "edited user0 comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.put(
        f"api/comments/record/{comment_record.id}", json=comment, headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.access_forbiden

def test_edit_not_exist_comment_user0(client, users):
    # sleep(1)
    user: User = users[0]
    token = user_token(user)
    comment_record = MagicMock(id=1000)
    comment = "edited user0 comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.put(
        f"api/comments/record/{comment_record.id}", json=comment, headers=[header,])

    assert responce.status_code == 404, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.record_not_found

def test_edit_comment_moderator(client, moderator, users, session):
    sleep(1)
    user: User = moderator
    author: User = users[1]
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    comment = "edited moderator comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.put(
        f"api/comments/record/{comment_record.id}", json=comment, headers=[header,])

    assert responce.status_code == 202, responce.text
    data = responce.json()
    assert data["id"] == comment_record.id
    assert data["created_at"] != data["updated_at"]
    assert data["user_id"] == author.id
    assert data["text"] == comment

def test_edit_comment_admin(client, admin, users, session):
    sleep(1)
    user: User = admin
    author: User = users[1]
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    comment = "edited admin comment"
    header = ["Authorization", f"Bearer {token}"]

    responce = client.put(
        f"api/comments/record/{comment_record.id}", json=comment, headers=[header,])

    assert responce.status_code == 202, responce.text
    data = responce.json()
    assert data["id"] == comment_record.id
    assert data["created_at"] != data["updated_at"]
    assert data["user_id"] == author.id
    assert data["text"] == comment

def test_comments_photo_exists(client, photos, users):
    photo: Photo = photos[0]
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/comments/{photo.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "user_id" in data[0]
    assert "photo_id" in data[0]
    assert "text" in data[0]

def test_comments_photo_not_exists(client, users):
    photo = MagicMock(id=uuid.uuid4())
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]

    responce = client.get(
        f"api/comments/{photo.id}", headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_comments_by_user_id(client, users):
    
    user: User = users[0]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("user_id", user.id), ("offset", "0"), ("limit", "10")]

    responce = client.get(
        f"/api/comments/users/", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "user_id" in data[0]
    assert data[0]["user_id"] == user.id
    assert "photo_id" in data[0]
    assert "text" in data[0]

def test_get_no_comments_by_user_id(client, users):

    user: User = users[2]
    token = user_token(user)
    header = ["Authorization", f"Bearer {token}"]
    params = [("user_id", user.id), ("offset", "0"), ("limit", "10")]

    responce = client.get(
        f"/api/comments/users/", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_comments_by_user_id_photo_id(client, users, photos):

    user: User = users[0]
    token = user_token(user)
    photo = photos[0]
    header = ["Authorization", f"Bearer {token}"]
    params = [("photo_id", photo.id), ("offset", "0"), ("limit", "10")]

    responce = client.get(
        f"/api/comments/users/{user.id}", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "user_id" in data[0]
    assert data[0]["user_id"] == user.id
    assert "photo_id" in data[0]
    assert data[0]["photo_id"] == str(photo.id)
    assert "text" in data[0]

def test_get_no_comments_by_user_id_photo_id(client, users, photos):

    user: User = users[0]
    token = user_token(user)
    photo = photos[1]
    header = ["Authorization", f"Bearer {token}"]
    params = [("photo_id", photo.id), ("offset", "0"), ("limit", "10")]

    responce = client.get(
        f"/api/comments/users/{user.id}", params=params, headers=[header,])

    assert responce.status_code == 200, responce.text
    data = responce.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_delete_own_comment_user0(client, users, session):
    user: User = users[0]
    author: User = user
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    header = ["Authorization", f"Bearer {token}"]

    responce = client.delete(
        f"api/comments/record/{comment_record.id}", headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden


def test_delete_other_comment_user0(client, users, session):
    user: User = users[0]
    author: User = users[1]
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    header = ["Authorization", f"Bearer {token}"]

    responce = client.delete(
        f"api/comments/record/{comment_record.id}", headers=[header,])

    assert responce.status_code == 403, responce.text
    data = responce.json()
    assert data["detail"] == RETURN_MSG.operation_forbiden

def test_delete_comment_moderator(client, moderator, users, session):
    user: User = moderator
    author: User = users[0]
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    header = ["Authorization", f"Bearer {token}"]

    responce = client.delete(
        f"api/comments/record/{comment_record.id}", headers=[header,])

    assert responce.status_code == 204, responce.text

def test_delete_comment_admin(client, admin, users, session):
    user: User = admin
    author: User = users[1]
    token = user_token(user)
    comment_record = session.query(
        Comment).filter_by(user_id=author.id).first()
    header = ["Authorization", f"Bearer {token}"]

    responce = client.delete(
        f"api/comments/record/{comment_record.id}", headers=[header,])

    assert responce.status_code == 204, responce.text
