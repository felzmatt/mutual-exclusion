import time
import datetime
import csv
from enum import Enum

def real_clock() -> int:
    return int(time.time())

class EventType(Enum):
    START = 10
    ACCESS = 1
    LEAVE = 2
    END = 20
    def __str__(self):
        return self.name

class Event:
    counter = 0
    def __init__(self, evtype: EventType, procID: int, anomaly: bool) -> None:
        
        self.ts = real_clock()
        self.procID = procID
        self.humandate = datetime.datetime.fromtimestamp(self.ts).strftime("%Y-%m-%d %H:%M:%S")
        self.evtype = evtype
        # logical clock
        Event.counter += 1
        self.logical_clock = Event.counter
        self.anomaly = anomaly

class EventRegister:
    def __init__(self):
        self.start = real_clock()
        self.humandate_start = datetime.datetime.fromtimestamp(self.start).strftime("%Y-%m-%d %H:%M:%S")
        self.cs_events = []

    def insert_event(self, ev: Event):
        self.cs_events.append(ev)
    
    def close_register(self):
        self.end = real_clock()
        self.humandate_end = datetime.datetime.fromtimestamp(self.end).strftime("%Y-%m-%d %H:%M:%S")
        self.total_time = self.end - self.start
    
    def write_on_csv(self, filepath: str):
        header = ["procID", "event_type", "cs_clock", "real_clock", "human_date", "anomaly"]
        with open(filepath, "w") as f:
            writer = csv.writer(f)
            # write row header
            writer.writerow(header)
            # write start event
            writer.writerow([None, "START", 0, self.start, self.humandate_start, False])

            # write actual data
            writer.writerows(self.cs_events)

            # write closing
            writer.writerow([None, "END", Event.counter + 1, self.end, self.humandate_end, False])
        