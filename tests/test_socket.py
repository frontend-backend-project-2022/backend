import pytest
from flask import session
import unittest
from flask import Flask, session, request, json as flask_json
from flask_socketio import SocketIO, send, emit, Namespace, disconnect

def test_index(client):
    pass
    # with client:
    #     client.emit('connect','258588','/workspace/test/test2.py',namespace='debugger')