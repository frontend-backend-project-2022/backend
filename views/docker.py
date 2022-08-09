from flask import Blueprint, jsonify, request
import docker
from docker import errors
import json

import tarfile
import time
from io import BytesIO, StringIO
import os

docker_bp = Blueprint("docker", __name__)


# use blueprint as app
@docker_bp.route("/")
def docker_index():
    client = docker.from_env()
    containers = client.containers
    return "Docker Index"

@docker_bp.route("/connect/", methods=['GET'])
def docker_connect(name=None):
    client = docker.from_env()
    containers = client.containers
    try: #existing
        container = containers.get(name)
    except:
        container = containers.run("ubuntu",name=name,tty=True, detach=True,command="bash", working_dir='/workspace')
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
@docker_bp.route("/bash/", methods=['POST'])
def docker_bash():
    data = json.loads(request.data)
    name = data['containerid']
    cmd = data['cmd']
    print(name, cmd)
    res = docker_exec_bash(name, cmd)
    print(res)
    if res is not None:
        return res,200
    return "failed", 500

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
    #     _, socket = container.exec_run('/bin/sh', stdin=True, socket=True)
    # except errors.NotFound as e:
    #     print(e)
    #     return None
    # sock = socket._sock
    # if timeout > 0:
    #     sock.settimeout(timeout)
    # sock.sendall(bytes(cmd+'\n',encoding='utf8'))
    # # unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
    # data = b''
    # try:
    #     unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
    #     buffer_size = 4096 # 4 KiB
    #     while True:
    #         part = socket._sock.recv(buffer_size)
    #         data += part
    #         if len(part) < buffer_size:
    #         # either 0 or end of data
    #             break
    #     return data.decode("utf8")
    # except Exception as e: 
    #     print(e)
    #     return None
    

# recursively print directorys
@docker_bp.route("/getdir/<containerid>", methods=['GET'])
def docker_getdir(containerid):
    res = docker_exec_bash(containerid, 'ls -RF')
    # print(res)
    dir_list = res.split('\n\n')
    dic_temp = {}
    dic=[]
    # print(dir_list)
    for item in dir_list:
        dir_part, content_part = item.strip().split(':')
        content_list = content_part.strip().split('\n')
        dic_temp[dir_part] = content_list
    # print(dic_temp)
    for dir_part, content_part in dic_temp.items():
        for content in content_part:
            if len(content) > 1 and content[-1] != '/':
                dic.append((dir_part, content))
                dic.append((dir_part+'/'+content,"/"))
            else:
                dic.append((dir_part, content[:-1]))
    
    dic.sort(key=lambda elem : elem[0].count('/'), reverse= True)
    # print(dic)
    dic2 = dict()
    for directory, content in dic:
        if content == '':
            dic2[directory] = {}
        elif content == '/':
            dic2[directory] = ''
        else:
            dic2[directory] = dic2.get(directory, dict())
            dic2[directory][content] = dic2[directory + '/' + content]
    # print(dic2['.'])
    return json.dumps(dic2['.']), 200

def put_test():
    client = docker.from_env()
    containers = client.containers
    container = containers.run("ubuntu",tty=True, detach=True,command="/bin/bash", working_dir='/workspace')
    print(container)
    with tarfile.open("vpc-example.tar", 'w') as tar:
        try:
                tar.add('test.txt')
        finally:
                tar.close()
    with open('vpc-example.tar', 'rb') as fd:
            ok = container.put_archive(path="/workspace", data=fd)
            if not ok:
                raise Exception('Put file failed')
            else:
                print("no exception")
                os.remove('vpc-example.tar')
    return container.id

def get_test(id):
    client = docker.from_env()
    containers = client.containers
    container = containers.get(id)
    strm, stat = container.get_archive('/workspace/test.txt')
    file_obj = BytesIO()
    for i in strm:
        file_obj.write(i)
    file_obj.seek(0)
    tar = tarfile.open(mode='r', fileobj=file_obj)
    text = tar.extractfile('test.txt')
    q = text.read()
    print(q)