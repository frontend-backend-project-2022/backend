from flask import Flask
from flask_cors import CORS
from views.dockers import *
from views.database import *
from views.login import login_bp

app = Flask(__name__)
app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(login_bp, url_prefix="/login")

app.config["SECRET_KEY"] = "secret!qwq"
# CSRFProtect(app)
CORS(app, supports_credentials=True)

# python language server: websocket
# from views.pyls import sock
# sock.init_app(app)
import views.pyls

# xterm.js
from views.xterm import socketio
socketio.init_app(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

db_init()

if __name__ == "__main__":
    app.run(debug=True)
