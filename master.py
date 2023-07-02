import sys
import os
import queue
import threading
import socket
import select
import random
import time
import string
import secrets

import numpy as np
from typing import Union, List, Set

from common.common import create_message, read_message, Message, decode_message, ACCESS_ORDER, STOP_ORDER, RELEASE, REQUEST, ACK, CS_ENTERED, CS_RELEASED, CS_REQUESTED, STOPPED
from events import Event, EventRegister, EventType
from common.config import CONFIG

BUFSIZE = 16

NUM = int(os.getenv("NUM_PROC"))
AUTOMODE = bool(int(os.getenv("AUTOMODE"))) # it is 0 or 1
LOAD = float(os.getenv("LOAD")) # it has sense only if AUTOMODE
EXP_TIME = int(os.getenv("EXP_TIME"))

######################################
#       AUXILIARY FUNCTIONS          #
######################################
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

def elect_participants() -> Set[int]:
    k = int(NUM*LOAD)
    elected = np.random.choice(range(1, NUM + 1), size=k, replace=False)
    return set(elected.tolist())

def deliver(messages: queue.Queue) -> Union[Message,None]:
    try:
        msg = messages.get(block=False, timeout=1)
        return msg
    except queue.Empty:
        return None

def send(router_sock, message: Message):
    # print(f"Sending {message}")
    router_sock.send(message.pack())

def listen_incoming(router_sock, messages_queue: queue.Queue, register: EventRegister, stopped, accessed: Set[int]):
    while True:
        data = router_sock.recv(BUFSIZE)
        msg = decode_message(data=data)
        if msg.receiver != 0:
            messages_queue.put(msg)
        
        if msg.msg == RELEASE or msg.msg == REQUEST or msg.msg == ACK:
            register.insert_event(ev=Event(
                evtype=EventType.MSG,
                procID=msg.sender,
                message=msg
            ))
        else:
            if msg.msg == CS_REQUESTED:
                evtype = EventType.CS_REQUESTED
            elif msg.msg == CS_ENTERED:
                evtype = EventType.CS_ACCESS
                accessed.add(msg.sender)
            elif msg.msg == CS_RELEASED:
                evtype = EventType.CS_LEAVE
            elif msg.msg == STOPPED:
                
                evtype = EventType.PROC_STOPPED
                stopped.append(msg.sender)
                print(stopped)
            else:
                print("Strange message" + str(msg))
                evtype = None
        
            register.insert_event(ev=Event(
                evtype=evtype,
                procID=msg.sender
            ))


######################################
#       MASTER PROCESS CLASS         #
######################################
class Master:
    def __init__(self):
        self.automode = AUTOMODE
        self.exp_time = EXP_TIME
        if not self.automode:
            self.participants = elect_participants()
    
    def create_listener(self, router_host: str, router_port: int):
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.sock.bind((router_host, router_port))
        self.sock.listen()
        print("ready")
    
    def accept_processes(self):
        self.connections = []
        while len(self.connections) < NUM:
            sock, addr = self.sock.accept()
            self.connections.append(sock)
        print("anonymous connected")

    def recognize_processes(self):
        self.processes = dict()
        while len(self.processes) < NUM:
            readable, _, _ = select.select(self.connections, [], [])
            for sock in readable:
                raw_data = sock.recvfrom(16)
                sender, receiver, msg_type, ts = read_message(msg=raw_data[0])
                if sender not in self.processes:
                    self.processes[sender] = sock
        print("I know these guys", self.processes)
    
    def start_time(self):
        self.start = time.time()
    
    def time_expired(self):
        return time.time() - self.start > self.exp_time
    
    def all_accessed(self):
        return self.accessed == len(self.participants)
    
    def check_stop_conditions(self):
        if self.automode:
            return self.time_expired()
        else:
            return self.time_expired() or self.all_accessed()
    
    def mainloop(self):
        register = EventRegister()
        messages = queue.Queue()
        listeners: List[threading.Thread]= []
        stopped = []
        accessed = set()
        
        for proc_sock in self.processes.values():
            listeners.append(threading.Thread(target=listen_incoming, args=(proc_sock, messages, register, stopped, accessed)))
    
        for listener in listeners:
            listener.start()
        
        stop_sent = False
        if not self.automode:
            for part in self.participants:
                access_order = Message(sender=0, receiver=part, msg=ACCESS_ORDER)
                send(self.processes[part], access_order)
        while True:
            # print(f"Stopped {stopped}")
            if ((not self.automode and (len(accessed) == len(self.participants))) or self.time_expired()) and not stop_sent:
                for proc in self.processes:
                    stop = Message(sender=0, receiver=proc, msg=STOP_ORDER)
                    send(self.processes[proc], stop)
                stop_sent = True
            
            if stop_sent and (len(stopped) == NUM):
                print("closing")
                register.close_register()
                filepath = "./data/"+generate_random_string(10)
                register.write_on_csv(filepath)
                print(f"written on {filepath}")
                sys.exit(0)
            try:
                msg = deliver(messages=messages)
                if msg and not stop_sent:
                    send(self.processes[msg.receiver], msg)
            except Exception as e:
                pass
            # time.sleep(1)

if __name__ == "__main__":

    master = Master()
    master.create_listener(router_host=CONFIG["ROUTER_HOST"], router_port=CONFIG["ROUTER_PORT"])
    master.accept_processes()
    master.recognize_processes()
    master.start_time()
    master.mainloop()
