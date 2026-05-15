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


def _send_message(send_file, recv_file, message: str):
    """Send a message and return the parsed DataTuple response.

    Returns None if sending or parsing fails.
    """
    try:
        send_file.write(message + '\r\n')
        send_file.flush()
        response = recv_file.readline()
        return ds_protocol.extract_json(response)
    except Exception as e:
        print(f"ERROR: Failed to send message. {e}")
        return None


def _join(send_file, recv_file, username: str, password: str):
    """Send a join message and return the auth token on success.

    Returns None if join fails.
    """
    msg = ds_protocol.format_join(username, password)
    result = _send_message(send_file, recv_file, msg)
    if result is None:
        return None
    if result.type == 'ok':
        return result.token
    print(f"ERROR: Join failed. {result.message}")
    return None


def _send_post(send_file, recv_file, token: str, entry: str):
    """Send a post message. Returns True on success, False otherwise."""
    timestamp = str(time.time())
    msg = ds_protocol.format_post(token, entry, timestamp)
    result = _send_message(send_file, recv_file, msg)
    if result is None:
        return False
    if result.type == 'ok':
        return True
    print(f"ERROR: Post failed. {result.message}")
    return False


def _send_bio(send_file, recv_file, token: str, entry: str):
    """Send a bio message. Returns True on success, False otherwise."""
    timestamp = str(time.time())
    msg = ds_protocol.format_bio(token, entry, timestamp)
    result = _send_message(send_file, recv_file, msg)
    if result is None:
        return False
    if result.type == 'ok':
        return True
    print(f"ERROR: Bio failed. {result.message}")
    return False


def send(server: str, port: int, username: str, password: str,
         message: str, bio: str = None):
    """Join a DSP server and send a message, bio, or both.

    Returns True if all intended operations succeed, False otherwise.
    """
    try:
        connection = _connect(server, port)
        if connection is None:
            return False

        client, send_file, recv_file = connection

        try:
            token = _join(send_file, recv_file, username, password)
            if token is None:
                return False

            success = True

            if message and message.strip():
                if not _send_post(send_file, recv_file, token, message):
                    success = False

            if bio is not None and bio.strip():
                if not _send_bio(send_file, recv_file, token, bio):
                    success = False

            return success

        finally:
            send_file.close()
            recv_file.close()
            client.close()

    except Exception as e:
        print(f"ERROR: Unexpected error in send. {e}")
        return False