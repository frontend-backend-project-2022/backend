from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

# Form validation and models

PASSWORD_VALIDATORS = [DataRequired(message='密码未填'), Length(8, 64, message='密码长度太长或太短')]
PASSWORD_CONFIRM_VALIDATORS = [DataRequired(message='密码未填'), Length(8, 64, message='密码长度太长或太短'),
                               EqualTo('password', message="密码不匹配")]
USERNAME_VALIDATORS = [DataRequired(message='用户名未填'), Length(4, 64, message='用户名长度太长或太短')]


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=USERNAME_VALIDATORS)
    password = PasswordField('password', validators=PASSWORD_VALIDATORS)
    password_confirm = PasswordField('password_confirm', validators=PASSWORD_CONFIRM_VALIDATORS)
    submit = SubmitField('register')


class DeRegistrationForm(FlaskForm):
    username = StringField('username', validators=USERNAME_VALIDATORS)
    password = PasswordField('password', validators=PASSWORD_VALIDATORS)
    submit = SubmitField('deregister')


class LoginForm(FlaskForm):
    # Login Validation in security.py
    username = StringField('username', validators=[DataRequired(message='用户名不能为空')])
    password = PasswordField('Password', validators=PASSWORD_VALIDATORS)
    submit = SubmitField('Log in')

