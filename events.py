import time

class Event:
    def __init__(self, observer: int, ev_type: str):
        self.ts = time.time()
        self.ev_type = ev_type
        self.observer = observer
    def tuplify(self):
        return (self.observer, self.ev_type, self.ts)