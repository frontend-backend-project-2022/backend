# xterm.js <=> socketio
from flask_socketio import SocketIO
from views.dockers import docker_connect,docker_exec_bash
import pty
import select
import os
import subprocess
import time
from flask import request

class xtermData():
    def __init__(self, containerid):
        container_id = docker_connect(containerid)
        self.pty, tty = pty.openpty()
        self.terminal = subprocess.Popen(
            ["docker", "exec", "-it", container_id, "/bin/bash"], stdin=tty, stdout=tty, stderr=tty
        )

socket_poll = dict()

socketio = SocketIO(cors_allowed_origins="*")

def send_worker(sid):
    terminal = socket_poll[sid].terminal
    pty = socket_poll[sid].pty
    while terminal.poll() is None:
        r, _, _ = select.select([pty], [], [])
        if pty in r:
            output_from_docker = os.read(pty, 1024)
            socketio.emit("response", output_from_docker.decode(),to=sid)

@socketio.on("connectSignal")
def init_terminal(containerid):
    socket_poll[request.sid] = xtermData(containerid)
    socketio.start_background_task(send_worker,request.sid)

@socketio.on("message")
def handle_message(data):
    os.write(socket_poll[request.sid].pty, data.encode())

@socketio.on("disconnectSignal")
def tear_terminal(containerid):
    del socket_poll[request.sid]