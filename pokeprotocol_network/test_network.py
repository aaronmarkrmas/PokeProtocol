from network import UDPSocket
import time

# Create two UDP sockets on different ports
socket_a = UDPSocket(5000)
socket_b = UDPSocket(5001)

# Define how each socket reacts when it receives a message
def handle_a(msg, addr):
    print(f"[A] Received from {addr}: {msg}")

def handle_b(msg, addr):
    print(f"[B] Received from {addr}: {msg}")

socket_a.on_receive(handle_a)
socket_b.on_receive(handle_b)

# Start both listeners
socket_a.start()
socket_b.start()

# Send test messages between them
socket_a.send("Hello from A!", ("127.0.0.1", 5001))
socket_b.send("Hello from B!", ("127.0.0.1", 5000))

# Keep the program running for a bit to receive messages
time.sleep(2)
