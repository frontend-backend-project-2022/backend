from .database import db_insertuser, db_verify_pw, db_deleteuser
from flask import Blueprint, session, Flask, request, redirect, url_for, render_template
from flask_wtf import CSRFProtect
from .form import RegistrationForm, DeRegistrationForm, LoginForm


login_bp = Blueprint("login", __name__)


@login_bp.route('/is_login')
def is_login():
    if 'username' in session:
        return f'{session["username"]}'
    else:
        return False


@login_bp.route('/')
def index():
    if is_login():
        return render_template('index.html')
    return redirect(url_for('login.login'))

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('login.index'))
    if request.method == 'POST':
        form = LoginForm()
        if not form.validate_on_submit():
            return render_template('login.html', form=form)
        if db_verify_pw(form.username.data, form.password.data):
            session['username'] = request.form['username']
            return redirect(url_for('login.index'))
    return render_template('login.html')


@login_bp.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login.index'))


@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if not form.validate_on_submit():
        return render_template('register.html')

    db_insertuser(form.username.data, form.password.data)
    return redirect(url_for('login.login'))


@login_bp.route('/deregister', methods=['GET', 'POST'])
def deregister():
    form = DeRegistrationForm()
    if form.validate_on_submit():
        if db_deleteuser(form.username.data, form.password.data):
            return redirect(url_for('login.login'))
    return render_template('deregister.html')
