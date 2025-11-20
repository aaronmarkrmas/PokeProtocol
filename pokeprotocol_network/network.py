# network.py
import socket
import threading
from typing import Callable, Optional, Tuple

class UDPSocket:
    def __init__(self, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 
        self.sock.bind(('0.0.0.0', port))
        self.port = port
        self.peer_addr: Optional[Tuple[str, int]] = None
        self.running = True
        self.on_packet_callbacks: list[Callable[[str, Tuple[str, int]], None]] = []

    def on_receive(self, callback: Callable[[str, Tuple[str, int]], None]):
        """Register a function to handle incoming packets"""
        self.on_packet_callbacks.append(callback)

    def start(self):
        """Start listening for packets in background thread"""
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)
                raw = data.decode('utf-8')
                for cb in self.on_packet_callbacks:
                    cb(raw, addr)
            except Exception as e:
                if self.running:
                    print(f"[NETWORK] Error receiving: {e}")

    def send(self,  data : str, addr=None):
        """Send message to specific address or default peer"""
        target = addr or self.peer_addr
        if not target:
            print("[NETWORK] Cannot send: no peer address known.")
            return
        try:
            self.sock.sendto(data.encode('utf-8'), target)
        except Exception as e:
            print(f"[NETWORK] Send failed: {e}")