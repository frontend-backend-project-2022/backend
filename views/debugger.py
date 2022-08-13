import docker

client = docker.from_env()
containers = client.containers
container = containers.get('69')
_, sock = container.exec_run("/bin/bash", socket=True, stdin=True, tty=True)
import pexpect.fdpexpect
session=pexpect.fdpexpect.fdspawn(sock.fileno(),timeout=10)
session.expect("#")
# print(session.before.decode('utf-8'))
print(session.after.decode('utf-8'))
session.send("cd test && python -m pdb test.py\n")

session.expect("Pdb")
print(session.before.decode('utf-8'))
print(session.after.decode('utf-8'))