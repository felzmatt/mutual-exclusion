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
    RELEASED = 0
    WANTED = 1
    HELD = 2

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

# messages types
REQ = 10
ACK = 20
REL = 30

def get_interested(p: int = 0.5):
    return secrets.randbelow(100) < 100*p

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

def maekawa(cs_time: int, my_id: int, peers: List[int], router_sock) -> None:
    
    #######################
    #        INIT         #
    #######################
    state = State.RELEASED
    voted = False
    V = get_voting_set(my_id, peers)
    replies = 0
    pending = []
    
    messages = queue.Queue()
    listener = threading.Thread(target=listen_incoming, args=(router_sock, messages))
    listener.start()
    last_enter = 0
    while True:
        
        if state == State.RELEASED:
            if get_interested(p=0.05):
                state = State.WANTED
                for peer in V:
                    req = Message(sender=my_id, receiver=peer, msg=REQ)
                    send(router_sock, req)
        
        elif state == State.WANTED:
            if replies == len(V):
                    # access CS
                    state = State.HELD
                    print("CS")
                    requests.post("http://cs:5000/enter_cs",data={"procID":my_id})
                    last_enter = time.time()
        
        elif state == State.HELD:
            if time.time() - last_enter > cs_time:
                # release the cs
                print("Leave")
                state = State.RELEASED
                replies = 0
                r = requests.post("http://cs:5000/leave_cs",data={"procID":my_id})
                for peer in V:
                    rel = Message(sender=my_id, receiver=peer, msg=REL)
                    send(router_sock, rel)
        try:
            msg = deliver(messages=messages)
            
            if msg:
                print(msg)
                
                # upon receipt of REQ
                if msg.msg == REQ:
                    if state == State.HELD or voted:
                        pending.append(msg.sender)
                    else:
                        ack = Message(sender=my_id, receiver=msg.sender, msg=ACK)
                        send(router_sock, ack)
                        voted = True
                # upon receipt of ACK
                elif msg.msg == ACK:
                    replies += 1
                    
                # upon receipt of REL
                elif msg.msg == REL:
                    if len(pending) > 0:
                        candidate = select_next(pending)
                        ack = Message(sender=my_id, receiver=candidate, msg=ACK)
                        send(router_sock, ack)
                        voted = True
                    else:
                        voted = False


        except Exception as e:
            # nothing to read go on
            pass
        time.sleep(1)

