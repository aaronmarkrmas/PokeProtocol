# main.py
import time
from threading import Timer
from network import UDPSocket
from network_reliability import ReliableSender
from handshake import connect_to_host, start_host
from callback_interface import on_incoming_event
from messages import parse_message, serialize_message
from pokemon import load_pokemon, get_sample_pokemon
from battle_engine import BattleEngine
from state_machine import BattleStateMachine
from chat_display import ChatDisplay

# === CONFIGURATION ===
IS_HOST = False           # True = Host, False = Joiner
HOST_IP = "127.0.0.1"     # Host IP (for Joiner)
BIND_PORT = 9001          # My listening port
HOST_PORT = 9000          # Host's port to send to

# === GLOBALS ===
udp = None
reliable = None
seed = None
handshake_done = False
battle_setup_sent = False
received_seq_numbers = set()  # For deduplicating incoming messages
pokemon_data = None
battle_engine = None
state_machine = None
chat_display = None


def packet_handler(raw: str, addr):
    """
    Called for every UDP packet received.
    Parses message, sends bare ack_number, and routes based on message_type.
    """
    global reliable, seed, udp, handshake_done, battle_setup_sent, received_seq_numbers
    global pokemon_data, battle_engine, state_machine, chat_display

    if pokemon_data is None:
        pokemon_data = load_pokemon('pokemon.csv')
        if not pokemon_data:
            pokemon_data = get_sample_pokemon()
        battle_engine = BattleEngine(pokemon_data)
        state_machine = BattleStateMachine(battle_engine)
        chat_display = ChatDisplay()

    if udp.peer_addr is None:
        udp.peer_addr = addr
        print(f"[INIT] Peer address set to {addr}")

    if reliable is None:
        reliable = ReliableSender(udp, addr)
        print("[INIT] ReliableSender created")

    msg = parse_message(raw)
    seq_str = msg.get("sequence_number")
    seq = int(seq_str) if seq_str else None

    if "ack_number" in msg:
        ack_num = int(msg["ack_number"])
        reliable.acknowledge(ack_num)
        return

    if seq is not None:
        if seq in received_seq_numbers:
            return
        received_seq_numbers.add(seq)

    if seq is not None:
        ack_raw = f"ack_number: {seq}\n"
        udp.send(ack_raw, addr)
        print(f"[SEND ACK #{seq}]")

    mtype = msg.get("message_type")

    # host handshake
    if mtype == "HANDSHAKE_REQUEST" and IS_HOST and not handshake_done:
        print("[HOST] Received HANDSHAKE_REQUEST")

        start_host(reliable)
        handshake_done = True

        # Prevent duplicate timers
        def send_host_setup():
            global battle_setup_sent
            if battle_setup_sent:
                return
            battle_setup_sent = True

            host_setup_msg = {
                "message_type": "BATTLE_SETUP",
                "pokemon_name": "Charmander",
                "communication_mode": "P2P",
                "stat_boosts": '{"special_attack_uses": 5, "special_defense_uses": 5}'
            }
            reliable.send(host_setup_msg)
            print("[HOST] Sent BATTLE_SETUP")

            # Start first attack
            time.sleep(0.5)
            attack_msg = {
                "message_type": "ATTACK_ANNOUNCE",
                "move_name": "Flamethrower"
            }
            reliable.send(attack_msg)
            print("[HOST] Sent ATTACK_ANNOUNCE: Flamethrower")

        Timer(0.1, send_host_setup).start()
        return

    # joiner handshake
    elif mtype == "HANDSHAKE_RESPONSE" and not IS_HOST:
        if seed is not None:
            return

        seed = int(msg["seed"])
        print(f"[JOINER] Received HANDSHAKE_RESPONSE with seed={seed}")

        def send_battle_setup():
            global battle_setup_sent
            if battle_setup_sent:
                return
            battle_setup_sent = True

            battle_setup_msg = {
                "message_type": "BATTLE_SETUP",
                "pokemon_name": "Pikachu",
                "communication_mode": "P2P",
                "stat_boosts": '{"special_attack_uses": 5, "special_defense_uses": 5}'
            }
            reliable.send(battle_setup_msg)
            print("[JOINER] Sent BATTLE_SETUP")

        Timer(0.2, send_battle_setup).start()
        return

    elif mtype == "BATTLE_SETUP":
        pkmn = msg.get("pokemon_name")
        print(f"[EVENT] Received BATTLE_SETUP from {pkmn}")
        on_incoming_event(msg)

    elif mtype == "ATTACK_ANNOUNCE":
        move = msg.get("move_name")
        print(f"[ACTION] Opponent used {move}!")

        defense_msg = {"message_type": "DEFENSE_ANNOUNCE"}
        reliable.send(defense_msg)
        print("[SENT] DEFENSE_ANNOUNCE")

        on_incoming_event(msg)

    elif mtype == "DEFENSE_ANNOUNCE":
        print("[ACTION] Defender acknowledged the attack.")
        on_incoming_event(msg)

    elif mtype == "CALCULATION_REPORT":
        attacker = msg.get("attacker")
        damage = msg.get("damage_dealt")
        hp_left = msg.get("defender_hp_remaining")
        print(f"[REPORT] {attacker} dealt {damage} damage. HP left: {hp_left}")
        on_incoming_event(msg)

    elif mtype == "CALCULATION_CONFIRM":
        print("[CONFIRM] Both peers agree on calculation.")
        on_incoming_event(msg)

    elif mtype == "RESOLUTION_REQUEST":
        attacker = msg.get("attacker")
        damage = msg.get("damage_dealt")
        hp_left = msg.get("defender_hp_remaining")
        print(f"[RESOLVE] Discrepancy: {attacker} dealt {damage}, HP left: {hp_left}")
        on_incoming_event(msg)

    elif mtype == "GAME_OVER":
        winner = msg.get("winner")
        loser = msg.get("loser")
        print(f"[GAME OVER] {winner} defeated {loser}!")
        on_incoming_event(msg)

    elif mtype == "CHAT_MESSAGE":
        sender = msg.get("sender_name", "Unknown")
        content_type = msg.get("content_type")
        if content_type == "TEXT":
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")
        else:
            print(f"[CHAT] {sender} sent a sticker.")
        on_incoming_event(msg)

    else:
        on_incoming_event(msg)


# main program
if __name__ == "__main__":

    udp = UDPSocket(BIND_PORT)
    udp.on_receive(packet_handler)
    udp.start()

    print(f"Started on port {BIND_PORT}. Role: {'Host' if IS_HOST else 'Joiner'}")

    if IS_HOST:
        print("Waiting for joiner...")
    else:
        time.sleep(1)
        temp_sender = ReliableSender(udp, (HOST_IP, HOST_PORT))
        connect_to_host(temp_sender)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        udp.running = False
