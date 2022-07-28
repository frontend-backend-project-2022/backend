from flask import Flask
from views.docker import docker_bp
from views.socket import socket_bp
from views.database import database_bp
from views.login import login_bp


app = Flask(__name__)
app.register_blueprint(docker_bp, url_prefix='/docker')
app.register_blueprint(socket_bp, url_prefix='/socket')
app.register_blueprint(database_bp, url_prefix='/database')
app.register_blueprint(login_bp, url_prefix='/login')


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
