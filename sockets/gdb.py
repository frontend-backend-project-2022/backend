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
import random
from views.dockers import docker_exec_bash
from views.database import db_getProjectInfo

class gdbData():
    def __init__(self, containerid, filepath, gdbsocket, runsocket, port):
        self.bp = [] #
        self.containerid = containerid
        self.filepath = filepath
        self.gdbsocket = gdbsocket
        self.runsocket = runsocket
        self.lineno = 1 #
        self.state = 1 #
        self.port = port

    def response(self, messageType="none", message = ""):
        # 返回的bp里-1代表已删除
        # bp_ = [[self.filepath, line_number] for line_number in self.bp]
        dic = {'bp':self.bp, 'lineno':[self.filepath, self.lineno],'state':self.state, 'messageType':messageType, 'message':message}
        return dic

gdb_poll = dict()
raw_sock_poll = dict()

def gdb_stdout(runsocket, sid):
    while runsocket.isalive():
        try:
            output = runsocket.read(1).decode('utf-8')
            if output == '':
                print('EOF reached.')
                gdb_exit(sid)
                return
            else:
                socketio.emit('stdout', output, to=sid, namespace="/gdb")
        except:
            print("runsocket is closed")

@socketio.on("start", namespace="/gdb")
def gdb_connect(container_id, filepath):
    def getPort():
        pscmd = "netstat -ntl |grep -v Active| grep -v Proto|awk '{print $4}'|awk -F: '{print $NF}'"
        procs = docker_exec_bash(container_id, pscmd)
        procarr = procs.split("\n")
        tt= random.randint(15000,20000)
        if tt not in procarr:
            return tt
        else:
            getPort()

    try:
        client = docker.from_env()
        containers = client.containers
        container = containers.get(container_id)

        _, gdb_raw_sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
        gdbsocket = pexpect.fdpexpect.fdspawn(gdb_raw_sock.fileno(), timeout=2)
        gdbsocket.expect("#")

        port = int(getPort())

        print("k")
        res = db_getProjectInfo(container_id)
        language_version = res['version']
        print(language_version)
        if 'gcc' in language_version:
            docker_exec_bash(container_id, "g++ -g %s -o .run.exe"%(filepath,))
        elif 'clang' in language_version: 
            docker_exec_bash(container_id, "clang++ -g %s -o .run.exe"%(filepath,))
        else:
            socketio.emit('error', "No suitable compiler")

        _, run_raw_sock = container.exec_run("gdbserver localhost:%d .run.exe"%(port, ), socket=True, stdin=True, tty=True)

        runsocket = pexpect.fdpexpect.fdspawn(run_raw_sock.fileno(), timeout=None)
        index = runsocket.expect(['Listen',])

        if index == 0:
            gdbsocket.sendline('gdb -q .run.exe')
            gdbsocket.sendline('target remote localhost:%d'%port)
            gdbsocket.expect('\(gdb\).*\(gdb\)')
            index = runsocket.expect(["Remote debugging from host 127\.0\.0\.1(, port \d+)?\r\n",pexpect.TIMEOUT])

            if index:
                raise Exception('timeout')
            runsocket.send('')
            thread = threading.Thread(target = gdb_stdout, args=(runsocket, request.sid))
            thread.start()
            print("successfully connected")
            gdb = gdbData(container_id, filepath, gdbsocket, runsocket, port)
            gdb_poll[request.sid] = gdb
            raw_sock_poll[request.sid] = {
                'gdb': gdb_raw_sock,
                'run': run_raw_sock
            }

            socketio.emit("initFinished", to=request.sid, namespace="/gdb")

    except Exception as e:
        print("error", e)


@socketio.on("add", namespace="/gdb")
def gdb_add_breakpoint(lineno):
    print(f'add breakpoint {lineno}')
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        socketio.emit("error", "Unstarted")
    gdbsocket = gdb.gdbsocket
    print(lineno)
    gdbsocket.sendline(f"b {lineno[1]}")
    index = gdbsocket.expect([f"Breakpoint \d+ at .* line {lineno[1]}\.","End of file","\*\*\*"])

    if index == 0:
        print(f"successfully added line {lineno[1]}")
        gdb.bp.append(lineno)
        socketio.emit("response", gdb.response(),to=request.sid, namespace="/gdb")
    elif index == 2:
        # gdb print "*** Blank or comment" when breakpoint is not on code.
        socketio.emit("response", gdb.response(),to=request.sid, namespace="/gdb")
    else:
        print("error %d:%s"%(index, gdbsocket.after.decode('utf-8')))

@socketio.on("addList", namespace="/gdb")
def gdb_add_breakpoint_list(linenoList):
    for lineno in linenoList:
        gdb_add_breakpoint(lineno)

@socketio.on("delete", namespace="/gdb")
def gdb_delete_breakpoint(lineno):
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        return "Unstarted", 500
    gdbsocket = gdb.gdbsocket
    pos = [i + 1 for i in range(len(gdb.bp)) if gdb.bp[i] == lineno]
    for i in pos:
        print(i)
        gdbsocket.sendline("del %d"%i)
        index = gdbsocket.expect(["\(gdb\)","End of file","\*\*\*"])

        if index == 0:
            print("successfully deleted bp %d"%i)
            gdb.bp[i - 1] = ["",-1]
        else:
            print("error %d:%s"%(index, gdbsocket.after.decode('utf-8')))
    socketio.emit("response", gdb.response(),to=request.sid, namespace="/gdb")

@socketio.on("skip", namespace="/gdb")
def gdb_next_breakpoint():
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        return "Unstarted", 500
    gdbsocket = gdb.gdbsocket
    gdbsocket.sendline("c")
    while gdbsocket.isalive():
        index = gdbsocket.expect(["Breakpoint \d+, .*:\d+\r\n.*\r\n.*\(gdb\)", "q to quit, c to continue", pexpect.EOF, pexpect.TIMEOUT])
        print(gdbsocket.before)
        if index == 0:
            break
        elif index == 1:
            print("get")
            gdbsocket.sendline("<RET>")
        elif index == 2:
            gdb_exit()
            return

    res = gdbsocket.after.decode('utf-8')
    res = res.split('\r\n')[-3]
    s, f = re.search(':\d+', res).span()
    print("lineno:", res[s + 1 : f]) #lineno
    gdb.lineno = int(res[s + 1 : f])

    socketio.emit("response", gdb.response(),to=request.sid, namespace="/gdb")


@socketio.on("next", namespace="/gdb")

def gdb_next_line():
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        return "Unstarted", 500
    gdbsocket = gdb.gdbsocket
    gdbsocket.sendline("n")
    while gdbsocket.isalive():
        index = gdbsocket.expect(["\d+.*\r\n.*\(gdb\)", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            break
        elif index == 1:
            gdb_exit()
            return

    res = gdbsocket.after.decode('utf-8')
    res = res.split('\r\n')[0]
    # s = 0
    # while res[s].isdigit() == False:
    #     s += 1
    # f = s + 1
    # while res[f].isdigit():
    #     f += 1
    s, f = re.search('\d+\t', res).span()
    print("lineno:", res[s : f - 1]) #lineno
    gdb.lineno = int(res[s : f - 1])

    socketio.emit("response", gdb.response(),to=request.sid, namespace="/gdb")


@socketio.on("check", namespace="/gdb")
def gdb_getvalue(variables):
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        return "Unstarted", 500
    gdbsocket = gdb.gdbsocket
    variables_list = []
    for i in variables:
        gdbsocket.sendline("p %s"%i)
        gdbsocket.expect(["p %s\r\n"%i])
        index = gdbsocket.expect(["\r\n\(gdb\)"])
        if index == 0:
            res = gdbsocket.before.decode('utf-8')
            value = "=".join(res.split('=')[1:])
        print(value)

        message = f"'value': {i} = {value}" # {'name':i,'value':value,'type':typeof}
        variables_list.append(message)

    socketio.emit("response", gdb.response(messageType="variables",message=variables_list),to=request.sid, namespace="/gdb")

@socketio.on("stdin", namespace="/gdb")
def gdb_stdin(message):
    gdb = gdb_poll[request.sid]
    if gdb.state == 0:
        return "Unstarted", 500
    runsocket = gdb.runsocket
    runsocket.send(message)

@socketio.on("exit", namespace="/gdb")
def gdb_exit(sid=None):
    if sid == None:
        sid = request.sid

    if sid not in gdb_poll.keys():
        return
    gdb = gdb_poll[sid]
    if gdb.state == 0:
        return "Unstarted", 500

    try:
        gdbsocket = gdb.gdbsocket
        gdbsocket.sendline("exit")
        index1 = gdbsocket.expect(["exit"])
    except:
        pass

    gdb.gdbsocket.close()
    gdb.runsocket.close()

    gdb.lineno = -1
    gdb.state = 0
    socketio.emit("response", gdb.response(),to=sid, namespace="/gdb")
    socketio.emit("end", namespace="/gdb")
    del gdb_poll[sid]

@socketio.on("disconnect", namespace="/gdb")
def gdb_disconnect():
    gdb_exit()
