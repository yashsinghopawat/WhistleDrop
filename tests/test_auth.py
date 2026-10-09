from app.core.config import settings


def register(client, **changes):
    data = {
        "username": "mod1",
        "email": "mod1@example.com",
        "password": "strongpass123",
        "invite_code": settings.moderator_invite_code,
    }
    data.update(changes)
    return client.post("/auth/register", json=data)


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "mod1"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_wrong_invite_code(client):
    response = register(client, invite_code="wrong")
    assert response.status_code == 403


def test_register_duplicate_username(client):
    register(client)
    response = register(client, email="other@example.com")
    assert response.status_code == 409


def test_register_duplicate_email(client):
    register(client)
    response = register(client, username="mod2")
    assert response.status_code == 409


def test_register_short_password(client):
    response = register(client, password="123")
    assert response.status_code == 422


def test_register_invalid_email(client):
    response = register(client, email="not-an-email")
    assert response.status_code == 422


def test_login_success(client):
    register(client)
    response = client.post("/auth/login", json={"username": "mod1", "password": "strongpass123"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register(client)
    response = client.post("/auth/login", json={"username": "mod1", "password": "wrongpass123"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever123"})
    assert response.status_code == 401
