"""Finding a session by its name on the local network (a UDP question; whoever hosts that name answers)."""
import json
import socket
import threading
import time

PORT = 47474


def local_ips():
    """This device's addresses on its networks (the ones a friend could reach)."""
    found = []
    try:  # (no packet is sent: this asks which network the system would use)
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("10.255.255.255", 1))
        found.append(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass
    try:
        found += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    out = []
    for ip in found:
        if ip not in out and not ip.startswith(("127.", "169.254.", "0.")):
            out.append(ip)
    return out


def broadcast_targets():
    """Where to ask: each network's own broadcast address (a PC with several networks only uses one for the general
    address), the general one, and this device (a second copy of the game on the same PC)."""
    out = [ip.rsplit(".", 1)[0] + ".255" for ip in local_ips()]
    return out + ["255.255.255.255", "127.0.0.1"]


class Announcer:
    """The host's side: answers "who has <name>?" with its game port."""

    def __init__(self, name, game_port, port=PORT):
        self.name, self.game_port, self.running = name, game_port, True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))
        self.sock.settimeout(0.5)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = json.loads(data.decode("utf-8"))
                if isinstance(msg, dict) and msg.get("who") == self.name:
                    reply = json.dumps({"have": self.name, "port": self.game_port}).encode("utf-8")
                    self.sock.sendto(reply, addr)
            except socket.timeout:
                continue
            except (OSError, ValueError):
                if not self.running:
                    return

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass


def find(name, timeout=1.5, port=PORT, targets=None):
    """(ip, game port) of the session called name, or None."""
    targets = targets or broadcast_targets()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.3)
        ask = json.dumps({"who": name}).encode("utf-8")
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            for t in targets:
                try:
                    sock.sendto(ask, (t, port))
                except OSError:
                    pass
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode("utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(msg, dict) and msg.get("have") == name and isinstance(msg.get("port"), int):
                return addr[0], msg["port"]
        return None
    finally:
        sock.close()
