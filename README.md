# PokeProtocol
A peer-to-peer Pokémon battle simulator built with Python, featuring reliable UDP networking and turn-based combat mechanics.

PokeProtocol is a distributed battle system that allows two players to engage in Pokémon battles over a network. The system uses a custom UDP-based protocol with reliability guarantees, ensuring synchronized game state between peers without requiring a central server. 

It delivers a complete peer-to-peer battle experience with a reliable UDP protocol featuring ACK-based confirmation, automatic retransmission, and message deduplication. The battle system implements turn-based combat with authentic Pokémon mechanics including type effectiveness, stat-based damage calculation, and HP management. Deterministic RNG using shared seeds ensures both players experience identical battle outcomes, while a state machine protocol with calculation verification prevents desynchronization. Players can communicate through real-time chat, receive automatic battle announcements, and enjoy clear turn indicators throughout the match.


to run network side locally: 

navigate to folder 

in main: 

    FOR HOST CONFIG: 

    IS_HOST = True          # True = Host, False = Joiner
    HOST_IP = "127.0.0.1"     # Host IP (for Joiner)
    BIND_PORT = 9000          # My listening port
    HOST_PORT = 9000          # Host's port to send to

run the main file to run host 

open another cmd 

edit main file to: 

    IS_HOST = False          # True = Host, False = Joiner
    HOST_IP = "127.0.0.1"     # Host IP (for Joiner)
    BIND_PORT = 9001          # My listening port
    HOST_PORT = 9000          # Host's port to send to

run the main file in the second cmd to run joiner 