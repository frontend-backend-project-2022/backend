from flask import Blueprint, request, make_response, send_from_directory
import docker
import json
import tarfile
from io import BytesIO
import os
import uuid
import shutil
import re

docker_bp = Blueprint("docker", __name__)

TEMPFILES_DIR = 'tempfiles'

# This file contains docker-related part.


# use blueprint as app
@docker_bp.route("/")
def docker_index():
    client = docker.from_env()
    containers = client.containers
    return "Docker Index"

# create (if not exists) / connect (if exists) a container
@docker_bp.route("/connect/", methods=['GET'])
def docker_connect(name=None, language=None, version=None):
    client = docker.from_env()
    containers = client.containers

    try: #existing
        container = containers.get(name)
        container.start()
    except:
        img = 'ubuntu'
        print(img,language,version)
        if language and version:
            if language == 'Python':
                if version in ['Python 3.8', 'Python 3.9', 'Python 3.10']:
                    s, f = re.search('3.\d+', version).span()
                    img = "web-ide/python:%s"%version[s:f]
            elif language == 'C/C++':
                if version in ['gcc 8.3','clang 14']:
                    if version[0]=='g':
                        img = "web-ide/gcc:8.3"
                    else:
                        img = 'web-ide/clang:14'
            elif language == 'node':
                if version in ['node 16.17','node 18.7']:
                    s, f = re.search('1\d.\d+', version).span()
                    img = "web-ide/node:%s"%version[s:f]
        print(img)
        container = containers.run(img, name=name,tty=True, detach=True,command="bash", working_dir='/workspace', cap_add=["SYS_PTRACE",],security_opt=["seccomp=unconfined",])
        container.kill()
    return container.id

# stop a container
def docker_close(id):
    client = docker.from_env()
    containers = client.containers
    try: #existing
        container = containers.get(id)
        container.kill()
        return True
    except docker.errors.NotFound as e:
        print("docker close error:",e)
    except docker.errors.APIError as e:
        print("docker close error:",e)
    return False

# stop a container from front-end
@docker_bp.post("/closeContainer/<containerid>/")
def docker_close_container(containerid):
    if not docker_close(containerid):
        print('Error: close container failed.')
    return 'success'

# stop & rm a container
def docker_rm(id):
    client = docker.from_env()
    containers = client.containers
    try: #existing
        container = containers.get(id)
        container.kill()
        container.remove()
        return True
    except docker.errors.NotFound as e:
        print("docker rm error:",e)
    except docker.errors.APIError as e:
        print("docker rm error:",e)
    return False

# receive and execute bash command from front-end 
@docker_bp.route("/bash/", methods=['POST'])
def docker_bash():
    data = json.loads(request.data)
    name = data['containerid']
    cmd = data['cmd']
    print(name, cmd)
    res = docker_exec_bash(name, cmd)
    print(res)
    if res is not None:
        return res, 200
    return "failed", 500

# execute bash command in a container 
def docker_exec_bash(name, cmd):
    client = docker.from_env()
    containers = client.containers
    socket = None
    try: #existing
        container = containers.get(name)
        container.start()
        cmd = '/bin/sh -c "%s"'%cmd
        res = container.exec_run(cmd=cmd, stream=False, demux=False)
        print(res)
        if res.exit_code == 0:
            return res.output.decode()
        else:
            print("exec bash error")
            return None
    except Exception as e:
        print("exec bash error:",e)
        return None


# recursively print directorys in a container and emit to front-end
@docker_bp.route("/getdir/<containerid>", methods=['GET'])
def docker_getdir(containerid):
    try:
        res = docker_exec_bash(containerid, 'ls -RF')
        dir_list = res.split('\n\n')
        dic_temp = {}
        dic=[]
        for item in dir_list:
            dir_part, content_part = item.strip().split(':')
            content_list = content_part.strip().split('\n')
            dic_temp[dir_part] = content_list
        for dir_part, content_part in dic_temp.items():
            for content in content_part:
                if len(content) > 1 and content[-1] != '/':
                    content_ = content if content[-1] not in ['*','|','='] else content[:-1]
                    dic.append((dir_part, content_))
                    dic.append((dir_part+'/'+content_,"/"))
                else:
                    dic.append((dir_part, content[:-1]))

        dic.sort(key=lambda elem : elem[0].count('/'), reverse= True)
        dic2 = dict()
        for directory, content in dic:
            if content == '':
                dic2[directory] = {}
            elif content == '/':
                dic2[directory] = ''
            else:
                dic2[directory] = dic2.get(directory, dict())
                dic2[directory][content] = dic2[directory + '/' + content]
        return json.dumps(dic2['.']), 200
    except Exception as e:
        print(repr(e) + "during docker_getdir()")
        return "failed", 500

# receive file from front-end and add into a container
@docker_bp.route("/uploadFile/", methods=['POST'])
def docker_upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        return 'No file part', 400
    try:
        file = request.files['file']
        form = request.form.to_dict()
        container_dir = form['dir']
        container_id = form['containerid']
        filedir = TEMPFILES_DIR + '/' + str(uuid.uuid4())
        os.makedirs(filedir + '/' + os.path.dirname(file.filename))
        file.save(filedir + '/' + file.filename)
        with tarfile.open(filedir + '/' + file.filename+'.tar', 'w') as tar:
            try:
                tar.add(filedir + '/' + file.filename, arcname=container_dir + '/' + file.filename)
            finally:
                tar.close()

        client = docker.from_env()
        container = client.containers.get(container_id)
        with open(filedir + '/' + file.filename+'.tar', 'rb') as fd:
            ok = container.put_archive(path="/workspace", data=fd)
            if not ok:
                raise Exception('Put file failed')
            else:
                print("no exception")
                shutil.rmtree(filedir)
        return "success", 201
    except KeyError as e:
        print(repr(e))
        return repr(e), 400
    except Exception as e:
        print(str(e))
        return str(e), 500


# receive file contents from front-end and modify in a container
@docker_bp.route("/uploadContent/", methods=['POST'])
def docker_upload_content():

    try:

        data = json.loads(request.data)
        print(data)
        filename = data['filename']
        container_dir = data['dir']
        container_id = data['containerid']
        content = data['content']
        filedir = TEMPFILES_DIR + '/' + str(uuid.uuid4())
        os.makedirs(filedir)

        with open(filedir + '/' + filename, 'w') as f:
            f.write(content)

        with tarfile.open(filedir + '/' + filename+'.tar', 'w') as tar:
            try:
                tar.add(filedir + '/' + filename, arcname=container_dir + '/' + filename)
            finally:
                tar.close()

        client = docker.from_env()
        container = client.containers.get(container_id)
        with open(filedir + '/' + filename+'.tar', 'rb') as fd:
            ok = container.put_archive(path="/workspace", data=fd)
            if not ok:
                raise Exception('Put file failed')
            else:
                print("no exception")
                shutil.rmtree(filedir)
        return "success", 201
    except Exception as e:
        return str(e), 500


# receive folder from front-end and add into a container
@docker_bp.route("/uploadFolder/", methods=['POST'])
def docker_upload_folder():
    # check if the post request has the file part
    if 'file' not in request.files:
        return 'No file part', 400
    try:
        form = request.form.to_dict()
        container_dir = form['dir']
        container_id = form['containerid']
        client = docker.from_env()
        container = client.containers.get(container_id)

        filedir = TEMPFILES_DIR + '/' + str(uuid.uuid4())

        files = request.files.getlist("file")

        for file in files:
            filedir_ = filedir + '/' + os.path.dirname(file.filename)
            if os.path.exists(filedir_) is False:
                os.path.makedirs(filedir_)
            file.save(filedir + '/' + file.filename)

            with tarfile.open(filedir + '/' + file.filename+'.tar', 'w') as tar:
                try:
                    tar.add(filedir_ + '/' + file.filename, arcname=container_dir + '/' + file.filename)
                finally:
                    tar.close()

            with open(filedir + '/' + file.filename+'.tar', 'rb') as fd:
                ok = container.put_archive(path="/workspace", data=fd)
                if not ok:
                    raise Exception('Put file failed')
                else:
                    print("no exception")
        shutil.rmtree(filedir)
        return "success", 201
    except KeyError as e:
        print(repr(e))
        return repr(e), 400
    except Exception as e:
        print(str(e))
        return str(e), 500

# get file content from a container and sent to front-end
@docker_bp.route("/downloadContent/", methods=['GET', 'POST'])
def docker_download_content():
    try:
        data = json.loads(request.data)
        id = data['containerid']
        dir = data['dir']
        filename = data['filename']
        client = docker.from_env()
        containers = client.containers
        container = containers.get(id)
        strm, stat = container.get_archive(path='/workspace' + '/' + dir + '/' + filename)
        file_obj = BytesIO()
        for i in strm:
            file_obj.write(i)
        file_obj.seek(0)
        tar = tarfile.open(mode='r', fileobj=file_obj)
        text = tar.extractfile(os.path.basename(filename))
        tar.close()
        q = text.read()
        return q, 200
    except KeyError as e:
        print(repr(e))
        return repr(e), 400
    except Exception as e:
        print(str(e))
        return str(e), 500


# get file from a container and sent to front-end
@docker_bp.route("/downloadFile/", methods=['GET'])
def docker_download_file():
    try:
        data = request.args
        id = data['containerid']
        dir = data['dir']
        filename = data['filename']
        client = docker.from_env()
        containers = client.containers
        container = containers.get(id)
        strm, stat = container.get_archive(path='/workspace' + '/' + dir + '/' + filename)
        file_obj = BytesIO()
        for i in strm:
            file_obj.write(i)
        file_obj.seek(0)
        tar = tarfile.open(mode='r', fileobj=file_obj)
        text = tar.extractfile(os.path.basename(filename))
        q = text.read()
        tar.close()

        filedir = TEMPFILES_DIR + '/' + str(uuid.uuid4())
        os.makedirs(filedir)

        with open(filedir +'/' + filename,"wb") as f:
                f.write(q)

        response = make_response(send_from_directory(filedir, filename, as_attachment=True))
        shutil.rmtree(filedir)
        return response
    except KeyError as e:
        print(repr(e))
        return repr(e), 400


# get the project as a .tar file from a container and sent to front-end
@docker_bp.route("/downloadFolder/", methods=['GET'])
def docker_download_folder():
    try:
        data = request.args
        id = data['containerid']
        dir = data['dir']
        client = docker.from_env()
        containers = client.containers
        container = containers.get(id)
        strm, stat = container.get_archive(path='/workspace')
        filedir = TEMPFILES_DIR + '/' + str(uuid.uuid4())
        os.makedirs(filedir)
        project_name = id
        return_name = filedir + '/' + project_name
        with open(return_name + '.tar',"wb") as f:
            for i in strm:
                f.write(i)
        response = make_response(send_from_directory(filedir, project_name + '.tar', as_attachment=True))
        shutil.rmtree(filedir)
        return response
    except KeyError as e:
        print(repr(e))
        return repr(e), 400

# create folder in a container
@docker_bp.route("/createFolder/", methods=['POST'])
def docker_create_folder():
    data = json.loads(request.data)
    id = data['containerid']
    dir = data['dir']
    if docker_exec_bash(id, "cd %s && mkdir %s"%(os.path.dirname(dir), os.path.basename(dir))) is not None:
        return "success", 201
    return "failed", 500

# delete folder in a container
@docker_bp.route("/deleteFolder/", methods=['DELETE'])
def docker_delete_folder():
    data = json.loads(request.data)
    id = data['containerid']
    dir = data['dir']
    if docker_exec_bash(id, "rm -rf %s"%dir) is not None:
        return "success", 200
    return "failed", 500

# create a file in a container
@docker_bp.route("/createFile/", methods=['POST'])
def docker_create_file():
    data = json.loads(request.data)
    id = data['containerid']
    dir = data['dir']
    filename = data['filename']
    if docker_exec_bash(id, "cd %s && touch %s"%(dir, filename)) is not None:
        return "success", 201
    return "failed", 500

# delete a file in a container
@docker_bp.route("/deleteFile/", methods=['DELETE'])
def docker_delete_file():
    data = json.loads(request.data)
    id = data['containerid']
    dir = data['dir']
    filename = data['filename']
    if docker_exec_bash(id, "cd %s && rm -f %s"%(dir,filename)) is not None:
        return "success", 200
    return "failed", 500

# rename a file in a container
@docker_bp.route("/renameFile/", methods=['POST'])
def docker_rename_file():
    data = json.loads(request.data)
    id = data['containerid']
    dir = data['dir']
    filename = data['filename']
    newname = data['newname']
    if docker_exec_bash(id, f"cd {dir} && mv {filename} {newname}") is not None:
        return "success", 200
    return "failed", 500

# get python package list from a container
@docker_bp.route("/getPipList/<containerid>")
def docker_get_pip_list(containerid):
    try:
        id = containerid
        res = docker_exec_bash(id, "pip list")
        pip_list = res.split('\n')
        pip_list = pip_list[2:-1]
        pip_dic = {}
        for item in pip_list:
            item_list = item.split(' ')
            while '' in item_list:
                item_list.remove('')
            if item_list[0] == 'WARNING:':
                break
            pip_dic[item_list[0]] = item_list[1]
        return json.dumps(pip_dic), 200
    except Exception as e:
        print(str(e))
        return str(e), 500

# pip python package into a container
@docker_bp.route("/addPythonPackage/", methods=['POST'])
def docker_add_python_package():
    try:
        data = json.loads(request.data)
        id = data['containerid']
        package = data['package']
        version = data['version']
        if version:
            if docker_exec_bash(id, f'pip install {package}=={version}') is not None:
                return 'success', 201
        else:
            if docker_exec_bash(id, f'pip install {package}') is not None:
                return 'success', 201
    except Exception as e:
        print(e)
        return str(e), 500

# delete python package into a container
@docker_bp.route("/deletePythonPackage/", methods=['DELETE'])
def docker_delete_python_package():
    try:
        data = json.loads(request.data)
        id = data['containerid']
        package = data['package']
        if docker_exec_bash(id, f'pip uninstall -y {package}') is not None:
            return 'success', 200
    except Exception as e:
        print(e)
        return str(e), 500

# get node.js package list from a container
@docker_bp.route("/getNodejsList/<containerid>")
def docker_get_nodejs_list(containerid):
    try:
        id = containerid
        res = docker_exec_bash(id, "npm list --depth=0")
        nodejs_list = res.split('\n')
        nodejs_list = nodejs_list[1:-2]
        nodejs_dic = {}
        for item in nodejs_list:
            print(item)
            item = item[4:]
            print(item)
            if item == '(empty)':
                continue
            item_list = item.split('@')
            print(item_list)
            nodejs_dic[item_list[0]] = item_list[1]
        return json.dumps(nodejs_dic), 200
    except Exception as e:
        print(str(e))
        return str(e), 500

# yarn isntall node.js package into a container
@docker_bp.route("/addNodejsPackage/", methods=['POST'])
def docker_add_nodejs_package():
    try:
        data = json.loads(request.data)
        id = data['containerid']
        package = data['package']
        version = data['version']
        if version:
            if docker_exec_bash(id, f'yarn add {package}@{version}') is not None:
                return 'success', 201
        else:
            if docker_exec_bash(id, f'yarn add {package}') is not None:
                return 'success', 201
    except Exception as e:
        print(e)
        return str(e), 500

# delete node.js package in a container
@docker_bp.route("/deleteNodejsPackage/", methods=['DELETE'])
def docker_delete_nodejs_package():
    try:
        data = json.loads(request.data)
        id = data['containerid']
        package = data['package']
        if docker_exec_bash(id, f'yarn remove {package}') is not None:
            return 'success', 200
    except Exception as e:
        print(e)
        return str(e), 500

