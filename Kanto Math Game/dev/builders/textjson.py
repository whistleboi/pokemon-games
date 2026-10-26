"""Edit hand-formatted region JSON as text: add to an area's list, set a key in an area's object.
Keeps the file's own formatting; every change is checked by parsing the result.

Keys are only ever matched at the area's own top level. (An earlier version matched the first
"gym": anywhere in the area, which hit backgrounds.gym and overwrote the Gym background images.)"""
import json
import re


class TextJSON:
    def __init__(self, path):
        self.path = path
        self.s = open(path, encoding="utf-8").read()

    def _match(self, i, open_ch, close_ch):
        """Index of the bracket closing the one at i (strings respected)."""
        depth, k, in_str = 0, i, False
        while k < len(self.s):
            c = self.s[k]
            if in_str:
                if c == "\\":
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return k
            k += 1
        raise ValueError("unbalanced")

    def _top_key(self, st, en, key):
        """(key_start, value_start) of `key` directly inside the object st..en, or None."""
        depth, k, s = 0, st, self.s
        while k < en:
            c = s[k]
            if c == '"':
                j = k + 1
                while s[j] != '"':
                    j += 2 if s[j] == "\\" else 1
                if depth == 1:
                    after = re.match(r'\s*:\s*', s[j + 1:])
                    if after and s[k + 1:j] == key:
                        return k, j + 1 + after.end()
                k = j + 1
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
            k += 1
        return None

    def _value_end(self, vstart):
        c = self.s[vstart]
        if c in "{[":
            return self._match(vstart, c, "}" if c == "{" else "]") + 1
        if c == '"':
            j = vstart + 1
            while self.s[j] != '"':
                j += 2 if self.s[j] == "\\" else 1
            return j + 1
        return vstart + re.match(r'[^,\n}\]]*', self.s[vstart:]).end()

    def area_span(self, area):
        m = re.search(r'"' + re.escape(area) + r'"\s*:\s*\{', self.s)
        assert m, area
        start = m.end() - 1
        return start, self._match(start, "{", "}")

    def append(self, area, key, obj):
        """Append obj to area[key] (a list), creating the list if missing."""
        st, en = self.area_span(area)
        hit = self._top_key(st, en, key)
        text = json.dumps(obj, ensure_ascii=False)
        if hit and self.s[hit[1]] == "[":
            a = hit[1]
            b = self._match(a, "[", "]")
            inner = self.s[a + 1:b].strip()
            ins = (",\n            " if inner else "\n            ") + text + "\n        "
            body = self.s[a + 1:b].rstrip()
            self.s = self.s[:a + 1] + body + ins + self.s[b:]
        else:
            self.s = self.s[:en] + f',\n        "{key}": [{text}]\n    ' + self.s[en:]
        json.loads(self.s)

    def _dump(self, value, at):
        """JSON text for a value set at index `at`: a list of objects gets one object per line,
        indented like the key's line (the hand-formatted style); anything else stays on one line."""
        if isinstance(value, list) and len(value) > 1 and all(isinstance(v, dict) for v in value):
            line_start = self.s.rfind("\n", 0, at) + 1
            pad = re.match(r"[ \t]*", self.s[line_start:]).group(0)
            items = (",\n" + pad + "  ").join(json.dumps(v, ensure_ascii=False) for v in value)
            return "[\n" + pad + "  " + items + "\n" + pad + "]"
        return json.dumps(value, ensure_ascii=False)

    def set(self, area, key, value):
        """Set area[key] = value (replacing an existing value of any shape)."""
        st, en = self.area_span(area)
        hit = self._top_key(st, en, key)
        text = self._dump(value, hit[0] if hit else en)
        if hit:
            vstart = hit[1]
            self.s = self.s[:vstart] + text + self.s[self._value_end(vstart):]
        else:
            self.s = self.s[:en].rstrip() + f',\n        "{key}": {text}\n    ' + self.s[en:]
        json.loads(self.s)

    def remove(self, area, key):
        """Delete area[key] (and the comma before it). No-op when missing."""
        st, en = self.area_span(area)
        hit = self._top_key(st, en, key)
        if not hit:
            return False
        kstart, vstart = hit
        vend = self._value_end(vstart)
        before = self.s[:kstart].rstrip()
        if before.endswith(","):
            self.s = before[:-1] + self.s[vend:]
        else:  # first key: drop the comma after it instead
            after = re.match(r'\s*,', self.s[vend:])
            self.s = self.s[:kstart] + self.s[vend + (after.end() if after else 0):].lstrip()
        json.loads(self.s)
        return True

    def drop_where(self, area, key, pred):
        """Remove items matching pred from the list area[key]."""
        lst = self.data()["STORY_PROGRESSION"][area].get(key) or []
        keep = [o for o in lst if not pred(o)]
        if len(keep) != len(lst):
            self.set(area, key, keep)
        return len(lst) - len(keep)

    def data(self):
        return json.loads(self.s)

    def save(self):
        json.loads(self.s)
        open(self.path, "w", encoding="utf-8", newline="").write(self.s)
