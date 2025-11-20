# callback_interface.py
def on_incoming_event(msg: dict):
    """
    replaced with battle engine code
    """
    print(f"[EVENT] Received: {msg.get('message_type')} | Data: {msg}")