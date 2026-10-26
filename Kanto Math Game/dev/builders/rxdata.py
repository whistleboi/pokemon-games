# [REF-0087: RPG Maker XP data reader]
"""Reads RPG Maker XP .rxdata files (Ruby Marshal 4.8): enough for the Pokemon Journeys V18 maps
(Jordan's fan-game find, see render_journeys_backgrounds.py). Strings stay bytes unless a Ruby
string carried an encoding; use text() to read them."""
import struct


class RObj:
    def __init__(self, cls):
        self.cls, self.attrs = cls, {}

    def __repr__(self):
        return f"<{self.cls} {list(self.attrs)[:6]}>"


class RUser:
    def __init__(self, cls, data):
        self.cls, self.data = cls, data


class Reader:
    def __init__(self, data):
        self.d, self.p = data, 2
        self.syms, self.objs = [], []

    def byte(self):
        b = self.d[self.p]; self.p += 1; return b

    def int(self):
        c = struct.unpack("b", bytes([self.byte()]))[0]
        if c == 0:
            return 0
        if 5 <= c <= 127:
            return c - 5
        if -128 <= c <= -5:
            return c + 5
        if c > 0:
            v = 0
            for i in range(c):
                v |= self.byte() << (8 * i)
            return v
        c = -c
        v = -1
        for i in range(c):
            v &= ~(0xff << (8 * i))
            v |= self.byte() << (8 * i)
        return v

    def raw(self):
        n = self.int(); s = self.d[self.p:self.p + n]; self.p += n; return s

    def sym(self):
        t = chr(self.byte())
        if t == ":":
            s = self.raw().decode("utf-8", "replace"); self.syms.append(s); return s
        if t == ";":
            return self.syms[self.int()]
        raise ValueError(t)

    def read(self):
        t = chr(self.byte())
        if t == "0": return None
        if t == "T": return True
        if t == "F": return False
        if t == "i": return self.int()
        if t == ":":
            s = self.raw().decode("utf-8", "replace"); self.syms.append(s); return s
        if t == ";": return self.syms[self.int()]
        if t == "@": return self.objs[self.int()]
        if t == "I":
            v = self.read()
            for _ in range(self.int()):
                self.sym(); self.read()
            if isinstance(v, bytes):
                v = v.decode("utf-8", "replace")
                # strings are already registered as bytes; replace
                for i in range(len(self.objs) - 1, -1, -1):
                    if isinstance(self.objs[i], bytes):
                        self.objs[i] = v; break
            return v
        if t == '"':
            s = self.raw(); self.objs.append(s); return s
        if t == "f":
            s = self.raw().decode(); v = float(s) if s not in ("inf", "-inf", "nan") else float(s); self.objs.append(v); return v
        if t == "l":
            sign = chr(self.byte()); n = self.int(); v = int.from_bytes(self.d[self.p:self.p + n * 2], "little"); self.p += n * 2
            v = v if sign == "+" else -v; self.objs.append(v); return v
        if t == "[":
            a = []; self.objs.append(a)
            for _ in range(self.int()): a.append(self.read())
            return a
        if t in "{}":
            h = {}; self.objs.append(h)
            for _ in range(self.int()):
                k = self.read(); h[k if not isinstance(k, (list, dict)) else id(k)] = self.read()
            if t == "}": self.read()
            return h
        if t == "o":
            o = RObj(self.sym()); self.objs.append(o)
            for _ in range(self.int()):
                k = self.sym(); o.attrs[k.lstrip("@")] = self.read()
            return o
        if t == "u":
            c = self.sym(); u = RUser(c, self.raw()); self.objs.append(u); return u
        if t in "cm":
            s = self.raw().decode(); self.objs.append(s); return s
        if t == "e":
            self.sym(); return self.read()
        if t == "S":
            o = RObj(self.sym()); self.objs.append(o)
            for _ in range(self.int()):
                k = self.sym(); o.attrs[k] = self.read()
            return o
        raise ValueError(f"type {t!r} at {self.p}")


def load(path):
    return Reader(open(path, "rb").read()).read()


def text(v):
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else (v or "")
