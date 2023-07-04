import os
import sys
import socket
import time
import random

from common.common import create_message
from common.config import CONFIG

from algorithms.modular_ra import ricart_agrawala
from algorithms.modular_ma import maekawa


def connect_router(router_host, router_port):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.connect((router_host, router_port))
    return sock

def get_peers(my_id: int, num: int):
    return [i for i in range(1,num+1) if i != my_id]

NUM = int(os.getenv("NUM_PROC"))
PROTOCOL = os.getenv("PROTOCOL")
CS_TIME = int(os.getenv("CS_TIME"))

if __name__ == "__main__":
    if PROTOCOL not in ["RA","M"]:
        print("Unknown protocol, exiting.")
        sys.exit(1)
    # print(os.environ.get("HOSTNAME"))
    # my_id = int(os.environ.get("HOSTNAME").split("_")[1])
    # print("connecting master ...")
    my_id = int(sys.argv[1])
    router_sock = connect_router(router_host=CONFIG["ROUTER_HOST"], router_port=CONFIG["ROUTER_PORT"])
    peers = get_peers(my_id=my_id, num=NUM)
    # print("connected")

    # make master know about me
    msg = create_message(sender=my_id, receiver=0, msg_type=0, ts=0)
    router_sock.sendall(msg)
    
    num = 1
    
    if PROTOCOL == "RA":
        ricart_agrawala(cs_time=CS_TIME, my_id=my_id, peers=peers, router_sock=router_sock)
    else:
        maekawa(cs_time=CS_TIME, my_id=my_id, peers=peers, router_sock=router_sock)
