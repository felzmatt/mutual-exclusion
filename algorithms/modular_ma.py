import time
import threading
import queue
import requests
import secrets
import sys
import os

from enum import Enum
from typing import List, Set, Union
from math import sqrt
from copy import deepcopy

from common.common import Message, decode_message, ACCESS_ORDER, STOP_ORDER, RELEASE, REQUEST, ACK, CS_ENTERED, CS_RELEASED, CS_REQUESTED, STOPPED

class State(Enum):
    NCS = 0
    REQUESTING = 1
    CS = 2
    STOPPED = 100

def get_interested(p: int = 0.5):
    return secrets.randbelow(100) < 100*p

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
    state = State.NCS
    replies = 0
    voted = False
    V = get_voting_set(my_id, peers)
    pending = []
    
    messages = queue.Queue()
    listener = threading.Thread(target=listen_incoming, args=(router_sock, messages))
    listener.start()
    
    last_enter = 0
    stopped = False
    automode = bool(int(os.getenv("AUTOMODE")))
    while True:
        if state == State.STOPPED:
            if not stopped:
                router_sock.close()
                sys.exit(0)
        
        if automode and state == State.NCS:
            if get_interested(p=0.01):
                print("I want CS")
                state = State.REQUESTING
                
                for peer in V:
                    req = Message(sender=my_id, receiver=peer, msg=REQUEST)
                    send(router_sock, req)
                cs_req = Message(sender=my_id, receiver=0, msg=CS_REQUESTED)
                send(router_sock, cs_req)
        
        elif state == State.REQUESTING:
            if replies == len(V):
                # access CS
                state = State.CS
                print("CS")
                requests.post("http://cs:5000/enter_cs",data={"procID":my_id})
                cs_entered = Message(sender=my_id, receiver=0, msg=CS_ENTERED)
                send(router_sock, cs_entered)
                last_enter = time.time()
        
        elif state == State.CS:
            if time.time() - last_enter > cs_time:
                # release the cs
                print("Leave")
                state = State.NCS
                replies = 0
                r = requests.post("http://cs:5000/leave_cs",data={"procID":my_id})
                for peer in V:
                    rel = Message(sender=my_id, receiver=peer, msg=RELEASE)
                    send(router_sock, rel)
                
                cs_rel = Message(sender=my_id, receiver=0, msg=CS_RELEASED)
                send(router_sock, cs_rel)
        try:
            msg = deliver(messages=messages)
            
            if msg:
                print(msg)
                if msg.msg == STOP_ORDER:
                    stopped = Message(sender=my_id, receiver=0, msg=STOPPED)
                    send(router_sock, stopped)
                    state = State.STOPPED
                
                elif msg.msg == ACCESS_ORDER:
                    print("I want CS")
                    state = State.REQUESTING
                    for peer in V:
                        req = Message(sender=my_id, receiver=peer, msg=REQUEST)
                        send(router_sock, req)
                    cs_req = Message(sender=my_id, receiver=0, msg=CS_REQUESTED)
                    send(router_sock, cs_req)
                # print(msg)
                # upon receipt of REQ
                elif msg.msg == REQUEST:
                    if state == State.CS or voted:
                        pending.append(msg.sender)
                    else:
                        ack = Message(sender=my_id, receiver=msg.sender, msg=ACK)
                        send(router_sock, ack)
                        voted = True
                    
                elif msg.msg == ACK:
                    replies += 1

                elif msg.msg == RELEASE:
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

