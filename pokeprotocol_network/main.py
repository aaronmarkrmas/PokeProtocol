# main.py
import time
import os
from threading import Thread
from collections import deque

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
BIND_PORT = 9001   # My listening port
HOST_PORT = 9000          # Host's port to send to

# === GLOBALS ===
udp = None
reliable = None
seed = None
handshake_done = False

my_setup_sent = False
opponent_setup_received = False

received_seq_numbers = set()
received_seq_order = deque(maxlen=4096)

pokemon_data = None
battle_engine = None
state_machine = None
chat_display = None

my_turn = IS_HOST

game_over = False

# Pokemon tracking
my_pokemon_name = None
opponent_pokemon_name = None


def _add_seq_if_new(seq: int) -> bool:
    """
    Add a sequence number to dedup cache if new.
    Returns True if it's a duplicate; False if newly added.
    """
    if seq in received_seq_numbers:
        return True
    if len(received_seq_numbers) >= received_seq_order.maxlen:
        oldest = received_seq_order.popleft()
        if oldest in received_seq_numbers:
            received_seq_numbers.remove(oldest)
    received_seq_numbers.add(seq)
    received_seq_order.append(seq)
    return False


def _print_help():
    """Print available CLI commands."""
    print("\n=== Available Commands ===")
    print("  setup [PokemonName]      -> Send your BATTLE_SETUP (interactive if no name provided)")
    print("  attack <MoveName>        -> Send ATTACK_ANNOUNCE on your turn")
    print("  chat <message>           -> Send a chat message")
    print("  help                     -> Show this help message")
    print("  quit                     -> Exit the application")
    print("==========================\n")


def _prompt_turn():
    """Display turn status and available commands."""
    if game_over:
        print("[GAME] Game has ended. Type 'quit' to exit.")
        return

    if not (my_setup_sent and opponent_setup_received):
        print("\n[INFO] Both players must send BATTLE_SETUP before the battle starts.")
        print("       Use: setup [PokemonName]")
        return

    if my_turn:
        print("\n[TURN] *** It's YOUR turn! ***")
        print("       Commands: attack <MoveName> | chat <message> | quit")
    else:
        print("\n[TURN] Waiting for opponent's move...")
        print("       (You can still: chat <message> | quit)")


def _maybe_prompt_after_setup():
    """Prompt only after both setups exchanged."""
    if my_setup_sent and opponent_setup_received:
        _prompt_turn()


def _flip_turn():
    """Flip turn ownership and prompt."""
    global my_turn
    my_turn = not my_turn
    _prompt_turn()


def _send_setup_interactive(default_name: str = None):
    """
    Prompt user for setup fields and send BATTLE_SETUP.
    """
    global reliable, my_setup_sent, my_pokemon_name, battle_engine
    if reliable is None:
        print("[WARN] Not connected yet. For Host, wait for a joiner to connect first.")
        return
    if my_setup_sent:
        print("[INFO] You have already sent your setup.")
        return

    # Gather inputs
    if default_name:
        pokemon_name = default_name.strip()
    else:
        try:
            pokemon_name = input("Enter your Pokemon name: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[WARN] Setup cancelled.")
            return

    if not pokemon_name:
        print("[WARN] Pokemon name cannot be empty.")
        return

    my_pokemon_name = pokemon_name

    if battle_engine:
        battle_engine.set_pokemon("my_pokemon", pokemon_name)
        battle_engine.is_my_turn = IS_HOST  # Host goes first

    try:
        boosts = input("Enter stat_boosts JSON (or press Enter for default): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[WARN] Setup cancelled.")
        return

    if not boosts:
        boosts = '{"special_attack_uses": 5, "special_defense_uses": 5}'

    communication_mode = "P2P"

    battle_setup_msg = {
        "message_type": "BATTLE_SETUP",
        "pokemon_name": pokemon_name,
        "communication_mode": communication_mode,
        "stat_boosts": boosts
    }
    reliable.send(battle_setup_msg)
    my_setup_sent = True
    print(f"[YOU] Sent BATTLE_SETUP for {pokemon_name}")
    _maybe_prompt_after_setup()


def _send_attack(move_name: str):
    """
    Send ATTACK_ANNOUNCE only when it's our turn and setups are complete.
    """
    global reliable, my_turn, state_machine
    if reliable is None:
        print("[WARN] Not connected yet.")
        return
    if not (my_setup_sent and opponent_setup_received):
        print("[WARN] Both BATTLE_SETUP messages must be exchanged before attacking.")
        print("       Use: setup [PokemonName]")
        return
    if not my_turn:
        print("[WARN] Not your turn. Wait for opponent's move.")
        return
    move_name = (move_name or "").strip()
    if not move_name:
        print("[WARN] Move name required. Usage: attack <MoveName>")
        return

    # Store attack data in state machine
    if state_machine:
        state_machine.current_turn_data = {
            'move_name': move_name,
            'is_my_attack': True
        }

    attack_msg = {
        "message_type": "ATTACK_ANNOUNCE",
        "move_name": move_name
    }
    reliable.send(attack_msg)
    print(f"[YOU] Sent ATTACK_ANNOUNCE: {move_name}")


def _send_chat(text: str):
    """Send a chat message."""
    global reliable
    if reliable is None:
        print("[WARN] Not connected yet.")
        return
    text = (text or "").strip()
    if not text:
        print("[WARN] Empty chat message.")
        return
    msg = {
        "message_type": "CHAT_MESSAGE",
        "sender_name": "Host" if IS_HOST else "Joiner",
        "content_type": "TEXT",
        "message_text": text
    }
    reliable.send(msg)
    print("[YOU] Chat sent.")


def _cli_loop():
    """
    CLI loop in its own thread for user commands:
      - setup [PokemonName]
      - attack <MoveName>
      - chat <message>
      - help
      - quit
    """
    print("\n[CLI] Ready. Type 'help' to see available commands.\n")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[CLI] Exiting...")
            os._exit(0)

        if not line:
            continue

        low = line.lower()

        if low in ("help", "?"):
            _print_help()
            continue

        if low in ("quit", "exit"):
            print("[CLI] Quitting...")
            os._exit(0)

        if low.startswith("setup"):
            parts = line.split(" ", 1)
            name = parts[1].strip() if len(parts) > 1 else None
            _send_setup_interactive(name)
            continue

        if low.startswith("attack "):
            move = line[7:].strip()
            _send_attack(move)
            continue

        if low.startswith("chat "):
            msg = line[5:].strip()
            _send_chat(msg)
            continue

        print("[CLI] Unknown command. Type 'help' for a list of commands.")


def packet_handler(raw: str, addr):
    """
    Called for every UDP packet received.
    Parses message, sends ACK, and routes based on message_type.
    """
    global reliable, seed, udp, handshake_done
    global pokemon_data, battle_engine, state_machine, chat_display
    global opponent_setup_received, game_over, my_pokemon_name, opponent_pokemon_name

    if pokemon_data is None:
        pokemon_data = load_pokemon('pokemon.csv')
        if not pokemon_data:
            pokemon_data = get_sample_pokemon()
        battle_engine = BattleEngine(pokemon_data)
        state_machine = BattleStateMachine(battle_engine)
        chat_display = ChatDisplay()

    # Establish peer and reliable sender if not set
    if udp.peer_addr is None:
        udp.peer_addr = addr
        print(f"[INIT] Peer address set to {addr}")

   
    if reliable is None:
        reliable = ReliableSender(udp, addr)
        print("[INIT] ReliableSender created")

    msg = parse_message(raw)

    if "ack_number" in msg:
        try:
            ack_num = int(msg["ack_number"])
        except ValueError:
            return
        reliable.acknowledge(ack_num)
        return

    seq = None
    seq_str = msg.get("sequence_number")
    if seq_str is not None:
        try:
            seq = int(seq_str)
        except ValueError:
            seq = None

    if seq is not None:
        if _add_seq_if_new(seq):
            return

    # Send ACK for any message with a sequence_number
    if seq is not None:
        ack_msg = {
            "message_type": "ACK",
            "ack_number": seq
        }
        udp.send(serialize_message(ack_msg), addr)
        print(f"[SEND ACK #{seq}]")

    mtype = msg.get("message_type")

    #Host handshake
    if mtype == "HANDSHAKE_REQUEST" and IS_HOST and not handshake_done:
        print("[HOST] Received HANDSHAKE_REQUEST")
        start_host(reliable)
        handshake_done = True
        print("[HOST] Handshake complete. Use 'setup [PokemonName]' to send your BATTLE_SETUP.")
        return

    #Joiner handshake 
    elif mtype == "HANDSHAKE_RESPONSE" and not IS_HOST and not handshake_done:
        try:
            seed_val = int(msg["seed"])
        except (KeyError, ValueError):
            print("[JOINER] Invalid or missing seed in HANDSHAKE_RESPONSE")
            return

        seed = seed_val
        handshake_done = True
        
        # Pass to state machine to set seed
        if state_machine:
            state_machine.handle_incoming_message(msg)
        
        print(f"[JOINER] Received HANDSHAKE_RESPONSE with seed={seed}")
        print("[JOINER] Use 'setup [PokemonName]' to send your BATTLE_SETUP.")
        return


    elif mtype == "BATTLE_SETUP":
        pkmn = msg.get("pokemon_name", "Unknown")
        opponent_setup_received = True
        opponent_pokemon_name = pkmn
        print(f"[EVENT] Received BATTLE_SETUP from opponent: {pkmn}")
        
        # Pass to state machine
        if state_machine:
            response = state_machine.handle_incoming_message(msg)
            if response:
                reliable.send(response)
        
        on_incoming_event(msg)
        _maybe_prompt_after_setup()

    elif mtype == "ATTACK_ANNOUNCE":
        move = msg.get("move_name", "Unknown Move")
        print(f"[ACTION] Opponent announced: {move}")
        is_opponent_attack = not state_machine.current_turn_data.get('is_my_attack', False)

        turn_result = battle_engine.handle_attack_announce(
                    state_machine.current_turn_data['move_name'], 
                    is_opponent_attack=is_opponent_attack
                )
        if state_machine:
            response = state_machine.handle_incoming_message(msg)
            if response:
                reliable.send(response)
                print(f"[SENT] {response['message_type']}")
                
                if response['message_type'] == 'DEFENSE_ANNOUNCE':
                    calc_report = state_machine.generate_calculation_report(turn_result)
                    if calc_report:
                        reliable.send(calc_report)
                        print(f"[SENT] {calc_report['message_type']}")
                        state_machine.transition_state("AWAITING_CALCULATION")
        
        on_incoming_event(msg)

    elif mtype == "DEFENSE_ANNOUNCE":
        print("[ACTION] Defender acknowledged the attack.")
        
        if state_machine:
            response = state_machine.handle_incoming_message(msg)
            if response:
                reliable.send(response)
                print(f"[SENT] {response['message_type']}")
        
        on_incoming_event(msg)

    elif mtype == "CALCULATION_REPORT":
        attacker = msg.get("attacker", "Unknown")
        damage = msg.get("damage_dealt", "?")
        hp_left = msg.get("defender_hp_remaining", "?")
        print(f"[REPORT] {attacker} dealt {damage} damage. HP left: {hp_left}")
        
        if state_machine:
            response = state_machine.handle_incoming_message(msg)
            if response:
                reliable.send(response)
                print(f"[SENT] {response['message_type']}")
        
        on_incoming_event(msg)

    elif mtype == "CALCULATION_CONFIRM":
        print("[CONFIRM] Both peers agree on calculation.")
        
        if state_machine:
            state_machine.handle_incoming_message(msg)
        
        on_incoming_event(msg)
        _flip_turn()

    elif mtype == "RESOLUTION_REQUEST":
        attacker = msg.get("attacker", "Unknown")
        damage = msg.get("damage_dealt", "?")
        hp_left = msg.get("defender_hp_remaining", "?")
        print(f"[RESOLVE] Discrepancy: {attacker} dealt {damage}, HP left: {hp_left}")
        
        if state_machine:
            response = state_machine.handle_incoming_message(msg)
            if response:
                reliable.send(response)
                print(f"[SENT] {response['message_type']}")
        
        on_incoming_event(msg)

    elif mtype == "GAME_OVER":
        winner = msg.get("winner", "Unknown")
        loser = msg.get("loser", "Unknown")
        game_over = True
        print(f"\n{'='*50}")
        print(f"[GAME OVER] {winner} defeated {loser}!")
        print(f"{'='*50}\n")
        on_incoming_event(msg)

    elif mtype == "CHAT_MESSAGE":
        sender = msg.get("sender_name", "Unknown")
        content_type = msg.get("content_type", "TEXT")
        if content_type == "TEXT":
            text = msg.get("message_text", "")
            print(f"[CHAT] {sender}: {text}")
        elif content_type == "STICKER":
            print(f"[CHAT] {sender} sent a sticker (not displayed).")
        else:
            print(f"[CHAT] {sender} sent unknown content type: {content_type}")
        on_incoming_event(msg)

    else:
        print(f"[DEBUG] Received unhandled message type: {mtype}")
        on_incoming_event(msg)


# === MAIN PROGRAM ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PokeProtocol Battle System")
    print("="*60)
    print(f"  Role: {'HOST' if IS_HOST else 'JOINER'}")
    print(f"  Bind Port: {BIND_PORT}")
    if not IS_HOST:
        print(f"  Host Address: {HOST_IP}:{HOST_PORT}")
    print("="*60 + "\n")

    # Initialize UDP socket
    udp = UDPSocket(BIND_PORT)
    udp.on_receive(packet_handler)
    udp.start()

    print(f"[NETWORK] UDP socket started on port {BIND_PORT}")

    if IS_HOST:
        print("[HOST] Waiting for joiner to connect...")
        print("[HOST] Once connected, use 'setup [PokemonName]' to begin.\n")
    else:
        print("[JOINER] Connecting to host...")
        time.sleep(0.5)  # Brief delay to ensure socket is ready
        
        reliable = ReliableSender(udp, (HOST_IP, HOST_PORT))
        udp.peer_addr = (HOST_IP, HOST_PORT)  # Set peer address early
        
        connect_to_host(reliable)  
        print("[JOINER] Handshake request sent. Waiting for response...\n")

    cli_thread = Thread(target=_cli_loop, daemon=True)
    cli_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Received interrupt signal...")
        print("[SHUTDOWN] Closing connections...")
        if udp:
            udp.running = False
        print("[SHUTDOWN] Goodbye!")
        os._exit(0)