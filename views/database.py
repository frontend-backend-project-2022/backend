from flask import Blueprint


database_bp = Blueprint("database", __name__)


# use blueprint as app
@database_bp.route("/")
def database_index():
    return "Database Index"
