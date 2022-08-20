# xterm.js <=> socketio
from sockets import socketio
from views.dockers import docker_connect, docker_exec_bash, docker_close
import pty
import select
import os
import subprocess
import time
from flask import request

class runnerData():
    def __init__(self, containerid, fileurl):
        container_id = docker_connect(containerid, fileurl)
        self.container_id = container_id
        self.pty, tty = pty.openpty()
        self.terminal = subprocess.Popen(
            ["docker", "exec", "-it", container_id, "python", fileurl], stdin=tty, stdout=tty, stderr=tty
        )

socket_poll = dict()

def send_worker(sid):
    terminal = socket_poll[sid].terminal
    pty = socket_poll[sid].pty
    while terminal.poll() is None:
        r, _, _ = select.select([pty], [], [], 0.1)
        if pty in r:
            output_from_docker = os.read(pty, 1024)
            socketio.emit("response", output_from_docker.decode(), to=sid, namespace="/runner")
    socketio.emit('end', to=sid, namespace="/runner")


@socketio.on("start", namespace="/runner")
def init_terminal(containerid, fileurl):
    socket_poll[request.sid] = runnerData(containerid, fileurl)
    socketio.start_background_task(send_worker,request.sid)

@socketio.on("message", namespace="/runner")
def handle_message(data):
    os.write(socket_poll[request.sid].pty, data.encode())

@socketio.on("disconnect", namespace="/runner")
def tear_terminal():
    if request.sid not in socket_poll.keys():
        return
    del socket_poll[request.sid]
