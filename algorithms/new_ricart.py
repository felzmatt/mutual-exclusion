import time
import threading
import queue
import requests
import secrets

from enum import Enum
from typing import List, Set, Union
from math import sqrt
from copy import deepcopy

from common.common import Message, decode_message

class State(Enum):
    NCS = 0
    REQUESTING = 1
    CS = 2

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
    voting = list()
    proc_i = (procID - 1) // nsq
    proc_j = (procID-1) % nsq
    # print(i,j)
    for i in range(nsq):
        for j in range(nsq):
            if i == proc_i or j == proc_j:
                voting.append(matrix[i][j])
    # print(matrix)
    return voting

def select_next(pending: List[int]) -> int:
    return pending.pop(0)

def get_interested(p: int = 0.5):
    return secrets.randbelow(100) < 100*p

# messages types
REQ = 10
ACK = 20

BUFSIZE = 16
def listen_incoming(router_sock, messages_queue: queue.Queue):
    while True:
        data = router_sock.recv(BUFSIZE)
        msg = decode_message(data=data)
        # print(f"Received {msg}")
        messages_queue.put(msg)

def deliver(messages: queue.Queue) -> Union[Message,None]:
    try:
        msg = messages.get(block=False, timeout=1)
        return msg
    except queue.Empty:
        return None

def send(router_sock, message: Message):
    # print(f"Sending {message}")
    router_sock.send(message.pack())

def ricart_agrawala(cs_time: int, my_id: int, peers: List[int], router_sock) -> None:
    
    #######################
    #        INIT         #
    #######################
    state = State.NCS
    replies = 0
    Q = []
    num = 1
    last_req = num
    
    messages = queue.Queue()
    listener = threading.Thread(target=listen_incoming, args=(router_sock, messages))
    listener.start()
    
    last_enter = 0
    while True:
        # print(f"    Status {state} replies {replies}")
        if state == State.NCS:
            if get_interested(p=0.25):
                print("I want CS")
                state = State.REQUESTING
                num += 1
                last_req = num
                for peer in peers:
                    req = Message(sender=my_id, receiver=peer, msg=REQ, ts=num)
                    send(router_sock, req)
        
        elif state == State.REQUESTING:
            if replies == len(peers):
                # access CS
                state = State.CS
                print("CS")
                requests.post("http://cs:5000/enter_cs",data={"procID":my_id})
                last_enter = time.time()
        
        elif state == State.CS:
            if time.time() - last_enter > cs_time:
                # release the cs
                print("Leave")
                state = State.NCS
                replies = 0
                r = requests.post("http://cs:5000/leave_cs",data={"procID":my_id})
                for req in Q:
                    ack = Message(sender=my_id, receiver=req[1], msg=ACK, ts=num)
                    send(router_sock, ack)
                Q.clear()
        try:
            msg = deliver(messages=messages)
            
            if msg:
                print(msg)
                # upon receipt of REQ
                if msg.msg == REQ:
                    if state == State.CS or (state == State.REQUESTING and (last_req, my_id) < (msg.ts, msg.sender)):
                        Q.append((msg.ts, msg.sender))
                    else:
                        ack = Message(sender=my_id, receiver=msg.sender, msg=ACK)
                        send(router_sock, ack)
                    num = max(msg.ts, num)
                
                # upon receipt of ACK
                if msg.msg == ACK:
                    replies += 1
                
        except Exception as e:
            # nothing to read go on
            pass
        time.sleep(1)

