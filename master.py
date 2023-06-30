import sys
import os
import socket
import select
import random
import time

from common.common import create_message, read_message

from common.config import CONFIG

def choose_elected():
    elected = set()
    k = random.randint(1, NUM)
    while len(elected) < k:
        e = random.randint(1, NUM)
        if e not in elected:
            elected.add(e)
    return elected

def create_listener(router_host: str, router_port: int):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.bind((router_host, router_port))
    sock.listen()
    return sock

if __name__ == "__main__":

    NUM = int(os.getenv("NUM_PROC"))
    master_sock = create_listener(router_host=CONFIG["ROUTER_HOST"], router_port=CONFIG["ROUTER_PORT"])

    print("ready")

    connections = []
    while len(connections) < NUM:
        sock, addr = master_sock.accept()
        connections.append(sock)

    print("anonymous connected")

    processes = dict()
    while len(processes) < NUM:
        readable, _, _ = select.select(connections, [], [])
        for sock in readable:
            raw_data = sock.recvfrom(16)
            sender, receiver, msg_type, ts = read_message(msg=raw_data[0])
            if sender not in processes:
                processes[sender] = sock
    
    print("I know these guys", processes)

    orders = [time.time()]
    first = True
    while True:
        # select guys who must enter cs
        now = time.time()
        if first or (now - orders[-1]) > 2.0:
            
            first = False
            cs_elected = choose_elected()
            print(f"Send orders to some processes {cs_elected}")
            for proc in cs_elected:
                order = create_message(sender=0, receiver=proc, msg_type=99, ts=0)
                processes[proc].sendall(order)
            cs_elected.clear()
            orders.append(time.time())
        readable, _, _ = select.select(connections, [], [])
        for sock in readable:
            raw_data = sock.recvfrom(16)
            sender, receiver, msg_type, ts = read_message(raw_data[0])
            # routing
            processes[receiver].sendall(raw_data[0])