import docker
import pexpect
import re
import os
import json
from flask import request, jsonify
import threading
from sockets import socketio

class pdbData():
    def __init__(self, containerid, filepath, pdbsocket, runsocket, host, post):
        self.bp = [] #
        self.containerid = containerid
        self.filepath = filepath
        self.pdbsocket = pdbsocket
        self.runsocket = runsocket
        self.lineno = 2 #
        self.state = 1 #
        self.host = host
        self.post = post

    def response(self, messageType="none", message = ""):
        # 返回的bp里-1代表已删除
        bp_ = map(lambda x: x - 1, [{i for i in self.bp} - {-1}])
        dic = {'bp':bp_, 'lineno':self.lineno - 1,'state':self.state, 'messageType':messageType, 'message':message}
        return jsonify(dic)

pdb_poll = dict()

def pdb_stdout(runsocket):
    while True:
        index = runsocket.expect(['\n', pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            print(runsocket.before)
            socketio.emit('stdout', runsocket.before.decode('utf-8'))
        elif index == 1:
            break
            
@socketio.on("connect", namespace="/debugger")
def pdb_connect(container_id, filepath):
    try:
        client = docker.from_env()
        containers = client.containers
        container = containers.get(container_id)
        _, sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
        pdbsocket = pexpect.fdpexpect.fdspawn(sock.fileno(),timeout=1)

        _, sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
        runsocket = pexpect.fdpexpect.fdspawn(sock.fileno(),timeout=1)

        runsocket.expect("#")
        pdbsocket.expect("#")

        runsocket.sendline("sed '1i from remote_pdb import set_trace;set_trace();' %s > .run"%filepath )
        runsocket.expect("#")

        runsocket.sendline('python .run')
        index = runsocket.expect(['waiting for connection ...',])
        
        if index == 0:
            res = runsocket.before.decode('utf-8')
            s,f = re.search('\d+\.\d+\.\d+\.\d+:\d+',res).span()
            host, post = res[s:f].split(":")
            print('telnet %s %s'%(host, post))
            pdbsocket.sendline('telnet %s %s'%(host, post))
            index = pdbsocket.expect(['(Pdb)',pexpect.TIMEOUT])
            if index:
                raise Exception('timeout')
            index = runsocket.expect(["RemotePdb accepted connection \S+.",pexpect.TIMEOUT])
            if index:
                raise Exception('timeout')

            thread = threading.Thread(target = pdb_stdout, args=(runsocket,))
            thread.start()
            print("successfully connected")
            pdb = pdbData(container_id, filepath, pdbsocket, runsocket, host, post)
            pdb_poll[request.sid] = pdb
            
    except Exception as e:
        print("error", e)


@socketio.on("add", namespace="/debugger")
def pdb_add_breakpoint(lineno):
    lineno += 1
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        socketio.emit("error", "Unstarted")
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("b %d"%lineno)
    index = pdbsocket.expect(["Breakpoint \d+ at .*:%d"%lineno,"End of file","\*\*\*"])
    if index == 0:
        print("successfully added line %d"%lineno)
        pdb.bp.append(lineno)
        socketio.emit("response", pdb.response(),to=request.sid, namespace="/debugger")
    else:
        print("error %d:%s"%(index, pdbsocket.after.decode('utf-8')))

@socketio.on("delete", namespace="/debugger")
def pdb_delete_breakpoint(lineno):
    lineno += 1
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pos = [i + 1 for i in range(len(pdb.bp)) if pdb.bp[i] == lineno]
    for i in pos:
        print(i)
        pdbsocket.sendline("cl %d"%i)
        index = pdbsocket.expect(["Deleted breakpoint \d+ at .*:\d+","End of file","\*\*\*"])

        if index == 0:
            print("successfully deleted bp %d"%i)
            pdb.bp[i - 1] = -1
        else:
            print("error %d:%s"%(index, pdbsocket.after.decode('utf-8')))
    socketio.emit("response", pdb.response(),to=request.sid, namespace="/debugger")

@socketio.on("skip", namespace="/debugger")
def pdb_next_breakpoint():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("c")
    while True:
        index = pdbsocket.expect(["> .*\(\d+\)<module>()", pexpect.TIMEOUT])
        if not index:
            break

    res = pdbsocket.after.decode('utf-8')
    s, f = re.search('\(\d+\)<', res).span()
    print("lineno:", res[s + 1 : f - 2]) #lineno
    pdb.lineno = int(res[s + 1 : f - 2])

    socketio.emit("response", pdb.response(),to=request.sid, namespace="/debugger")


@socketio.on("next", namespace="/debugger")
def pdb_next_line():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("n")
    while True:
        index = pdbsocket.expect(["> .*\(\d+\)<module>()", pexpect.TIMEOUT])
        if not index:
            break
            
    res = pdbsocket.after.decode('utf-8')
    s, f = re.search('\(\d+\)<', res).span()
    print("lineno:", res[s + 1 : f - 2]) #lineno
    pdb.lineno = int(res[s + 1 : f - 2])

    socketio.emit("response", pdb.response(),to=request.sid, namespace="/debugger")



@socketio.on("check", namespace="/debugger")
def pdb_getvalue(variables):
    variables = json.loads(variables)
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    variables_list = []
    for i in variables:
        pdbsocket.sendline("p %s"%i)
        pdbsocket.expect(["p %s\r\n"%i])
        index = pdbsocket.expect(["\r\n\(Pdb\)"])
        if index == 0:
            res = pdbsocket.before.decode('utf-8')
            value = "\n".join(res.split('\r\n'))
        print(value)

        pdbsocket.sendline("p type(%s)"%i)
        index = pdbsocket.expect(["<class .*>"])
        if index == 0:
            res = pdbsocket.after.decode('utf-8')
            typeof = res

        if typeof == "<class 'int'>":
            value = int(value)
        elif typeof == "<class 'float'>":
            value = int(value)

        variables_list.append({'name':i,'value':value,'type':typeof})
    socketio.emit("response", pdb.response(messageType="variables",message=variables_list),to=request.sid, namespace="/debugger")

@socketio.on("check", namespace="/debugger")
def pdb_stdin(message):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    runsocket = pdb.runsocket
    runsocket.send(message)

@socketio.on("check", namespace="/debugger")
def pdb_stdout(message):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    runsocket = pdb.runsocket
    runsocket.send(message)

@socketio.on("exit", namespace="/debugger")
def pdb_exit():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("exit")
    index1 = pdbsocket.expect(["exit"])
    runsocket = pdb.runsocket
    runsocket.sendline("exit")
    index2 = runsocket.expect(["exit"])
    if index1 == 0 and index2 == 0:
        pdb.lineno = 0
        pdb.state = 0
        socketio.emit("response", pdb.response(),to=request.sid, namespace="/debugger")
        del pdb_poll[request.sid]

@socketio.on("disconnect", namespace="/debugger")
def pdb_disconnect():
    pdb_exit()

# pdb_connect('258588', r'/workspace/test/test2.py')