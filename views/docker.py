from flask import Blueprint


docker_bp = Blueprint("docker", __name__)


# use blueprint as app
@docker_bp.route("/")
def docker_index():
    return "Docker Index"
