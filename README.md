# PokeProtocol
A Peer-to-Peer Pokémon Battle Protocol (PokeProtocol) using UDP as its transport layer.


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