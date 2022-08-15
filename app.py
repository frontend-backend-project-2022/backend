from flask import Flask
from flask_cors import CORS
from views.dockers import *
from views.database import *
from views.login import login_bp

app = Flask(__name__, template_folder="templates")
app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(login_bp, url_prefix="/login")

app.config["SECRET_KEY"] = "secret!qwq"
# CSRFProtect(app)
CORS(app, supports_credentials=True)

# python language server: websocket
from views.pyls import sock
sock.init_app(app)

# xterm.js
from views.xterm import socketio
socketio.init_app(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

db_init()

    # tar = tarfile.open(mode='r', fileobj=file_obj)
    # text = tar.extractfile(os.path.basename(filename))
    # tar.close()
    # q = text.read()
    # return q

# id = docker_connect()
# docker_exec_bash(id, "mkdir dir1 && mkdir dir2 && touch file2 && cd dir1 && touch file1 && mkdir dir3")
# downfile(id)

if __name__ == "__main__":
    app.run(debug=True)
