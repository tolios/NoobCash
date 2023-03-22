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
            print('Starting node using process: ', str(pid))
            sleep(3.)
        else:
            pid = run(f"python ./src/rest.py --port={5000+i}", f'logs/id{i}.log')
            pid_file.write(str(pid)+'\n')
            print('Starting node using process: ', str(pid))
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

    parser = ArgumentParser(description='''main.py is used for initializing and dealing with NBC nodes''')
    parser.add_argument('-stop', action='store_true',
                        help='Used for stopping all active rest processes!')
    parser.add_argument('-t', action='store', type=float, nargs=3,
                        help='Transaction made as: -t sender_id receiver_id amount')
    parser.add_argument('-v', action='store', type=int, nargs=1,
                        help='View transaction(s) in the last validated block of an id')
    parser.add_argument('-b', action='store', type=int, nargs=1,
                        help='Get balance of an id')
    parser.add_argument('-tf', action='store_true',
                        help='Use transaction files!')
    args = parser.parse_args()
    
    if not args.stop:
        if (args.t is None) and (args.v is None) and (args.b is None):
            with open(PID_FILE, mode='w') as pid_file:
                #initialize all nodes and make genesis transactions!
                init_nodes(pid_file, num_nodes=N)
                if args.tf:
                    #use transaction files!
                    print('Will use transaction files...')
                    #use N = 5 or 10 else raise...
        else:
            if not (args.t is None):
                assert len(args.t) == 3
                sender_id, receiver_id, amount = args.t
                sender_id, receiver_id = int(sender_id), int(receiver_id)
                requests.post(f'http://127.0.0.1:{5000+sender_id}/new_transaction',
                            json={'id':str(receiver_id), 'amount': amount})
            elif not (args.v is None):
                assert len(args.v) == 1
                sender_id = args.v.pop(0)
                answer = requests.get(f'http://127.0.0.1:{5000+sender_id}/view')
                print('\n'.join(answer.json()))
            elif not (args.b is None):
                assert len(args.b) == 1
                sender_id = args.b.pop(0)
                answer = requests.get(f'http://127.0.0.1:{5000+sender_id}/balance')
                print(answer.json())
            else:
                print('Something wrong happened, only one command at a time...')
    else:
        #stops all pids registered in PIDFILE
        stop()
        #clean the pid file...
        with open(PID_FILE,'w') as file:
            pass
        #delete all id* files...
        for f in glob("./logs/id*.log"):
            remove(f) #remove all id.log files
