import sys
import socket
import select

from common import create_message, read_message
from config import CONFIG

def create_listener(router_host: str, router_port: int):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.bind((router_host, router_port))
    sock.listen()
    return sock

if __name__ == "__main__":
    master_sock = create_listener(router_host=CONFIG["ROUTER_HOST"], router_port=CONFIG["ROUTER_PORT"])

    print("ready")

    connections = []
    while len(connections) < CONFIG["NUM_PROC"]:
        sock, addr = master_sock.accept()
        connections.append(sock)

    print("anonymous connected")

    processes = dict()
    while len(processes) < CONFIG["NUM_PROC"]:
        readable, _, _ = select.select(connections, [], [])
        for sock in readable:
            raw_data = sock.recvfrom(16)
            sender, receiver, msg_type, ts = read_message(msg=raw_data[0])
            if sender not in processes:
                processes[sender] = sock
    
    print("I know these guys", processes)
    
    while True:
        readable, _, _ = select.select(connections, [], [])
        for sock in readable:
            raw_data = sock.recvfrom(16)
            sender, receiver, msg_type, ts = read_message(raw_data[0])
            # routing
            processes[receiver].sendall(raw_data[0])