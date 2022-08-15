import docker
import pexpect.fdpexpect
import re
import os
from flask import request, jsonify
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

class pdbData():
    def __init__(self, containerid, filepath, psocket):
        self.bp = [] #
        self.containerid = containerid
        self.filepath = filepath
        self.psocket = psocket
        self.lineno = 1 #
        self.state = 1 #
    def response(self,message = ""):
        # 返回的bp里-1代表已删除
        dic = {'bp':self.bp, 'lineno':self.lineno,'state':self.state, 'message':message}
        return jsonify(dic)

pdb_poll = dict()

@socketio.on("connectSignal")
def pdb_connect(container_id, filepath):
    try:
        client = docker.from_env()
        containers = client.containers
        container = containers.get(container_id)
        _, sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
        psocket = pexpect.fdpexpect.fdspawn(sock.fileno(),timeout=10)

        psocket.expect("#")
        psocket.sendline("python -m pdb %s"%filepath)
        index = psocket.expect(["> \S*\(1\)<module>\(\)", "Error"])
        if index == 0:
            print("successfully connected")
        elif index == 1:
            return 500
        psocket.expect("(Pdb)")
        pdb = pdbData(container_id, filepath, psocket)
        pdb_poll[response.sid] = pdb
        socketio.emit("message",pdb.response(),to=response.sid)
    except:
        socketio.emit("error","",to=response.sid)

@socketio.on("add")
def pdb_add_breakpoint(lineno):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    psocket.sendline("b %d"%lineno)
    index = psocket.expect(["Breakpoint \d+ at .*:%d"%lineno,"End of file","\*\*\*"])
    if index == 0:
        print("successfully added line %d"%lineno)
        pdb.bp.append(lineno)
        socketio.emit("response", pdb.response(),to=response.sid)
    else:
        print("error %d:%s"%(index, psocket.after.decode('utf-8')))
        
            
@socketio.on("delete")
def pdb_delete_breakpoint(linenos):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    pos = [i + 1 for i in range(len(pdb.bp)) if pdb.bp[i] in linenos]
    for i in pos:
        print(i)
        psocket.sendline("cl %d"%i)
        index = psocket.expect(["Deleted breakpoint \d+ at .*:\d+","End of file","\*\*\*"])

        if index == 0:
            print("successfully deleted bp %d"%i)
            pdb.bp[i - 1] = -1
        else:
            print("error %d:%s"%(index, psocket.after.decode('utf-8')))
    socketio.emit("response", pdb.response(),to=response.sid)

@socketio.on("skip")
def pdb_next_breakpoint():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    psocket.sendline("c")
    index = psocket.expect(["> .*\(\d+\)<module>()"])
    if index == 0:
        res = psocket.after.decode('utf-8')
        '''
        > xxx (templine content)
        (Pdb) n
        xxx (stdout/stderr)
        > /test/test2.py(xxx)<module>
        '''
        console = res.split('\r\n')[2:-1]
        print(console) #stdout/stderr

        s, f = re.search('\(\d+\)<', res).span()
        print(res[s + 1 : f - 2]) #lineno
        pdb.lineno = int(res[s + 1 : f - 2])
        socketio.emit("response", pdb.response(console),to=response.sid)
    else:
        pdb.state = 0
        socketio.emit("response", pdb.response(),to=response.sid)

@socketio.on("next")
def pdb_next_line():    
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    psocket.sendline("n")
    index = psocket.expect(["> .*\(\d+\)<module>()"])
    if index == 0:
        res = psocket.after.decode('utf-8')
        console = res.split('\r\n')[2:-1]
        print(console) #stdout/stderr
        s, f = re.search('\(\d+\)<', res).span()
        print(res[s + 1:f - 2]) #lineno
        pdb.lineno = int(res[s + 1 : f - 2])
        socketio.emit("response", pdb.response(console),to=response.sid)
        
@socketio.on("exit")
def pdb_exit():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    psocket.sendline("exit")
    index = psocket.expect(["exit"])
    if index == 0:
        pdb.lineno = 0
        pdb.state = 0
        socketio.emit("response", pdb.response(),to=response.sid)
        del pdb_poll[request.sid]

@socketio.on("check")
def pdb_getvalue(variables):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    psocket = pdb.psocket
    variables_list = []
    for i in variables:
        psocket.sendline("p %s"%i)
        psocket.expect(["p %s\r\n"%i])
        index = psocket.expect(["\r\n\(Pdb\)"])
        if index == 0:
            res = psocket.before.decode('utf-8')
            value = "\n".join(res.split('\r\n'))
        print(value)

        psocket.sendline("p type(%s)"%i)
        index = psocket.expect(["<class .*>"])
        if index == 0:
            res = psocket.after.decode('utf-8')
            typeof = res

        if typeof == "<class 'int'>":
            value = int(value)
        elif typeof == "<class 'float'>":
            value = int(value)

        variables_list.append({'name':i,'value':value,'type':typeof})
    socketio.emit("response", pdb.response(variables_list),to=response.sid)