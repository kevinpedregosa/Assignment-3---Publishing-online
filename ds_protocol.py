# Kevin Noel Pedregosa
# pedregok@uci.edu
# 18447962

# ds_protocol.py
# Handles encoding and decoding of DSP protocol JSON messages.

import json
from collections import namedtuple

DataTuple = namedtuple('DataTuple', ['type', 'message', 'token'])