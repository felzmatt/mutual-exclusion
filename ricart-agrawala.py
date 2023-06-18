import time
from enum import Enum
from typing import List

from common import create_message, read_message, format_message

class State(Enum):
    NCS = 0
    REQUESTING = 1
    CS = 2

class MSG_TYPE(Enum):
    REQUEST = 77
    REPLY = 88
    ENTER_CS = 99

def ricart_agrawala(my_id: int, peers: List[int], router_sock) -> None:
    replies = 0
    state = State.NCS
    Q = []
    num = 1
    last_req = num
    while True:
        raw_data = router_sock.recv(16)
        sender, receiver, msg_type, ts = read_message(msg=raw_data)
        print(f"Received {format_message(sender=sender, receiver=receiver, msg_type=msg_type, ts=ts)}")
        
        # upon receipt of REQUEST
        if msg_type == MSG_TYPE.REQUEST:
            if state == State.CS or (state == State.REQUESTING and (last_req, my_id) < (ts, sender)):
                Q.append((ts, sender))
            else:
                reply = create_message(sender=my_id, receiver=sender, msg_type=MSG_TYPE.REPLY, ts=0)
                router_sock.sendall(reply)
            num = max(ts, num)
        
        # upon receipt of REPLY
        elif msg_type == MSG_TYPE.REPLY:
            replies += 1

        # upon receive ENTER_CS
        elif msg_type == MSG_TYPE.ENTER_CS:
            if state == State.CS:
                pass
            else:
                state = State.REQUESTING
                num += 1
                last_req = num
                for peer in peers:
                    req = create_message(sender=my_id, receiver=peer, msg_type=MSG_TYPE.REQUEST, ts=num)
                    router_sock.sendall(req)
