"""Edit hand-formatted region JSON as text: add to an area's list, set a key in an area's object.
Keeps the file's own formatting; every change is checked by parsing the result."""
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

    def area_span(self, area):
        m = re.search(r'"' + re.escape(area) + r'"\s*:\s*\{', self.s)
        assert m, area
        start = m.end() - 1
        return start, self._match(start, "{", "}")

    def append(self, area, key, obj):
        """Append obj to area[key] (a list), creating the list if missing."""
        st, en = self.area_span(area)
        part = self.s[st:en]
        m = re.search(r'"' + key + r'"\s*:\s*\[', part)
        text = json.dumps(obj, ensure_ascii=False)
        if m:
            a = st + m.end() - 1
            b = self._match(a, "[", "]")
            inner = self.s[a + 1:b].strip()
            ins = (",\n            " if inner else "\n            ") + text + "\n        "
            body = self.s[a + 1:b].rstrip()
            self.s = self.s[:a + 1] + body + ins + self.s[b:]
        else:
            self.s = self.s[:en] + f',\n        "{key}": [{text}]\n    ' + self.s[en:]
        json.loads(self.s)

    def set(self, area, key, value):
        """Set area[key] = value (replacing an existing value of any shape)."""
        st, en = self.area_span(area)
        part = self.s[st:en]
        m = re.search(r'\n(\s*)"' + key + r'"\s*:\s*', part)
        text = json.dumps(value, ensure_ascii=False)
        if m:
            vstart = st + m.end()
            c = self.s[vstart]
            if c in "{[":
                vend = self._match(vstart, c, "}" if c == "{" else "]") + 1
            else:
                vend = vstart + re.match(r'[^,\n}]*', self.s[vstart:]).end()
            self.s = self.s[:vstart] + text + self.s[vend:]
        else:
            self.s = self.s[:en].rstrip() + f',\n        "{key}": {text}\n    ' + self.s[en:]
        json.loads(self.s)

    def remove(self, area, key):
        """Delete area[key] (and the comma before it). No-op when missing."""
        st, en = self.area_span(area)
        m = re.search(r',\s*\n(\s*)"' + key + r'"\s*:\s*', self.s[st:en])
        if not m:
            return False
        vstart = st + m.end()
        c = self.s[vstart]
        if c in "{[":
            vend = self._match(vstart, c, "}" if c == "{" else "]") + 1
        else:
            vend = vstart + re.match(r'[^,\n}]*', self.s[vstart:]).end()
        self.s = self.s[:st + m.start()] + self.s[vend:]
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
