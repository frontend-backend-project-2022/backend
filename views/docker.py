from flask import Blueprint
import docker
from docker import errors

docker_bp = Blueprint("docker", __name__)
client = docker.from_env()
containers = client.containers

# use blueprint as app
@docker_bp.route("/")
def docker_index():
    return "Docker Index"

def docker_connect(name):
    try: #existing
        container = containers.get(name)
        container.start()
        
    except errors.NotFound as e:
        container = containers.run("ubuntu",name=name,tty=True, detach=True,command="/bin/bash")
        _, socket = container.exec_run('sh', stdin=True, socket=True)
        socket._sock.sendall(b'mkdir /workspace')
    return container.id

# exec_bash
def docker_exec_bash(name, bash_str):
    try: #existing
        container = containers.get(name)
        container.start()
        _, socket = container.exec_run('sh', stdin=True, socket=True)
    except errors.NotFound as e:
        pass
    sock = socket._sock
    sock.sendall(bytes(bash_str)+b'\n')

    unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
    try:
        unknown_byte=socket._sock.recv(docker.constants.STREAM_HEADER_SIZE_BYTES)
        print(unknown_byte)
        buffer_size = 4096 # 4 KiB
        data = b''
        while True:
            part = socket._sock.recv(buffer_size)
            data += part
            if len(part) < buffer_size:
            # either 0 or end of data
                break
        print(data.decode("utf8"))
        return data.decode("utf8")
    except Exception: 
        pass

# recursively print directorys
def docker_getdir(name):
    docker_exec_bash(name, 'cd /workspace\nls -R\n')