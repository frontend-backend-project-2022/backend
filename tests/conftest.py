import sys
from pathlib import Path
sys.path.append('.')

import pytest
from app import app as flask_app
class AuthActions(object):

    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        # with self._client.session_transaction() as session:
        #     session['username'] = 'test'
        self._client.post(
            '/login/register/',
            json={'username': username, 'password': password}
        )
        return self._client.post(
            '/login/',
            json={'username': username, 'password': password}
        )
    def logout(self):
        return self._client.get('/login/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)
# 通过 auth 固件，可以在调试中调用 auth.login() 登录为 test 用户。这个用户的数据已经在 app 固件中写入了数据。


@pytest.fixture()
def app():
    flask_app.config.update({
        "TESTING": True,
    })
    return flask_app

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
