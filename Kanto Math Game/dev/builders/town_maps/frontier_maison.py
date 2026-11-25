"""The Battle Maison at the Battle Frontier (Jordan, 11-14: "merge the battle resort with the frontier ... add an area and
build for the battle maison. use the battle tent resource from emerald as the building exterior and interior but have it
act just like the maison. lower streaks to be more realistic for kids").

Outside: Emerald's Battle Tent (Verdanturf's, its own tiles with its roof's top layer: 0_14.png, em_top/0_14.png), standing
where the wide lounge south of the Exchange was (Jordan OK'd the spot: "clean up the background the upper part of the
building so it doesn't look like cliffs": the cliff and lawn round the tent are cut away, the Frontier's pavement under it).
The Battle Resort's own content now lives here too (Jordan, 11-14: "move oras content into the frontier ... then wally
could be there"): Wally by the Maison, the five type masters, the Judge in the Pokemon Center, the Day Care Annex (the
free lounge door, L), Looker, the custodian and his Gengarite, the Berry lover and the little girl, the two grunts and their
Pokemon, the Whismur show, the move tutors, the Resort's hidden items; on your first visit Wally greets you on the pier and
the other team's admin hands you their Mega Stone (resort(), below; the options are hoenn_area_data.json's).
Inside: Slateport's Battle Tent rooms (Emerald's 9.2 lobby, 9.3 corridor, 9.4 battle room, their own pictures): the lobby's
attendant takes your challenge (src/world/frontier.py, facility "maison": a streak of single battles, then Chatelaine
Nita; 5 wins the first time, 10 after), the corridor leads to the battle room, where Nita waits.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TILES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "assets", "tiles")
KEY = "HOENN_BATTLE_FRONTIER"
AT = (77, 48)            # (the tent's top-left tile on the Frontier: 5 x 5, its door at the bottom's middle)
DOOR = (AT[0] + 2, AT[1] + 4)
LOUNGE = (77, 46, 7, 6)  # (the lounge house it replaces, and the strip above its roof: x, y, w, h in tiles)
PAVE = (84, 47)          # (a tile of the Frontier's pavement, to lay under the tent)
TENT = (1, 3, 5, 5)      # (the tent in Verdanturf's picture: x, y, w, h in tiles)

LOBBY = ["ccccccccccccc",
         "cccccc1cccccc",
         "c.cc.....cccc",
         "c.cN......ccc",
         "c.mmmm.mmmmcc",
         "..mmmm.mmmm..",
         ".............",
         "...N.....N...",
         "cN.........Nc",
         "cc....nn...cc"]
HALL = ["ccccc",
        "cc1cc",
        "c...c",
        "c...c",
        "c...c",
        "c...c",
        "c...c",
        "c111c"]
BATTLE = ["cccccccccc",
          "c....N...c",
          "c........c",
          "c........c",
          "c........c",
          "c........c",
          "c........c",
          "c........c",
          "ccc111cccc"]


def _picture():
    """The Frontier's picture with the tent in the lounge's place (ground and top layer), written next to Emerald's."""
    import pygame as pg
    if not pg.get_init():
        pg.init()
    T = 16
    ground = pg.image.load(os.path.join(TILES, "em_ground", "26_104.png"))
    top = pg.image.load(os.path.join(TILES, "em_top", "26_104.png")).convert_alpha() if pg.display.get_surface() else \
        pg.image.load(os.path.join(TILES, "em_top", "26_104.png"))
    pave = ground.subsurface((PAVE[0] * T, PAVE[1] * T, T, T)).copy()
    lx, ly, lw, lh = LOUNGE
    for x in range(lx, lx + lw):
        for y in range(ly, ly + lh + 1):
            ground.blit(pave, (x * T, y * T))
    top = top.copy()
    top.fill((0, 0, 0, 0), (lx * T, ly * T, lw * T, (lh + 1) * T))
    verd = pg.image.load(os.path.join(TILES, "em_ground", "0_14.png")).copy()
    verd.blit(pg.image.load(os.path.join(TILES, "em_top", "0_14.png")), (0, 0))
    tx, ty, tw, th = TENT
    tent = pg.Surface((tw * T, th * T), pg.SRCALPHA)
    tent.blit(verd, (0, 0), (tx * T, ty * T, tw * T, th * T))
    # the cliff and the lawn round it: every colour of Verdanturf's cliff (above the tent) and lawn, cut away where it
    # reaches the picture's edge (so the tent's own pixels, inside its outline, stay)
    bg = set()
    for (bx, by) in ((0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (2, 2), (4, 12), (5, 12), (6, 10), (8, 9), (9, 9)):
        for i in range(T):
            for j in range(T):
                bg.add(tuple(verd.get_at((bx * T + i, by * T + j)))[:3])
    w, h = tent.get_size()
    seen, todo = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while todo:
        x, y = todo.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if tuple(tent.get_at((x, y)))[:3] not in bg:
            continue
        tent.set_at((x, y), (0, 0, 0, 0))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    ground.blit(tent, (AT[0] * T, AT[1] * T))
    pg.image.save(ground, os.path.join(TILES, "em_ground", "26_104_maison.png"))
    pg.image.save(top, os.path.join(TILES, "em_top", "26_104_maison.png"))
    return "em_ground/26_104_maison.png", "em_top/26_104_maison.png"


def _room(art, pic, title, people, exits, links, moves=None):
    r = {"art": art, "exits": exits, "buildings": {}, "links": links, "people": people,
         "roofs": {"_picture": {"f": f"em_ground/{pic}.png", "at": [0, 0]}, "_signs_in_picture": True, "_buildings_in_picture": True},
         "theme": "room", "title": title}
    if moves:
        r["moves"] = moves
    return r


def apply(maps):
    m = maps.get(KEY)
    if not m:
        return
    rows = [list(r) for r in m["art"]]
    lx, ly, lw, lh = LOUNGE
    for y in range(ly + 3, ly + lh):   # (the lounge's own tiles: open now)
        for x in range(lx, lx + lw):
            if rows[y][x] == "c":
                rows[y][x] = "."
    for y in range(AT[1], AT[1] + 5):
        for x in range(AT[0], AT[0] + 5):
            rows[y][x] = "c"
    used = {c for r in rows for c in r} | set(m.get("buildings") or {})   # (a letter of its own: the map's letters follow its doors,
    mark = next(c for c in "PQRSTUVWXYZ" if c not in used)                 #  and Emerald's lounges have doors since 11-24)
    rows[DOOR[1]][DOOR[0]] = "D"
    rows[DOOR[1] - 1][DOOR[0]] = mark
    assert rows[DOOR[1] + 1][DOOR[0]] == ".", "the Maison's door opens onto the path"
    m["art"] = ["".join(r) for r in rows]
    m["buildings"] = dict(m.get("buildings") or {}, **{mark: "maison"})
    m["inside"] = dict(m.get("inside") or {}, **{f"{DOOR[0]},{DOOR[1]}": "maison"})
    g, t = _picture()
    m["roofs"] = dict(m["roofs"], _picture=dict(m["roofs"]["_picture"], f=g))
    m["overheads"] = [dict(o, f=t) if o.get("f") == "em_top/26_104.png" else o for o in m.get("overheads") or []]
    rooms = m.setdefault("rooms", {})
    rooms["maison"] = _room(LOBBY, "9_2", "Battle Maison",
                            ["Maison attendant", "Maison fan", "Streak hopeful", "Maison regular", "Maison spectator"],
                            {"n": f"OUT:{DOOR[0]},{DOOR[1]}"}, {"6,1": ["maison_hall", 2, 6]},
                            {"3,3": {"m": "face", "d": "d"}, "3,7": {"m": "wander", "d": "lr", "r": [1, 0]},
                             "9,7": {"m": "look", "d": "udlr"}, "1,8": {"m": "face", "d": "r"}, "11,8": {"m": "face", "d": "l"}})
    rooms["maison"]["overheads"] = [{"kind": "picture", "f": "em_top/9_2.png", "at": [0, 0], "size": [13, 10]}]   # (the lobby's own top layer: the counter and walls over you, as Emerald draws them; H7 look)
    rooms["maison_hall"] = _room(HALL, "9_3", "Battle Maison", [], {},
                                 {"2,1": ["maison_battle", 4, 7], "1,7": ["maison", 6, 2], "2,7": ["maison", 6, 2], "3,7": ["maison", 6, 2]})
    rooms["maison_battle"] = _room(BATTLE, "9_4", "Battle Maison: battle room", ["Chatelaine Nita"], {},
                                   {"3,8": ["maison_hall", 2, 2], "4,8": ["maison_hall", 2, 2], "5,8": ["maison_hall", 2, 2]},
                                   {"5,1": {"m": "face", "d": "d"}})


# ---------------------------------------------------------------- the Battle Resort's content, at the Frontier
# who stands where (each near the tile given: the nearest open one with open floor all round it)
RESORT_PEOPLE = [("Wally", (82, 53)), ("Looker", (100, 57)), ("Custodian", (112, 35)), ("GENGARITE", (114, 35)),
                 ("Berry lover", (58, 47)), ("Little girl", (62, 47)), ("Magma Grunt", (66, 54)), ("Aqua Grunt", (69, 54)),
                 ("Whismur show", (37, 45)), ("Tutor Thunder Punch", (8, 46)), ("Tutor Fire Punch", (10, 46)),
                 ("Tutor Ice Punch", (12, 46)), ("Tutor Superpower", (14, 46)), ("Bike fan", (96, 48))]
MASTERS = [("Fairy Tale Girl Josephine", (100, 41)), ("Rich Boy Antoin", (113, 41)), ("Aroma Lady Carnation", (11, 41)),
           ("Poke Maniac Kelvin", (27, 47)), ("Bug Maniac Felix", (31, 47))]
HIDDEN = {(24, 66): "MAX_ETHER", (93, 34): "BIG_PEARL", (117, 33): "FULL_RESTORE"}
ANNEX_DOOR = (121, 31)   # (the Day Care Annex: the lounge at this door - its building's letter is looked up, 11-24)


def _spot(rows, want, taken):
    h, w = len(rows), len(rows[0])
    best = None
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if rows[y][x] != "." or (x, y) in taken:
                continue
            if not all(rows[y + dy][x + dx] in ".!" and (x + dx, y + dy) not in taken for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            d = abs(x - want[0]) + abs(y - want[1])
            if best is None or d < best[0]:
                best = (d, x, y)
    return best[1], best[2]


def _add(rows, names, ch, adds):
    have = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ch]
    pairs = list(zip(have, names)) + [((x, y), n) for (x, y), n in adds]
    extra = names[len(have):]
    for (x, y), _n in adds:
        rows[y][x] = ch
    pairs.sort(key=lambda p: (p[0][1], p[0][0]))
    return [n for _xy, n in pairs] + extra


def resort(maps):
    m = maps.get(KEY)
    if not m:
        return
    rows = [list(r) for r in m["art"]]
    taken = set()
    people, trainers = [], []
    for name, want in RESORT_PEOPLE:
        xy = _spot(rows, want, taken)
        taken |= {(xy[0] + dx, xy[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        people.append((xy, name))
    for name, want in MASTERS:
        xy = _spot(rows, want, taken)
        taken |= {(xy[0] + dx, xy[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        trainers.append((xy, name))
    m["people"] = _add(rows, list(m.get("people") or []), "N", people)
    m["trainer_spots"] = _add(rows, list(m.get("trainer_spots") or []), "X", trainers)
    m["art"] = ["".join(r) for r in rows]
    moves = dict(m.get("moves") or {})
    for (x, y), name in trainers:
        moves[f"{x},{y}"] = {"m": "look", "d": "udlr", "s": 3}
    for (x, y), name in people:
        if name in ("Wally", "Looker", "Custodian"):
            moves[f"{x},{y}"] = {"m": "look", "d": "udlr"}
    m["moves"] = moves
    m["hidden"] = dict(m.get("hidden") or {}, **{f"{x},{y}": it for (x, y), it in HIDDEN.items() if m["art"][y][x] in ".!"})
    _annex = m["art"][ANNEX_DOOR[1] - 1][ANNEX_DOOR[0]]
    if _annex in (m.get("buildings") or {}):
        m["buildings"] = dict(m["buildings"], **{_annex: "annex"})
    m["rooms"]["center"]["people"] = list(m["rooms"]["center"].get("people") or []) + ["The Judge"]
    art = [list(r) for r in m["rooms"]["center"]["art"]]
    art[4][12] = "N"   # (the Judge: in the Center's corner, as ORAS's)
    m["rooms"]["center"]["art"] = ["".join(r) for r in art]
    # your first visit: Wally on the pier (ORAS's arrival at the Battle Resort), then the other team's admin and a Mega Stone
    scenes = [sc for sc in (m.get("scenes") or []) if not str(sc.get("flag", "")).startswith("frontier_arrival")]
    scenes.append({"trigger": "enter", "flag": "frontier_arrival_wally",
                   "cast": [{"sheet": "em_135.png", "from": [24, 66], "to": "player", "leave": "back",
                             "lines": ["Wally: {player_name}! You came to the Battle Frontier too?!",
                                       "Wally: They moved the Battle Maison here from the Resort. I'm going to train until I'm the best!",
                                       "Wally: Come find me by the Maison. Let's battle!"]}]})
    for ver, admin, stone, team in (("OMEGA_RUBY", "Matt", "SHARPEDONITE", "Team Aqua"), ("ALPHA_SAPPHIRE", "Courtney", "CAMERUPTITE", "Team Magma")):
        scenes.append({"trigger": "enter", "condition": [f"hoenn_version:{ver}", "frontier_arrival_wally"], "flag": f"frontier_arrival_{ver.lower()}",
                       "cast": [{"sheet": "@other_leader", "from": [26, 66], "to": "player", "leave": "back",
                                 "lines": [f"{admin}: Whoa there! Watch where your little friend's running!",
                                           f"{admin}: Hey, you're the kid who stopped us. {team}'s over that now. Here, take this. Boss's orders!"],
                                 "event": {"lines": [f"You received the {stone.title()}!"], "gift_item": {stone: 1},
                                           "flag": f"got_{stone.lower()}_frontier"}}]})
    m["scenes"] = scenes


_apply_maison = apply


def apply(maps):   # noqa: F811  (the Maison, then the Resort's content round it)
    _apply_maison(maps)
    resort(maps)
