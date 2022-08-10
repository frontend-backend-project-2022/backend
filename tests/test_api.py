import pytest
from flask import session
from views.docker import docker_rm
from io import BytesIO, StringIO
import os
import zipfile
import shutil


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
        client.post('/login/init/')
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
        client.post('/login/init/')
        response = client.post('/database/createProject/', json = project_data)
        assert response.data
        containerid = response.data.decode()

        response = client.get('/docker/getdir/%s' % containerid)
        bash_post['containerid'] = containerid
        client.post('/docker/bash/', json = bash_post)

        response = client.get('/docker/getdir/%s' % containerid)
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
        client.post('/login/init/')
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


def test_file(client, auth):
    project_data = {
        "projectname": "PROJECT",
        "language": "python",
        "version": "10",
    }
    tempfile = BytesIO(b"post-data")
    tempfile.name = 'folder/123.txt'
    put_data = {
        'file':tempfile,
        'dir':'hsu1023',
    }
    get_data = {
        'dir':'./hsu1023',
        'filename' : 'folder/123.txt',
    }
    with client:
        auth.login()
        client.post('/login/init/')
        containerid = client.post('/database/createProject/', json = project_data).data.decode()
        put_data['containerid'] = get_data['containerid'] = containerid
        print(containerid)
        
        response = client.post('/docker/uploadFile/', data=put_data,
                      content_type='multipart/form-data')
        assert '200' in str(response)

        response = client.get('/docker/getdir/%s' % containerid)
        print(response.data.decode())
        assert '{"hsu1023": {"folder": {"123.txt": ""}}}' == response.data.decode()

        client.delete('/database/deleteProject/'+ containerid)
        
        r = client.get('/docker/downloadContent/', json=get_data).data.decode()
        assert "post-data" == r

# def test_folder(client, auth):
#     project_data = {
#         "projectname": "PROJECT",
#         "language": "python",
#         "version": "10",
#     }
#     put_data = {
#         'dir':'hsu1023',
#     }
#     with client:
#         auth.login()
#         client.post('/login/init/')
#         if os.path.exists('test-folder') is False:
#             os.makedirs('test-folder')
#         with open('test-folder/test.txt', "w") as fd:
#             fd.write('DATA')

#         # f = zipfile.ZipFile('archive.zip','w',zipfile.ZIP_DEFLATED)
#         # startdir = "test-folder"
#         # for dirpath, dirnames, filenames in os.walk(startdir):
#         #     for filename in filenames:
#         #         f.write(os.path.join(dirpath,filename))
#         # f.close()
#         # f = open('archive.zip','rb')
#         # put_data['file'] = f

#         containerid = client.post('/database/createProject/', json = project_data).data.decode()
#         put_data['containerid']  = containerid
        

#         response = client.post('/docker/uploadFolder/', data=put_data,content_type='multipart/form-data')

#         assert '200' in str(response)

#         client.delete('/database/deleteProject/'+ containerid)
        
#         response = client.get('/docker/getdir/%s' % containerid)
#         print(response.data.decode())
#         assert '{"hsu1023": {"123.txt": ""}}' == response.data.decode()

#         shutil.rmtree('test-folder')
#         os.remove('archive.zip')
#         f.close()