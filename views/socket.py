from flask import Blueprint


socket_bp = Blueprint("Socket", __name__)


# use blueprint as app
@socket_bp.route("/")
def docker_index():
    return "Socket Index"
