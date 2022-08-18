# xterm.js <=> socketio
from sockets import socketio
from views.dockers import docker_connect, docker_exec_bash, docker_close
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



def send_worker(sid):
    terminal = socket_poll[sid].terminal
    pty = socket_poll[sid].pty
    while terminal.poll() is None:
        r, _, _ = select.select([pty], [], [])
        if pty in r:
            output_from_docker = os.read(pty, 1024)
            socketio.emit("response", output_from_docker.decode(),to=sid, namespace="/xterm")

@socketio.on("start", namespace="/xterm")
def init_terminal(containerid):
    socket_poll[request.sid] = xtermData(containerid)
    socketio.start_background_task(send_worker,request.sid)

@socketio.on("message", namespace="/xterm")
def handle_message(data):
    os.write(socket_poll[request.sid].pty, data.encode())

@socketio.on("disconnect", namespace="/xterm")
def tear_terminal(containerid):
    docker_close(containerid)
    del socket_poll[request.sid]