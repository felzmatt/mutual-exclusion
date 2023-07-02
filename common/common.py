import struct

# from master
ACCESS_ORDER: int = 21
STOP_ORDER: int = 22
# to master
CS_REQUESTED: int = 151
CS_ENTERED: int = 153
CS_RELEASED: int = 155
STOPPED: int = 157
# among peers
REQUEST: int = 1
ACK: int = 2
RELEASE: int = 3

class Message:
    FMT = "!IIII"
    def __init__(self, sender: int, receiver: int, msg: int, ts: int = 0):
        self.sender = sender
        self.receiver = receiver
        self.msg = msg
        self.ts = ts
    
    def pack(self) -> bytes:
        return struct.pack(Message.FMT, self.sender, self.receiver, self.msg, self.ts)
    
    def __str__(self):
        return f"Message: {self.msg} with  ts={self.ts} [FROM: {self.sender}] [TO: {self.receiver}]"
    
def decode_message(data: bytes):
    return Message(*struct.unpack(Message.FMT, data))

def create_message(sender: int, receiver: int, msg_type: int, ts: int) -> bytes:
    return struct.pack(Message.FMT, sender, receiver, msg_type, ts)

def read_message(msg: bytes) -> tuple:
    return struct.unpack(Message.FMT, msg)

def format_message(sender: int, receiver: int, msg_type: int, ts: int) -> str:
    return f"MSG: sender {sender}, receiver {receiver}, type {msg_type}, ts {ts}"
