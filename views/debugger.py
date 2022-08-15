import docker
import pexpect.fdpexpect
import re

client = docker.from_env()
containers = client.containers
container_id = '69'
container = containers.get(container_id)
_, sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
session = {'bp':[]}

psocket = pexpect.fdpexpect.fdspawn(sock.fileno(),timeout=10)

def pdb_connect(container_id):
    psocket.expect("#")
    psocket.sendline("cd test && python -m pdb test2.py")
    index = psocket.expect(["> \S*\(1\)<module>\(\)", "Error"])
    if index == 0:
        print("successfully connected")
    elif index == 1:
        return 500
    psocket.expect("(Pdb)")
    try:        
        return psocket
    except:
        return 200

def pdb_add_breakpoint(linenos):
    for i in linenos:
        psocket.sendline("b %d"%i)
        index = psocket.expect(["Breakpoint \d+ at .*:%d"%i,"End of file","\*\*\*"])
        if index == 0:
            print("successfully added line %d"%i)
            session['bp'].append(i)
        else:
            print("error %d:%s"%(index, psocket.after.decode('utf-8')))

def pdb_delete_breakpoint(linenos):
    pos = [i + 1 for i in range(len(session['bp'])) if session['bp'][i] in linenos]
    for i in pos:
        print(i)
        psocket.sendline("cl %d"%i)
        index = psocket.expect(["Deleted breakpoint \d+ at .*:\d+","End of file","\*\*\*"])

        if index == 0:
            print("successfully deleted bp %d"%i)
            session[i] = -1
        else:
            print("error %d:%s"%(index, psocket.after.decode('utf-8')))
        
def pdb_next_breakpoint():
    psocket.sendline("c")
    # psocket.expect('(Pdb) c')
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
        print(res[s + 1:f - 2]) #lineno

def pdb_next_line():
    psocket.sendline("n")
    index = psocket.expect(["> .*\(\d+\)<module>()"])
    if index == 0:
        res = psocket.after.decode('utf-8')
        console = res.split('\r\n')[2:-1]
        print(console) #stdout/stderr
        s, f = re.search('\(\d+\)<', res).span()
        print(res[s + 1:f - 2]) #lineno
        
def pdb_exit():
    psocket.sendline("exit")
    index = psocket.expect(["exit"])
    if index == 0:
        return 200

def pdb_getvalue(variables):
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
    print(variables_list)
    return variables_list

pdb_connect('69',)
pdb_add_breakpoint([4,])
pdb_next_breakpoint()
pdb_next_line()
pdb_delete_breakpoint([4,])
pdb_next_line()
pdb_getvalue(['i','sum'])