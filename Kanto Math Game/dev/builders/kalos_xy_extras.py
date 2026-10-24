"""The X/Y Kalos dex species the encounter tables don't cover (hordes, eggs, gifts, statics), placed the
X/Y way. Run after kalos_xy_pools.py, from the game folder: python dev/builders/kalos_xy_extras.py dev/builders
- Babies and horde-only base forms join the pool where a relative of theirs already lives, at a low rate.
- Kanto starters: Sycamore's gift after the Bug Badge (matching your Kalos starter's type), and all three
  rare on Route 19 with the Kalos starters.
- Zapdos and Moltres join Articuno at the Sea Spirit's Den; an Old Amber (Aerodactyl) in Glittering Cave."""
import json
import re
import sys

sys.path.insert(0, sys.argv[1])
from textjson import TextJSON  # noqa: E402

P = "assets/kalos_area_data.json"
RELATIVE_PLACED = [172, 283, 446, 296, 360, 50, 194, 92, 509, 261, 504, 270, 418, 81, 100, 220, 532, 27, 167, 21,
                   163, 174, 353, 570, 574, 438, 216, 633]
lv = json.load(open("assets/pokemon_levels.json", encoding="utf-8"))
pairs = [tuple(int(x) for x in k.split(">")) for k in lv["pairs"]]


def to_100(w):
    tot = sum(w.values())
    sc = {k: v * 100 / tot for k, v in w.items()}
    out = {k: max(1, int(v)) for k, v in sc.items()}
    diff = 100 - sum(out.values())
    order = sorted(sc, key=lambda k: sc[k] - int(sc[k]), reverse=diff > 0)
    i = 0
    while diff:
        k = order[i % len(order)]
        if diff > 0:
            out[k] += 1; diff -= 1
        elif out[k] > 1:
            out[k] -= 1; diff += 1
        i += 1
    return out


def relatives(pid):
    near = {b for a, b in pairs if a == pid} | {a for a, b in pairs if b == pid}
    far = {b for a, b in pairs if a in near} | {a for a, b in pairs if b in near}
    return [near, far - near - {pid}]


raw = open(P, encoding="utf-8", newline="").read()
d = json.loads(raw)
sp = d["STORY_PROGRESSION"]
kalos_pools = sorted({a["wild_pool_percentages"] for a in sp.values() if a.get("wild_pool_percentages")})


def put(key, pid, share):
    global raw
    pool = dict(d[key])
    if str(pid) in pool:
        return False
    pool[str(pid)] = sum(pool.values()) * share / 100
    new = to_100(pool)
    d[key] = new
    m = re.search(r'("%s": )(\{[^{}]*\})' % re.escape(key), raw)
    raw = raw[:m.start(2)] + json.dumps(new).replace('{"', '{ "').replace('}', ' }') + raw[m.end(2):]
    return True


placed = {}
for pid in RELATIVE_PLACED:
    if any(str(pid) in d[k] for k in kalos_pools):
        continue
    for ring in relatives(pid):
        best = max(((d[k].get(str(r), 0), k) for k in kalos_pools for r in ring), default=(0, None))
        if best[0]:
            put(best[1], pid, 5)
            placed[pid] = best[1]
            break
for pid in (1, 4, 7):
    put("KALOS_ROUTE_19_PERCENTAGES", pid, 3)
json.loads(raw)
open(P, "w", encoding="utf-8", newline="").write(raw)
print("placed by relative:", placed)
print("not placed:", [p for p in RELATIVE_PLACED if p not in placed and not any(str(p) in d[k] for k in kalos_pools)])

t = TextJSON(P)
den = t.data()["STORY_PROGRESSION"]["SEA_SPIRITS_DEN"]["route_menu"]
for pid, name in ((145, "Zapdos"), (146, "Moltres")):
    if not any((o.get("boss") or {}).get("id") == pid for o in den):
        i = next(k for k, o in enumerate(den) if o.get("action") == "EXIT")
        den.insert(i, {"text": f"{name.upper()} OF THE DEN", "action": "BOSS", "color": "GOLD",
                       "condition": [f"not:defeated_kalos_{name.lower()}"],
                       "boss": {"id": pid, "name": name, "victory_flag": f"defeated_kalos_{name.lower()}"}})
t.set("SEA_SPIRITS_DEN", "route_menu", den)
cave = t.data()["STORY_PROGRESSION"]["GLITTERING_CAVE"]["route_menu"]
if not any(o.get("text") == "SEARCH THE FOSSIL DIG" for o in cave):
    i = next(k for k, o in enumerate(cave) if o.get("action") == "EXIT")
    cave.insert(i, {"text": "SEARCH THE FOSSIL DIG", "action": "EVENT", "color": "ORANGE",
                    "flag_condition": "not got_kalos_old_amber",
                    "event": {"lines": ["A Hiker is digging near the cave wall. \"Found another one! I've got plenty.\"",
                                        "\"Take this Old Amber. The lab in Ambrette Town can bring it back to life.\""],
                              "gift_item": {"OLD_AMBER": 1}, "flag": "got_kalos_old_amber"}})
    t.set("GLITTERING_CAVE", "route_menu", cave)
lum = t.data()["STORY_PROGRESSION"]["LUMIOSE_CITY"]["explore_options"]
if not any(o.get("text") == "Sycamore's Kanto Pokemon" for o in lum):
    i = next(k for k, o in enumerate(lum) if o.get("action") == "GYM")
    lum.insert(i, {"text": "Sycamore's Kanto Pokemon", "action": "EVENT", "color": "GOLD",
                   "condition": "has_bug_badge", "flag_condition": "not got_kalos_kanto_starter",
                   "event": {"lines": ["Professor Sycamore: These Pokemon come from Kanto, far away.",
                                       "Your partner and this one should get along. Take good care of it!"],
                             "gift_pokemon": {"650": 1, "653": 4, "656": 7, "default": 1},
                             "flag": "got_kalos_kanto_starter"}})
    t.set("LUMIOSE_CITY", "explore_options", lum)
t.save()
print("ok")
