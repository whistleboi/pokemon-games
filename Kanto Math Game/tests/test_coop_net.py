"""Co-op admission and networking, over real local sockets (python tests/test_coop_net.py)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.coop import admission as adm  # noqa: E402
from src.coop import session as sess  # noqa: E402
from src.net import discovery, protocol  # noqa: E402

fails = 0
count = 0


def check(ok, what):
    global fails, count
    count += 1
    if not ok:
        fails += 1
        print("FAIL", what)


class Clock:
    t = 1000.0

    def __call__(self):
        return self.t


def pump(host, guests, seconds=2.0, until=None):
    """Poll both sides until until() is true; the host's events are collected."""
    seen = []
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        seen += host.poll()
        for g in guests:
            g.poll()
        if until and until():
            seen += host.poll()
            break
        time.sleep(0.005)
    return seen


def link(host, password="pass", name="Sam", session="Fun"):
    return sess.GuestLink("127.0.0.1", host.port, session, password, name)


# ---- the password and the seats, with no network
a = adm.Admission("secret", seats=1)
nonce = a.new_nonce()
good = adm.proof("secret", a.salt, nonce)
check(a.request("p", "Sam", adm.proof("wrong", a.salt, nonce), nonce, 0.0) == ("invalid", None), "wrong password refused")
status, rid = a.request("p", "Sam", good, nonce, 0.0)
check(status == "pending" and a.taken == 1, "right password only waits; the seat is held")
check(a.request("q", "Pat", good, nonce, 0.0) == ("full", None), "last seat: only one request holds it")
check(a.decide(rid, False) and a.taken == 0 and not a.decide(rid, True), "deny frees the seat, and can't be undone")
status, rid = a.request("p", "Sam", good, nonce, 0.0)
check(a.expire(adm.PENDING_SECONDS + 1) == [rid] and a.taken == 0, "an unanswered request expires")
b = adm.Admission("x")
n = b.new_nonce()
for _ in range(adm.MAX_FAILS):
    b.request("p", "A", "nope", n, 0.0)
check(b.request("p", "A", adm.proof("x", b.salt, n), n, 1.0)[0] == "rate_limited", "too many wrong tries: locked out")
check(b.request("other", "A", adm.proof("x", b.salt, n), n, 1.0)[0] == "pending", "...only that address")
check(b.request("p", "A", adm.proof("x", b.salt, n), n, adm.FAIL_WINDOW + 1)[0] != "rate_limited", "...for a while")
check(adm.clean_name("\n" + "a" * 40) == "a" * 16 and adm.clean_name("  ") == "Friend", "display names are tidied")
c = adm.Admission("x", seats=1)
c.open = False
n = c.new_nonce()
check(c.request("p", "A", adm.proof("x", c.salt, n), n, 0.0)[0] == "closed", "closed to hop-ins")

# ---- messages
check(protocol.decode(protocol.encode({"t": "ping"})[:-1]) == {"t": "ping"}, "messages round-trip")
for bad in (b"[1]", b"{", b'{"t":"nope"}', b"\xff"):
    try:
        protocol.decode(bad)
        check(False, f"bad message accepted {bad}")
    except protocol.BadMessage:
        check(True, "bad message refused")

# ---- over real sockets
clock = Clock()
host = sess.HostSession("Fun", "pass", seats=1, announce=False, clock=clock)
g1 = link(host)
ev = pump(host, [g1], until=lambda: g1.status == "pending")
check(g1.status == "pending" and any(e[0] == "request" for e in ev), "right password: pending, and the host is asked")
check(g1.pid is None and host.waiting() == [(1, "Sam")], "...nothing given to the guest yet")
check(g1.password is None, "the guest forgets the password once used")
g2 = link(host, name="Pat")
pump(host, [g2], until=lambda: g2.status not in ("connecting",))
check(g2.status == "full", "a second request for the last seat is told full")
g2.close()
host.deny(1)
pump(host, [g1], until=lambda: g1.status == "denied")
check(g1.status == "denied" and host.admission.taken == 0, "denied: told so, seat free")
g1.close()
g3 = link(host)
pump(host, [g3], until=lambda: g3.status == "pending")
check(g3.status == "pending", "a retry after Deny needs a fresh request")
g3.close()  # (gone while waiting)
pump(host, [], seconds=0.5, until=lambda: not host.waiting())
check(not host.waiting() and host.admission.taken == 0, "hanging up while waiting frees the seat")
g4 = link(host, password="bad")
pump(host, [g4], until=lambda: g4.status == "invalid")
check(g4.status == "invalid", "wrong password over the wire")
g4.close()
g5 = link(host, session="Other")
pump(host, [g5], until=lambda: g5.status == "invalid")
check(g5.status == "invalid", "wrong session name gets the same answer")
g5.close()
g6 = link(host)
pump(host, [g6], until=lambda: g6.status == "pending")
rid = host.waiting()[0][0]
clock.t += adm.PENDING_SECONDS + 1
pump(host, [g6], until=lambda: g6.status == "expired")
check(g6.status == "expired" and host.admission.taken == 0, "a request the host ignores expires")
g6.close()
pump(host, [], seconds=0.1)
g7 = link(host)
pump(host, [g7], until=lambda: g7.status == "pending")
rid = host.waiting()[0][0]
pid = host.allow(rid)
ev = pump(host, [g7], until=lambda: g7.status == "allowed")
check(g7.status == "allowed" and g7.pid == pid and bool(g7.token), "allowed: in, with a reconnect token")
host.send(pid, {"t": "state", "hi": 1})
got = []
end = time.monotonic() + 2
while time.monotonic() < end and not got:
    host.poll()
    got = g7.poll()
    time.sleep(0.005)
check(got and got[0].get("hi") == 1, "the host's messages reach the guest")
g7.send_intent({"do": "step"})
ev = pump(host, [g7], seconds=1, until=lambda: False) if False else []
end = time.monotonic() + 2
while time.monotonic() < end and not any(e[0] == "intent" for e in ev):
    ev += host.poll()
    time.sleep(0.005)
check(any(e[0] == "intent" and e[1] == pid and e[2].get("do") == "step" for e in ev), "the guest's intents reach the host")
host.set_open(False)
g8 = link(host)
pump(host, [g8], until=lambda: g8.status == "closed")
check(g8.status == "closed" and pid in host.guests, "closing hop-ins keeps the guest who's in")
g8.close()
host.set_open(True)
token = g7.token
g7.close()
ev = pump(host, [], seconds=1, until=lambda: host.guests[pid]["cid"] is None)
check(host.guests[pid]["cid"] is None and host.admission.taken == 1, "dropped: the seat is held")
back = sess.GuestLink("127.0.0.1", host.port, "Fun", "", "Sam", token=token)
ev = pump(host, [back], until=lambda: back.status == "allowed")
check(back.status == "allowed" and back.pid == pid and any(e[0] == "back" for e in ev), "the token gets them back in")
back.close()
pump(host, [], seconds=1, until=lambda: host.guests[pid]["cid"] is None)
bad = sess.GuestLink("127.0.0.1", host.port, "Fun", "", "Sam", token="0" * 48)
pump(host, [bad], until=lambda: bad.status == "invalid")
check(bad.status == "invalid", "a made-up token gets nothing")
bad.close()
clock.t += sess.GRACE_SECONDS + 1
ev = pump(host, [], seconds=0.2, until=lambda: pid not in host.guests)
check(pid not in host.guests and host.admission.taken == 0, "gone past the grace period: the seat frees")
host.close()

# ---- finding a session by name
h2 = sess.HostSession("Named", "pw", announce=True, discovery_port=47999)
where = discovery.find("Named", port=47999, targets=("127.0.0.1",))
check(where == ("127.0.0.1", h2.port), "found by its name on the network")
check(discovery.find("Nobody", timeout=0.4, port=47999, targets=("127.0.0.1",)) is None, "a name nobody hosts")
h2.close()

# ---- typed addresses; this device's real network address, not just loopback
check(sess.find_host("X", "10.0.0.5:1234") == ("10.0.0.5", 1234), "an address and port, typed")
check(sess.find_host("X", " 10.0.0.5 ") == ("10.0.0.5", 47475), "an address alone uses the game's port")
ips = discovery.local_ips()
check(all(not ip.startswith("127.") for ip in ips), "only addresses a friend could reach")
if ips:
    h3 = sess.HostSession("Lan", "pw", announce=True, discovery_port=47998)
    where = discovery.find("Lan", port=47998, targets=discovery.broadcast_targets())
    check(where is not None and where[1] == h3.port, "found through the network's broadcast")
    g = sess.GuestLink(ips[0], h3.port, "Lan", "pw", "Sam")
    pump(h3, [g], seconds=4, until=lambda: g.status == "pending")
    check(g.status == "pending", "reached over the real network address")
    h3.allow(h3.waiting()[0][0])
    pump(h3, [g], seconds=4, until=lambda: g.ms is not None)
    check(g.status == "allowed" and g.ms is not None, "connected, and the link's speed is measured")
    g.close()
    h3.close()

print(f"{count - fails}/{count} passed" if not fails else f"{fails} FAILED of {count}")
sys.exit(1 if fails else 0)
