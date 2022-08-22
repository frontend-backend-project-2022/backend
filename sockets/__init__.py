from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

from . import language_server, xterm, runner, gdb, pdb