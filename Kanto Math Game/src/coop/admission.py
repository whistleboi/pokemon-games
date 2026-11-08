"""Who gets in: the password proves itself without crossing the network, then the host still says Allow or Deny.
No game state here; time is passed in, so all of it can be tested."""
import hashlib
import hmac
import secrets

PBKDF_ROUNDS = 60000
PENDING_SECONDS = 60.0
MAX_FAILS = 5
FAIL_WINDOW = 60.0


def derive(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF_ROUNDS)


def proof(password, salt_hex, nonce_hex):
    """What a guest sends: shows it knows the password, and can't be replayed (the nonce is new each time)."""
    return hmac.new(derive(password, salt_hex), bytes.fromhex(nonce_hex), hashlib.sha256).hexdigest()


def clean_name(text):
    text = "".join(c for c in str(text or "") if c.isprintable()).strip()[:16]
    return text or "Friend"


class Admission:
    def __init__(self, password, seats=1):
        self.password = password  # (host memory only, for Reveal: never saved, logged or sent)
        self.salt = secrets.token_hex(16)
        self.key = derive(password, self.salt)
        self.seats = seats          # (guests, not counting the host)
        self.open = True
        self.taken = 0
        self.pending = {}           # request id -> {"name", "peer", "at"}
        self.fails = {}             # peer -> [times]
        self._next = 1

    def set_password(self, password):
        self.password, self.salt = password, secrets.token_hex(16)
        self.key = derive(password, self.salt)

    def new_nonce(self):
        return secrets.token_hex(16)

    def _limited(self, peer, now):
        recent = [t for t in self.fails.get(peer, []) if now - t < FAIL_WINDOW]
        self.fails[peer] = recent
        return len(recent) >= MAX_FAILS

    def request(self, peer, name, given, nonce, now):
        """("pending", request id) or (a refusal, None): rate_limited, closed, invalid or full."""
        if self._limited(peer, now):
            return "rate_limited", None
        if not self.open:
            return "closed", None
        want = hmac.new(self.key, bytes.fromhex(nonce), hashlib.sha256).hexdigest()
        if not isinstance(given, str) or not hmac.compare_digest(want, given):
            self.fails.setdefault(peer, []).append(now)
            return "invalid", None
        self.expire(now)
        if self.taken >= self.seats:
            return "full", None
        self.taken += 1  # (the seat is held while the host decides)
        rid = self._next
        self._next += 1
        self.pending[rid] = {"name": clean_name(name), "peer": peer, "at": now}
        return "pending", rid

    def decide(self, rid, allow):
        """True if the request was still waiting. Allow keeps the seat; deny gives it back."""
        if self.pending.pop(rid, None) is None:
            return False
        if not allow:
            self.taken -= 1
        return True

    def cancel(self, rid):
        return self.decide(rid, False)

    def expire(self, now):
        """Requests nobody answered in time: their ids (the seats are freed)."""
        old = [r for r, p in self.pending.items() if now - p["at"] >= PENDING_SECONDS]
        for r in old:
            self.decide(r, False)
        return old

    def release(self):
        self.taken = max(0, self.taken - 1)
