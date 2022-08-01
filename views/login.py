from flask import Blueprint


login_bp = Blueprint("login", __name__)


# use blueprint as app
@login_bp.route("/")
def login_index():
    return "Login Index"
