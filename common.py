import struct

FMT = "!IIII"

def create_message(sender: int, receiver: int, msg_type: int, ts: int) -> bytes:
    return struct.pack(FMT, sender, receiver, msg_type, ts)

def read_message(msg: bytes) -> tuple:
    return struct.unpack(FMT, msg)