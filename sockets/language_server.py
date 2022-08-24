from pyls_jsonrpc import streams
import subprocess
import threading
import json
from sockets import socketio
from flask import request

# This contains language-serve-related part, based on LSP

def install_lsp(language, run_lsp_command):
    namespace = f'/{language}'
    sid2data = {}

    @socketio.on("connect", namespace=namespace)
    def init_lsp():
        print('lsp connect')
        sid2data[request.sid] = {}
        sid2data[request.sid]['language_server'] = subprocess.Popen(
            run_lsp_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        sid2data[request.sid]['reader'] = streams.JsonRpcStreamReader(
            sid2data[request.sid]['language_server'].stdout)
        sid2data[request.sid]['writer'] = streams.JsonRpcStreamWriter(
            sid2data[request.sid]['language_server'].stdin)

        def consume(reader, sid):
            reader.listen(lambda msg: socketio.emit(
                "send", json.dumps(msg), to=sid, namespace=namespace))
        consume_thread = threading.Thread(target=consume, args=(
            sid2data[request.sid]['reader'], request.sid))
        consume_thread.daemon = True
        consume_thread.start()

    @socketio.on("receive", namespace=namespace)
    def receive_lsp(msg):
        while request.sid not in sid2data:
            pass
        sid2data[request.sid]['writer'].write(json.loads(msg))

    @socketio.on("disconnect", namespace=namespace)
    def disconnect_lsp():
        pyls_resource = sid2data.pop(request.sid)
        pyls_resource['language_server'].terminate()

    @socketio.on_error(namespace)
    def error_handler(e):
        print('Error:', e)


install_lsp('python', 'pyls')
install_lsp('cpp', 'clangd')
