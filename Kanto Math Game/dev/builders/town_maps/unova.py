"""Unova's walkable maps (11-19): Black 2 / White 2's own layouts, by way of RPG Maker XP.

The layout comes from unova_geo.json, which kanto_handoff/unova_map_tools/rmxp_import.py writes from the RMXP project
Jordan adjusts (kanto_handoff/unova_rmxp, itself written from Black 2's file by export_rmxp.py): walls, water, doors,
where each person, sign and building stands, the ground pictures (assets/tiles/b2_ground) and the buildings as the
game's camera sees them (assets/tiles/b2). This file adds what the layout can't say: who each person is and what they
say (in our own words), what each door opens, and the story's scenes. Re-running the importer never loses any of it.

People and signs are keyed by the game file's own numbers (a zone's person n, a sign's script), so a person Jordan
moves in RMXP keeps their lines. A person or sign left out of the tables below is not placed."""
import json
import os

GEO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "unova_geo.json"), encoding="utf-8"))

LETTERS = "ABCEFGHIJKLMOPQRSTUVWYZ"          # (building letters: not D, N or X, which mean door, person, trainer spot)


def _sheet(z, n):
    p = next((p for p in GEO[str(z)]["people"] + GEO[str(z)]["items"] if p["n"] == n), None)
    return p and p["sheet"]


def _say(text, *lines, **kw):
    """A person: their label (unique in the town: it names their walking sheet too) and lines."""
    out = {"text": text, "action": "EVENT", "event": {"lines": list(lines)}}
    out.update(kw)
    return out


def _place(z, people, signs, extra_people=(), counters=None):
    """(art rows, people options in reading order, signs in reading order, the zone's doors) for one zone."""
    g = GEO[str(z)]
    rows = [list(r) for r in g["rows"]]
    w, h = g["w"], g["h"]
    spots = []
    for p in g["people"] + g["items"]:
        opt = people.get(p["n"])
        if opt is None or not (0 <= p["x"] < w and 0 <= p["y"] < h):
            continue
        opts = [dict(o) for o in opt] if isinstance(opt, list) else [dict(opt)]
        for o in opts:
            if p["sheet"] and "_look" not in o:
                o["_look"] = "sheet:" + p["sheet"]
        opt = opts if isinstance(opt, list) else opts[0]
        spots.append((p["y"], p["x"], opt))
    for x, y, opt in extra_people:
        spots.append((y, x, opt))
    for y, x, _o in spots:
        rows[y][x] = "N"
    if (not g["outdoor"]) if counters is None else counters:   # (someone behind a counter: the counter between them and the floor is "m", talked across)
        for y, x, _o in spots:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                a, b = (x + dx, y + dy), (x + 2 * dx, y + 2 * dy)
                if 0 <= b[0] < w and 0 <= b[1] < h and rows[a[1]][a[0]] == "c" and rows[b[1]][b[0]] == ".":
                    rows[a[1]][a[0]] = "m"
    sg, _sign_at = [], set()
    for s in g["signs"]:
        lines = signs.get((s["x"], s["y"])) or signs.get(s["script"])
        if lines and 0 <= s["x"] < w and 0 <= s["y"] < h and (s["x"], s["y"]) not in _sign_at:   # (one sign a tile: a rail zone's copies meet)
            _sign_at.add((s["x"], s["y"]))
            rows[s["y"]][s["x"]] = "!"
            sg.append((s["y"], s["x"], lines))
    return rows, [o for _y, _x, o in sorted(spots, key=lambda t: (t[0], t[1]))], [l for _y, _x, l in sorted(sg)], g["doors"]


# Each place's camera (11-20): read from the game file (camview.camera: a/0/5/9 by the zone header's camera number), its
# angle drawn into the pictures and its zoom set here automatically. CAMERAS {camera number: {"camera_zoom", "cameras":
# [{"rect", "zoom"}]}} is only for places that need more (a moving camera zone, Castelia's near-level street view).
CAMERAS = {}


def _camera(z):
    """The place's zoom from its own camera in the game file (unova_geo.json "cam" "zoom": camera 0 is 1), then CAMERAS'."""
    out = {}
    zoom = (GEO[str(z)].get("cam") or {}).get("zoom")
    if zoom and abs(zoom - 1.0) > 0.01:
        out["camera_zoom"] = zoom
    out.update(CAMERAS.get((GEO[str(z)].get("cam") or {}).get("camera"), {}))
    areas = (GEO[str(z)].get("cam") or {}).get("areas")
    if areas:   # (11-20: the strips where the game's camera moves as you cross them, Black 2's a/1/5/6: the Outlook...)
        out["cameras"] = list(out.get("cameras") or []) + [{k: a[k] for k in ("rect", "axis", "zoom", "pan")} for a in areas]
    return out


def _picture(z, outdoor):
    g = GEO[str(z)]
    roofs = {"_picture": {"f": g["picture"], "at": [0, 0], "px": 32}, "_signs_in_picture": True}
    if g["buildings"] and (outdoor or g.get("cam")):   # (a room's furniture too, when it's seen through the camera, 11-20)
        roofs["_objects"] = [dict(b) for b in g["buildings"]]
        roofs["_models"] = True
    else:
        roofs["_buildings_in_picture"] = True
    if g.get("cam"):   # (walked as the DS camera sees it: the ground lifted by height, buildings leaning, shadows)
        roofs["_cam"] = dict(g["cam"], lift=g["lift"])
    roofs["_shadows"] = True
    return roofs


B2_CENTERS = {41, 435, 443, 454}   # (Castelia, Aspertia, Floccesy, Virbank: one model, its counter ring 3 tiles below)


def _no_drops(z, rows, exit_chars):
    """A room's walkable patches you could only reach by a drop (11-21, the live 3D audit): Black 2 joins two tiles only
    at about the same height (its own heights, GEO lift), while our walk map joined every walkable tile, so every Center
    let you step off its upper floor down behind the counter, 3 tiles below. Tiles are joined where the height changes
    by 1.5 tiles at most (stairs climb a step a tile); a patch that can't reach a way out that way is closed (people
    standing there stay: they're talked to across the counter)."""
    g = GEO[str(z)]
    lift, k = g.get("lift"), float((g.get("cam") or {}).get("lift_k") or 0)
    if z not in B2_CENTERS or not lift or not k or not exit_chars:   # (Centers only: elsewhere the heights often don't line
        return   # up with the walk rows, and the 3D model showed no drop at what they'd cut off: offices, the cafe, labs, 11-21)
    h, w = len(rows), len(rows[0])
    hgt = lambda x, y: lift[y][x] / k
    walk = lambda x, y: rows[y][x] == "." or rows[y][x] in exit_chars
    seen = set()
    todo = [(x, y) for y in range(h) for x in range(w) if rows[y][x] in exit_chars]
    seen.update(todo)
    while todo:
        x, y = todo.pop()
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= q[0] < w and 0 <= q[1] < h and q not in seen and walk(*q) and abs(hgt(*q) - hgt(x, y)) <= 1.5:
                seen.add(q)
                todo.append(q)
    # each cut-off patch closed only when small (the counter ring: 13 tiles): a big one means the heights don't line up
    # with this room's walk rows (Virbank's north gate: three columns read 5 tiles up), so it stays open
    total = sum(1 for y in range(h) for x in range(w) if walk(x, y))
    left = {(x, y) for y in range(h) for x in range(w) if rows[y][x] == "." and (x, y) not in seen}
    while left:
        part, todo = set(), [left.pop()]
        while todo:
            x, y = todo.pop()
            part.add((x, y))
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in left:
                    left.discard(q)
                    todo.append(q)
        if len(part) <= 20 and len(part) <= 0.15 * total:
            for x, y in part:
                rows[y][x] = "c"


def room(z, people, signs, out_door, stairs=None, exits_extra=None, scenes=None, extra_people=()):
    """A building's room: its way out ("v", across its door mat) leads back below out_door; stairs: {zone: "ROOM:name"}.
    extra_people: [(x, y, option)] someone the file doesn't stand there (Hugh in Virbank's terminal, off the counter's spot)."""
    rows, ppl, sg, doors = _place(z, people, signs, extra_people)
    exits = {}
    for d in doors:
        if d["to"] == OUTSIDE[z]:
            ch, tgt = "v", "OUT:%d,%d" % tuple(out_door)
        elif stairs and d["to"] in stairs:
            ch, tgt = stairs[d["to"]]
        elif exits_extra and d["to"] in exits_extra:
            ch, tgt = exits_extra[d["to"]]
        else:
            continue
        for k in range(max(1, d["w"])):
            for j in range(max(1, d.get("h", 1))):   # (a doorway three tiles tall: the gates' side doors, Virbank's 447)
                if 0 <= d["x"] + k < len(rows[0]) and 0 <= d["y"] + j < len(rows):
                    rows[d["y"] + j][d["x"] + k] = ch
        exits[ch] = tgt
    _no_drops(z, rows, set(exits))
    m = {"theme": "room", "art": ["".join(r) for r in rows], "exits": exits, "buildings": {}, "roofs": _picture(z, False), "people": ppl}
    if sg:
        m["signs"] = sg
    if scenes:
        m["scenes"] = scenes
    m.update(_camera(z))
    return m


def town(z, people, signs, doors, rooms, extra_people=(), edges=None, **more):
    """A town: each door the game has becomes a one-row building around it (kind from `doors`: {zone: (kind, room)}).
    edges: {letter: (target, [(x, y), ...])}: the town's ways out at its map edges (Floccesy's roads, batch 1)."""
    rows, ppl, sg, gdoors = _place(z, people, signs, extra_people)
    buildings, exits, inside = {}, {}, {}
    for ch, (target, tiles) in (edges or {}).items():
        for x, y in tiles:
            rows[y][x] = ch
        exits[ch] = target
    letters = iter(LETTERS)
    for d in gdoors:
        if d["to"] not in doors:
            continue
        kind, rname = doors[d["to"]][:2]
        L = next(letters)
        x, y = d["x"], d["y"]
        rows[y][x] = "D"
        for xx in (x - 1, x + 1):          # (the building: the door and the wall either side of it, one row)
            if 0 <= xx < len(rows[0]) and rows[y][xx] == "c":
                rows[y][xx] = L
        buildings[L] = kind
        if len(doors[d["to"]]) > 2:          # (a gate: its building is also the town's way out there; its room plays first)
            exits[L] = doors[d["to"]][2]
        if rname:
            inside["%d,%d" % (x, y)] = rname
    m = {"art": ["".join(r) for r in rows], "exits": exits, "buildings": buildings, "roofs": _picture(z, True), "signs": sg,
         "people": ppl, "rooms": rooms, "inside": inside}
    m.update(_camera(z))
    m.update(more)
    return m


# ---------------------------------------------------------------------------------------------------------- Aspertia City
# Zones (Black 2): 427 the city, 428 your house, 429/430 Hugh's house, 431/432 and 433/434 houses, 435 the Pokemon Center,
# 436 the Trainers' School, 438 the gate to Route 19 (489, the school's yard Gym, comes with the Gym's batch).
OUTSIDE = {428: 427, 429: 427, 430: 429, 431: 427, 432: 431, 433: 427, 434: 433, 435: 427, 436: 427, 438: 427}

ASPERTIA_DOORS = {428: ("home", "home"), 429: ("house", "hugh"), 431: ("house", "house_sw"), 433: ("house", "house_ne"),
                  435: ("center", "center"), 436: ("house", "school"), 438: ("gate", "gate")}

NOT_YET = "not:received_starter_unova"

ASPERTIA_PEOPLE = {
    # (Hugh 0, Mom 1, Hugh's sister 3 and Mom 13 are the opening's cast, walked in by its scenes; Bianca 2 waits at the Outlook)
    2: _say("Bianca", "Bianca: Isn't the view amazing?", flag_condition="not received_starter_unova"),
    4: _say("Girl by the house", "I can't wait for the Trainers' School to open! There's so much I want to learn."),
    5: _say("Girl by the hedges", "The view of Route 19 from the Outlook is Aspertia's pride and joy."),
    6: _say("Boy at the school door", "The Trainers' School just got built, but nobody's allowed in yet.",
            "Not until a teacher starts. Or a Gym Leader, I heard!", condition=["not:b2_gym_open"]),
    8: {"text": "Poke Ball by the pond", "action": "EVENT", "flag_condition": "not b2_aspertia_tm119",
        "event": {"lines": ["You found TM119 Energy Ball!"], "gift_item": {"TM119": 1}, "flag": "b2_aspertia_tm119"}},
    9: _say("Boy on the east side", "Trainers battle side by side with their Pokemon. Gym Leaders are the strongest of them, they say!"),
    10: _say("Boy by the Outlook road", "People grow up when they go on a journey. Maybe I should leave town someday too..."),
    11: _say("Woman by the west road", "Your mom's wonderful with Pokemon, you know. Tired ones perk right up around her."),
    12: _say("Girl on the east side", "Wild Pokemon can be scary. But the ones you befriend stay right by your side!"),
}
# Cheren outside the school (Jordan 11-20): only when he's your second rival (the BW rival pick), a rival's first meeting;
# no battle here (BW has none at this point). Picked Bianca: she makes her promise after the catching lesson on Route 19.
ASPERTIA_CHEREN = (8, 36, _say("Cheren", "Cheren: So you're {player_name}. I'm Cheren.",
                                "Cheren: Two years ago I set out on a journey from Nuvema Town, with my friends. Now I'm going to teach here.",
                                "Cheren: As the Gym Leader, if you can believe it. The Gym isn't open yet.",
                                "Cheren: You remind me of myself back then. So let's make it a promise: when we meet out on the road, we battle.",
                                "Cheren: Leader or not, I won't hold back. Get strong, {player_name}!",
                                condition=["friend:cheren", "not:b2_gym_open"]))

ASPERTIA_SIGNS = {14: ["ASPERTIA CITY", "Where the sky feels close."], 15: ["Your house."],
                  16: ["ASPERTIA OUTLOOK", "All of Unova, laid out before you."],
                  (5, 35): ["TRAINERS' SCHOOL", "Still being built."], (9, 35): ["ASPERTIA GYM", "Leader: Cheren", "A Trainer seeking the right path."]}

# --- the opening (B2W2's, Jordan 11-19): your house, Hugh, Bianca at the Outlook, the starter, Hugh's battle, the Center,
#     Mom and Hugh's sister at its door. Each step sets a flag the next one waits on.
HOME_SCENES = [
    {"who": "Mom", "trigger": {"zone": [1, 7, 9, 9]}, "condition": "not:b2_mom_talk", "flag": "b2_mom_talk", "approach": True,
     "lines": ["Mom: Off out, {player_name}? Wait, you'll want to hear this first!",
               "Mom: Professor Juniper called. We go way back, she and I. She asked if you'd like a Pokemon of your own.",
               "Mom: And a Pokedex, to help with her research. That means a journey! I said yes for you. You don't mind, right?",
               "Mom: Her assistant Bianca came all the way to Aspertia to find you. Look for a big green hat!",
               "Mom: It's her first time here, so she's probably lost. Go find her!"],
     "after": "home"},
]

TOWN_SCENES = [
    {"trigger": "enter", "condition": ["b2_mom_talk", "not:b2_hugh_met"], "flag": "b2_hugh_met",
     "cast": [{"sheet": "b2_hugh.png", "from": [11, 48], "to": "player",
               "lines": ["{rival_name}: Hey, {player_name}! Got a Pokemon yet? Nobody around here battles. I'm bored out of my mind!",
                         "{rival_name}: ...Wait. Someone named Bianca is giving you one? Seriously?!"], "stay": True},
              {"sheet": "b2_c9.png", "from": [12, 48], "to": "player", "leave": [11, 47],
               "lines": ["{rival_name}'s sister: {player_name}... when you get your Pokemon, take really good care of it, okay?"]},
              {"as": 0, "lines": ["{rival_name}: Then it's settled! I've got something I need to do out there.",
                                  "{rival_name}: And I want someone I can count on with me. That's you!",
                                  "{rival_name}: The Outlook up north is the best spot in town. I bet Bianca's up there!"],
               "leave": [5, 21]}]},
    {"who": "Bianca", "trigger": {"zone": [1, 7, 6, 10]}, "condition": ["b2_hugh_met", NOT_YET], "flag": "b2_bianca_met", "approach": True,
     "lines": ["???: Wow... it's sooo pretty up here!",
               "Bianca: Oh, hello! I'm Bianca. I help Professor Juniper with her research.",
               "Bianca: I'm looking for a Trainer called {player_name}. Wait... is that you? You're just how she described!",
               "Bianca: I have a really big favour to ask. Will you help us fill in the Pokedex?",
               "Bianca: Yay! Thank you! Okay, then... ta-daa! Inside here is the Pokemon who'll be your partner!"],
     "then": "event:b2_bianca_starter", "after": "stay"},
    {"trigger": "enter", "condition": ["received_starter_unova", "not:b2_hugh_battle", "not:b2_hugh_battled"], "flag": "b2_hugh_battle",   # (the battle ends the scene: its flag, won or lost)
     "cast": [{"sheet": "b2_bianca.png", "from": [4, 5], "to": "player", "stay": True,
               "lines": ["Bianca: You two are a perfect match! And here's the Pokedex. It records every Pokemon you meet."],
               "then": "event:b2_pokedex"},
              {"sheet": "b2_hugh.png", "from": [5, 21], "to": "player",
               "lines": ["{rival_name}: There you are! So that's your partner? Nice!",
                         "{rival_name}: Hey, is that a Pokedex? Can I have one too? I need to get stronger!",
                         "Bianca: Um... who are you? Well, okay! I just happen to have a spare.",
                         "Bianca: Ooh, I've got an idea! You both have Pokemon now. Why not have a battle?",
                         "{rival_name}: You're on! My partner hatched from an Egg I raised myself. Let's go!"],
               "then": "event:b2_hugh_battle", "stay": True}]},
    {"trigger": "enter", "condition": ["b2_hugh_battled", "not:b2_led_to_center"], "flag": "b2_led_to_center",
     "cast": [{"sheet": "b2_hugh.png", "from": [5, 21], "to": "player", "leave": [20, 7],
               "lines": ["{rival_name}: Not bad for a first battle! I'm heading out ahead. Get stronger, okay?"]},
              {"sheet": "b2_bianca.png", "from": [4, 5], "to": "player",
               "lines": ["Bianca: Both your Pokemon did great! Let's rest yours at the Pokemon Center. Follow me!"],
               "lead": [[16, 36, []]], "leave": [16, 35]}],
     "room": ["center", 7, 17]},
    {"trigger": "enter", "condition": ["b2_center_tour", "not:b2_send_off"], "flag": "b2_send_off",
     "cast": [{"sheet": "b2_mom.png", "from": [12, 40], "to": "player",
               "lines": ["Mom: Oh! You must be Bianca. And {player_name} picked a partner! Looking good, you two.",
                         "Mom: Before I forget, these are for you: Running Shoes! Hold the run button and off you go."],
               "then": "event:b2_running_shoes", "stay": True},
              {"sheet": "b2_c9.png", "from": [12, 40], "to": "player",
               "lines": ["{rival_name}'s sister: Um... this is from me. A Town Map!",
                         "Bianca: Two Town Maps?",
                         "{rival_name}'s sister: The other one's for my big brother. Could you take it to him?"],
               "then": "event:b2_town_map", "leave": [11, 47]},
              {"as": 0, "lines": ["Mom: Have a wonderful trip, {player_name}! See lots of Pokemon, and lots of people!"], "leave": [15, 58]},
              {"sheet": "b2_bianca.png", "from": [16, 36], "to": "player",
               "lines": ["Bianca: Aww, that was so sweet! Okay! Next stop, Route 19. I'll show you how to catch a Pokemon!",
                         "Bianca: It's through the gate at the north end of town. See you there!"],
               "leave": [20, 7]}]},
]

TOWN_SCENES.append(
    {"trigger": "enter", "condition": ["b2_basic_badge", "not:b2_bianca_return"], "flag": "b2_bianca_return",
     "cast": [{"sheet": "b2_bianca.png", "from": [12, 40], "to": "player",
               "lines": ["Bianca: {player_name}! You got the Basic Badge? Congratulations!",
                         "Bianca: Here's a present! It's a move that gets stronger the more your Pokemon likes you.",
                         "{player_name} received TM274 Return!",
                         "Bianca: The next Gym's in Virbank City. Through Floccesy, then east along Route 20!"],
               "then": "event:b2_bianca_return", "leave": [20, 7]}]})

CENTER_SCENES = [
    {"trigger": "enter", "condition": ["b2_led_to_center", "not:b2_center_tour"], "flag": "b2_center_tour",
     "cast": [{"sheet": "b2_bianca.png", "from": [7, 18], "to": "player",
               "lines": ["Bianca: Here we are! I'll show you around."],
               "lead": [[7, 12, ["Bianca: This counter's where they heal your Pokemon. It's free, any time!"]],
                        [4, 12, ["Bianca: And that's a PC. Any Trainer can use it to keep their Pokemon."]],
                        [8, 6, ["Bianca: Over here is the Poke Mart. You can buy and sell all kinds of things.",
                                "Bianca: Here, {player_name}. Some Poke Balls to start you off!"]]],
               "then": "event:b2_bianca_balls", "heal": True, "leave": [7, 19]}]},
]

GATE_SCENES = [
    {"trigger": {"zone": [1, 2, 9, 3]}, "condition": "not:b2_send_off", "every": True,
     "cast": [], "call": ["(Bianca said to meet her outside the Pokemon Center first.)"], "push": [0, 1]},   # (nobody speaks: a thought)
]

ASPERTIA = town(
    427, ASPERTIA_PEOPLE, ASPERTIA_SIGNS, ASPERTIA_DOORS, rooms={
        "home": room(428, {0: [_say("Mom", "Mom: Look for a big green hat! Bianca can't be far.", flag_condition="not received_starter_unova"),
                               _say("Mom ", "Mom: Your partner looks happy. Go on, the world's waiting!", flag_condition="received_starter_unova")]},
                     {}, (15, 57), scenes=HOME_SCENES),
        "hugh": room(429, {0: _say("{rival_name}'s mom", "{rival_name}'s mom: Honestly, I'd rather my son stayed home.",
                                   "{rival_name}'s mom: But what parent doesn't want to see their child grow?"),
                           1: _say("Man in Hugh's house", "Too bad you don't have a Pokemon yet. You could see who's the better Trainer!")},
                     {}, (11, 46), stairs={430: ("^", "ROOM:hugh_2f")}),
        "hugh_2f": room(430, {0: _say("{rival_name}'s sister", "{rival_name}'s sister: I hope you find that Bianca lady soon!"),
                              1: _say("Purrloin", "Purrloin: Mew?", _look="sheet:b2_c308.png")},
                        {}, (11, 46), stairs={429: ("v", "ROOM:hugh")}),
        "house_sw": room(431, {0: _say("Old man", "Got a Pokemon with you? Then you can head out of town!"),
                               1: _say("Old woman", "Look after your Pokemon. That little one will show you a whole new world.")},
                         {}, (6, 57), stairs={432: ("^", "ROOM:house_sw_2f")}),
        "house_sw_2f": room(432, {0: _say("Woman upstairs", "Ever since Poke Balls, anyone can live with Pokemon. Amazing, when you think about it."),
                                  1: _say("Boy upstairs", "I want to have a Pokemon battle soon!")},
                            {}, (6, 57), stairs={431: ("v", "ROOM:house_sw")}),
        "house_ne": room(433, {0: _say("Woman by the window", "Aspertia's way out in the corner of Unova. The big battles happen in the middle."),
                               1: [_say("Girl with a Lillipup", "My Pokemon hasn't battled yet. I'm scared it'll get hurt...",
                                        condition=["not:b2_basic_badge"]),
                                   {"text": "Girl with a Lillipup ", "action": "EVENT", "condition": ["b2_basic_badge"], "event": {
                                       "lines": ["You beat Cheren? Wow... Maybe my Pokemon and I can be brave too. Take this!"],
                                       "gift_item": {"ULTRA_BALL": 1}, "flag": "b2_aspertia_ultra_ball",
                                       "done": ["My Lillipup and I are going to try our first battle!"]}}],
                               2: _say("Lillipup", "Lillipup: Yap! Yap yap!")},
                         {}, (27, 19), stairs={434: ("^", "ROOM:house_ne_2f")}),
        "house_ne_2f": room(434, {0: _say("Girl upstairs", "My fortune-telling says you'll meet a Pokemon soon!"),
                                  1: _say("Boy by the bed", "A good Poke Ball makes all the difference when you find the Pokemon you want.")},
                            {}, (27, 19), stairs={433: ("v", "ROOM:house_ne")}),
        "center": room(435, {6: {"text": "Pokémon Center", "action": "HEAL"},
                             2: {"text": "Shop", "action": "SHOP"},
                             3: _say("Clerk", "Welcome! The counter on the left has everything you need."),
                             1: _say("Woman at the PC counter", "The PCs here are free for every Trainer."),
                             10: _say("Man by the counter", "Advice from someone who practically lives in Pokemon Centers: heal up whenever HP gets low!"),
                             9: _say("Woman by the PC", "This is where every journey in Aspertia begins."),
                             4: _say("Trainer by the door", "Gym Leader Cheren? He travelled all over Unova a few years back."),
                             0: {"text": "Mr. Medal  ", "action": "EVENT", "condition": ["b2_gym_open"], "event": {"medal_rally": True}}},
                     {}, (16, 35), scenes=CENTER_SCENES),
        "school": room(436, {1: {"text": "Student", "action": "EVENT", "event": {
                                 "lines": ["Do you use items in battle? A good Trainer knows when to. Here, try this!"],
                                 "gift_item": {"X_DEFENSE": 1}, "flag": "b2_school_x_defend",
                                 "done": ["X items only last while that Pokemon stays in battle."]}},
                             2: _say("Student by the desks", "Normal-types are weak to Fighting-types. Remember that!"),
                             0: _say("Teacher", "We asked Alder of Floccesy Town to teach here. He says it's the young people's turn now."),
                             3: _say("Student at the back", "The blackboard explains status problems. Poison, sleep, burns..."),
                             4: _say("Girl by the window", "Did you know? Press B while a Pokemon is evolving and it stops!",
                                     "Some Trainers like their Pokemon just the way they are.")},
                       {}, (7, 34), exits_extra={489: ("^", "ROOM:gym")},
                       scenes=[{"trigger": {"zone": [8, 2, 10, 3]}, "condition": ["not:b2_gym_open"], "every": True,
                                "cast": [], "call": ["(The back door to the Gym is locked. It isn't open yet.)"], "push": [0, 1]}]),
        "gate": room(438, {0: {"text": "Gate guard", "action": "EVENT", "event": {
                                  "lines": ["Hey, {player_name}! Off on your journey? Here's a little something for the road."],
                                  "gift_item": {"POTION": 1}, "flag": "b2_gate_potion",
                                  "done": ["When your Pokemon get hurt, take it easy and visit a Pokemon Center."]}},
                           1: _say("Girl in the gate", "I love reading the news on the big board by the wall.")},
                     {}, (20, 6), exits_extra={437: ("^", "UNOVA_ROUTE_19")}, scenes=GATE_SCENES),
    },
    extra_people=[ASPERTIA_CHEREN],
    scenes=TOWN_SCENES,
)

FACE = {0: "u", 1: "d", 2: "l", 3: "r"}          # (a person's facing in the game file)


def route(z, people, signs, exits, hidden=None, scenes=None, trainers=None, extra_people=(), season_people=None, season_hidden=None,
          season_exits=None, **more):
    """A route (11-20): walked on the route maps (dungeon.py), its grass, ledges and water from the game's walk data.
    exits: {letter: (target, [(x, y), ...] the tiles that lead there)}: the map's edges and its gate doors.
    trainers: {person n: name in the area's trainer_pool}: they stand where the game has them ("X"), facing its way,
    seeing as far as its sight (11-20, batch 1)."""
    rows, ppl, sg, _doors = _place(z, people, signs, extra_people, counters=False)   # (a route has no shop counters: the Complex is "indoors" in the file)
    out = {}
    for ch, (target, tiles) in exits.items():
        for x, y in tiles:
            rows[y][x] = ch
        out[ch] = target
    spots, moves = [], {}
    for p in GEO[str(z)]["people"]:
        name = (trainers or {}).get(p["n"])
        if name:
            name, sight = name if isinstance(name, tuple) else (name, 3)   # ((name, sight): the game file's sight, tiles)
            rows[p["y"]][p["x"]] = "X"
            spots.append((p["y"], p["x"], name))
            moves["%d,%d" % (p["x"], p["y"])] = {"m": "face", "d": FACE.get(p.get("dir"), "d"), "s": max(1, int(sight))}
    m = {"art": ["".join(r) for r in rows], "exits": out, "roofs": _picture(z, True), "signs": sg, "people": ppl}
    if spots:
        m["trainer_spots"] = [n for _y, _x, n in sorted(spots)]
        m["moves"] = moves
    if hidden:
        m["hidden"] = hidden
    if scenes:
        m["scenes"] = scenes
    if GEO[str(z)].get("dark"):   # (dark grass: tall grass with its own, stronger Pokemon; 11-20)
        m["dark_grass"] = GEO[str(z)]["dark"]
    m.update(_camera(z))
    m.update(more)
    seasons = GEO[str(z)].get("seasons") or {}
    if seasons:   # (a season with its own map, from the game's own blocks for it: Route 20 in autumn, its leaf piles; 11-20)
        keep = GEO[str(z)]
        m["story_maps"] = []
        for season, sv in seasons.items():
            GEO[str(z)] = dict(keep, rows=sv["rows"], cam=sv["cam"], lift=sv["lift"], dark=sv.get("dark"), seasons=None)
            try:   # (that season's own people, hidden items and ways out: Route 20's autumn Rangers, the leaves' items)
                alt = route(z, {**people, **(season_people or {}).get(season, {})}, signs,
                            {**exits, **(season_exits or {}).get(season, {})},
                            hidden={**(hidden or {}), **(season_hidden or {}).get(season, {})} or None, scenes=scenes,
                            trainers=trainers, extra_people=extra_people, **more)
            finally:
                GEO[str(z)] = keep
            m["story_maps"].append({"when": ["season:" + season], "map": alt})
    return m


def _ball(label, item, flag, count=1, name=None):
    """An item ball (the game's own, read by kanto_handoff/unova_map_tools/uitems.py)."""
    gift = {"balls": count} if item == "balls" else {item: count}
    return {"text": label, "action": "EVENT", "flag_condition": "not " + flag,
            "event": {"lines": ["You found %s!" % (name or item.replace("_", " ").title())], "gift_item": gift, "flag": flag}}


# ---------------------------------------------------------------------------------------------------------------- Route 19
# Zone 437 (Black 2): from Aspertia's gate (south-west) east to Floccesy Town. Bianca's catching lesson just outside the
# gate; a Youngster shows off the ledge; Alder calls down from the hill by Floccesy and leads you on. The north side is
# reached with Surf (Water Stone, Nest Ball; Alder's spot hides an Expert Belt), a boy at the stairs till Alder has met you.
ROUTE_19_PEOPLE = {
    5: _say("Bianca", "Bianca: The Pokedex fills itself in as you meet Pokemon. Catching them adds even more!",
            flag_condition="not b2_route19_lesson"),
    0: _say("Youngster by the ledge", "Youngster: Ledges make great shortcuts. Hop off and you're down in no time!"),
    4: _say("Boy in the grass", "Boy: I'm looking for Pokemon in the tall grass!",
            "Boy: If you'd rather not meet any, stay out of the grass."),
    1: _say("Alder", "Alder: Off to Floccesy! I'll be waiting.", flag_condition="not b2_alder_met"),
    7: _say("Boy at the stairs", "Boy: You can Surf? Cool! Let's be Surf buddies!", flag_condition="not b2_alder_met"),
    6: {"text": "Poke Ball in the grass", "action": "EVENT", "flag_condition": "not b2_r19_potion",
        "event": {"lines": ["You found a Potion!"], "gift_item": {"POTION": 1}, "flag": "b2_r19_potion"}},
    2: {"text": "Poke Ball by the pond", "action": "EVENT", "flag_condition": "not b2_r19_water_stone",
        "event": {"lines": ["You found a Water Stone!"], "gift_item": {"WATER_STONE": 1}, "flag": "b2_r19_water_stone"}},
    3: {"text": "Poke Ball on the north path", "action": "EVENT", "flag_condition": "not b2_r19_nest_ball",
        "event": {"lines": ["You found a Nest Ball!"], "gift_item": {"NEST_BALL": 1}, "flag": "b2_r19_nest_ball"}},
}
ROUTE_19_SIGNS = {
    6: ["ROUTE 19", "Aspertia City - Floccesy Town"],
    4: ["TRAINER TIPS", "Talk to everyone you meet! Most of them have something useful to say."],
    5: ["ROUTE 19", "Floccesy Town is straight ahead."],
}
ROUTE_19_SCENES = [
    # Bianca's catching lesson, just outside the gate (the game's own step trigger: 19-23, 27)
    {"trigger": {"zone": [19, 26, 23, 27]}, "condition": ["b2_send_off", "not:b2_route19_lesson"], "flag": "b2_route19_lesson",
     "cast": [{"person": "Bianca", "path": [[21, 25]], "face": "d",
               "lines": ["Bianca: Heeey! Over here!",
                         "Bianca: Okay, here's how it works. Your Pokedex fills in whenever you meet a Pokemon.",
                         "Bianca: Catch one, and you learn even more about it! Watch me!"], "stay": True},
              {"person": "Bianca", "path": [[22, 25], [24, 25], [26, 25]], "face": "r", "lines": [], "stay": True},
              {"sheet": "mon:509", "from": [30, 25], "path": [[27, 25]], "face": "l", "wait": 10,
               "lines": ["A wild Purrloin jumped out of the grass!",
                         "Bianca's Pokemon wore it down... and Bianca threw a Poke Ball!",
                         "Gotcha! Purrloin was caught!"]},
              {"person": "Bianca", "path": [[25, 25], [22, 25], [21, 26]], "face": "d",
               "lines": ["Bianca: Phew, it worked! Here's the important part:",
                         "Bianca: Weaken a Pokemon first, then throw your Poke Ball. A sleeping or paralysed one is even easier!",
                         "Bianca: Floccesy Town is straight east. Go meet lots of Pokemon, and catch lots of them!"],
               "leave_path": [[21, 27], [21, 30], [21, 31]], "gone": True}]},
    # Bianca as your second rival (the BW rival pick, Jordan 11-20): her promise, straight after the lesson
    {"trigger": {"zone": [19, 26, 23, 27]}, "condition": ["b2_route19_lesson", "friend:bianca", "not:b2_bianca_rival"],
     "flag": "b2_bianca_rival",
     "cast": [{"sheet": "b2_bianca.png", "from": [21, 30], "to": "player",
               "lines": ["Bianca: Oh! Wait, wait! One more thing!",
                         "Bianca: Two years ago I went on a journey too, with my best friends. We battled each other all the time!",
                         "Bianca: So... let's be rivals! Whenever we meet on the road, let's have a battle. I'm going to get stronger too!"],
               "leave": [21, 31]}]},
    # the Youngster shows how a ledge works: he hops off it in front of you
    {"trigger": {"zone": [44, 16, 47, 19]}, "condition": ["not:b2_ledge_demo"], "flag": "b2_ledge_demo",
     "cast": [{"person": "Youngster by the ledge", "face": "l",
               "lines": ["Youngster: Hey! Do you know about ledge jumping?",
                         "Youngster: ...Oh, you do? Well, watch me anyway!",
                         "Youngster: From the top of the ledge... Boing!"]},
              {"person": "Youngster by the ledge", "path": [[48, 18], [47, 18]], "face": "r",
               "lines": ["Youngster: See? A shortcut! You can only hop down, though, never back up."]}]},
    # Alder, from the hill by Floccesy (the game's own triggers: 58-59, 21-26)
    {"trigger": {"zone": [57, 20, 59, 25]}, "condition": ["not:b2_alder_met"], "flag": "b2_alder_met", "call": ["???: You there, Trainer!"],
     "cast": [{"person": "Alder", "face": "d", "lines": ["???: My name is Alder! I'm a Trainer who loves seeing the world.",
                                                       "Alder: My goal? To show people how wonderful it is to walk toward the future with Pokemon."],
               "stay": True},
              {"person": "Alder", "path": [[61, 20], [61, 21]], "zoom": 1.25, "look": [60, 21],
               "lines": ["Alder: ...And you are? {player_name}, from Aspertia City! Your partner looks fine indeed.",
                         "Alder: But you're not a seasoned Trainer yet. I'll train you a little! Follow me to Floccesy!"],
               "leave_path": [[62, 21], [63, 21]], "gone": True}]},
    # Alder again, on your way back to Aspertia for the Gym (the game's own trigger: 58, 21-26, once the Gym is open)
    {"trigger": {"zone": [57, 21, 58, 26]}, "condition": ["b2_gym_open", "not:b2_alder_oran"], "flag": "b2_alder_oran",
     "cast": [{"sheet": "b2_c97.png", "from": [63, 22], "to": "player",
               "lines": ["Alder: {player_name}! Excuse me! I forgot to tell you something important. First, take these!",
                         "{player_name} received 5 Oran Berries!",
                         "Alder: Oran Berries! Give one to a Pokemon and its HP comes back.",
                         "Alder: Better still, let a Pokemon hold one. When it's hurt in battle, it eats the Berry by itself!",
                         "Alder: Aspertia's Gym Leader is strong. But think about what your Pokemon can do, and you'll be fine!",
                         "Alder: Then take on stronger Trainers, and every city's Gym Leader. That's how you grow, together!"],
               "then": "event:b2_alder_oran", "leave": [63, 22]}]},
]
ROUTE_19 = route(
    437, ROUTE_19_PEOPLE, ROUTE_19_SIGNS,
    exits={"v": ("ASPERTIA_CITY", [(20, 31), (21, 31), (22, 31)]),
           ">": ("FLOCCESY_TOWN", [(63, y) for y in range(19, 26)])},
    hidden={"61,19": "EXPERT_BELT"},
    scenes=ROUTE_19_SCENES,
)


# ====================================================================================================== batch 1 (11-20)
# Black 2's story from Route 19 to the first badge: Floccesy Town (Alder), Route 20, Floccesy Ranch (Hugh, the lost
# Herdier, the first Plasma Grunt), Alder's students, Pledge Grove, and Cheren's Gym behind Aspertia's Trainers' School.
# Story flags in order: b2_alder_met (Route 19) -> b2_floccesy_met -> b2_alder_maps -> b2_hugh_ranch -> b2_ranch_owners
# -> b2_ranch_north -> b2_ranch_cry -> b2_herdier_found -> b2_alder_seymour -> b2_alder_cassie -> b2_alder_training
# -> b2_gym_open -> b2_basic_badge (Cheren's win) -> b2_jerome -> b2_cheren_route20, b2_habitat_list.
# Items, hidden items and who stands where: the game file (uitems.py); lines: the game's, in our own words.

# ----------------------------------------------------------------------------------------------------------- Floccesy Town
# Zones: 439 the town, 440 Alder's house, 441 and 442 houses, 443 the Pokemon Center (600: a post-game memory, not built).
OUTSIDE.update({440: 439, 441: 439, 442: 439, 443: 439, 489: 0})
FLOCCESY_DOORS = {440: ("house", "alder"), 441: ("house", "house_w"), 442: ("house", "house_e"), 443: ("center", "center"),
                  614: ("gate", None, "PLEDGE_GROVE")}
FLOCCESY_PEOPLE = {
    0: _say("Alder", "Alder: My house is just past the clock tower. Stop by the Pokemon Center first if you like!",
            condition=["b2_alder_met", "not:b2_floccesy_met"]),
    # (1, Mr. Medal: he gives the Medal Box in the scene below and leaves; after that he's in the Pokemon Centers)
    2: _say("Man by the clock", "My Pokemon wake me up when they're hungry, and hog the whole bed at night. I love it!"),
    3: _say("Woman by the tower", "People always dream about the past or the future. But the best time with Pokemon is right now!"),
    4: _say("Boy by Alder's house", "I save a record of my journey all the time, so I never forget what I've done. Good habit!"),
    5: _say("Woman by the Center", "Wild Pokemon at Floccesy Ranch can take you by surprise! Your own Pokemon are your best help."),
    6: _say("Girl by the steps", "Want to know what Alder taught me? The Pokemon at the top of your party goes out first.",
            "So put the one you're raising there!"),
    7: _ball("Poke Ball west of Alder's house", "X_SPEED", "b2_floccesy_x_speed", name="an X Speed"),
    8: _say("Boy on the path", "Are you happy you get to train Pokemon? Me too!"),
}
FLOCCESY_ALDER = (16, 25, [_say("Alder ", "Alder: Just follow the road east to Route 20! I'll wait here till you've delivered that Town Map.",
                                condition=["b2_floccesy_met", "not:b2_herdier_found"]),
                           _say("Alder  ", "Alder: Back already? Come on in, my house is right there!",
                                condition=["b2_herdier_found", "not:b2_alder_training"])])
FLOCCESY_SIGNS = {13: ["FLOCCESY TOWN", "Where a prophecy flocks."], 15: ["An old clock tower..."]}
FLOCCESY_SCENES = [
    # Alder waits at the way in from Route 19 (the game's own trigger: x 12, rows 54-57)
    {"trigger": {"zone": [0, 53, 13, 57]}, "condition": ["b2_alder_met", "not:b2_floccesy_met"], "flag": "b2_floccesy_met",
     "cast": [{"person": "Alder", "face": "l",
               "lines": ["Alder: Ah, {player_name}! Are your Pokemon well?",
                         "Alder: Your Pokemon always give their all for you, so you must always be kind to them!",
                         "Alder: My house is just a little farther. Stop by the Pokemon Center first if you'd like!"],
               "leave_path": [[14, 48], [16, 41], [17, 31], [16, 26]], "gone": True}]},
    # by the clock tower: the two Town Maps (the game's triggers 4-7 around 15-19, 27-30)
    {"who": "Alder ", "trigger": {"zone": [15, 26, 19, 30]}, "condition": ["b2_floccesy_met", "not:b2_alder_maps"], "flag": "b2_alder_maps",
     "approach": True,
     "lines": ["Alder: Hey, this way! Shall we start training?",
               "Alder: By the way... why are you holding two Town Maps?",
               "Alder: Oh ho! It's your friend's, is it? The one who raised his partner from an Egg?",
               "Alder: He was training his Pokemon on Route 20 just now. Give him his Town Map first!",
               "Alder: Follow this road east. It goes right to Route 20. I'll be waiting here!"],
     "after": "home"},
    # back from the ranch: Alder's students are ready (Mr. Medal and the Gym news when you come back out)
    {"trigger": "enter", "condition": ["b2_alder_training", "not:b2_gym_open"], "flag": "b2_gym_open",
     "cast": [{"sheet": "b2_c360.png", "from": [11, 26], "to": "player", "leave": [11, 30],
               "lines": ["???: Bravo! What a battle! I'm Mr. Medal!",
                         "Mr. Medal: I give Medals to Trainers who do great things on their travels: catching, battling, exploring...",
                         "Mr. Medal: Here's a Medal Box to keep them in!",
                         "{player_name} received the Medal Box!",
                         "Mr. Medal: Come and see me at any Pokemon Center, and I'll hand over the Medals you've earned!"],
               "then": "event:b2_medal_box"},
              {"sheet": "b2_c97.png", "from": [11, 22], "to": "player",
               "lines": ["Alder: {player_name}! You know the Trainers' School and Gym they just built in Aspertia?",
                         "Alder: Word is, the Gym Leader has arrived! If you want to get stronger, go and challenge the Gym.",
                         "Alder: Behind my house is Pledge Grove. A quiet place... though they say something special visits it."],
               "leave": [11, 22]}]},
    # after the badge: Bianca adds the Habitat List to your Pokedex (the game's trigger by the road east, 26, 21-23)
    {"trigger": {"zone": [24, 21, 30, 23]}, "condition": ["b2_basic_badge", "not:b2_habitat_list"], "flag": "b2_habitat_list",
     "cast": [{"sheet": "b2_bianca.png", "from": [30, 22], "to": "player",
               "lines": ["Bianca: Heeey! Sorry, I forgot to upgrade the Pokedex I gave you!",
                         "Bianca: I'm adding the Habitat List. Just borrowing it for a second...",
                         "{player_name}'s Pokedex was upgraded!",
                         "Bianca: Now you can see which Pokemon live in each area. Open the Pokedex and pick a place!",
                         "Bianca: One more tip: sometimes you'll see grass rustling. Go there and... I'll let it be a surprise!",
                         "Bianca: Meet lots of Pokemon in lots of places, okay? See you!"],
               "leave": [30, 22]}]},
]
ALDER_SCENES = [
    {"trigger": "enter", "condition": ["b2_herdier_found", "not:b2_alder_seymour"], "flag": "b2_alder_seymour",
     "cast": [{"sheet": "b2_c97.png", "from": [6, 3], "to": "player", "stay": True,
               "lines": ["Alder: Oh! You've delivered the Town Map! And you were only gone a moment...",
                         "Alder: Yet you and your Pokemon have grown. Now then, training! These two are my students."]},
              {"sheet": "b2_c16.png", "from": [5, 8], "to": "player", "stay": True,
               "lines": ["Girl: Are we going to help train that Trainer, sir?"]},
              {"sheet": "b2_c12.png", "from": [7, 8], "to": "player",
               "lines": ["Boy: Really? But they look really tough!",
                         "Alder: That's right! But you can learn from losing, too. And remember: just enjoy the battle!",
                         "Alder: So, {player_name}! Be their opponent!",
                         "Boy: I'll show you what's cool about my Pokemon!"],
               "then": "event:b2_seymour"}]},
    # (the next two straight after each battle, wherever you stand in the room: "enter" plays only as you come in)
    {"trigger": {"zone": [0, 0, 13, 15]}, "condition": ["b2_alder_seymour", "not:b2_alder_cassie"], "flag": "b2_alder_cassie", "heal": True,
     "cast": [{"sheet": "b2_c97.png", "from": [6, 3], "to": "player", "stay": True,
               "lines": ["Alder: A fine battle, both of you! First, let's heal your Pokemon, {player_name}.", "Alder: Next!"]},
              {"sheet": "b2_c16.png", "from": [5, 8], "to": "player",
               "lines": ["Girl: Ready! Some battles are decided by type matchups!"], "then": "event:b2_cassie"}]},
    {"trigger": {"zone": [0, 0, 13, 15]}, "condition": ["b2_alder_cassie", "not:b2_alder_training"], "flag": "b2_alder_training", "heal": True,
     "cast": [{"sheet": "b2_c97.png", "from": [6, 3], "to": "player",
               "lines": ["Alder: What a rousing battle! The Pokemon were enjoying themselves too!",
                         "Alder: Types matter, don't they? Water beats Fire, Fire beats Grass, Grass beats Water...",
                         "Alder: And a move that matches its user's type hits harder still!",
                         "Alder: Let's heal those hard workers. {player_name}, your partner did a great job for you!"]}]},
]
FLOCCESY = town(
    439, FLOCCESY_PEOPLE, FLOCCESY_SIGNS, FLOCCESY_DOORS, rooms={
        "alder": room(440, {2: _say("Alder   ", "Alder: Meeting Pokemon and people you'd never have met otherwise... that's the best of travelling!",
                                    condition=["b2_alder_training"]),
                            0: _say("Cassie", "Girl: Some battles are decided by type matchups! Remember that!", condition=["b2_alder_training"]),
                            1: _say("Seymour", "Boy: That Trainer really was tough...", condition=["b2_alder_training"])},
                      {}, (11, 22), scenes=ALDER_SCENES),
        "house_w": room(441, {0: {"text": "Old man", "action": "EVENT", "event": {
                                  "lines": ["Items never weigh you down, no matter how many you carry! Here, take this."],
                                  "gift_item": {"POTION": 1}, "flag": "b2_floccesy_potion",
                                  "done": ["Bags are wonderful. Everything sorted by type, all by itself!"]}},
                              1: _say("Woman by the table", "Castelia's the biggest city in Unova! I want to take the boat from Virbank and go."),
                              3: _say("Patrat's owner", "On sunny days my Patrat's fur gets all fluffy. I can't stop petting it!"),
                              2: _say("Patrat", "Patrat: Skuwaaa!")},
                        {}, (21, 54)),
        "house_e": room(442, {1: _say("Man by the window", "People made homes wherever they went looking for Pokemon.",
                                      "The ranch was just a grassy meadow once. Now people and Pokemon both live there."),
                              2: _say("Boy by the bed", "I just raise one Pokemon and charge ahead! It's the hard way, though..."),
                              0: _say("Lillipup", "Lillipup: Yip!")},
                        {}, (26, 54)),
        "center": room(443, {4: {"text": "Pokémon Center", "action": "HEAL"},
                             5: {"text": "Shop", "action": "SHOP"},
                             6: _say("Clerk ", "Welcome! Potions and Poke Balls are a Trainer's best friends."),
                             2: _say("Woman by the counter", "A bit of advice: carry lots of Potions! And lots of Poke Balls, too!"),
                             3: _say("Boy by the PCs", "Boys and girls, Pokemon too... I wonder what makes them different?"),
                             9: _say("Girl at the PC", "I read the Help on the PC. I feel smarter already!"),
                             8: _say("Man by the door", "Floccesy's a quiet town. Alder could live anywhere, but he likes it here."),
                             0: {"text": "Mr. Medal ", "action": "EVENT", "condition": ["b2_gym_open"], "event": {"medal_rally": True}}},
                       {}, (9, 54)),
    },
    extra_people=[FLOCCESY_ALDER],
    edges={"<": ("UNOVA_ROUTE_19", [(0, y) for y in range(53, 58)]),
           ">": ("UNOVA_ROUTE_20", [(31, y) for y in (0, 1, 21, 22, 23)])},   # (rows 0-1: the dead end Route 20's autumn leaves open)
    edge_to={"31,%d" % y: [0, y] for y in (0, 1, 21, 22, 23)},
    hidden={"31,15": "POTION"},   # (the dead end's hidden Potion: reached from Route 20 in autumn)
    split=True,   # (two parts: the town, and the dead end on its east edge, each from its own edge)
    scenes=FLOCCESY_SCENES,
)

# -------------------------------------------------------------------------------------------------------------- Route 20
# Zone 446, 64 x 64: Floccesy's east road (x 0, rows 21-23) to the Virbank gate (x 57, rows 10-12). Hiker Jerome keeps the
# steps to the east side (x 31, rows 4-6) till you have a badge. North (x 12-18, row 0): the path up to Floccesy Ranch.
# The south loop (Surf; Pokemon Rangers, a Rare Candy, a Max Revive, a Sticky Barb) and the Poke Ball boxed in west of the
# steps (15, 10) are autumn's (the leaves open them): ROUTE_20_AUTUMN, on the autumn map (11-20).
ROUTE_20_PEOPLE = {
    0: [_say("Hiker Jerome", "Hiker Jerome: Come on! A kid without a single Gym Badge going on past here?",
             "Hiker Jerome: Battle the Trainers and Pokemon around here, then battle some more!", condition=["not:b2_basic_badge"]),
        {"text": "Hiker Jerome ", "action": "EVENT", "condition": ["b2_basic_badge"], "event": {
            "lines": ["Hiker Jerome: Hey! That shiny thing's the Basic Badge! Don't let it go to your head. I'll show you!"],
            "flag": "b2_jerome", "done": ["Hiker Jerome: With Pokemon like yours, even a kid can hold their own against a grown-up!"],
            "battle": {"name": "Hiker Jerome", "class": "HIKER", "sprite": "hiker.png", "team": [447], "levels": [11],
                       "rewards": {"balls": 3},
                       "dialogue": {"player_won": ["Hiker Jerome: All right... I'm beat! Go on through."]}}}}],
    24: _say("Man by the sign", "Battles start when eyes meet! That's the rule for Trainers."),
    3: _say("Twin Lily", "Lily: My sister and I battle together!"),
    13: _ball("Poke Ball north of the lass", "PARALYZE_HEAL", "b2_r20_parlyz", name="a Paralyze Heal"),
    15: _ball("Poke Ball by the preschoolers", "ANTIDOTE", "b2_r20_antidote", name="an Antidote"),
    16: _ball("Poke Ball by the nursery aide", "DIRE_HIT", "b2_r20_dire_hit", name="a Dire Hit"),
    19: _ball("Poke Ball in the dark grass", "GREAT_BALL", "b2_r20_great_ball", name="a Great Ball"),
}
ROUTE_20_SIGNS = {5: ["ROUTE 20", "Floccesy Town - Virbank City"]}


def _ranger(label, name, sex, team, levels, berry, line, won, condition=()):
    """An autumn-only Pokemon Ranger of Route 20 (B2W2: they come with the fallen leaves; a Berry for beating them)."""
    return {"text": label, "action": "EVENT", "condition": ["season:AUTUMN"] + list(condition), "event": {
        "lines": [line], "flag": "b2_r20_" + name.lower(),
        "done": [won],
        "battle": {"name": "Pokemon Ranger " + name, "class": "POKEMON_RANGER", "sprite": "b2_ranger_%s.png" % sex,
                   "team": team, "levels": levels, "rewards": {"balls": 3, berry: 1},
                   "dialogue": {"player_won": [won, "Take this Berry. The forest gave it to me!"]}}}}


# Route 20 in autumn (its own map from the game's autumn blocks: the leaf piles open the south loop and the boxed-in spot west
# of the steps): four Pokemon Rangers (Leaf only after Team Plasma is beaten at Virbank's docks: batch 2's flag) and the
# leaves' items. Their spots are the game file's (people 8-11, 14, 17, 18, 20).
ROUTE_20_AUTUMN = {
    8: _ranger("Ranger Naoko", "Naoko", "f", [590, 542], [32, 32], "SITRUS_BERRY",
               "Pokemon Ranger Naoko: The leaves pile up so high in autumn, you'd never know I was here!",
               "Pokemon Ranger Naoko: You found me AND beat me!"),
    9: _ranger("Ranger Bret", "Bret", "m", [508], [33], "LEPPA_BERRY",
               "Pokemon Ranger Bret: Autumn's the best season for a Ranger. Let's battle!",
               "Pokemon Ranger Bret: Great battle! The forest agrees."),
    10: _ranger("Ranger Malory", "Malory", "f", [59], [33], "LEPPA_BERRY",
                "Pokemon Ranger Malory: Rangers protect Pokemon and nature. Show me how strong your bond is!",
                "Pokemon Ranger Malory: Your bond is the real thing."),
    11: _ranger("Ranger Leaf", "Leaf", "m", [585, 545], [32, 32], "SITRUS_BERRY",
                "Pokemon Ranger Leaf: You chased Team Plasma off at Virbank? Then show me what you've got!",
                "Pokemon Ranger Leaf: I can see why Team Plasma ran!", condition=["b2_virbank_dock"]),
    14: _ball("Poke Ball in the leaves", "balls", "b2_r20_ball", name="a Poke Ball"),
    17: _ball("Poke Ball by the south water", "RARE_CANDY", "b2_r20_rare_candy", name="a Rare Candy"),
    18: _ball("Poke Ball by the south bank", "MAX_REVIVE", "b2_r20_max_revive", name="a Max Revive"),
    20: _ball("Poke Ball below the bridge", "STICKY_BARB", "b2_r20_sticky_barb", name="a Sticky Barb"),
}
ROUTE_20_SCENES = [
    # no badge, no way past Jerome (the game's trigger: x 31, rows 4-6)
    {"who": "Hiker Jerome", "trigger": {"zone": [31, 4, 31, 6]}, "condition": ["not:b2_basic_badge"], "every": True,
     "lines": ["Hiker Jerome: A kid without a single Gym Badge? Battle some more first!"], "push": [-1, 0]},
    # past Jerome with the badge: Cheren and Hugh by the dark grass (the game's trigger: x 32-37, row 20)
    {"trigger": {"zone": [32, 19, 37, 21]}, "condition": ["b2_basic_badge", "not:b2_cheren_route20"], "flag": "b2_cheren_route20",
     "cast": [{"sheet": "b2_hugh.png", "from": [45, 9], "to": "player", "stay": True, "lines": ["{rival_name}: {player_name}! Wait up!"]},
              {"sheet": "b2_cheren.png", "from": [45, 9], "to": "player", "stay": True,
               "lines": ["Cheren: Come with me, you two. See the dark tall grass here?",
                         "Cheren: Now and then two Pokemon jump out of it at once. And the ones hiding in it are a little stronger.",
                         "Cheren: If you're heading for the next Gym, it's in Virbank City. These might help!",
                         "{player_name} received 3 Pecha Berries!",
                         "Cheren: Do your best, both of you!"],
               "then": "event:b2_pecha", "leave": [45, 9]},
              {"as": 0, "lines": ["{rival_name}: Cheren really knows his stuff... I've decided. I'm going to get stronger than him!",
                                  "{rival_name}: You fill up that Pokedex and watch my back. Got it?"],
               "leave": [57, 11]}]},
]
# Route 20 (batch 2): the Grunt who ran from the docks, in the clearing south of the steps (the game's person 22), then Hugh.
ROUTE_20_PEOPLE[22] = {"text": "Plasma Grunt", "action": "EVENT", "condition": ["b2_virbank_dock", "not:b2_r20_grunt_battled"],
                       "event": {"lines": ["Plasma Grunt: Huh?! You followed me all the way out here?"],
                                 "flag": "b2_r20_grunt_battled", "battle": {
                                     "name": "Plasma Grunt", "class": "GRUNT", "sprite": "b2_plasma_grunt_f.png", "team": [509],
                                     "levels": [14], "rewards": {"balls": 3},
                                     "dialogue": {"player_won": ["Plasma Grunt: Ugh! Why did I run inland? I'm supposed to get to the coast!"]}}}}
ROUTE_20_SCENES.append(
    {"trigger": {"zone": [24, 25, 29, 30]}, "condition": ["b2_r20_grunt_battled", "not:b2_r20_hugh"], "flag": "b2_r20_hugh",
     "cast": [{"sheet": "b2_hugh.png", "from": [27, 22], "to": "player",
               "lines": ["{rival_name}: {player_name}! Did you find one? ...She got away? Tch.",
                         "{rival_name}: Listen! People in town saw Team Plasma heading out to sea on some kind of ship!",
                         "{rival_name}: Let's get back to Virbank. If they're on a ship, we need one too!"],
               "leave": [57, 11]}]})

ROUTE_20 = route(
    446, ROUTE_20_PEOPLE, ROUTE_20_SIGNS,
    exits={"<": ("FLOCCESY_TOWN", [(0, y) for y in range(21, 24)]),
           "^": ("FLOCCESY_RANCH_OUTSIDE", [(x, 0) for x in range(12, 19)]),
           ">": ("VIRBANK_CITY", [(57, y) for y in range(10, 13)])},
    trainers={1: ("Youngster Petey", 4), 7: ("Youngster Terrell", 3), 12: ("Lass Isabel", 3), 4: ("Preschooler Albert", 1),
              5: ("Preschooler Lin", 3), 6: ("Nursery Aide Kimya", 3), 2: ("Twins Lia & Lily", 5)},
    hidden={"53,36": "HEART_SCALE", "22,27": "BIG_MUSHROOM"},
    scenes=ROUTE_20_SCENES,
    season_people={"AUTUMN": ROUTE_20_AUTUMN},
    season_exits={"AUTUMN": {"<": ("FLOCCESY_TOWN", [(0, y) for y in (0, 1, 21, 22, 23)])}},   # (the leaves: the top corner too)
    edge_to={"0,%d" % y: [31, y] for y in (0, 1, 21, 22, 23)},
)

# ------------------------------------------------------------------------------------------------------- Floccesy Ranch
# 444: the path up from Route 20 to the ranch's arch (13-15, 21); 445: the ranch (in by its arch at 45-47, 54).
RANCH_OUTSIDE = route(
    444, {}, {1: ["FLOCCESY RANCH", "Meet lots of Pokemon! Just off Floccesy Town."]},
    exits={"v": ("UNOVA_ROUTE_20", [(x, 31) for x in range(12, 17)]), "^": ("FLOCCESY_RANCH", [(13, 21), (14, 21), (15, 21)])},
    hidden={"28,31": "balls"},
)
RANCH_PEOPLE = {
    0: _say("{rival_name}", "{rival_name}: Let's find that Herdier!", condition=["b2_hugh_ranch", "not:b2_herdier_found"],
            _look="sheet:b2_hugh.png"),
    3: _say("Herdier", "Herdier: Yaarrrp...", condition=["not:b2_herdier_found"]),
    10: _say("Herdier ", "Herdier: Bawoof! Ba woof!"),
    11: _say("Mareep", "Mareep: Baa!"), 12: _say("Mareep ", "Mareep: Baa baa!"), 13: _say("Mareep  ", "Mareep: Baawn!"),
    14: _say("Mareep   ", "Mareep: Baa haa!"), 15: _say("Mareep    ", "Mareep: Ba baaa!"),
    7: _ball("Poke Ball between the pastures", "balls", "b2_ranch_ball", name="a Poke Ball"),
    8: _ball("Poke Ball south of the youngster", "X_ATTACK", "b2_ranch_x_attack", name="an X Attack"),
    9: _ball("Poke Ball in the forest", "POTION", "b2_ranch_potion_ball", name="a Potion"),
}
RANCH_OWNERS = [(46, 51, _say("Ranch owner", "Owner: Thanks to you and your Pokemon! Say, did Alder train you?",
                               "Owner: The ranch started when a fence was put up to keep Pokemon safe.",
                               condition=["b2_ranch_owners"], _look="sheet:b2_c34.png")),
                (45, 52, _say("Owner's wife", "Wife: If your Pokemon get hurt out here, rest a while. Nobody gets far tired out!",
                               condition=["b2_ranch_owners"], _look="sheet:b2_c35.png"))]
RANCH_SCENES = [
    # Hugh, as you head for the pastures (the game's trigger: 41, 45-46)
    {"trigger": {"zone": [40, 44, 42, 47]}, "condition": ["b2_alder_maps", "not:b2_hugh_ranch"], "flag": "b2_hugh_ranch",
     "cast": [{"sheet": "b2_hugh.png", "from": [25, 44], "to": "player",
               "lines": ["{rival_name}: Oh! Nice! You came here to toughen up too?",
                         "{rival_name}: All right! Let's see how much stronger you've got. Come at me!"],
               "then": "event:b2_hugh_ranch"}]},
    # (right after the battle, where it was fought: a route's "enter" plays only as you arrive)
    {"trigger": {"zone": [40, 44, 42, 47]}, "condition": ["b2_hugh_ranch", "not:b2_ranch_owners"], "flag": "b2_ranch_owners",
     "cast": [{"sheet": "b2_hugh.png", "from": [41, 44], "to": "player", "stay": True,
               "lines": ["{rival_name}: Not bad... You think about how to bring out your Pokemon's strength. I can count on you!",
                         "{rival_name}: What are you doing here, anyway? ...A Town Map? From my sister?",
                         "{player_name} handed over the Town Map!",
                         "{rival_name}: Tch... She didn't have to. Thanks, though. We only just left, and you're already helping me out."]},
              {"sheet": "b2_c34.png", "from": [46, 52], "to": "player", "stay": True,
               "lines": ["???: I thought I heard a battle! Isn't it nice to be young!",
                         "{rival_name}: Who are you?",
                         "???: I own this ranch! And this is my wife."]},
              {"sheet": "b2_c35.png", "from": [46, 53], "to": "player", "stay": True,
               "lines": ["Wife: After a battle you should heal your Pokemon. Here, one for each of you!",
                         "{player_name} received a Potion!"], "then": "event:b2_ranch_potion"},
              {"as": 1, "lines": ["Owner: By the way, you didn't see a Herdier around, did you? One of ours wandered off.",
                                  "Owner: Our two are always together. I'm a little worried..."]},
              {"as": 0, "lines": ["{rival_name}: A LITTLE worried? Are you kidding me?! Your Pokemon could be lost forever!",
                                  "{rival_name}: Forget it! I'll look myself. {player_name}, help out!"],
               "leave": [22, 30]},
              {"as": 1, "lines": ["Owner: Why'd he get so mad? It's probably just playing somewhere in the ranch..."], "leave": [46, 51]},
              {"as": 2, "lines": ["Wife: I wonder... Dear, if your Pokemon get hurt, let me know!"], "leave": [45, 52]}]},
    # the path north (the game's trigger: 21-23, 33)
    {"trigger": {"zone": [21, 32, 23, 34]}, "condition": ["b2_ranch_owners", "not:b2_ranch_north"], "flag": "b2_ranch_north",
     "cast": [{"sheet": "b2_hugh.png", "from": [22, 26], "to": "player",
               "lines": ["{rival_name}: Did Herdier wander back here? Let's have a look!"], "leave": [22, 24]}]},
    # by the janitor (the game's trigger: 23, 11-13): a Paralyze Heal
    {"trigger": {"zone": [22, 10, 24, 13]}, "condition": ["b2_ranch_north", "not:b2_ranch_parlyz"], "flag": "b2_ranch_parlyz",
     "cast": [{"sheet": "b2_hugh.png", "from": [21, 14], "to": "player",
               "lines": ["{rival_name}: Wow, this ranch is huge... Oh! Here, I'll share something good with you!",
                         "{player_name} received a Paralyze Heal!",
                         "{rival_name}: Use it if your Pokemon gets paralyzed. Still... Pokemon don't just wander off on their own.",
                         "{rival_name}: Worst case, it's mixed up in some kind of trouble!"],
               "then": "event:b2_hugh_parlyz", "leave": [21, 14]}]},
    # a cry in the woods (the game's triggers: 43, 12-13 and 41-42, 14)
    {"trigger": {"zone": [41, 12, 43, 14]}, "condition": ["b2_ranch_parlyz", "not:b2_ranch_cry"], "flag": "b2_ranch_cry",
     "cast": [{"sheet": "b2_hugh.png", "from": [41, 16], "to": "player",
               "lines": ["Yawrp!", "{rival_name}: Did you hear that just now?",
                         "{rival_name}: I'll check around here! You go deeper into the woods and look!"], "leave": [41, 16]}]},
    # Herdier, and the Plasma Grunt who had it cornered (the game's trigger: 50-52, 24)
    {"trigger": {"zone": [49, 23, 53, 25]}, "condition": ["b2_ranch_cry", "not:b2_herdier_found"], "flag": "b2_herdier_found",
     "cast": [{"person": "Herdier", "face": "d", "lines": ["Herdier: Yaarrrp..."], "stay": True},
              {"sheet": "b2_hugh.png", "from": [50, 29], "to": "player", "stay": True,
               "lines": ["{rival_name}: That cry! You found it! What a relief!",
                         "{rival_name}: I'll go get its Trainer. You stay here with it!"], "leave": [50, 29]},
              {"sheet": "b2_c293.png", "from": [52, 19], "to": "player", "stay": True,
               "lines": ["???: Tch... You little pest! I'm with a group that strikes fear into all who face it: Team Plasma!",
                         "Plasma Grunt: The righteous ones who tried to take Unova two years ago, to free Pokemon!",
                         "Plasma Grunt: First I get lost chasing that Herdier, and now some nosy kid finds me! Take this!",
                         "The Plasma Grunt threw something at {player_name}! It was TM273 Frustration!",
                         "Plasma Grunt: I'll use this chance to retreat!"],
               "then": "event:b2_grunt_tm", "leave": [52, 12]},
              {"sheet": "b2_c34.png", "from": [50, 29], "to": "player", "stay": True,
               "lines": ["Herdier: Yap! Bwoof!",
                         "Owner: Herdier! What brought you all the way back here? Thank you, both of you!"]},
              {"sheet": "b2_hugh.png", "from": [50, 29], "to": "player",
               "lines": ["{rival_name}: You're awfully calm about this! Your Pokemon could have been gone for good! Take better care of it!"],
               "leave": [50, 33]},
              {"as": 3, "lines": ["Owner: Hmm... It's as if he's afraid of losing Pokemon...",
                                  "Owner: Come on, Herdier! Everyone's waiting. Let's go home!"], "leave": [50, 33]},
              {"person": "Herdier", "path": [[51, 22], [50, 22], [50, 33]], "gone": True, "lines": []}]},
]
# ------------------------------------------------------------------------------------------------------ Hidden Grottoes
# (11-23, Jordan: "Build them, backfill"; src/world/grottoes.py.) Black 2's zone 518 is every grotto's map: a path north
# (way out at 15, 27: the game's trigger 5) to a clearing whose middle (15, 12: trigger 2000) holds the grotto's one thing.
# Its entrance on the place's map is a person with sprite 293 (Floccesy Ranch's 16 at 52, 20), here a door into the room.
# What it holds is one option per thing, each shown only while the grotto holds it ("world:grottoes:<n>:<kind>[:<id>]").
_GROTTOES = {g["grotto"]: g for g in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                                                                   "assets", "unova_area_data.json"), encoding="utf-8"))["HIDDEN_GROTTOES"]}
OUTSIDE[518] = -1   # (one map for every grotto: its way out is placed by grotto_room, not by a warp)


def grotto_room(gid, door):
    g = _GROTTOES[gid]
    ev = {"world": "grottoes", "grotto": gid, "at": [15, 12]}
    opts, seen = [], set()
    for v in ("BLACK_2", "WHITE_2"):
        for s in g["pokemon"][v]:
            if s["id"] in seen:
                continue
            seen.add(s["id"])
            opts.append({"text": s["name"] + " in the grotto", "action": "EVENT", "no_tag": True, "_look": "pokemon:%d" % s["id"],
                         "condition": ["world:grottoes:%d:pokemon:%d" % (gid, s["id"])],
                         "event": dict(ev, lines=["%s! It's watching you from the middle of the clearing." % s["name"]])})
    opts.append({"text": "Poke Ball in the clearing", "action": "EVENT", "no_tag": True, "_look": "sheet:b2_item_ball.png",
                 "condition": ["world:grottoes:%d:item" % gid], "event": dict(ev)})
    opts.append({"text": "Something in the grass", "action": "EVENT", "no_tag": True, "_look": "sheet:b2_none.png",
                 "condition": ["world:grottoes:%d:hidden" % gid], "event": dict(ev)})
    m = room(518, {}, {}, None, extra_people=[(15, 12, opts)])
    rows = [list(r) for r in m["art"]]
    rows[27][15] = "v"
    m["art"] = ["".join(r) for r in rows]
    m["exits"] = {"v": "OUT:%d,%d" % tuple(door)}
    m["title"] = "Hidden Grotto"
    return m


RANCH = route(
    445, RANCH_PEOPLE, {},
    exits={"v": ("FLOCCESY_RANCH_OUTSIDE", [(45, 54), (46, 54), (47, 54)])},
    trainers={6: ("Youngster Kenny", 2), 4: ("Lass Molly", 3), 5: ("Janitor Orville", 2)},
    extra_people=RANCH_OWNERS,
    scenes=RANCH_SCENES,
    rooms={"grotto": grotto_room(0, (52, 20))},
    inside={"52,20": "grotto"},   # (the gap in the trees, north-east, by Surf: Black 2's person 16)
)
RANCH["art"][20] = RANCH["art"][20][:52] + "D" + RANCH["art"][20][53:]   # (the grotto's way in is a door)

# --------------------------------------------------------------------------------------------------------- Pledge Grove
# Zone 614, behind Alder's house: a clearing in the trees, and the rock with three deep cuts (Keldeo: post-game, its BOSS).
PLEDGE_GROVE = route(
    614, {}, {1: ["Three sharp marks are cut deep into the rock."]},
    exits={"v": ("FLOCCESY_TOWN", [(15, 55), (16, 55)])},
    boss_spot=[15, 14],
)

# ------------------------------------------------------------------------------------------------- Aspertia Gym (489)
# Cheren's Gym: the yard behind the Trainers' School (in by its back door, 9, 1). Two trainers first, then Cheren.
GYM_ASPERTIA = room(
    489, {0: [{"text": "Gym", "action": "GYM", "_look": "sheet:b2_cheren.png", "condition": ["not:b2_basic_badge"]},
              _say("Cheren", "Cheren: Decide what you want to do from here on. Don't worry about losing your way: you have Pokemon by your side!",
                   condition=["b2_basic_badge"])],
          1: {"text": "Youngster Pedro", "action": "EVENT", "event": {
              "lines": ["Youngster Pedro: Cheren saw potential in me and made me a Trainer at this Gym! Here I come!"],
              "battle": {"name": "Youngster Pedro", "class": "YOUNGSTER", "sprite": "youngster.png", "team": [504, 506], "levels": [9, 9],
                         "rewards": {"balls": 2}, "dialogue": {"player_won": ["Youngster Pedro: Okay, you're good! But can you beat the girl too?"]}},
              "flag": "gym_trainer_ASPERTIA_CITY_1", "done": ["Youngster Pedro: Beat the girl too, and you can challenge Cheren!"]}},
          2: {"text": "Lass Serena", "action": "EVENT", "event": {
              "lines": ["Lass Serena: Now I'll show you everything I learned from Cheren!"],
              "battle": {"name": "Lass Serena", "class": "LASS", "sprite": "lass.png", "team": [506, 504], "levels": [9, 9],
                         "rewards": {"balls": 2}, "dialogue": {"player_won": ["Lass Serena: I have to learn even more about my Pokemon!"]}},
              "flag": "gym_trainer_ASPERTIA_CITY_2", "done": ["Lass Serena: Wow! You can challenge the Gym Leader now!"]}},
          3: {"text": "Clyde", "action": "EVENT", "event": {
              "lines": ["Hello! I'm Clyde, guide to every Trainer who takes on a Gym. Thanks for challenging!",
                        "Here's something to celebrate your debut!"],
              "gift_item": {"FRESH_WATER": 1}, "flag": "b2_clyde_aspertia",
              "done": ["If you run out of Pokemon that can fight, you lose! Having a few with you helps."]}}},
    {}, (0, 0), stairs={436: ("v", "ROOM:school")},
    scenes=[{"trigger": "enter", "condition": ["not:b2_cheren_hello"], "flag": "b2_cheren_hello",
             "cast": [{"person": "Gym", "face": "d",
                       "lines": ["???: You must be a challenger! Welcome to Aspertia's Gym. I'm Cheren, the Gym Leader!",
                                 "Cheren: ...Well, I just became the Gym Leader. We have a challenger! You two, take your places!",
                                 "Cheren: Beat these two, and then I'll be your opponent!"]}]}],
)

ASPERTIA["rooms"]["gym"] = GYM_ASPERTIA

# ====================================================================================================== batch 2 (11-20)
# Black 2's story from Route 20's east gate to the boat for Castelia: Virbank City (Mom's first Xtransceiver call, Roxie and
# Pop Roxie's argument), Roxie's Gym (the Toxic Badge), Pokestar Studios (the scout's tour, Pop Roxie's film, your first
# film: src/states/pokestar.py), Team Plasma at the docks (HM Cut), the Grunt on Route 20, and Pop Roxie back as captain.
# Story flags in order: b2_virbank_arrived (Mom's call) -> b2_roxie_argument -> b2_toxic_badge -> b2_scout_met ->
# b2_pokestar_tour -> b2_pop_roxie_movie -> b2_first_film -> b2_dock_scene -> b2_dock_grunt_battled -> b2_virbank_dock
# (Cut) -> b2_r20_grunt_battled -> b2_r20_hugh -> b2_pop_roxie_back -> b2_hugh_terminal -> (the ship) visited_CASTELIA_CITY.
# Zones: 447 the gate from Route 20, 448 the city, 449-452 houses and the ship terminal, 453 the gate to Pokestar Studios,
# 454 the Pokemon Center, 455 the Gym's lobby, 502 its stage; 456 the Complex outside, 457 the Complex; 566 Pokestar
# Studios, 568 its soundstage, 567 the effects room, 574 the theater (586, the stars' dressing room: post-game, not built).

# ----------------------------------------------------------------------------------------------------------- Virbank City
OUTSIDE.update({447: 448, 449: 448, 450: 448, 451: 448, 452: 448, 453: 448, 454: 448, 455: 448, 502: 0,
                568: 566, 574: 566, 567: 0})
VIRBANK_DOORS = {447: ("gate", "gate_w"), 454: ("center", "center"), 449: ("house", "house_ne"), 450: ("house", "nursery"),
                 451: ("house", "house_s"), 452: ("house", "terminal"), 455: ("gym", "gym"), 453: ("gate", "gate_n")}
DOCK = ["b2_first_film", "not:b2_dock_grunt_battled"]   # (Team Plasma at the docks: after your first film, till the battle)
VIRBANK_PEOPLE = {
    6: _say("Pokestar guard", "Past here is Pokestar Studios! Auditions are on right now, so no one gets in without a pass.",
            condition=["not:b2_toxic_badge"]),
    13: _say("Woman with a Watchog", "My Watchog's been with me since I was little. Its Keen Eye has saved us more times than I can count!"),
    14: _say("Watchog", "Watchog: Hoooog!"),
    5: _say("Guitarist by the steps", "Roxie's band is the best! Tickets sell out so fast now. Maybe they'll go on a world tour!"),
    18: _say("Boy on the bridge", "One, two, three, four, five, six! That's how many Poke Balls fit on your belt. Six Pokemon, no more!"),
    16: _say("Woman by the railing", "Mr. Medal hands out Medals for all sorts of things. Mine's so shiny! Collect lots of them!"),
    3: _say("Worker on the walkway", "Work at the complex would wear me out if I didn't have my Pokemon with me!"),
    4: _say("Old man by the stairs", "Kid! Before a big battle, think about which six you take. A good team is half the battle!"),
    2: {"text": "Roughneck by the Gym", "action": "EVENT", "event": {
        "lines": ["Roxie's poison stings, stings, and stiiings! But I caught a Magnemite in the complex, and it was fine!",
                  "Steel-types don't get poisoned, see? Here, go catch a Magnemite or something!"],
        "gift_item": {"balls": 5}, "flag": "b2_virbank_balls",
        "done": ["A Magnemite from the complex shrugs off Roxie's poison!"]}},
    17: _say("Sailor on the pier", "The sea air's the best! Watch the big ships come in from Castelia."),
    15: _say("Man at the pier's end", "On a clear day you can see Castelia City from here. Not that it's ever clear!"),
    # Team Plasma at the docks (the game's people 7-11): Roxie, Hugh and three Grunts; talk to the one in the middle
    7: _say("Roxie", "Roxie: Help us out, {player_name}! These creeps are after people's Pokemon!", condition=DOCK),
    8: _say("{rival_name} ", "{rival_name}: Pokemon thieves... I'll never forgive them!", condition=DOCK),
    9: {"text": "Plasma Grunt", "action": "EVENT", "condition": DOCK, "event": {
        "lines": ["Plasma Grunt: Well, it's fine, isn't it? If we take their Pokemon too... Okay, kiddo. Give it your best shot!"],
        "flag": "b2_dock_grunt_battled", "battle": {
            "name": "Plasma Grunt", "class": "GRUNT", "sprite": "b2_plasma_grunt_m.png", "team": [504], "levels": [14],
            "rewards": {"balls": 3},
            "dialogue": {"player_won": ["Plasma Grunt: Kids like you caught us off guard?! Tch... everybody, run!"]}}}},
    10: _say("Plasma Grunt ", "Plasma Grunt: We got chased all over that ranch by a Lillipup. This day stinks.", condition=DOCK),
    11: _say("Plasma Grunt  ", "Plasma Grunt: Two years ago our king betrayed us. But we'll never give up!", condition=DOCK),
}
VIRBANK_SIGNS = {15: ["VIRBANK CITY", "City of falling fog and rising stars!"], 16: ["POKESTAR STUDIOS AHEAD",
                 "Bringing a new golden age of cinema!"], 17: ["VIRBANK CITY POKEMON GYM", "Leader: Roxie",
                 "Poison days, poison on the stage!"]}
VIRBANK_SCENES = [
    # just in from Route 20's gate: Mom's first Xtransceiver call (the game's trigger: x 3, rows 9-12)
    {"trigger": {"zone": [3, 9, 3, 12]}, "condition": ["not:b2_virbank_arrived"], "flag": "b2_virbank_arrived",
     "cast": [], "call": ["Bzzzt... bzzzt... The Xtransceiver is ringing!"], "then": "event:b2_mom_call"},
    # by the Pokemon Center: Roxie and her father, the captain (the game's trigger: x 13, rows 10-12)
    {"trigger": {"zone": [13, 10, 13, 12]}, "condition": ["b2_virbank_arrived", "not:b2_roxie_argument"], "flag": "b2_roxie_argument",
     "cast": [{"sheet": "b2_c359.png", "from": [19, 11], "path": [[19, 11]], "face": "l", "stay": True,
               "lines": ["???: Roxie, don't try to stop me! I'm off to Pokestar Studios to live up to my true potential!",
                         "???: I'll be a ship's captain AND a movie star!"]},
              {"sheet": "b2_c224.png", "from": [17, 11], "path": [[17, 11]], "face": "r", "stay": True,
               "lines": ["Roxie: Get real, Pop! You're a captain already! If your ship doesn't sail, people can't get anywhere!"]},
              {"as": 0, "lines": ["Captain: Oh, my dear daughter. You're a Gym Leader and you lead a band, don't you?",
                                  "Captain: If you can do two jobs, so can I! Off to my audition!"],
               "leave": [24, 1]},
              {"as": 1, "lines": ["Roxie: AAAAAH! You dim, dense, dumb, daft, dorky... DOOFUS!",
                                  "Roxie: Two jobs aren't the problem! Leaving people stuck is the problem!",
                                  "Roxie: ...Oh! A Trainer? Sorry you saw that. If you want a battle, come to my Gym!"],
               "leave": [36, 28]}]},
    # the road north to Pokestar Studios: shut till the Gym is done (the game's trigger: 23-27, row 2)
    {"who": "Pokestar guard", "trigger": {"zone": [23, 2, 27, 2]}, "condition": ["not:b2_toxic_badge"], "every": True,
     "lines": ["Sorry! Auditions are in progress. No one without a pass gets through!"], "push": [0, 1]},
    # Team Plasma at the docks (on the way onto the pier)
    {"trigger": {"zone": [43, 29, 45, 31]}, "condition": DOCK + ["not:b2_dock_scene"], "flag": "b2_dock_scene",
     "cast": [{"person": "Roxie", "face": "r", "stay": True,
               "lines": ["Roxie: So you lot are Team Plasma, huh?"]},
              {"person": "Plasma Grunt  ", "face": "l", "stay": True,
               "lines": ["Plasma Grunt: That's right! Two years ago the one we called our king betrayed us, and our plan to rule Unova failed!",
                         "Plasma Grunt: But we'll never give up! We'll free every Pokemon from their Trainers!"]},
              {"person": "{rival_name} ", "face": "r", "stay": True,
               "lines": ["{rival_name}: Shut it! You talk about saving Pokemon, but you're nothing but thieves!",
                         "{rival_name}: I'll crush you and your new plans!"]},
              {"person": "Roxie", "face": "l", "lines": ["Roxie: {player_name}! Help out! Take the one in the middle!"]}]},
    # after the battle (where it was fought): the Grunts run, Roxie's thanks: HM Cut
    {"trigger": {"zone": [40, 28, 52, 31]}, "condition": ["b2_dock_grunt_battled", "not:b2_virbank_dock"], "flag": "b2_virbank_dock",
     "cast": [{"sheet": "b2_c293.png", "from": [50, 29], "path": [[55, 29], [63, 29]],
               "lines": ["Plasma Grunts: Run for it!"], "leave_path": [[63, 29]], "gone": True},
              {"sheet": "b2_hugh.png", "from": [46, 31], "to": "player", "stay": True,
               "lines": ["{rival_name}: Tsk! What a bunch of creeps!"]},
              {"sheet": "b2_c224.png", "from": [47, 29], "to": "player",
               "lines": ["Roxie: If I'd lost, my Pokemon would've been taken! Thanks, you two. Here, use this!",
                         "{player_name} received HM01 Cut!",
                         "{rival_name}: A Hidden Machine! Cut. A Pokemon that knows it can cut down small trees, even outside battle.",
                         "Roxie: They split up! You two, go check Route 20! I'll look around town."],
               "then": "event:b2_cut", "leave": [36, 28]},
              {"as": 1, "lines": ["{rival_name}: Come on, {player_name}! Back west, through the gate!"], "leave": [2, 10]}]},
    # back from Route 20: Pop Roxie, home from the studios (the game's trigger: x 47, rows 29-31)
    {"trigger": {"zone": [43, 29, 47, 31]}, "condition": ["b2_r20_hugh", "not:b2_pop_roxie_back"], "flag": "b2_pop_roxie_back",
     "cast": [{"sheet": "b2_c224.png", "from": [48, 29], "path": [[48, 29]], "face": "d", "stay": True,
               "lines": ["Roxie: I thought your movie was pretty good, Pop."]},
              {"sheet": "b2_c359.png", "from": [48, 31], "path": [[48, 31]], "face": "u", "stay": True,
               "lines": ["Pop Roxie: So you saw it... No, it wasn't the movie. It was me. I never really became Riolu-Man.",
                         "Pop Roxie: Acting like that won't thrill anyone..."]},
              {"as": 0, "lines": ["Roxie: C'mon, don't get down! You can keep trying while you captain the ship.",
                                  "Roxie: Just don't leave people stuck, and I won't get mad."]},
              {"as": 1, "lines": ["Pop Roxie: ...Oh! Did you hear us? Team Plasma got away, it seems. At least they're gone.",
                                  "Pop Roxie: Right! I'll do my best as a captain, and thrill everyone by barreling through rough waves!",
                                  "Pop Roxie: The ship sails for Castelia City whenever you're ready. Come to the terminal!"],
               "leave": [50, 28]},
              {"as": 0, "lines": ["Roxie: Thanks for everything, {player_name}. Go see the world!"], "leave": [36, 28]}]},
]
VIRBANK = town(
    448, VIRBANK_PEOPLE, VIRBANK_SIGNS, VIRBANK_DOORS, rooms={
        "gate_w": room(447, {0: {"text": "Gate attendant", "action": "EVENT", "event": {
                                 "lines": ["Hello! Oh, you're travelling with Pokemon! The more you have, the more fun your journey gets.",
                                           "Here! Take these, and catch some more!"],
                                 "gift_item": {"GREAT_BALL": 2}, "flag": "b2_virbank_gate_balls",
                                 "done": ["Cheerful company shortens the miles, they say!"]}},
                             1: _say("Man in the gate", "You know what they say: cheerful company shortens the miles!"),
                             2: _say("Girl in the gate", "When you walk, the grass rustles... It's Pokemon hide-and-seek!",
                                     "Audino hide in rustling grass. They give lots of Exp. Points, too!")},
                         {1: ["ROUTE 20  -  VIRBANK CITY"]}, (1, 10), exits_extra={446: ("<", "UNOVA_ROUTE_20")},
                         scenes=[{"who": "Gate attendant", "trigger": {"zone": [13, 4, 13, 8]}, "condition": ["not:b2_virbank_gate_balls"],
                                  "approach": True, "then": "talk"}]),
        "center": room(454, {2: {"text": "Pokémon Center", "action": "HEAL"},
                             3: {"text": "Shop", "action": "SHOP"},
                             4: _say("Clerk ", "Welcome! The counter on the left sells everyday items."),
                             5: _say("Clerk  ", "Specialty Poke Balls are over here! Each one's good at something different."),
                             9: {"text": "Mr. Medal", "action": "EVENT", "event": {"medal_rally": True}},
                             0: _say("Boy by the door", "Roxie told me: fight Poison-types with Poison-types! She's a Gym Leader AND she plays in a band!"),
                             1: _say("Boy by the door ", "The more Gym Badges you have, the more things the shop will sell you. I didn't know that!"),
                             6: _say("Girl with questions", "Hi! Question! Do you like playing outside, or at home?",
                                     "...I see, I see! I'd say you're a curious one!"),
                             7: _say("Worker by the counter", "Healing here is free! That's a relief after a day at the complex."),
                             8: _say("Woman by the sofa", "Virbank's always foggy. I like it, though. It's cosy."),
                             10: _say("Man by the door", "Lots of people come through here for the ship to Castelia."),
                             11: _say("Man at the PC", "I keep my best Pokemon in a Box, ready for any big battle.")},
                       {}, (18, 8)),
        "house_ne": room(449, {0: _say("Woman with an Audino", "I can't wait for Pokestar Studios! My dear Audino is going to be in a movie!"),
                               1: _say("Woman by the table", "When a Pokemon evolves, it changes shape and gets stronger.",
                                       "If you stop it evolving, though, it learns some moves sooner!"),
                               2: _say("Audino", "Audino: Brrrm... brrrm."),
                               3: _ball("Poke Ball in the house", "POKE_TOY", "b2_virbank_poke_toy", name="a Poke Toy")},
                         {}, (32, 8)),
        "nursery": room(450, {1: {"text": "Nursery Aide", "action": "EVENT", "event": {
                                  "lines": ["Trainer! In case one of your Pokemon gets burned, please use this!"],
                                  "gift_item": {"BURN_HEAL": 1}, "flag": "b2_virbank_burn_heal",
                                  "done": ["A burn lowers a Pokemon's HP and its Attack. It's a real mess!"]}},
                              0: _say("Worker by the window", "My Pokemon used to be wimpy. Then they trained at the complex. Now look at them!"),
                              5: _say("Nursery Aide ", "The children teach me so much. Your Pokemon can be your teachers, too!"),
                              2: _say("Little boy", "Shop clerks sell different things! Did you know?"),
                              3: _say("Little girl", "If you use a Repel, wild Pokemon won't come out as much!"),
                              4: _say("Little girl ", "The Pokemon at the top of your list goes out first! I know great things!")},
                        {}, (9, 28)),
        "house_s": room(451, {0: _say("Woman by the table", "Two years ago a group called Team Plasma tried to take over Unova,",
                                      "led by a hero who was with the legendary Pokemon {legend}."),
                              1: _say("Boy in the house", "I'm going to be a hero, and make friends with {legend}! It's a legendary Pokemon! I don't know much about it, though..."),
                              2: _say("Old woman", "Oh, a Pokemon Trainer? My grandson goes round the Gyms with his Pokemon too, collecting Badges.")},
                        {}, (33, 28)),
        "terminal": room(452, {2: [_say("Sailor at the counter", "If you want the captain, he's at Pokestar Studios! Says he'll be a captain AND an actor.",
                                        condition=["not:b2_pop_roxie_back"]),
                                   {"text": "Pop Roxie", "action": "EVENT", "condition": ["b2_pop_roxie_back", "not:b2_sailed_castelia"],
                                    "_look": "sheet:b2_c359.png",
                                    "event": {"lines": ["Pop Roxie: Ahoy! Shall we set sail for Castelia City? Please, step this way!"],
                                              "flag": "b2_sailed_castelia", "travel": "CASTELIA_CITY", "land": ["prime_pier", 14, 11]}},
                                   {"text": "Pop Roxie ", "action": "EVENT", "condition": ["b2_sailed_castelia"], "_look": "sheet:b2_c359.png",
                                    "event": {"lines": ["Pop Roxie: Off to Castelia City again? All aboard!"], "travel": "CASTELIA_CITY",
                                              "land": ["prime_pier", 14, 11]}}],
                               0: _say("Sailor by the door", "The ship to Castelia City leaves from here! It crosses seas too rough for Pokemon to swim."),
                               1: _say("Old woman on the bench", "Your life is your own. Work hard at one thing, or try lots of different things!"),
                               },
                         {}, (50, 28), extra_people=[(7, 6, _say("{rival_name}", "{rival_name}: You're heading to Castelia City too, right? I'm going after Team Plasma!",
                                                                 condition=["b2_pop_roxie_back", "not:b2_sailed_castelia"], _look="sheet:b2_hugh.png"))],
                         scenes=[{"who": "{rival_name}", "trigger": "enter", "condition": ["b2_pop_roxie_back", "not:b2_hugh_terminal"],
                                  "flag": "b2_hugh_terminal", "approach": True,
                                  "lines": ["{rival_name}: {player_name}! You're going to Castelia City, right?",
                                            "{rival_name}: Team Plasma's travelling by ship. I'm going to find them. I can't forgive those guys!"]}]),
        "gate_n": room(453, {0: _say("Gate attendant", "Welcome! Through this gate is Pokestar Studios!"),
                             1: _say("Woman in the gate", "Pokestar Studios! It's where you get to live all kinds of different lives!")},
                       {}, (24, 0), exits_extra={566: ("^", "POKESTAR_STUDIOS")}),
    },
    edges={"v": ("VIRBANK_COMPLEX_OUTSIDE", [(2, 31), (17, 31), (18, 31), (19, 31)])},
    edge_to={"%d,31" % x: [x, 0] for x in (2, 17, 18, 19)},
    hidden={"4,24": "ANTIDOTE"},
    scenes=VIRBANK_SCENES,
)

# ---------------------------------------------------------------------------------------------- Roxie's Gym (455, 502)
# The lobby (Clyde), then up to the stage: a rock club. The band's too loud for Roxie to hear you till her two bandmates
# (Roughneck Nicky, Guitarist Billy Jo) are beaten. After her: a scout from Pokestar Studios; Roxie runs off after her father.
GYM_VIRBANK_STAGE = room(
    502, {0: [{"text": "Gym", "action": "GYM", "_look": "sheet:b2_c295.png", "condition": ["not:b2_toxic_badge"]},
              _say("Roxie ", "Roxie: Using the Pokemon I like, and reaching people with the music I like: that's who I am!",
                   "Roxie: Do what you enjoy, your own way. Just don't cause anyone trouble!",
                   condition=["b2_virbank_dock"], _look="sheet:b2_c295.png")],
          1: {"text": "Roughneck Nicky", "action": "EVENT", "event": {
              "lines": ["Roughneck Nicky: Can't hear ya over the music! Let's battle instead!"],
              "battle": {"name": "Roughneck Nicky", "class": "ROUGHNECK", "sprite": "b2_roughneck.png", "team": [88, 109], "levels": [14, 14],
                         "rewards": {"balls": 2}, "dialogue": {"player_won": ["Roughneck Nicky: The music stopped... that means I lost!"]}},
              "flag": "gym_trainer_VIRBANK_CITY_1", "done": ["Roughneck Nicky: Roxie can hear you now. Go on!"]}},
          2: {"text": "Guitarist Billy Jo", "action": "EVENT", "event": {
              "lines": ["Guitarist Billy Jo: This next song is a poisonous one! Here we go!"],
              "battle": {"name": "Guitarist Billy Jo", "class": "GUITARIST", "sprite": "b2_guitarist.png", "team": [543, 109], "levels": [14, 14],
                         "rewards": {"balls": 2}, "dialogue": {"player_won": ["Guitarist Billy Jo: My strings! You've cut the show short!"]}},
              "flag": "gym_trainer_VIRBANK_CITY_2", "done": ["Guitarist Billy Jo: The stage is all yours. Roxie's waiting!"]}},
          5: _say("Sound engineer", "I run the sound! I balance it so everyone can hear. You balance your team's types, right?")},
    {}, (0, 0), stairs={455: ("v", "ROOM:gym")},
    scenes=[{"trigger": {"zone": [3, 6, 4, 6]}, "condition": ["not:gym_trainer_VIRBANK_CITY_2"], "every": True,
             "cast": [], "call": ["The band is way too loud! Roxie can't hear a thing. Stop the music first: beat her bandmates!"]},
            {"trigger": {"zone": [0, 0, 17, 16]}, "condition": ["b2_toxic_badge", "not:b2_scout_met"], "flag": "b2_scout_met",
             "cast": [{"sheet": "b2_c358.png", "from": [8, 15], "to": "player", "stay": True,
                       "lines": ["???: Hey, you! I could tell you were something special during that battle with Roxie!",
                                 "Scout: I'm a scout for Pokestar Studios, north of town. Please, come with me to the studios!"]},
                      {"sheet": "b2_c224.png", "from": [8, 3], "to": "player",
                       "lines": ["Roxie: You're going to Pokestar Studios?! OH! I forgot! The old man!",
                                 "Roxie: I have to drag him back to work as captain!"], "leave": [8, 15]},
                      {"as": 0, "lines": ["Scout: I'll be waiting for you at the studios. Just go north through the gate!"],
                       "leave": [8, 15]}]}],
)
GYM_VIRBANK = room(
    455, {0: {"text": "Clyde", "action": "EVENT", "event": {
              "lines": ["This is a Pokemon Gym, and a rock club too! The Leader and her band are practising inside.",
                        "You'll need to stay hydrated. Here you go!"],
              "gift_item": {"FRESH_WATER": 1}, "flag": "b2_clyde_virbank",
              "done": ["Everyone here uses Poison-types! Grass and Bug moves don't work well on them.",
                       "And a poisoned Pokemon keeps losing HP. Bring Antidotes!"]}}},
    {5: ["VIRBANK CITY POKEMON GYM", "Leader: Roxie"], 6: ["I can sing! Wanted: the rest of a band!"]},
    (36, 27), stairs={502: ("^", "ROOM:gym_stage")},
    scenes=[{"who": "Clyde", "trigger": {"zone": [8, 3, 10, 3]}, "condition": ["not:b2_clyde_virbank"], "approach": True, "then": "talk"}],
)
VIRBANK["rooms"]["gym"] = GYM_VIRBANK
VIRBANK["rooms"]["gym_stage"] = GYM_VIRBANK_STAGE

# -------------------------------------------------------------------------------------------------- Virbank Complex
# 456 the outside (south of the city, by its edge): the Roughneck's daily ball swap, a Silk Scarf, an X Accuracy, a hidden
# Pearl. 457 the Complex (its gate at the top): three trainers, the foreman's three new Workers (TM94 Rock Smash), the
# Scientist who talks to himself (an Ether, the third time), a small tree for Cut, the Habitat List girl.
COMPLEX_OUTSIDE = route(
    456, {2: {"text": "Roughneck by the crane", "action": "EVENT", "event": {
              "lines": ["Yo! Good deal here. Your Poke Ball for my Great Ball?"],
              "ball_swap": "GREAT_BALL", "daily": True, "flag": "b2_complex_swap",
              "fail": ["You don't even have a Poke Ball?! Come back with one!"],
              "done": ["See? Good deal, right? We can trade again tomorrow!"]}},
          0: _ball("Poke Ball behind the Roughneck", "SILK_SCARF", "b2_complex_silk_scarf", name="a Silk Scarf"),
          1: _ball("Poke Ball in the grass", "X_ACCURACY", "b2_complex_x_accuracy", name="an X Accuracy")},
    {1: ["VIRBANK COMPLEX", "Where fire meets steel."]},
    exits={"^": ("VIRBANK_CITY", [(2, 0), (17, 0), (18, 0), (19, 0)]),
           "v": ("VIRBANK_COMPLEX", [(x, 21) for x in range(16, 21)])},
    edge_to={"%d,0" % x: [x, 31] for x in (2, 17, 18, 19)},
    hidden={"30,1": "PEARL"},
    split=True,   # (the west lane to the Silk Scarf: in from Virbank's own west lane, by its edge)
)
WORKERS = {   # (the foreman's three new Workers: B2W2's teams, Normal mode)
    6: ("Worker Nathan", [447, 506], "Every day's the same... I get bored, so sure, let's battle!",
        "It's fine if every day's the same here. It means there's no trouble!"),
    5: ("Worker Mitchell", [504, 239], "I came here so my Pokemon could do great things. The foreman says battle? Okay!",
        "I forgot! If I don't work hard, my Pokemon never get to shine. Time to get to work!"),
    4: ("Worker Isaac", [240, 109], "I'm happy just being with my Pokemon... A battle? I'll play a bit.",
        "Huh! Battling sure fires you up!"),
}
COMPLEX_PEOPLE = {
    3: [{"text": "Foreman", "action": "EVENT", "condition": ["not:b2_foreman_ask"], "event": {
            "lines": ["Hey there, Trainer! Your Pokemon look full of energy! Can I ask a favour?",
                      "I've got three new Workers who need firing up. Battle them for me!",
                      "They're in different parts of the complex. Thanks!"], "flag": "b2_foreman_ask"}},
        {"text": "Foreman ", "action": "EVENT", "condition": ["b2_worker_6", "b2_worker_5", "b2_worker_4"], "event": {
            "lines": ["Hey! You did it, didn't you! Here's a token of my thanks!"],
            "gift_item": {"TM294": 1}, "flag": "b2_foreman_tm294",
            "done": ["The complex is lively now. Everyone's fired up and ready to go!"]}},
        _say("Foreman  ", "The three new Workers are in different parts of the complex. Go get 'em fired up!",
             condition=["b2_foreman_ask", {"any": ["not:b2_worker_4", "not:b2_worker_5", "not:b2_worker_6"]}])],
    7: {"text": "Scientist by the tower", "action": "EVENT", "condition": ["not:b2_sci_1"], "event": {
        "lines": ["Heating crude oil splits it into its parts... That's what this distillation tower is for!",
                  "...Oh! My knowledge overflowed, and somebody heard! Excuse me!"], "flag": "b2_sci_1"}},
    11: [{"text": "Girl in the south", "action": "EVENT", "condition": ["habitat:VIRBANK_COMPLEX"], "event": {
             "lines": ["Amazing! Your Habitat List for the complex is full! So many Pokemon live here!", "Here, take these as thanks!"],
             "gift_item": {"GREAT_BALL": 5}, "flag": "b2_complex_habitat",
             "done": ["Fill in the Habitat Lists and you'll finish the Pokedex before you know it!"]}},
         _say("Girl in the south ", "Oh! You have a Pokedex! The newest ones have a Habitat List, I hear.",
              "Show me when the complex's list is full!", condition=["not:habitat:VIRBANK_COMPLEX"])],
    8: _ball("Poke Ball past the small tree", "SUPER_POTION", "b2_complex_super_potion", name="a Super Potion"),
    9: _ball("Poke Ball by the south-east tanks", "TM018", "b2_complex_tm018", name="TM018 Thief"),
}
for _n, (_name, _team, _hi, _won) in WORKERS.items():
    COMPLEX_PEOPLE[_n] = [
        {"text": _name + " ", "action": "EVENT", "condition": ["b2_foreman_ask"], "event": {
            "lines": [_name + ": " + _hi], "flag": "b2_worker_%d" % _n, "done": [_name + ": " + _won],
            "battle": {"name": _name, "class": "WORKER", "sprite": "b2_worker.png", "team": _team, "levels": [12, 12],
                       "rewards": {"balls": 3}, "dialogue": {"player_won": [_name + ": " + _won]}}}},
        _say(_name, "Working at this complex was my dream... and now that it's come true, I don't know what's next.",
             condition=["not:b2_foreman_ask"])]
COMPLEX_SCIENTIST = [   # (the Scientist runs off as you listen: to the south-west smokestack, then the south clearing; an Ether)
    (10, 44, {"text": "Scientist by the smokestack", "action": "EVENT", "condition": ["b2_sci_1", "not:b2_sci_2"], "event": {
        "lines": ["The smokestacks rise right up into the sky. They burn off waste gas, you know.",
                  "...Oh! You overheard more of my vast knowledge! Excuse me!"], "flag": "b2_sci_2"}}),
    (14, 55, {"text": "Scientist in the clearing", "action": "EVENT", "condition": ["b2_sci_2"], "event": {
        "lines": ["The gas holders are round because a sphere stands up best to the pressure inside!",
                  "...You're actually interested? Then you're my complex buddy! Here, take this!"],
        "gift_item": {"ETHER": 1}, "flag": "b2_sci_ether",
        "done": ["The foreman even offered me a job. But I'm happy just looking at the complex!"]}}),
]
COMPLEX = route(
    457, COMPLEX_PEOPLE, {},
    exits={"^": ("VIRBANK_COMPLEX_OUTSIDE", [(x, 17) for x in range(16, 21)])},
    trainers={0: ("Youngster Masahiro", 3), 1: ("Lass Daya", 1), 2: ("Youngster Waylon", 1)},
    extra_people=COMPLEX_SCIENTIST,
    hidden={"23,47": "GREAT_BALL", "26,29": "TINY_MUSHROOM"},
)
COMPLEX["art"][24] = COMPLEX["art"][24][:4] + "2" + COMPLEX["art"][24][5:]   # (the small tree on the west path: Cut, the game's person 10)

# ------------------------------------------------------------------------------------------------- Pokestar Studios
# 566: the plaza (in from Virbank's north gate at the bottom), the soundstage (568, its effects room 567) and the theater
# (574). After Roxie's badge the scout and the boss, Stu Deeoh, meet you and show you round; Pop Roxie's film plays in the
# theater; then your own first film, with Brycen (the movie game: src/states/pokestar.py; more scripts after happy endings).
POKESTAR_DOORS = {574: ("house", "theater"), 568: ("house", "studio"), 453: ("gate", None, "VIRBANK_CITY")}
POKESTAR_PEOPLE = {
    3: _say("Lillipup on set", "Lillipup: Bwoo! Bowoof!"),
    4: _say("Director on set", "Hey, AD! This Lillipup's fur isn't what I pictured! Bring me another Lillipup, now!"),
    2: _say("Rookie AD", "I'm a rookie assistant director. I love movies, but I'm not good at making them yet...",
            "The director is so strict. He's always mad at me!"),
    5: _say("Director by the set", "Hey, AD! That set is in the way of my shot! Move it, right now!"),
    6: _say("Director looking up", "Hey, AD! Those clouds don't suit my film at all! Get them out of the sky, right now!"),
    7: _say("Director by the bridge", "You did it, AD! A perfect scene! Now we reshoot all the others from scratch!"),
    8: _say("Actor rehearsing", "I'm rehearsing. To make a good film, the work before the shoot matters most!"),
    9: _say("Portrait seller", "How about a portrait of one of Pokestar Studios' famous stars?",
            "Brycen's is the hot ticket right now!"),
    10: _say("Man by the portraits", "Man... that director's off again. There's a fine line between genius and madness..."),
    11: _say("Boy by the posters", "Pokestar Studios makes horror films too. Who even watches kids' stuff like that?!"),
    12: _say("Woman by the trailer", "There's a dressing room inside this trailer. Costumes, makeup, script checks!"),
    13: _say("Boy dreaming big", "Someday I'll be in pictures, become a famous actor, and buy a mansion! A HUGE one!"),
    14: _say("Child actress", "Todos me consideran una nina prodigio! Soy una autentica estrella!"),
    15: _say("Her manager", "I'm her manager. She says: everyone knows her as a brilliant child actress. And a top star!"),
    16: _say("Girl by the posters", "Just looking at the posters is exciting! Which movie should I watch today?"),
    17: _say("Woman waiting", "I've been waiting three hours... How long does makeup take, anyway?"),
    19: _say("Actress by the props", "Props and special sets are stored in here. Before computer effects, we built everything!"),
}
POKESTAR_SIGNS = {38: ["A detailed model of the Royal Unova. A set for a movie."],
                  37: ["A movie set: the Skyarrow Bridge at 1/144 scale."],
                  36: ["Movie props for shooting films."], 35: ["This fake building is so detailed, it looks real."],
                  34: ["POKESTAR STUDIOS SOUND STAGE", "No public access!"]}
POKESTAR_SCENES = [
    {"trigger": "enter", "condition": ["b2_scout_met", "not:b2_pokestar_tour"], "flag": "b2_pokestar_tour",
     "call": ["???: Hm... I see... That kid sounds promising...", "???: Indeed. And that kid should be here any moment!"],
     "cast": [{"sheet": "b2_c358.png", "from": [30, 50], "to": "player", "stay": True,
               "lines": ["Scout: Welcome... to Pokestar Studios! {player_name}, we've been waiting for you!",
                         "Scout: This is our boss, Mr. Stu Deeoh!"]},
              {"sheet": "b2_c345.png", "from": [32, 50], "to": "player",
               "lines": ["Stu Deeoh: Bonsoir! Hello! I'm Stu Deeoh! Charmed, I'm sure!",
                         "Stu Deeoh: Movies! They're amazing! They move people all over the world!",
                         "Stu Deeoh: I need a little time to prepare. In the meantime, let us show you around!"],
               "leave": [20, 21]},
              {"as": 0, "lines": ["Scout: That's my boss! What graceful footwork! Well then, come with me!",
                                  "Scout: Pokestar Studios was built for making films. It's a movie metropolis!"],
               "lead": [[45, 19, ["Scout: This is the theater! Films are shown here, and movie fans come from all over.",
                                  "Scout: Our captain from Virbank just shot his first film. Let's have a look inside!"]]],
               "leave": [45, 18]}],
     "room": ["theater", 15, 29]},
]
THEATER_SCENES = [
    {"trigger": "enter", "condition": ["b2_pokestar_tour", "not:b2_pop_roxie_movie"], "flag": "b2_pop_roxie_movie",
     "cast": [{"sheet": "b2_c358.png", "from": [14, 30], "to": "player", "stay": True,
               "lines": ["Scout: Here we are. Watching a film is the best way to learn how it all works!"]},
              {"sheet": "b2_c359.png", "from": [9, 10], "path": [[13, 12], [15, 12]], "face": "d", "stay": True,
               "lines": ["On the screen: 'RIOLU-MAN!' starring the captain from Virbank...",
                         "Riolu-Man: Have no fear! Riolu-Man is... um... what's my line?",
                         "The audience yawns. Someone's snoring in the back row..."]},
              {"as": 1, "lines": ["Pop Roxie: ...That's not how I pictured it. I'll head back to Virbank."], "leave": [14, 31]},
              {"as": 0, "lines": ["Scout: Hmm. Not every film's a hit. Now it's your turn, {player_name}!",
                                  "Scout: The soundstage is west across the plaza. Mr. Deeoh's waiting with a script!"],
               "leave": [14, 31]}]},
]
STUDIO_SCENES = [
    {"trigger": {"zone": [12, 18, 16, 20]}, "condition": ["b2_pop_roxie_movie", "not:b2_first_film"],
     "cast": [{"sheet": "b2_c345.png", "from": [14, 15], "to": "player", "stay": True,
               "lines": ["Stu Deeoh: Ah, there you are! Today's film: 'Brycen-Man Strikes Back'!",
                         "Stu Deeoh: Your co-star is the great Brycen himself, as the villain! Your partner: a rental Pokemon.",
                         "Stu Deeoh: Pick your lines as the scene goes. Choose the ones that feel just right! Places, everyone!"]}],
     "then": "event:b2_first_film"},
]
POKESTAR = town(
    566, POKESTAR_PEOPLE, POKESTAR_SIGNS, POKESTAR_DOORS, rooms={
        "studio": room(568, {0: {"text": "Assistant director", "action": "EVENT", "condition": ["b2_first_film"],
                                 "event": {"lines": ["Ready to shoot? Pick a script!"], "scene": "pokestar"}},
                             3: _say("Receptionist", "Welcome to the soundstage of Pokestar Studios!"),
                             4: _say("Dressing room guard", "Only special stars approved by the boss may use this dressing room. Scram!"),
                             5: _say("Girl with a Lillipup", "Movies here use rental Pokemon. Does that mean my Lillipup can't be in one?"),
                             6: _say("Boy with a Stunfisk", "Shoot a film with a rental Pokemon and get a happy ending,",
                                     "and then you can act with your own! Me and my Stunfisk are working on it!"),
                             7: _say("Stunfisk", "Stunfisk: ..."),
                             8: _say("Actress", "Hi! New here? If you're an actor, check the script! Work hard and be a star like Brycen!"),
                             9: _say("Effects specialist", "See the green screens? What's shot in front of them becomes amazing scenes!"),
                             10: _say("Studio guide", "Films here follow a script. Choose the line that makes you think: this is great!",
                                      "The lines you choose change how your co-stars act, and how the story ends."),
                             11: _say("Guard by the back", "The back of the soundstage is staff only.")},
                       {}, (19, 20), stairs={567: ("^", "ROOM:studio_vfx")}, scenes=STUDIO_SCENES),
        "studio_vfx": room(567, {0: _say("Suit actor", "This jumpsuit is cutting-edge effects tech. It's still embarrassing to wear!"),
                                 1: _say("Suit actor ", "VFX means visual effects: computers that change the pictures we shoot!"),
                                 4: _say("Screenwriter", "I write the scripts! My head's packed with nothing but stories."),
                                 7: _say("Prop maker", "I'm a big guy, but I make small props. Even furniture for the sets!"),
                                 8: _say("Cameraman", "Hello! I'm the cinematographer. Put simply, the cameraman."),
                                 3: _say("Sound engineer ", "Most lines are recorded again later, in the booth. That's my job!"),
                                 6: _say("Rookie AD ", "Where's that megaphone?! I'm in trouble again if I can't find it!"),
                                 9: _say("Woman by the screens", "Every film here needs a whole team behind the camera.")},
                           {}, (0, 0), stairs={568: ("v", "ROOM:studio")}),
        "theater": room(574, {0: _say("Theater attendant", "Movies are wonderful! Two thumbs up!"),
                              1: _say("Fan in the lobby", "Hey, {player_name}! I'm a huge fan of your work!", condition=["b2_first_film"]),
                              2: _say("Woman in the lobby", "That film just now couldn't have been made without you, {player_name}!",
                                      condition=["b2_first_film"]),
                              23: _say("Old woman", "Oh my stars, a star! Your last film gave me quite a turn, dear."),
                              24: _say("Girl by the screens", "Which film should I watch? There are eight showing at once!"),
                              14: _say("Policeman", "Your film slapped the cuffs on this Policeman's heart!", condition=["b2_first_film"])},
                        {10866: ["POKESTAR STUDIOS RECORDS", "The best films' records are posted here."]},
                        (44, 18), scenes=THEATER_SCENES),
    },
    scenes=POKESTAR_SCENES,
)




# ====================================================================================================== batch 3a (11-20)
# Castelia City, Black 2's way: the waterfront avenue (zone 28, walked on the game's rails: rails.py) is the town; every
# street, pier and building is a room through its own camera (Jordan 11-20: "each street its own camera"). Doors pair
# exactly by the game's own warp numbers (castelia_room). Part 1: the city, the ship's arrival, the Harlequin Hunt, Burgh
# away and Iris to Thumb Pier. Part 2 (to come): the Sewers with Hugh, Burgh's Gym, Colress.
# Story flags: b2_sailed_castelia (Virbank's ship) -> b2_castelia_arrived (the pier: Hugh's Xtransceiver) ->
# b2_burgh_away (Gym Street: Clyde and Iris) -> b2_iris_thumb (the avenue) -> b2_thumb_scene (Thumb Pier: Hugh runs in).

CASTELIA_ROOMS = {30: "plaza", 31: "gym_street", 32: "route4_street", 33: "mode_street", 34: "castelia_street",
                  35: "narrow_street", 36: "liberty_pier", 37: "unity_pier", 38: "prime_pier", 39: "cruise_dock",
                  40: "thumb_pier", 41: "center", 42: "passerby", 43: "studio", 44: "battle_co", 45: "battle_co_47",
                  46: "battle_co_55", 47: "gf_lobby", 48: "game_freak", 49: "r4_west", 50: "r4_west_47", 53: "cafe",
                  54: "cs_west", 55: "cs_west_11", 56: "gs_west", 57: "medal_office", 58: "r4_north", 59: "r4_north_47",
                  60: "r4_south", 61: "r4_south_47", 494: "fennel", 51: "gate_route4", 252: "bridge_gate",
                  29: "gym", 488: "gym_burgh"}
CASTELIA_AREAS = {495: "CASTELIA_SEWERS", 326: "UNOVA_ROUTE_4", 551: "UNOVA_ROUTE_4"}
_EXIT_CHARS = "v^<>ghijklqtyz"


def _thin(rows, chars):
    """A doorway box several tiles deep (the game's warp strips): only its tiles touching open ground stay a way out; the
    rest become wall (a way out is walked into from the ground beside it)."""
    h, w = len(rows), len(rows[0])
    keep = set()
    for y in range(h):
        for x in range(w):
            if rows[y][x] in chars and any(0 <= y + dy < h and 0 <= x + dx < w and rows[y + dy][x + dx] in ".N\"\""
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                keep.add((x, y))
    for y in range(h):
        for x in range(w):
            if rows[y][x] in chars and (x, y) not in keep:
                rows[y][x] = "c"


def _castelia_target(d):
    to = d["to"]
    if to == 28:
        return "ROOM:MAIN"
    if to in CASTELIA_ROOMS:
        return "ROOM:" + CASTELIA_ROOMS[to]
    return CASTELIA_AREAS.get(to)


def castelia_room(z, people, signs, extra_people=(), scenes=None, lift=None, title=None, **more):
    """A Castelia street, pier or building: each of its doors leads where the game's own warp does (the avenue, another
    room, the Sewers...). lift: [[label, room, x, y], ...]: the lift doors (the zone's two lift signs at the top wall)."""
    g = GEO[str(z)]
    sg_lines = dict(signs)
    lift_tiles = [s for s in g["signs"] if 10405 <= s["script"] <= 10418] if lift else []
    for s in lift_tiles:
        sg_lines[(s["x"], s["y"])] = ["The lift."]
    rows, ppl, sg, doors = _place(z, people, sg_lines, extra_people, counters=not g["outdoor"])
    exits, chars = {}, {}
    for d in doors:
        tgt = _castelia_target(d)
        if not tgt:
            continue
        ch = chars.get(tgt) or _EXIT_CHARS[len(chars)]
        chars[tgt] = ch
        for k in range(max(1, d["w"])):
            for j in range(max(1, d.get("h", 1))):
                if 0 <= d["x"] + k < len(rows[0]) and 0 <= d["y"] + j < len(rows):
                    rows[d["y"] + j][d["x"] + k] = ch
        exits[ch] = tgt
    _thin(rows, set(exits))
    if not 28 <= z <= 40:   # (rooms only: not the streets and piers, marked indoor in the file, nor Burgh's Gym (29), its floors reached by the threads)
        _no_drops(z, rows, set(exits))
    m = {"theme": "room", "art": ["".join(r) for r in rows], "exits": exits, "buildings": {}, "roofs": _picture(z, g["outdoor"]),
         "people": ppl}
    if sg:
        m["signs"] = sg
    if scenes:
        m["scenes"] = scenes
    if lift and not exits:   # (a floor reached only by the lift: it's where you step out)
        m["landings"] = [[f[2], f[3]] for f in lift if f[1] == CASTELIA_ROOMS.get(z)]
    if lift:
        m["sign_events"] = {"%d,%d" % (s["x"], s["y"]): {"text": "Lift", "action": "EVENT", "event": {"lift": lift}} for s in lift_tiles}
    if title:
        m["title"] = title
    m.update(_camera(z))
    m.update(more)
    return m


def _gift(label, lines, item, flag, done, count=1, **kw):
    gift = {"balls": count} if item == "balls" else {item: count}
    out = {"text": label, "action": "EVENT", "event": {"lines": list(lines), "gift_item": gift, "flag": flag, "done": list(done)}}
    out.update(kw)
    return out


def _clerk_battle(label, name, cls, sprite, team, levels, hi, won, flag, gift=None):
    ev = {"lines": [hi], "flag": flag, "done": [won],
          "battle": {"name": name, "class": cls, "sprite": sprite, "team": team, "levels": levels, "rewards": dict({"balls": 2}, **(gift or {})),
                     "dialogue": {"player_won": [won]}}}
    return {"text": label, "action": "EVENT", "event": ev}


HUNT = ["b2_hunt_medal", "b2_hunt_passerby", "b2_hunt_battleco"]


def _hunted(label, place, flag):
    """One of the Castelia Harlequin Hunt's three hidden Harlequins (B2W2)."""
    return [{"text": label, "action": "EVENT", "condition": ["b2_hunt_start", "not:" + flag], "_look": "sheet:b2_c54.png", "event": {
                "lines": ["I'm from the Castelia Harlequin Hunt! You found the %s Harlequin! All riiight!" % place], "flag": flag}},
            _say(label + " ", "Enjoy Castelia City! Every corner has something to see.", _look="sheet:b2_c54.png",
                 condition=[{"any": ["not:b2_hunt_start", flag]}])]


BATTLE_CO_LIFT = [["1F", "battle_co", 6, 2], ["47F", "battle_co_47", 6, 1], ["55F", "battle_co_55", 6, 2]]
GF_LIFT = [["1F", "gf_lobby", 6, 2], ["22F", "game_freak", 6, 2]]
R4W_LIFT = [["1F", "r4_west", 6, 2], ["47F", "r4_west_47", 6, 2]]
CSW_LIFT = [["1F", "cs_west", 6, 2], ["11F", "cs_west_11", 6, 2]]
GSW_LIFT = [["1F", "gs_west", 6, 2], ["2F", "medal_office", 6, 2], ["3F", "fennel", 6, 2]]
R4N_LIFT = [["1F", "r4_north", 6, 2], ["47F", "r4_north_47", 6, 1]]
R4S_LIFT = [["1F", "r4_south", 6, 2], ["47F", "r4_south_47", 6, 1]]

CASTELIA_PEOPLE = {   # (the avenue: Oceanfront Road)
    12: _say("Iris", "Iris: Thumb Pier's just past here! Come on, come on!", condition=["b2_burgh_away", "not:b2_thumb_scene"],
             _look="sheet:b2_c355.png"),
    1: _say("Clerk by the railing", "When I fall asleep in my bed... when my Pokemon lands a critical hit... So many things make me happy!"),
    5: _say("Clerk on her break", "I'm a battling Clerk! If I don't give up, I'll win someday!"),
    6: _say("Tired clerk", "Everyone's faces blend together... Is that because I'm tired?"),
    7: _say("Clerk with a coffee", "When you're tired, rest! Don't force yourself to be cheerful."),
    9: _say("Clerk thinking", "Should I change my Pokemon's moves, or its held item?"),
    10: _say("Clerk looking out to sea", "Living among so many people... do you have to like everyone, or just yourself?"),
    3: _say("Man by the steps", "I wonder what Castelia was like before it got this big."),
    2: _say("Clerk on the corner", "The Pokemon and the people here are so full of life!"),
    8: _say("Battle Company clerk", "The Battle Company needs people for focus testing. Confident Trainers, come and try it!"),
    4: _say("Clerk by the bay", "Seasons and trends always pass..."),
    11: [{"text": "Harlequin", "action": "EVENT", "condition": ["not:b2_hunt_start"], "event": {
             "lines": ["Welcome to Castelia City! It's the Castelia Harlequin Hunt!",
                       "First time here? Here, have this! Get around the city in style!",
                       "{player_name} received a Bicycle!",
                       "The rules are simple: find the three Harlequins hiding in the city. The Medal Office, Passerby Analytics HQ, and the Battle Company!"],
             "gift_item": {"BICYCLE": 1}, "flag": "b2_hunt_start"}},
         {"text": "Harlequin ", "action": "EVENT", "condition": HUNT, "event": {
             "lines": ["You found all three! You've completed the Castelia Harlequin Hunt! Here's your prize!"],
             "gift_item": {"RARE_CANDY": 1}, "flag": "b2_hunt_done",
             "done": ["The Hunt's a way to make more people love Castelia City! Come back any time!"]}},
         _say("Harlequin  ", "Still hunting? The Medal Office, Passerby Analytics HQ and the Battle Company!",
              condition=["b2_hunt_start", {"any": ["not:" + f for f in HUNT]}])],
}
CASTELIA_SIGNS = {(70, 37): ["CASTELIA CITY", "A city of grandeur."], 3: ["AHEAD: CASTELIA STREET", "Ocean side: Cruise Dock"],
                  4: ["AHEAD: MODE STREET", "Ocean side: Prime Pier"], 5: ["AHEAD: NARROW STREET", "Ocean side: Unity Pier"],
                  6: ["AHEAD: POKEMON GYM", "Ocean side: Liberty Pier"], 7: ["PASSERBY ANALYTICS HQ", "...people pass by as they walk along."],
                  8: ["BATTLE COMPANY", "Talented Trainers welcome!"]}
CASTELIA_SCENES = [
    # Iris waits by the way to Thumb Pier (the game's trigger: 77, 39-44)
    {"trigger": {"zone": [76, 38, 79, 45]}, "condition": ["b2_burgh_away", "not:b2_iris_thumb"], "flag": "b2_iris_thumb",
     "cast": [{"person": "Iris", "face": "d", "lines": ["Iris: Hey, c'mon! Thumb Pier's past here!",
                                                     "Iris: Suspicious places in Castelia? There's really only one that comes to mind!",
                                                     "Iris: This way! This way! Come and look!"], "leave_path": [[76, 31]], "gone": True}]},
]

# --- the avenue's ways into its streets and piers: the game's own warp boxes (the doors to 41, 42, 44 are buildings)
_ave_edges, _ave_to = {}, {}
for _d in GEO["28"]["doors"]:
    _t = _castelia_target(_d)
    if not _t or _d["to"] in (41, 42, 44):
        continue
    _ch = _ave_to.get(_t) or "ghijklqtyz<>"[len(_ave_to)]
    _ave_to[_t] = _ch
    _box = [(_d["x"] + k, _d["y"] + j) for k in range(_d["w"]) for j in range(_d["h"])]
    _open_at = lambda x, y: 0 <= y < len(GEO["28"]["rows"]) and 0 <= x < len(GEO["28"]["rows"][y]) and GEO["28"]["rows"][y][x] == "."
    _touch = lambda b: any(_open_at(x + dx, y + dy) for x, y in b for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    if not _touch(_box):   # (the rails' road stops short of a warp box: Narrow Street's, x 30-32 with the road ending at 28:
        for _n in range(1, 4):   #  slid onto the road's edge, or it is thinned away and the street can't be entered; 11-21)
            _moved = next((m_ for m_ in ([(x - _n, y) for x, y in _box], [(x + _n, y) for x, y in _box], [(x, y - _n) for x, y in _box],
                                         [(x, y + _n) for x, y in _box]) if _touch(m_)), None)
            if _moved:
                _box = _moved
                break
    _ave_edges.setdefault(_ch, (_t, []))[1].extend(_box)

PRIME_PIER_SCENES = [
    {"trigger": "enter", "condition": ["b2_sailed_castelia", "not:b2_castelia_arrived"], "flag": "b2_castelia_arrived",
     "cast": [{"person": "Pop Roxie", "face": "r", "lines": ["Pop Roxie: Everyone, we've arrived at Castelia City!"]},
              {"sheet": "b2_hugh.png", "from": [12, 9], "to": "player",
               "lines": ["{rival_name}: So this is Castelia City... It's way bigger than I'd heard!",
                         "{rival_name}: Doesn't matter. I'll find Team Plasma wherever they run!",
                         "{rival_name}: Oh yeah, {player_name}! Let's register each other's Xtransceiver numbers.",
                         "{rival_name}: Back in Aspertia we never needed to. We could just see each other!",
                         "{player_name} registered {rival_name} in the Xtransceiver!"],
               "leave": [13, 1]}]},
]
GYM_STREET_SCENES = [
    # Burgh's away: Clyde at the Gym, then Iris (the game's script 2 at the Gym door)
    {"trigger": {"zone": [19, 44, 25, 52]}, "condition": ["b2_castelia_arrived", "not:b2_burgh_away"], "flag": "b2_burgh_away",
     "cast": [{"person": "Clyde", "face": "l",
               "lines": ["Clyde: If you're looking for Gym Leader Burgh, he said there might be trouble, and off he went!",
                         "Clyde: Feel free to go and look for him!"], "stay": True},
              {"sheet": "b2_c355.png", "from": [16, 62], "to": "player", "stay": True,
               "lines": ["???: Huh? Burgh vanished again?"]},
              {"person": "Clyde", "face": "l", "lines": ["Clyde: Oh! Hello, Iris. Something came up, and Burgh isn't here right now."]},
              {"as": 1, "lines": ["Iris: Hmm... Isn't Burgh always vanishing? He says he's got artist's block and wanders off.",
                                  "Iris: Hi! Who are you? ...Looking for Team Plasma? But they broke up two years ago!",
                                  "Iris: Doesn't matter! You've got a problem, so I'll help!",
                                  "Iris: Hmm... where would suspicious people go to hide?",
                                  "Iris: ...That's it! That might be where they are!"], "leave": [16, 62]},
              {"person": "Clyde", "face": "l",
               "lines": ["Clyde: Good grief... Burgh and Iris are so alike.",
                         "Clyde: Looks like she went round the corner, toward the Pokemon Center. Follow the street down to the sea, then east!"]}]},
    # the Gym's shut till Burgh's back (after the Sewers)
    {"trigger": {"zone": [24, 48, 24, 48]}, "condition": ["not:b2_sewers_done"], "every": True,
     "cast": [], "call": ["Clyde: Sorry! Burgh isn't here right now."], "push": [-1, 0]},
]
THUMB_PIER_SCENES = [
    # Iris shows you the way into the Sewers; Hugh runs in (the game's triggers: 4, 9-18 and 9-11, 19)
    {"trigger": {"zone": [2, 8, 8, 19]}, "condition": ["b2_iris_thumb", "not:b2_thumb_scene"], "flag": "b2_thumb_scene",
     "cast": [{"person": "Iris ", "face": "l",
               "lines": ["Iris: You can get into the sewers from here! Seems pretty suspicious, right?"], "stay": True},
              {"sheet": "b2_hugh.png", "from": [1, 14], "to": "player",
               "lines": ["{rival_name}: {player_name}! Did you find Team Plasma?!",
                         "{rival_name}: ...Not yet? Then the only place I haven't checked is...",
                         "{rival_name}: {player_name}! Help me out!"], "leave": [19, 17]},
              {"as": 0, "lines": ["Iris: Yep! The sewers are a perfect hiding place. Go on, after him!"]}]},
]

CASTELIA = town(
    28, CASTELIA_PEOPLE, CASTELIA_SIGNS,
    {41: ("center", "center"), 44: ("house", "battle_co"), 42: ("house", "passerby")}, rooms={
        "prime_pier": castelia_room(38, {
            0: [_say("Pop Roxie", "Pop Roxie: Ahoy! Back to Virbank City? Step this way!", condition=["not:b2_castelia_arrived"]),
                {"text": "Pop Roxie ", "action": "EVENT", "condition": ["b2_castelia_arrived"], "event": {
                    "lines": ["Pop Roxie: Ahoy! Shall we sail for Virbank City? Please, step this way!"],
                    "travel": "VIRBANK_CITY", "land": ["terminal", 6, 7]}}],
            2: _ball("Poke Ball at the pier's end", "HEART_SCALE", "b2_castelia_heart_scale", name="a Heart Scale"),
            3: _say("Woman by the water", "That's a strange ship out there. A sailing ship, these days?"),
            4: _say("Man by the rail", "When you just can't take it any more, scream at the ocean!")},
            {}, scenes=PRIME_PIER_SCENES, title="Prime Pier"),
        "thumb_pier": castelia_room(40, {
            1: _say("Iris ", "Iris: The sewers are right there! Go on!", condition=["b2_iris_thumb", "not:b2_sewers_done"],
                    _look="sheet:b2_c355.png"),
            0: _say("Sewer worker", "Because of the tide, the Castelia Sewers can't always be entered the same way. It depends on the season."),
            3: _say("Man on the pier", "Thumbs up! Stick out your thumb and curl your fingers. It means OK... or well done!")},
            {}, scenes=THUMB_PIER_SCENES, title="Thumb Pier"),
        "unity_pier": castelia_room(37, {
            1: _say("Ship attendant", "This is the ship for Unity Tower, where Trainers from around the world gather.",
                    "It only sails for Trainers who've traded with someone far away. Not today, sorry!"),
            0: _gift("Girl on the pier", ["We're all tied together by destiny. But we each choose our own red thread.", "That's why I want you to have this!"],
                     "DESTINY_KNOT", "b2_castelia_destiny_knot", ["If a Pokemon holding it falls in love, the other one does too!"])},
            {}, title="Unity Pier"),
        "liberty_pier": castelia_room(36, {
            0: _say("Boy on the pier", "Liberty Garden, huh? Long ago a rich man hid an amazing Pokemon there: Victini!"),
            2: _say("Old man on the pier", "Ho ho! Team Plasma fell apart because they wanted to misuse power like Victini's."),
            1: {"text": "Liberty Garden sailor", "action": "EVENT", "event": {
                "lines": ["Would you like to sail to Liberty Garden? Your timing's perfect. All aboard!"], "travel": "LIBERTY_GARDEN", "land_floor": [0, 7, 12]}}},
            {}, title="Liberty Pier"),
        "cruise_dock": castelia_room(39, {
            0: {"text": "Royal Unova attendant", "action": "EVENT", "event": {"lines": ["..."], "cruise": "board"}}},   # (src/world/royal_unova.py)
            {}, title="Cruise Dock"),
        "plaza": castelia_room(30, {1: _say("Old man by the fountain", "If you want to be strong, battle lots of Trainers, and get to know your Pokemon well!"),
                                    0: _say("Colress", "Colress: I'll be waiting on Route 4. It's just beyond here!",
                                            condition=["b2_colress_plaza", "not:b2_colress_route4"])},
                               {1: ["CENTRAL PLAZA", "Ahead: Route 4"]}, title="Central Plaza", scenes=[
            # (after Burgh's badge: the man in the white coat looks at your team, and names himself; Route 4 next, batch 3b)
            {"trigger": "enter", "condition": ["b2_insect_badge", "not:b2_colress_plaza"], "flag": "b2_colress_plaza",
             "cast": [{"sheet": "b2_c250.png", "from": [15, 4], "to": "player", "stay": True,
                       "lines": ["???: Oh, it's you again! If it's no trouble, may I take a look at your Pokemon?",
                                 "???: ...Oh! How interesting! Your Pokemon shows more confidence than others of its kind.",
                                 "???: And you're a Trainer with only three Badges... Somehow, you bring out your Pokemon's power!",
                                 "Colress: Oh, excuse me! I'm a scientist. My name is Colress.",
                                 "Colress: My research: bringing out the power of Pokemon. Is it the bond with their Trainer? Or some other way?",
                                 "Colress: I'd like to test my theory by battling you. I'll be waiting on Route 4. It's just beyond here!"],
                       "leave": [15, 1]}]}]),
        "gym_street": castelia_room(31, {
            1: _say("Clerk on Gym Street", "Wanting to get stronger as a Trainer is good! Play with your Pokemon, or work with them!"),
            2: _say("Woman with a Palpitoad", "My little Palpitoad is utterly charming! When I come home tired, it cheers me right up."),
            3: _say("Trainer by the Gym", "When it comes to loving my Pokemon, I won't lose to anybody!"),
            4: _say("Girl with Potions", "I've got plenty of Potions! With them, I bet I can beat the Gym Leader!"),
            5: _say("Clerk going home", "If I only had five Badges, I could buy Ultra Balls...")},
            {1: ["CASTELIA CITY POKEMON GYM", "Leader: Burgh", "Premier Insect Artist"]}, scenes=GYM_STREET_SCENES, title="Gym Street",
            extra_people=[(22, 47, _say("Clyde", "Clyde: Burgh isn't here right now, I'm afraid.", condition=["not:b2_sewers_done"],
                                        _look="sheet:b2_c187.png"))]),   # (beside the Gym's door, not in it: the scene below turns you back)
        "route4_street": castelia_room(32, {
            0: _say("Woman by the gate", "Nimbasa City has the Pokemon Musical. It never goes well for me, but I'll keep trying!"),
            1: [_say("Man on the street", "Trainers and Pokemon make an amazing team! They dug out the ruins on Route 4!",
                     condition=["not:unova_version:WHITE_2"]),
                _say("Man on the street ", "Trainers and Pokemon make an amazing team! They built that row of new buildings on Route 4!",
                     condition=["unova_version:WHITE_2"])]},
            {1: ["ROUTE 4 AHEAD"]}, title="Street to Route 4"),
        "mode_street": castelia_room(33, {
            0: {"text": "Casteliacone seller", "action": "EVENT", "condition": ["not:season:WINTER"], "event": {
                "lines": ["Castelia's famous Casteliacone! The perfect souvenir! Just $100."],
                "pay": 100, "gift_item": {"CASTELIACONE": 1}, "daily": True, "flag": "b2_casteliacone",
                "done": ["You bought today's last one! Please come again tomorrow!"]}},
            3: _say("Boy in the line", "Boy oh boy! If the Champion buys them, they've got to be cool!", condition=["not:season:WINTER"]),
            4: _say("Girl in the line", "I can't wait to eat one!", condition=["not:season:WINTER"]),
            5: _say("Hiker in the line", "My daughter asked me to get them for her... but look at this line!", condition=["not:season:WINTER"]),
            6: _say("Clerk in the line", "The line gets really long. But it's worth the wait!", condition=["not:season:WINTER"])},
            {2: ["CASTELIA'S FAMOUS CASTELIACONE"], 1: ["STUDIO CASTELIA"]}, title="Mode Street",
            extra_people=[(13, 36, _say("Woman in the line", "I came all the way from Anville Town on the train just to get one!",
                                        condition=["not:season:WINTER"]))]),
        "castelia_street": castelia_room(34, {}, {1: ["GAME FREAK"]}, title="Castelia Street"),
        "narrow_street": castelia_room(35, {
            0: {"text": "Man by the dumpsters", "action": "EVENT", "event": {
                "lines": ["Where did I put those sunglasses...? Ah, found them!",
                          "And you really ought to have more light to see by. Take this. It'll help in dark places."],
                "gift_item": {"TM291": 1}, "flag": "b2_castelia_tm291",
                "done": ["Flash lowers your opponent's accuracy. Use it twice and they'll hardly ever hit!"]}},
            1: _say("Dancer", "Grin! Ehehehe..."), 2: _say("Dancer ", "Hey, yo! Yeah!")},
            {1: ["CAFE SONATA"]}, title="Narrow Street"),
        "center": castelia_room(41, {
            3: {"text": "Pokémon Center", "action": "HEAL"}, 0: {"text": "Shop", "action": "SHOP"},
            2: _say("Clerk ", "Welcome! Everyday items on this side."), 1: _say("Clerk  ", "Specialty Poke Balls are over here!"),
            7: {"text": "Mr. Medal", "action": "EVENT", "event": {"medal_rally": True}},
            4: _say("Boy with questions", "I want to know everyone's favourite kind of Pokemon!"),
            5: _say("Woman by the door", "Fennel's moved to Castelia City! She's a professor researching Pokemon Trainers."),
            8: _say("Nurse by the PC", "Want to heal your Pokemon? The counter's right there!"),
            9: _say("Audino", "Audino: Au-di-no?"),
            10: _say("Man by the stairs", "Upstairs there's a big globe. People mark where they're from on it."),
            11: _say("Clerk by the window", "Castelia's so busy, I come in here just for the quiet.")},
            {}, title="Pokemon Center"),
        "battle_co": castelia_room(44, {
            0: _say("Receptionist", "People here have Pokemon battles, not arguments! Upstairs, be ready for a challenge."),
            1: _say("Clerk by the lift", "Welcome! For the lift, use the buttons on or beside its door."),
            3: _say("Janitor", "I'm the janitor. I keep everything spick and span!",
                    "Have your Pokemon share Exp. Points? You can switch Exp. Share on in the Options. Handy, isn't it?"),
            2: [_gift("Ace Trainer by the window", ["A Pokedex! Coooool! Your first partner was Snivy? Then this is for you!"], "MIRACLE_SEED", "b2_bc_starter_item",
                      ["Lots of items work when a Pokemon holds them. Keep an eye out!"], condition=["party_has:495"]),
                _gift("Ace Trainer by the window ", ["A Pokedex! Coooool! Your first partner was Tepig? Then this is for you!"], "CHARCOAL", "b2_bc_starter_item",
                      ["Lots of items work when a Pokemon holds them. Keep an eye out!"], condition=["party_has:498", "not:party_has:495"]),
                _gift("Ace Trainer by the window  ", ["A Pokedex! Coooool! Your first partner was Oshawott? Then this is for you!"], "MYSTIC_WATER",
                      "b2_bc_starter_item", ["Lots of items work when a Pokemon holds them. Keep an eye out!"],
                      condition=["party_has:501", "not:party_has:495", "not:party_has:498"]),
                _say("Ace Trainer by the window   ", "Which Pokemon did you start with? Bring it along and show me!",
                     condition=["not:party_has:495", "not:party_has:498", "not:party_has:501"])],
            4: _hunted("Harlequin in the lobby", "Battle Company", "b2_hunt_battleco")},
            {1: ["Burgh's signature is scrawled in the corner of the painting."]}, lift=BATTLE_CO_LIFT, title="Battle Company"),
        "battle_co_47": castelia_room(45, {
            0: _gift("Developer", ["I'm in charge of development! Since you came for a company tour, have this!"], "SCOPE_LENS", "b2_bc_scope_lens",
                     ["A Pokemon holding a Scope Lens lands critical hits more often!"]),
            1: _clerk_battle("Clerk Clemens", "Clerk Clemens", "CLERK", "b2_worker.png", [58], [16], "A company tour? Anyway, let's battle!",
                             "What power! Take this present: Quick Balls work best at the very start of a battle.", "b2_bc_clemens", {"QUICK_BALL": 2}),
            3: _clerk_battle("Clerk Warren", "Clerk Warren", "CLERK", "b2_worker.png", [183], [16], "Here for Pokemon practice? Happy to help!",
                             "With skills like that, you'll get the most out of these Timer Balls!", "b2_bc_warren", {"TIMER_BALL": 5}),
            4: _clerk_battle("Clerk Gilligan", "Clerk Gilligan", "CLERK", "b2_worker.png", [519], [17], "Work hard, battle harder!",
                             "I lost... back to my desk.", "b2_bc_gilligan"),
            5: _clerk_battle("Clerk Britney", "Clerk Britney", "CLERK", "b2_worker.png", [406], [16], "A visitor! Let's see what you've got!",
                             "Wow, you're good!", "b2_bc_britney"),
            2: _ball("Poke Ball by the desks", "GUARD_SPEC", "b2_bc_guard_spec", name="a Guard Spec.")},
            {}, lift=BATTLE_CO_LIFT, title="Battle Company 47F"),
        "battle_co_55": castelia_room(46, {
            0: _ball("Poke Ball in the corner", "ETHER", "b2_bc_ether", name="an Ether"),
            1: _say("Boy by the window", "Think 'when I win it's my Pokemon, when I lose it's me'. That might make you stronger."),
            2: _clerk_battle("President", "Battle Company President", "GENTLEMAN", "gentleman.png", [133, 507], [17, 17],
                             "Oh! You're the Trainer I met at the entrance! I'll show you how much this company has researched Pokemon and Trainers!",
                             "I lost... You were strong. My dream as president? A device that lets people talk to Pokemon!", "b2_bc_president")},
            {}, lift=BATTLE_CO_LIFT, title="Battle Company 55F"),
        "passerby": castelia_room(42, {
            0: _say("Passerby Analytics leader", "Welcome to Passerby Analytics HQ! We survey the people you pass by.",
                    "Our surveys need lots of passers-by from far and wide, so there's no work for you just yet."),
            12: _hunted("Harlequin at the desks", "Passerby Analytics HQ", "b2_hunt_passerby"),
            10: _say("Statistician", "What do people like? What's popular? Surveys tell us!"),
            11: _say("Statistician ", "Hello! A cheerful greeting is important, isn't it?"),
            1: _say("Statistician  ", "Do you know the ranks of statisticians? Finish requests and you move up!"),
            2: _say("Statistician   ", "People pass by as they walk along... and we count them!")},
            {}, title="Passerby Analytics HQ"),
        "studio": castelia_room(43, {
            0: _say("Curator", "We're showing works by up-and-coming young artists!"),
            1: _say("Visitor", "In Castelia City, the Pokemon Gym itself is Burgh's artwork!"),
            2: {"text": "Painter", "action": "EVENT", "event": {
                "lines": ["I'm not the artist Burgh is, but I love painting. Show me a Pokemon to paint today!",
                          "Inspiring! Thank you! Take a Berry as thanks."],
                "gift_cycle": ["CHERI_BERRY", "CHESTO_BERRY", "PECHA_BERRY", "RAWST_BERRY", "ASPEAR_BERRY"], "daily": True, "flag": "b2_studio_berry",
                "done": ["As long as the artist enjoys making it, good or bad doesn't matter. Come back tomorrow!"]}}},
            {1: ["Title: 'White and Black Dragons'"], 2: ["Title: 'Sin and Money Stack Up'"], 3: ["Title: 'Ugly Truth'"],
             4: ["Title: 'Vanished Hero'"], 5: ["Title: 'Eternal Ideals'"], 6: ["Title: 'Two Beings - A Meeting That Must Occur'"],
             10: ["Title: 'The Recipient'"], 11: ["Title: 'The Moving Pokemon'"], 12: ["Title: 'A Gift'"]}, title="Studio Castelia"),
        "gf_lobby": castelia_room(47, {
            0: _say("Medal Rally boy", "You're in the Medal Rally too? Let's see who collects more!"),
            1: _say("Boy with a Roggenrola", "My Roggenrola's Ability is Sturdy! One hit at full HP can't knock it out!"),
            2: _say("Roggenrola", "Roggenrola: Sturrr!"),
            3: _say("Woman in the lobby", "Item maniacs are odd! They'll pay far more than normal for ordinary items!")},
            {}, lift=GF_LIFT, title="Castelia Street building"),
        "game_freak": castelia_room(48, {
            0: _ball("Poke Ball by the server", "REVIVE", "b2_gf_revive", name="a Revive"),
            1: _say("Game Director", "Hello! I'm the Game Director. You're filling your Pokedex! When it's full, come and show me!"),
            9: _say("Programmer", "A game is something you think up, program, and at the end, hope for! Work! Work!"),
            2: _say("Graphic Designer", "To draw something I've never seen, I have to look at lots of things. Lots!"),
            8: {"text": "Morimoto", "action": "EVENT", "event": {
                "lines": ["Morimoto: A tip for getting strong? Lots of battles! Well, let's begin!"], "daily": True, "flag": "b2_gf_morimoto",
                "done": ["Morimoto: You think about battles really carefully. Come back tomorrow!"],
                "battle": {"name": "GAME FREAK Morimoto", "class": "PKMN_TRAINER", "sprite": "gentleman.png", "team": [511, 513, 515],
                           "levels": [14, 14, 14], "rewards": {"balls": 3},
                           "dialogue": {"player_won": ["Morimoto: I lost, but I learned a lot from you. That was fun!"]}}}},
            5: {"text": "Nishino", "action": "EVENT", "event": {
                "lines": ["Nishino: I like to win with my favourite Pokemon!"], "daily": True, "flag": "b2_gf_nishino",
                "done": ["Nishino: Your Pokemon really trust you. Let's battle again tomorrow!"],
                "battle": {"name": "GAME FREAK Nishino", "class": "PKMN_TRAINER", "sprite": "lass.png", "team": [35], "levels": [16],
                           "rewards": {"balls": 3}, "dialogue": {"player_won": ["Nishino: Aww! What great Pokemon!"]}}}},
            7: _say("Planner", "I'm Snorlax. No, no, I'm the Planner! Leftovers are important, aren't they?"),
            4: _say("Sound Designer", "I just woke up. I wonder what kind of music people like."),
            6: _say("Staff", "It's cold in here because the server has to stay cool."),
            3: _say("Staff ", "I'm thinking up, er... a new plan for, er... a game.")},
            {}, lift=GF_LIFT, title="Game Freak 22F"),
        "cs_west": castelia_room(54, {
            1: _say("Laughing man", "My Pokemon and I love to laugh! When one of us starts, we both do! Gwa ha ha!"),
            2: _say("His Pokemon", "Gahoohoo!"), 0: _say("Receptionist ", "What do you like on TV? I like the lady and Watchy Watchog!"),
            3: _say("Boy", "Once my Poke Ball only shook once before it caught the Pokemon!"),
            4: _say("Girl", "That happens sometimes! I call it a critical capture. Catch lots of Pokemon and it happens more!")},
            {}, lift=CSW_LIFT, title="Castelia Street west building"),
        "cs_west_11": castelia_room(55, {
            1: _gift("Guitarist", ["Are you getting enough sleep? You won't feel better without rest! Here, take this!"], "TM085", "b2_castelia_tm085",
                     ["My Pokemon hold Chesto Berries. They rest, feel better, and wake right up!"]),
            0: _say("Curious man", "I'm a 'curiosee'! I'm curious about everything, and check every place I go!"),
            2: _say("Pokemon", "Whooon!")},
            {}, lift=CSW_LIFT, title="Castelia Street west building 11F"),
        "gs_west": castelia_room(56, {
            0: _say("Receptionist  ", "Floor two is the Medal Office. Floor three is Professor Fennel's lab."),
            1: _say("Feeling Reader", "I'm the Feeling Reader. People take Feeling Checks on their C-Gear together. I'll read yours one day!"),
            2: {"text": "Name Rater", "action": "EVENT", "event": {"lines": ["I'm the Name Rater! Shall I look at one of your Pokemon's names?"],
                                                                   "name_rater": True}},
            3: {"text": "Pokemon groomer", "action": "EVENT", "event": {
                "lines": ["Hello! If you'd like, I'll give your Pokemon a massage."],
                "salon": {"key": "b2_castelia_massage", "gain": 10, "said": "There, all done! The massage has made {mon} friendlier with you!",
                          "again": ["Sorry! I'm worn out from the last massage. Please come back tomorrow!"]}}},
            4: _say("Pokemon ", "Faafoon!"),
            5: _say("Woman by the desk", "You can't rename a Pokemon you got from someone else. Its name holds their wishes!")},
            {}, lift=GSW_LIFT, title="Gym Street west building"),
        "medal_office": castelia_room(57, {
            3: _hunted("Harlequin in the Medal Office", "Medal Office", "b2_hunt_medal"),
            1: _say("Medal fan", "Medals for everything you do! I want them all!"),
            0: _say("Medal fan ", "Mr. Medal remembers every Medal you've earned."),
            2: _say("Medal fan  ", "Collect lots of Medals and something good happens. I heard!")},
            {}, lift=GSW_LIFT, title="Medal Office",
            extra_people=[(9, 3, {"text": "Mr. Medal ", "action": "EVENT", "_look": "sheet:b2_c360.png", "event": {"medal_rally": True}})]),
        "fennel": castelia_room(494, {
            0: _say("Fennel", "Hi there, Trainer! I'm Fennel. I'm researching Pokemon Trainers, and the dreams of sleeping Pokemon!",
                    "My Game Sync research needs Trainers from all over the world, so it'll have to wait for now."),
            1: [{"text": "Amanita", "action": "EVENT", "event": {
                    "lines": ["I'm Amanita. I look after the PC Boxes! How are they working for you?",
                              "Oh! I have a bunch of Eevee. Would you take one for me? It came from a friend in Kanto!"],
                    "gift_pokemon": 133, "gift_level": 10, "flag": "b2_castelia_eevee",
                    "done": ["Eevee can evolve in so many ways! Catch lots of Pokemon and use the Boxes!"]}}],
            2: _say("Fennel's assistant", "I'm Fennel's assistant. Pokemon dreams... someday we'll be able to visit them!")},
            {}, lift=GSW_LIFT, title="Fennel's Lab"),
        "cafe": castelia_room(53, {
            1: _gift("Cafe manager", ["Your first visit to our cafe, isn't it? Please... give this to your dear Pokemon."], "MOOMOO_MILK",
                     "b2_cafe_moomoo", ["You came all this way. Enjoy..."]),
            0: _say("Guitarist in the cafe", "A beautiful melody makes people happy. A sad one makes them sorrowful. That's the power of melodies..."),
            2: _say("Regular", "I've been letting my tired mind relax in this cafe all day..."),
            3: _say("Clerk in the cafe", "Listen to him play... It reminds me of home."),
            4: _say("Woman in the cafe", "You can't change your family, but you can change how you get along.")},
            {}, title="Cafe Sonata"),
        "r4_west": castelia_room(49, {
            3: _gift("Old man", ["Travelling Trainer! Here's an amulet to keep you smiling!"], "AMULET_COIN", "b2_castelia_amulet",
                     ["A Pokemon holding it in battle earns you more prize money!"]),
            0: _say("Hiker by the window", "My friend worries about everyone's health on journeys, so he nicknames every Pokemon he trades 'Gesundheit'!"),
            2: _say("Gesundheit", "Gesundheit: ...Pan?"),
            1: _say("Receptionist   ", "Mr. Lock... He was a mysterious man...")},
            {}, lift=R4W_LIFT, title="Street to Route 4 west building"),
        "r4_west_47": castelia_room(50, {
            0: _say("Clerk 47F", "I want Pokemon in the new office... but I can't say so in front of my girlfriend."),
            1: _say("Woman by the window ", "My Pokemon... where did it go...?"),
            2: _say("Guard", "Even before Poke Balls, people and Pokemon were good friends. I hope that lasts."),
            3: _say("Clerk 47F ", "Missing Pokemon... even if it's Team Plasma, we don't know where they are.")},
            {}, lift=R4W_LIFT, title="Street to Route 4 west building 47F"),
        "r4_north": castelia_room(58, {
            0: {"text": "Pokemon fanatic", "action": "EVENT", "condition": ["seen_at_least:40"], "event": {
                "lines": ["I'm a Pokemon fanatic. Famous in Castelia, too! Oh, a Pokedex! You've seen 40 kinds or more? Wonderful! Take this!"],
                "gift_item": {"EVIOLITE": 1}, "flag": "b2_castelia_eviolite",
                "done": ["Eviolite raises Defense and Sp. Def, but only for a Pokemon that can still evolve!"]}},
            1: _say("Man by the door", "I've been thinking about starting a new business... but it's such a chore."),
            2: _say("Patrat", "Squeak!"), 3: _say("Girl by the Patrat", "My Patrat's Ability is Run Away! It can always escape wild Pokemon!"),
            4: _say("Clerk by the desk", "What kinds of Abilities do your Pokemon have?"),
            5: _say("Clerk by the desk ", "A service that teaches Pokemon moves? There are people who already do that?"),
            6: _say("Art lover", "Magnificent! Burgh's paintings are magnificent!")},
            {}, lift=R4N_LIFT, title="Street to Route 4 north building"),
        "r4_north_47": castelia_room(59, {
            0: _ball("Poke Ball by the window", "CHARCOAL", "b2_castelia_charcoal", name="a Charcoal"),
            1: _say("Man scared of heights", "When I look down on the city from up here, I tremble. I-I'm scared of heights..."),
            2: _say("Badge expert", "The Basic Badge makes Pokemon up to Lv. 20 obey. Each Badge raises it by ten!"),
            3: _say("Pokemon  ", "Hwoof hwoof!")},
            {}, lift=R4N_LIFT, title="Street to Route 4 north building 47F"),
        "r4_south": castelia_room(60, {
            0: _say("Lift guard", "Going up? I need to check you first. Frisk, frisk... Nothing suspicious. OK, you can go!"),
            2: _say("Man by the lift", "I'm invited to a party, but the guard by the lift wants to pat me down. Or is that my imagination?"),
            3: _say("Clerk by the lift", "Where are you from? Aspertia City? It's lovely! That Outlook is fantastic!"),
            1: _say("Girl by the lift", "I talked with lots of people upstairs. It was fun!")},
            {}, lift=R4S_LIFT, title="Street to Route 4 south building"),
        "r4_south_47": castelia_room(61, {
            4: _gift("Girl at the party", ["Ohh, your Pokemon are so charming! I want cute ones too... Here, use this!"], "TM240", "b2_castelia_tm240",
                     ["Attract makes Pokemon of the opposite gender fall in love!"]),
            0: _say("Party host", "Welcome! Welcome to my party! Enjoy talking with everyone!"),
            1: _say("Guest", "Ich habe mir ein Auto gekauft! I bought a car! Now the next town is close, even without Badges!"),
            2: _say("Guest ", "Hello. Have you tried a Casteliacone yet?"),
            3: _say("Dancer at the party", "Check out my moves! I learned these at the Musical Theater in the next city!"),
            5: _say("Woman at the party", "Did you see what Elesa, the supermodel, was wearing?"),
            6: _say("Woman at the party ", "Whatever Elesa wears is stunning!"),
            7: _say("Guest  ", "My boyfriend's so slow getting up, I asked his Pokemon to wake him!"),
            8: _say("Guest   ", "Ciao! Having a good time? Don't be shy. Talk to anyone!"),
            9: _say("Guest    ", "It's hard to get up the morning after a fun day like this."),
            10: _say("Guest     ", "My Pokemon sings instead of an alarm clock... and I never wake up!"),
            11: _say("Guest      ", "First time here! But this view makes me feel right at home!")},
            {}, lift=R4S_LIFT, title="Street to Route 4 south building 47F"),
        "gate_route4": castelia_room(51, {
            0: _say("Gate guard", "Nimbasa City is at the end of Route 4."),
            1: _say("Woman in the gate", "The Pokemon Breeder on Route 4 challenges every Trainer she sees. That's Route 4 for you!"),
            3: _say("Harlequin in the gate", "It's the Castelia Harlequin Hunt! Have you found them all?", _look="sheet:b2_c54.png")},
            {}, title="Castelia Gate",
            scenes=[{"trigger": "enter", "condition": ["b2_colress_plaza", "not:b2_got_dowsing"], "flag": "b2_bianca_gate",   # (3b: Bianca catches up)
                     "cast": [{"sheet": "b2_bianca.png", "from": [5, 14], "to": "player", "gone": True, "leave_path": [[5, 14]],
                               "lines": ["Bianca: Heeey! I saw you in the city and just had to catch up!",
                                         "Bianca: Here, take this! It's a Dowsing MCHN!",
                                         "Bianca: It finds places where items are hidden. Finding an item while you're looking for Pokemon is so exciting!",
                                         "Bianca: Ooh, good luck!"],
                               "then": "event:b2_dowsing"}]}]),
        "bridge_gate": castelia_room(252, {   # (Skyarrow Bridge, south: still being inspected; its batch opens it)
            0: _say("Gate receptionist", "Hello! Cross the Skyarrow Bridge from this side and you'll reach Pinwheel Forest and Nacrene City.",
                    "The Skyarrow Bridge has been here a very long time."),
            2: _say("Tired traveller", "I walked so far! My legs are sore! ...Um, you don't have to look."),
            1: _say("Worker by the bridge", "Please wait to cross. We're inspecting the Skyarrow Bridge to make sure it's strong enough.",
                    "It's the first inspection in a few years, so it may take a while. Thanks for your patience!"),
            3: _gift("Woman in the gate", ["Quick! Take this!"], "QUICK_CLAW", "b2_bridge_quick_claw",
                     ["Let a Pokemon hold that Quick Claw, and sometimes it gets to move first in battle!"]),
            4: _say("Harlequin in the gate ", "Free-for-all! It's the Castelia Harlequin Hunt! Explore the city and find us all!",
                    _look="sheet:b2_c54.png")},
            {}, title="Bridge Gate"),
    },
    edges=_ave_edges,
    scenes=CASTELIA_SCENES,
    split=True,   # (the rails' grid leaves pockets by the mouths: each way out checked from itself)
)
_art = [list(r) for r in CASTELIA["art"]]
_thin(_art, set(_ave_to.values()))
for _y, _r in enumerate(_art):   # (a building's door the rails stop short of: the tile in front of it opened onto the road)
    for _x, _c in enumerate(_r):
        if _c == "D" and not any(_art[_y + dy][_x + dx] in ".N" for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                                 if 0 <= _y + dy < len(_art) and 0 <= _x + dx < len(_r)):
            if _y + 1 < len(_art) and _art[_y + 1][_x] == "c":
                _art[_y + 1][_x] = "."
CASTELIA["art"] = ["".join(r) for r in _art]


# ------------------------------------------------------------------------------------------------- Burgh's Gym (29, 488)
# Black 2's own gimmick (kanto_handoff/unova_map_tools/castelia_gym.py -> castelia_gym.json: overlay 91 "gym_insect.c"):
# three floors over one footprint (ground, silk at 10, silk at 20 tiles up: the room's own floor model), cocoons joined by
# threads: walk into a cocoon facing the thread's way and it carries you to the other end (walk_town "cocoons"). Burgh's
# room (488) is reached by the lower-left top cocoon entered from its left; its two holes drop you back (left: the ground
# by the north-west pillar; bottom: the cocoon you came by). The ground's north-west pillar (8, 4) also goes up to Burgh:
# the game checks a flag first; here, once you hold the Insect Badge (our reading of it). Route (B2W2's walkthrough):
# centre cocoon -> the web -> right tower -> the top right -> lower-right cocoon (Jack pops out) -> down by the east pillar
# (Gary) -> the east pillar from its right -> the top middle -> left -> the lower left (Anders) -> from its left: Burgh.
GYM_DATA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "castelia_gym.json"), encoding="utf-8"))
GYM_ROOM = {0: "gym", 10: "gym_10", 20: "gym_20"}
_D = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}
_GYM_BOX = {(11, 3): (10, 1, 3, 4), (20, 5): (19, 3, 3, 4), (4, 14): (3, 13, 3, 3), (25, 15): (24, 13, 3, 4),   # (the game's boxes)
            (3, 3): (2, 2, 3, 3), (28, 3): (27, 2, 3, 3), (16, 11): (15, 10, 3, 2)}   # (the rings on the towers, and the web's)


def _gym_blocked(level):
    """The cocoon tiles on a floor (walked into, not onto)."""
    out = set()
    for t in GYM_DATA["threads"]:
        x, lv, z = t["from"]
        if t["zone"] == 29 and lv == level and (x, z) in _GYM_BOX and level:
            bx, by, bw, bh = _GYM_BOX[(x, z)]
            out |= {(bx + i, by + j) for i in range(bw) for j in range(bh)}
    return out


def _gym_stand(t):
    """Where you stand to walk into a thread's start: back from it along the way in, off the cocoon."""
    x, lv, z = t["from"]
    dx, dy = _D[t["face"]]
    rows, blocked = GYM_DATA["floors"][str(lv)], _gym_blocked(lv)
    for k in (1, 2, 3, 4):
        s = (x - dx * k, z - dy * k)
        if rows[s[1]][s[0]] == "." and s not in blocked:
            return s
    return None


def _gym_landing(q):
    """Where a thread sets you down at q = (x, level, z): where you'd stand to ride it back, else the nearest open tile."""
    for t in GYM_DATA["threads"]:
        if t["zone"] == 29 and t["from"] == list(q) and t["face"] in _D:
            s = _gym_stand(t)
            if s:
                return s, t["face"]
    rows, blocked = GYM_DATA["floors"][str(q[1])], _gym_blocked(q[1])
    best = min(((x, y) for y in range(len(rows)) for x in range(len(rows[0])) if rows[y][x] == "." and (x, y) not in blocked),
               key=lambda p: abs(p[0] - q[0]) + abs(p[1] - q[2]))
    return best, "d"


def _gym_cocoons(level):
    """{"x,y,face": [room, x, y, face, condition]} for one floor: the tiles you walk into (the cocoon's and the one before it)."""
    out = {}
    for t in GYM_DATA["threads"]:
        x, lv, z = t["from"]
        if t["zone"] != 29 or lv != level or t["face"] not in _D:
            continue
        dx, dy = _D[t["face"]]
        if t["leaves"]:   # (into Burgh's room: the lower-left top cocoon from its left, the ground's north-west pillar)
            land, face, cond = ((15, 19), "u", None) if (x, z) == (4, 14) else ((9, 14), "d", ["b2_insect_badge"])
            ride = ["gym_burgh", land[0], land[1], face] + ([cond] if cond else [])
        else:
            (lx, ly), face = _gym_landing(tuple(t["to"]))
            ride = [GYM_ROOM[t["to"][1]], lx, ly, face]
        stand = _gym_stand(t)
        for k in range(1, 4):
            tile = (stand[0] + dx * k, stand[1] + dy * k)
            out["%d,%d,%s" % (tile[0], tile[1], t["face"])] = ride
            if tile == (x, z):
                break
    return out


def _gym_floor(level, people, signs=None, scenes=None, extra_people=(), title=None):
    m = castelia_room(29, people, signs or {}, extra_people=extra_people, scenes=scenes, title=title or "Castelia Gym")
    rows, blocked = GYM_DATA["floors"][str(level)], _gym_blocked(level)
    art = [list(r) for r in m["art"]]
    for y, r in enumerate(art):
        for x, c in enumerate(r):
            if c in "N!X" or c in m["exits"]:
                continue
            art[y][x] = "." if rows[y][x] == "." and (x, y) not in blocked else "c"
    m["art"] = ["".join(r) for r in art]
    if level:   # (no door up here: you arrive by the threads)
        m["art"] = ["".join("c" if c in m["exits"] else c for c in r) for r in m["art"]]
        m["exits"] = {}
    m["cocoons"] = _gym_cocoons(level)
    cam = m["roofs"].get("_cam")
    if cam:   # (you're drawn standing on this floor's silk)
        k = float(GYM_GEO_K) * level
        m["roofs"]["_cam"] = dict(cam, lift=[[k] * len(r) for r in cam["lift"]])
    return m


GYM_GEO_K = GEO["29"]["cam"]["lift_k"]


def _harlequin(label, name, team, levels, hi, won, n, **kw):
    out = {"text": label, "action": "EVENT", "event": {
        "lines": [name + ": " + hi], "flag": "gym_trainer_CASTELIA_CITY_%d" % n, "done": [name + ": " + won],
        "battle": {"name": name, "class": "HARLEQUIN", "sprite": "b2_harlequin.png", "team": team, "levels": levels,
                   "rewards": {"balls": 2}, "dialogue": {"player_won": [name + ": " + won]}}}}
    out.update(kw)
    return out


GYM_CASTELIA = _gym_floor(0, {
    4: {"text": "Clyde", "action": "EVENT", "event": {
        "lines": ["Clyde: Hello! You must be tired, wandering Castelia's crowded streets after Team Plasma and the Gym Leader.",
                  "Clyde: So here, take this!"],
        "gift_item": {"FRESH_WATER": 1}, "flag": "b2_clyde_castelia",
        "done": ["Clyde: This Gym's theme is cocoons! Go inside one and ride its thread up.",
                 "Clyde: The threads all lead to Burgh... eventually!"]}},
    1: _harlequin("Harlequin Gary", "Harlequin Gary", [540, 415, 557], [19, 19, 19],
                  "Which side did you come in by? The cocoons care, you know!", "Ooh, you found the right thread!", 3)},
    {(14, 17): ["CASTELIA POKEMON GYM", "Leader: Burgh"], (18, 17): ["CASTELIA POKEMON GYM", "Leader: Burgh"]})
GYM_CASTELIA_10 = _gym_floor(10, {
    2: _harlequin("Harlequin Clarence", "Harlequin Clarence", [540, 540], [20, 20],
                  "Welcome to the cocoons! Hope you don't get tangled up!", "All wrapped up... in defeat!", 1)})
GYM_CASTELIA_20 = _gym_floor(20, {
    3: _harlequin("Harlequin Anders", "Harlequin Anders", [557, 541], [20, 20],
                  "Hiding makes your battle instincts dull, you know!", "Hiding makes battle instincts dull... I'll remember that.", 4)},
    scenes=[   # (Jack hides in the lower-right cocoon and pops out as you come by: the game's trigger 24, 17)
        {"trigger": {"zone": [23, 17, 26, 17]}, "condition": ["not:gym_trainer_CASTELIA_CITY_2"], "flag": "gym_jack_popped",
         "cast": [{"sheet": "b2_c54.png", "from": [25, 16], "to": "player", "stay": True,
                   "lines": ["Harlequin Jack: When the cocoon breaks open, the one that pops out is... me!",
                             "Harlequin Jack: And on that note, battle me!"],
                   "event": {"flag": "gym_trainer_CASTELIA_CITY_2", "battle": {
                       "name": "Harlequin Jack", "class": "HARLEQUIN", "sprite": "b2_harlequin.png", "team": [415, 541], "levels": [20, 20],
                       "rewards": {"balls": 2}, "dialogue": {"player_won": ["Harlequin Jack: Back into my cocoon I go..."]}}}}]}])
GYM_BURGH = castelia_room(488, {
    0: [{"text": "Gym", "action": "GYM", "_look": "sheet:b2_c225.png", "condition": ["not:b2_insect_badge"]},
        _say("Burgh", "Burgh: How many discoveries have you made since you set out?",
             "Burgh: I fell for Bug Pokemon as a kid. I drew them, battled with them... and I still find new things.",
             "Burgh: A world shared with Pokemon is a world swarming with mysteries.", condition=["b2_insect_badge"])]},
    {}, title="Burgh's Studio")
GYM_BURGH["cocoons"] = {"%d,%d,%s" % (x, y, f): ride for (x, y), ride in (((9, 13), ["gym", 8, 6, "d"]), ((15, 20), ["gym_20", 4, 16, "d"]))
                        for f in "udlr"}   # (its holes: any way in, you drop)
GYM_BURGH["scenes"] = [{"trigger": "enter", "condition": ["not:b2_burgh_hello"], "flag": "b2_burgh_hello",
                        "cast": [{"person": "Gym", "face": "d",
                                  "lines": ["Burgh: Good work back there in the sewers! My Bug Pokemon are scurrying with excitement.",
                                            "Burgh: Dwebble's round little eyes are cute! And my ace, Leavanny, sews leaf clothes for other Pokemon.",
                                            "Burgh: Well now... let's get right to it!"]}]}]

_lands = {}   # (where the threads set you down: each floor's landings, for the reach check)
for _r in (GYM_CASTELIA, GYM_CASTELIA_10, GYM_CASTELIA_20, GYM_BURGH):
    for _ride in _r["cocoons"].values():
        _lands.setdefault(_ride[0], set()).add((_ride[1], _ride[2]))
for _name, _r in (("gym", GYM_CASTELIA), ("gym_10", GYM_CASTELIA_10), ("gym_20", GYM_CASTELIA_20), ("gym_burgh", GYM_BURGH)):
    _r["landings"] = [list(t) for t in sorted(_lands.get(_name, ()))]
CASTELIA["rooms"].update({"gym": GYM_CASTELIA, "gym_10": GYM_CASTELIA_10, "gym_20": GYM_CASTELIA_20, "gym_burgh": GYM_BURGH})


# ------------------------------------------------------------------------------------------------- the Castelia Sewers
# 495, in from Thumb Pier's door (89, 20). Black 2's story: Hugh waits inside and walks with you (walk_partners "hugh":
# wild Pokemon two at a time, beside you; he heals your team after every battle); up the north stairs two Plasma Grunts:
# you and Hugh against them; Burgh turns up, Hugh gives you HM04 Strength and goes; Colress watches from the tunnel; Burgh
# heads back to his Gym (b2_sewers_done: Clyde lets you in). The water: high in spring and summer, low in autumn and winter
# (the game swaps the zone's whole map: camview.SEASONAL 495; rmxp_import builds both). Side rooms: two empty manhole
# rooms (496, 497), the medicine scientists (498, 499: a gift a day), Back Street (501: the boss trio); the Empty Lot (500)
# is an area of its own (its grass). The tunnel north (51, 0) is the Relic Passage: a later batch.
# Story flags: b2_thumb_scene -> walk_hugh (he joins) -> b2_sewer_plasma_battled -> b2_sewers_done.
OUTSIDE.update({496: 495, 497: 495, 498: 495, 499: 495, 501: 495})
SEWER_TRAINERS = {13: ("Janitor Felix", 3), 18: ("Janitor Brady", 3), 14: ("Worker Zack", 3), 16: ("Worker Scott", 3),
                  12: ("Doctor Heath", 3), 17: ("Scientist Clarke", 3), 15: ("Scientist Caroline", 3)}
SEWER_PEOPLE = {
    0: {"text": "{rival_name}", "action": "EVENT", "condition": ["b2_thumb_scene", "not:b2_sewer_plasma_battled"],
        "event": {"walk_partner": "hugh"}},
    1: _say("Plasma Grunt", "Team Plasma: What do you want?", condition=["not:b2_sewers_done"]),
    2: _say("Plasma Grunt ", "Team Plasma: Get lost, kid!", condition=["not:b2_sewers_done"]),
    21: [_say("Worker by the channel", "Waitasecond! I dropped something down here! Just wait till I find it!",
              condition=["not:b2_sewers_done"]),
         _say("Worker by the channel ", "Phew... I finally made it back here.",
              "Going further in? There's nothing back there but Trainers.", condition=["b2_sewers_done"])],
    22: _say("Man in the tunnel", "The sewers carry Castelia's rain out to sea. When the water's high, it fills the channels."),
    3: _ball("Poke Ball by the Doctor", "LEFTOVERS", "b2_sewer_leftovers", name="the Leftovers"),
    4: _ball("Poke Ball by the Grunts", "TWISTED_SPOON", "b2_sewer_twisted_spoon", name="a TwistedSpoon"),
    5: _ball("Poke Ball in the west channel", "RARE_BONE", "b2_sewer_rare_bone", name="a Rare Bone"),
    6: _ball("Poke Ball in the south", "X_SP_ATK", "b2_sewer_x_special", name="an X Sp. Atk"),
    7: _ball("Poke Ball on the island", "X_SP_DEF", "b2_sewer_x_sp_def", name="an X Sp. Def"),
    8: _ball("Poke Ball by the south-west stairs", "PEARL", "b2_sewer_pearl", name="a Pearl"),
    9: _ball("Poke Ball by the north stairs", "HEART_SCALE", "b2_sewer_heart_scale", name="a Heart Scale"),
    10: _ball("Poke Ball in the far south", "BLACK_SLUDGE", "b2_sewer_black_sludge", name="Black Sludge"),
    11: _ball("Poke Ball past the Scientist", "TM276", "b2_sewer_tm276", name="TM276 Torment"),
}
SEWER_SCENES = [
    # Hugh's waiting just inside (the game's trigger: 83, 20-21): he walks with you from here
    {"who": "{rival_name}", "trigger": {"zone": [82, 19, 84, 21]}, "condition": ["b2_thumb_scene", "not:walk_hugh_met"],
     "flag": "b2_sewer_hugh_met", "approach": True,
     "lines": ["{rival_name}: So this is the sewer... It's not as stinky as I expected.",
               "{rival_name}: Still... Pokemon live everywhere, don't they?"], "then": "talk"},
    # the north walkway: two Plasma Grunts (the game's trigger: 49-52, 9)
    {"trigger": {"zone": [49, 8, 52, 10]}, "condition": ["walk_hugh", "not:b2_sewer_plasma_battled"], "flag": "b2_sewer_plasma_met",
     "cast": [{"person": "Plasma Grunt", "face": "d", "lines": ["{player_name}: Hey!", "Team Plasma: What do you want?"], "stay": True},
              {"person": "Plasma Grunt ", "face": "d",
               "lines": ["{rival_name}: Team Plasma! You villains!",
                         "Team Plasma: Villains? Don't get in the way of our plan to liberate Pokemon!",
                         "{rival_name}: Liberate? You're just thieves! And you use stolen Pokemon like tools!",
                         "Team Plasma: Shaddap! Hand over your Pokemon!",
                         "{rival_name}: Let's do this, {player_name}!"],
               "then": "event:b2_sewer_plasma", "stay": True}]},
    # after the battle: the Grunts run; Burgh; Hugh's thanks (Strength) and he's off; Colress; Burgh heads home
    {"trigger": {"zone": [44, 2, 56, 12]}, "condition": ["b2_sewer_plasma_battled", "not:b2_sewers_done"], "flag": "b2_sewers_done",
     "cast": [{"person": "Plasma Grunt", "face": "d", "lines": ["Team Plasma: They're really tough! Whatever. We've got the Pokemon we need!",
                                                                 "Team Plasma: Now, we flee!"], "leave_path": [[50, 3], [51, 1]], "gone": True},
              {"person": "Plasma Grunt ", "leave_path": [[52, 3], [51, 1]], "gone": True},
              {"sheet": "b2_hugh.png", "from": [52, 11], "to": "player", "stay": True,
               "lines": ["{rival_name}: Tch! They run off like Patrat!", "{rival_name}: Let's go further in! There might be more of them!"]},
              {"sheet": "b2_c225.png", "from": [41, 7], "to": "player", "stay": True,
               "lines": ["???: I don't think that's necessary, you two."]},
              {"as": 2, "lines": ["{rival_name}: Could you be... Gym Leader Burgh?"]},
              {"as": 3, "lines": ["Burgh: Yessir! The very same. And I've looked: nobody suspicious back there!",
                                  "Burgh: I'm worried about Team Plasma too. But shall we get out of here? This sewer's bugging me."]},
              {"as": 2, "lines": ["{rival_name}: Huh... Didn't you and the other Gym Leaders fight Team Plasma two years ago?",
                                  "{rival_name}: {player_name}, thanks for your help. Here, use this!"],
               "event": {"gift_item": {"HM_STRENGTH": 1}, "flag": "b2_got_strength", "lines": ["{player_name} received HM04 Strength!"]}},
              {"as": 2, "lines": ["{rival_name}: I'll find the rest of those Plasma punks. I'll never forgive Pokemon thieves!"],
               "leave": [88, 20]},
              {"as": 3, "lines": ["Burgh: He's gone..."]},
              {"sheet": "b2_c250.png", "from": [51, 1], "to": "player", "stay": True,
               "lines": ["???: You there! That was an excellent demonstration of battling.",
                         "???: The way you drew out your Pokemon's power against Team Plasma... Astounding. Interesting, too. I see..."],
               "leave": [51, 1]},
              {"as": 3, "lines": ["Burgh: Who... was that?",
                                  "Burgh: Well, no matter. You can stay and train down here. Or come challenge me, the Gym Leader!",
                                  "Burgh: Be seeing you!"], "leave": [41, 7]}]},
]


def _lab(label, items, key, hi):
    """The sewer scientists' medicine (B2W2): one a day, the day's experiment deciding which."""
    return {"text": label, "action": "EVENT", "event": {"lines": list(hi), "daily_gift": {
        "key": key, "items": items, "wait": ["I run my experiments every day. Come back tomorrow and see how it went!"]}}}


SEWERS = route(
    495, SEWER_PEOPLE, {},
    exits={">": ("CASTELIA_CITY", [(89, 20), (89, 21)]), "<": ("CASTELIA_EMPTY_LOT", [(45, 19), (45, 20)]),
           "^": ("RELIC_PASSAGE", [(51, 0)])},
    trainers=SEWER_TRAINERS, scenes=SEWER_SCENES,
    hidden={"1,48": "ULTRA_BALL", "28,73": "POISON_GEM", "50,44": "NUGGET", "52,69": "MAX_REPEL", "19,84": "HP_UP"},
    rooms={
        "manhole_w": room(496, {}, {}, (11, 31)),
        "manhole_e": room(497, {}, {}, (49, 31)),
        "lab_m": room(498, {0: _lab("Scientist", ["ANTIDOTE", "ANTIDOTE", "ANTIDOTE", "FULL_HEAL", "FULL_HEAL", "FULL_RESTORE"],
                                    "b2_sewer_lab_m", ["I'm making medicine from the toxins down here in the sewers.",
                                                       "Here's what today's experiment made. Take it!"])}, {}, (18, 18)),
        "lab_f": room(499, {0: _lab("Scientist ", ["POTION", "POTION", "POTION", "SUPER_POTION", "SUPER_POTION", "REVIVE"],
                                    "b2_sewer_lab_f", ["Lots of toxins build up in the sewers. I think I can make medicine from them!",
                                                       "Here's what today's experiment made. You can have it!"])}, {}, (30, 31)),
        "back_street": room(501, {
            0: _ball("Poke Ball by the trucks", "BLACK_GLASSES", "b2_back_street_glasses", name="BlackGlasses"),
            1: _ball("Poke Ball by the gate", "REPEL", "b2_back_street_repel", name="a Repel"),
            4: _clerk_battle("Roughneck Ricky", "Roughneck Ricky", "ROUGHNECK", "b2_roughneck.png", [559], [32],
                             "Hey! This is our secret spot! You can't come waltzing in like you own the place!",
                             "You aren't one of us... But I don't mind tough Trainers. Beat all three of us, and maybe you're in.",
                             "b2_back_ricky"),
            3: _clerk_battle("Dancer Jean-Paul", "Dancer Jean-Paul", "DANCER", "b2_dancer.png", [554], [32],
                             "This worn-out lot is our paradise! No stranger's trashing it!",
                             "Your battling's got a tight rhythm... I was grooving along before I knew it!", "b2_back_jean_paul"),
            2: [_say("Guitarist Tina", "Tina: If you want to battle me, you'll have to beat Jean-Paul first!", condition=["not:b2_back_jean_paul"]),
                dict(_clerk_battle("Guitarist Tina ", "Guitarist Tina", "GUITARIST", "b2_guitarist.png", [552, 510], [33, 33],
                                   "You made my crew cry! I'm paying you back in spades!",
                                   "People like you deserve a Medal... OK. You're the new boss of this lot!", "b2_back_tina"),
                     condition=["b2_back_jean_paul"])]},
            {}, (25, 1)),
    },
    inside={"11,31": "manhole_w", "49,31": "manhole_e", "18,18": "lab_m", "30,31": "lab_f", "25,1": "back_street", "26,1": "back_street"},
)


def _doors(m, inside):
    for _xy in inside:
        _x, _y = (int(v) for v in _xy.split(","))
        m["art"][_y] = m["art"][_y][:_x] + "D" + m["art"][_y][_x + 1:]


_doors(SEWERS, SEWERS["inside"])
# the east manhole (49, 31) and Scientist Caroline's pocket: walled off by the high water in spring and summer
SEWERS["art"][31] = SEWERS["art"][31][:49] + "c" + SEWERS["art"][31][50:]
SEWERS["inside"] = {k: v for k, v in SEWERS["inside"].items() if k != "49,31"}
# Janitor Brady (38, 20) is there in autumn and winter only (B2W2): off the spring-and-summer map
_bx, _by = 38, 20
SEWERS["art"][_by] = SEWERS["art"][_by][:_bx] + "." + SEWERS["art"][_by][_bx + 1:]
SEWERS["trainer_spots"] = [t for t in SEWERS["trainer_spots"] if t != "Janitor Brady"]
SEWERS["moves"].pop("38,20", None)
# (autumn and winter, the low-water map: you walk the channel floors; the west walkways stay up out of reach (B2W2: Back
# Street and that side are spring-and-summer places), so their doors are left off; the east manhole opens instead)
_LOW_OFF = ("25,1", "26,1", "18,18", "11,31")
for _sm in SEWERS.get("story_maps") or []:
    _sm["map"]["inside"] = {k: v for k, v in dict(SEWERS["inside"], **{"49,31": "manhole_e"}).items() if k not in _LOW_OFF}
    _doors(_sm["map"], _sm["map"]["inside"])

# ------------------------------------------------------------------------------------------------- the Empty Lot
# 500: up the stairs from the Sewers (its door 10, 14-16): a little park, tall and dark grass, a Miracle Seed.
EMPTY_LOT = route(
    500, {0: _ball("Poke Ball in the park", "MIRACLE_SEED", "b2_empty_lot_seed", name="a Miracle Seed"),
          1: _say("Man in the lot", "Apparently, this is where it all began for Castelia City.")},
    {}, exits={">": ("CASTELIA_SEWERS", [(10, 14), (10, 15), (10, 16)])},
)


# ------------------------------------------------------------------------------------------------- Liberty Garden
# 235 the island (the boat from Liberty Pier ties up at Dock 1, west), 236 the lighthouse, 237 up its stairs the room
# where the rich man kept Victini. B2W2 has no Team Plasma here: the islanders remember. Professor Juniper comes over if
# you bring Victini, and Victini dances in its old room (zone 237's trigger, script 4). Jordan 11-21: Victini itself
# waits in that room after the Champion (Black and White's spot, Lv 15).
OUTSIDE.update({236: 235, 237: -1})
VICTINI = {"text": "Victini", "action": "BOSS", "color": "RED", "_look": "sheet:b2_victini.png",
           "boss": {"id": 494, "name": "Victini", "level": 15, "victory_flag": "LIBERTY_GARDEN_boss_defeated"},
           "condition": ["beat_unova_champion", "not:LIBERTY_GARDEN_boss_defeated"]}
LIBERTY_SCENES = [
    # Juniper, out to see the island, spots Victini with you (text 300, 14-18)
    {"trigger": "enter", "condition": ["party_has:494", "not:b2_liberty_juniper"], "flag": "b2_liberty_juniper",
     "cast": [{"sheet": "b2_juniper.png", "from": [11, 11], "to": "player", "gone": True, "leave_path": [[11, 11], [11, 7]],
               "lines": ["Professor Juniper: Oh? Is that... Victini?!",
                         "Professor Juniper: In the Unova Pokedex, Victini was given a special number: zero.",
                         "Professor Juniper: They say that number was chosen in the hope that Victini's knack for victory "
                         "would be shared with whoever carries the Pokedex.",
                         "Professor Juniper: How do you get along with your Pokemon? As your Pokedex fills, you'll find "
                         "your own answer. That's what I'm hoping for. See you!"]}]},
]
VICTINI_ROOM_SCENES = [
    # Victini, home again, wants out of its ball for a moment (text 302)
    {"trigger": {"zone": [2, 8, 7, 9]}, "condition": ["party_has:494", "not:b2_liberty_dance"], "flag": "b2_liberty_dance",
     "cast": [{"sheet": "b2_victini.png", "from": [4, 7], "to": "player", "gone": True,
               "leave_path": [[5, 7], [5, 6], [4, 6], [4, 7]],
               "lines": ["Victini is wriggling inside its Poke Ball... You let it out.",
                         "Victini: Ta-ta-ta-tah!",
                         "Victini went back into its Poke Ball, looking pleased with itself."]}]},
]
LIBERTY_GARDEN = route(
    235, {0: {"text": "Liberty Garden sailor", "action": "EVENT", "event": {
              "lines": ["Back to Castelia City? We cast off any minute now. Climb aboard!"],
              "travel": "CASTELIA_CITY", "land": ["liberty_pier", 21, 12]}},
          1: _say("Girl by the dock", "There's something about this island. Being here makes me feel stronger!"),
          2: _say("Man on the path", "Have you heard? A rich man once hid a Pokemon on this island to keep it safe from bad people!"),
          4: _say("Woman by the lighthouse", "I wonder how that Pokemon felt, shut away in a room for so long...",
                  "It must have been very lonely."),
          3: [_say("Man on the south walk ", "Wait... that Pokemon with you... Is that Victini, the Victory Pokemon?!",
                   "Have you been winning and winning with its help? I wish I had your luck...", condition=["party_has:494"]),
              _say("Man on the south walk", "Victini, the Victory Pokemon... They say it lends its Trainer amazing strength.",
                   "I wonder who has that power now...", condition=["not:party_has:494"])],
          5: _say("Woman on the east walk", "Pokemon do what their Trainers ask, without a second thought.",
                  "And still some people try to use them for bad things!"),
          6: _say("Boy in the trees", "Hardly any tourists come here these days. It's so boring...",
                  "But if the other choice is people like Team Plasma, I'll take boring!")},
    {8: ["LIBERTY GARDEN", "Two hundred years ago a very rich family bought this island and named it Liberty Garden:",
         "a place where people and Pokemon can live freely."],
     9: ["DOCK 2", "The tour boat leaves from Dock 1."],
     10: ["The lighthouse shines with the light of freedom.", "Authorized personnel only."]},
    exits={}, scenes=LIBERTY_SCENES,
    rooms={
        "lighthouse": room(236, {}, {}, (16, 19), stairs={237: ("^", "ROOM:victini_room")}),
        "victini_room": room(237, {}, {}, None, stairs={236: ("v", "ROOM:lighthouse")}, extra_people=[(5, 6, VICTINI)],
                             scenes=VICTINI_ROOM_SCENES),
    },
    inside={"16,19": "lighthouse"},
    landings=[[7, 12]],   # (off the boat at Dock 1: the island's only way in and out is the sailor's boat)
)
LIBERTY_GARDEN["rooms"]["lighthouse"]["title"] = "Lighthouse"
LIBERTY_GARDEN["rooms"]["victini_room"]["title"] = "Lighthouse Room"
_doors(LIBERTY_GARDEN, LIBERTY_GARDEN["inside"])


# ------------------------------------------------------------------------------------------------- the Royal Unova
# 52: the evening cruise from the Cruise Dock (src/world/royal_unova.py: the clock, whistles, crew, prize). One map: the
# corridors to the west (you board facing the bow, so port is the west half: 8 cabin doors, 4 blue; starboard the east:
# 7, 2 blue), the cabins themselves to the east, each door paired with its cabin by the game's own warp numbers. Each
# cabin's person is the day's Trainer (B2W2's teams, before and after the Hall of Fame), else a passenger or a long
# talker (the next whistle blows when they finish). Which Trainers sail which day is our reading; the counts are the
# game's: Mon 4, Tue 3, Wed 4, Thu 5, Fri 4, Sat 6, Sun 7.
RU_DOORS = {g["warp"]: g for g in GEO["52"]["doors"]}


def _ru_links():
    rows = GEO["52"]["rows"]
    out = {}
    for d in GEO["52"]["doors"]:
        t = RU_DOORS[d["to_warp"]]
        land = next(((t["x"] + a, t["y"] + b) for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))
                     if 0 <= t["y"] + b < len(rows) and 0 <= t["x"] + a < len(rows[0]) and rows[t["y"] + b][t["x"] + a] == "."), None)
        if land:
            out["%d,%d" % (d["x"], d["y"])] = [0, land[0], land[1]]
    return out


# (cabin person n: side, door colour) from the cabins' pictures and their doors' places
RU_CABINS = {23: ("port", "blue"), 24: ("port", "blue"), 21: ("port", "blue"), 22: ("port", "blue"),
             17: ("port", "red"), 20: ("port", "red"), 16: ("port", "red"), 14: ("port", "red"),
             19: ("starboard", "blue"), 18: ("starboard", "blue"),
             13: ("starboard", "red"), 12: ("starboard", "red"), 11: ("starboard", "red"), 15: ("starboard", "red"), 10: ("starboard", "red")}
# Trainer: (cabin n, class, look, picture, days, B2W2 team before the Hall of Fame, after it, hello, beaten, off-day lines, talker?)
RU_TRAINERS = {
    "Mariana": (23, "ACE_TRAINER", "b2_c31.png", "b2_ace_trainer_f.png", "mon,wed,sun", ([81, 550], [18, 18]), ([479, 12, 594], [62, 62, 62]),
                "A cruise and a battle: the perfect evening!", "Beaten on my night off... You're good.",
                ["I'm just enjoying the river breeze tonight."], False),
    "Henry": (19, "ACE_TRAINER", "b2_c30.png", "b2_ace_trainer_m.png", "tue,thu,sat,sun", ([507, 183], [18, 18]), ([128, 321], [63, 63]),
              "I booked this cabin to train in peace. You'll do as a sparring partner!", "That settles it. I need more training.",
              ["I'm resting up tonight. Even Ace Trainers need a day off."], False),
    "Sibyl": (24, "LASS", "b2_c15.png", "b2_lass.png", "wed,fri,sat,sun", ([406, 540], [16, 16]), ([433, 413], [61, 61]),
              "You found my cabin! Let's battle!", "Aww... I thought I'd win this time!",
              ["Oh, hi! Want to hear about my trip? So first we went to Nimbasa, and the Musical was so cute, and then my friend said",
               "we should ride the Ferris wheel, but I was scared, so we got ice cream instead, and the ice cream was the Casteliacone,",
               "and it melted all over my hat, and then we saw the Battle Subway, and my friend said it's for really strong Trainers,",
               "and I said I'm really strong, and she laughed, and then... wait, where was I? Oh! The cruise! It's lovely, isn't it?"], True),
    "Brad": (12, "RICH_BOY", "b2_c58.png", "b2_rich_boy.png", "mon,thu,sat", ([504, 41], [16, 16]), ([190, 198], [61, 61]),
             "Daddy bought me this cabin. Now I want a battle!", "Hmph! I'll just buy stronger Pokemon!",
             ["Daddy says the Royal Unova is the finest ship in Unova. He should know: he bought the best cabin!"], False),
    "Elizandra": (18, "LADY", "b2_c22.png", "b2_lady.png", "tue,fri,sun", ([509, 133], [16, 16]), ([52, 37, 133], [60, 60, 60]),
                  "A battle aboard ship? How delightful!", "Oh my. That was rather exciting.",
                  ["Such a lovely evening on the water, isn't it?"], False),
    "Cassandra": (13, "SOCIALITE", "b2_c96.png", "b2_socialite.png", "wed,fri,sat,sun", ([509], [17]), ([510, 24], [61, 61]),
                  "Darling! You've come to battle me? How charming!", "Oh, how dreadful... and in front of the other guests!",
                  ["Darling, have you heard? The Lady down the hall bought a new hat in Castelia, and she wore it to dinner,",
                   "and the Gentleman next door said it looked like a Swanna's nest, and she said his moustache looked like a Patrat's tail,",
                   "and then the Rich Boy laughed so hard he spilled his juice on the captain, and the captain was ever so gracious,",
                   "but I could tell he was furious, simply furious! Isn't a cruise wonderful? There's always something going on!"], True),
    "Robert": (17, "GENTLEMAN", "b2_c44.png", "b2_gentleman.png", "wed,fri,sun", ([506], [17]), ([228, 164, 229], [60, 60, 60]),
               "A Trainer aboard? Let us have a civilized battle.", "Splendid! A battle worthy of this fine ship.",
               ["When I was young, I sailed on this very ship with my late wife. We danced on the deck until the sun came up.",
                "She loved the lights of Castelia from the river. Every year since, I take this cruise on our anniversary.",
                "The ship has changed, the city has grown, but the river is the same. I can almost hear the band playing...",
                "Ah, forgive an old man's ramblings. Thank you for listening so patiently."], True),
    "Tanya": (20, "MAID", "b2_c65.png", "b2_maid.png", "mon,thu,sat", ([239], [17]), ([587, 26], [61, 61]),
              "Welcome! May I offer you... a battle?", "Thank you for the lovely battle. Please enjoy your cruise.", None, False),
    "Chaz": (14, "CLERK", "b2_c52.png", "b2_clerk_m.png", "tue,thu,sun", ([543, 54], [16, 16]), ([168, 419], [61, 61]),
             "A clerk needs a break too! Let's battle!", "Back to work tomorrow... after that, I need the rest.",
             ["Ahh, an evening off. No meetings, no emails, just the river."], False),
    "Abe": (21, "YOUNGSTER", "b2_c11.png", "b2_youngster.png", "mon,thu,sat", ([519, 504], [16, 16]), ([21, 264, 22], [60, 60, 60]),
            "I snuck aboard to battle! Don't tell the captain!", "Aw, man! I'm getting off at the next stop!",
            ["This ship is huge! I've been exploring all evening."], False),
}
RU_PASSENGERS = {   # (cabins with no Trainer: a passenger, or a long talker)
    22: ("Backer", "b2_c59.png", ["Hey! I'm cheering for every Trainer aboard tonight! Go, go, go!",
                                 "You know what I love most about cruises? The whistle! Every time it blows, I cheer!",
                                 "And between whistles I cheer for the river, and the bridges, and the stars, and the captain,",
                                 "and the cook, and the band, and the Pokemon, and YOU! Go, go, go! Woo! ...I'm a little hoarse now."], True),
    16: ("Rich Boy", "b2_c58.png", ["My cabin is the biggest. Well, it's the same size as the others. But it feels bigger."], False),
    11: ("Gentleman", "b2_c44.png", ["A fine evening for a cruise. The lights of the city are splendid from the water."], False),
    15: ("Lady", "b2_c22.png", ["Did you know? The cook aboard used to work at a restaurant in Castelia. Or was it Nimbasa?",
                               "No, I'm sure it was Castelia, because I remember the Casteliacone stand outside. Or was that Nacrene?",
                               "Well, wherever it was, the soup is lovely. You simply must try the soup. Or the fish. Or both!",
                               "Oh dear, have I been talking long? Mother always says I could talk a Chatot into silence."], True),
    10: ("Socialite", "b2_c96.png", ["Darling, isn't the river divine at this hour?"], False),
}


def _ru_cabin(n):
    out = []
    for name, (cab, cls, look, pic, days, early, late, hi, won, off, talks) in RU_TRAINERS.items():
        if cab != n:
            continue
        label = cls.replace("_", " ").title() + " " + name
        flag = "b2_ru_" + name.lower()
        for when, (team, lv), pad in (("not:beat_unova_champion", early, ""), ("beat_unova_champion", late, " ")):
            o = dict(_clerk_battle(label + pad, label, cls, pic, team, lv, hi, won, flag), _look="sheet:" + look)
            o["condition"] = ["weekday:" + days, when]
            out.append(o)
        if off:
            o = _say("Passenger in %s's cabin" % name, *off, _look="sheet:" + look, condition=["not:weekday:" + days])
            if talks:
                o["event"]["cruise"] = "talker"
            out.append(o)
    if n in RU_PASSENGERS:
        cls, look, lines, talks = RU_PASSENGERS[n]
        o = _say("%s in cabin %d" % (cls, n), *lines, _look="sheet:" + look)
        if talks:
            o["event"]["cruise"] = "talker"
        out.append(o)
    return out


RU_PEOPLE = {n: _ru_cabin(n) for n in RU_CABINS}
RU_PEOPLE.update({
    0: {"text": "Sailor by the stairs", "action": "EVENT", "event": {"lines": ["..."], "cruise": "crew"}},
    1: {"text": "Sailor to port", "action": "EVENT", "event": {"lines": ["..."], "cruise": "port_hint"}},
    4: {"text": "Sailor to starboard", "action": "EVENT", "event": {"lines": ["..."], "cruise": "blue_hint"}},
    2: _say("Sailor in the west hall", "Sailor: Mind your step! We're passing under the Skyarrow Bridge soon."),
    3: _say("Sailor at the deck stairs", "Sailor: We sail up the river as far as the Marvelous Bridge, then turn for home."),
    5: _say("Boy in the corridor", "I keep getting lost! All these doors look the same!"),
    7: _say("Girl in the corridor", "Some cabins have red doors and some have blue. I wonder who's behind them?"),
    8: _say("Girl by the port cabins", "The whistle blows every so often. When it's blown five times, we're back in Castelia!"),
    9: _say("Sailor's boy", "My dad's a sailor on this ship! He says the Trainers move cabins every day."),
    6: _say("Man in the hall", "I come every evening. A different crowd every night!"),
})
ROYAL_UNOVA = route(52, RU_PEOPLE, {}, exits={}, landings=[[29, 17]], scenes=[
    # (the top of the stairs: the game's own trigger, script 28 (28-30, 10); Black 2 has no deck map, its stairs end here)
    {"who": "Sailor at the deck stairs", "trigger": {"zone": [28, 10, 30, 10]}, "flag": "b2_ru_deck_note",
     "lines": ["Sailor: The Royal Unova's famous observation deck is just up ahead!"]}])
ROYAL_UNOVA["links"] = _ru_links()
ROYAL_UNOVA["arrive"] = {"CASTELIA_CITY": [29, 17]}   # (aboard at the bow end of the hall, however you came)
ROYAL_UNOVA["cruise"] = {
    "days": {d: [t for t, v in RU_TRAINERS.items() if d in v[4].split(",")] for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")},
    "cabins": {t: {"side": RU_CABINS[v[0]][0], "door": RU_CABINS[v[0]][1], "flag": "b2_ru_" + t.lower()} for t, v in RU_TRAINERS.items()},
    "prizes": {"mon": "LAVA_COOKIE", "tue": "BERRY_JUICE", "wed": "LAVA_COOKIE", "thu": "OLD_GATEAU", "fri": "LAVA_COOKIE",
               "sat": "RAGECANDYBAR", "sun": "RARE_CANDY"},
}
assert [len(ROYAL_UNOVA["cruise"]["days"][d]) for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")] == [4, 3, 4, 5, 4, 6, 7]
for _xy in ROYAL_UNOVA["links"]:   # (each cabin door a doorway you step through)
    _x, _y = (int(v) for v in _xy.split(","))
    ROYAL_UNOVA["art"][_y] = ROYAL_UNOVA["art"][_y][:_x] + "1" + ROYAL_UNOVA["art"][_y][_x + 1:]   # ("1": a passage, the map's "links")


# ------------------------------------------------------------------------------------------------- Route 4 (batch 3b)
# Black 2: 326, a new settlement (rooms 327/519, 520/521, 522/523, 524/525, rest house 328). White 2: 551, the same
# cells with its own blocks (g5map.VERSION_ZONES): building stopped when ruins were found (rooms 526-530). The version
# picked at the start decides which you walk (Jordan 11-21: both, by version). Both: Colress and the Crustle across the
# road (his device wakes them; Magnemite, Klink; a Protein), Pokemon Breeder Irene by the gate, the weekly birds with
# their Hidden Abilities (Jordan: both for everyone, each on its day - Mandibuzz Thursdays, Braviary Mondays).
def _join(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


OUTSIDE.update({327: 326, 520: 326, 522: 326, 524: 326, 328: 326, 519: -1, 521: -1, 523: -1, 525: -1,
                526: 551, 527: 551, 528: 551, 529: 551, 530: 551})
R4_COLRESS_LINES = ["Colress: I've been waiting for you! Curious about what's behind me?",
                    "Colress: Those aren't rocks. They're Crustle. Watch: this device of mine gives Pokemon energy..."]
R4_COLRESS_AFTER = ["Colress: Were those Crustle just lying here, worn out, with their boulders on their backs?",
                    "Colress: Team Plasma said Pokemon should be freed from people. I disagree: people should bring out the "
                    "hidden power in Pokemon!",
                    "Colress: I never asked your name... {player_name}. I'll remember it. Now, let me test whether you're a "
                    "Trainer who can bring out that power!"]
R4_COLRESS_WON = ["Colress: I see! Like the Gym Leaders and the Champion, you bring out a Pokemon's power by being kind to it.",
                  "Colress: Thank you for your help. A token of my gratitude!"]
R4_COLRESS_BYE = ["Colress: If only we could talk with Pokemon to bring out their power... No one could ever do that, could they?",
                  "Colress: Well then, {player_name}, until we meet again."]


def _r4_birds(here, other):
    """The weekly Hidden Ability birds: this version's at its own spot, the other's beside it (both for everyone)."""
    m = {"text": "Mandibuzz", "action": "BOSS", "color": "RED", "_look": "sheet:b2_c348.png", "condition": ["weekday:thu", {"any": ["not:b2_r4_mandibuzz", "legend_back:b2_r4_mandibuzz"]}],
         "boss": {"id": 630, "name": "Mandibuzz", "level": 25, "ability": "WEAK-ARMOR", "victory_flag": "b2_r4_mandibuzz",
                  "lines": ["Kreeeee!"]}}
    b = {"text": "Braviary", "action": "BOSS", "color": "RED", "_look": "sheet:b2_c4712.png", "condition": ["weekday:mon", {"any": ["not:b2_r4_braviary", "legend_back:b2_r4_braviary"]}],
         "boss": {"id": 628, "name": "Braviary", "level": 25, "ability": "DEFIANT", "victory_flag": "b2_r4_braviary",
                  "lines": ["Ra ra ra ra!"]}}
    return (m, b) if here == "mandibuzz" else (b, m)


def _r4_colress(at, crustle, trigger, worker):
    """Colress's scene and the Crustle across the road (the game's own trigger strip in front of him)."""
    people = {n: {"text": "Crustle %d" % i, "action": "EVENT", "_look": "sheet:b2_c326.png", "condition": ["not:b2_colress_r4"],
                  "event": {"lines": ["It's a huge boulder... It doesn't look like a Pokemon could move it."]}}
              for i, n in enumerate(crustle)}
    people[at] = {"text": "Colress", "action": "EVENT", "_look": "sheet:b2_c250.png", "condition": ["not:b2_colress_r4_done"],
                  "event": {"lines": R4_COLRESS_LINES}}
    people[worker] = [_say("Worker by the boulders", "Hey, Trainer! These boulders lined up across the road out of nowhere.",
                           "And Strength won't budge them!", condition=["not:b2_colress_r4"]),
                      _say("Worker by the boulders ", "Who knew they were Crustle? If you like Crustle, the Desert Resort is "
                           "just past here!", condition=["b2_colress_r4"])]
    scenes = [
        {"who": "Colress", "trigger": {"zone": trigger}, "condition": ["not:b2_colress_r4"], "flag": "b2_colress_r4_met",
         "approach": True, "lines": R4_COLRESS_LINES + R4_COLRESS_AFTER, "then": "event:b2_colress_route4"},
        {"who": "Colress", "trigger": {"zone": trigger}, "condition": ["b2_colress_r4", "not:b2_colress_r4_done"],
         "flag": "b2_colress_r4_done", "lines": R4_COLRESS_WON + R4_COLRESS_BYE, "then": "event:b2_colress_protein"}]
    return people, scenes


def _stat_room(z, who, look, stat, item, key, others=None):
    p = {who: {"text": "Ace Trainer in the house", "action": "EVENT", "_look": "sheet:" + look,
               "event": {"lines": ["..."], "stat_check": {"stat": stat, "item": item, "key": key}}}}
    p.update(others or {})
    return p


def _cry_room(n, key):
    return {n: {"text": "Maid who imitates cries", "action": "EVENT", "event": {"lines": ["..."], "cry_quiz": {"item": "POKE_TOY", "flag": key}}}}


def _trade(n, label, want, give, flag, said_want):
    return {n: {"text": label, "action": "EVENT", "event": {
        "lines": [said_want, "Pokemon trade! Pokemon trade! Off they go, and back they come!"],
        "trade": {"want": want, "give": give}, "flag": flag,
        "fail": ["The Pokemon I want is %s. Come back with one!" % {546: "Cottonee", 548: "Petilil"}[want]],
        "done": ["They were your %s and my %s. Now they're your %s and my %s!" % (
            {546: "Cottonee", 548: "Petilil"}[want], {546: "Cottonee", 548: "Petilil"}[give],
            {546: "Cottonee", 548: "Petilil"}[give], {546: "Cottonee", 548: "Petilil"}[want])]}}}


def _healer(n, label):
    return {n: {"text": label, "action": "EVENT", "event": {
        "lines": ["You look worn out! Rest here a minute.", "Your Pokemon were fully healed!"], "heal": True}}}


R4_VENDING = {"text": "Vending machine", "action": "EVENT", "no_tag": True, "_look": "sheet:b2_none.png",   # (model 155, by the rest house)
              "event": {"lines": ["A vending machine! Cold drinks, ready to go."], "stock": ["FRESH_WATER", "SODA_POP", "LEMONADE"]}}
R4_SIGNS = {1: ["ROUTE 4"], 2: ["TRAINER TIPS", "Each move has PP, its Power Points. A move with none left can't be used:",
                                "that's a good time to head for a Pokemon Center!"],
            3: ["ROUTE 4", "Planned route-expansion area"],
            8: ["ROUTE 4"], 9: ["DESERT RESORT AHEAD", "Right: Nimbasa City"],
            6: ["TRAINER TIPS", "Each move has PP, its Power Points. A move with none left can't be used:",
                "that's a good time to head for a Pokemon Center!"]}

_B2_COLRESS, _B2_COLRESS_SCENES = _r4_colress(15, [12, 13, 14, 17, 18, 19, 20, 21, 22, 23, 24], [43, 104, 48, 104], 16)
_B2_BIRD, _B2_OTHER = _r4_birds("mandibuzz", None)
R4_B2_PEOPLE = _join(_B2_COLRESS, {
    25: _B2_BIRD,
    26: _ball("Poke Ball in the sand", "STARDUST", "b2_r4_stardust", name="a Stardust"),
    27: _ball("Poke Ball by the road", "TM055", "b2_r4_tm055", name="TM055 Dig"),
    28: _ball("Poke Ball in the expansion area", "GRIP_CLAW", "b2_r4_grip_claw", name="a Grip Claw"),
    29: _ball("Poke Ball by the water", "MYSTIC_WATER", "b2_r4_mystic_water", name="a Mystic Water"),
    30: _say("Woman by the road", "Places with ruins keep getting built over. Bits of our history get lost..."),
    31: _say("Man by the gate", "The Relic Castle is being buried by the sand. Someday even the memory of it may be buried too."),
    32: _say("Girl in the sand", "Look at the sand, Trainer! See how some of it is darker? Pokemon hide in the darker sand!"),
})
ROUTE_4 = route(
    326, R4_B2_PEOPLE, R4_SIGNS,
    exits={"^": ("JOIN_AVENUE", [(x, 10) for x in range(45, 48)]), "v": ("CASTELIA_CITY", [(x, 119) for x in range(45, 48)]),
           "<": ("DESERT_RESORT_ENTRANCE", [(x, 32) for x in range(15, 20)])},
    trainers={11: "Pokemon Breeder Irene", 1: "Fisherman Hubert", 0: "Fisherman Andrew", 2: "Policeman Braven",
              9: "Policeman Dell", 10: "Policeman Neagle", 8: "Roughneck Silvester", 7: "Roughneck Joey",
              6: "Youngster Sinclair", 5: "Biker Stanley", 3: "Hooligans Rob & Sal"},
    hidden={"22,64": "RED_SHARD", "25,80": "HYPER_POTION", "30,85": "STARDUST", "26,89": "YELLOW_SHARD", "11,95": "GREEN_SHARD"},
    scenes=_B2_COLRESS_SCENES, extra_people=[(31, 89, _B2_OTHER), (14, 52, R4_VENDING)],
    rooms={
        "speed_house": room(327, _stat_room(327, 0, "b2_c31.png", "SPEED", "HEALTH_WING", "b2_r4_speed",
                                            {1: _say("Ace Trainer's brother", "My sister's crazy about Speed. Me? I like Attack.")}),
                            {}, (50, 87), stairs={519: ("^", "ROOM:speed_house_2")}),
        "speed_house_2": room(519, {0: _say("Woman upstairs", "We moved here because they said this place would grow..."),
                                    1: _say("Man upstairs", "With the building stopped, guys like those hooligans hang around."),
                                    2: _say("Girl upstairs", "I love it here! It's close to Castelia and Nimbasa both!")},
                              {}, None, stairs={327: ("v", "ROOM:speed_house")}),
        "trade_house": room(520, _join(_trade(2, "Lass who wants Cottonee", 546, 548, "b2_r4_trade",
                                             "I'd love to trade my Petilil for a Cottonee!"),
                                      {0: _say("Man by the TV", "Sandstorms are awful! But Rock-, Ground- and Steel-types "
                                                 "come through them unhurt."),
                                         1: _say("Herdier", "Grrrrr!")}),
                            {}, (50, 78), stairs={521: ("^", "ROOM:trade_house_2")}),
        "trade_house_2": room(521, {0: _say("Woman upstairs ", "When I'm sad, my Pokemon's round little eyes make it melt away."),
                                    1: _say("Lillipup", "Yip! Yip!"),
                                    2: _ball("Poke Ball by the TV", "WIDE_LENS", "b2_r4_wide_lens", name="a Wide Lens")},
                              {}, None, stairs={520: ("v", "ROOM:trade_house")}),
        "empty_house": room(522, {0: _say("Man in the empty house", "Hi! Welcome! Well... there's nothing here."),
                                  2: _say("Boy in the empty house", "On Thursdays, some Pokemon fly in here."),
                                  1: _say("Woman in the empty house", "Next to a big Pokemon, even I look slim!")},
                            {}, (42, 68), stairs={523: ("^", "ROOM:empty_house_2")}),
        "empty_house_2": room(523, {0: {"text": "Black Belt upstairs", "action": "EVENT", "flag_condition": "not b2_r4_sitrus",
                                        "event": {"lines": ["Hmm? You've got sharp eyes, Trainer! Take these!",
                                                            "Talk to lots of people, and good things happen!"],
                                                  "gift_item": {"SITRUS_BERRY": 3}, "flag": "b2_r4_sitrus"}}},
                              {}, None, stairs={522: ("v", "ROOM:empty_house")}),
        "cry_house": room(524, _cry_room(0, "b2_r4_cry_quiz"), {}, (50, 57), stairs={525: ("^", "ROOM:cry_house_2")}),
        "cry_house_2": room(525, {0: _say("Biker upstairs", "People call those hooligans brats, but they're just hanging out. "
                                          "Never judge a book by its cover.")},
                            {}, None, stairs={524: ("v", "ROOM:cry_house")}),
        "rest_house": room(328, _join(_healer(1, "Woman in the rest house"), {0: _say("Mareep in the rest house", "Glugluglug!")}),
                           {}, (10, 56)),
    },
    inside={"50,87": "speed_house", "50,78": "trade_house", "42,68": "empty_house", "50,57": "cry_house", "10,56": "rest_house"},
)
for _r, _t in (("speed_house_2", "Upstairs"), ("trade_house_2", "Upstairs"), ("empty_house_2", "Upstairs"), ("cry_house_2", "Upstairs")):
    ROUTE_4["rooms"][_r]["title"] = _t
_doors(ROUTE_4, ROUTE_4["inside"])

_W2_COLRESS, _W2_COLRESS_SCENES = _r4_colress(14, [15, 16, 17, 18, 19, 20, 21, 22], [19, 98, 23, 98], 13)
_W2_BIRD, _W2_OTHER = _r4_birds("braviary", None)
R4_W2_PEOPLE = _join(_W2_COLRESS, {
    12: _W2_BIRD,
    23: _ball("Poke Ball by the water", "MYSTIC_WATER", "b2_r4_mystic_water", name="a Mystic Water"),
    24: _ball("Poke Ball in the ruins", "STARDUST", "b2_r4_stardust", name="a Stardust"),
    25: _ball("Poke Ball by the road", "TM055", "b2_r4_tm055", name="TM055 Dig"),
    26: _ball("Poke Ball in the north-west ruins", "LIGHT_CLAY", "b2_r4_light_clay", name="a Light Clay"),
    29: _say("Man by the freeway", "All I do is watch the cars go by on the freeway."),
    28: _say("Man by the gate", "When the ruins turned up, the building stopped. You can't argue with that much history."),
    27: _say("Girl in the sand", "Look at the sand, Trainer! See how some of it is darker? Pokemon hide in the darker sand!"),
})
ROUTE_4_W2 = route(
    551, R4_W2_PEOPLE, R4_SIGNS,
    exits={"^": ("JOIN_AVENUE", [(x, 10) for x in range(45, 48)]), "v": ("CASTELIA_CITY", [(x, 119) for x in range(45, 48)]),
           "<": ("DESERT_RESORT_ENTRANCE", [(x, 32) for x in range(15, 20)])},
    trainers={2: "Pokemon Breeder Irene", 0: "Fisherman Hubert", 1: "Fisherman Andrew", 3: "Backpacker Clifford",
              5: "Twins Tara & Val", 4: "Rich Boy Keenan", 10: "Lady Lina", 7: "Backpacker Rachel", 9: "Pokefan Sachiko",
              8: "Pokefan Norbert", 11: "Backpacker Roland"},
    hidden={"14,84": "RED_SHARD", "16,70": "HYPER_POTION", "52,69": "STARDUST", "47,89": "YELLOW_SHARD", "44,63": "GREEN_SHARD"},
    scenes=_W2_COLRESS_SCENES, extra_people=[(48, 65, _W2_OTHER)],
    rooms={
        "heal_house": room(527, _join(_healer(0, "Woman in the house"), {1: _say("Gothita in the house", "Gelloooo.")}),
                           {}, (56, 68)),
        "attack_house": room(529, _stat_room(529, 1, "b2_c30.png", "ATTACK", "SWIFT_WING", "b2_r4_attack",
                                             {0: _say("Ace Trainer's sister", "My brother's crazy about Attack. Me? I like Speed.")}),
                             {}, (34, 71)),
        "trade_house": room(528, _join(_trade(2, "Youngster who wants Petilil", 548, 546, "b2_r4_trade",
                                             "I'd love to trade my Cottonee for a Petilil!"),
                                      {0: _say("Man by the TV", "Sandstorms are awful! But Rock-, Ground- and Steel-types "
                                                 "come through them unhurt."),
                                         1: _say("Herdier", "Grrrrr!"),
                                         3: _ball("Poke Ball by the window", "BRIGHT_POWDER", "b2_r4_bright_powder", name="a BrightPowder")}),
                           {}, (40, 71)),
        "cry_house": room(530, _cry_room(0, "b2_r4_cry_quiz"), {}, (11, 80)),
        "black_belt_house": room(526, {2: {"text": "Black Belt in the house", "action": "EVENT", "flag_condition": "not b2_r4_sitrus",
                                           "event": {"lines": ["Hmm? You've got sharp eyes, Trainer! Take these!",
                                                               "Go places, talk to people, and good things happen!"],
                                                     "gift_item": {"SITRUS_BERRY": 3}, "flag": "b2_r4_sitrus"}},
                                       0: _say("Boy in the house", "Every Monday, Pokemon fly in from somewhere."),
                                       1: _say("Man in the house", "If Pokemon were freed and showed their true power... "
                                               "would we end up battling for them someday?")},
                                 {}, (48, 95)),
    },
    inside={"56,68": "heal_house", "34,71": "attack_house", "40,71": "trade_house", "11,80": "cry_house", "48,95": "black_belt_house"},
)
_doors(ROUTE_4_W2, ROUTE_4_W2["inside"])
ROUTE_4["story_maps"] = [{"when": ["unova_version:WHITE_2"], "map": ROUTE_4_W2}]
for _m in (ROUTE_4, ROUTE_4_W2):   # (the top-left corner is the desert entrance's own ground, zone 157: walled off here)
    for _y in range(32):
        _m["art"][_y] = "c" * 32 + _m["art"][_y][32:]

# ------------------------------------------------------------------------------------------------- the Desert Resort (3b)
# 157: the desert's entrance on the world map, off Route 4's north-west; its Route Gate (159) opens onto the desert
# itself (158, a sandstorm, Nurse Mariah heals after her battle; the Ranger's Funfest Mission is dropped: he just talks).
# Relic Castle (160, 161): only its top two floors open from the desert in Black 2 (Jordan 11-21: the deep floors come
# with the Relic Passage, condensed).
OUTSIDE.update({159: 157, 161: 160})
DESERT_ENTRANCE = route(
    157, {1: _say("Backpacker by the gate", "The Desert Resort is huge, and its Pokemon are strong. A perfect place to test yourself!"),
          0: _say("Hiker by the gate", "Go through the gate and keep straight on. That's the way to the Relic Castle.")},
    {(22, 11): ["DESERT RESORT AHEAD", "Nicer than the average desert!"]},
    exits={"v": ("UNOVA_ROUTE_4", [(x, 31) for x in range(47, 52)])},
    rooms={"gate": room(159, {1: _say("School Kid in the gate", "Wild Pokemon turn up almost anywhere in the desert, like in a cave.",
                                      "But they don't hide in the pale sand. Walk there and you won't be bothered!"),
                              0: _say("Gate guard", "The Relic Castle, out in the Desert Resort... You can tell time's been cruel to it.")},
                        {}, (18, 8), exits_extra={158: ("^", "DESERT_RESORT")})},
    inside={"18,8": "gate"},
)
DESERT_ENTRANCE["rooms"]["gate"]["title"] = "Route Gate"
_doors(DESERT_ENTRANCE, DESERT_ENTRANCE["inside"])

DESERT_PEOPLE = {
    19: {"text": "Backpacker who wants water", "action": "EVENT", "flag_condition": "not b2_desert_soft_sand",
         "event": {"lines": ["I came all the way out here to train... It'd be so much easier with a Water-type.",
                             "You're only the second person to come out here and talk to me! I'm so touched. Take this!",
                             "If a Pokemon holds Soft Sand, its Ground-type moves get stronger!"],
                   "gift_item": {"SOFT_SAND": 1}, "flag": "b2_desert_soft_sand",
                   "done": ["If a Pokemon holds Soft Sand, its Ground-type moves get stronger!"]}},
    0: _say("Pokemon Ranger in the sand", "This desert keeps us Rangers busy! Watch out for the sandstorm out here."),
    18: _say("Hiker in the dunes", "They say the Relic Castle was a city built by a hero of old and the dragon that went with them."),
    20: _say("Treasure hunter", "A sea of sand and a castle buried in it! There must be treasure here!",
             "It's been a year since my treasure sense went off... Living my dream every day. Is THAT the treasure?!"),
    10: _ball("Poke Ball in the sand", "RED_SHARD", "b2_desert_red_shard", name="a Red Shard"),
    11: _ball("Poke Ball by the rocks", "BLUE_SHARD", "b2_desert_blue_shard", name="a Blue Shard"),
    12: _ball("Poke Ball in the east", "YELLOW_SHARD", "b2_desert_yellow_shard", name="a Yellow Shard"),
    13: _ball("Poke Ball in the south-west", "MAX_ETHER", "b2_desert_max_ether", name="a Max Ether"),
    14: _ball("Poke Ball in the south", "GREEN_SHARD", "b2_desert_green_shard", name="a Green Shard"),
    15: _ball("Poke Ball near the nurse", "STARDUST", "b2_desert_stardust", name="a Stardust"),
    16: _ball("Poke Ball by the castle", "HEART_SCALE", "b2_desert_heart_scale", name="a Heart Scale"),
    17: _ball("Poke Ball in the north-west", "NUGGET", "b2_desert_nugget", name="a Nugget"),
    5: [{"text": "Nurse Mariah ", "action": "EVENT", "condition": ["not:b2_desert_mariah"], "_look": "sheet:b2_c51.png",
                            "event": {"lines": ["Nurse Mariah: Battling in a sandstorm? Then let's see how your team holds up!"],
                                      "flag": "b2_desert_mariah",
                                      "battle": {"name": "Nurse Mariah", "class": "NURSE", "sprite": "nurse.png", "team": [173],
                                                 "levels": [22], "rewards": {"balls": 2},
                                                 "dialogue": {"player_won": ["Nurse Mariah: Well done! Come back any time and "
                                                                             "I'll heal your team."]}},
                                      "done": ["Nurse Mariah: Come back any time and I'll heal your team."]}},
        {"text": "Nurse Mariah", "action": "EVENT", "condition": ["b2_desert_mariah"],
         "event": {"lines": ["Nurse Mariah: Let me take care of your Pokemon!", "Your Pokemon were fully healed!"], "heal": True}}],
}
DESERT_RESORT = route(
    158, DESERT_PEOPLE, {},
    exits={"v": ("DESERT_RESORT_ENTRANCE", [(x, 83) for x in range(82, 85)]), "^": ("RELIC_CASTLE", [(61, 29)])},
    trainers={1: "Psychic Tommy", 2: "Backpacker Tami", 3: "Pokemon Ranger Anja", 4: "Pokemon Ranger Jaden",
              6: "Psychic Future", 7: "Backpacker Walt", 8: "Backpacker Sam", 9: "Backpacker Clara"},
    hidden={"56,35": "GROUND_GEM", "44,38": "RED_SHARD", "55,56": "BLUE_SHARD", "65,65": "STAR_PIECE", "24,82": "FIRE_STONE",
            "76,24": "SUPER_REPEL"},
)

RELIC_CASTLE = route(
    160, {1: _say("Hiker in the ruins", "Two things I've learned about quicksand: walk through the middle and you fall in.",
                  "Run through it, and you fall in too!")},
    {},
    exits={"v": ("DESERT_RESORT", [(21, 21)])},
    trainers={0: "Psychic Perry"},
    rooms={"b1f": room(161, {0: _clerk_battle("Psychic Dua", "Psychic Dua", "PSYCHIC", "psychic_f.png", [574], [23],
                                              "The castle's old power still lingers here. Can you feel it?",
                                              "My mind's eye saw that coming... too late.", "b2_relic_dua"),
                             1: _clerk_battle("Psychic Low", "Psychic Low", "PSYCHIC", "psychic_m.png", [577], [23],
                                              "Down here, the sand whispers. It told me you were coming!",
                                              "The sand didn't whisper that part.", "b2_relic_low"),
                             2: _ball("Poke Ball in the sand", "TM036", "b2_relic_tm036", name="TM036 Rock Tomb")},
                       {}, (20, 3))},
    inside={"20,3": "b1f", "4,17": "b1f"},
)
RELIC_CASTLE["rooms"]["b1f"]["title"] = "B1F"
RELIC_CASTLE["rooms"]["b1f"]["hidden"] = {"4,9": "HEART_SCALE"}
# (the floors as the file pairs them: 1F (20,3) <-> B1F (20,3), 1F (4,17) <-> B1F (12,18). Row 7 by the top-right stairs
#  is flowing sand at the hall's own height (lift -2.2 both sides): walkable. The two quicksand pits (the game's triggers
#  2,9 and 11,10, 5x5) drop you to B1F's upper half, as Black 2's quicksand does)
_rc = RELIC_CASTLE["art"]
_rc[7] = _rc[7][:18] + "......" + _rc[7][24:]
for _x, _y in ((4, 11), (13, 12)):
    _rc[_y] = _rc[_y][:_x] + "1" + _rc[_y][_x + 1:]
RELIC_CASTLE["links"] = {"4,11": [1, 8, 8], "13,12": [1, 8, 8]}
_b1 = RELIC_CASTLE["rooms"]["b1f"]
_b1["art"][18] = _b1["art"][18][:12] + "w" + _b1["art"][18][13:]
_b1["exits"]["w"] = "OUT:4,17"
_b1["land"] = {"4,17": [3, 16]}
_b1["parts"] = True   # (two halves: the upper reached by the quicksand and its stairs, the lower by its own stairs)
_doors(RELIC_CASTLE, RELIC_CASTLE["inside"])

# ------------------------------------------------------------------------------------------------- Join Avenue (3b)
# 490: the avenue, north of Route 4, south of Nimbasa; 491: the manager's office. The owner meets you as you walk in (the
# game's trigger, row 69) and makes you manager (src/world/join_avenue.py: Black 2's offline rules, Jordan 11-21). Three
# visitor spots and a shopkeeper at each of the 8 lots (the lot signs down the avenue).
OUTSIDE.update({491: 490})
JA_LOT_SIGNS = [(9, 9), (17, 16), (9, 23), (17, 30), (9, 37), (17, 44), (9, 51), (17, 58)]
JA_KEEPER_LOOKS = ["b2_c24.png", "b2_c22.png", "b2_c33.png", "b2_c26.png", "b2_c44.png", "b2_c96.png", "b2_c58.png", "b2_c65.png"]


def _ja_keepers():
    out = []
    for n, (sx, sy) in enumerate(JA_LOT_SIGNS):
        kx = sx + 1 if sx < 13 else sx - 1
        out.append((kx, sy + 1, {"text": "Shopkeeper on lot %d" % (n + 1), "action": "EVENT", "condition": ["ja_lot_%d" % n],
                                 "_look": "sheet:" + JA_KEEPER_LOOKS[n], "event": {"lines": ["..."], "join_avenue": "shop", "lot": n}}))
    return out


JA_LOOKS = {"market": "b2_c52.png", "florist": "b2_c22.png", "cafe": "b2_c65.png", "dojo": "b2_c46.png", "antique": "b2_c44.png",
            "raffle": "b2_c58.png", "salon": "b2_c96.png", "nursery": "b2_c33.png"}   # (= join_avenue.LOOKS: their look follows their dream)
JA_VISITOR = lambda i, _look=None: [{"text": "Visitor %d %s" % (i + 1, k), "action": "EVENT", "condition": ["b2_join_manager", "ja_visitor:%d:%s" % (i, k)],
                                     "_look": "sheet:" + look, "event": {"lines": ["..."], "join_avenue": "visitor", "slot": i}}
                                    for k, look in JA_LOOKS.items()]
JA_OWNER = {"text": "Join Avenue owner", "action": "EVENT", "condition": ["not:b2_join_manager"], "_look": "sheet:b2_c52.png",
            "event": {"lines": ["..."], "join_avenue": "owner"}}
JOIN_AVENUE = town(
    490, {0: JA_OWNER,
          3: _say("Assistant Jacci", "Jacci: Welcome! The owner's just over here.", condition=["not:b2_join_manager"]),
          4: _say("Assistant Future", "Future: A brand-new avenue! Exciting, isn't it?", condition=["not:b2_join_manager"]),
          1: JA_VISITOR(0, "b2_c31.png"), 2: JA_VISITOR(1, "b2_c30.png")},
    {(9, 65): ["JOIN AVENUE", "Meet, discover, and have fun!"],
     **{(x, y): ["JOIN AVENUE: LOT %d" % (n + 1), "A shop opens here when a visitor's dream comes true."]
        for n, (x, y) in enumerate(JA_LOT_SIGNS)}},
    {491: ("house", "office")},
    {"office": room(491, {3: {"text": "Assistant Jacci ", "action": "EVENT", "event": {"lines": ["..."], "join_avenue": "assistant"}},
                          2: _say("Assistant Future ", "Future: Invite visitors whose dreams you like, and recommend the shops they'll love!"),
                          1: _say("Owner in the office", "Owner: Just stopping by to see how my avenue's doing! Keep it up, manager.",
                                  condition=["b2_join_manager"]),
                          0: _say("Receptionist", "Welcome to the manager's office. The manager's assistants are always here to help.")},
                    {}, (8, 66))},
    extra_people=[(15, 40, JA_VISITOR(2, "b2_c27.png"))] + _ja_keepers(),
    edges={"^": ("NIMBASA_CITY", [(x, 5) for x in range(10, 17)]), "v": ("UNOVA_ROUTE_4", [(x, 74) for x in range(9, 18)])},
    scenes=[{"who": "Join Avenue owner", "trigger": {"zone": [9, 69, 18, 69]}, "condition": ["not:b2_join_manager"],
             "flag": "b2_join_owner_met", "approach": True, "lines": ["Owner: Hello there! Welcome to Join Avenue! Please, come and talk to me!"]}],
)
JOIN_AVENUE["rooms"]["office"]["title"] = "Manager's Office"


# ====================================================================================================== batch 4a (11-23)
# Nimbasa City (its Center, houses, gates, Big Stadium's and Small Court's lobbies, the amusement park, the Gym and the
# Shining Roller Coaster), Route 16 (its Bridge Gate), Lostlorn Forest, Route 5 (Bianca's Fly, its Hidden Grotto, the
# crowd at the drawbridge). Black 2's teams from its own trainer table (dev/builders/unova_trainers.py: the routes' pools,
# and town_maps/unova_teams.json for the story and Gym battles, _b2). Jordan's calls: unova_check/DECISIONS.md "Batch 4".
# Story flags in order: b2_nimbasa_gym_out (the guide at the Gym) -> b2_elesa_coaster (the roller coaster's lady) ->
# gym_trainer_NIMBASA_CITY_1-3 -> b2_bolt_badge -> b2_nimbasa_plasma_battled -> b2_nimbasa_plasma (Hugh) -> b2_got_fly
# (Route 5, Bianca) -> b2_charles (the drawbridge). Side: b2_subway_bosses (you and Rosa / Nate against Ingo and Emmet),
# b2_nimbasa_rival (your picked BW rival's meeting). Batch 4b: Gear Station, the Battle Subway, Anville; 4c: the Musical,
# Big Stadium / Small Court's daily athletes, the roller coaster's switches, the Dropped Item.
# Zones: 62 the city, 63 the Gym, 64 the park, 65 the Center, 79/80 Big Stadium's lobby and stands, 84/85 Small Court's,
# 88/89 and 94/95 houses, 91 / 92 the gates west (Route 5) and east (Route 16), 93 the Battle Institute, 585 the roller
# coaster; 329 Route 5, 330 its trailer; 383 Route 16, 384 the Bridge Gate; 385 Lostlorn Forest, 386 its trailer.
_TEAMS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "unova_teams.json"), encoding="utf-8"))


def _b2(tid, **over):
    """A battle from Black 2's own trainer table (dev/builders/unova_trainers.py writes unova_teams.json)."""
    t = {k: v for k, v in _TEAMS[str(tid)].items() if k != "b2_id"}
    t.update(over)
    return t


def _b2_battle(label, tid, flag, lines, won, done, name=None, **kw):
    """A trainer standing in a room or park who battles when talked to (a Gym's catwalk, the roller coaster)."""
    b = _b2(tid)
    b["name"] = name or b["name"]
    b["dialogue"] = {"player_won": list(won)}
    out = {"text": label, "action": "EVENT", "event": {"lines": list(lines), "battle": b, "flag": flag, "done": list(done)}}
    out.update(kw)
    return out


NIMBASA_ROOMS = {62: "MAIN", 65: "center", 79: "stadium", 80: "stadium_stands", 84: "court", 85: "court_stands",
                 88: "house_w", 89: "house_w_2f", 94: "house_e", 95: "house_e_2f", 93: "institute", 91: "gate_w", 92: "gate_e",
                 64: "park", 63: "gym", 585: "coaster",
                 # batch 4c: the Musical Theater, the five playing fields (reached by the lobbies' warp panels)
                 77: "musical", 81: "field_football", 82: "field_baseball", 83: "field_soccer", 86: "court_tennis",
                 87: "court_basketball",
                 # batch 4b: Gear Station (66), its eight platforms (67-74: the lines in the file's own order, text 76 lines 18-25),
                 # the Subway car (75) and the lines' end station (76)
                 66: "gear", 67: "plat_single", 68: "plat_double", 69: "plat_multi", 70: "plat_wifi", 71: "plat_super_single",
                 72: "plat_super_double", 73: "plat_super_multi", 74: "plat_anville", 75: "car", 76: "subway_stop"}
NIMBASA_AREAS = {329: "UNOVA_ROUTE_5", 383: "UNOVA_ROUTE_16", 490: "JOIN_AVENUE"}
OUTSIDE.update({z: -1 for z in NIMBASA_ROOMS if z != 62})
OUTSIDE.update({384: 383, 330: 329})   # (Route 16's Bridge Gate, Route 5's trailer)


def nimbasa_room(z, people, signs, extra_people=(), scenes=None, title=None, **more):
    """A Nimbasa room or the park: each door leads where the game's own warp does (as Castelia's streets: castelia_room)."""
    g = GEO[str(z)]
    rows, ppl, sg, doors = _place(z, people, signs, extra_people, counters=not g["outdoor"])
    exits, chars = {}, {}
    for d in doors:
        tgt = ("ROOM:" + NIMBASA_ROOMS[d["to"]]) if d["to"] in NIMBASA_ROOMS else NIMBASA_AREAS.get(d["to"])
        if not tgt:
            continue
        ch = chars.get(tgt) or _EXIT_CHARS[len(chars)]
        chars[tgt] = ch
        for k in range(max(1, d["w"])):
            for j in range(max(1, d.get("h", 1))):
                if 0 <= d["x"] + k < len(rows[0]) and 0 <= d["y"] + j < len(rows):
                    rows[d["y"] + j][d["x"] + k] = ch
        exits[ch] = tgt
    _thin(rows, set(exits))
    if not g["outdoor"] and z != 63:
        _no_drops(z, rows, set(exits))
    m = {"theme": "room", "art": ["".join(r) for r in rows], "exits": exits, "buildings": {}, "roofs": _picture(z, g["outdoor"]),
         "people": ppl}
    if sg:
        m["signs"] = sg
    if scenes:
        m["scenes"] = scenes
    if title:
        m["title"] = title
    m.update(_camera(z))
    m.update(more)
    return m


# ---------------------------------------------------------------------------------------------------------- Nimbasa City
def _subway_bosses(who, pic, ids):
    """You and Rosa / Nate (their team by your starter: Snivy, Tepig, Oshawott) against Ingo and Emmet."""
    p = _b2(ids[0])
    partner = {"name": who, "class": "PKMN_TRAINER", "sprite": pic, "team": p["team"], "levels": p["levels"],
               "team_choice": {s: _TEAMS[str(t)]["team"] for s, t in zip(("495", "498", "501"), ids)}}
    return _b2(732, name="Subway Boss Ingo", sprite="b2_ingo.png", rewards={"balls": 4},
               battle_options={"double": True, "partner": partner, "second_trainer": _b2(733, rewards={"balls": 4})},
               dialogue={"player_won": ["Ingo: Bravo! You and your Pokemon make a fine combination!",
                                        "Emmet: I lost, but I had fun! Ride the subway and battle us there next time!"],
                         "player_lost": ["Emmet: Follow the rules and drive safely! All aboard!"]})


PLASMA_HERE = ["b2_bolt_badge", "not:b2_nimbasa_plasma"]            # (Team Plasma outside Big Stadium: after Elesa's badge)
BOSSES_HERE = ["not:b2_subway_bosses"]                              # (Ingo and Emmet outside Gear Station, till you've battled)
NIMBASA_PEOPLE = {
    0: _say("Plasma Grunt", "Plasma Grunt: What are you looking at?", condition=PLASMA_HERE),
    1: _say("Plasma Grunt ", "Plasma Grunt: Move along, kid.", condition=PLASMA_HERE),
    2: _say("Plasma Grunt  ", "Plasma Grunt: We're just standing here. Is that a crime?", condition=PLASMA_HERE),
    4: _say("Plasma Grunt   ", "Plasma Grunt: Trainers sure are unruly these days.", condition=PLASMA_HERE),
    3: _say("{rival_name}", "{rival_name}: These are the creeps! Pokemon thieves, every one of them!", condition=PLASMA_HERE),
    # the Subway Bosses and the Trainer who wants to take them on with you (a girl player: Nate; a boy: Rosa)
    5: [{"text": "Rosa", "action": "EVENT", "_look": "sheet:b2_rosa.png", "condition": BOSSES_HERE + ["world:unova_story:male_player"],
         "event": {"lines": ["Rosa: I came to test my skills on the Battle Subway, and the Subway Bosses are right here!",
                             "Rosa: They'll battle, but only two on two. Will you team up with me? Please?",
                             "Rosa: Thanks! I'm Rosa! Let's be the best partners ever!"],
                   "flag": "b2_subway_bosses", "battle": _subway_bosses("Rosa", "b2_rosa.png", (363, 364, 365))}},
        {"text": "Nate", "action": "EVENT", "_look": "sheet:b2_nate.png", "condition": BOSSES_HERE + ["world:unova_story:female_player"],
         "event": {"lines": ["Nate: I came to test my skills on the Battle Subway, and the Subway Bosses are right here!",
                             "Nate: They'll battle, but only two on two. Will you team up with me?",
                             "Nate: Thanks! The name's Nate! Pokemon-fan teamwork is better than perfect!"],
                   "flag": "b2_subway_bosses", "battle": _subway_bosses("Nate", "b2_nate.png", (360, 361, 362))}}],
    6: _say("Subway Boss Ingo", "Ingo: I am Ingo, a Subway Boss. I usually battle aboard the trains that leave Gear Station.",
            condition=BOSSES_HERE),
    7: _say("Subway Boss Emmet", "Emmet: I'm Emmet. Subway Boss. I love Double Battles! Two Pokemon together!", condition=BOSSES_HERE),
    10: _say("Athlete in the plaza", "Athletes and their Pokemon make a super team! See them play at Big Stadium and Small Court!"),
    11: _say("Singer in the plaza", "Nimbasa City is full of plaaaces for toughening uuup your Pokemon!"),
    12: _say("Nurse in the plaza", "I'd love to go to Anville Town some day. They say the trains go there from Gear Station."),
    13: _say("Man by the avenue", "Every time I walk past Join Avenue, I wonder which new shop has opened."),
    14: _say("Backpacker in the plaza", "Triple Battles and Rotation Battles need three Pokemon. I only have two partners so far!"),
    15: _say("Little girl", "I was good, so I got to come to the amusement park! Pansear came too!"),
    16: _say("Pansear", "Pansear: Raesnap!"),
    17: _say("Boy in the plaza", "I rode the roller coaster and it went zoom, zoom! Just like Quick Attack!"),
    18: _say("Woman in the plaza", "Nimbasa's Gym Leader, Elesa, is a fashion model! I'd love to see her walk the catwalk."),
    19: _say("Woman by the Institute", "A Trainer! The woman of mystery at the Battle Institute tests Trainers' skills...",
             "...over the wireless network, though. Come back when you've beaten the Champion!"),
}
NIMBASA_SIGNS = {1: ["NIMBASA CITY", "Lit by the flash of lightning!"], 2: ["BIG STADIUM", "Baseball, football and soccer"],
                 3: ["SMALL COURT", "Tennis and basketball"], 4: ["BATTLE SUBWAY", "Battle and ride!"],
                 5: ["MUSICAL THEATER", "Props, music, dance, excitement!"],
                 6: ["TRAINER TIPS", "Games are played at set times in Big Stadium and Small Court.",
                     "You might battle your favourite athlete!"],
                 10: ["TRAINER TIPS", "The Musical Theater is always looking for performers!",
                      "Take part again and again for more wonderful Props."],
                 11: ["BATTLE INSTITUTE", "Test your Trainer skills!"]}
NIMBASA_SCENES = [
    # just in from Join Avenue: your picked BW rival (Cheren or Bianca) has come to see the city too (Jordan 11-23: a meeting,
    # no battle; BW's rival met you here)
    {"trigger": {"zone": [44, 58, 48, 62]}, "condition": ["friend:cheren", "not:b2_nimbasa_rival"], "flag": "b2_nimbasa_rival",
     "cast": [{"sheet": "b2_cheren.png", "from": [46, 54], "to": "player",
               "lines": ["Cheren: {player_name}! You made it to Nimbasa too.",
                         "Cheren: Two years ago I passed through here on my own journey. I wanted to be strong, and I didn't know why.",
                         "Cheren: Now I teach at Aspertia. ...Elesa's Gym is in the amusement park. Show her what you've learned."],
               "leave": [46, 40]}]},
    {"trigger": {"zone": [44, 58, 48, 62]}, "condition": ["friend:bianca", "not:b2_nimbasa_rival"], "flag": "b2_nimbasa_rival",
     "cast": [{"sheet": "b2_bianca.png", "from": [46, 54], "to": "player",
               "lines": ["Bianca: {player_name}! Hi hi! Isn't Nimbasa amazing? All the lights!",
                         "Bianca: Two years ago my dad came all the way here to take me home. I'd never seen him so worried!",
                         "Bianca: We talked it over, and he let me keep going. ...Elesa helped, actually. Go say hi at her Gym!"],
               "leave": [46, 40]}]},
    # Hugh and Team Plasma outside Big Stadium (the game's trigger: x 25, rows 21-24), after Elesa's badge
    {"trigger": {"zone": [25, 21, 25, 24]}, "condition": PLASMA_HERE + ["not:b2_nimbasa_plasma_battled"], "flag": "b2_nimbasa_plasma_met",
     "cast": [{"person": "{rival_name}", "face": "l", "stay": True,
               "lines": ["{rival_name}: Hold it! What are you lot up to here?"]},
              {"person": "Plasma Grunt", "face": "r", "stay": True,
               "lines": ["Team Plasma: Nothing. We're just standing here. Why bother us?"]},
              {"person": "{rival_name}", "face": "l", "stay": True,
               "lines": ["{rival_name}: You didn't do anything to me. But I'll never forgive Pokemon thieves like you!"]},
              {"person": "Plasma Grunt", "face": "r", "stay": True,
               "lines": ["Team Plasma: Trainers these days... You think your Pokemon's strength is your own?"]},
              {"person": "{rival_name}", "face": "d", "lines": ["{rival_name}: {player_name}! Cover me!"]}],
     "then": "event:b2_nimbasa_plasma"},
    {"trigger": {"zone": [20, 18, 30, 26]}, "condition": ["b2_nimbasa_plasma_battled", "not:b2_nimbasa_plasma"], "flag": "b2_nimbasa_plasma",
     "cast": [{"person": "Plasma Grunt", "face": "r",
               "lines": ["Team Plasma: We give up! Two kids...",
                         "Team Plasma: Just so you know, Team Plasma is searching for something. When we find it, our secret weapon "
                         "will show its true power!", "Team Plasma: Farewell!"],
               "leave": [0, 22], "gone": True},
              {"person": "{rival_name}", "to": "player",
               "lines": ["{rival_name}: Five years ago, Team Plasma stole my little sister's Purrloin. It was a present for her.",
                         "{rival_name}: I was just a kid. I couldn't do anything... That's why I have to get stronger!",
                         "{rival_name}: Good work, by the way. Here, let me patch your team up.",
                         "{rival_name} fully healed {player_name}'s Pokemon!",
                         "{rival_name}: Keep filling that Pokedex and getting stronger. I'm counting on you!"],
               "heal": True, "leave": [0, 22]}]},
]
NIMBASA_GYM = nimbasa_room(63, {
    4: {"text": "Gym", "action": "GYM", "_look": "sheet:b2_c226.png"},
    1: _gift("Gym guide", ["Welcome to the Nimbasa Gym! A stylish battle and fashion show of Pokemon and Trainers starts now!",
                           "Proceed by beating the Trainers waiting on the catwalk.",
                           "Electric-types don't like Ground-type moves... but watch out: Emolga floats above them!",
                           "Here, take this for now!"], "FRESH_WATER", "b2_clyde_nimbasa",
             ["Elesa uses bright Electric-type attacks. Shine even brighter than her!"]),
    2: _b2_battle("Beauty Nikola", 207, "gym_trainer_NIMBASA_CITY_1",
                  ["Beauty Nikola: Are you beautiful as a Trainer? Surprise me!"], ["Beauty Nikola: You and your Pokemon sparkle!"],
                  ["Ms. Elesa is strong and beautiful. Don't think she's the same as us."]),
    3: _b2_battle("Beauty Fleming", 208, "gym_trainer_NIMBASA_CITY_2",
                  ["Beauty Fleming: Beauty isn't just about looks. Strength is part of it too!"],
                  ["Beauty Fleming: You shine as brightly as Elesa!"], ["Strength is part of beauty, for you and for Elesa."]),
    0: _b2_battle("Beauty Ampere", 209, "gym_trainer_NIMBASA_CITY_3",
                  ["Beauty Ampere: The show's finale! Let's see if you're worthy of Elesa's stage!"],
                  ["Beauty Ampere: A match between you and Elesa this close... I can't wait!"],
                  ["That's a battle I want to see!"], name="Beauty Ampere"),
}, {(18, 57): ["NIMBASA CITY POKEMON GYM", "Leader: Elesa", "The Shining Beauty"],
    (12, 57): ["NIMBASA CITY POKEMON GYM", "Leader: Elesa", "The Shining Beauty"]}, title="Nimbasa Gym")
# The catwalk's lights (11-23, closing 4a: Jordan "Build the lighting"). Black 2's gimmick 1 -> overlay 92 (gym_elec.c):
# the runway is dark; the zone's triggers across it at file rows 54, 39 and 24 (var 0x409b = 0/1/2) each light the next
# stretch, up to its model, "a new section is lit up as you approach each Gym Trainer, until you reach Elesa singing on
# the stage". The entrance and Elesa's stage are lit from the start. "lit": rectangles lit once their flag is set (None:
# always); "flags"/"radius" are the plain dark room's light round you (wider with each section) where "lit" isn't drawn.
_GYM_LIT = [[7, 55, 13, 61, None], [9, 39, 11, 54, "b2_elesa_lit1"], [9, 24, 11, 38, "b2_elesa_lit2"],
            [9, 8, 11, 23, "b2_elesa_lit3"], [1, 0, 20, 7, None]]
NIMBASA_GYM["dark"] = {"flags": ["b2_elesa_lit1", "b2_elesa_lit2", "b2_elesa_lit3"], "radius": [2.5, 3.5, 4.5], "lit": _GYM_LIT}
NIMBASA_GYM["scenes"] = (NIMBASA_GYM.get("scenes") or []) + [
    {"trigger": {"zone": [9, row, 11, row]}, "flag": "b2_elesa_lit%d" % k, "cast": [], "call": ["(Click! A spotlight comes on further down the catwalk.)"]}
    for k, row in ((1, 54), (2, 39), (3, 24))]
_COASTER_WOMAN = _gift("Woman at the back", ["Oh my! Did you come here looking for the Gym Leader?",
                                             "I'm sorry, you just missed her. She's gone back to her Gym!",
                                             "Take this for coming all this way!"], "PARALYZE_HEAL", "b2_elesa_coaster",
                       ["The Gym Leader loves the thrill of this roller coaster."])
_COASTER_ROLAN = _b2_battle("Rich Boy Rolan", 621, "b2_coaster_rolan", ["Rich Boy Rolan: Are you cool on a roller coaster? I'll "
                                                                        "overwhelm you with the speed I learned riding it!"],
                            ["Rich Boy Rolan: Your way of battling... It's elegant!"], ["Faster! Faster! Speed feels great!"])
_COASTER_COLETTE = _b2_battle("Lady Colette", 148, "b2_coaster_colette",
                              ["Lady Colette: Ms. Elesa toughened me up too. I won't give up easily!"],
                              ["Lady Colette: An honour to face a Trainer like you."], ["The ride's nearly at its finale."])
# The cars (11-23, closing 4a: Jordan "Now, before 4b"). Black 2's gimmick 47 -> overlay 102: nine car stops at the platforms'
# edges (0x21f0228: entrance 14,39 and 5,39; middle 22,39; left 16,27 and 16,15; back 41,40 and 49,40; top 34,8 and 22,8)
# and the four switches' routes (0x21f01f8, two settings each; 255 = no car): middle switch (29,33): middle <-> entrance /
# middle <-> left's foot; left switch (13,16): - / left's top <-> back; back switch (46,41): - / back's east <-> top's east;
# top switch (25,9): - / entrance's west <-> top's west. Each switch flips as you step on it (the room's triggers, scripts
# 2-5); each car carries you to its partner stop and you step off onto that platform (an animated scene). The cars' and
# switches' own model positions are the table at 0x21f0268 (the switches at exactly the trigger tiles).
_STOPS = [(14, 39), (22, 39), (16, 27), (16, 15), (41, 40), (49, 40), (34, 8), (22, 8), (5, 39)]
_OFF = {(14, 39): (14, 40), (22, 39): (22, 40), (16, 27): (16, 28), (16, 15): (16, 16), (41, 40): (41, 41), (49, 40): (49, 41),
        (34, 8): (34, 9), (22, 8): (22, 9), (5, 39): (5, 40)}   # (the platform tile you step off onto)
_SWITCHES = [((29, 33), [(1, 0), (1, 2)]), ((13, 16), [None, (4, 3)]), ((46, 41), [None, (6, 5)]), ((25, 9), [None, (8, 7)])]


def _coaster_scenes():
    out = []
    for k, ((sx, sy), states) in enumerate(_SWITCHES):
        out.append({"trigger": {"zone": [sx, sy, sx, sy]}, "every": True, "cast": [],
                    "call": ["{player_name} pressed the switch. The roller coaster's path changed!"],
                    "then": "event:b2_coaster_switch_%d" % k})
        for on, route in enumerate(states):
            if route is None:
                continue
            a, b = _STOPS[route[0]], _STOPS[route[1]]
            cond = ["b2_coaster_sw%d" % k] if on else ["not:b2_coaster_sw%d" % k]
            for frm, to in ((a, b), (b, a)):
                out.append({"trigger": {"zone": [frm[0], frm[1], frm[0], frm[1]]}, "every": True, "condition": cond,
                            "cast": [{"you": [list(to), list(_OFF[to])], "zoom": 0.8}]})
    return out


NIMBASA_COASTER = nimbasa_room(585, {
    2: _COASTER_WOMAN,
    3: _say("Guide at the entrance", "To ride the roller coaster, step into a car. The switches on the platforms change "
                                    "where the cars go!", "Beat a Trainer and you can ride on in their car. Aim for the back!"),
    4: _say("Girl by the cars", "Elesa's amazing! Most Leaders remodel their Gym, but she built a whole new one!"),
    5: _say("Boy by the cars", "In other places, roller coasters are called jet coasters!"),
}, {}, extra_people=[(50, 41, _COASTER_COLETTE), (17, 15, _COASTER_ROLAN)], title="Shining Roller Coaster",
    scenes=_coaster_scenes())
# (Colette and Rolan stand by their cars at 49,38 and 16,13 in Black 2, out on the track: here a step onto their platforms.)
NIMBASA_COASTER["landings"] = [list(_OFF[s]) for s in _STOPS]   # (the platforms reached by the cars, for the map check)
# ---------------------------------------------------------------------------------------------- the park's Ferris wheel
# (11-23, closing 4a's "not done yet") Black 2's Rondez-View Ferris wheel: one trainer a season, by your character (a boy
# meets Persephone / June / Trisha / December, a girl Dirk / Augustin / Andy / January: text 673, their teams a/0/9/1).
# Walk up and they call out; the battle, then you ride together and they talk. A second visit: again, and a second ride.
# The park's person 1 (54, 15) is their spot (its code 162: Black 2's script picks the look). Our words throughout.
FERRIS = [   # (season, player, label, team id, sheet, [intro 1, ride 1, intro 2, ride 2])
    ("SPRING", "male", "Lass Persephone", 47, "b2_c15.png", [
        ["Lass Persephone: Ah... achoo! Spring! ...Hey! You were looking at me! When eyes meet, it's a battle!"],
        ["Persephone: Whaa! I lost?! Fine. Let's ride this rickety old Ferris wheel. First one scared loses!",
         "(The car creaks up into the sky...)", "Persephone: ...Stop looking at me! OK, OK, I'll let you go this time. Next time you're going down!"],
        ["Persephone: Achoo! You again?! Got a crush on me or something? You owe me a rematch!"],
        ["Persephone: Not again... Fine, you win. You're the Feral Liepard of Nimbasa now.",
         "(Round and round the Ferris wheel goes...)", "Persephone: Don't you dare tell anyone I lost! Someday I'll make you cry!"]]),
    ("SUMMER", "male", "Nursery Aide June", 803, "b2_c23.png", [
        ["Nursery Aide June: Phew, it's hot... Oh, are you lost? No? A battle, then? I'm better at caring for Pokemon than battling..."],
        ["June: Your Pokemon are so strong. I can tell you raise them with love.", "June: Let's spend a little longer together. Come on, ride with me!",
         "(The car rises over the park...)", "June: Some Trainers blame us when their Pokemon get a scratch. You're different. Thank you."],
        ["June: Hi again! Do you have time? Let's play a little first. My Pokemon's in great shape today!"],
        ["June: That was fun! I'd love to just play like this and quit my job...", "(The Ferris wheel turns slowly...)",
         "June: Summer's not the best time for this ride, is it? Working with kids is messy, but I love it."]]),
    ("AUTUMN", "male", "Clerk Trisha", 10, "b2_c53.png", [
        ["Clerk Trisha: The wind's turned cold... Oh! Do you want to battle, perhaps?"],
        ["Trisha: That was over in an instant. I'm not very good. Have you ridden this Ferris wheel? Come ride with me!",
         "(The car climbs into the autumn sky...)", "Trisha: I'll be a mum soon. The doctor says to rest, but today I relaxed enough for two. Thanks!"],
        ["Trisha: Why hello again! Shall we battle? Gently, please!"],
        ["Trisha: I can't keep up! Stay a little longer with me.", "(Round goes the wheel...)",
         "Trisha: I hope my child grows up kind, like you. See you again!"]]),
    ("WINTER", "male", "Beauty December", 804, "b2_c303.png", [
        ["Beauty December: Who are you? Did they send a kid to take me back to the manor? Fine! Battle me!"],
        ["December: You just wanted to battle? Then let's ride the Ferris wheel. Hurry!", "(The car sways in the winter wind...)",
         "December: I'm being chased by a certain organization... You don't have to believe me. Let's hope we meet again."],
        ["December: You again? Help me out: they're getting tougher. Battle me!"],
        ["December: You're as good as ever. Come, let's ride. Even they can't reach us up there.", "(The wheel turns...)",
         "December: World peace is kept by something very simple. It's best you don't know more than that."]]),
    ("SPRING", "female", "Dancer Dirk", 138, "b2_c55.png", [
        ["Dancer Dirk: Yawn... A fan of mine? It's my first day off in ages... Well, I guess one battle!"],
        ["Dirk: You rocked the house! Dirk and the Darumaka still have work to do. Let's ride the Ferris wheel!",
         "(The car rises over Nimbasa...)", "Dirk: This just reminds me of a good memory. Thanks for my day off!"],
        ["Dirk: Hey! I have a show later, but I thought you might come by. Battle me first?"],
        ["Dirk: You're tough! Are you aiming to be Champion? ...Let's ride! The view's so mellow.", "(The wheel turns slowly...)",
         "Dirk: Two years ago I had a friend here I could never beat. That's why I started my dance team."]]),
    ("SUMMER", "female", "Clerk Augustin", 805, "b2_c52.png", [
        ["Clerk Augustin: It's sooo hot! A battle or a ride? I don't mind either, but I'm not very tough."],
        ["Augustin: See? Not very good. Work keeps me busy. As thanks, let me treat you to a ride.",
         "(The car creaks upward...)", "Augustin: My company runs this old wheel. It's worn out, and they plan to tear it down someday."],
        ["Augustin: Hey! I was waiting for you. Battle me again, then ride with me? You need two people to ride."],
        ["Augustin: I thought I might lose. That's OK. Shall we ride?", "(The wheel turns...)",
         "Augustin: My parents had their first date on this wheel. If not for it, I wouldn't exist..."]]),
    ("AUTUMN", "female", "Hiker Andy", 136, "b2_c64.png", [
        ["Hiker Andy: My heart falls with every leaf... What, a battle? I accept. Let's get this over with."],
        ["Andy: Every battle reminds me of that summer... Will you listen? Come here with me.",
         "(The car rises into the autumn air...)", "Andy: Sniff... Excuse me. I want to be alone for a moment."],
        ["Andy: Oh... it's you. My heart's still waiting for rescue. Could you spare a moment? A battle first..."],
        ["Andy: I can't concentrate! Why can't I forget that summer? Stay with me a little longer...", "(The wheel turns...)",
         "Andy: Love and breakups are hard. But tell people how you feel. Don't let fear win."]]),
    ("WINTER", "female", "Guitarist January", 806, "b2_c295.png", [
        ["Guitarist January: You! Cold-looking clothes in the middle of winter? That's rock 'n' roll! Let's prove who rocks hardest!"],
        ["January: Way to rock! For that funky battle I'll sing you a song, but not here. Roll on over this way!",
         "(The car sways as she strums...)", "January: A country tune about a lost love. That's it for today. I'll be playing streets all over!"],
        ["January: Hey! It's... no. Excuse me. Would you battle me?"],
        ["January: I knew you rocked. Please listen to my song again!", "(The wheel turns to the music...)",
         "January: I got scouted, but they want me to sing sweet pop and speak politely. Maybe I'll change... Thanks for listening."]]),
]


def _ferris(season, who, label, tid, sheet, words):
    """One trainer's two visits: stages (a battle each), their scenes (they call out, then the ride)."""
    k = "b2_ferris_" + label.split()[-1].lower()
    cond = ["season:" + season, "world:unova_story:%s_player" % who]
    opt = {"text": label, "action": "EVENT", "_look": "sheet:" + sheet, "condition": cond, "event": {
        "stages": [{"flag": k + "_1", "lines": words[0], "battle": _b2(tid, dialogue={"player_won": [words[1][0]]})},
                   {"flag": k + "_2", "requires": [k + "_1", "world:unova_story:not_today:" + k + "_1"], "lines": words[2],
                    "battle": _b2(tid, dialogue={"player_won": [words[3][0]]})}],
        "done": ["Thanks for riding with me!"]}}
    scenes = [{"who": label, "trigger": {"zone": [52, 16, 56, 17]}, "condition": cond + ["not:" + k + "_1"], "flag": k + "_seen1",
               "approach": True, "then": "talk", "after_lines": words[1][1:]},
              {"who": label, "trigger": {"zone": [52, 16, 56, 17]},
               "condition": cond + [k + "_1", "world:unova_story:not_today:" + k + "_1", "not:" + k + "_2"],
               "flag": k + "_seen2", "approach": True, "then": "talk", "after_lines": words[3][1:]}]
    return opt, scenes


FERRIS_PEOPLE, FERRIS_SCENES = [], []
for _f in FERRIS:
    _o, _s = _ferris(*_f)
    FERRIS_PEOPLE.append(_o)
    FERRIS_SCENES += _s
# the Dropped Item (park person 11, 23, 23): a lost Xtransceiver; it rings, and "???" asks you to keep it till they can come.
# The owner (Yancy for a boy, Curtis for a girl) meets you at the Ferris wheel after the Champion: post-game batch.
DROPPED_ITEM = {"text": "Something dropped", "action": "EVENT", "flag_condition": "not b2_dropped_item", "_look": "sheet:b2_item_ball.png",
                "no_tag": True, "event": {"scene": "xtransceiver", "caller": "???", "flag": "b2_dropped_item", "call": [
                    "(Someone's dropped an Xtransceiver here... and it's ringing! You pick it up.)",
                    "???: Hello? Oh! You found my Xtransceiver? Thank goodness!",
                    "???: I'm so sorry, I'm swamped at work and can't come for it. Could you hold on to it for me?",
                    "???: I'll call you on it now and then. ...Thank you! Talk soon!"]}}

NIMBASA_PARK = nimbasa_room(64, {
    0: _ball("Poke Ball by the rides", "PARALYZE_HEAL", "b2_park_parlyz", name="a Paralyze Heal"),
    1: FERRIS_PEOPLE,
    11: DROPPED_ITEM,
    12: [_say("Gym guide outside", "Oh, are you a challenger? I'm sorry, the Gym Leader is out right now...",
              "She should be in the roller coaster building by the park's entrance.", condition=["not:b2_elesa_coaster"])],
    2: _say("Woman by the Gym", "It's a shining, sparkling, bright fashion show!"),
    3: _say("Boy by the rides", "I hear a Clown's make-up has a teardrop mark."),
    4: _say("Girl by the rides", "A roller coaster and a Ferris wheel! Which should I ride first?!"),
    5: _say("Boy on a date", "Ah ah ah! Wh-what do I talk about on my first date..."),
    6: _say("Girl on a date", "Even at the amusement park, he just plays guitar... He loves music from the bottom of his heart!"),
    7: _say("Boy by the bench", "What's that? Uh, I dunno. Audino?"),
    8: _say("Woman by the bench", "A famous TV star filmed here! Between takes the star was on the Xtransceiver the whole time!"),
    9: _say("Audino", "Audino: Chuuu!"),
    10: _say("Clown", "Uuugh!"),
    13: _say("Girl by the coaster", "The best part of a roller coaster is screaming your heart out!"),
}, {1: ["NIMBASA CITY POKEMON GYM", "Leader: Elesa", "The Shining Beauty"],
    2: ["THE SHINING ROLLER COASTER", "Former Nimbasa City Pokemon Gym"]},
    hidden={"44,11": "REVIVE"}, title="Amusement Park",
    scenes=FERRIS_SCENES + [{"who": "Gym guide outside", "trigger": {"zone": [70, 11, 72, 13]}, "condition": ["not:b2_nimbasa_gym_out"],
             "flag": "b2_nimbasa_gym_out", "approach": True,
             "lines": ["Oh, are you a challenger? I'm sorry, the Gym Leader is out right now...",
                       "She should be in the roller coaster building by the park's entrance."]},
            {"who": "Gym guide outside", "trigger": {"zone": [70, 10, 72, 11]}, "condition": ["not:b2_elesa_coaster"], "every": True,
             "lines": ["The Gym Leader is out right now. Try the roller coaster building!"], "push": [0, 1]}])
NIMBASA_PARK["rooms_note"] = "the park is a separate map (zone 64), as Castelia's streets"

# ------------------------------------------------------------------------------------------ Gear Station, the Battle Subway
# (batch 4b, 11-23; Jordan: "all lines", "Lv 50, as Black 2", "walk into the car"). Zone 66 is the round hall: eight stairways
# down to the lines' platforms (67-74, in the file's own order of text 76: Single, Double, Multi, Wi-Fi, Super Single, Super
# Double, Super Multi, Anville), its way out up the stairs (16, 37) to Nimbasa. On each platform the Depot Agent (n0, script
# 10333) boards you; the train is the car room (75): the next Trainer walks in from the next car (a scene for each walking
# look: Black 2's own class -> overworld table, overlay 12), and the battle follows. After seven, the line's end station (76).
# All of it runs in src/world/battle_subway.py from assets/b2_subway.json (dev/builders/unova_subway.py). The Wi-Fi Train is
# a link feature: its platform says so. The Brown Line (74) runs to Anville Town.
_SUBWAY_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "b2_subway.json")
SUBWAY = json.load(open(_SUBWAY_JSON, encoding="utf-8"))
SUBWAY_LINES = {67: "single", 68: "double", 69: "multi", 71: "super_single", 72: "super_double", 73: "super_multi"}
_LINE_NAME = {"single": "Single Train", "double": "Double Train", "multi": "Multi Train", "super_single": "Super Single Train",
              "super_double": "Super Double Train", "super_multi": "Super Multi Train"}


# The Brown Line's ride (11-23, closing 4b): the train cut from Black 2's own Anville picture (dev/builders/unova_trains.py),
# pulling out of Gear Station's platform and into Anville's station, and back. Tiles of 16 pixels on half-size pictures.
_R = "tiles/unova_rides/"
BROWN_LINE_OUT = {"legs": [
    {"picture": _R + "platform.png", "sprite": _R + "train_h.png", "from": [21, 11], "to": [42, 11], "camera": [24, 9], "frames": 150},
    {"picture": _R + "anville.png", "sprite": _R + "train_v.png", "from": [24.5, 82], "to": [24.5, 63], "frames": 170}]}
BROWN_LINE_BACK = {"legs": [
    {"picture": _R + "anville.png", "sprite": _R + "train_v.png", "from": [24.5, 63], "to": [24.5, 82], "frames": 150},
    {"picture": _R + "platform.png", "sprite": _R + "train_h.png", "from": [42, 11], "to": [21, 11], "camera": [24, 9], "frames": 170}]}


def _platform(z):
    line = SUBWAY_LINES.get(z)
    if line:
        agent = {"text": "Depot Agent", "action": "EVENT", "event": {"world": "battle_subway", "board": line}}
        title = "Platform: " + _LINE_NAME[line]
    elif z == 70:
        agent = _say("Depot Agent", "This is the platform for Wi-Fi Trains. They run on link play with Trainers far away.",
                     "That train isn't running here. The other lines are all open!")
        title = "Platform: Wi-Fi Train"
    else:   # (the Brown Line: no battles, the local train out to Anville Town)
        agent = {"text": "Depot Agent", "action": "EVENT", "event": {
            "lines": ["Depot Agent: This is the platform for the train to Anville Town. It's a local train: no battles aboard!",
                      "All aboard! ...The train rattles out of Nimbasa and across the countryside, all the way to Anville Town."],
            "travel": "ANVILLE_TOWN", "land": [None, 21, 52], "ride": BROWN_LINE_OUT}}
        title = "Platform: Anville Town"
    ppl = {0: agent, 1: _say("Rail fan", "I come to watch the trains leave. Each line's car is different!"),
           2: _say("Rail fan's friend", "Seven Trainers ride each train. Beat them all and the line goes on and on!")}
    if z == 74:
        ppl = {0: agent, 1: _say("Rail fan", "The Brown Line doesn't battle. It's a quiet local train out to Anville Town.")}
    m = nimbasa_room(z, ppl, {(6, 15): ["It's a subway map of the Unova region.", "Eight lines run from Gear Station."]},
                     title=title)
    m["barred"] = PLATFORM_TRAIN
    return m


# (the train waiting on a platform's track: Black 2's own car, cut into tiles by dev/builders/unova_trains.py)
_TRAIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "dungeon", "characters", "b2_train")
PLATFORM_TRAIN = [{"tiles": [[13 + int(f.split("_c")[1][:-4]), 8 + int(f[1:f.index("_")])]], "look": "img:b2_train/" + f,
                   "lines": ["The train waits at the platform, its doors open."]}
                  for f in sorted(os.listdir(_TRAIN_DIR)) if f.endswith(".png")]


def _car_scenes():
    """The car: whoever's next walks in from the next car's door and challenges you (one scene per walking look)."""
    looks = sorted({t["walk"] for t in SUBWAY["trainers"].values() if t.get("walk")} | {"b2_c207.png", "b2_c107.png"})
    return [{"trigger": "enter", "every": True, "condition": ["world:battle_subway:foe:" + w],
             "cast": [{"sheet": w, "from": [15, 4], "to": "player", "lines": ["(The door to the next car slides open...)"],
                       "then": "event:b2_subway_fight", "stay": True}]} for w in looks]


GEAR = nimbasa_room(66, {
    0: _say("Man by the map", "You can take the Battle Subway from Gear Station!"),
    1: _say("Depot Agent", "The Battle Subway is where Trainers come to see who's strongest!"),
    2: {"text": "Depot Agent by the stairs", "action": "EVENT",
        "event": {"lines": ["The Battle Subway has seven lines in all! At first you can ride the Single, Double and Multi Trains.",
                            "Beat a Subway Boss and that line's Super train opens. Those Trainers are really tough!"]}},
    3: _say("Interviewer", "Hi, hi! I'm asking Trainers what they say before a battle, and how they feel when they win!",
            "...You'd rather keep it a secret? That's fine! Good luck on the Subway!"),
    4: _say("Ace Trainer", "I lost on the 20th Trainer again... One more and I'd have met the Subway Boss!"),
}, {}, extra_people=[(12, 28, {"text": "Exchange: items", "action": "BP_SHOP", "shop": "b2w2_items", "color": "GOLD"}),
                     (21, 28, {"text": "Exchange: TMs", "action": "BP_SHOP", "shop": "b2w2_tms", "color": "GOLD"})],
    title="Gear Station")
for _x in range(14, 18):   # (the stairs up to Nimbasa: the file's warp 8 goes "back where you came from")
    GEAR["art"][37] = GEAR["art"][37][:_x] + "z" + GEAR["art"][37][_x + 1:]
GEAR["exits"]["z"] = "ROOM:MAIN"   # (a letter of its own: nimbasa_room gives "v", "^"... to the platforms' stairways)
CAR = nimbasa_room(75, {}, {}, scenes=_car_scenes(), title="Battle Subway train")   # (empty, as Black 2: each Trainer walks in)
SUBWAY_STOP = nimbasa_room(76, {
    0: {"text": "Depot Agent", "action": "EVENT", "event": {"world": "battle_subway", "stop": True}},
    1: {"text": "Depot Agent ", "action": "EVENT", "event": {"world": "battle_subway", "stop": True}},
    2: _say("Trainer resting", "I'm taking a little rest here. These Trainers are tough!",
            "I wonder how far I'll get with my skills."),
}, {}, title="Battle Subway station")
CAR["landings"] = [[8, 4]]              # (no door: the train's own ride puts you aboard and takes you off: battle_subway.py CAR)
SUBWAY_STOP["landings"] = [[20, 12]]    # (the lines' end: off the train here, battle_subway.py STOP_AT)
SUBWAY_ROOMS = {"gear": GEAR, "car": CAR, "subway_stop": SUBWAY_STOP}
SUBWAY_ROOMS.update({NIMBASA_ROOMS[z]: _platform(z) for z in range(67, 75)})

# -------------------------------------------------------------------------------------------------------------- Anville Town
# (batch 4b, 11-23) Zone 418 (a map of its own, matrix 128), its houses 419-421. Reached only by the Brown Line from Gear
# Station (the platform's Depot Agent; here the station's agent, n2, takes you back). Black 2's people by their own n:
# the girl who lost her Pansage (it rode the wrong train: the Depot Agent outside Nimbasa's Musical Theater has it), the
# Worker on the bridge (the turntable's car of the day: src/world/anville.py), the weekend crowd and its three traders
# (Saturday / Sunday, not on the Hyperspeed Train's days), the flautist, and the lost-and-found Depot Agent's house (421).
OUTSIDE.update({419: 418, 420: 418, 421: 418})
NIMBASA_PANSAGE = {"text": "Depot Agent by the theater", "action": "EVENT", "condition": ["not:b2_pansage_back"], "event": {
    "stages": [{"flag": "b2_pansage_back", "requires": ["b2_pansage_asked"],
                "lines": ["Depot Agent: This Pansage got off a train all on its own. It keeps looking towards the Brown Line...",
                          "A girl in Anville Town lost her Pansage? Then this must be it! Please take it home to her!",
                          "(You take the Pansage with you, to bring it back to Anville Town.)"]}],
    "then": {"lines": ["Depot Agent: A Pansage got off a train here all by itself. I wonder who it belongs to..."]}}}
_WEEKEND = ["world:anville:weekend"]
ANVILLE_PEOPLE = {
    0: {"text": "Girl on the platform", "action": "EVENT", "event": {"stages": [
        {"flag": "b2_pansage_asked", "lines": ["Oh, Pansage... where could you be?",
                                                "We went to the amusement park in Nimbasa and saw a musical. But on the way home, "
                                                "Pansage got on a different train!", "I wonder where it is now..."]},
        {"flag": "b2_pansage_reward", "requires": ["b2_pansage_back"],
         "lines": ["Oh! Pansage! You found it! Thank you so, so much. This isn't much, but please take it."],
         "gift_item": {"BRIGHT_POWDER": 1}}],
        "then": {"lines": ["My silly Pansage... A man with green hair told me Pansage's dream is to be a railroad conductor!",
                           "But... can he really talk with Pokemon?"]}}},
    15: _say("Pansage", "Pansage: Ook!", condition=["b2_pansage_reward"]),
    1: {"text": "Worker on the bridge", "action": "EVENT", "event": {"world": "anville", "turntable": True,
                                                                     "lines": ["Oh, are you curious about that train too?"]}},
    2: {"text": "Depot Agent", "action": "EVENT", "event": {
        "lines": ["Depot Agent: A train to Nimbasa City is leaving shortly. All aboard!",
                  "...The train rolls back across the plains and into Gear Station."],
        "travel": "NIMBASA_CITY", "land": ["plat_anville", 11, 14], "ride": BROWN_LINE_BACK}},
    3: _say("Rich Boy", "This is a quiet town! Relax and stay for a while."),
    4: {"text": "Traveller with a pack", "action": "EVENT", "condition": _WEEKEND, "event": {
        "world": "anville", "trade": "REVIVE", "lines": ["Ah... I'm in trouble. I got so caught up in my trip, I ran out of Escape Ropes."]}},
    5: {"text": "Collector", "action": "EVENT", "condition": _WEEKEND + ["world:anville:item:PP_UP"], "event": {
        "world": "anville", "trade": "PP_UP", "lines": ["I collect Star Pieces! You, over there! Let's do business."]}},
    6: {"text": "Lady by the tracks", "action": "EVENT", "condition": _WEEKEND, "event": {
        "world": "anville", "trade": "FULL_RESTORE", "lines": ["With that face, I bet you have something I want. Poke Balls!"]}},
    7: _say("Depot Agent on the bridge", "A lot of train cars come to rest here.", "If there are lots of people, I feel like the trains are happy!"),
    8: _say("Hiker", "It's so lively on weekends! Me? I came to watch the trains.", condition=_WEEKEND),
    9: _say("Woman", "You can trade all sorts of items here. It was surprisingly fun when I tried!", condition=_WEEKEND),
    10: _say("Man with a camera", "I wanted a picture from exactly this angle!", condition=_WEEKEND),
    11: _say("Boy by the fence", "The thing that turns the trains round is called a turntable!"),
    12: _say("Little boy", "Trains are so cooool! My mom brought me, but now she's off taking pictures somewhere.", condition=_WEEKEND),
    13: _say("Man", "On weekends, loads of people come to watch the trains. Do you trade items too?", condition=_WEEKEND),
    14: _say("Girl", "If there are lots of people, I think the trains are happy!", condition=_WEEKEND),
    16: _say("Flautist", "(A beautiful tune is spreading throughout the town...)"),
}
ANVILLE_SIGNS = {(20, 47): ["ANVILLE TOWN", "Rolling Out the Steel Rails"], (33, 37): ["It's a subway map of the Unova region."]}
ANVILLE = town(
    418, ANVILLE_PEOPLE, ANVILLE_SIGNS, {419: ("house", "house_n"), 420: ("house", "house_w"), 421: ("house", "lost_found")},
    rooms={
        "house_n": room(419, {0: _say("Woman by the window", "Maybe it's the design... trains run so fast and still feel so comfortable.",
                                      "Every part working together. Simple, but so beautiful!"),
                              1: _say("Man at the table", "Isn't it amazing? Just riding a train, you can see so many kinds of scenery."),
                              2: _say("Nursery Aide", "Everyone in this town loves trains!")},
                        {}, (40, 37)),
        "house_w": room(420, {0: _say("Man by the shelf", "On weekends, item collectors gather here. They'll trade you for different items."),
                              1: _say("Boy", "Everyone sure loves trains!"),
                              2: _say("Old man", "One day I'll take the Subway Bosses Ingo and Emmet down!")},
                        {}, (35, 47)),
        "lost_found": room(421, {0: {"text": "Depot Agent", "action": "EVENT", "event": {"world": "anville", "lost_found": True}}},
                           {}, (44, 47)),
    },
    title="Anville Town")
ANVILLE["landings"] = [[21, 52]]   # (the station: in and out by the Brown Line only)


# ---------------------------------------------------------------------------- batch 4c: Big Stadium and Small Court
# (11-24, Jordan's batch 4 call "as Black 2") Each lobby's warp panel (9, 8) leads onto the day's field (src/world/
# nimbasa_sports.py: the sport by weekday, the game hours by the real clock); each field's panel leads back. Both are
# step-on scenes, as Black 2 picks the field by the day: the fields have no fixed door to a lobby. During a game the
# ushers stand before the panel and the stands fill with cheering fans; in practice the athletes battle once a day,
# their teams by your badges, and after the League three visitors a day stand on one arena's field (b2_sports.json,
# dev/builders/unova_sports.py). Black 2's people flags: 655 = shown during a game, 666 = shown in practice.
_SPORTS = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "assets", "b2_sports.json"), encoding="utf-8"))


def _sp(arena, sport):
    return "world:nimbasa_sports:sport:%s:%s" % (arena, sport)


def _game(arena):
    return "world:nimbasa_sports:game:" + arena


def _practice(arena):
    return "world:nimbasa_sports:open:" + arena


def _pad_scene(xy, ev_key):
    return {"trigger": {"zone": [xy[0], xy[1], xy[0], xy[1]]}, "every": True, "cast": [],
            "call": ["(The warp panel hums...)"], "then": "event:" + ev_key}


_BIG = ("football", "baseball", "soccer")
_SMALL = ("tennis", "basketball")
_STADIUM_ATHLETE_LOOK = {"football": "b2_c59.png", "baseball": "b2_c57.png", "soccer": "b2_c58.png"}
_COURT_ATHLETE_LOOK = {"tennis": "b2_c60.png", "basketball": "b2_c133.png"}
_PLAYER = {"football": "Football player", "baseball": "Infielder", "soccer": "Striker", "tennis": "Smasher",
           "basketball": "Hoopster"}
_COPY = {"football": "a quarterback's throw", "baseball": "a pitcher's throw", "soccer": "a goalkeeper's throw"}
STADIUM = nimbasa_room(79, {
    0: [_say("Receptionist", "There's a %s game on in Big Stadium right now!" % s, condition=[_sp("stadium", s), _game("stadium")])
        for s in _BIG] + [_say("Receptionist", "The %s players are practising in Big Stadium now. You can go and watch!" % s,
                               "Step on the warp panel to go out onto the field.", condition=[_sp("stadium", s), _practice("stadium")])
                          for s in _BIG],
    1: _say("Boy in the lobby", "Kids really look up to athletes, you know."),
    3: _say("Man in the lobby", "I raise the same Pokemon as my favourite athlete!"),
    4: [_say("Kid by the panel", "When I throw a Poke Ball, I copy %s!" % _COPY[s], condition=[_sp("stadium", s), _practice("stadium")])
        for s in _BIG],
    2: [_say("%s with a sore hand" % _PLAYER[s], "Ha ha! I'm a %s! I hurt my hand, so no autographs today. Sorry!"
             % _PLAYER[s].lower().replace("football player", "football player"),
             "What does the signature on your Trainer Card look like?", _look="sheet:" + _STADIUM_ATHLETE_LOOK[s],
             condition=[_sp("stadium", s), _practice("stadium")]) for s in _BIG],
    5: _say("Usher", "I'm sorry. You can't go onto the field while a game is on.", condition=[_game("stadium")]),
    6: _say("Usher ", "I'm sorry. You can't go onto the field while a game is on.", condition=[_game("stadium")]),
    7: _say("Usher  ", "I'm sorry. You can't go onto the field while a game is on.", condition=[_game("stadium")]),
}, {}, title="Big Stadium", scenes=[dict(_pad_scene((9, 8), "b2_field_stadium"), condition=[_practice("stadium")])])
STADIUM_STANDS = nimbasa_room(80, {
    0: _say("Woman in the stands", "Athletes look so cool in the middle of a game!"),
    2: _say("Man in the stands", "You can tell how good these players are just from watching them practise."),
    3: _say("Girl in the stands", "On the field they play for real!"),
    7: _say("Boy in the stands", "I want to be good at sports AND Pokemon battles!", condition=[_game("stadium")]),
    1: _say("Fan in the stands", "One ball can make people and Pokemon smile. Sports are wonderful!", condition=[_game("stadium")]),
    5: _say("Cheering fan", "Eeee! Look this waaay!", condition=[_game("stadium")]),
    4: _say("Cheering fan ", "There! Turn like that!", condition=[_game("stadium")]),
    6: _say("Dizzy fan", "Watching the ball go left and right makes me woozy...", condition=[_game("stadium")]),
}, {}, title="Big Stadium Stands")
COURT = nimbasa_room(84, {
    7: [_say("Receptionist ", "There's a %s match on in Small Court right now!" % s, condition=[_sp("court", s), _game("court")])
        for s in _SMALL] + [_say("Receptionist ", "The %s players are practising in Small Court now. Come and watch!" % s,
                                 "Step on the warp panel to go out onto the court.", condition=[_sp("court", s), _practice("court")])
                            for s in _SMALL],
    0: _say("Fan by the court", "We love sports. Games are great, but we enjoy watching practices too!", condition=[_practice("court")]),
    1: _say("Fan  by the court", "New kinds of basketball and tennis, made by people and Pokemon together!", condition=[_practice("court")]),
    2: _say("Man by the wall", "Talk to the athletes during a practice, and they might challenge you to a battle!"),
    3: [_say("%s by the panel" % _PLAYER[s], "The top %ss are waiting on the court with their Pokemon!" % _PLAYER[s].lower(),
             _look="sheet:" + _COURT_ATHLETE_LOOK[s], condition=[_sp("court", s), _practice("court")]) for s in _SMALL],
    4: _say("Usher   ", "I'm sorry. You can't go onto the court while a game is on.", condition=[_game("court")]),
    5: _say("Usher    ", "I'm sorry. You can't go onto the court while a game is on.", condition=[_game("court")]),
    6: _say("Usher     ", "I'm sorry. You can't go onto the court while a game is on.", condition=[_game("court")]),
}, {}, title="Small Court", scenes=[dict(_pad_scene((9, 8), "b2_field_court"), condition=[_practice("court")])])
COURT_STANDS = nimbasa_room(85, {
    2: _say("Man at the back", "I watch them practise quietly. I trust the athletes!"),
    7: _say("Kid in the stands", "Wooow! Someday I want to play on that court!"),
    0: _say("Fan  in the stands", "We love watching games, and practices too!", condition=[_game("court")]),
    1: _say("Fan   in the stands", "New styles of sport, made by people and Pokemon... Maybe they're the future!", condition=[_game("court")]),
    3: _say("Coach in the stands", "Hey! There! No! No, no! Yes, yes! That's it! Why don't they listen to me?!", condition=[_game("court")]),
    4: _say("Player in the stands", "Hmm-hmm! I'll copy that play in my next game.", condition=[_game("court")]),
    5: _say("Muscle fan", "Did you see that? What a muscle move! Good hustle!", condition=[_game("court")]),
    6: _say("Excited fan", "This could be the game of a lifetime! I might see history made!", condition=[_game("court")]),
}, {}, title="Small Court Stands")

# The fields: the athletes (Black 2's own, by tier), the spare spots for the post-game visitors, the other players and
# their Pokemon (lines in our words, after the zones' text 91-97). Each field's warp panel leads back to its lobby.
_FIELD_TALK = {
    81: {15: ("Coach on the field", "Players who score and players who help them... Picking the roles is the key to a team!"),
         16: ("Football player", "Football's a fun sport. It's split into offence and defence."),
         14: ("Football player ", "Those eyes... It's like he's charging straight at me!"),
         13: ("Football player  ", "The helmet and pads weigh about 15 pounds!"),
         12: ("Football player   ", "I built these muscles tackling Pokemon! Nothing can move me!"),
         11: ("Football player    ", "OK! I'll defend to the end with moves like Protect and Detect!"),
         17: ("Football player     ", "My favourite moves? Hmm... Tackle and Take Down!"),
         18: ("Football player      ", "Reading the other side's attack and picking your next move... Battles and football share that thrill!"),
         19: ("Football player       ", "Why is football fun? First, just watch a game without worrying about the rules!"),
         20: ("Football player        ", "I'll guard my team with my whole body!"),
         22: ("Quarterback", "In football the quarterback picks the plan and carries it out. Kind of like a Pokemon Trainer!"),
         21: ("Football player         ", "You have to learn every single formation by heart!"),
         9: ("Football player at the end", "The ball's oval and hard to throw. But once you get the hang of it, it flies!"),
         8: ("Secret weapon", "I'm the team's secret weapon! So secret I've never played in a game..."),
         10: ("Football player running", "Yoo-hoo! Pass me the ball!"),
         28: ("Owner on the field", "Bodies crashing into bodies! Go, go, go! I'm the team's owner. That's what I like to see!"),
         29: ("Pansage", "Pansage: Ook!"), 30: ("Pansear", "Pansear: Ookiii!"), 31: ("Panpour", "Panpour: Ook! Ook!")},
    82: {13: ("Infielder", "To get good at something, you do it again, day after day after day."),
         12: ("Infielder ", "When I was a kid, I played catch with my Pokemon!"),
         7: ("Infielder  ", "Growing up isn't bad. Forgetting how it felt to be a kid is."),
         8: ("Infielder   ", "I've got baseball and I've got Pokemon. How lucky am I!"),
         9: ("Infielder    ", "If you never swing, you never hit. You won't fail... but you won't win either."),
         10: ("Infielder     ", "I give it everything, every time. That's all I know how to do!"),
         16: ("Infielder      ", "What I'm proudest of? My bat!"),
         17: ("Herdier", "Herdier: Bwoof!")},
    83: {0: None},
    86: {8: ("Smasher", "Pokemon tennis is wonderful! You're never alone out there: your Pokemon is always with you!"),
         9: ("Smasher ", "Tennis is rackets and balls. Nothing deep about it."),
         10: ("Ball boy", "I'm a ball boy who collects tennis balls. You're a Trainer who collects Pokemon!"),
         11: ("Ball boy ", "To be ball boys, we have to practise!"),
         14: ("Lillipup", "Lillipup: Woowoof!"), 15: ("Lillipup ", "Lillipup: Yap!")},
    87: {8: ("Hoopster", "A game can end in the blink of an eye. What matters is how hard you prepare!"),
         9: ("Hoopster ", "I'm not playing basketball because I'm tall. Maybe I grew tall because I wanted to play so much!"),
         12: ("Scraggy", "Scraggy: Aaagy!")},
}
_FIELD_TALK[83] = {
    0: ("Goalkeeper", "Everyone makes mistakes. But a keeper can't, because a keeper can't score to make up for it.",
        "With Pokemon, the others on your team and their Trainer can cover for you!"),
    1: ("Striker", "A Striker and a teammate understand each other with one look. Same as a Pokemon and its Trainer!"),
    2: ("Striker ", "Really strong Trainers do everything they can, every time!"),
    3: ("Striker  ", "Soccer is beautiful and fun! So are Pokemon!"),
    4: ("Striker   ", "Pokemon soccer... Poccer? No? Hmm, I'll keep thinking."),
    5: ("Striker    ", "Pass the ball to a teammate, then move fast to get it back!"),
    21: ("Striker running", "Run! Run! Just think about running!"),
    24: ("Patrat", "Patrat: Squeeskwaa!"), 25: ("Patrat ", "Patrat: Meep!")}


def _field_room(z):
    f = _SPORTS["fields"][str(z)]
    arena, sport = f["arena"], f["sport"]
    people = {}
    for a in f["athletes"]:
        key = a["key"]
        people[a["n"]] = {"text": key + ("" if not a["second"] else " "), "action": "EVENT",
                          "condition": ["world:nimbasa_sports:athlete:" + key],
                          "event": {"world": "nimbasa_sports", "athlete": key}}
    pad = None
    geo = GEO[str(z)]
    for p in geo["people"]:
        if p["code"] in (163, 164, 165):   # (Black 2's spare spots: the script dresses them as the day's visitors)
            slot = p["code"] - 163
            people[p["n"]] = [{"text": v["battle"]["name"] + " " * (1 + list(FIELD_NAMES).index(z)), "action": "EVENT",
                               "_look": "sheet:" + v["walk"],
                               "condition": ["world:nimbasa_sports:visitor:%s:%d:%d" % (arena, slot, v["id"])],
                               "event": {"world": "nimbasa_sports", "visitor": v["id"]}}
                              for v in _SPORTS["visitors"] if v["slot"] == slot]
    for n, said in _FIELD_TALK.get(z, {}).items():
        if said:
            people[n] = _say(said[0], *said[1:])
    m = nimbasa_room(z, people, {}, title=FIELD_NAMES[z])
    for d in geo["doors"]:   # (its warp panel: a step-on scene back to the lobby, not a door)
        pad = (d["x"], d["y"])
    ch = m["art"][pad[1]][pad[0]]
    m["art"][pad[1]] = m["art"][pad[1]][:pad[0]] + "." + m["art"][pad[1]][pad[0] + 1:]
    m["exits"].pop(ch, None)
    m["scenes"] = [_pad_scene(pad, "b2_field_leave_" + arena)]
    m["landings"] = [[pad[0], pad[1] - 1]]   # (reached by the lobby's panel: nimbasa_sports puts you here)
    return m


FIELD_NAMES = {81: "Big Stadium: Football", 82: "Big Stadium: Baseball", 83: "Big Stadium: Soccer",
               86: "Small Court: Tennis", 87: "Small Court: Basketball"}
FIELD_ROOMS = {"field_football": _field_room(81), "field_baseball": _field_room(82), "field_soccer": _field_room(83),
               "court_tennis": _field_room(86), "court_basketball": _field_room(87)}

# ------------------------------------------------------------------------------------- batch 4c: the Musical Theater
# (11-24, Jordan: "a simple show game"; Dress Up snaps each Prop to its spot, the show asks math for the spotlight, the
# fans come about 20 shows sooner than Black 2's 120, the Toy Cake after the first show: unova_check/DECISIONS.md)
# Zone 77: the owner greets you on your first visit and hands over the Prop Case a superstar left behind two years ago
# (zone 606's lines: its props are the Top Hat, Blue Barrettes, Square Glasses, Maraca, Umber Belt and Tie). The middle
# receptionist starts a Musical (src/states/musical.py); after a show your fans wait in the lobby, each with a Prop
# (Black 2's ten fan spots, flags 622-626 / 661-665). src/world/musical.py keeps the Prop Case and the counts.
_FANS = [1, 4, 5, 2, 3, 18, 17, 19, 20, 21]   # (the file's fan spots in the order they fill)
MUSICAL = nimbasa_room(77, dict({
    0: {"text": "Musical receptionist", "action": "EVENT", "event": {"world": "musical", "join": True}},
    15: _say("Receptionist at the photos", "You can hang the photo from a Musical on the wall behind me!",
             "The photo up there now is from the last show."),
    16: _say("Receptionist for link shows", "This counter is for Musicals with friends far away.",
             "It runs on link play, so it isn't open here. The middle counter's shows are always open!"),
    11: {"text": "Theater owner", "action": "EVENT", "event": {"world": "musical", "owner": True}},
    7: {"text": "Rival stylist", "action": "EVENT", "event": {"world": "musical", "rival": True}},
    8: _say("Maid in the lobby", "In Dress Up, matching the show is everything!",
            "Match it well and the audience falls for you. If you're going on stage, you have to stand out!"),
    6: _say("Socialite in the lobby", "Every Prop has its own image: cool, cute, elegant or quirky.",
            "Think about the look you want before you play Dress Up."),
    14: _say("Gentleman by the stairs", "I'm not bragging, but we're rather rich. And rich people love the Musical!",
             "Even for a man like me, the Pokemon Musical is the best entertainment there is!"),
    12: _say("Little girl in the theater", "When there are cute Pokemon on stage, I can't look away!"),
    13: _say("Pokefan in the lobby", "Your Pokemon are wonderful! I always watch them. Keep entertaining us!"),
    10: _say("Man by the posters", "Long ago, people performed in this theater. One day a Pokemon wandered on stage and copied the actors.",
             "Everyone loved it! And so the Pokemon Musical was born."),
    9: {"text": "Woman by the posters", "action": "EVENT", "event": {
        "lines": ["Do well in the Musical and people become your fans. They give you Props!",
                  "I don't have any Props, so here's this instead!"],
        "gift_item": {"TM277": 1}, "flag": "b2_musical_tm49",
        "done": ["Echoed Voice gets stronger every turn it's used in a row. Keep at the Musical, and keep using Echoed Voice!"]}},
    22: _say("Lady in the lobby", "It's such a treat when Trainers dress up their Pokemon this charmingly."),
    23: _say("Usher by the seats", "The seats are through here... but I think you belong on the stage!"),
    24: _say("Man by the posters ", "Props plus music plus dance! It's a moving spectacle!"),
}, **{}) | {n: {"text": "Fan %d" % (k + 1), "action": "EVENT", "condition": ["world:musical:fan:%d" % k],
                "event": {"world": "musical", "fan": k}} for k, n in enumerate(_FANS)},
    {12: ["MUSICAL PHOTOS", "Photos of the Pokemon Musical hang here."], 14: ["MUSICAL THEATER", "Props + music + dance = a moving spectacle!"]},
    title="Musical Theater",
    scenes=[{"trigger": "enter", "condition": ["not:b2_prop_case"], "flag": "b2_prop_case",
             "cast": [{"sheet": "b2_c44.png", "from": [16, 15], "to": "player", "leave": [16, 15], "lines": [
                 "Owner: Hello! How do you do? I'm the owner of this theater!",
                 "Ooh! You have quite an aura. Like a superstar who drew crowds here two years ago...",
                 "That superstar left this Prop Case behind. If they come back, we'll return it in a trice.",
                 "Until then, I see a worthy successor in you! Here, take it. Props to you!",
                 "{player_name} received the Prop Case! The Top Hat, Blue Barrettes, Square Glasses, a Maraca, the Umber Belt "
                 "and a Tie are inside.",
                 "In the Musical we dress Pokemon up in Props and they dance on stage. Talk to the receptionist to join!"],
                 "then": "event:b2_prop_case"}]}])
MUSICAL["title"] = "Musical Theater"


NIMBASA = town(
    62, NIMBASA_PEOPLE, NIMBASA_SIGNS,
    {65: ("center", "center"), 79: ("house", "stadium"), 84: ("house", "court"), 88: ("house", "house_w"),
     94: ("house", "house_e"), 93: ("house", "institute"), 91: ("gate", "gate_w"), 92: ("gate", "gate_e"), 66: ("house", "gear"),
     77: ("house", "musical")},
    rooms={
        "center": nimbasa_room(65, {
            0: {"text": "Pokémon Center", "action": "HEAL"}, 3: {"text": "Shop", "action": "SHOP"},
            5: _say("Clerk ", "Welcome! The counter on the left sells everyday items."),
            4: _say("Clerk  ", "Specialty Poke Balls are over here!"),
            7: {"text": "Mr. Medal", "action": "EVENT", "event": {"medal_rally": True}},
            10: _gift("Gentleman by the counter", ["Ha ha! Check the dust clouds in caves: they're chock-full of Shards!",
                                                    "I've a pile of them. I'll share!"], "RED_SHARD", "b2_nimbasa_shards",
                      ["Somewhere in Driftveil City an artisan teaches moves in exchange for Shards!"], count=10),
            8: _say("Girl with Minccino", "My beauteous Minccino! I met it on Route 5. It'll be a hit in the Musical!"),
            9: _say("Minccino", "Minccino: Chulululucha!"),
            1: _say("Man by the door", "Nimbasa never sleeps! The lights stay on all night."),
            2: _say("Woman by the door", "My Pokemon and I came for the Musical. We practise every day!"),
            6: _say("Boy by the sofa", "The Battle Subway's trains run from Gear Station. Seven Trainers in a row!"),
            11: _say("Trainer at the PC", "I keep my best Pokemon in a Box, ready for the Subway."),
        }, {}),
        "stadium": STADIUM, "stadium_stands": STADIUM_STANDS, "court": COURT, "court_stands": COURT_STANDS,
        "musical": MUSICAL, **FIELD_ROOMS,
        "house_w": nimbasa_room(88, {
            0: _say("Man in the house", "With a friend, wireless battles can use the Wonder Launcher rule: items in battle!"),
            1: _say("Woman in the house", "Wonder Launcher points build up as you battle. Spend them on items!"),
            2: _say("Old man in the house", "Nimbasa's glitz was nice a few years ago. Now it's too much. Maybe I'll move to the country."),
            3: _say("Woman by the window", "Some people whose Pokemon Team Plasma stole still haven't got them back."),
            4: _say("Man by the window", "I hear former Team Plasma members returned the Pokemon they took from one man. Is that enough?"),
        }, {}, title="House"),
        "house_w_2f": nimbasa_room(89, {
            0: _say("Woman upstairs", "A game starts at the same time every day in Big Stadium!"),
            1: _say("Girl upstairs", "Small Court has basketball and tennis!"),
            2: {"text": "Socialite upstairs", "action": "EVENT", "flag_condition": "not b2_soothe_bell",
                "event": {"lines": ["Oh my! Your Pokemon seems to like you very much! That makes me want to give you this!"],
                          "gift_item": {"SOOTHE_BELL": 1}, "flag": "b2_soothe_bell",
                          "requires": ["lead_friend:200"],
                          "fail": ["Oh? Your Pokemon's feelings toward you seem... neutral.",
                                   "Win its friendship, and I'll give you something nice!"]}},
        }, {}, title="Upstairs"),
        "house_e": nimbasa_room(94, {
            0: _say("Man in the house", "A Shiny Krokorok! Those colours blew my mind!"),
            1: _say("Girl in the house", "Pokemon that glitter when they come out of the grass are called Shiny Pokemon!"),
            2: _say("Psychic in the house", "Nuha nuha nuhaha!"),
        }, {}, title="House"),
        "house_e_2f": nimbasa_room(95, {
            0: _gift("Ace Trainer upstairs", ["If I compared Nimbasa's glow to something, it'd be the sun! It inspires me. Take this!"],
                     "SUN_STONE", "b2_nimbasa_sun_stone", ["A Sun Stone makes some Pokemon evolve. Petilil, for one!"]),
            1: _say("Girl upstairs", "I gave my Cottonee a Sun Stone as a present!"),
            2: _say("Man upstairs", "Pokemon evolve in all sorts of ways. Love them and you'll stay close, whatever they look like."),
        }, {}, title="Upstairs"),
        "institute": nimbasa_room(93, {
            0: _say("Woman of mystery", "Welcome to the Battle Institute. Our Battle Tests are taken over the wireless network.",
                    "...Our network doesn't reach this far. Perhaps another time."),
            1: _say("Girl in the Institute", "The Battle Test... The woman of mystery shows you the ropes. Keep your Pokemon from fainting!"),
        }, {}, title="Battle Institute"),
        "gate_w": nimbasa_room(91, {
            0: _say("Man at the board", "There are performers gathering on Route 5!"),
            1: _say("Ranger in the gate", "I wonder if the news on the board is just someone's mutterings..."),
        }, {1: ["ROUTE 5  -  NIMBASA CITY"]}, title="Nimbasa Gate"),
        "gate_e": nimbasa_room(92, {
            0: _gift("Infielder in the gate", ["Let's get to training! Give your Pokemon this and get them into shape!"],
                     "MACHO_BRACE", "b2_macho_brace",
                     ["A Macho Brace slows its holder down, but it grows stronger! A bit tricky, but that's how it goes!"]),
            1: _say("Woman in the gate", "Two years ago, a Zoroark hid its lair in Lostlorn Forest on Route 16."),
            2: _say("Man at the board", "This way leads to Route 16 and Marvelous Bridge!"),
        }, {1: ["ROUTE 16  -  NIMBASA CITY"]}, title="Nimbasa Gate"),
        "park": NIMBASA_PARK, "gym": NIMBASA_GYM, "coaster": NIMBASA_COASTER, **SUBWAY_ROOMS,
    },
    hidden={"18,49": "THUNDER_STONE"},
    extra_people=[(50, 19, NIMBASA_PANSAGE)],
    edges={"v": ("JOIN_AVENUE", [(x, 63) for x in range(45, 48)]), "q": ("ROOM:park", [(52, y) for y in range(44, 49)])},
    scenes=NIMBASA_SCENES,
)
NIMBASA["edge_to"] = {"45,63": [12, 5], "46,63": [13, 5], "47,63": [14, 5]}   # (Join Avenue's north end: its own 7-tile road)
JOIN_AVENUE["edge_to"] = {"%d,5" % x: [45 if x < 13 else 46 if x == 13 else 47, 63] for x in range(10, 17)}
for _r in ("stadium_stands", "court_stands"):
    NIMBASA["rooms"][_r]["title"] = NIMBASA["rooms"][_r].get("title") or "Stands"

# --------------------------------------------------------------------------------------------------------------- Route 16
# Zone 383: Nimbasa's east gate to the Bridge Gate (Marvelous Bridge: shut till the Hall of Fame, a broken lift: Rotom's
# prank) and north into Lostlorn Forest. A small tree (Cut) by the Heal Ball, a boulder (Strength) by Blossom and TM66.
ROUTE_16 = route(
    383, {9: _ball("Poke Ball past the boulder", "TM247", "b2_r16_tm66", name="TM66 Payback"),
          10: _ball("Poke Ball in the grove", "HEAL_BALL", "b2_r16_heal_ball", name="a Heal Ball")},
    {1: ["ROUTE 16"], 2: ["MARVELOUS BRIDGE", "Truly marvelous! And also a bridge!"]},
    exits={"<": ("NIMBASA_CITY", [(6, y) for y in range(21, 24)]), "^": ("LOSTLORN_FOREST", [(35, 0), (36, 0)])},
    trainers={2: "Backers Stu & Art", 4: "Cyclist Krissa", 5: "Cyclist Hector", 6: "Backpacker Blossom",
              7: "Backpacker Ivan", 8: "Depot Agent Hank"},
    hidden={"44,4": "TINY_MUSHROOM"},
    rooms={"bridge_gate": room(384, {0: _say("Woman in the gate", "What? The lift's broken? Oh no!"),
                                     1: {"text": "Roughneck by the machine", "action": "EVENT", "flag_condition": "not b2_bridge_gate_water",
                                         "event": {"lines": ["Awesome! This vending machine gave me an extra drink, for free!",
                                                             "I'll share my spoils with you, or I'll burst with joy!"],
                                                   "gift_item": {"FRESH_WATER": 1}, "flag": "b2_bridge_gate_water",
                                                   "done": ["If I keep getting extra drinks, I'll be rich!"]}},
                                     2: _say("Man with an umbrella", "That lift wasn't broken. A Rotom was playing a prank!",
                                             "Rotom can get inside electrical appliances!")},
                           {}, (55, 15), exits_extra={263: ("^", "MARVELOUS_BRIDGE")},
                           scenes=[{"who": "Woman in the gate", "trigger": {"zone": [19, 4, 21, 4]}, "condition": ["not:beat_unova_champion"],
                                    "every": True, "lines": ["The lift up to Marvelous Bridge isn't working..."], "push": [0, 1]}])},
    inside={"55,15": "bridge_gate"},
)
# (Black 2's people 0 and 1: the small tree at 26, 9; the boulder, its model 2 x 2 over the walls at 34-35, 20-21, the way into
#  the fenced middle: Blossom, TM66. Its person stands at 34, 23, below it.)
for _y, _x, _c in ((9, 26, "2"), (21, 34, "b"), (21, 35, "b"), (20, 34, "."), (20, 35, ".")):
    ROUTE_16["art"][_y] = ROUTE_16["art"][_y][:_x] + _c + ROUTE_16["art"][_y][_x + 1:]
ROUTE_16["rooms"]["bridge_gate"]["title"] = "Bridge Gate"
ROUTE_16["gated_exits"] = {"MARVELOUS_BRIDGE": ["beat_unova_champion"]}   # (the lift's scene turns you back till the Hall of Fame:
#  for the reach checks, which read a map's ways out but not its scenes; Main's inbox clean-main-unova-reach-gated-exits)
ROUTE_16["art"][15] = ROUTE_16["art"][15][:55] + "D" + ROUTE_16["art"][15][56:]   # (the Bridge Gate's door)

# -------------------------------------------------------------------------------------------------------- Lostlorn Forest
# Zone 385: the forest Zoroark hid with illusions two years ago. Breeder Galen battles again each visit; the Rangers give
# Berries; the odd Backpacker gives TM95 Snarl and runs off as a Zoroark. Its Hidden Grotto (record 2) at the north-east.
# Veteran Murphy, the Rare Candy and the Grass Gem are past the waterfall (Surf, Waterfall: the river's walk codes 0x3F / 0x40,
# read since 11-23). The Grass Gem (hidden at 19, 33): on main since 7eab28af (cleanup clean-main-unova-gen5-gems), placed 11-23.
LOSTLORN = route(
    385, {4: _ball("Poke Ball in the stump", "ULTRA_BALL", "b2_lostlorn_ultra", name="an Ultra Ball"),
          5: _ball("Poke Ball in the dark grass", "RARE_CANDY", "b2_lostlorn_candy", name="a Rare Candy"),   # (above the falls: Surf, Waterfall)
          6: _ball("Poke Ball by the north stump", "NET_BALL", "b2_lostlorn_net", name="a Net Ball"),
          7: {"text": "Odd Backpacker", "action": "EVENT", "flag_condition": "not b2_lostlorn_snarl",
              "event": {"lines": ["Hi, Trainer! I'm a traveller. Do you know a Pokemon called Zoroark?",
                                  "They say one settled here two years ago, and changed how the forest looked with its illusions.",
                                  "Every rumour has a kernel of truth. Here, a small present.",
                                  "{player_name} received TM95 Snarl!", "...Growwwf!", "The Backpacker turned into a Zoroark and ran off!"],
                        "gift_item": {"TM030": 1}, "flag": "b2_lostlorn_snarl"}}},
    {},
    exits={"v": ("UNOVA_ROUTE_16", [(12, 52), (13, 52)])},
    trainers={0: "Pokemon Breeder Galen", 1: "Pokemon Ranger Serenity", 2: "Pokemon Ranger Forrest", 3: "Veteran Murphy"},
    hidden={"6,24": "LEAF_STONE", "19,33": "GRASS_GEM"},
    rooms={"grotto": grotto_room(2, (22, 9))},
    inside={"22,9": "grotto"},
)
LOSTLORN["art"][9] = LOSTLORN["art"][9][:22] + "D" + LOSTLORN["art"][9][23:]

# ---------------------------------------------------------------------------------------------------------------- Route 5
# Zone 329: from Nimbasa's west gate to the Driftveil Drawbridge. Bianca catches up with HM02 Fly and shows you the route's
# Hidden Grotto (record 1: its first visit always a Minccino with Skill Link, as Black 2's script sets it). Performers
# crowd the west end: Motorcyclist Charles blocks the drawbridge (Rotation in Black 2, Triple in White 2: a double battle
# here, Jordan 11-19). Your picked BW rival battles you before the bridge (BW's Route 5 battle: area on_enter_event).
ROUTE5_CROWD = ["not:b2_charles"]
ROUTE_5 = route(
    329, {18: _ball("Poke Ball on the ledge", "SUPER_REPEL", "b2_r5_super_repel", name="a Super Repel"),
          19: _ball("Poke Ball behind the fence", "HYPER_POTION", "b2_r5_hyper_potion", name="a Hyper Potion"),
          0: _say("Ranger by the gate", "Pokemon Rangers patrol here. Route 5 is always lively: performers love it!"),
          2: _say("Man watching", "Every day there's a show on Route 5. Never the same one twice!"),
          20: _say("Girl watching", "Look at all the performers! I want to be in a show too!"),
          21: {"text": "Berry seller", "action": "EVENT", "event": {"world": "b2_errands", "berry_bunch": {"key": "b2_r5_berry_bunch"}}},
          22: _say("Clown by the trailer", "Smile! A sad face makes a bad show!"),
          23: _say("Girl by the trailer", "The Maid in the trailer is always hungry for new ingredients."),
          8: [{"text": "Motorcyclist Charles", "action": "EVENT", "condition": ROUTE5_CROWD + ["unova_version:" + _v], "event": {
              "lines": ["I'm a heartbreaker... My name... Charles.",
                        "I mastered a new style of battling to win a girl's heart. Hey, Trainer! Battle me!"],
              "flag": "b2_charles", "battle": _b2(_tid, dialogue={"player_won": ["Charles: You've got a good attitude! I'm always "
                                                                                   "at full throttle... Fine. The bridge is yours."]})}}
              for _v, _tid in (("BLACK_2", 339), ("WHITE_2", 340))],
          9: _say("Ace Trainer in the crowd", "That Motorcyclist won't let anyone across the drawbridge! Can you help?",
                  condition=ROUTE5_CROWD),
          **{n: _say(f"Performer {n}", "What a crowd! Nobody can get past to the drawbridge.", condition=ROUTE5_CROWD)
             for n in range(10, 18)}},
    {1: ["ROUTE 5", "Nimbasa City - Driftveil Drawbridge"], 3: ["TRAINER TIPS", "Hidden Grottoes look like a big shadow under "
                                                                   "the trees. Step in and see what's inside!"],
     2: ["DRIFTVEIL DRAWBRIDGE", "Ahead: Driftveil City"]},
    exits={">": ("NIMBASA_CITY", [(57, y) for y in range(21, 24)]), "<": ("DRIFTVEIL_DRAWBRIDGE", [(9, y) for y in range(15, 18)])},
    trainers={1: "Baker Jenn", 3: "Dancer Brian", 4: "Backers Ava & Aya", 6: "Artist Horton", 7: "Pokemon Ranger Lois"},
    hidden={"36,19": "HYPER_POTION"},
    rooms={"trailer": room(330, {0: {"text": "Maid in the trailer", "action": "EVENT", "event": {
               "world": "b2_errands", "maid_food": True}}},
                           {}, (45, 18)),
           "grotto": grotto_room(1, (53, 8))},
    inside={"45,18": "trailer", "53,8": "grotto"},
    scenes=[{"trigger": {"zone": [52, 21, 52, 25]}, "condition": ["not:b2_got_fly"], "flag": "b2_r5_bianca",
             "cast": [{"sheet": "b2_bianca.png", "from": [57, 22], "to": "player",
                       "lines": ["Bianca: {player_name}! Wait! Congratulations on the Bolt Badge!",
                                 "Bianca: Professor Juniper asked me to give you this. It's HM02 Fly!",
                                 "{player_name} received HM02 Fly!",
                                 "Bianca: With Fly you can zip back to any town you've been to. Use it with Pidove or Sigilyph!",
                                 "Bianca: ...Huh? Do you hear that? Rustling, over by the trees... Come on!"],
                       "then": "event:b2_fly", "path": [[53, 10]], "stay": True},
                      {"as": 0, "lines": ["Bianca: See that big shadow under the trees? It's a Hidden Grotto!",
                                          "Bianca: Sometimes there's a Pokemon inside with a rare Ability, or an item. They come back after a while!",
                                          "Bianca: This one has a Minccino in it, I think! I'll leave it to you. Bye-bye!"],
                       "leave": [57, 22]}],
             "then": "event:b2_r5_grotto_minccino"}],
)
ROUTE_5["art"][8] = ROUTE_5["art"][8][:53] + "D" + ROUTE_5["art"][8][54:]
ROUTE_5["rooms"]["trailer"]["title"] = "Trailer"
ROUTE_5["art"][18] = ROUTE_5["art"][18][:45] + "D" + ROUTE_5["art"][18][46:]   # (the trailer's door)

MAPS = {"ASPERTIA_CITY": ASPERTIA, "UNOVA_ROUTE_19": ROUTE_19, "FLOCCESY_TOWN": FLOCCESY, "UNOVA_ROUTE_20": ROUTE_20,
        "FLOCCESY_RANCH_OUTSIDE": RANCH_OUTSIDE, "FLOCCESY_RANCH": RANCH, "PLEDGE_GROVE": PLEDGE_GROVE,
        "VIRBANK_CITY": VIRBANK, "VIRBANK_COMPLEX_OUTSIDE": COMPLEX_OUTSIDE, "VIRBANK_COMPLEX": COMPLEX, "POKESTAR_STUDIOS": POKESTAR,
        "CASTELIA_CITY": CASTELIA,
        "CASTELIA_SEWERS": SEWERS, "CASTELIA_EMPTY_LOT": EMPTY_LOT, "LIBERTY_GARDEN": LIBERTY_GARDEN,
        "ROYAL_UNOVA": ROYAL_UNOVA,
        "UNOVA_ROUTE_4": ROUTE_4, "DESERT_RESORT_ENTRANCE": DESERT_ENTRANCE, "DESERT_RESORT": DESERT_RESORT,
        "RELIC_CASTLE": RELIC_CASTLE, "JOIN_AVENUE": JOIN_AVENUE,
        "NIMBASA_CITY": NIMBASA, "UNOVA_ROUTE_16": ROUTE_16, "LOSTLORN_FOREST": LOSTLORN, "UNOVA_ROUTE_5": ROUTE_5,
        "ANVILLE_TOWN": ANVILLE}
