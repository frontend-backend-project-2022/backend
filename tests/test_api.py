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
        assert user_data['username'] in response.data.decode()

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
        print(response.data.decode())
        assert '{"dir1": {"dir3": {}, "file1": ""}, "dir2": {}, "file2": ""}' == response.data.decode()
        docker_rm(containerid)

def test_project(client, auth):
    host = '/database/'
    project_data = {
        "projectname": "PROJECT",
        "language": "python",
        "version": "10",
    }
    project_data2 = {
        "projectname": "PROJECT2",
        "language": "C++",
        "version": "17",
    }
    update_data = {
        "newname" : "NewProject",
    }
    with client:
        auth.login()
        containerid = client.post(host + 'createProject/', json = project_data).data.decode()
        containerid2 = client.post(host + 'createProject/', json = project_data2).data.decode()
        assert containerid
        assert containerid2
        project_list = client.get(host + 'getAllProjects/').json
        assert len(project_list) == 2

        update_data['containerid'] = project_list[1]['containerid']
        client.post(host + 'updateProject/', json = update_data)
        project_list = client.get(host + 'getAllProjects/').json
        assert project_list[1]['projectname'] == 'NewProject'

        project = client.get(host + 'getProject/'+project_list[1]['containerid']).json
        assert project['version'] == '17'

        response = client.delete(host + 'deleteProject/'+ project_list[1]['containerid'])
        project_list = client.get(host + 'getAllProjects/').json
        assert len(project_list) == 1
        assert project_list[0]['language'] == 'python'
        client.delete(host + 'deleteProject/'+ project_list[0]['containerid'])
