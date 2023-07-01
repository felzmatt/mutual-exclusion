import sys
import os
import queue
import threading
import socket
import select
import random
import time

from typing import Union, List

from common.common import create_message, read_message, Message, decode_message

from common.config import CONFIG

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
    messages = queue.Queue()
    listeners: List[threading.Thread]= []
    
    for proc_sock in processes.values():
        listeners.append(threading.Thread(target=listen_incoming, args=(proc_sock, messages)))
    
    for listener in listeners:
        listener.start()

    while True:
        try:
            msg = deliver(messages=messages)
            if msg:
                send(processes[msg.receiver], msg)
        except Exception as e:
            pass