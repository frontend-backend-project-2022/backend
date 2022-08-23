from flask import Flask
from flask_cors import CORS
from views.dockers import *
from views.database import *
from views.login import login_bp
import os

from sockets import socketio

app = Flask(__name__)
app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(login_bp, url_prefix="/login")

app.config["SECRET_KEY"] = "secret!qwq"
CORS(app, supports_credentials=True)

socketio.init_app(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

db_init()
os.system("python images/setup.sh")


if __name__ == "__main__":
    app.run(debug=True)