import time
import select
from enum import Enum
from typing import List

from common import create_message, read_message, format_message

class State(Enum):
    NCS = 0
    REQUESTING = 1
    CS = 2


REQUEST = 77
REPLY = 88
ENTER_CS = 99

def ricart_agrawala(cs_time: int, my_id: int, peers: List[int], router_sock) -> None:
    replies = 0
    state = State.NCS
    Q = []
    num = 1
    last_req = num
    enters = []
    
    # event loopS
    while True:
        if state == State.REQUESTING:
            if replies == len(peers):
                # received all REPLY required to access CS
                # access cs
                # TODO: make access call
                print("I AM ENTERING CS")
                state = State.CS
                enters.append(time.time())
        
        elif state == State.CS:
            now = time.time()
            if now - enters[-1] > cs_time:
                # time to exit cs
                # exit CS
                # TODO: make exit call
                print("I AM LEAVING CS")
                # send replies
                for req in Q:
                    reply = create_message(sender=my_id, receiver=req[1], msg_type=REPLY, ts=num)
                    router_sock.sendall(reply)
                Q.clear()
                state = State.NCS
                replies = 0
        
        readable, _, _ = select.select([router_sock], [], [])
        for sock in readable:
            raw_data = sock.recvfrom(16)
            sender, receiver, msg_type, ts = read_message(msg=raw_data[0])
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
