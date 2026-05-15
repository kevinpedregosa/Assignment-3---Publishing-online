# Kevin Noel Pedregosa
# pedregok@uci.edu
# 18447962

# ds_protocol.py
# Handles encoding and decoding of DSP protocol JSON messages.

import json
from collections import namedtuple

DataTuple = namedtuple('DataTuple', ['type', 'message', 'token'])

def extract_json(json_msg: str) -> DataTuple:
    """Parse a DSP server JSON response string into a DataTuple.

    Returns a DataTuple with type, message, and token fields.
    Returns None if the message cannot be decoded.
    """
    try:
        json_obj = json.loads(json_msg)
        response = json_obj['response']
        resp_type = response['type']
        message = response.get('message', '')
        token = response.get('token', '')
        return DataTuple(resp_type, message, token)
    except json.JSONDecodeError:
        print("ERROR: JSON cannot be decoded.")
        return None
    except KeyError:
        print("ERROR: Unexpected JSON structure.")
        return None
    
def format_join(username: str, password: str) -> str:
    """Return a JSON-formatted join message string."""
    obj = {
        "join": {
            "username": username,
            "password": password,
            "token": ""
        }
    }
    return json.dumps(obj)