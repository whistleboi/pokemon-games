"""A co-op session over the network. HostSession and GuestLink are polled once a frame by the game; nothing about
the map or battles yet, only who's in. Guests get nothing but "pending" until the host allows them."""
import secrets
import time

from src.coop import admission as adm
from src.net import discovery, protocol, transport

GRACE_SECONDS = 120.0


class HostSession:
    def __init__(self, name, password, seats=1, port=None, announce=True, clock=time.monotonic, discovery_port=discovery.PORT):
        self.name, self.clock = name, clock
        self.admission = adm.Admission(password, seats)
        self.server = transport.Server(port=port)
        self.port = self.server.port
        self.announcer = discovery.Announcer(name, self.port, discovery_port) if announce else None
        self.nonces = {}    # connection -> nonce
        self.requests = {}  # request id -> connection
        self.conn_rid = {}
        self.names = {}     # request id -> display name
        self.guests = {}    # pid -> {"name", "cid", "token", "left_at"}
        self.conn_pid = {}
        self.events = []    # for the game: ("request", rid, name), ("joined", pid, name), ("left", pid, name)...
        self._next_pid = 1

    # ---------------------------------------------------------------- what the host's screens use
    def set_open(self, on):
        self.admission.open = bool(on)

    def waiting(self):
        return [(r, p["name"]) for r, p in sorted(self.admission.pending.items())]

    def allow(self, rid):
        cid = self.requests.pop(rid, None)
        name = self.names.pop(rid, "Friend")
        if not self.admission.decide(rid, True) or cid is None:
            return None
        self.conn_rid.pop(cid, None)
        return self._admit(cid, name)

    def deny(self, rid):
        cid = self.requests.pop(rid, None)
        self.names.pop(rid, None)
        if self.admission.decide(rid, False) and cid is not None:
            self.conn_rid.pop(cid, None)
            self._refuse(cid, "denied")

    def _admit(self, cid, name):
        pid, self._next_pid = self._next_pid, self._next_pid + 1
        token = secrets.token_hex(24)
        self.guests[pid] = {"name": name, "cid": cid, "token": token, "left_at": None}
        self.conn_pid[cid] = pid
        self.server.send(cid, {"t": "join_result", "status": "allowed", "pid": pid, "token": token})
        self.events.append(("joined", pid, name))
        return pid

    def send(self, pid, msg):
        g = self.guests.get(pid)
        return bool(g and g["cid"] is not None and self.server.send(g["cid"], msg))

    def kick(self, pid):
        g = self.guests.pop(pid, None)
        if g is None:
            return
        if g["cid"] is not None:
            self.conn_pid.pop(g["cid"], None)
            self.server.send(g["cid"], {"t": "bye", "reason": "removed"})
            self.server.drop(g["cid"])
        self.admission.release()
        self.events.append(("gone", pid, g["name"]))

    def close(self):
        if self.announcer:
            self.announcer.close()
        self.server.close()

    # ---------------------------------------------------------------- every frame
    def poll(self):
        now = self.clock()
        for kind, cid, data in self.server.poll():
            if kind == "msg":
                self._message(cid, data, now)
            elif kind == "close":
                self._closed(cid, now)
        for rid in self.admission.expire(now):
            cid = self.requests.pop(rid, None)
            self.names.pop(rid, None)
            if cid is not None:
                self.conn_rid.pop(cid, None)
                self._refuse(cid, "expired")
        for pid, g in list(self.guests.items()):
            if g["left_at"] is not None and now - g["left_at"] >= GRACE_SECONDS:
                del self.guests[pid]
                self.admission.release()
                self.events.append(("gone", pid, g["name"]))
        out, self.events = self.events, []
        return out

    def _closed(self, cid, now):
        self.nonces.pop(cid, None)
        rid = self.conn_rid.pop(cid, None)
        if rid is not None:
            self.requests.pop(rid, None)
            self.names.pop(rid, None)
            self.admission.cancel(rid)
        pid = self.conn_pid.pop(cid, None)
        if pid is not None and pid in self.guests:
            self.guests[pid].update(cid=None, left_at=now)
            self.events.append(("left", pid, self.guests[pid]["name"]))

    def _message(self, cid, msg, now):
        t = msg["t"]
        pid = self.conn_pid.get(cid)
        if t == "hello" and pid is None:
            self._hello(cid, msg)
        elif t == "join_request" and pid is None and cid not in self.conn_rid:
            self._join(cid, msg, now)
        elif t == "reconnect" and pid is None:
            self._reconnect(cid, msg)
        elif t == "intent" and pid is not None and "ping" in msg:  # (the link's own check: see GuestLink.poll)
            self.guests[pid]["ms"] = msg.get("ms")
            self.server.send(cid, {"t": "state", "pong": msg["ping"]})
        elif t == "intent" and pid is not None:
            self.events.append(("intent", pid, msg))
        elif t == "bye" and pid is not None:
            self.kick(pid)

    def _refuse(self, cid, status):
        self.server.send(cid, {"t": "join_result", "status": status})

    def _hello(self, cid, msg):
        if msg.get("v") != protocol.VERSION:
            return self._refuse(cid, "version")
        if not self.admission.open:
            return self._refuse(cid, "closed")
        if msg.get("session") != self.name:
            return self._refuse(cid, "invalid")
        nonce = self.admission.new_nonce()
        self.nonces[cid] = nonce
        self.server.send(cid, {"t": "challenge", "salt": self.admission.salt, "nonce": nonce})

    def _join(self, cid, msg, now):
        nonce = self.nonces.pop(cid, None)  # (each nonce is good for one try)
        if nonce is None:
            return self._refuse(cid, "invalid")
        conn = self.server.conns.get(cid)
        status, rid = self.admission.request(conn.peer if conn else "?", msg.get("name"), msg.get("proof"), nonce, now)
        if status != "pending":
            return self._refuse(cid, status)
        self.requests[rid], self.conn_rid[cid] = cid, rid
        self.names[rid] = self.admission.pending[rid]["name"]
        self.events.append(("request", rid, self.names[rid]))
        self._refuse(cid, "pending")

    def _reconnect(self, cid, msg):
        token = msg.get("token")
        for pid, g in self.guests.items():
            if isinstance(token, str) and secrets.compare_digest(g["token"], token):
                if g["cid"] is not None:
                    self.conn_pid.pop(g["cid"], None)
                    self.server.drop(g["cid"], "replaced")
                g.update(cid=cid, left_at=None)
                self.conn_pid[cid] = pid
                self.server.send(cid, {"t": "join_result", "status": "allowed", "pid": pid, "token": token})
                self.events.append(("back", pid, g["name"]))
                return
        self._refuse(cid, "invalid")


def find_host(session, address=""):
    """(ip, port) for a session: by the address typed ("10.0.0.5" or "10.0.0.5:47475"), else by its name on the
    network. None if it can't be found. (Blocks for a moment: call it off the main thread.)"""
    address = (address or "").strip()
    if address:
        ip, _, port = address.partition(":")
        return ip, int(port) if port.isdigit() else transport.GAME_PORT
    return discovery.find(session)


class GuestLink:
    """status: connecting, pending, allowed, or a refusal (denied, expired, invalid, closed, full, rate_limited, version)."""

    def __init__(self, host, port, session, password, name, token=None):
        self.session, self.password, self.name, self.token = session, password, name, token
        self.host, self.port = host, port
        self.client = transport.Client(host, port)
        self.status, self.pid, self.lost = "connecting", None, False
        self.inbox = []
        self.ms, self._ping_at = None, 0.0  # (how long a message takes there and back)
        if token:
            self.client.send_host({"t": "reconnect", "token": token})
        else:
            self.client.send_host({"t": "hello", "v": protocol.VERSION, "session": session})

    def poll(self):
        for kind, _cid, data in self.client.poll():
            if kind == "close":
                self.lost = True
            elif kind == "msg":
                self._message(data)
        now = time.monotonic()
        if self.status == "allowed" and not self.lost and now - self._ping_at >= 1.0:
            self._ping_at = now
            self.client.send_host({"t": "intent", "ping": now, "ms": self.ms})
        out, self.inbox = self.inbox, []
        return out

    def _message(self, msg):
        t = msg["t"]
        if t == "challenge":
            try:
                given = adm.proof(self.password, msg["salt"], msg["nonce"])
            except (KeyError, TypeError, ValueError):
                self.status = "invalid"
                return
            self.client.send_host({"t": "join_request", "name": self.name, "proof": given})
            self.password = None  # (done with it)
        elif t == "join_result":
            self.status = str(msg.get("status"))
            if self.status == "allowed":
                self.pid, self.token = msg.get("pid"), msg.get("token")
        elif t == "bye":
            self.status = "removed"
        elif t == "state" and "pong" in msg:
            self.ms = int((time.monotonic() - float(msg["pong"])) * 1000)
        else:
            self.inbox.append(msg)

    def send_intent(self, data):
        return self.client.send_host(dict(data, t="intent"))

    def leave(self):
        self.client.send_host({"t": "bye"})
        self.client.close()

    def close(self):
        self.client.close()
