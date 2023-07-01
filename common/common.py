import struct

FMT = "!IIII"


def create_message(sender: int, receiver: int, msg_type: int, ts: int) -> bytes:
    # print(f"creo un messaggio per {receiver} da {sender} del tipo {msg_type} e ts {ts}")
    return struct.pack(FMT, sender, receiver, msg_type, ts)

def read_message(msg: bytes) -> tuple:
    return struct.unpack(FMT, msg)

def format_message(sender: int, receiver: int, msg_type: int, ts: int) -> str:
    return f"MSG: sender {sender}, receiver {receiver}, type {msg_type}, ts {ts}"

def display_message(sender: int, receiver: int, msg_type: int, ts = 0):
    print(sender, receiver, msg_type, ts)
    print("MANNAGGIA")
    if msg_type not in [10,20,30,99]:
        msgtype = "UNKNOWN"
    else:
        if msg_type == 10:
            msgtype = "REQ"
        
        elif msgtype == 20:
            msgtype = "ACK"
        
        elif msgtype == 30:
            msgtype = "REL"
        
        else:
            msgtype = "ENTER_CS"
    print("A TE")
    
    return f"{msgtype} FROM:{sender}"