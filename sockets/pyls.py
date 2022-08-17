from pyls_jsonrpc import streams
import subprocess
import threading
import json
from sockets import socketio
from flask import request
import os, signal

sid2data = {}

@socketio.on("connect", namespace="/pyls")
def init_pyls():
    print('pyls connect')
    sid2data[request.sid] = {}
    sid2data[request.sid]['language_server'] = subprocess.Popen(
        ["pyls"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    sid2data[request.sid]['reader'] = streams.JsonRpcStreamReader(sid2data[request.sid]['language_server'].stdout)
    sid2data[request.sid]['writer'] = streams.JsonRpcStreamWriter(sid2data[request.sid]['language_server'].stdin)
    def consume(reader, sid):
        reader.listen(lambda msg: socketio.emit("send", json.dumps(msg), to=sid, namespace="/pyls"))
    consume_thread = threading.Thread(target=consume, args=(sid2data[request.sid]['reader'], request.sid))
    consume_thread.daemon = True
    consume_thread.start()
    print('pyls connect finished.')


@socketio.on("receive", namespace="/pyls")
def receive_message(msg):
    while request.sid not in sid2data:
        pass
    sid2data[request.sid]['writer'].write(json.loads(msg))


@socketio.on("disconnect", namespace="/pyls")
def disconnect_pyls():
    pyls_resource = sid2data.pop(request.sid)
    pyls_resource['language_server'].terminate()


@socketio.on_error('/pyls')
def error_handler(e):
    print('Error:', e)
