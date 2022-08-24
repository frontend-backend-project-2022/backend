# xterm.js <=> socketio
from sockets import socketio
from views.dockers import docker_connect, docker_exec_bash, docker_close
import pty
import select
import os
import subprocess
import time
from flask import request

# This contains WEB-terminal related part.

class xtermData():
    # start a terminal by subprocess
    def __init__(self, containerid):
        container_id = docker_connect(containerid)
        self.container_id = container_id
        self.pty, tty = pty.openpty()
        self.terminal = subprocess.Popen(
            ["docker", "exec", "-it", container_id, "/bin/bash"], stdin=tty, stdout=tty, stderr=tty
        )

socket_poll = dict()

# get stdout/stderr from tty and sent to front-end
def send_worker(sid):
    terminal = socket_poll[sid].terminal
    pty = socket_poll[sid].pty
    while terminal.poll() is None:
        r, _, _ = select.select([pty], [], [], 0.2)
        if pty in r:
            output_from_docker = os.read(pty, 1024)
            socketio.emit("response", output_from_docker.decode(),to=sid, namespace="/xterm")
    socketio.emit('end', to=sid, namespace="/xterm")

# start a terminal and establish connections
@socketio.on("start", namespace="/xterm")
def init_terminal(containerid):
    socket_poll[request.sid] = xtermData(containerid)
    socketio.start_background_task(send_worker,request.sid)

# listen to message from front-end and sent to tty for handling
@socketio.on("message", namespace="/xterm")
def handle_message(data):
    os.write(socket_poll[request.sid].pty, data.encode())

# disconnect and tear
@socketio.on("disconnect", namespace="/xterm")
def tear_terminal():
    print('xterm disconnect')
    if request.sid not in socket_poll.keys():
        return
    containerid = socket_poll[request.sid].container_id
    del socket_poll[request.sid]
