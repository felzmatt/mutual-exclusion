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

def select_next(pending: List[int]) -> int:
    return pending.pop(0)


REQUEST = 77
REPLY = 88
ENTER_CS = 99

def maekawa(cs_time: int, my_id: int, peers: List[int], router_sock) -> None:
    replies = 0
    # slides variables
    state = State.RELEASED
    voted = False
    V = get_voting_set(my_id, peers)
    replies = 0
    pending = []
    
    enters = []

    router_sock.setblocking(0)
    router_sock.settimeout(1)
    
    # event loopS
    while True:
        # print("looping")
        if state == State.WANTED:
            if replies == len(V) - 1:
                # received all REPLY required to access CS
                # access cs
                # TODO: make access call
                print("I AM ENTERING CS")
                r = requests.post("http://cs:5000/enter_cs",data={"procID":my_id})
                if r.status_code == 200:
                    state = State.HELD
                    enters.append(time.time())
        
        elif state == State.HELD:
            now = time.time()
            print(now - enters[-1])
            if now - enters[-1] > cs_time:
                # time to exit cs
                # exit CS
                # TODO: make exit call
                print("I AM LEAVING CS")
                r = requests.post("http://cs:5000/leave_cs",data={"procID":my_id})
                # send replies
                state = State.RELEASED
                replies = 0
                for peer in V:
                    if peer != my_id:
                        rel = create_message(sender=my_id, receiver=peer, msg_type=MSGType.REL, ts=0)
                        router_sock.sendall(rel)


        
        # readable, _, _ = select.select([router_sock], [], [])
        # for sock in readable:
        try:
            raw_data = router_sock.recv(16)
            sender, receiver, msg_type, ts = read_message(msg=raw_data)

            # don't print messages from master
            if sender != 0:
                print(f"Received {format_message(sender=sender, receiver=receiver, msg_type=msg_type, ts=ts)}")
        
            # upon receipt of REQUEST
            if msg_type == MSGType.REQ:
                if state == State.HELD or voted:
                    pending.append(sender)
                else:
                    ack = create_message(sender=my_id, receiver=sender, msg_type=MSGType.ACK, ts=0)
                    router_sock.sendall(ack)
                    voted = True
            
            # upon receipt of ACK
            elif msg_type == MSGType.ACK:
                replies += 1
        
            # upon receipt of RELEASE
            elif msg_type == MSGType.REL:
                if len(pending) > 0:
                    candidate = select_next(pending)
                    # pending.remove(candidate)
                    ack = create_message(sender=my_id, receiver=candidate, msg_type=MSGType.ACK, ts=0)
                    router_sock.sendall(ack)
                    voted = True
                else:
                    voted = False

            # upon receive ENTER_CS
            elif msg_type == ENTER_CS:
                state = State.WANTED
                for peer in V:
                    if peer != my_id:
                        req = create_message(sender=my_id, receiver=peer, msg_type=MSGType.REQ, ts=0)
                        router_sock.sendall(req)
        except Exception as e:
            pass
        time.sleep(1)
