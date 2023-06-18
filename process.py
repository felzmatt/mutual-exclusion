import sys
import socket
import time
import random

from common import create_message, read_message, format_message
from config import CONFIG

from ricart_agrawala import ricart_agrawala


def connect_router(router_host, router_port):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.connect((router_host, router_port))
    return sock

def get_peers(my_id: int, num: int):
    return [i for i in range(1,num+1) if i != my_id]

if __name__ == "__main__":
    my_id = int(sys.argv[1])
    router_sock = connect_router(router_host=CONFIG["ROUTER_HOST"], router_port=CONFIG["ROUTER_PORT"])
    peers = get_peers(my_id=my_id, num=CONFIG["NUM_PROC"])

    # make master know about me
    msg = create_message(sender=my_id, receiver=0, msg_type=0, ts=0)
    router_sock.sendall(msg)
    
    num = 1
    """
    while True:

        # if random.randint(0,100) > 50:
        receiver = random.choice(peers)
        msg = create_message(sender=my_id, receiver=receiver, msg_type=69, ts=num)
        print(f"Sending {format_message(sender=my_id, receiver=receiver, msg_type=69, ts=num)}")
        router_sock.sendall(msg)
        num += 1
        
        raw_data = router_sock.recv(16)
        sender, receiver, msg_type, ts = read_message(msg=raw_data)
        print(f"Received {format_message(sender=sender, receiver=receiver, msg_type=msg_type, ts=ts)}")
        raw_msg = create_message(sender=my_id, receiver=sender, msg_type=69, ts=num)
        
        time.sleep(2)
        """
    ricart_agrawala(cs_time=4, my_id=my_id, peers=peers, router_sock=router_sock)