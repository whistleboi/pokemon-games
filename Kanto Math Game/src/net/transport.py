"""TCP for co-op. Background threads fill one queue; the game drains it with poll(), once a frame."""
import queue
import socket
import threading
import time

from src.net import protocol

PING_EVERY = 2.0
SILENT_LIMIT = 10.0
GAME_PORT = 47475


class _Conn:
    def __init__(self, sock, cid, peer):
        self.sock, self.cid, self.peer = sock, cid, peer
        self.lock = threading.Lock()
        self.last_rx = time.monotonic()
        self.alive = True


class _Endpoint:
    def __init__(self):
        self.inbox = queue.Queue()
        self.conns = {}
        self.running = True
        self._guard = threading.Lock()
        threading.Thread(target=self._heartbeat, daemon=True).start()

    def poll(self):
        """Everything that's happened since last time: ("open"|"msg"|"close", conn id, message or reason)."""
        out = []
        while True:
            try:
                out.append(self.inbox.get_nowait())
            except queue.Empty:
                return out

    def _add(self, sock, cid, peer):
        sock.settimeout(5.0)
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        conn = _Conn(sock, cid, peer)
        with self._guard:
            self.conns[cid] = conn
        self.inbox.put(("open", cid, None))
        threading.Thread(target=self._reader, args=(conn,), daemon=True).start()
        return conn

    def _reader(self, conn):
        buf = b""
        reason = "closed"
        while conn.alive and self.running:
            try:
                data = conn.sock.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                reason = "lost"
                break
            if not data:
                break
            conn.last_rx = time.monotonic()
            buf += data
            if len(buf) > protocol.MAX_LINE and b"\n" not in buf:
                reason = "too big"
                break
            bad = False
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = protocol.decode(line)
                except protocol.BadMessage:
                    bad = True
                    break
                if msg["t"] != "ping":
                    self.inbox.put(("msg", conn.cid, msg))
            if bad:
                reason = "bad message"
                break
        self._drop(conn, reason)

    def _drop(self, conn, reason):
        with self._guard:
            if not conn.alive:
                return
            conn.alive = False
            self.conns.pop(conn.cid, None)
        try:
            conn.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            conn.sock.close()
        except OSError:
            pass
        self.inbox.put(("close", conn.cid, reason))

    def send(self, cid, msg):
        with self._guard:
            conn = self.conns.get(cid)
        if conn is None:
            return False
        data = protocol.encode(msg)
        try:
            with conn.lock:
                conn.sock.sendall(data)
            return True
        except OSError:
            self._drop(conn, "lost")
            return False

    def drop(self, cid, reason="closed"):
        with self._guard:
            conn = self.conns.get(cid)
        if conn is not None:
            self._drop(conn, reason)

    def _heartbeat(self):
        while self.running:
            time.sleep(PING_EVERY)
            with self._guard:
                conns = list(self.conns.values())
            for conn in conns:
                if time.monotonic() - conn.last_rx > SILENT_LIMIT:
                    self._drop(conn, "timed out")
                else:
                    self.send(conn.cid, {"t": "ping"})

    def close(self):
        self.running = False
        with self._guard:
            conns = list(self.conns.values())
        for conn in conns:
            self._drop(conn, "closed")


class Server(_Endpoint):
    def __init__(self, host="0.0.0.0", port=None):
        """port None: the game's own port, or any free one if something's using it."""
        super().__init__()
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if port is None:
            try:
                self.listener.bind((host, GAME_PORT))
            except OSError:
                self.listener.bind((host, 0))
        else:
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind((host, port))
        self.listener.listen(8)
        self.listener.settimeout(0.5)
        self.port = self.listener.getsockname()[1]
        self._next = 1
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while self.running:
            try:
                sock, addr = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            self._add(sock, self._next, addr[0])
            self._next += 1

    def close(self):
        super().close()
        try:
            self.listener.close()
        except OSError:
            pass


class Client(_Endpoint):
    """One connection, to the host (its id is always 0)."""

    def __init__(self, host, port, timeout=5.0):
        super().__init__()
        sock = socket.create_connection((host, port), timeout=timeout)
        self._add(sock, 0, host)

    def send_host(self, msg):
        return self.send(0, msg)
