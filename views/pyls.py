from pyls_jsonrpc import streams
import subprocess
import threading
import json
from views.xterm import socketio
from flask import request

sid2data = {}

@socketio.on("python.connect")
def init_pyls():
    # on connected:
    language_server = subprocess.Popen(
        ["pyls", "-v"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    print('Python connect')

    writer = streams.JsonRpcStreamWriter(language_server.stdin)
    reader = streams.JsonRpcStreamReader(language_server.stdout)

    def consume(reader, sid):
        reader.listen(lambda msg: socketio.emit("python.send", json.dumps(msg), to=sid))
    consume_thread = threading.Thread(target=consume, args=(reader, request.sid))
    consume_thread.daemon = True
    consume_thread.start()

    sid2data[request.sid] = {
        'language_server': language_server,
        'reader': reader,
        'writer': writer
    }

@socketio.on("python.receive")
def receive_message(msg):
    print(msg)
    sid2data[request.sid]['writer'].write(json.loads(msg))

@socketio.on("python.disconnect")
def disconnect_pyls():
    pyls_resource = sid2data[request.sid]
    pyls_resource['language_server'].terminate()
    pyls_resource['reader'].close()
    pyls_resource['writer'].close()
