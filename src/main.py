from subprocess import Popen, DEVNULL
from signal import SIGKILL
from os import kill
from time import sleep
import requests
from config import N

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

def init_nodes(pid_file, num_nodes = 5):
    '''
        This function performs the initialization of nodes (locally).
    It activates the bootstrap, then each other node. It performs the
    genesis block, giving all the starting NBCs
    '''
    for i in range(num_nodes):
        if i == 0:
            #bootstrap...
            pid = run(f"python ./src/rest.py --port={5000} -b", 'logs/id0.log')
            pid_file.write(str(pid)+'\n')
            print(pid)
            sleep(3.)
        else:
            pid = run(f"python ./src/rest.py --port={5000+i}", f'logs/id{i}.log')
            pid_file.write(str(pid)+'\n')
            print(pid)
            sleep(3.)

    requests.post(f'http://127.0.0.1:{5000}/broadcast_peers')
    sleep(3.)
    #make bootstrap start genesis...
    requests.post(f'http://127.0.0.1:{5000}/genesis')
    sleep(3.)
    #intitialize processings...
    for i in range(num_nodes):
        try:
            requests.post(f'http://127.0.0.1:{5000+i}/processing', timeout=2.)
        except:
            print(f'processing active for node {i}')



if __name__=="__main__":
    from argparse import ArgumentParser
    from os import remove
    from glob import glob

    parser = ArgumentParser()
    parser.add_argument('-stop', action='store_true',
                          help='Used for stopping all active rest processes!')
    args = parser.parse_args()

    if not args.stop:
        with open(PID_FILE, mode='w') as pid_file:
            #initialize all nodes and make genesis transactions!
            init_nodes(pid_file, num_nodes=N)

    if args.stop:
        #stops all pids registered in PIDFILE
        stop()
        #clean the pid file...
        with open(PID_FILE,'w') as file:
            pass
        #delete all id* files...
        for f in glob("./logs/id*.log"):
            remove(f) #remove all id.log files