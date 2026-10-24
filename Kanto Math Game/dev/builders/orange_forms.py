"""Orange Islands forms (Jordan's alt form info, 2026-10-23). Safe to re-run; edits the data in place.
- Pinkan Island: the full lines from the anime's "In the Pink" (pink sprites, Pinkan evolutions).
- Valencia Island: Professor Ivy's colour variants (hue-shifted sprites).
- Crystal Onix: Jordan's custom stats, moves from luminescent.team, and a Crystal Stone evolution from
  Onix (a separate branch from Steelix). Mateo gives one; after the Orange League, Pummelo sells them.
build_orange.py is out of date (it predates the playtest's Orange level patch); don't re-run it.
Run from the game folder: python dev/builders/orange_forms.py dev/builders"""
import colorsys
import json
import os
import re
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame  # noqa: E402

sys.path.insert(0, sys.argv[1])
from textjson import TextJSON  # noqa: E402

names = json.load(open("assets/pokemon_names.json", encoding="utf-8"))
SP = "assets/sprites/pokemon"

# ---- Pinkan: every line seen on Pinkan Island (In the Pink), smart IDs 9101-9136 in dex order.
from orange_special import PINKAN  # noqa: E402
PINKAN_LINES = [[10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20], [29, 30, 31], [32, 33, 34], [43, 44, 45],
                [46, 47], [48, 49], [50, 51], [56, 57], [69, 70, 71], [102, 103], [111, 112]]
ITEM_STEPS = {(30, 31): "MOON_STONE", (33, 34): "MOON_STONE", (44, 45): "LEAF_STONE", (70, 71): "LEAF_STONE",
              (102, 103): "LEAF_STONE", (61, 62): "WATER_STONE"}

# ---- Valencia: Ivy's colour variants, smart IDs 9501-9517 in dex order. (form id, base, hue shift in
# degrees, warm tint on light parts); an evolution shares its line's shift.
VALENCIA = [(9501, 12, 150, (255, 170, 80)), (9502, 20, 200, None), (9503, 29, 80, None), (9504, 30, 80, None),
            (9505, 31, 80, None), (9506, 32, -60, None), (9507, 33, -60, None), (9508, 34, -60, None),
            (9509, 45, 25, None), (9510, 46, 60, None), (9511, 47, 60, None), (9512, 61, 60, None),
            (9513, 62, 60, None), (9514, 70, -45, None), (9515, 71, -45, None), (9516, 91, -100, None),
            (9517, 130, -60, None)]
VALENCIA_LINES = [[29, 30, 31], [32, 33, 34], [46, 47], [61, 62], [70, 71]]

CRYSTAL_ONIX = 9201
CRYSTAL_STATS = {"HP": 70, "ATTACK": 90, "DEFENSE": 60, "SPECIAL-ATTACK": 110, "SPECIAL-DEFENSE": 70, "SPEED": 110}
CRYSTAL_LEVEL_UP = [(1, "BIND"), (1, "HARDEN"), (1, "TACKLE"), (4, "CURSE"), (7, "ROCK-THROW"), (10, "ICE-SHARD"),
                    (13, "COIL"), (16, "ROCK-BLAST"), (19, "ICICLE-SPEAR"), (22, "DRAGON-BREATH"),
                    (25, "DRAGON-TAIL"), (31, "ROCK-SLIDE"), (34, "ICICLE-CRASH"), (37, "ROCK-POLISH"),
                    (40, "POWER-GEM"), (43, "STONE-EDGE"), (46, "FROST-BREATH"), (49, "HEAVY-SLAM"),
                    (55, "EARTH-POWER"), (60, "HEAD-SMASH")]
CRYSTAL_OTHER = ["ROAR", "TOXIC", "HAIL", "SUNNY-DAY", "TAUNT", "ICE-BEAM", "BLIZZARD", "HYPER-BEAM", "PROTECT",
                 "IRON-TAIL", "EARTHQUAKE", "DIG", "SANDSTORM", "ROCK-TOMB", "FACADE", "REST", "DRAGON-PULSE",
                 "PAYBACK", "AVALANCHE", "GYRO-BALL", "STEALTH-ROCK", "DAZZLING-GLEAM", "FLASH-CANNON", "SURF",
                 "STRENGTH", "ROCK-SMASH", "BULLDOZE", "ROLLOUT", "MUD-SLAP", "IRON-DEFENSE", "IRON-HEAD",
                 "SCORCHING-SANDS", "ZAP-CANNON", "TWISTER", "ANCIENT-POWER", "STOMPING-TANTRUM"]


def pname(base, form):
    return f"{form.title()} {names[str(base)]}"


# ---------------------------------------------------------------- art
pygame.display.init()
pygame.display.set_mode((1, 1))


def recolor(src, dst, fn):
    if not os.path.exists(src):
        return 0
    img = pygame.image.load(src).convert_alpha()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.get_at((x, y))
            if a:
                img.set_at((x, y), fn(r, g, b, a))
    pygame.image.save(img, dst)
    return 1


def pink(r, g, b, a):  # same as make_orange_art.py
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    if lum < 40:
        return (int(lum * 1.1), int(lum * 0.6), int(lum * 0.8), a)
    k = lum / 255
    return (min(255, int(130 + 125 * k)), int(60 + 150 * k * k), int(110 + 120 * k), a)


def hue_shift(deg, tint):
    def fn(r, g, b, a):
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.16:  # outlines stay dark
            return (r, g, b, a)
        h = (h + deg / 360) % 1
        nr, ng, nb = (int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
        if tint and s < 0.25 and v > 0.6:  # light, unsaturated parts (wings) take the tint
            k = 0.45
            nr, ng, nb = (int(c * (1 - k) + t * k) for c, t in zip((nr, ng, nb), tint))
        return (nr, ng, nb, a)
    return fn


made = 0
for sid, base in PINKAN.items():  # only the missing ones: the first Pinkan art came from make_orange_art.py
    for d in (SP, f"{SP}/back", f"{SP}/shiny"):
        made += not os.path.exists(f"{d}/{sid}.png") and recolor(f"{d}/{base}.png", f"{d}/{sid}.png", pink)
for sid, base, deg, tint in VALENCIA:
    for d in (SP, f"{SP}/back", f"{SP}/shiny"):
        made += recolor(f"{d}/{base}.png", f"{d}/{sid}.png", hue_shift(deg, tint))
# The Crystal Stone: a small pale-blue gem.
gem = pygame.Surface((30, 30), pygame.SRCALPHA)
pts = [(15, 3), (25, 11), (21, 26), (9, 26), (5, 11)]
pygame.draw.polygon(gem, (40, 70, 110), pts)
pygame.draw.polygon(gem, (170, 225, 255), [(15, 5), (23, 11), (20, 24), (10, 24), (7, 11)])
pygame.draw.polygon(gem, (235, 250, 255), [(15, 6), (19, 11), (15, 15), (11, 11)])
pygame.image.save(gem, "assets/sprites/items/crystal-stone.png")
print("sprites:", made)

# ---------------------------------------------------------------- orange_area_data.json
p = "assets/orange_area_data.json"
d = json.load(open(p, encoding="utf-8-sig"))
fm = d["FORM_MAP"]
for sid, base in PINKAN.items():
    fm[str(sid)] = {"id": base, "form": "pinkan", "name": pname(base, "pinkan")}
for sid, base, *_ in VALENCIA:
    fm[str(sid)] = {"id": base, "form": "valencia", "name": pname(base, "valencia")}
# Pinkan Reserve: every listed line; first stages common, later ones rarer. (Scyther isn't on the list.)
weights = {}
for line in PINKAN_LINES:
    for i, base in enumerate(line):
        sid = next(s for s, b in PINKAN.items() if b == base)
        weights[str(sid)] = [8, 4, 2][i] if len(line) == 3 else [8, 3][i]
total = sum(weights.values())
pct = {k: max(1, round(v * 100 / total)) for k, v in weights.items()}
fix = 100 - sum(pct.values())
for k in sorted(pct, key=lambda k: -pct[k])[:abs(fix)]:
    pct[k] += 1 if fix > 0 else -1
d["ORANGE_PINKAN_RESERVE_PERCENTAGES"] = pct
d["ORANGE_PINKAN_RESERVE"] = [int(k) for k in pct]
# Valencia Beach: Ivy's variants make up about a third of the beach's Pokemon.
beach = {k: v for k, v in d["ORANGE_VALENCIA_BEACH_PERCENTAGES"].items() if int(k) < 9500}
var = {str(sid): (4 if base in (29, 32, 46, 61) else 3 if base in (30, 70, 20) else 2) for sid, base, *_ in VALENCIA}
scale = (100 - sum(var.values())) / sum(beach.values())
beach = {k: max(1, round(v * scale)) for k, v in beach.items()}
beach.update(var)
beach[max(beach, key=beach.get)] += 100 - sum(beach.values())
d["ORANGE_VALENCIA_BEACH_PERCENTAGES"] = beach
d["ORANGE_VALENCIA_BEACH"] = [int(k) for k in beach]
sp = d["STORY_PROGRESSION"]
# Mateo's gift: the Crystal Stone too.
for o in sp["SUNBURST_ISLAND"]["explore_options"]:
    ev = o.get("event") or {}
    if ev.get("flag") == "got_mateo_gift":
        ev["gift_item"] = {"AMULET_COIN": 1, "CRYSTAL_STONE": 1}
        line = "And this Crystal Stone: an Onix that touches it turns to living crystal, like the one in the cave!"
        if line not in ev["lines"]:
            ev["lines"].append(line)
# Pummelo Island's Mart (the Orange League island) sells Crystal Stones after the League.
sp["PUMMELO_ISLAND"]["extra_stock"] = [{"item": "CRYSTAL_STONE", "condition": "beat_orange_champion"}]
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write(json.dumps(d, indent=2, ensure_ascii=False))

# ---------------------------------------------------------------- pokemon_evolutions.json (hand-formatted)
p = "assets/pokemon_evolutions.json"
s = open(p, encoding="utf-8", newline="").read()
s = s.replace('"ONIX": ["STEELIX"],', '"ONIX": ["STEELIX", "ONIX_CRYSTAL"],')
evo = json.loads(s)
add = {}
for form, table in (("pinkan", PINKAN), ("valencia", {sid: base for sid, base, *_ in VALENCIA})):
    have = set(table.values())
    for line in PINKAN_LINES if form == "pinkan" else VALENCIA_LINES:
        for a, b in zip(line, line[1:]):
            if a in have and b in have:
                add[f"{pname(a, form).upper()}_{form.upper()}"] = [f"{names[str(b)].upper()}_{form.upper()}"]
new_lines = "".join(f'    {json.dumps(k)}: {json.dumps(v)},\n' for k, v in add.items() if k not in evo)
if new_lines:
    s = s.replace('    "ONIX": ["STEELIX", "ONIX_CRYSTAL"],\n', '    "ONIX": ["STEELIX", "ONIX_CRYSTAL"],\n' + new_lines, 1)
for form, table in (("pinkan", PINKAN), ("valencia", {sid: base for sid, base, *_ in VALENCIA})):
    for (a, b), item in ITEM_STEPS.items():
        if a not in table.values() or b not in table.values():
            continue
        key = f"{pname(a, form).upper()}_{form.upper()}"
        target = f"{names[str(b)].upper()}_{form.upper()}"
        m = re.search(r'("%s": \{)' % item, s)
        if f'"{key}"' not in s[m.end():m.end() + 2000].split("}")[0]:
            s = s[:m.end()] + f'"{key}": "{target}", ' + s[m.end():]
if '"CRYSTAL_STONE"' not in s:
    s = s.replace('        "METAL_COAT": {', '        "CRYSTAL_STONE": {"ONIX": "ONIX_CRYSTAL"},\n        "METAL_COAT": {', 1)
json.loads(s)
open(p, "w", encoding="utf-8", newline="").write(s)

# ---------------------------------------------------------------- Crystal Onix: stats, types, moves
p = "assets/pokemon_movesets.json"
ms = json.load(open(p, encoding="utf-8"))
moves = json.load(open("assets/moves.json", encoding="utf-8"))
onix = ms["95"]
entry = dict(onix, name="CRYSTAL ONIX", types=["ROCK", "ICE"], stats=CRYSTAL_STATS)
mv = []
for name in [m for _, m in CRYSTAL_LEVEL_UP] + CRYSTAL_OTHER:
    info = moves.get(name)
    if info and name not in [x["name"] for x in mv]:
        mv.append({"name": name, "power": info.get("power") or 0, "type": info.get("type"),
                   "accuracy": info.get("accuracy"), "category": info.get("category")})
entry["moves"] = mv
ms["95_crystal"] = entry
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write(json.dumps(ms, indent=2, separators=(",", ": "), ensure_ascii=False))
p = "assets/pokemon_levels.json"
lv = json.load(open(p, encoding="utf-8"))
lv["learnsets"][str(CRYSTAL_ONIX)] = [[l, m] for l, m in CRYSTAL_LEVEL_UP if m in moves]
raw = open(p, encoding="utf-8", newline="").read()
open(p, "w", encoding="utf-8", newline="").write(json.dumps(lv, separators=(",", ":"), ensure_ascii=False)
                                                  + ("\n" if raw.endswith("\n") else ""))
missing = [m for _, m in CRYSTAL_LEVEL_UP if m not in moves] + [m for m in CRYSTAL_OTHER if m not in moves]
print("pinkan evolutions:", len(add), "| crystal moves:", len(mv), "| moves not in moves.json:", missing)
