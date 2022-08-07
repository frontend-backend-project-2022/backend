import pytest
from flask import session


def test_index(client):
    response = client.get("/")
    assert b"<p>Hello, World!</p>" in response.data

def test_login(client):
    user_data = {
        "username": "j31234",
        "password": "123456"
    }
    with client:
        client.post('/login/register/', json=user_data)
        client.post('/login/', json=user_data)
        assert "username" in session
        response = client.get('/login/is_logged_in/')
        assert f"User {user_data['username']} logged in." in response.data.decode()
