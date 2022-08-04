import sys
from pathlib import Path
sys.path.append('.')

import pytest
from app import app as flask_app

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
