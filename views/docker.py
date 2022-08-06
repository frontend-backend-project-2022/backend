from flask import Blueprint
import docker
from docker import errors
import json

docker_bp = Blueprint("docker", __name__)


# use blueprint as app
@docker_bp.route("/")
def docker_index():
    return "Docker Index"

@docker_bp.route("/connect", methods=['GET'])
def docker_connect(name=None):
    client = docker.from_env()
    containers = client.containers
    try: #existing
        container = containers.get(name)
    except:
        container = containers.run("ubuntu",name=name,tty=True, detach=True,command="/bin/bash", working_dir='/workspace')
    return container.id

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


# exec_bash

@docker_bp.route("/bash")
def docker_exec_bash(name, bash_str):
    client = docker.from_env()
    containers = client.containers
    try: #existing
        container = containers.get(name)
        container.start()
        _, socket = container.exec_run('/bin/bash', stdin=True, socket=True)
    except errors.NotFound as e:
        pass
    sock = socket._sock
    sock.settimeout(1)
    sock.sendall(bytes(bash_str+'\n',encoding='utf8'))
    # unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
    try:
        unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
        buffer_size = 4096 # 4 KiB
        data = b''
        while True:
            part = socket._sock.recv(buffer_size)
            data += part
            if len(part) < buffer_size:
            # either 0 or end of data
                break
        # print(data.decode("utf8"))
        return data.decode("utf8")
    except Exception: 
        pass

# recursively print directorys
@docker_bp.route("/getdir")
def docker_getdir(name):
    res = docker_exec_bash(name, 'ls -RF\n')
    dir_list = res.split('\n\n')
    dic_temp = {}
    dic=[]
    for item in dir_list:
        dir_part, content_part = item.strip().split(':')
        content_list = content_part.strip().split('\n')
        dic_temp[dir_part] = content_list
    for dir_part, content_part in dic_temp.items():
        for content in content_part:
            if content[-1] != '/':
                dic.append((dir_part, content))
                dic.append((dir_part+'/'+content,""))
            else:
                dic.append((dir_part, content[:-1]))
    
    dic.sort(key=lambda elem : elem[0].count('/'), reverse= True)
    dic2 = dict()
    for directory, content in dic:
        if content == '':
            dic2[directory] = ''
        else:
            dic2[directory] = dic2.get(directory, dict())
            dic2[directory][content] = dic2[directory + '/' + content]
    return json.dumps(dic2['.'])