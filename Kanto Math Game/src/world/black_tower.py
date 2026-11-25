"""The Black Tower (Black City) and White Treehollow (White Forest): Unova's Challenge, as Black 2 (Unova batch 11b, 11-25).

Jordan 11-24 (questions/UNOVA.md 16): ten Areas, their trainers and gate keys, the Boss at the end, Black 2's prizes.
Bulbapedia's Black Tower page (read 11-25) gives the rest, kept here:
- Area n: floors F = 1,1,1,1,1,2,3,2,3,4; each floor a grid of rooms, 3x3 (Areas 1-3, 6-7) or 4x4 (4-5, 8-10), built from
  Black 2's own room types (the lift room, plain rooms, pillar rooms, Surf rooms; the Boss's room); trainers per floor
  8, 10, 12, 16, 16, 12, 14, 24, 24, 24; two at most a room (three from Area 7), none in the lift's room, one in a Surf
  room; one Doctor (the Treehollow: a Nurse) a floor, who battles, then heals you once.
- One trainer on the top floor is the gate trainer: beating them opens the Boss's door, always the room north of theirs.
  Trainers' hints after a battle point the way (by class, as Black 2's).
- Normal trainers use two Pokemon from their own pool, both at one level in the Area's range (Area 1: 47-50, +3 each
  Area). Area n's Boss is Black 2's own (Abed ... Ira, then Benga; the Treehollow: Abigail ... Iria, then Benga), and Janna
  / Jariel in Area 10 once you've beaten Benga.
- Clearing an Area: back to the lobby, a prize (Areas 1-3 a vitamin, 4-5 two; 6-7 a Wing or Rare Candy, 8-9 two; 10 an
  EV-lowering Berry or Rare Candy), the next Area opens (unova_city: "b2_tower" progress; the Market's stores follow it).
- The lobby's receptionist sends you to any Area you've opened; the lift panel in each floor's lift room takes you to the
  Area's other floors or back down (you give up the Area; its trainers stand again next time).
Our layout is the same for every visit of an Area (Black 2 shuffles it): seeded by tower and Area, so maps, checks and the
Journal agree. Data: assets/unova_towers.json (dev/builders/unova_towers.py, from the game file).
Rooms (made by dev/builders/town_maps/unova.py from layout()): the city's rooms "tower_<t><n>_<floor>_<row>_<col>", where t
is "b" or "w". Flags: "bt_<t><n>_..." for that Area's battles (cleared each time you start the Area), b2_bt_benga."""
import json
import os
import random

FLOORS = [1, 1, 1, 1, 1, 2, 3, 2, 3, 4]
GRID = [3, 3, 3, 4, 4, 3, 3, 4, 4, 4]
PER_FLOOR = [8, 10, 12, 16, 16, 12, 14, 24, 24, 24]
TYPES = ("plain", "pillar", "surf")
ZONES = {"BLACK": {"lift": 481, "boss": 483, "plain": 493, "pillar": 486, "surf": 484, "lobby": 479},
         "WHITE": {"lift": 480, "boss": 482, "plain": 492, "pillar": 485, "surf": 487, "lobby": 478}}
SPOTS = {"plain": [(4, 5), (8, 9), (8, 5)], "pillar": [(4, 5), (8, 9), (9, 5)], "surf": [(10, 6)],
         "boss": [(6, 6)], "lift": []}
DOORS = {"N": (6, 1), "S": (6, 14), "W": (0, 7), "E": (12, 7)}
ARRIVE = {"N": (6, 12), "S": (6, 2), "W": (11, 7), "E": (1, 7)}   # (you came through that side's door: you stand inside the
STEP = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}      #  opposite door of the next room)
LIFT_AT = (6, 10)        # (where the lift sets you down in a floor's lift room)
LOBBY_AT = (9, 9)        # (the lobby, in front of the desk)
PRIZES = {(1, 3): (["HP_UP", "PROTEIN", "IRON", "CALCIUM", "ZINC", "CARBOS"], 1),
          (4, 5): (["HP_UP", "PROTEIN", "IRON", "CALCIUM", "ZINC", "CARBOS"], 2),
          (6, 7): (["HEALTH_WING", "MUSCLE_WING", "RESIST_WING", "GENIUS_WING", "CLEVER_WING", "SWIFT_WING", "RARE_CANDY"], 1),
          (8, 9): (["HEALTH_WING", "MUSCLE_WING", "RESIST_WING", "GENIUS_WING", "CLEVER_WING", "SWIFT_WING", "RARE_CANDY"], 2),
          (10, 10): (["POMEG_BERRY", "KELPSY_BERRY", "QUALOT_BERRY", "HONDEW_BERRY", "GREPA_BERRY", "TAMATO_BERRY", "RARE_CANDY"], 1)}
NAMES = {"BLACK": "the Black Tower", "WHITE": "the White Treehollow"}
_DATA = {}


def data():
    if "d" not in _DATA:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "unova_towers.json")
        try:
            _DATA["d"] = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            _DATA["d"] = {}
    return _DATA["d"]


def room_name(t, n, f, r, c):
    return "tower_%s%d_%d_%d_%d" % (t[0].lower(), n, f, r, c)


def prefix(t, n):
    return "bt_%s%d_" % (t[0].lower(), n)


def layout(t, n):
    """Area n of tower t: {"floors": [{"cells": {(r, c): type}, "lift": (r, c)}], "boss": (f, r, c), "gate": (f, r, c, slot),
    "people": [(f, r, c, slot, kind, k)] (kind "trainer" k = the area's trainer index, "healer" k = its healer index)}."""
    rng = random.Random("%s-%d" % (t, n))
    g, nf, want = GRID[n - 1], FLOORS[n - 1], PER_FLOOR[n - 1]
    per_room = 2 if n < 7 else 3
    d = (data().get(t) or {}).get(str(n)) or {}
    ntr, nhe = max(1, len(d.get("trainers") or [])), max(1, len(d.get("healers") or []))
    floors, people = [], []
    boss = gate = None
    for f in range(nf):
        lift = (g - 1, rng.randrange(g))
        cells = {(r, c): rng.choice(TYPES) for r in range(g) for c in range(g)}
        cells[lift] = "lift"
        if f == nf - 1:   # (the Boss's room on the top floor, in the top row, its gate room below it)
            bc = rng.choice([c for c in range(g) if (1, c) != lift])
            cells[(0, bc)] = "boss"
            if cells[(1, bc)] == "surf":
                cells[(1, bc)] = "plain"
            boss = (f, 0, bc)
        floors.append({"cells": cells, "lift": lift})
        free = [(r, c, s) for (r, c), ty in sorted(cells.items()) if ty not in ("lift", "boss")
                for s in range(min(per_room, len(SPOTS[ty])))]
        rng.shuffle(free)
        if f == nf - 1:   # (the gate trainer first: in the room below the Boss's)
            gs = next(x for x in free if (x[0], x[1]) == (1, boss[2]))
            free.remove(gs)
            free.insert(0, gs)
        taken = free[:want]
        healer = next(i for i, x in enumerate(taken) if f != nf - 1 or i != 0)
        for i, (r, c, s) in enumerate(taken):
            if i == healer:
                people.append((f, r, c, s, "healer", rng.randrange(nhe)))
            else:
                people.append((f, r, c, s, "trainer", rng.randrange(ntr)))
            if f == nf - 1 and i == 0:
                gate = (f, r, c, s)
    return {"floors": floors, "boss": boss, "gate": gate, "people": people, "grid": g}


def doors(cells, r, c, g):
    """The sides of room (r, c) that lead to a room next to it."""
    ty = cells[(r, c)]
    out = {}
    for side, (dr, dc) in STEP.items():
        rr, cc = r + dr, c + dc
        if not (0 <= rr < g and 0 <= cc < g):
            continue
        other = cells[(rr, cc)]
        if ty == "boss" and side != "S" or other == "boss" and side != "N" or ty == "lift" and side == "N" \
                or other == "lift" and side == "S":
            continue
        out[side] = (rr, cc)
    return out


# ---------------------------------------------------------------- the game side
def _story(state):
    return state.game.story_manager


def _flag(t, n, f, r, c, s):
    return prefix(t, n) + "%d_%d_%d_%d" % (f, r, c, s)


def condition(story, arg):
    what, *rest = str(arg).split(":")
    if what == "gate":   # gate:<T>:<n>: the Area's gate trainer is beaten
        t, n = rest[0].upper(), int(rest[1])
        g = layout(t, n)["gate"]
        return bool(g and story.story_flags.get(_flag(t, n, *g)))
    return False


def _clear_area(story, t, n):
    p = prefix(t, n)
    for k in [k for k in story.story_flags if str(k).startswith(p)]:
        story.story_flags.pop(k, None)


def _go(state, room, at):
    if state.game.current_state is not state:
        state.game.change_state(state)
    state._go(room, "LIFT")
    state.player = state.anim_from = state.partner = state.partner_from = (int(at[0]), int(at[1]))
    state.facing = (0, 1)
    state._remember()


def _team(t, n, who, rng):
    """A normal trainer's battle: two Pokemon from their own pool, one level in the Area's range."""
    d = data()[t][str(n)]
    lo, hi = d["levels"]
    sets = [d["sets"][str(s)] for s in who["sets"] if str(s) in d["sets"]]
    pick = rng.sample(sets, min(2, len(sets))) if sets else []
    lv = rng.randint(lo, hi)
    team = [p["id"] for p in pick]
    out = {"name": who["name"], "class": who["class"], "sprite": who["sprite"], "team": team, "levels": [lv] * len(team),
           "movesets": {str(p["id"]): p["moves"] for p in pick if p.get("moves")}, "rewards": {"balls": 2}}
    held = {str(p["id"]): p["item"] for p in pick if p.get("item") and n >= 5 and who["class"] not in
            ("RICH_BOY", "LADY", "GENTLEMAN", "SOCIALITE") and (who["class"] not in ("DOCTOR", "NURSE") or n >= 7)}
    if held:
        out["held_items"] = held
    return out


def _side(a, b):
    """The direction from room a to room b, in words."""
    (ra, ca), (rb, cb) = a, b
    ns = "north" if rb < ra else "south" if rb > ra else ""
    ew = "west" if cb < ca else "east" if cb > ca else ""
    return (ns + ew) or "right here"


def _hint(game, t, n, cls, here):
    """What a beaten trainer tells you (Black 2's hints, by class)."""
    L = layout(t, n)
    gf, gr, gc, _gs = L["gate"]
    f, r, c = here
    if cls in ("YOUNGSTER", "SCHOOL_KID", "POLICEMAN", "WORKER"):
        k = sum(1 for p in L["people"] if p[:3] == (gf, gr, gc)) - 1
        return "The gate trainer's room has %s other trainer%s in it." % (k or "no", "" if k == 1 else "s")
    if cls in ("PSYCHIC", "BACKPACKER", "HIKER", "BLACK_BELT", "BATTLE_GIRL") and f == gf:
        return "The gate trainer's room is %s of here." % _side((r, c), (gr, gc))
    if cls in ("SCIENTIST", "WAITER", "JANITOR", "ROUGHNECK", "BAKER") or f != gf:
        return "The gate trainer is %s." % ("on this floor" if f == gf else "higher up" if gf > f else "further down")
    if cls in ("RICH_BOY", "GENTLEMAN", "BREEDER"):
        doc = next((p for p in L["people"] if p[0] == f and p[4] == "healer"), None)
        return "The %s's room is %s of here." % ("Nurse" if t == "WHITE" else "Doctor", _side((r, c), doc[1:3])) if doc else \
            "Oww! Take it easy on me!"
    if cls in ("LADY", "SOCIALITE"):
        boss = data()[t][str(n)]["boss"]
        from src.minigames.base import species_name
        return "I hear the Boss Trainer leads with %s." % species_name(game, boss["team"][0]) if boss.get("team") else             "Good luck with the Boss!"
    return "The Boss Trainer's door is just north of the gate trainer's room."


def event(state, ev, lines, show):
    story = _story(state)
    game = state.game
    from src.states.overworld.common import _say_then
    from src.states.systems.pick_list import PickListState
    if ev.get("desk"):
        t = str(ev["desk"]).upper()
        from src.world import unova_city
        done = unova_city.cleared(story, t)
        open_to = min(10, done + 1)
        rows = [("Area %d" % n + (" (cleared)" if n <= done else ""), n) for n in range(1, open_to + 1)]

        def go(n):
            game.change_state(state)
            if n is None:
                show(["We'll be waiting for your challenge!"])
                return
            _clear_area(story, t, n)
            L = layout(t, n)
            f0 = L["floors"][0]["lift"]
            _go(state, room_name(t, n, 0, *f0), LIFT_AT)
        _say_then(state, ["Welcome to %s, Unova's Challenge! Which Area will you take on?" % NAMES[t]],
                  lambda: game.change_state(PickListState(game, state, "WHICH AREA?", rows, go)))
        return
    if ev.get("tower_lift"):   # (not "lift": that key is the shared lift list the Journal reads)
        t, n, f = str(ev["tower_lift"][0]).upper(), int(ev["tower_lift"][1]), int(ev["tower_lift"][2])
        L = layout(t, n)
        rows = [("Floor %d" % (k + 1), k) for k in range(len(L["floors"])) if k != f] + [("Back to the lobby", -1)]

        def ride(k):
            game.change_state(state)
            if k is None:
                return
            if k == -1:
                _go(state, "lobby", LOBBY_AT)
                show(["You left Area %d. Its trainers will be waiting next time." % n])
                return
            _go(state, room_name(t, n, k, *L["floors"][k]["lift"]), LIFT_AT)
        game.change_state(PickListState(game, state, "THE LIFT", rows, ride))
        return
    if ev.get("fight"):
        t, n, f, r, c, s = ev["fight"]
        t = str(t).upper()
        flag = _flag(t, n, f, r, c, s)
        L = layout(t, n)
        who_kind, k = next((p[4], p[5]) for p in L["people"] if tuple(p[:4]) == (f, r, c, s))
        d = data()[t][str(n)]
        who = (d["healers"] if who_kind == "healer" else d["trainers"])[k % len(d["healers" if who_kind == "healer" else "trainers"])]
        if story.story_flags.get(flag):
            if who_kind == "healer":
                if story.story_flags.get(flag + "_healed"):
                    show(["Take care of your Pokemon."])
                    return
                story.story_flags[flag + "_healed"] = True
                from src.states.overworld.area_transition import heal_team
                heal_team(game)
                show(["Let me see your Pokemon... There. They're all healed. I can only do this once, mind!"])
                return
            if (f, r, c, s) == tuple(L["gate"]):
                show(["You beat me, so the Boss Trainer's door is open now. It's the room just north of this one."])
                return
            show([_hint(game, t, n, who["class"], (f, r, c))])
            return
        rng = random.Random()
        info = _team(t, n, who, rng)
        info["dialogue"] = {"player_won": ["You're strong!"]}
        _battle(game, story, info, flag, {"world": "black_tower", "t": t, "n": n})
        return
    if ev.get("boss"):
        t, n = str(ev["boss"][0]).upper(), int(ev["boss"][1])
        flag = prefix(t, n) + "boss"
        if story.story_flags.get(flag):
            return _finish(state, t, n, show)
        d = data()[t][str(n)]
        b = dict(d["boss_later"] if n == 10 and story.story_flags.get("b2_bt_benga") and d.get("boss_later") else d["boss"])
        b["dialogue"] = {"player_won": ["Area %d is cleared! Well done!" % n]}
        _battle(game, story, b, flag, {"world": "black_tower", "t": t, "n": n, "boss": True})
        return
    show(lines or ["..."])


def _battle(game, story, info, flag, facility):
    """A tower battle: a facility's (battle.py's after_battle hook, as FireRed's Trainer Tower): lose and the challenge ends
    in the lobby (no whiting out); beat the Boss and the Area's done."""
    from src.states.overworld.common import _start_event_battle
    intro = _start_event_battle(game, story.current_area_key, info, flag)
    b = getattr(intro, "next_state", None) or intro
    b.facility = facility
    game.change_state(intro)


def _to_lobby(game, said):
    """Back to the tower's lobby on its city's map (a fresh walk state there), then the words."""
    from src.states.overworld import CityState
    area = game.story_manager.current_area_key
    game.walk_town_room = (area, "lobby")
    game.walk_town_pos = (area, tuple(LOBBY_AT), (0, 1))
    st = CityState(game)
    game.change_state(st)
    cur = game.current_state
    if said:
        (getattr(cur, "show_message", None) or getattr(cur, "say", None) or (lambda ls: None))(said)


def after_battle(game, info, won):
    """battle.py's facility hook: None (back to the map), or a function that goes on itself."""
    t, n = str(info.get("t")).upper(), int(info.get("n", 1))
    story = game.story_manager
    if not won:
        _clear_area(story, t, n)
        return lambda: _to_lobby(game, ["You lost in Area %d of %s." % (n, NAMES.get(t, "the tower")),
                                        "Your challenge ends here. Its trainers will be waiting when you try again."])
    if info.get("boss"):
        return lambda: _to_lobby(game, _done(story, t, n))
    return None


def _finish(state, t, n, show):
    said = _done(_story(state), t, n)
    _go(state, "lobby", LOBBY_AT)
    show(said)


def _done(story, t, n):
    """Area n cleared: the next opens, Black 2's prize; its trainers stand again next time. -> the words to say."""
    from src.world import unova_city
    if "Benga" in str(data()[t][str(n)]["boss"].get("name")) and n == 10:
        story.story_flags["b2_bt_benga"] = True
    tw = unova_city.tower(story, t)
    first = n > tw.get("cleared", 0)
    tw["cleared"] = max(tw.get("cleared", 0), n)
    pool, k = next(v for (lo, hi), v in PRIZES.items() if lo <= n <= hi)
    item = random.choice(pool)
    story.inventory[item] = story.inventory.get(item, 0) + k
    _clear_area(story, t, n)
    said = ["You cleared Area %d of %s!" % (n, NAMES[t]),
            "Here's your reward: %s%s!" % ("" if k == 1 else "%d x " % k, item.replace("_", " ").title())]
    if first and n < 10:
        said.append("Area %d is open to you now." % (n + 1))
    if n == 10 and first:
        said.append("You've cleared every Area of %s! Amazing!" % NAMES[t])
    return said
