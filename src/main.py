from subprocess import Popen, DEVNULL
from signal import SIGKILL
from os import kill
from time import sleep
import requests

PID_FILE = "logs/pids.log"

# ps aux | awk '{print $2,$11,$12,$13}' | grep ./src/rest.py
# kill -9 pid if i have running rest processes (error or bug in main.py)

def run(cmd: str, logfile: str):
    '''
    Runs a process and returns its id...
    '''
    proc = Popen(cmd.split(),
                stdout=open(logfile, 'w'),
                stderr=DEVNULL)
    return proc.pid

def stop():
    '''
    Delete all the processes that start from the 'start' step
    '''
    with open(PID_FILE, mode='r') as pid_file:
        pids = [pid for pid in pid_file.read().split('\n')]
        #
        for pid in pids:
            if pid != '':
                kill(int(pid), SIGKILL)
                print("Killed: "+pid)

def init_nodes():
    '''
        This function performs the initialization of nodes (locally).
    It activates the bootstrap, then each other node. It performs the
    genesis block, giving all the starting NBCs
    '''
    raise NotImplemented


if __name__=="__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-stop', action='store_true',
                          help='Used for stopping all active rest processes!')
    args = parser.parse_args()

    if not args.stop:
        with open(PID_FILE, mode='w') as pid_file:

            pid1 = run("python ./src/rest.py --port=5000 -b", 'logs/hi0.log')
            print(pid1)
            pid_file.write(str(pid1)+'\n')
            sleep(3.)

            pid2 = run("python ./src/rest.py --port=5001", 'logs/hi2.log')
            print(pid2)
            pid_file.write(str(pid2)+'\n')
            sleep(3.)

            pid3 = run("python ./src/rest.py --port=5002", 'logs/hi3.log')
            print(pid3)
            pid_file.write(str(pid3)+'\n')
            sleep(3.)

            pid4 = run("python ./src/rest.py --port=5003", 'logs/hi4.log')
            print(pid4)
            pid_file.write(str(pid4)+'\n')
            sleep(3.)

            pid5 = run("python ./src/rest.py --port=5004", 'logs/hi5.log')
            print(pid5)
            pid_file.write(str(pid5)+'\n')
            sleep(3.)

            requests.post('http://127.0.0.1:5000/broadcast_peers')

    if args.stop:
        #stops all pids registered in PIDFILE
        stop()
        #clean the pid file...
        with open(PID_FILE,'w') as file:
            pass