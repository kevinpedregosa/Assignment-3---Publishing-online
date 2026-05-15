# Kevin Noel Pedregosa
# pedregok@uci.edu
# 18447962

# ds_client.py
# Handles socket communication with the ICS 32 DSP server.

import socket
import time
import ds_protocol

def _connect(server: str, port: int):
    """Open a socket connection and return (client, send_file, recv_file).

    Returns None if the connection fails.
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server, port))
        send_file = client.makefile('w')
        recv_file = client.makefile('r')
        return client, send_file, recv_file
    except socket.error as e:
        print(f"ERROR: Could not connect to server. {e}")
        return None