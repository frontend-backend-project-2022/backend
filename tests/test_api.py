import pytest
from flask import session
from views.docker import docker_rm


def test_index(client):
    response = client.get("/")
    assert b"<p>Hello, World!</p>" in response.data
    response = client.get("/docker/")
    assert b"Docker" in response.data

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

def test_bash(client, auth):
    project_data = {
        "projectname": "PROJECT",
        "language": "python",
        "version": "10",
    }
    bash_post = {
        "cmd": "mkdir dir1 && mkdir dir2 && touch file2 && cd dir1 && touch file1 && mkdir dir3"
    }
    with client:
        auth.login()
        response = client.post('/database/createProject/', json = project_data)
        assert response.data
        containerid = response.data.decode()

        response = client.get('/docker/getdir/%s' % containerid)
        bash_post['containerid'] = containerid
        client.post('/docker/bash/', json = bash_post)

        response = client.get('/docker/getdir/%s' % containerid)
        assert '{"dir1": {"dir3": "", "file1": ""}, "dir2": "", "file2": ""}' == response.data.decode()
        docker_rm(containerid)