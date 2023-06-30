import time
import select
from enum import Enum
from typing import List, Set
import requests
from math import sqrt
from copy import deepcopy

from common.common import create_message, read_message, format_message

class MSGType(Enum):
    REQ = 10
    ACK = 20
    REL = 30

    def __str__(self):
        return self.name

class State(Enum):
    RELEASED = 1
    WANTED = 2
    HELD = 3

    def __str__(self):
        return self.name
    
def get_voting_set(procID: int, peers: List[int]) -> Set[int]:
    
    processes = deepcopy(peers)
    processes.append(procID)
    processes.sort()
    n = len(processes)
    nsq = int(sqrt(n))
    print(n, nsq)
    matrix = []
    k = 0
    for i in range(nsq):
        row = []
        # print(k)
        for j in range(nsq):
            # print(i,j)
            row.append(processes[k])
            k  += 1
        matrix.append(row)
    voting = set()
    proc_i = (procID - 1) // nsq
    proc_j = (procID-1) % nsq
    # print(i,j)
    for i in range(nsq):
        for j in range(nsq):
            if i == proc_i or j == proc_j:
                voting.add(matrix[i][j])
    # print(matrix)
    return voting


REQUEST = 77
REPLY = 88
ENTER_CS = 99

def maekawa(cs_time: int, my_id: int, peers: List[int], router_sock) -> None:
    replies = 0
    # slides variables
    state = State.RELEASED
    voted = False
    V = get_voting_set(my_id, peers)
    replies = []
    pending = []
    
    enters = []

    router_sock.setblocking(0)
    router_sock.settimeout(1)
    
    # event loopS
    while True:
        # print("looping")
        if state == State.REQUESTING:
            if replies == len(peers):
                # received all REPLY required to access CS
                # access cs
                # TODO: make access call
                print("I AM ENTERING CS")
                r = requests.post("http://cs:5000/enter_cs",data={"procID":my_id})
                if r.status_code == 200:
                    state = State.CS
                    enters.append(time.time())
        
        elif state == State.CS:
            now = time.time()
            print(now - enters[-1])
            if now - enters[-1] > cs_time:
                # time to exit cs
                # exit CS
                # TODO: make exit call
                print("I AM LEAVING CS")
                r = requests.post("http://cs:5000/leave_cs",data={"procID":my_id})
                # send replies
                for req in Q:
                    reply = create_message(sender=my_id, receiver=req[1], msg_type=REPLY, ts=num)
                    router_sock.sendall(reply)
                Q.clear()
                state = State.NCS
                replies = 0
        
        # readable, _, _ = select.select([router_sock], [], [])
        # for sock in readable:
        try:
            raw_data = router_sock.recv(16)
            sender, receiver, msg_type, ts = read_message(msg=raw_data)

            # don't print messages from master
            if sender != 0:
                print(f"Received {format_message(sender=sender, receiver=receiver, msg_type=msg_type, ts=ts)}")
        
            # upon receipt of REQUEST
            if msg_type == REQUEST:
                if state == State.CS or (state == State.REQUESTING and (last_req, my_id) < (ts, sender)):
                    Q.append((ts, sender))
                else:
                    reply = create_message(sender=my_id, receiver=sender, msg_type=REPLY, ts=0)
                    router_sock.sendall(reply)
                num = max(ts, num)
        
            # upon receipt of REPLY
            elif msg_type == REPLY:
                replies += 1

            # upon receive ENTER_CS
            elif msg_type == ENTER_CS:
                if state == State.NCS:
                    state = State.REQUESTING
                    num += 1
                    last_req = num
                    for peer in peers:
                        req = create_message(sender=my_id, receiver=peer, msg_type=REQUEST, ts=num)
                        router_sock.sendall(req)
        except Exception as e:
            pass
        time.sleep(1)
