from .database import db_insertuser, db_verify_pw, db_deleteuser
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
        return 'success'
    return 'failed'

@login_bp.get('/is_logged_in/')
@login_required
def check_logged_in():
    return f'User {session["username"]} logged in.'


@login_bp.get('/logout/')
def logout():
    session.pop('username', None)
    return 'success'


@login_bp.route('/register/', methods=['POST', 'DELETE'])
def register():
    body_json = request.json
    if request.method == 'POST':
        db_insertuser(body_json["username"], body_json["password"])
    else:
        if not db_deleteuser(body_json["username"], body_json["password"]):
            abort(500)
    return 'suceess'
