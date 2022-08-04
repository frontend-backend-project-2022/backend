import pytest

def test_index(client):
    response = client.get("/")
    assert b"<p>Hello, World!</p>" in response.data
