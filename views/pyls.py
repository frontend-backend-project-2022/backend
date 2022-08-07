from flask_sock import Sock
from pyls_jsonrpc import streams
import subprocess
import threading
import json

sock = Sock()


@sock.route("/python")
def echo(ws):
    # on connected:
    language_server = subprocess.Popen(
        ["pyls", "-v"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    writer = streams.JsonRpcStreamWriter(language_server.stdin)

    def consume():
        reader = streams.JsonRpcStreamReader(language_server.stdout)
        reader.listen(lambda msg: ws.send(json.dumps(msg)))
    thread = threading.Thread(target=consume)
    thread.daemon = True
    thread.start()

    while True:
        msg = ws.receive()
        writer.write(json.loads(msg))
