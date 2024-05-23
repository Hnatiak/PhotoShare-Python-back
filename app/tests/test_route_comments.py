from unittest.mock import MagicMock

from src.entity.models import User, Photo, Role, Comment
from main import app
from src.services.auth import auth_service


def test_create_comment(client, monkeypatch, session):
    user: User = session.query(User).filter_by(role=Role.user).first()
    mock_get_current_user = MagicMock()
    mock_get_current_user.get_current_user().return_value = user
    monkeypatch.setattr("src.routes.comments.auth_service",
                mock_get_current_user)
    
    app.dependency_overrides[auth_service] = mock_get_current_user
    photo: Photo = session.query(Photo).first()
    comment = {"comment": "user comment"}
    responce = client.post(f"api/comments/{photo.id}", json=comment, headers={"Authorization": f"Bearer "})
    print(responce.__dict__)

    assert responce.status_code == 201, responce.text