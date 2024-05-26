from unittest.mock import MagicMock
from time import sleep
import asyncio

from src.entity.models import User
from src.services.auth import auth_service
from src.exceptions.exceptions import RETURN_MSG

test_access_token = None
test_refresh_token = None


def test_create_user(client, new_user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    
    responce = client.post("api/auth/signup", json=new_user)

    assert responce.status_code == 201, responce.text
    data = responce.json()
    assert data['user']['email'] == new_user.get('email')
    assert 'id' in data['user']
    mock_send_email.assert_called_once()

def test_repeat_create_user(client, new_user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = client.post("/api/auth/signup",json=new_user,)
    
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.user_exists
    mock_send_email.assert_not_called()

def test_request_email_not_confirmed(client, new_user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    body = {'email': new_user.get('email')}

    response = client.post(f"/api/auth/request_email", json=body)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == RETURN_MSG.emaii_check_confirmation
    mock_send_email.assert_called_once()

def test_login_user_not_confirmed(client, new_user):
    data = {"username": new_user.get(
        'email'), "password": new_user.get('password')}

    response = client.post("/api/auth/login", data=data)
    
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.email_not_confirmed

def test_confirmation_link(client, new_user):
    token = auth_service.create_email_token({"sub": new_user.get('email')})

    response = client.get(f"/api/auth/confirmed_email/{token}")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == RETURN_MSG.email_confirmed

def test_repeat_confirmation_link(client, new_user):
    token = auth_service.create_email_token({"sub": new_user.get('email')})

    response = client.get(f"/api/auth/confirmed_email/{token}")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == RETURN_MSG.email_already_confirmed

def test_confirmation_wrong_link(client):
    token = auth_service.create_email_token({"sub": "not_exist_user@mail.com"})

    response = client.get(f"/api/auth/confirmed_email/{token}")

    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.verification_error

def test_request_email_confirmed(client, new_user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    body = {'email': new_user.get('email')}

    response = client.post(f"/api/auth/request_email", json=body)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == RETURN_MSG.email_already_confirmed
    mock_send_email.assert_not_called()

def test_request_email_wrong(client, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    body = {'email': "not_exist_user@mail.com"}

    response = client.post(f"/api/auth/request_email", json=body)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == RETURN_MSG.email_invalid
    mock_send_email.assert_not_called()

def test_login_user_confirmed(client, new_user):
    global test_access_token
    global test_refresh_token

    data = {"username": new_user.get('email'), "password": new_user.get('password')}
    
    response = client.post("/api/auth/login", data=data)
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    test_access_token = data["access_token"]
    assert "refresh_token" in data
    test_refresh_token = data["refresh_token"]
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, new_user):
    data = {"username": new_user.get('email'), "password": 'password'}

    response = client.post("/api/auth/login", data=data)
    
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.password_invalid

def test_login_wrong_email(client, new_user):
    data = {"username": 'email', "password": new_user.get('password')}

    response = client.post("/api/auth/login", data=data)
    
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.email_invalid

def test_login_user_banned(client, session):
    user: User = session.query(User).filter_by(isbanned=True).first()
    
    data = {"username": user.email, "password": "doesnt_matter"}

    response = client.post("/api/auth/login", data=data)

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.user_banned

def test_refresh_token_user_not_exist(client):
    token = asyncio.run(auth_service.create_refresh_token({"sub": "wrong@mail.com"}))
    header = ["Authorization", f"Bearer {token}"]

    response = client.get("/api/auth/refresh_token", headers=[header,])

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.verification_error

def test_refresh_token_correct(client):
    # Should be executed after test_login_user_confirmed and before test_refresh_token_wrong
    global test_access_token
    global test_refresh_token
    token = test_refresh_token
    header = ["Authorization", f"Bearer {token}"]

    response = client.get("/api/auth/refresh_token", headers=[header,])

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    test_access_token = data["access_token"]
    assert "refresh_token" in data
    test_refresh_token = data["refresh_token"]
    assert data["token_type"] == "bearer"

def test_refresh_token_wrong(client, new_user):
    sleep(1)
    data = {"username": 'email', "password": new_user.get('password')}
    token = asyncio.run(auth_service.create_refresh_token({"sub": new_user.get('email')}))
    header = ["Authorization", f"Bearer {token}"]

    response = client.get("/api/auth/refresh_token", headers=[header,])

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.token_refresh_invalid

def test_logout_correct(client, monkeypatch):
    mock_dell_from_bleck_lis = MagicMock()
    monkeypatch.setattr(
        "src.routes.auth.repository_users.dell_from_bleck_list", mock_dell_from_bleck_lis)
    token = test_access_token
    header = ["Authorization", f"Bearer {token}"]

    response = client.post("/api/auth/logout", headers=[header,])

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["logout"] == RETURN_MSG.user_logout

def test_logout_wrong_token(client):
    token = "wrong_token"
    header = ["Authorization", f"Bearer {token}"]

    response = client.post("/api/auth/logout", headers=[header,])

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == RETURN_MSG.credentials_error
