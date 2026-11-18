"""The places you land on from Soaring in the Sky (Jordan OK'd the layouts, 11-14): ORAS-only, so no file to read them from;
drawn in our style the way Birth Island and Navel Rock are, small and finished. kanto_handoff/SOARING_2D.md has the plan.

Every one: your Eon waits where it set you down ("SOAR AWAY": talk to it to fly off again). A legend stands at the back
where ORAS's mysterious ring floats; one of a place's legends is out each visit (src/world/soaring.py, roll_visit), so
its other spots stand empty. The daily Mirage spots (forest, cave, mountain) hide the once-only item of the place you
landed at (ORAS's eight places a kind, Bulbapedia's tables); each place's item has its own nook.

  ~ sea all round (you came by air)   s beach   . grass   f flowers   T trees   r rocks   c rock / cave wall
  " tall grass (wild Pokemon)   1 a passage between the outside and the cave (the floor's "links")   N someone / something
"""

_ISLE_LEGEND = "SEEK CRESSELIA"


def _check(rows, w=None):
    w = w or len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == w, f"row {i} is {len(r)} wide, not {w}: {r!r}"
    return rows


CRESCENT_ISLE = _check([
    "~~~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~~~ssss~~~~~~~~~",
    "~~~~~~~~sss..Nss~~~~~~~~",
    "~~~~~~ss..f...ss~~~~~~~~",
    "~~~~~s..f..sss~~~~~~~~~~",
    "~~~~s....ss~~~~~~~~~~~~~",
    "~~~s...fs~~~~~~~~~~~~~~~",
    "~~~s...s~~~~~~~~~~~~~~~~",
    "~~s..f.s~~~~~~~~~~~~~~~~",
    "~~s....s~~~~~~~~~~~~~~~~",
    "~~~s...s~~~~~~~~~~~~~~~~",
    "~~~s.f..s~~~~~~~~~~~~~~~",
    "~~~~s....ss~~~~~~~~~~~~~",
    "~~~~~s..f..sss~~~~~~~~~~",
    "~~~~~~ss......ss~~~~~~~~",
    "~~~~~~~~sss..Nss~~~~~~~~",
    "~~~~~~~~~~~ssss~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~",
])

PATHLESS_PLAIN = _check([
    "~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~~~ssssssss~~~~~~~~~",
    "~~~~~~sss........sss~~~~~~",
    "~~~~~s....N..N..N...s~~~~~",
    "~~~~s................s~~~~",
    "~~~s...r......f.......s~~~",
    "~~~s..........f...r...s~~~",
    "~~s....f..............s~~~",
    "~~s.........r..........s~~",
    "~~s...f.........ff.....s~~",
    "~~s....................s~~",
    "~~~s..r....f...........s~~",
    "~~~s..............r...s~~~",
    "~~~~s.....f..........s~~~~",
    "~~~~s........r.......s~~~~",
    "~~~~~s..............s~~~~~",
    "~~~~~~ss.....N....ss~~~~~~",
    "~~~~~~~~sss.....sss~~~~~~~",
    "~~~~~~~~~~~sssss~~~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~~~~~",
])

TRACKLESS_FOREST = _check([
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "TTTTTTTT........TTTTTTTT",
    "TTTTTTT..N..N..N.TTTTTTT",
    "TTTTTTT..........TTTTTTT",
    "TTTTTTTTT...f..TTTTTTTTT",
    "TTTTTTTTTTT..TTTTTTTTTTT",
    "TTTTT.......TTTTTTTTTTTT",
    "TTTT..TTTTTTTTTTTTTTTTTT",
    "TTTT..T.....TTTTTTTTTTTT",
    "TTTTT...TTT...TTTTTTTTTT",
    "TTTTTTTTTTTTT....TTTTTTT",
    "TTTTTTTTTTTTTTT...TTTTTT",
    "TTTTTTTT..TTTTTT..TTTTTT",
    "TTTTTTT....TTTTT..TTTTTT",
    "TTTTTTT..T..TTT...TTTTTT",
    "TTTTTTTT.TT.....TTTTTTTT",
    "TTTTTTTT..TTTTTTTTTTTTTT",
    "TTTTTTTTT..TTTTTTTTTTTTT",
    "TTTTTTTTTT...TTTTTTTTTTT",
    "TTTTTTTTTTT..f.TTTTTTTTT",
    "TTTTTTTTTT....N.TTTTTTTT",
    "TTTTTTTTTTT.....TTTTTTTT",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
])

# The Gnarled Den: Mt. Chimney's ash-grey west slope, then the hollow inside (twisted rock pillars, Kyurem at the back).
GNARLED_OUT = _check([
    "cccccccccccccc",
    "cccccc1ccccccc",
    "ccccc....ccccc",
    "cccc..r...cccc",
    "ccc.........cc",
    "ccc..r....r.cc",
    "cc...........c",
    "cc.....N.....c",
    "ccc.........cc",
    "cccccccccccccc",
])
GNARLED_IN = _check([
    "cccccccccccccccc",
    "cccccccccccccccc",
    "ccccccc..ccccccc",
    "cccccc..N.cccccc",
    "cccc.r......cccc",
    "ccc...........cc",
    "ccc.r.....r...cc",
    "cc............cc",
    "cc..r......r..cc",
    "ccc...........cc",
    "cccc..r...r..ccc",
    "cccccc....cccccc",
    "ccccccc1cccccccc",
    "cccccccccccccccc",
])

# The Fabled Cave: an island in the bay east of Route 110's cycling road, then one misty room.
FABLED_OUT = _check([
    "~~~~~~~~~~~~~~",
    "~~~~cccccc~~~~",
    "~~~cccc1ccc~~~",
    "~~sccc...ccs~~",
    "~s....r....s~~",
    "~s.f.......s~~",
    "~s.......f..s~",
    "~~s....N...s~~",
    "~~~ss....ss~~~",
    "~~~~~ssss~~~~~",
    "~~~~~~~~~~~~~~",
    "~~~~~~~~~~~~~~",
])
FABLED_IN = _check([
    "cccccccccccccccc",
    "ccccc......ccccc",
    "cccc..N..N..cccc",
    "ccc..........ccc",
    "cc............cc",
    "cc..r......r..cc",
    "cc............cc",
    "ccc..........ccc",
    "ccc...r......ccc",
    "cccc........cccc",
    "cccc.....r..cccc",
    "ccccc......ccccc",
    "cccccc....cccccc",
    "cccccc....cccccc",
    "ccccccc..ccccccc",
    "ccccccc..ccccccc",
    "ccccccc1cccccccc",
    "cccccccccccccccc",
])

# The Nameless Cavern: a rocky islet north-east of Sootopolis, a short tunnel, a round chamber round a still pool.
NAMELESS_OUT = _check([
    "~~~~~~~~~~~~",
    "~~~cccccc~~~",
    "~~ccc1cccc~~",
    "~~cc....cc~~",
    "~s..r....s~~",
    "~s.......s~~",
    "~~s..N..s~~~",
    "~~~sssss~~~~",
    "~~~~~~~~~~~~",
    "~~~~~~~~~~~~",
])
NAMELESS_IN = _check([
    "cccccccccccccccccc",
    "cccccc......cccccc",
    "cccc..N..N..N..ccc",
    "ccc............ccc",
    "cc....~~~~~~....cc",
    "cc...~~~~~~~~...cc",
    "cc...~~~~~~~~...cc",
    "cc....~~~~~~....cc",
    "ccc............ccc",
    "cccc..........cccc",
    "cccccc......cccccc",
    "cccccccc..cccccccc",
    "cccccccc..cccccccc",
    "cccccccc..cccccccc",
    "cccccccc1ccccccccc",
    "cccccccccccccccccc",
])

# The daily Mirage spots. Each of ORAS's eight places a kind hides its own item in its own nook (the item people, in
# reading order, are MIRAGE_ITEMS[kind] in place order: the eight N's after the Eon's are taken top-left first).
MIRAGE_FOREST = _check([
    "~~~~~~~~~~~~~~~~~~~~",
    "~~~~~ssssssssss~~~~~",
    "~~~ssTTTTTTTTTTss~~~",
    "~~sTTT...TTT.NTTTs~~",
    "~~sTT....\"\"\"...TTs~~",
    "~sTTN..\"\"\"\"\"\"...TTs~",
    "~sTT..\"\"\"..\"\"\"..TTs~",
    "~sTT.\"\"\"....\"\"..NTs~",
    "~sTT.\"\"..f...\"\"..Ts~",
    "~sTTN.\"\"....\"\"...Ts~",
    "~sTT..\"\"\"..\"\"\"..TTs~",
    "~sTTT..\"\"\"\"\"\"..NTTs~",
    "~~sTT..........TTs~~",
    "~~sTTTN..T..NTTTTs~~",
    "~~~sTTTT.....TTTs~~~",
    "~~~~ssTT..N..TTs~~~~",
    "~~~~~~ss.....ss~~~~~",
    "~~~~~~~~sssss~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~",
])
MIRAGE_CAVE_OUT = _check([
    "~~~~~~~~~~~~~~",
    "~~~~cccccc~~~~",
    "~~~ccc1cccc~~~",
    "~~~cc....cc~~~",
    "~~s...r....s~~",
    "~~s........s~~",
    "~~~s..N...s~~~",
    "~~~~sssss~~~~~",
    "~~~~~~~~~~~~~~",
])
MIRAGE_CAVE_IN = _check([
    "cccccccccccccccccccc",
    "cc.....cccccc....Ncc",
    "cc..r...cccc..r...cc",
    "cc.......cc.......cc",
    "ccc..N..........cccc",
    "cccc.......r....N.cc",
    "cc......cccc......cc",
    "cc.N...cccccc..r..cc",
    "cc.....ccccc......cc",
    "ccc..r.........N.ccc",
    "cccc.....N.......ccc",
    "cccccc........cccccc",
    "cccccccc.1cccccccccc",
    "cccccccccccccccccccc",
])
# A stepped peak: rings of cliff with gaps that wind up to the top; the ledges (_) hop you back down.
MIRAGE_MOUNTAIN = _check([
    "~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~sccccccs~~~~~~",
    "~~~~sccc.NN.cccs~~~~",
    "~~~sccN.......ccs~~~",
    "~~sccc..cccc..cccs~~",
    "~~scc..cc..cc..ccs~~",
    "~scc.N.c....c....cs~",
    "~scc...c.N..c..N.cs~",
    "~scc...cc__cc....cs~",
    "~scc.............cs~",
    "~sccc____ccc..cccs~~",
    "~~scc.N.......ccs~~~",
    "~~sccc....N..cccs~~~",
    "~~~sccccc..cccss~~~~",
    "~~~~sss.....sss~~~~~",
    "~~~~~~s..N..s~~~~~~~",
    "~~~~~~~sssss~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~",
])

# A Mirage Island (ORAS's, not Emerald's on Route 130): sand, grass, tall grass, a few rocks. At the back, where one of
# the Gen 1-3 legends Hoenn has no home for may be out (Jordan, 11-14: "Home for Gen 1-3 legends"); its six places'
# item nooks; the Eon on the south beach.
MIRAGE_ISLAND = _check([
    "~~~~~~~~~~~~~~~~~~~~~~",
    "~~~~~~~ssssssss~~~~~~~",
    "~~~~~ss..........ss~~~",
    "~~~~s...N.N.N.N.N..s~~",
    "~~~s...............s~~",
    "~~s...r..\"\"\"\"..r...s~~",
    "~~s.N..\"\"\"\"\"\"\".....s~~",
    "~s....\"\"\"\"\"\"\"\"\"\"..N.s~",
    "~s...\"\"\"\"ff\"\"\"\".....s~",
    "~sN..\"\"\"\"\"\"\"\"\"\"..r..s~",
    "~s.....\"\"\"\"\"\".......s~",
    "~~s..r.......f..N..s~~",
    "~~s.f....N.........s~~",
    "~~~s.........r....s~~~",
    "~~~~s...N........s~~~~",
    "~~~~~ss...N....ss~~~~~",
    "~~~~~~~sssssss~~~~~~~~",
    "~~~~~~~~~~~~~~~~~~~~~~",
])
ISLAND_LEGENDS = ["SEEK ARTICUNO", "SEEK ZAPDOS", "SEEK MOLTRES", "SEEK MEWTWO", "SEEK CELEBI"]

EON = "SOAR AWAY"   # (your Eon, waiting: its figure is drawn as the one that carries you, dungeon._figure_img "eon")

# ORAS's places for each kind of daily Mirage spot, in src/world/soaring.DAILY's order, and the item each hides
# (Bulbapedia's tables; the PP items are left out: this game has no PP).
MIRAGE_ITEMS = {
    "island": [None, "BIG_PEARL", "STAR_PIECE", None, "TM093", "TM103", "RARE_CANDY", "TM247"],
    "forest": [None, "FULL_RESTORE", "TM180", "CALCIUM", "HYPER_POTION", "MAX_REVIVE", "GREEN_SHARD", "IRON"],
    "cave": [None, "TM030", "YELLOW_SHARD", "CARBOS", None, "RARE_CANDY", "FULL_HEAL", "BIG_PEARL"],
    "mountain": ["PROTEIN", "TM083", "ZINC", "RED_SHARD", "RARE_CANDY", "FULL_RESTORE", "BLUE_SHARD", "MAX_REVIVE"],
}


def item_text(kind, i):
    """An item option's text on the map ("ZINC" ...; each unique in its area: the place's number after it)."""
    item = MIRAGE_ITEMS[kind][i]
    return f"{item.replace('_', ' ')} {i + 1}"


def _items(kind):
    return [item_text(kind, i) for i, it in enumerate(MIRAGE_ITEMS[kind]) if it]


def _links(out_rows, in_rows):
    """The '1' on the outside floor (0) and the inside floor (1) lead to each other."""
    def find(rows):
        return next((x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "1")
    (ox, oy), (ix, iy) = find(out_rows), find(in_rows)
    return {f"{ox},{oy}": [1, ix, iy]}, {f"{ix},{iy}": [0, ox, oy]}


def _two(out_rows, in_rows, out_people, in_people, names, in_theme="cave", out_look=None):
    lo, li = _links(out_rows, in_rows)
    out = {"art": out_rows, "exits": {}, "people": out_people, "links": lo}
    if out_look:   # (a slope of its own colour outside: the Gnarled Den's volcanic ash)
        out.update(theme="cave", roofs={"_look": out_look})
    return {"floors": [out,
                       {"art": in_rows, "exits": {}, "people": in_people, "links": li, "theme": in_theme}],
            "floor_names": names}


SOARING = {
    "HOENN_CRESCENT_ISLE": {"art": CRESCENT_ISLE, "exits": {}, "buildings": {}, "people": [_ISLE_LEGEND, EON]},
    "HOENN_PATHLESS_PLAIN": {"art": PATHLESS_PLAIN, "exits": {}, "buildings": {},
                             "people": ["SEEK COBALION", "SEEK TERRAKION", "SEEK VIRIZION", EON]},
    "HOENN_TRACKLESS_FOREST": {"art": TRACKLESS_FOREST, "exits": {}, "buildings": {}, "style": "forest",
                               "people": ["SEEK RAIKOU", "SEEK ENTEI", "SEEK SUICUNE", EON]},
    "HOENN_GNARLED_DEN": _two(GNARLED_OUT, GNARLED_IN, [EON], ["SEEK KYUREM"], ["The ashen slope", "The hollow"],
                             out_look={"floor": [172, 168, 162], "top": [112, 106, 102], "wall": [138, 130, 124]}),
    "HOENN_FABLED_CAVE": _two(FABLED_OUT, FABLED_IN, [EON], ["SEEK RESHIRAM", "SEEK ZEKROM"], ["The island", "The misty room"]),
    "HOENN_NAMELESS_CAVERN": _two(NAMELESS_OUT, NAMELESS_IN, [EON], ["SEEK UXIE", "SEEK MESPRIT", "SEEK AZELF"],
                                  ["The islet", "The chamber"]),
    "HOENN_MIRAGE_FOREST": {"art": MIRAGE_FOREST, "exits": {}, "buildings": {}, "people": None},
    "HOENN_MIRAGE_CAVE": _two(MIRAGE_CAVE_OUT, MIRAGE_CAVE_IN, [EON], None, ["The islet", "Inside"]),
    "HOENN_MIRAGE_MOUNTAIN": {"art": MIRAGE_MOUNTAIN, "exits": {}, "buildings": {}, "people": None},
}


# The Mirage spots' people, in reading order of their N's (a list per map): the item nooks, then the Eon at the shore.
def _mirage_people(rows, items):
    n = sum(r.count("N") for r in rows)
    assert n == len(items) + 1, f"{n} N's for {len(items)} items and the Eon"
    return items + [EON]   # (the Eon's N is the last: at the south shore)


SOARING["HOENN_MIRAGE_ISLANDS"] = {"art": MIRAGE_ISLAND, "exits": {}, "buildings": {},
                                   "people": ISLAND_LEGENDS + _mirage_people(MIRAGE_ISLAND[4:], _items("island"))}
SOARING["HOENN_MIRAGE_FOREST"]["people"] = _mirage_people(MIRAGE_FOREST, _items("forest"))
SOARING["HOENN_MIRAGE_MOUNTAIN"]["people"] = _mirage_people(MIRAGE_MOUNTAIN, _items("mountain"))
SOARING["HOENN_MIRAGE_CAVE"]["floors"][1]["people"] = _items("cave")
assert sum(r.count("N") for r in MIRAGE_CAVE_IN) == len(_items("cave"))


def _arrive(rows, n_index):
    """Where you stand on landing: beside your Eon (the n-th N in reading order), the first open tile N, W, E or S of it."""
    ns = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "N"]
    x, y = ns[n_index]
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        if rows[y + dy][x + dx] in ".sf=":
            return [x + dx, y + dy]
    raise AssertionError(f"no room beside the Eon at {x},{y}")


for _key, _m in SOARING.items():   # you land beside your Eon (dungeon.py: the map's "arrive" {came-from area: [x, y]})
    _rows, _people = (_m["floors"][0]["art"], _m["floors"][0]["people"]) if _m.get("floors") else (_m["art"], _m["people"])
    _spot = _arrive(_rows, _people.index(EON))
    _m["arrive"] = {"HOENN_SOARING_IN_THE_SKY": _spot}
    if not _m.get("floors"):
        _m["landings"] = [_spot]


for _key, _m in SOARING.items():   # Hoopa's ring floats at the back (dungeon.py "ring"): at the middle legend's spot
    for _fl in (_m["floors"] if _m.get("floors") else [_m]):
        _ns = [(x, y) for y, r in enumerate(_fl["art"]) for x, ch in enumerate(r) if ch == "N"]
        _legs = [xy for xy, who in zip(_ns, _fl["people"] or []) if str(who).startswith("SEEK ")]
        if _legs:
            _fl["ring"] = list(_legs[len(_legs) // 2])


# ORAS's extras on the Mirage spots (Jordan, 11-14): a hidden item, a new one each day (option "HIDDEN ITEM", its
# event's "gift_daily"), and cracked rocks your Pokemon breaks one at a time, a wild Pokemon from the place's pool behind
# some (map "smash_wild": dungeon._smash). Crescent Isle has the item but no rocks (no wild Pokemon there).
HIDDEN = "HIDDEN ITEM"


def _put(rows, x, y, ch, was="."):
    assert rows[y][x] in was, f"{x},{y} is {rows[y][x]!r}, not {was!r}"
    return rows[:y] + [rows[y][:x] + ch + rows[y][x + 1:]] + rows[y + 1:]


def _add_person(fl, x, y, name):
    """Stand someone at (x, y), in its place in the people list (reading order of the N's)."""
    before = sum(r.count("N") for r in fl["art"][:y]) + fl["art"][y][:x].count("N")
    fl["art"] = _put(fl["art"], x, y, "N")
    fl["people"] = list(fl["people"])
    fl["people"].insert(before, name)


_EXTRAS = {   # map: (floor, hidden item's tile, rocks' tiles)
    "HOENN_CRESCENT_ISLE": (None, (4, 9), []),
    "HOENN_MIRAGE_FOREST": (None, (8, 8), [(8, 12), (12, 12), (5, 4)]),
    "HOENN_MIRAGE_MOUNTAIN": (None, (10, 9), [(5, 9), (15, 9), (12, 3)]),
    "HOENN_MIRAGE_CAVE": (1, (4, 3), [(4, 2), (11, 5), (5, 9), (15, 7)]),
    "HOENN_MIRAGE_ISLANDS": (None, (15, 10), [(6, 5), (16, 9), (13, 13), (5, 11)]),
}
for _key, (_fi, _item_at, _rocks) in _EXTRAS.items():
    _m = SOARING[_key]
    _fl = _m["floors"][_fi] if _fi is not None else _m
    for _x, _y in _rocks:
        _fl["art"] = _put(_fl["art"], _x, _y, "0", ".r")
    _add_person(_fl, _item_at[0], _item_at[1], HIDDEN)
    if _rocks:
        _m["smash_wild"] = True
    _rows = _m["floors"][0]["art"] if _m.get("floors") else _m["art"]   # (the Eon's spot moved in the list: land beside it again)
    _people = _m["floors"][0]["people"] if _m.get("floors") else _m["people"]
    _m["arrive"] = {"HOENN_SOARING_IN_THE_SKY": _arrive(_rows, _people.index(EON))}
    if not _m.get("floors"):
        _m["landings"] = [_m["arrive"]["HOENN_SOARING_IN_THE_SKY"]]
