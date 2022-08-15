# xterm.js <=> socketio
from flask_socketio import SocketIO
from views.dockers import docker_connect,docker_exec_bash
import pty
import select
import os
import subprocess
import time


socketio = SocketIO(cors_allowed_origins="*")

def send_worker():
    while socketio.terminal.poll() is None:
        r, _, _ = select.select([socketio.pty], [], [])
        if socketio.pty in r:
            output_from_docker = os.read(socketio.pty, 1024)
            socketio.emit("response", output_from_docker.decode())


@socketio.on("connectSignal")
def init_terminal(name):
    container_id = docker_connect(name)
    socketio.pty, tty = pty.openpty()
    socketio.terminal = subprocess.Popen(
        ["docker", "exec", "-it", container_id, "/bin/bash"], stdin=tty, stdout=tty, stderr=tty
    )
    socketio.start_background_task(send_worker)

@socketio.on("message")
def handle_message(data):
    os.write(socketio.pty, data.encode())