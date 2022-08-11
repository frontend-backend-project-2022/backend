from .database import db_insertuser, db_verify_pw, db_deleteuser, db_selectUserByName
from flask import Blueprint, session, request, redirect, url_for, render_template, abort
from functools import wraps


login_bp = Blueprint("login", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            abort(401)  # 401 Unauthorized
        return view_func(*args, **kwargs)
    return wrapper

@login_bp.route('/', methods=["POST"])
def login():
    body_data = request.json
    if db_verify_pw(body_data["username"], body_data["password"]):
        session['username'] = body_data['username']
        return 'success', 200
    return 'failed', 401

@login_bp.get('/is_logged_in/')
@login_required
def check_logged_in():
    return session["username"], 200


@login_bp.get('/logout/')
def logout():
    session.pop('username', None)
    return 'success', 200


@login_bp.route('/register/', methods=['POST', 'DELETE'])
def register():
    body_json = request.json
    if request.method == 'POST':
        if db_selectUserByName(body_json["username"]):
            return 'duplicate username', 400
        if not db_insertuser(body_json["username"], body_json["password"]):
            return 'failed to register', 500
        else:
            return 'suceess', 201
    else:
        if not db_verify_pw(body_json["username"], body_json["password"]):
            return 'password wrong', 401
        if not db_deleteuser(body_json["username"], body_json["password"]):
            return 'failed to deregister', 500
        else:
            return 'suceess', 200
