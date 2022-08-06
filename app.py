from flask import Flask
from flask_wtf import CSRFProtect
from views.docker import docker_bp, docker_connect, docker_getdir
from views.database import database_bp, db_init, db_insertuser, db_selectuser, db_verify_pw, db_insertcontainer, db_deleteuser
from views.login import login_bp



app = Flask(__name__, template_folder="templates")
app.register_blueprint(docker_bp, url_prefix="/docker")
app.register_blueprint(database_bp, url_prefix="/database")
app.register_blueprint(login_bp, url_prefix="/login")

app.config["SECRET_KEY"] = "secret!qwq"
CSRFProtect(app)

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
# _ = docker_connect('Alice')
# print(docker_getdir('Alice'))
# db_insertuser('Alice','123456')
# db_insertcontainer('Alice')
# print(db_verify_pw('Alice', '123456'), db_verify_pw('Dave', '123456'), db_verify_pw('Alice', '12346'))
# db_deleteuser('Alice','123')
# # db_insertcontainer('Alice')
# db_deleteuser('Alice','123456')
# assert db_selectuser('Alice') == None
# db_insertcontainer('Alice')

if __name__ == "__main__":
    app.run(debug=True)
