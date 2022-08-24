# xterm.js <=> socketio
from sockets import socketio
from views.dockers import docker_connect, docker_exec_bash, docker_close
import pty
import select
import os
import subprocess
import time
from flask import request
from views.database import db_getProjectInfo

# This contains project-running related part.

# Support for Python, C/C++, Node.js currently.

class runnerData():
    def __init__(self, containerid, start_cmd):
        container_id = docker_connect(containerid)
        self.container_id = container_id
        self.pty, tty = pty.openpty()
        print(f"docker exec -it {containerid} {start_cmd}")
        self.terminal = subprocess.Popen(
            f"docker exec -it {containerid} {start_cmd}", stdin=tty, stdout=tty, stderr=tty, shell=True
        )

socket_poll = dict()

# get stdout/stderr from tty and sent to front-end
def send_worker(sid):
    terminal = socket_poll[sid].terminal
    pty = socket_poll[sid].pty
    while terminal.poll() is None:
        r, _, _ = select.select([pty], [], [], 0.1)
        if pty in r:
            output_from_docker = os.read(pty, 1024)
            socketio.emit("response", output_from_docker.decode(), to=sid, namespace="/runner")
    socketio.emit('end', to=sid, namespace="/runner")

# start and run a project
@socketio.on("start", namespace="/runner")
def init_terminal(containerid, language, fileurl):
    file_without_suffix = '.'.join(fileurl.split('.')[:-1])
    start_cmd_dict = {
        "Python": f"python {fileurl}",
        "C/C++": f"/bin/bash -c \"g++ {fileurl} -o {file_without_suffix} && {file_without_suffix}\"" if 'gcc' in db_getProjectInfo(containerid)['version'] else f"/bin/bash -c \"clang++ {fileurl} -o {file_without_suffix} && {file_without_suffix}\"",
        'node': f"node {fileurl}"
    }

    socket_poll[request.sid] = runnerData(containerid, start_cmd_dict[language])
    socketio.start_background_task(send_worker,request.sid)

# listen to message from front-end and sent to tty for handling
@socketio.on("message", namespace="/runner")
def handle_message(data):
    os.write(socket_poll[request.sid].pty, data.encode())

# disconnect and tear
@socketio.on("disconnect", namespace="/runner")
def tear_terminal():
    if request.sid not in socket_poll.keys():
        return
    del socket_poll[request.sid]
