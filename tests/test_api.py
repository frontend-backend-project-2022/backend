from flask import session
from views.dockers import *
from io import BytesIO
import os
import tarfile

# This file is pytest-related part, run "pytest" in terminal and automatically start a test

def test_index(client):
    response = client.get("/")
    assert b"<p>Hello, World!</p>" in response.data
    response = client.get("/docker/")
    assert b"Docker" in response.data

# test login-related part
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
        client.get('/login/logout/')
        client.delete('/login/register/', json=user_data)
        client.post('/login/', json=user_data)
        response = client.get('/login/is_logged_in/')
        assert user_data['username'] not in response.data.decode()
        response = client.delete('/login/register/', json=user_data)
        assert '401' in str(response)


# test docker-bash-related part
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
        response = client.delete('/database/deleteProject/'+ containerid)


# test project-related part
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
        print(project_list)
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


# test file-related part
def test_file(client, auth):
    project_data = {
        "projectname": "PROJECT",
        "language": "Python",
        "version": "Python 3.9",
    }
    tempfile = BytesIO(b"post-data")
    tempfile.name = 'folder/123.txt'
    put_data = {
        'file':tempfile,
        'dir':'hsu1023',
    }
    get_data = {
        'dir':'hsu1023',
        'filename' : 'folder/123.txt',
    }
    upload_content = {
        'filename':'test.py',
        'dir':'hsu1023/new',
        'content':'print("hello world")',
    }
    downloadFolder_data = {
        'dir':'hsu1023',
    }
    downloadFile_data = {
        'dir':'hsu1023/new',
        'filename':'test.py',
    }
    createFolder_data = {
        'dir':'hsu1023/newFolder',
    }
    createFile_data = {
        'dir':'hsu1023/newFolder',
        'filename':'test.py'
    }
    renameFile_data = {
        'dir':'hsu1023/new',
        'filename':'test.py',
        'newname':'test2.py',
    }
    with client:
        auth.login()
        client.post('/login/init/')
        containerid = client.post('/database/createProject/', json = project_data).data.decode()
        put_data['containerid'] = get_data['containerid'] = downloadFolder_data['containerid'] = downloadFile_data['containerid'] = upload_content['containerid'] = renameFile_data['containerid'] = createFile_data['containerid'] = createFolder_data['containerid'] = containerid

        response = client.post('/docker/uploadFile/', data=put_data,
                      content_type='multipart/form-data')
        assert '201' in str(response)

        response = client.get('/docker/getdir/%s' % containerid)
        print(response.data.decode())
        assert '{"hsu1023": {"folder": {"123.txt": ""}}, "main.py": ""}' == response.data.decode()

        response = client.get('/docker/downloadFolder/', query_string = downloadFolder_data)
        with open("download.tar", mode='w') as f:
            f.write(response.get_data(as_text=True))
        assert tarfile.is_tarfile("download.tar")
        os.remove('download.tar')

        response = client.post('/docker/uploadContent/', json = upload_content)
        # print(docker_exec_bash(containerid, 'ls -RF'))
        assert '201' in str(response)


        response = client.get('/docker/downloadFile/', query_string  = downloadFile_data)
        # print(response.text, type(response.text))
        with open('test.py', mode='w') as f:
            f.write(response.get_data(as_text=True))
        with open('test.py', mode="r") as f:
            q = f.read()
        assert q == 'print("hello world")'
        os.remove('test.py')

        r = client.get('/docker/downloadContent/', json=get_data).data.decode()
        assert "post-data" == r
        
        response = client.post('/docker/createFolder/', json=createFolder_data)
        assert '201' in str(response)
        response = client.post('/docker/createFile/', json=createFile_data)
        assert '201' in str(response)
        response = client.delete('/docker/deleteFile/', json=createFile_data)
        assert '200' in str(response)
        response = client.delete('/docker/deleteFolder/', json=createFolder_data)
        assert '200' in str(response)

        response = client.post('/docker/renameFile/', json=renameFile_data)
        assert '200' in str(response)

        client.delete('/database/deleteProject/'+ containerid)###

# test dependency-related part
def test_dependencies_manage(client, auth):
    python_project_data = {
        "projectname": "PROJECT",
        "language": "Python",
        "version": "Python 3.9",
    }
    nodejs_project_data = {
        "projectname": "PROJECT2",
        "language": "node",
        "version": "node 16.17",
    }
    getPipList_data = {}
    addPythonPackage_data_1 = {
        'package': 'wtforms',
        'version': '3.0.0',
    }
    addPythonPackage_data_2 = {
        'package': 'wtforms',
        'version': '',
    }
    addNodejsPackage_data = {
        'package': 'typescript',
        'version': '',
    }
    with client:
        auth.login()
        client.post('/login/init/')
        containerid = client.post('/database/createProject/', json=python_project_data).data.decode()
        getPipList_data['containerid'] = addPythonPackage_data_1['containerid'] = addPythonPackage_data_2['containerid'] = containerid

        response = client.get('/docker/getPipList/%s'%containerid)
        assert '200' in str(response)

        response = client.post('/docker/addPythonPackage/', json=addPythonPackage_data_2)
        assert '201' in str(response)
        response = client.delete('/docker/deletePythonPackage/', json=addPythonPackage_data_2)
        assert '200' in str(response)

        client.delete('/database/deleteProject/'+ containerid)

        containerid = client.post('/database/createProject/', json=nodejs_project_data).data.decode()
        addNodejsPackage_data['containerid'] = containerid

        response = client.get('/docker/getNodejsList/%s'%containerid)
        assert '200' in str(response)
        response = client.post('/docker/addNodejsPackage/', json=addNodejsPackage_data)
        assert '201' in str(response)
        response = client.get('/docker/getNodejsList/%s'%containerid)
        assert '200' in str(response)
        response = client.delete('/docker/deleteNodejsPackage/', json=addNodejsPackage_data)
        assert '200' in str(response)

        client.delete('/database/deleteProject/'+ containerid)
