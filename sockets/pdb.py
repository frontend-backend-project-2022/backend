import docker
import pexpect
import pexpect.fdpexpect
import re
import os
import json
from flask import request, jsonify
import threading
from sockets import socketio
import select
from views.dockers import docker_exec_bash

# This file contains Python-debugging related part.

class pdbData():
    # basic info of a running pdb
    def __init__(self, containerid, filepath, pdbsocket, runsocket, host, post):
        self.bp = []
        self.containerid = containerid
        self.filepath = filepath
        self.pdbsocket = pdbsocket
        self.runsocket = runsocket
        self.lineno = ['.run.py', -1]
        self.state = 1
        self.host = host
        self.post = post

    def response(self, messageType="none", message = ""):
        # 返回的bp里-1代表已删除
        # bp = [[self.filepath, line_number] for line_number in self.bp]
        dic = {'bp':self.bp, 'lineno':self.lineno,'state':self.state, 'messageType':messageType, 'message':message}
        return dic

# memory poll for pdbData
pdb_poll = dict()
raw_sock_poll = dict()

# get stdout/stderr from runsocket and sent to front-end
def pdb_stdout(runsocket, sid):
    while runsocket.isalive():
        try:
            output = runsocket.read(1).decode('utf-8')
            if output == '':
                print('EOF reached.')
                pdb_exit(sid)
                return
            else:
                socketio.emit('stdout', output, to=sid, namespace="/pdb")
        except:
            print("runsocket is closed")

# start pdb and detach run-terminal and pdb-terminal
@socketio.on("start", namespace="/pdb")
def pdb_connect(container_id, filepath):
    try:
        client = docker.from_env()
        containers = client.containers
        container = containers.get(container_id)

        _, pdb_raw_sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
        pdbsocket = pexpect.fdpexpect.fdspawn(pdb_raw_sock.fileno(), timeout=2)
        pdbsocket.expect("#")

        docker_exec_bash(container_id, r"echo 'from remote_pdb import set_trace\nset_trace()\nimport importlib.util\nspec = importlib.util.spec_from_file_location(\"__main__\", \"{}\")\nfoo = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(foo)' > .run".format(filepath))
        _, run_raw_sock = container.exec_run("python .run", socket=True, stdin=True, tty=True)
        runsocket = pexpect.fdpexpect.fdspawn(run_raw_sock.fileno(), timeout=None)
        index = runsocket.expect(['waiting for connection ...',])

        if index == 0:
            res = runsocket.before.decode('utf-8')
            s,f = re.search('\d+\.\d+\.\d+\.\d+:\d+',res).span()
            host, post = res[s:f].split(":")
            # print('telnet %s %s'%(host, post))
            pdbsocket.sendline('telnet %s %s'%(host, post))
            index = pdbsocket.expect(['(Pdb)',pexpect.TIMEOUT])
            if index:
                raise Exception('timeout')
            print(post, type(post))
            index = runsocket.expect(["RemotePdb accepted connection from \('%s', \d+\)\.\r\nRemotePdb accepted connection from \('%s', \d+\)\.\r\n"%(host, host),pexpect.TIMEOUT])
            if index:
                raise Exception('timeout')
            runsocket.send('')

            thread = threading.Thread(target = pdb_stdout, args=(runsocket, request.sid))
            thread.start()
            print("successfully connected")
            pdb = pdbData(container_id, filepath, pdbsocket, runsocket, host, post)
            pdb_poll[request.sid] = pdb
            raw_sock_poll[request.sid] = {
                'pdb': pdb_raw_sock,
                'run': run_raw_sock
            }

            socketio.emit("initFinished", to=request.sid, namespace="/pdb")

    except Exception as e:
        print("error", e)

# add a breakpoint
@socketio.on("add", namespace="/pdb")
def pdb_add_breakpoint(lineno):
    print(f'add breakpoint {lineno}')
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        socketio.emit("error", "Unstarted")
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline(f"b {lineno[0]}:{lineno[1]}")
    index = pdbsocket.expect(["Breakpoint \d+ at .*:%d"%lineno[1],"End of file","\*\*\*"])

    if index == 0:
        print(f"successfully added line {lineno[0]}:{lineno[1]}")
        print(pdbsocket.after.decode('utf-8'))
        pdb.bp.append(lineno)
        socketio.emit("response", pdb.response(),to=request.sid, namespace="/pdb")
    elif index == 2:
        # pdb print "*** Blank or comment" when breakpoint is not on code.
        socketio.emit("response", pdb.response(),to=request.sid, namespace="/pdb")
    else:
        print("error %d:%s"%(index, pdbsocket.after.decode('utf-8')))

# add breakpoint list
@socketio.on("addList", namespace="/pdb")
def pdb_add_breakpoint_list(linenoList):
    for lineno in linenoList:
        pdb_add_breakpoint(lineno)
    socketio.emit("addListFinished", to=request.sid, namespace="/pdb")

# delete a breakpoint
@socketio.on("delete", namespace="/pdb")
def pdb_delete_breakpoint(lineno):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pos = [i + 1 for i in range(len(pdb.bp)) if pdb.bp[i] == lineno]
    for i in pos:
        pdbsocket.sendline("cl %d"%i)
        index = pdbsocket.expect(["Deleted breakpoint \d+ at .*:\d+","End of file","\*\*\*"])

        if index == 0:
            print("successfully deleted bp %d"%i)
            pdb.bp[i - 1] = ["", -1]
        else:
            print("error %d:%s"%(index, pdbsocket.after.decode('utf-8')))
    socketio.emit("response", pdb.response(),to=request.sid, namespace="/pdb")

line_result_regex = r"> ([^ ]*|<[^<>]*>)\((\d+)\)[<\w>]+\(\)"

# continue
@socketio.on("skip", namespace="/pdb")
def pdb_next_breakpoint():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("c")
    while pdbsocket.isalive():
        index = pdbsocket.expect([line_result_regex, pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            break
        elif index == 1:
            pdb_exit()
            return

    res = pdbsocket.after.decode('utf-8')
    re_result = re.search(line_result_regex, res)
    fileurl, lineNumber = re_result.group(1), int(re_result.group(2))
    fileurl = '/'.join(['.'] + fileurl.split('/')[2:])  # to relative path
    pdb.lineno = [fileurl, lineNumber]

    socketio.emit("response", pdb.response(),to=request.sid, namespace="/pdb")

# next
@socketio.on("next", namespace="/pdb")
def pdb_next_line():
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    pdbsocket = pdb.pdbsocket
    pdbsocket.sendline("n")
    while pdbsocket.isalive():
        index = pdbsocket.expect([line_result_regex, pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            break
        elif index == 1:
            pdb_exit()
            return

    res = pdbsocket.after.decode('utf-8')
    print(res)
    re_result = re.search(line_result_regex, res)
    fileurl, lineNumber = re_result.group(1), int(re_result.group(2))
    print(fileurl, lineNumber)
    if fileurl.startswith('/workspace') and fileurl != './.run':
        fileurl = '/'.join(['.'] + fileurl.split('/')[2:])  # to relative path
        pdb.lineno = [fileurl, lineNumber]
        print(pdb.lineno)
        socketio.emit("response", pdb.response(),to=request.sid, namespace="/pdb")
    else:
        pdb_next_line()

# check value of variables
@socketio.on("check", namespace="/pdb")
def pdb_getvalue(variables):
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

        message = None
        pdbsocket.sendline("p type(%s)"%i)
        index = pdbsocket.expect(["<class .*>", "\*\*\* NameError: name .* is not defined"])
        if index == 0:
            res = pdbsocket.after.decode('utf-8')
            typeof = res

            if typeof == "<class 'int'>":
                value = int(value)
            elif typeof == "<class 'float'>":
                value = float(value)
        else:
            message = pdbsocket.after.decode('utf-8')

        if message is None:
            message = f"{typeof}: {i} = {value}" # {'name':i,'value':value,'type':typeof}
        variables_list.append(message)

    socketio.emit("response", pdb.response(messageType="variables",message=variables_list),to=request.sid, namespace="/pdb")

# listen to message from front-end and sent to runsocket for handling
@socketio.on("stdin", namespace="/pdb")
def pdb_stdin(message):
    pdb = pdb_poll[request.sid]
    if pdb.state == 0:
        return "Unstarted", 500
    runsocket = pdb.runsocket
    runsocket.send(message)

# exit debugging
@socketio.on("exit", namespace="/pdb")
def pdb_exit(sid=None):
    if sid == None:
        sid = request.sid

    if sid not in pdb_poll.keys():
        return
    pdb = pdb_poll[sid]
    if pdb.state == 0:
        return "Unstarted", 500

    try:
        pdbsocket = pdb.pdbsocket
        pdbsocket.sendline("exit")
        index1 = pdbsocket.expect(["exit"])
    except:
        pass

    pdb.pdbsocket.close()
    pdb.runsocket.close()

    pdb.lineno = ['.run.py', -1]
    pdb.state = 0
    socketio.emit("response", pdb.response(),to=sid, namespace="/pdb")
    socketio.emit("end", namespace="/pdb")
    del pdb_poll[sid]

@socketio.on("disconnect", namespace="/pdb")
def pdb_disconnect():
    pdb_exit()