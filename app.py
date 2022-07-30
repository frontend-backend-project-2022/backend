from flask import Flask
from views.docker import docker_bp, docker_connect
from views.database import database_bp
from views.login import login_bp
from flask_socketio import SocketIO


app = Flask(__name__)
app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(login_bp, url_prefix="/login")

app.config["SECRET_KEY"] = "secret!qwq"
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


# xterm.js socket
import pty
import select
import os
import subprocess


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

if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True)
