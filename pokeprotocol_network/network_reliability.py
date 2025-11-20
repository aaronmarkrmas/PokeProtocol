# reliability.py
import time
from threading import Timer, Lock
from typing import Dict
from messages import serialize_message
from network import UDPSocket

class ReliableSender:
    def __init__(self, udp_socket: UDPSocket, peer_addr):
        self.udp = udp_socket
        self.peer = peer_addr
        self.seq_num = 1
        self.outbox: Dict[int, Dict] = {} 

    def send(self, msg_dict: Dict[str, str]):
        """Send message reliably with sequence number and retry"""
        with self.lock:
            seq = self.seq_num
            msg_dict['sequence_number'] = str(seq)
            raw = serialize_message(msg_dict)

            #retry
            timer = Timer(0.5, self._retry, args=[seq])
            timer.daemon = True

            self.outbox[seq] = {"raw": raw, "retry": 0, "timer": timer}
            timer.start()
            self.udp.send(raw, self.peer)
            print(f"[SEND #{seq}] {msg_dict.get('message_type')}")
            self.seq_num += 1

    def acknowledge(self, ack_num: int):
        """Stop retries for acknowledged messages"""
        with self.lock:
            if ack_num in self.outbox:
                timer = self.outbox[ack_num]["timer"]
                timer.cancel()
                del self.outbox[ack_num]
                print(f"[ACK] Received for #{ack_num}")

    def _retry(self, seq):

        with self.lock:
            if seq not in self.outbox:
                return

            entry = self.outbox[seq]

            if entry["retry"] >= 3:
                print(f"[FAIL] Message #{seq} failed after 3 retries.")
                entry["timer"].cancel()
                del self.outbox[seq]
                return

            entry["timer"].cancel()

            self.udp.send(entry["raw"], self.peer)
            entry["retry"] += 1
            print(f"[RETRY #{seq}] Attempt {entry['retry']}")

            new_timer = Timer(0.5, self._retry, args=[seq])
            new_timer.daemon = True
            new_timer.start()
            entry["timer"] = new_timer