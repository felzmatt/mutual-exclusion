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
    stopped = False
    automode = bool(int(os.getenv("AUTOMODE")))
    while True:
        if state == State.STOPPED:
            if not stopped:
                router_sock.close()
                sys.exit(0)
        # print(f"    Status {state} replies {replies}")
        if automode and state == State.NCS:
            if get_interested(p=0.01):
                print("I want CS")
                state = State.REQUESTING
                num += 1
                last_req = num
                for peer in peers:
                    req = Message(sender=my_id, receiver=peer, msg=REQUEST, ts=num)
                    send(router_sock, req)
                cs_req = Message(sender=my_id, receiver=0, msg=CS_REQUESTED)
                send(router_sock, cs_req)
        
        elif state == State.REQUESTING:
            if replies == len(peers):
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
                for req in Q:
                    ack = Message(sender=my_id, receiver=req[1], msg=ACK)
                    send(router_sock, ack)
                Q.clear()
                cs_rel = Message(sender=my_id, receiver=0, msg=CS_RELEASED)
                send(router_sock, cs_rel)
        try:
            msg = deliver(messages=messages)
            
            if msg:
                # print(msg)
                if msg.msg == STOP_ORDER:
                    stopped = Message(sender=my_id, receiver=0, msg=STOPPED)
                    send(router_sock, stopped)
                    state = State.STOPPED
                
                if msg.msg == ACCESS_ORDER:
                    print("I want CS")
                    state = State.REQUESTING
                    num += 1
                    last_req = num
                    for peer in peers:
                        req = Message(sender=my_id, receiver=peer, msg=REQUEST, ts=num)
                        send(router_sock, req)
                    cs_req = Message(sender=my_id, receiver=0, msg=CS_REQUESTED)
                    send(router_sock, cs_req)
                # print(msg)
                # upon receipt of REQ
                if msg.msg == REQUEST:
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

