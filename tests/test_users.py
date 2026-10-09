def test_me_without_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_with_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401


def test_me_with_valid_token(client, moderator_headers):
    response = client.get("/users/me", headers=moderator_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "mod1"
