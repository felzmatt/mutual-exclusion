import time
import datetime
import csv
from enum import Enum

from common.common import Message, REQUEST, RELEASE, ACK

def get_now():
    return time.time()

class EventType(Enum):
    START = 10
    END = 20
    CS_ACCESS = 1
    CS_LEAVE = 2
    CS_REQUESTED = 3
    PROC_STOPPED = 4
    MSG = 222
    def __str__(self):
        return self.name

class Event:
    counter = 0
    def __init__(self, evtype: EventType, procID: int, message: Message = None) -> None:
        
        self.real_clock = get_now()
        self.procID = procID
        # logical clock
        Event.counter += 1
        self.logical_clock = Event.counter
        self.evtype = evtype
        if self.evtype == EventType.MSG:
            # print("Creating a message event")
            self.msg_type = message.msg
            self.msg_receiver = message.receiver
            self.msg_ts = message.ts
            #self.anomaly = False
        else:
            self.msg_type = None
            self.msg_receiver = None
            self.msg_ts = None
            #self.anomaly = anomaly
    
    def tuplify(self):
        msg_type = ""
        if self.evtype == EventType.MSG:
            if self.msg_type == REQUEST:
                msg_type = "REQUEST"
            elif self.msg_type == RELEASE:
                msg_type = "RELEASE"
            elif self.msg_type == ACK:
                msg_type = "ACK"
            else:
                msg_type = "UNKNOWN"
        else:
            msg_type = self.msg_type
        return (self.procID, self.evtype, self.logical_clock, self.real_clock, msg_type, self.msg_receiver, self.msg_ts)

class EventRegister:
    def __init__(self):
        self.start = get_now()
        self.humandate_start = datetime.datetime.fromtimestamp(self.start).strftime("%Y-%m-%d %H:%M:%S")
        self.cs_events = []

    def insert_event(self, ev: Event):
        self.cs_events.append(ev)
    
    def close_register(self):
        self.end = get_now()
        self.humandate_end = datetime.datetime.fromtimestamp(self.end).strftime("%Y-%m-%d %H:%M:%S")
        self.total_time = self.end - self.start
        # print(self.cs_events)
    
    def write_on_csv(self, filepath: str):
        header = ["procID", "event_type", "logical_clock", "real_clock", "msg", "msg_receiver", "msg_ts"]
        with open(filepath, "w") as f:
            writer = csv.writer(f)
            # write row header
            writer.writerow(header)
            # write start event
            writer.writerow([0, "START", 0, self.start, None, None, None])

            # write actual data
            writer.writerows([ev.tuplify() for ev in self.cs_events])

            # write closing
            writer.writerow([0, "END", Event.counter + 1, self.end, None, None, None])
        