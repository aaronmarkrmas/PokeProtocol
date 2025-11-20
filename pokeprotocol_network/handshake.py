# handshake.py
import random

_handshake_seed = None
_handshake_done = False
_joiner_handshake_sent = False


def start_host(reliable_sender) -> int:
    """
    Host:
    - Generates seed once
    - Sends HANDSHAKE_RESPONSE only once
    - Prevents duplicate responses
    """
    global _handshake_seed, _handshake_done

    if _handshake_done:
        return _handshake_seed

    if _handshake_seed is None:
        _handshake_seed = random.randint(10000, 99999)
        print(f"[HOST] Generated seed: {_handshake_seed}")

    _handshake_done = True

    msg = {
        "message_type": "HANDSHAKE_RESPONSE",
        "seed": str(_handshake_seed)
    }
    reliable_sender.send(msg)

    return _handshake_seed



def connect_to_host(reliable_sender):
    """
    Joiner:
    - Sends HANDSHAKE_REQUEST only once
    - Prevents multiple handshake floods
    """
    global _joiner_handshake_sent

    if _joiner_handshake_sent:
        return  # do not resend handshake unless user resets manually

    _joiner_handshake_sent = True

    msg = {"message_type": "HANDSHAKE_REQUEST"}
    reliable_sender.send(msg)
    print("[JOINER] Sent HANDSHAKE_REQUEST")
