"""Co-op messages: one JSON object a line, each with its type in "t"."""
import json

VERSION = 1
MAX_LINE = 4 * 1024 * 1024  # (a floor's snapshot is the biggest thing sent)
TYPES = {"ping", "hello", "challenge", "join_request", "join_result", "reconnect", "bye", "state", "intent", "event"}


class BadMessage(ValueError):
    pass


def encode(msg):
    if not isinstance(msg, dict) or msg.get("t") not in TYPES:
        raise BadMessage("unknown message")
    return json.dumps(msg, separators=(",", ":")).encode("utf-8") + b"\n"


def decode(line):
    try:
        msg = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise BadMessage("not JSON") from e
    if not isinstance(msg, dict) or msg.get("t") not in TYPES:
        raise BadMessage("unknown message")
    return msg
