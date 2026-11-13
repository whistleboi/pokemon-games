"""Route dungeons (Jordan, 11-05): every route, cave and building is walked on a map, Mystery Dungeon style
(the route menu underneath only supplies its actions: battles, catches, events).

Which areas: every one that isn't a town, in every region (Jordan, 11-05: the map replaces the route
menu). Each gets a recipe: its own in assets/dungeon_routes.json (Kanto's), else one made from the area
(recipe_for: its battle type picks the look, a fishing spot gets ponds). The rules (floors, turns, wild
Pokemon that chase you, loot, TM spots) are src/dungeon/core.py; this is the screen.

How the route's actions map onto the walk:
- CATCH WILD PKMN -> bump into a wild Pokemon and pick MATH: one question, a right answer throws a ball
  at the route catch's odds (a wrong one and it runs away). Or HONEY (used from the Bag) or SWEET SCENT
  (the H key) draws three wild Pokemon for the usual three-Pokemon catch (the route's own catch screen,
  then back to the map).
- The buttons (Jordan, 11-05): POKeMON (your party), POKeDEX, and WAIT (a turn standing still: the wild
  Pokemon come to you).
- BATTLE WILD PKMN -> bump into a wild Pokemon and pick BATTLE (the full battle screen).
- BATTLE TRAINER -> bump into a trainer, or walk into one's line of sight.
- Items lie about (the area's loot table), and TM spots hold a TM picked once per save.
- The ways out are signs on the map: where you came in, and the rest in the far rooms (stairs first
  when the area has more than one floor).
- The route's other buttons (a boss, a story event, someone to talk to, the Day Care) are figures on the
  map: walk into one for the same thing its button does. Each shows while its button would, on its zone's
  floor, else the last floor; but a boss doesn't wait for the area's trainers to be beaten (Jordan, 11-05:
  finding it is the task).
- FISH: beside water (a pond, or anywhere at sea); HEADBUTT: beside a tree. A button turns up there.
- An area in zones (the Pokemon Tower's floors, the Seafoam Islands, the Safari Zone's areas) has a floor
  for each zone, with stairs (or gates) between; its trainers, ways out and figures are on their zone's.
- Trainers and figures are drawn with Pokemon Journeys' overworld sprites (assets/dungeon/characters,
  which is whose in assets/dungeon_sprites.json); a Pokemon without one, with its party icon.
- You walk as your trainer (Jordan, 11-05), your lead Pokemon following a step behind.
- An area of many zones can put several side by side on one wide floor (recipe "zones_per_floor", up to 4:
  the Safari Zones; Johto's and the Great Marsh three areas a floor, Kanto's and Hoenn's all four on one): a gate line marks each border, and crossing it puts you in
  that area (its wild Pokemon, its name on the bar).
- The Bug-Catching Contest (Jordan, 11-05; Gold/Silver/Crystal and HeartGold/SoulSilver: National Park;
  any day, once a day): an area with "bug_contest" is the contest's own map.
  Bugs roam it; you have 20 Sport Balls and CONTEST_TURNS turns, catch with MATH only, and keep only your
  best catch. When time's up (or you leave by the gate) the judges score it against the others'.
- Buildings are fixed (the same floors every visit, made from the area's own seed) and have no fog: the
  whole floor shows. The Celadon Game Corner is drawn (assets/dungeon_routes.json "layout"): talk to the
  clerk across the counter to pick a game, buy coins or trade for prizes; play the slots at a machine.

DungeonState is a PlayState, so battles, the catch screen, evolutions and the side menus all work as
on a route. PlayState(game) itself hands back a DungeonState for a dungeon area (see PlayState.__new__),
and after a battle the same walk carries on (the battle builds PlayState(game, restore_data)).
Headless (the check suites) the old route screen stays, unless game.dungeon_routes is set.
"""
import json
import math
import os
import random

import pygame

from src.config import FPS
from src.dungeon import core
from src.pokemon import balance, catching, forms, tms
from src.pokemon import items as itemlib
from src.pokemon.data import Pokemon
from src.states.overworld.common import _trainer_sprite, travel_label
from src.states.overworld.route import PlayState
from src.states.overworld.overworld_battle import OverworldBattles
from src.ui import theme
from src.utils import Utils
from src.world import levels

TILE = 56

# The walked map sits in a frame (Jordan, 11-12): black all round it, MENU, the Journal and the mini-map
# in the left band, the buttons stacked in the right one, so nothing covers the map and a way out on
# its edge is never at the very edge of the screen.
FRAME_LEFT, FRAME_TOP, FRAME_RIGHT, FRAME_BOTTOM = 300, 88, 160, 12
FRAME_BLACK = (0, 0, 0)
SIDE_W = 140  # (the right band's buttons)


def map_view(game):
    """The part of the screen the walked map is drawn in."""
    W, H = game.width, game.height
    return pygame.Rect(FRAME_LEFT, FRAME_TOP, W - FRAME_LEFT - FRAME_RIGHT, H - FRAME_TOP - FRAME_BOTTOM)


def draw_frame(screen, view):
    """The thin line round the map's frame."""
    pygame.draw.rect(screen, (70, 82, 120), view.inflate(6, 6), 3, border_radius=6)


def side_buttons(game):
    """The right band's button spots, bottom up: (x, y, w, h) for WAIT, HONEY, POKEDEX, POKEMON, then a tall
    one for what's beside you (Fish, Headbutt...), then BAG at the top (Jordan, 11-12: the Bag one press away on the map)."""
    W, H = game.width, game.height
    x = W - FRAME_RIGHT + (FRAME_RIGHT - SIDE_W) // 2
    return [pygame.Rect(x, H - 72, SIDE_W, 60), pygame.Rect(x, H - 140, SIDE_W, 60),
            pygame.Rect(x, H - 224, SIDE_W, 74), pygame.Rect(x, H - 308, SIDE_W, 74),
            pygame.Rect(x, H - 404, SIDE_W, 86), pygame.Rect(x, H - 474, SIDE_W, 60)]


def mini_scale(w, h, room_w, room_h):
    """The mini-map's pixels a tile: 4, smaller for a big map so it fits the left band."""
    return max(1, min(4, (room_w - 8) // max(1, w), (room_h - 8) // max(1, h)))
STEP_FRAMES = 6          # frames a step takes (the walk animation)
MATH_SECONDS = 30
TAP_FRAMES = 12     # how long a tapped tile stays lit, when it isn't where you're walking to
QUICK_SECONDS = 5        # a right answer this fast weakens it to 1 HP (as on the route catch screen)

COLORS = {  # floor, tall grass, wall (trees or rock), wall top
    "field": ((150, 206, 108), (82, 164, 78), (44, 104, 58), (62, 132, 70)),
    "forest": ((118, 160, 92), (64, 132, 66), (24, 72, 44), (38, 94, 54)),
    "cave": ((160, 140, 116), (140, 122, 100), (72, 60, 54), (96, 82, 72)),
    "building": ((206, 196, 170), (176, 160, 132), (64, 66, 84), (104, 108, 128)),  # (grass: a rug)
    "sea": ((84, 146, 214), (60, 118, 190), (112, 104, 96), (150, 140, 126)),     # you surf the floor
    "snow": ((232, 238, 246), (196, 214, 232), (84, 110, 126), (210, 226, 238)),   # snowy firs
    "desert": ((226, 204, 150), (204, 180, 120), (164, 120, 80), (196, 152, 104)),  # sand, rock
    "mountain": ((176, 168, 120), (120, 150, 84), (118, 96, 76), (150, 126, 100)),  # outdoor rock, a canyon
    # Hyperspace Lumiose's zones: glowing floors in each theme's colours
    "hyper_verdant": ((92, 150, 110), (60, 120, 90), (40, 30, 70), (130, 90, 200)),
    "hyper_ember": ((170, 96, 80), (140, 70, 64), (50, 24, 40), (230, 120, 90)),
    "hyper_tidal": ((70, 120, 170), (50, 96, 150), (24, 30, 70), (110, 170, 240)),
    "hyper_frost": ((170, 196, 226), (140, 170, 210), (40, 50, 90), (200, 220, 255)),
    "hyper_volt": ((150, 140, 80), (120, 110, 60), (40, 30, 60), (250, 220, 90)),
}
# An area without its own recipe: its look from its battle type.
STYLE_OF = {"grass": "field", "field": "field", "outdoor": "field", "cave": "cave", "mountain": "cave",
            "indoor": "building", "distortion": "building", "ocean": "sea", "water": "sea", "forest": "forest",
            "snow": "snow", "desert": "desert", "sand": "desert"}
WATER_C = ((70, 130, 206), (150, 196, 240))  # a pond, its ripples
TREE_STYLES = ("field", "forest", "snow")  # where HEADBUTT works (a wall is a tree)
# The route's buttons that are figures on the map (walk into one: its button's action).
FIGURE_ACTIONS = ("BOSS", "EVENT", "NPC", "HOENN_EVENT", "DAYCARE", "BERRY", "CAMP", "REST", "WEATHER_DIRECTOR", "CENTER",
                  "SNAG", "MAX_RAID", "DIVE", "GAME_CORNER", "BUG_CONTEST")
DECOR_C = {"slot": ((200, 60, 70), (250, 230, 120)), "counter": ((150, 100, 60), (204, 156, 100)),
           "poster": ((60, 60, 80), (236, 226, 200))}
FACING_ROW = {(0, 1): 0, (-1, 0): 1, (1, 0): 2, (0, -1): 3}  # a sheet's rows: down, left, right, up

# The Bug-Catching Contest: its balls and turns, prizes for 1st, 2nd, 3rd (and the rest), how a catch scores
CONTEST_BALLS, CONTEST_TURNS = 20, 150
# The Safari Game (Jordan, 11-13: "a timer or ball limit for safari visits"): an area with "safari_game" gives each visit
# its own Safari Balls and steps (Emerald's 30 and 500); you catch only with those, no battling; when either runs out,
# the visit is over and you're walked back out.
SAFARI_BALLS, SAFARI_STEPS = 30, 500
CONTEST_DAYS = tuple(range(7))  # any day, once a day (Jordan, 11-05; the games: Tuesday, Thursday, Saturday)
CONTEST_PRIZES = ["SUN_STONE", "EVERSTONE", "RARE_CANDY"]
CONTEST_RARE = {123: 100, 127: 100, 12: 70, 15: 70, 49: 70, 402: 60, 11: 30, 14: 30, 47: 40}
CONTEST_RIVALS = ["Bug Catcher Don", "Bug Catcher Ed", "Cooltrainer Nick", "Pokefan Beverly", "Youngster Samuel"]

_recipes = {}
_sprite_map = {}


def contest_score(p, rng=None):
    """A contest catch's score (the games': level, its stats, how rare it is, a little luck)."""
    import random as _r
    ivs = getattr(p, "ivs", None) or {}
    iv = sum(ivs.values()) if isinstance(ivs, dict) else sum(ivs or [])
    return int(CONTEST_RARE.get(p.id, 10) + p.level * 4 + iv // 4 + (rng or _r).randint(0, 20))


def contest_entry(state):
    """The officer at National Park's gate: the contest's map, on its days, once a day."""
    import datetime
    from src.states.overworld.area_transition import AreaTransitionState
    game = state.game
    story = game.story_manager
    today = datetime.date.today()
    show = getattr(state, "show_dialogue", None)
    back = getattr(state, "show_progression_menu", None)
    if today.weekday() not in CONTEST_DAYS:
        show(["Officer: There's no Bug-Catching Contest today.",
              "Come back another day with your best Pokemon!"], callback=back)
        return
    if story.story_flags.get("bug_contest_day") == today.isoformat():
        show(["Officer: You've already entered today's contest. Come back next time!"], callback=back)
        return
    if not any(p and p.current_hp > 0 for p in story.player_team):
        show(["Officer: Your Pokemon need rest first. Come back after a visit to a Pokemon Center!"], callback=back)
        return
    story.story_flags["bug_contest_day"] = today.isoformat()
    show(["Officer: Welcome to the Bug-Catching Contest!",
          f"Here are {CONTEST_BALLS} SPORT BALLS. Catch the best Bug Pokemon you can before time runs out.",
          "You can keep only one: the best one you catch. Good luck!"],
         callback=lambda: game.change_state(AreaTransitionState(game, "BUG_CONTEST")))


def held_way(keys_map):
    """The way a held arrow key (or WASD) points, or None (Jordan, 11-07: hold to keep walking)."""
    try:
        pressed = pygame.key.get_pressed()
    except pygame.error:
        return None
    for key, way in keys_map.items():
        if pressed[key]:
            return way
    return None


def held_pointer():
    """Where a held tap (the mouse button, a finger) is, or None."""
    try:
        if pygame.mouse.get_pressed()[0]:
            return pygame.mouse.get_pos()
    except pygame.error:
        pass
    return None


def high_tide(now=None):
    """Shoal Cave's tide (the games: in from 3:00 to 9:00 and from 15:00 to 21:00, real time)."""
    import datetime as _dt
    h = (now or _dt.datetime.now()).hour
    return 3 <= h < 9 or 15 <= h < 21


def scene_sheet(game, token):
    """("mon:<species>" passes through: a Pokemon walking in a scene.) A scene's walking sheet: a file ("em_64.png"), or a token for someone who depends on the save (Jordan, 11-12):
    "@rival" (this save's rival, from trainers_<REGION>: Hoenn's Brendan or May), "@grunt" / "@grunt_f" (a villain of
    this version's team: Team Magma in Omega Ruby, Team Aqua in Alpha Sapphire)."""
    token = str(token or "")
    if not token.startswith("@") or token.startswith("mon:"):
        return token
    story = game.story_manager
    region = str(story.get_current_region() or "")
    own = sprite_map(game).get("trainers_" + region) or {}
    if token == "@rival":
        who = str(getattr(game, "rival_character", "") or "").lower()
        return own.get(f"{who}.png") or own.get("rival.png") or "NPC 17.png"
    if token == "@legend_primal":  # (its Primal form: Jordan's overworld sheets, 11-13)
        try:
            from src.world import hoenn as _h
            return "primal_kyogre.png" if _h.version(story) == "ALPHA_SAPPHIRE" else "primal_groudon.png"
        except Exception:
            return "primal_groudon.png"
    if token in ("@legend", "@legend_asleep"):  # (this version's super-ancient Pokemon: Emerald's Groudon / Kyogre, awake or asleep)
        try:
            from src.world import hoenn as _h
            aqua = _h.version(story) == "ALPHA_SAPPHIRE"
        except Exception:
            aqua = False
        return ("em_205.png" if aqua else "em_206.png") if token.endswith("asleep") else ("em_197.png" if aqua else "em_198.png")
    if token in ("@leader", "@other_leader"):  # (this version's villain leader, or the other team's: Emerald's Maxie and Archie)
        try:
            from src.world import hoenn as _h
            aqua = _h.version(story) == "ALPHA_SAPPHIRE"
        except Exception:
            aqua = False
        return "em_195.png" if aqua == (token == "@leader") else "em_196.png"
    if token in ("@grunt", "@grunt_f", "@other_grunt", "@other_grunt_f"):  # (this version's team; "other": the rival team's, Mt. Chimney's fight)
        try:
            from src.world import hoenn as _h
            aqua = _h.version(story) == "ALPHA_SAPPHIRE"
        except Exception:
            aqua = False
        if "other" in token:
            aqua = not aqua
        key = ("aqua" if aqua else "magma") + ("_f" if token.endswith("_f") else "")
        return {"aqua": "em_117.png", "aqua_f": "em_118.png", "magma": "em_119.png", "magma_f": "em_120.png"}[key]
    return "NPC 17.png"


def sprite_map(game):
    """Which overworld sheet is whose (assets/dungeon_sprites.json)."""
    if "all" not in _sprite_map:
        path = os.path.join(game.assets.assets_dir or "", "dungeon_sprites.json")
        try:
            with open(path, encoding="utf-8-sig") as f:
                _sprite_map["all"] = json.load(f)
        except (OSError, ValueError):
            _sprite_map["all"] = {}
    return _sprite_map["all"]


# ---------------------------------------------------------------- which areas, and their recipes
def recipes(game):
    if "all" not in _recipes:
        path = os.path.join(game.assets.assets_dir or "", "dungeon_routes.json")
        try:
            with open(path, encoding="utf-8-sig") as f:
                _recipes["all"] = json.load(f)
        except (OSError, ValueError):
            _recipes["all"] = {}
    return _recipes["all"]


def with_rooms(m):
    """A route map with buildings you walk into (Jordan, 11-12: "buildings on routes"), in the towns' own words: "rooms"
    {name: a map of its own (theme "room", its mats' "exits" {"v": "OUT:x,y"}, "people": route options by their text)}
    and "inside" {"x,y" of a door: room name} on the map (or on a floor of it). Each room becomes a floor of the area
    after its own, joined to its door: in at the door you stand on the room's mat, out by the mat you stand below the
    door. No wild Pokemon indoors. The map itself is not changed."""
    rooms = m.get("rooms") or {}
    if not rooms:
        return m
    floors = [dict(f) for f in m["floors"]] if m.get("floors") else [
        {k: m[k] for k in ("art", "exits", "signs", "people", "trainer_spots", "links", "overheads", "parts", "boss_spot", "inside", "stops",
                           "barred", "moves", "scenes", "berry_soil", "sign_scenes", "edge_to", "dive", "surface", "pool") if k in m}]   # (the map's own floor keeps everything of its own: who's in the way, how people move)
    n0 = len(floors)
    names = list(m.get("floor_names") or [""] * n0)
    where, doors = {}, {}
    for i, f in enumerate(floors):
        for d, name in (f.get("inside") or (m.get("inside") if n0 == 1 else None) or {}).items():
            if name in rooms:
                doors.setdefault(name, []).append((i, d))
    for name, room in rooms.items():
        if name not in doors:
            continue
        j = len(floors)
        where[name] = j
        art = [list(r) for r in room["art"]]
        links, mats = {}, {}
        land, enter, keep = room.get("land") or {}, room.get("enter") or {}, {}
        # (Kanto's gatehouses: a mat that is a real way out to the next area stays one; "land" {door: where you stand
        # outside it}, "enter" {door: where you stand inside}: a door in a building's side or back, or two tiles wide)
        for ch, target in (room.get("exits") or {}).items():
            if not str(target).startswith("OUT:"):
                keep[ch] = target
                continue
            x, y = (int(v) for v in str(target)[4:].split(","))
            back = next((i for i, d in doors[name] if d == f"{x},{y}"), doors[name][0][0])
            for ry, row in enumerate(art):
                for rx, c in enumerate(row):
                    if c == ch:
                        row[rx] = "1"
                        links[f"{rx},{ry}"] = [back, land[f"{x},{y}"][0], land[f"{x},{y}"][1] + 1] if f"{x},{y}" in land else [back, x, y + 1]
                        mats.setdefault(f"{x},{y}", (rx, ry))
        own = {k: v for k, v in room.items() if k not in ("art", "exits", "links", "land", "enter")}
        floors.append(dict(own, art=["".join(r) for r in art], exits=keep, links=links, boss_spot=None, parts=True, indoors=True,
                           pool="NO_WILD_INDOORS_PERCENTAGES", buildings=room.get("buildings") or {}))
        names.append(str(room.get("title") or name).title())
        for i, d in doors[name]:  # (the door outside: onto the room's mat for it)
            mat = (enter[d][0], enter[d][1] + 1) if d in enter else mats.get(d) or next(iter(mats.values()), None)
            if mat:
                floors[i] = dict(floors[i], links=dict(floors[i].get("links") or {}, **{d: [j, mat[0], mat[1]]}))
    on = dict(m.get("figure_floors") or {})
    for i, f in enumerate(floors):  # (everyone stays on the floor their spot is on: a figure with no floor named would be put on the last, a room)
        for t in list(f.get("people") or []) + list(f.get("trainer_spots") or []):
            if isinstance(t, str):
                on.setdefault(t, i)
    out = {k: v for k, v in m.items() if k not in ("art", "exits", "signs", "people", "trainer_spots", "links", "overheads", "parts", "inside", "stops", "rooms")}  # (boss_spot stays: the map's own)
    out.update(floors=floors, floor_names=names, figure_floors=on, room_floors=where, outdoor_floors=n0)
    return out


def art_recipe(m):
    """A route map recipe from one of our own maps (src/dungeon/art.py): its ground, its ways out (a letter
    each), what stands in the way (trees, fences, rocks, buildings, the sea), drawn in its own art. A map of
    floors ("floors": [{"art", "exits", "signs", "people"}...], Mt. Moon's) has a layout a floor, joined by
    its ladders (+ down, - up)."""
    if m.get("floors"):
        parts = [art_recipe(dict(m, floors=None, **f)) for f in m["floors"]]
        out = dict(parts[0])
        out["layout"] = [p["layout"][0] for p in parts]
        out["legend"] = {}
        for i, p in enumerate(parts):  # (each floor's own legend, under its own keys)
            out["layout"][i] = {"map": p["layout"][0]["map"], "legend": p["legend"]}
            for k in ("dive", "surface", "pool", "exit_order", "indoors"):  # (Dive: the seabed floor under this one, the surface over it, its own wild Pokemon)
                if m["floors"][i].get(k) is not None:
                    out["layout"][i][k] = m["floors"][i][k]
        out["floors"] = len(parts)
        out["exit_floors"] = {}
        for i, f in enumerate(m["floors"]):  # (a target on two floors: you come back on the lower-numbered one)
            for t in f.get("exits", {}).values():
                out["exit_floors"].setdefault(t, i)
        out["exit_floors_all"] = {}  # (the same place reached from several floors: each of them, in floor order: Victory Road's two mouths on Route 23)
        for i, f in enumerate(m["floors"]):
            for t in dict.fromkeys(f.get("exits", {}).values()):
                out["exit_floors_all"].setdefault(t, []).append(i)
        out["art"] = m
        out["descend"] = bool(m.get("descend"))
        return out
    from src.dungeon import art as _art
    grid, exits = m["art"], m.get("exits", {})
    doors = _art.doors(grid)
    kinds = m.get("buildings", {})
    signs = {t: i for i, t in enumerate(_art.signs(grid))}
    people = list(m.get("people", []))
    standers = list(m.get("trainer_spots", []))  # X: a trainer's own spot, by name, in reading order
    legend = {}
    rows = []
    for y, row in enumerate(grid):
        out = []
        for x, c in enumerate(row):
            if [x, y] == list(m.get("boss_spot") or ()):  # the area's boss asleep on this very tile (the map's "boss_spot": Snorlax on Route 12)
                ch = chr(0x2D80 + len(legend))
                legend[ch] = {"exit": "BOSS"}
                out.append(ch)
            elif c == "!":  # a sign: read it (sign:<its number>)
                ch = chr(0x2460 + signs[(x, y)])
                legend[ch] = {"decor": f"sign:{signs[(x, y)]}"}
                out.append(ch)
            elif c == "X" and standers:
                ch = chr(0x2700 + len(standers))
                legend[ch] = {"figure": f"trainer:{standers.pop(0)}"}
                out.append(ch)
            elif c == "N" and people:  # someone standing: a route option's figure, by its text (or a passer-by of the map's own: {"text", "action": "EVENT", ...})
                ch = chr(0x2500 + len(people))
                who = people.pop(0)
                legend[ch] = {"figure": who.get("text") if isinstance(who, dict) else who}
                out.append(ch)
            elif c == "D":  # a door: a way out (the building's own, or a gatehouse's), else walked into
                letter = doors.get((x, y))
                target = exits.get(letter) or (exits.get("D") if kinds.get(letter) == "gate" else None)
                through = (m.get("links") or {}).get(f"{x},{y}")  # (a gatehouse you walk through: in by this door, out by its other one: Route 12's)
                if through:
                    target = "WARP:%d:%d:%d" % tuple(through)
                ch = chr(0x2600 + len(legend))
                legend[ch] = {"exit": target} if target else {"decor": f"door:{kinds.get(letter, 'house')}"}
                out.append(ch)
            elif c in "+-":  # a ladder (a map of floors)
                out.append(c)
            elif c == "1":  # a passage to any other floor: the map's "links" {"x,y": [floor, x, y]}
                to = (m.get("links") or {}).get(f"{x},{y}")
                if to:
                    ch = chr(0x2D00 + len(legend))
                    legend[ch] = {"exit": "WARP:%d:%d:%d" % tuple(to[:3]) + (":fall" if "fall" in to[3:] else "")}  # (fall: a hole, Mt. Pyre's)
                    out.append(ch)
                else:
                    out.append(".")
            elif c in exits and not c.isupper():  # (a building's letter in exits: only its door leads out)
                out.append(c)
            elif c == '"':
                out.append(",")
            elif c == "o":  # open sea: Surf across it
                out.append("o")
            elif c in _art.CURRENTS:  # a current: sea that carries you its way
                ch = chr(0x2C00 + "[]{}".index(c))
                legend[ch] = {"surf": True, "current": list(_art.CURRENTS[c])}
                out.append(ch)
            elif c == ":":  # deep sea: Surf, and Dive
                legend["\u2c10"] = {"surf": True, "deep": True}
                out.append("\u2c10")
            elif c in _art.BRIDGES:  # a log bridge: over it along its length, under it across its width
                ch = chr(0x2C20 + "|;".index(c))
                legend[ch] = {"bridge": [abs(v) for v in _art.BRIDGES[c]]}
                out.append(ch)
            elif c == "x":  # a whirlpool: in the way until cleared with Whirlpool (whirl:<x>,<y>)
                ch = chr(0x2900 + len(legend))
                legend[ch] = {"decor": f"whirl:{x},{y}"}
                out.append(ch)
            elif c in "$/":  # a waterfall / a rock wall: in the way till you have Waterfall / Rock Climb
                ch = chr(0x2B00 + len(legend))
                legend[ch] = {"decor": f"{'falls' if c == '$' else 'climb'}:{x},{y}"}
                out.append(ch)
            elif c == "%":  # sheet ice: you slide across it
                out.append("%")
            elif c == "&":  # a hole in the floor: a boulder pushed in drops through (hole:<x>,<y>)
                ch = chr(0x2A00 + len(legend))
                legend[ch] = {"decor": f"hole:{x},{y}"}
                out.append(ch)
            elif c in "27'":  # a small tree (Cut), a steep muddy slope or round stones (the Bicycle): in the way till you have it (cut:, slope:, stones:<x>,<y>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": f"{ {'2': 'cut', '7': 'slope'}.get(c, 'stones')}:{x},{y}"}
                out.append(ch)
            elif c in "89":  # deep snow, marsh mud: ground you wade through (the walking is slowed, not the rules)
                out.append(".")
            elif c in "3456":  # a spin tile: the floor carries you its way till something stops you (Fuego Ironworks)
                ch = chr(0x2C30 + "3456".index(c))
                legend[ch] = {"current": [(-1, 0), (1, 0), (0, -1), (0, 1)]["3456".index(c)]}
                out.append(ch)
            elif c == "0":  # a cracked rock: in the way till you have Rock Smash (crack:<x>,<y>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": f"crack:{x},{y}"}
                out.append(ch)
            elif c == "?":  # a crate: the slide puzzle pushes it aside, no Strength needed (Orre's S.S. Libra: crate:<x>,<y>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": f"crate:{x},{y}"}
                out.append(ch)
            elif c == "b":  # a boulder: Strength, then the slide puzzle (boulder:<x>,<y>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": f"boulder:{x},{y}"}
                out.append(ch)
            elif c in _art.LEDGES:  # a ledge: in the way, but you hop over it its one way (ledge:<dx>,<dy>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": "ledge:%d,%d" % _art.LEDGES[c]}
                out.append(ch)
            elif c in _art.OPEN:
                out.append(".")
            elif c == "~":
                out.append("~")
            elif c == "T":
                out.append("#")  # (a tree: Headbutt works on it)
            else:
                out.append({"#": "F", "k": "F", "i": "F", "r": "R", "q": "R", "l": "R", "h": "R", "m": "R", "g": "R", "j": "R", "y": "R", "z": "R", "x": "R", "@": "R"}.get(c, "B"))
        rows.append("".join(out))
    legend.update({c: {"exit": t} for c, t in exits.items() if not c.isupper()})
    for c in "wu":  # (a way out across the sea: you surf onto it)
        if c in exits:
            legend[c] = {"exit": exits[c], "surf": True}
    for c in "<>^v":  # (one of the other ways out, where every tile of it lies out on the water: Route 124's four sides)
        spots = [(x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == c]
        if c in exits and spots and all(_art.at_sea(grid, x, y) for x, y in spots):
            legend[c] = {"exit": exits[c], "surf": True}
    legend.update({"+": {"exit": "STAIRS"}, "-": {"exit": "STAIRS_UP"}})
    legend.update({"F": {"decor": "fence"}, "R": {"decor": "rock"}, "B": {"decor": "building"}})
    return {"layout": [{"map": rows}], "legend": legend, "art": m, "fog": bool(m.get("fog")), "fixed": True,
            "style": "field", "floors": 1}  # (open, unless the map keeps its fog: the Pokemon Tower's)


def real_maps(game):
    """Routes walked on their real fan-game map (assets/walk_routes.json, dev/builders/build_walk_towns.py)."""
    if "all" not in _real_maps:
        path = os.path.join(game.assets.assets_dir or "", "walk_routes.json")
        try:
            with open(path, encoding="utf-8") as f:
                _real_maps["all"] = json.load(f)
        except (OSError, ValueError):
            _real_maps["all"] = {}
    return _real_maps["all"]


_real_maps = {}


def recipe_for(game, area_key):
    """DEFAULT, then the area's own recipe; an area without one gets its look from its battle type
    (a cave, a building, the sea...), ponds where you can fish, a smaller map for a small place.
    A route with a real map (Jordan, 11-06: Route 1 first) is walked on it: its picture, its grass, its
    ways out, wide open."""
    all_ = recipes(game)
    recipe = dict(all_.get("DEFAULT", {}))
    from src.states.overworld.walk_town import custom
    mine = custom(game).get(area_key)
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    if mine and area.get("area_type") != "town":  # our own map (Jordan, 11-06: the Johto pilot's Route 29)
        recipe.update(all_.get(area_key) or {})
        if mine.get("rooms"):  # (buildings you walk into: each room a floor of its own; everyone else stays outside)
            mine = with_rooms(mine)
            _on = mine["figure_floors"]
            for _o in list(area.get("route_menu") or []) + list(area.get("trainer_pool") or []):
                _t = _o.get("text") or _o.get("name")
                if _t and _t not in _on:
                    _on[_t] = 0 if mine["outdoor_floors"] == 1 else _on.get(_t, 0)
        recipe.update(art_recipe(mine), seed=area_key)
        recipe.pop("zones", None)
        if recipe.get("dark") or mine.get("dark"):  # (a dark cave: its fog stays, till Flash lights it)
            recipe["fog"], recipe["dark"] = True, True
        return recipe
    real = real_maps(game).get(area_key)
    if real and os.path.isfile(os.path.join(game.assets.assets_dir or "", "walk_routes", f"{area_key}.png")):
        recipe.update(all_.get(area_key) or {})
        recipe.update({"layout": [{"map": real["rows"]}], "legend": real["legend"], "image": area_key,
                       "fog": False, "fixed": True, "seed": area_key, "style": "field", "floors": 1})
        recipe.pop("zones", None)
        return recipe
    if area_key in all_:
        recipe.update(all_[area_key])
        return _building(recipe, area_key)
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    style = STYLE_OF.get(str(area.get("battle_type") or "").lower(), "field")
    name = str(area.get("route_name") or area_key).lower()
    if style == "cave" and str(area.get("battle_type")).lower() == "mountain" and "route" in name:
        style = "mountain"  # (a mountain route is out in the open: rocks and grass, not a cave)
    if style == "field" and ("forest" in name or "woods" in name or "jungle" in name):
        style = "forest"
    recipe["style"] = style
    if style == "building":
        recipe["size"] = [36, 24]
    if area.get("can_fish") and style != "sea":
        recipe["ponds"] = 2
    if not area.get("wild_pool_percentages") and not area.get("zone_pools"):
        recipe["wild"] = [0, 0]  # (a story place: trainers and figures only)
    return _building(recipe, area_key)


def _building(recipe, area_key):
    """A building is fixed (the same floors every visit, from its own seed) and has no fog (Jordan, 11-05)."""
    if recipe.get("style") == "building" or recipe.get("layout"):
        recipe.setdefault("fixed", True)
        recipe.setdefault("fog", False)
        recipe.setdefault("seed", area_key)
    return recipe


def enabled(game, area_key):
    """Every area but a town is a map (an area's recipe can say "enabled": false)."""
    if not area_key or area_key.startswith("_") or area_key == "DEFAULT":
        return False
    if (recipes(game).get(area_key) or {}).get("enabled") is False:
        return False
    if not getattr(game, "dungeon_routes", os.environ.get("SDL_VIDEODRIVER") != "dummy"):
        return False
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key)
    return bool(area) and area.get("area_type") != "town"


def dungeon_for(game, restore_data=None):
    """What PlayState(game, restore_data) should be here: the walk going on (back from a battle), a
    new DungeonState (still to be set up), or None for the old route screen."""
    key = game.story_manager.current_area_key
    if not enabled(game, key):
        return None
    cur = getattr(game, "dungeon_state", None)
    if restore_data and cur is not None and getattr(cur, "area_key", None) == key:
        return cur
    if (game.loader.area_data.get("STORY_PROGRESSION", {}).get(key) or {}).get("hyperspace"):
        from src.states.overworld.hyperspace import HyperspaceState  # (Hyperspace Lumiose's zones)
        return object.__new__(HyperspaceState)
    return object.__new__(DungeonState)


# ---------------------------------------------------------------- the screen
def ghost_figure():
    """A pale, see-through spirit with hollow eyes and a wavy hem (Jordan, 11-10: the Pokemon Tower's
    mysterious ghost, drawn in our own style: not any one Pokemon)."""
    w, h = TILE + 8, TILE + 26
    img = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, top, hem = w // 2, 6, h - 10
    rad = w // 2 - 6
    pygame.draw.circle(body, (236, 232, 255, 200), (cx, top + rad), rad)
    pygame.draw.rect(body, (236, 232, 255, 200), (cx - rad, top + rad, 2 * rad, hem - top - rad))
    wave = 4  # (a hem of four scallops)
    step = 2 * rad / wave
    for k in range(wave):
        pygame.draw.circle(body, (236, 232, 255, 200), (int(cx - rad + step * (k + 0.5)), hem), int(step / 2))
    for k in range(wave - 1):  # (the gaps between them)
        pygame.draw.circle(body, (0, 0, 0, 0), (int(cx - rad + step * (k + 1)), hem + int(step / 2)), int(step / 2))
    glow = pygame.Surface((w, h), pygame.SRCALPHA)  # (a soft purple haze around it)
    pygame.draw.ellipse(glow, (150, 110, 220, 60), (2, top - 2, w - 4, hem - top + 10))
    img.blit(glow, (0, 0))
    img.blit(body, (0, 0))
    eye_y = top + rad - 2
    for dx in (-rad // 2, rad // 2 - 2):
        pygame.draw.ellipse(img, (40, 20, 70, 230), (cx + dx - 4, eye_y - 7, 10, 15))
    pygame.draw.ellipse(img, (40, 20, 70, 200), (cx - 5, eye_y + 12, 10, 8))  # (a small, dark mouth)
    return img


class DungeonState(OverworldBattles, PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_dungeon_ready", False):  # the walk going on, back from a battle
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._dungeon_ready = True
        story = game.story_manager
        self.area_key = story.current_area_key
        self.recipe = recipe_for(game, self.area_key)
        if self.recipe.get("dark") and story.inventory.get("HM_FLASH", 0) > 0:  # (Flash lights a dark cave)
            self.recipe = dict(self.recipe, fog=False)
        if (self.recipe.get("art") or {}).get("fog") == "defog":  # (thick fog: you see only what is near, till Defog clears it: the Lost Tower)
            self.recipe = dict(self.recipe, fog=story.inventory.get("HM_DEFOG", 0) <= 0)
        game.dungeon_state = self

        self.exit_items = {}  # target area -> its route_menu entry (for the sign's name and its locks)
        for item in self.area_data.get("route_menu", []):
            target = item.get("target") or item.get("target_area")
            if item.get("action") in ("EXIT", "TRAVEL") and target and target not in self.exit_items:
                if self._exit_block(item, True) != "hidden":
                    self.exit_items[target] = item
        exits = list(self.exit_items)
        came = getattr(story, "last_area_key", None)
        nxt = self.area_data.get("next_area")
        if came in exits:
            entrance = came
        else:  # (a new game, a load, Fly...): start at the end away from where the route leads
            entrance = next((e for e in exits if e != nxt), exits[0] if exits else None)
        forwards = [e for e in exits if e != entrance] or ([nxt] if nxt else [])

        # an area in zones: a floor each (the Pokemon Tower's, the Seafoam Islands', the Safari Zone's)
        self.zones = [z.get("key") for z in self._zones()]
        recipe = dict(self.recipe)
        self.per_floor = max(1, int(recipe.get("zones_per_floor", 1) or 1))
        if self.zones and not self.area_data.get("zones_linear"):
            recipe["open"] = True  # (an open place: no stairs, openings in the edges between its areas)
        if self.zones:
            recipe["floors"] = -(-len(self.zones) // self.per_floor)
            recipe["floors"] += sum(1 for f in recipe.get("layout") or [] if isinstance(f, dict) and f.get("indoors"))  # (and its rooms: the Safari Zone's rest houses)
            if self.per_floor > 1:  # a wide floor: the areas side by side
                w, h = recipe.get("size", (40, 26))
                recipe["size"] = [w * self.per_floor, h]
        self.recipe = recipe
        n = max(1, int(recipe.get("floors", 1)))
        exits_by_floor, start = None, 0
        if recipe.get("exit_floors") and entrance in recipe["exit_floors"]:  # (our map of floors: in by its floor)
            start = recipe["exit_floors"][entrance]
            _all = (recipe.get("exit_floors_all") or {}).get(entrance) or []
            if len(_all) > 1 and core.ENTRANCE_COUNT >= len(_all):  # (in by the matching way: the far side has as many ways here as we have floors with one, or doors several tiles wide: Viridian Forest's gates)
                start = _all[min(core.ENTRANCE_INDEX * len(_all) // core.ENTRANCE_COUNT, len(_all) - 1)]
                core.ENTRANCE_INDEX = core.ENTRANCE_COUNT = 0
        if self.zones:
            by = {}
            for target, item in self.exit_items.items():
                at = self._floor_of(item, n - 1 if target != entrance else 0)
                ent, fwd = by.setdefault(at, [None, []])
                if target == entrance:
                    by[at][0] = target
                    start = at
                else:
                    fwd.append(target)
            exits_by_floor = {k: (v[0], v[1]) for k, v in by.items()}
            story.story_flags[f"zone_{self.area_key}"] = self.zones[start * self.per_floor]

        tides = (recipe.get("art") or {}).get("tides")  # (Shoal Cave: the sea in or out, by the clock: its high- or low-tide rooms)
        if tides:
            start = int(tides["high" if high_tide() else "low"].get(str(start), start))

        gate = self.recipe.get("gate")  # (a way out hidden till a switch is pushed: the Game Corner's stairs behind its poster)
        if gate and (entrance == gate.get("target") or any(story.story_flags.get(k) for k in gate.get("open_if", ()))):
            story.story_flags[gate["flag"]] = True  # (you've been through it already: an older save, or you came up it)
        pool = self.area_data.get("trainer_pool", [])
        cabins = set((self.recipe.get("art") or {}).get("cabin_trainers", []))  # (behind their doors: the S.S. Anne)
        trainers = [(i, t) for i, t in enumerate(pool) if story.trainer_on_map(self.area_key, i, t) and i not in cabins]
        spots = [s for s in self.recipe.get("tm_spots", []) if not story.story_flags.get(f"dungeon_tm_{s}")]
        loot = self.recipe.get("loot") or {}
        self.placed = []  # the route's buttons standing on the map as figures
        figures = [(self._figure_floor(item, n), item) for item in self._figure_items()]
        self.placed = [item for _f, item in figures]
        recipe = self.recipe
        lead = next((p for p in story.player_team if getattr(p, "current_hp", 1) > 0), None)
        if getattr(lead, "held_item", None) in itemlib.FEWER_WILD:  # (a Cleanse Tag on your lead: fewer wild Pokemon about)
            recipe = dict(recipe, wild=[max(1, w * 2 // 3) for w in (recipe.get("wild") or [4, 6])])
        self.run = core.Run(recipe, random.Random(), entrance=entrance, forwards=forwards,
                            make_wild=self._make_wild, trainers=trainers,
                            loot_for=self._floor_loot(loot), tm_spots=spots, figures=figures,
                            floor_of=lambda t: self._floor_of(t, None), exits_by_floor=exits_by_floor,
                            start_floor=start)

        at_edge = getattr(game, "arrive_edge", None)  # (out by an edge tile there: in beside its own partner here)
        game.arrive_edge = None
        if at_edge and at_edge[0] == entrance and at_edge[1] == self.area_key:
            p2, f = tuple(at_edge[2]), self.run.floor
            own = [e for e, v in f.exits.items() if v == entrance]
            t = min(own, key=lambda e: abs(e[0] - p2[0]) + abs(e[1] - p2[1])) if own else None  # (its partner, or the nearest to it)
            if t is not None:
                step = (1, 0) if t[0] == 0 else (-1, 0) if t[0] == f.w - 1 else (0, 1) if t[1] == 0 else (0, -1)
                inn = (t[0] + step[0], t[1] + step[1])
                if f.walkable(*inn) and inn not in f.exits:
                    self.run.player = inn
        self._sync_gate()
        if not self.run.fog and not story.story_flags.get(f"visited_{self.area_key}"):  # (dark places keep their own darkness)
            self.run.explore = True
            self.run.floor.seen = set()
            self.run.reveal()
        self.mode = "MAP"          # MAP, CHOICE, MATH, THROW, SPOTTED, CATCH (the route's catch screen)
        self.facing = (0, 1)
        self.anim = 0              # frames left of the step animation
        self.anim_from = self.run.player
        self.partner = self.run.player       # where your lead Pokemon walks (a step behind you)
        self.partner_from = self.run.player
        self.steps = 0                       # (which foot: the walking frames)
        self.walk_goal = None      # a tapped tile you're walking to
        self.encounter = None      # the wild Pokemon or trainer you met
        self.choice = 0            # MATH (0) or BATTLE (1) on the choice cards
        self.math_timer = 0
        self.throw_timer = 0
        self.throw_result = None
        self.spot_timer = 0
        self.pending = None        # ("wild" | "trainer", mover): a battle we're away at
        self.toast, self.toast_timer = "", 0
        self.scent_floor = -1      # the floor Sweet Scent was used on (once a floor)
        self.banner = 150          # the area's name, when you arrive
        # the Bug-Catching Contest: its Sport Balls, the turns left, your best catch (only one is kept)
        self.contest = ({"balls": CONTEST_BALLS, "turns": CONTEST_TURNS, "best": None, "score": 0}
                        if self.area_data.get("bug_contest") else None)
        _sg = self.area_data.get("safari_game")
        self.safari = ({"balls": int((_sg if isinstance(_sg, dict) else {}).get("balls", SAFARI_BALLS)),
                        "steps": int((_sg if isinstance(_sg, dict) else {}).get("steps", SAFARI_STEPS)), "hello": True}
                       if _sg and not self.contest else None)
        self._floor_surf = None
        self._floor_index = -1
        self._sprites = {}

    # ---- keys: the map takes the arrows (the keyboard highlight only works the catch screen)
    @property
    def uses_keyboard(self):
        return getattr(self, "mode", "MAP") != "CATCH"

    # ---------------------------------------------------------------- zones, figures
    def _floor_of(self, item, default):
        """The floor a trainer, way out or figure is on: its zone's, or the recipe's "figure_floors"
        {text: floor} (Navel Rock: Lugia below, Ho-Oh on top), else default."""
        if isinstance(item, dict) and item.get("_floor") is not None:  # (a passer-by of a map of floors: the floor it stands on)
            return int(item["_floor"])
        floors = dict(self.recipe.get("figure_floors") or {}, **((self.recipe.get("art") or {}).get("figure_floors") or {}))
        on = (floors.get(item.get("text"), floors.get(item.get("spot_name"), floors.get(item.get("name"))))) if isinstance(item, dict) else None  # (spot_name: one of several with the same name)
        if on is not None:
            return int(on)
        zone = item.get("zone") if isinstance(item, dict) else None
        if isinstance(zone, list):
            zone = zone[0] if zone else None
        if zone and zone in getattr(self, "zones", []):
            return self.zones.index(zone) // getattr(self, "per_floor", 1)
        return default

    def _figure_floor(self, item, n):
        """A figure's floor: its zone's (or figure_floors'); else, in an area of zones, a person or place on
        the first (the hub: the Isle of Armor's Master Dojo) and a legendary on the last; else the last."""
        n = min(n, int((self.recipe.get("art") or {}).get("outdoor_floors") or n))  # (never into a building's room: the rival on Route 22)
        default = 0 if self.zones and item.get("action") != "BOSS" else n - 1
        return self._floor_of(item, default)

    def _set_zone(self, index, x=None):
        """The zone you're in (its wild Pokemon, its picture in battle): floor index's, or on a wide floor
        the one whose part of it x is in."""
        if self.zones:
            self.game.story_manager.story_flags[f"zone_{self.area_key}"] = self.zones[self._zone_index(index, x)]

    def _zone_index(self, index, x=None, y=None):
        """Which zone floor index (at column x, on a wide floor) is. One of our own maps can lay its zones out
        any way ("zone_rects": [x, y, w, h] a zone, in the zones' order: the Safari Zone's four areas)."""
        rects = ((getattr(self, "recipe", None) or {}).get("art") or {}).get("zone_rects")
        lay = (getattr(self, "recipe", None) or {}).get("layout") or []
        if self.zones and index < len(lay) and isinstance(lay[index], dict) and lay[index].get("indoors"):  # (in a room: still the zone you came in from)
            now = self.game.story_manager.story_flags.get(f"zone_{self.area_key}")
            return self.zones.index(now) if now in self.zones else 0
        if rects and x is not None:
            yy = y if y is not None else (self.run.player[1] if hasattr(self, "run") else 0)
            for i, (rx, ry, rw, rh) in enumerate(rects):
                if rx <= x < rx + rw and ry <= yy < ry + rh:
                    return min(len(self.zones) - 1, i)
            return min(range(len(rects)), key=lambda i: abs(rects[i][0] + rects[i][2] / 2 - x)
                       + abs(rects[i][1] + rects[i][3] / 2 - yy))
        per = getattr(self, "per_floor", 1)
        part = 0
        if per > 1 and x is not None and hasattr(self, "run"):
            w = self.run.floors[index].w if index < len(self.run.floors) else self.recipe["size"][0]
            part = min(per - 1, max(0, x * per // max(1, w)))
        return min(len(self.zones) - 1, index * per + part)

    def _zone_name(self, i):
        return next((z.get("name") for z in self._zones() if z.get("key") == self.zones[i]), self.zones[i])

    def _note_area(self):
        """On a wide floor: crossing a gate line puts you in the next area (say so)."""
        if getattr(self, "per_floor", 1) <= 1 or not self.zones:
            return
        story = self.game.story_manager
        i = self._zone_index(self.run.index, self.run.player[0], self.run.player[1])
        if story.story_flags.get(f"zone_{self.area_key}") != self.zones[i]:
            self.game.story_manager.story_flags[f"zone_{self.area_key}"] = self.zones[i]
            self.flash(f"You entered {self._zone_name(i)}!", 120)

    def _figure_items(self):
        """The route's buttons that stand on the map now (as the route menu would show them)."""
        story = self.game.story_manager
        pool = self.area_data.get("trainer_pool", [])
        flags = story.story_flags
        out = []
        boss_in_way = any((self._gate(t) or ("",))[0] == "boss" for t in getattr(self, "exit_items", {})) or bool(self._boss_spot())
        _art_map = (getattr(self, "recipe", None) or {}).get("art") or {}
        indoors = {t for f in (_art_map.get("floors") or []) if f.get("indoors") for t in (f.get("people") or []) if isinstance(t, str)}
        for item in self.area_data.get("route_menu", []):
            if item.get("action") not in FIGURE_ACTIONS or (item.get("door") and item.get("text") not in indoors):
                continue  # (a house's option is through its door, not someone standing about; unless its room is built: then they stand in it)
            if boss_in_way and item.get("action") == "BOSS":
                continue  # (it sleeps across the way out: see _gate)
            if item.get("not_on_map"):
                continue  # (the map stands it there itself, as a stand-in: the Cave of Origin's legend on its rock)
            fc = item.get("flag_condition")
            if fc:
                parts = fc.split()
                if parts[0] == "not" and len(parts) == 2:
                    if flags.get(parts[1]):
                        continue
                elif not flags.get(parts[0]):
                    continue
            # (its zone's trainers, else the area's.) A boss (a legendary) doesn't wait for them here
            # (Jordan, 11-05): finding it on the map is the task.
            zone = self._floor_of(item, None)
            left = item.get("action") != "BOSS" and any(
                not story.is_trainer_defeated(self.area_key, i)
                and (zone is None or self._floor_of(t, None) in (None, zone)) for i, t in enumerate(pool))
            rematch = item.get("action") == "BOSS" and flags.get(f"legend_rematch_{self._boss_flag_for(item)}")
            cond = item.get("condition")
            if isinstance(cond, list):  # (on the map there are no rounds to play first: it's there when the story says so,
                cond = [c for c in cond if c != "can_exit"]  # not after two wild battles: the Cave of Origin's Primal)
            elif cond == "can_exit":
                cond = None
            if rematch or self._check_route_condition(cond, left, item):
                out.append(item)
        # the map's own passers-by: people who just talk (Jordan, 11-12), each on its own floor
        for _i, _f in (enumerate(_art_map["floors"]) if _art_map.get("floors") else [(None, _art_map)]):
            _keep = self.__dict__.setdefault("_floor_folk", {})  # (the same dict each time: figures are kept by identity)
            out += [_keep.setdefault(id(p), dict(p, _floor=_i)) if _i is not None else p
                    for p in (_f.get("people") or []) if isinstance(p, dict) and p.get("text") and self.npc_shown(p)]
        return out + self._arrival_figures()

    def _arrival_figures(self):
        """A story battle that a route starts when you arrive (the rival on Route 22, on Nugget Bridge, in
        the Pokemon Tower) stands on the map instead, while it would start: walk into it."""
        events = self.area_data.get("on_enter_event")
        out = []
        for ev in (events if isinstance(events, list) else [events] if events else []):
            if not isinstance(ev, dict) or ev.get("type") != "trainer_battle":
                continue
            if ev.get("flag_check") and self.game.story_manager.story_flags.get(ev["flag_check"]):
                continue
            if ev.get("condition") and not self._check_route_condition(ev["condition"], False):
                continue
            key = id(ev)
            self._arrivals = getattr(self, "_arrivals", {})
            out.append(self._arrivals.setdefault(key, {"action": "ARRIVAL", "event": ev, "zone": ev.get("zone"),
                                                       "text": (ev.get("trainer") or {}).get("name", "")}))
        return out

    def _sync_figures(self):
        """After a battle or an event: figures whose time has come turn up, and finished ones leave."""
        if not hasattr(self, "run"):
            return
        story = self.game.story_manager
        pool = self.area_data.get("trainer_pool", [])
        self._mark_route_progress(any(not story.is_trainer_defeated(self.area_key, i) for i in range(len(pool))))
        now = self._figure_items()
        _sc = getattr(self, "_scene_run", None)
        _held = _sc.playing[2] if _sc is not None and _sc.playing else None
        if _held is not None:  # (someone a scene is still playing out with stays till it ends)
            now += [m.payload for m in self.run.floor.movers if getattr(m, "motion", None) is _held and m.kind == "figure"
                    and not any(m.payload is j for j in now)]
        for item in [i for i in self.placed if not any(i is j for j in now)]:
            self.run.drop_figure(item)
        for item in [i for i in now if not any(i is j for j in self.placed)]:
            self.run.add_figure(self._figure_floor(item, self.run.n_floors), item)
        self.placed = now
        self._sync_gate()

    def _boss_spot(self):
        """The tile the area's boss sleeps on (the map's "boss_spot"), while it is still there."""
        spot = (self.recipe.get("art") or {}).get("boss_spot")
        boss = self.area_data.get("area_boss") or {}
        if not spot or not boss or self.game.story_manager.story_flags.get(boss.get("victory_flag")):
            return None
        return tuple(spot)

    def _sync_boss_spot(self):
        if (self.recipe.get("art") or {}).get("boss_spot") and hasattr(self, "run") and not self._boss_spot():
            for t in [t for t, v in self.run.floor.exits.items() if v == "BOSS"]:  # (beaten: the way is clear)
                del self.run.floor.exits[t]

    def _sync_gate(self):
        self._sync_boss_spot()
        """The recipe's "gate" (flag, tile, target): a way out that is plain wall till its flag is set (the stairs
        behind the Game Corner's poster)."""
        gate = self.recipe.get("gate")
        if not gate or not hasattr(self, "run"):
            return
        f, t = self.run.floor, tuple(gate["tile"])
        is_open = bool(self.game.story_manager.story_flags.get(gate["flag"]))
        if is_open != (t in f.exits):
            if is_open:
                f.tiles[t[1]][t[0]] = core.FLOOR
                f.exits[t] = gate["target"]
            else:
                f.tiles[t[1]][t[0]] = core.WALL
                f.exits.pop(t, None)
            self._floor_surf = None

    def push_switch(self):
        """The gate's switch (a poster on the wall): pushed once, it opens the way."""
        gate = self.recipe.get("gate") or {}
        flags = self.game.story_manager.story_flags
        if not self._ready():
            return
        self.walk_goal = None
        if flags.get(gate.get("flag")):
            self.say(gate.get("done") or ["The switch is pushed in."])
            return
        flags[gate["flag"]] = True
        self._sync_gate()
        self.say(gate.get("lines") or ["You push the switch."])

    def _stand_in_img(self, look, bar):
        """A story stand-in's picture (a map's "barred" look): "sheet:<walking sheet>" (bar "face" u d l r, "march": running
        on the spot), "ow:<folder>:<thing>" (a real game's own thing: a bag, a boat), "mon:<species>". None if there is none."""
        if look.startswith("ribbon:"):  # (a portrait of your Pokemon that won it: Lilycove Museum's paintings)
            p = self.game.story_manager.ribbon_holder(look[7:])
            if p is None:
                return None
            from src.minigames.base import icon
            return icon(self.game, int(p.id), TILE + 6)
        fc = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}.get(bar.get("face", "d"), (0, 1))
        fr = (1, 0, 3, 0)[(pygame.time.get_ticks() // 120) % 4] if bar.get("march") else 0
        if look.startswith("mon:"):
            from src.minigames.base import icon

            class _Mon:  # (just what the walking sheet needs)
                id, form, is_shiny, gender = int(look[4:]), "normal", False, None
            return (self._follower_img(_Mon(), fc) if bar.get("face") else None) or icon(self.game, int(look[4:]), TILE + 6)
        if look.startswith("sheet:"):   # ("big": a legend standing two tiles tall, the Cave of Origin's Primal one)
            return self._sheet_frame(scene_sheet(self.game, look[6:]), fc, frame=fr, height=self.JUMBO if bar.get("big") else None)
        if look.startswith("ow:"):
            from src.dungeon import art as _art
            fold, name = look[3:].split(":", 1)
            return _art._ow(fold, name, TILE)
        return None

    # ---------------------------------------------------------------- people who move (src/dungeon/npc.py)
    def _motion(self, m):
        """A figure's or a trainer's Motion (made the first time it's asked for: its way of moving is the map's
        "moves" at the spot it stands on, a trainer keeps the way it already faces)."""
        if m.kind not in ("figure", "trainer"):
            return None
        mo = getattr(m, "motion", None)
        if mo is None:
            from src.dungeon import npc
            here = self._here_art() if self.run.recipe.get("art") else {}
            mo = m.motion = npc.Motion((m.x, m.y), npc.spec_at(here.get("moves"), (m.x, m.y)), seed=self.area_key, facing=tuple(m.facing or (0, 1)))
            m.facing = mo.facing
        return mo

    def _npc_free(self, t, mover=None):
        """Can a person step onto t: open ground nothing stands on (no way out, item, sign), not you."""
        f = self.run.floor
        x, y = t
        if not (0 <= x < f.w and 0 <= y < f.h) or not f.walkable(x, y) or f.tile(x, y) == core.SURF or t in f.exits or t in f.items                 or t in f.tm_spots or t in f.decor:
            return False
        if t == tuple(self.run.player) or (self.anim > 0 and t == tuple(self.anim_from)):
            return False
        return not any(o is not mover and (t == (o.x, o.y) or (getattr(o, "motion", None) is not None and t == o.motion.frm and o.motion.moving()))
                       for o in f.movers)

    def _copy_step(self, dx, dy):
        """You stepped: anyone who copies your steps takes theirs (Route 119's Mimic Circle; a "copy" person, npc.py)."""
        f = self.run.floor
        for m in list(f.movers):
            mo = self._motion(m)
            if mo is None or mo.kind != "copy" or mo.hold:
                continue
            free = (lambda t, m=m, mo=mo: self._npc_free(t, m) and (not mo.grass or f.tile(*t) == core.GRASS or t == mo.home))  # (their own spot too)
            if mo.copy(dx, dy, free):
                m.x, m.y = mo.pos
                m.facing = mo.facing

    def _npc_tick(self):
        f = self.run.floor
        for m in list(f.movers):
            mo = self._motion(m)
            if mo is None:
                continue
            if mo.kind == "still" and mo.idle() and mo.emote == 0 and not mo.hold:
                continue
            turned = mo.tick(lambda t, m=m: self._npc_free(t, m))
            if mo.gone:  # (walked off the map: gone for this visit)
                self.run.remove(m)
                continue
            m.x, m.y = mo.pos
            m.facing = mo.facing
            if m.kind == "trainer" and (turned or not mo.idle()) and self._ready() and self.run._sees(m):
                self._meet_trainer(m, spotted=True)  # (it turned your way, or walked into view: it's seen you)
                return
        sc = self._scenes()
        if sc.busy():
            sc.tick()
        elif self._ready() and not self.walk_goal:
            sc.check()

    def _scenes(self):
        from src.dungeon import npc
        key = (id(self.run.floor), self.run.index)
        if getattr(self, "_scene_key", None) != key:
            here = self._here_art() if self.run.recipe.get("art") else {}
            self._scene_key, self._scene_run = key, npc.Scenes(here.get("scenes"), self)
        return self._scene_run

    def _scene_mover(self, who):
        for m in self.run.floor.movers:
            if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == who:
                return m
            if m.kind == "trainer" and str(who).startswith("trainer:") and who[8:] in ((m.payload[1] or {}).get("name"), (m.payload[1] or {}).get("spot_name")):  # (spot_name: a villain renamed for the version)
                return m
        return None

    # (the scene runner's host)
    def npc_person(self, who):
        m = self._scene_mover(who)
        return self._motion(m) if m is not None else None

    def npc_player(self):
        return tuple(self.run.player)

    def npc_passable(self, t, mo):
        m = next((o for o in self.run.floor.movers if getattr(o, "motion", None) is mo), None)
        return self._npc_free(t, m)

    def npc_shown(self, scene):
        story = self.game.story_manager
        fc = scene.get("flag_condition")
        if fc:
            parts = fc.split()
            if (len(parts) == 2 and parts[0] == "not" and story.story_flags.get(parts[1])) or (len(parts) == 1 and not story.story_flags.get(parts[0])):
                return False
        return not scene.get("condition") or self._check_route_condition(scene["condition"], False)

    def npc_flag(self, name):
        self.game.story_manager.story_flags[name] = True

    def npc_flagged(self, name):
        return bool(self.game.story_manager.story_flags.get(name))

    def npc_say(self, lines, then):
        from src.states.overworld.common import _fill_names
        self.say([_fill_names(self.game, line) for line in lines], then=then)

    def npc_run(self, who):
        m = self._scene_mover(who)
        if m is None:
            return
        self._scene_lock = False
        if m.kind == "trainer":
            self._meet_trainer(m)
        else:
            self._use_figure(m)

    def npc_push(self, dx, dy):
        self._scene_lock = False
        self.walk_goal = None
        self.step(dx, dy)

    def npc_event(self, key, then):
        from src.states.overworld.common import _run_story_event
        shown = []

        def show(lines):
            shown.append(1)
            self.npc_say(lines, then)
        _run_story_event(self, key, lambda c: self._check_route_condition(c, False), show)
        if not shown:  # (a battle or a scene of its own began instead: the scene carries on once you're back)
            then()

    def _actor_img(self, sheet, facing, frame):
        """A scene's walker: a person's walking sheet, or a Pokemon ("mon:<species>": its following sprite)."""
        if str(sheet).startswith("mon:"):
            class _Mon:  # (just what the walking sheet needs)
                id, form, is_shiny, gender = int(str(sheet)[4:]), "normal", False, None
            return self._follower_img(_Mon(), tuple(facing))
        return self._sheet_frame(sheet, facing, frame=frame)

    def npc_heal(self):
        from src.states.overworld.area_transition import heal_team
        heal_team(self.game)

    def npc_sheet(self, token):
        return scene_sheet(self.game, token)

    def npc_follow(self, t):
        t, p = tuple(t), tuple(self.run.player)
        if abs(t[0] - p[0]) + abs(t[1] - p[1]) != 1:
            return
        self.facing = (t[0] - p[0], t[1] - p[1])
        self.anim_from, self.anim = p, STEP_FRAMES
        self.partner_from, self.partner = self.partner, p
        self.run.player = t

    def npc_lock(self, on):
        self._scene_lock = on
        if on:
            self.walk_goal = None

    def npc_open(self, t):
        f = self.run.floor
        return 0 <= t[0] < f.w and 0 <= t[1] < f.h and f.walkable(*t) and not f.mover_at(*t)

    def npc_face_player(self, spot):
        p = self.run.player
        self.facing = (max(-1, min(1, spot[0] - p[0])), max(-1, min(1, spot[1] - p[1])))

    def npc_edge(self, mo):
        f = self.run.floor
        return min(f.exits, key=lambda t: abs(t[0] - mo.pos[0]) + abs(t[1] - mo.pos[1]), default=None)

    def _use_figure(self, mover):
        self.walk_goal = None
        mo = getattr(mover, "motion", None)
        if mo is not None:  # (they stop and turn to you)
            mo.path = []
            mo.face(self.run.player)
            mover.facing = mo.facing
            mo.hold = 150
        item = mover.payload
        if isinstance(item, dict) and self._scenes().on_talk(item.get("text")):  # (a scene of theirs plays instead)
            return
        if item.get("action") == "GAME_CORNER":
            self.talk_to_clerk()
            return
        if item.get("action") == "BUG_CONTEST":  # the officer at National Park's gate
            contest_entry(self)
            return
        if item.get("action") == "ARRIVAL":  # the rival waiting on the route
            self.trigger_scripted_on_enter_battle(item["event"])
            return
        callback = self._get_route_callback(item)
        callback()

    # ---------------------------------------------------------------- fishing and Headbutt
    def _menu_item(self, action):
        """The route's button for an action, if it would show (FISH needs a rod, HEADBUTT the helmet)."""
        for item in self.area_data.get("route_menu", []):
            if item.get("action") == action and self._check_route_condition(item.get("condition"), False, item):
                return item
        return None

    def _beside(self, kind):
        """The tile next to you of a kind ("water": a pond, or the sea; "tree"), or None. The way you face first."""
        f = self.run.floor
        px, py = self.run.player
        order = [self.facing] + [d for d in core.DIRS if d != self.facing]
        for dx, dy in order:
            t = f.tile(px + dx, py + dy)
            if kind == "water" and (t in (core.WATER, core.SURF) or (f.style == "sea" and f.walkable(px + dx, py + dy))):
                return px + dx, py + dy
            if kind == "tree" and t == core.WALL and f.style in TREE_STYLES and f.inside(px + dx, py + dy) \
                    and (px + dx, py + dy) not in f.decor:
                return px + dx, py + dy
            if kind.startswith("decor:") and f.decor.get((px + dx, py + dy)) == kind[6:]:
                return px + dx, py + dy
        return None

    def _act_here(self):
        """FISH or HEADBUTT, if you're beside water or a tree and can; TALK at the Game Corner's counter,
        PLAY SLOTS at a machine: (label, action), else None."""
        if self._beside("decor:counter") and self._clerk():
            return "TALK", self.talk_to_clerk
        plan = self._plan()
        if plan.get("dive") is not None and self.run.player in getattr(self.run.floor, "deep", ()):
            return "DIVE", self.dive_here
        if plan.get("surface") is not None:
            return "SURFACE", self.surface_here
        if self._beside("decor:slot"):
            return "PLAY SLOTS", self.play_slots
        if (self.recipe.get("gate") or {}).get("switch") and self._beside("decor:" + self.recipe["gate"]["switch"]):
            return "CHECK", self.push_switch
        if self._beside("water") and self._menu_item("FISH"):
            return "FISH", self.fish_here
        if self._beside("tree") and self._menu_item("HEADBUTT"):
            return "HEADBUTT", self.headbutt_here
        return None

    # ---------------------------------------------------------------- Dive (Hoenn's deep sea)
    def _plan(self):
        """This floor's own plan (a drawn map's: its Dive floor, its surface, its wild pool), else {}."""
        layout = self.run.recipe.get("layout") if hasattr(self, "run") else None
        return layout[self.run.index] if layout and self.run.index < len(layout) else {}

    def dive_here(self):
        """On deep, dark sea: Dive to the seabed floor, the same spot below."""
        if not self._ready():
            return
        if self.game.story_manager.inventory.get("HM_DIVE", 0) <= 0:
            self.say(["The sea is deep and dark here.", "A Pokemon could DIVE down to the seabed."])
            return
        to, spot = self._plan()["dive"], self.run.player
        below = self.run.made(to)
        if not below.walkable(*spot) or below.mover_at(*spot):
            self.flash("There's rock right under you here.", 100)
            return
        self.walk_goal = self.sliding = None
        self.run.jump_floor(to, spot)
        self.partner = self.partner_from = spot
        self._floor_surf = None
        self.flash("You dived down to the seabed!", 110)

    def surface_here(self):
        """On the seabed: back up to the sea right above you (only where there's open water overhead)."""
        if not self._ready():
            return
        to, spot = self._plan()["surface"], self.run.player
        above = self.run.made(to)
        if above.tile(*spot) != core.SURF or above.mover_at(*spot) or spot in above.exits:
            self.flash("There's no open water above you here.", 100)
            return
        self.walk_goal = self.sliding = None
        self.run.jump_floor(to, spot)
        self.partner = self.partner_from = spot
        self._floor_surf = None
        self.flash("You came up to the surface!", 110)

    # ---------------------------------------------------------------- the Game Corner
    def _clerk(self):
        """The Game Corner clerk (behind the counter): its figure's button, or None."""
        return next((m.payload for m in self.run.floor.movers
                     if m.kind == "figure" and m.payload.get("action") == "GAME_CORNER"), None)

    def talk_to_clerk(self):
        """Across the counter: the Game Corner's own menu (the games, coins, prizes); LEAVE comes back here."""
        if self._ready() and self._clerk():
            from src.states.systems import GameCornerState
            self.walk_goal = None
            self.game.change_state(GameCornerState(self.game, self))

    def play_slots(self):
        if not self._ready():
            return
        if self.game.story_manager.inventory.get("COIN_CASE", 0) <= 0:
            self.say(["The machine needs coins. You'll want a COIN CASE to hold them."])
            return
        from src.states.game_corner import SlotsState
        self.walk_goal = None
        self.game.change_state(SlotsState(self.game, self, background=self.game.assets.get_background(
            "celadon_game_corner.png")))

    def fish_here(self):
        if self._ready() and self._beside("water") and self._menu_item("FISH"):
            self.walk_goal = None
            self.action_fish()  # the route's own: a bite, a battle, then back to the map

    def headbutt_here(self):
        if self._ready() and self._beside("tree") and self._menu_item("HEADBUTT"):
            self.walk_goal = None
            self.action_headbutt()

    # ---------------------------------------------------------------- wild Pokemon
    def _make_wild(self, rng, spot=None):
        """A wild Pokemon for the area (on a wide floor: for the part of it where it will stand)."""
        story = self.game.story_manager
        flag = f"zone_{self.area_key}"
        keep = story.story_flags.get(flag)
        if spot is not None and getattr(self, "per_floor", 1) > 1 and self.zones:
            index = self.run.index if hasattr(self, "run") else 0  # (the first floor, while the walk is made)
            story.story_flags[flag] = self.zones[self._zone_index(index, spot[0], spot[1])]
        try:
            return self._wild_for_pool(rng)
        finally:
            if keep is not None:
                story.story_flags[flag] = keep

    def _wild_for_pool(self, rng):
        area = self.area_data
        layout = self.recipe.get("layout") if isinstance(getattr(self, "recipe", None), dict) else None
        own = layout[core.CURRENT_FLOOR].get("pool") if layout and core.CURRENT_FLOOR < len(layout) else None
        if own:  # (this floor's own Pokemon: the seabed's)
            area = {k: v for k, v in dict(area, wild_pool_percentages=own).items() if k != "zone_pools"}
        pool = self._get_wild_pool(area)
        if not pool:
            return None
        pid = int(Utils.weighted_random_choice(pool))
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)
        if not raw or raw.get("id", 0) == 0:
            return None
        p = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, p, self.area_key)
        return p

    # ---------------------------------------------------------------- coming and going
    def start(self):
        for el in [self.dialogue_box] + list(self.hud_buttons) + [self.btn_flee, self.btn_yes, self.btn_no]:
            if el not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(el)
        if self.mode != "CATCH":
            self.btn_flee.set_visibility(False)
        pygame.event.clear()
        self.game.story_manager.story_flags[f"visited_{self.area_key}"] = True
        self.is_resuming = False
        # a starter chosen out on a map (REGION_START "starter_area": Sinnoh's Lake Verity, walked to by Route 201): the
        # professor's bag, then the wild Pokemon to drive off, then home (the old route screen's own event, here too)
        if (self.area_data.get("starter_event") and self.game.story_manager.starter_on_route(self.game.story_manager.get_current_region()) == self.area_key
                and self.mode == "MAP"):
            if self._starter_walk_up():
                return
            if self._starter_return():
                return
            self.route_starter_event()

    def _back_from_battle(self):
        """Back on the map after a battle: the wild Pokemon is gone (beaten, caught or left behind),
        a beaten trainer too."""
        kind, mover = self.pending or (None, None)
        self.pending = None
        self._ow_foe = None
        if mover is not None:
            if kind == "wild":
                self.run.remove(mover)
            elif kind == "trainer":
                idx = mover.payload[0]
                if self.game.story_manager.beaten_today(self.area_key, idx):
                    self.run.remove(mover)
                else:  # lost (or ran out of Pokemon): it looks away, so you can get past
                    mover.facing = (-mover.facing[0], -mover.facing[1])
        self.encounter = None
        self.mode = "MAP"
        self.walk_goal = None
        self._sync_figures()

    def show_progression_menu(self):
        """The route's catch screen (or a battle) is done: back to the map."""
        self.is_progression_paused = True
        self.p_data = [None] * 3
        self.catch_selection_active = False
        self.selected_catch_idx = -1
        self.pause_timer = 0
        self.btn_flee.set_visibility(False)
        self.dialogue_box.visible = False
        self.mode = "MAP"
        self._sync_figures()

    def _leave(self, target):
        self.game.dungeon_state = None
        from src.coop import travel
        travel.passing(self.game, lambda: self.action_exit_route(target))

    # ---------------------------------------------------------------- talking
    def say(self, lines, then=None):
        def done():
            self.dialogue_box.visible = False
            if then:
                then()
        self.dialogue_box.reset(lines if isinstance(lines, list) else [lines])
        self.dialogue_box.callback = done

    def flash(self, text, frames=90):
        self.toast, self.toast_timer = text, frames

    # ---------------------------------------------------------------- a step
    def _ready(self):
        return self.mode == "MAP" and self.anim == 0 and not self.dialogue_box.visible and not getattr(self, "_scene_lock", False)

    braking = False  # (on a slope: you've braked (WAIT), and stay put till you move again)

    def _here_art(self):
        m = self.run.recipe.get("art") or {}
        if not m.get("floors"):
            return m
        f = m["floors"][self.run.index]
        if f.get("indoors") or not m.get("room_floors"):
            return f
        return dict({k: m[k] for k in ("cycling", "downhill") if k in m}, **f)  # (a route with rooms: its own rules are the map's, outdoors only. The Cycling Road's gatehouses)

    def _downhill(self, t=None):
        """Is this tile on a slope that pulls you south (the map's "downhill": [first row, last row]; the Cycling Road)?"""
        rows = self._here_art().get("downhill")
        x, y = t or self.run.player
        return bool(rows) and rows[0] <= y <= rows[1] and self.run.floor.tile(x, y) != core.SURF

    def _cycling(self, t=None):
        """Are you riding here (the map's "cycling": true, or [x0, y0, x1, y1]; with the Bicycle)?"""
        area = self._here_art().get("cycling")
        if not area or self.game.story_manager.inventory.get("BICYCLE", 0) <= 0:
            return False
        x, y = t or self.run.player
        return area is True or (area[0] <= x <= area[2] and area[1] <= y <= area[3])

    def _roll(self):
        """On a slope, not braking: one tile further downhill, if the way is clear (never into someone or something)."""
        if self.braking or self.walk_goal or not self._downhill():
            return
        f, (x, y) = self.run.floor, self.run.player
        to = (x, y + 1)
        ledge = str(f.decor.get(to, "")) == "ledge:0,1"
        if ledge:
            over = (x, y + 2)
            if not (f.walkable(*over) and f.mover_at(*over) is None):
                return
        elif not f.walkable(*to) or f.mover_at(*to) is not None or (f.tile(*to) == core.SURF and not self._on_surf()):
            return
        self._rolling = True
        try:
            self.step(0, 1)
        finally:
            self._rolling = False

    def _can_surf(self):
        return self.game.story_manager.inventory.get("HM_SURF", 0) > 0

    def _on_surf(self, t=None):
        f = self.run.floor
        return f.tile(*(t or self.run.player)) == core.SURF

    hop = False  # (mid-hop over a ledge: you arc through the air)
    sliding = None  # (on sheet ice: the way you're sliding, till something stops you)

    def _stop_tiles(self):
        """This floor's stop tiles (its map's "stops" [[x, y], ...]): where a spin tile's slide ends."""
        art = (getattr(self.run, "recipe", None) or {}).get("art") or {}
        floors = art.get("floors")
        src = floors[self.run.index] if floors and 0 <= self.run.index < len(floors) else art
        key = (id(src), self.run.index)
        if getattr(self, "_stops_key", None) != key:
            self._stops_key, self._stops = key, {tuple(t) for t in (src.get("stops") or [])}
        return self._stops

    def step(self, dx, dy):
        if not self._ready():
            return
        if self.sliding and (dx, dy) != self.sliding:  # (no turning on the ice)
            return
        from src.coop import roster
        if roster.host_tethered(self.game, (self.run.player[0] + dx, self.run.player[1] + dy)):
            self.walk_goal = None
            self.flash("Your team fainted: stay close to a friend.")
            return
        if roster.world.occupied(self.game, (self.run.player[0] + dx, self.run.player[1] + dy)):
            self.walk_goal, self.facing = None, (dx, dy)  # (a friend or their Pokemon is standing there)
            return
        self.facing = (dx, dy)
        if not getattr(self, "_rolling", False):
            self.braking = False  # (you moved yourself: off the brake)
        self._clear_boulders()  # (one already pushed aside isn't in the way)
        before = self.run.player
        to = (before[0] + dx, before[1] + dy)
        if self._on_surf(to) and not self._on_surf(before) and not self._can_surf():
            self.walk_goal = None  # (the open sea: Surf it, Routes 19-21)
            self.flash("The sea is deep. You need Surf to cross it!", 100)
            return
        hopped = False
        if str(self.run.floor.decor.get(to, "")) == f"ledge:{dx},{dy}":  # (a ledge, from its high side: hop over it)
            over = (to[0] + dx, to[1] + dy)
            if self.run.floor.walkable(*over) and self.run.floor.mover_at(*over) is None:
                self.run.player = to
                hopped = True
        events = self.run.step(dx, dy)
        if hopped and self.run.player == to:  # (couldn't land after all)
            self.run.player = before
        self.hop = (hopped or tuple(self.run.player) in getattr(self, "_stones", ()) or tuple(before) in getattr(self, "_stones", ()))             and self.run.player != before  # (a ledge; onto, along and off the round stones, hopping on the Bicycle)
        leaving = any(ev[0] in ("exit", "stairs", "stairs_up") for ev in events)
        on_ice = self.run.player != before and self.run.player in getattr(self.run.floor, "ice", ())
        self.sliding = (dx, dy) if on_ice and not leaving else None
        swept = getattr(self.run.floor, "current", {}).get(self.run.player) if self.run.player != before and not leaving else None
        if swept and (self.run.player[0] + swept[0], self.run.player[1] + swept[1]) != before:
            self.sliding = swept  # (a sea current: it carries you its own way, whichever way you came onto it; never straight back and forth)
        if self.sliding and tuple(self.run.player) in self._stop_tiles():
            self.sliding = None  # (a stop tile: a spin tile's slide ends here: the Rocket Hideout's maze)
        if self.sliding:
            self.walk_goal = None
        if self.run.player != before:
            self.anim_from, self.anim = before, STEP_FRAMES
            _m = self.run.recipe.get("art") or {}
            _g = (_m["floors"][self.run.index]["art"] if _m.get("floors") else _m.get("art")) or []
            _x, _y = self.run.player
            if 0 <= _y < len(_g) and 0 <= _x < len(_g[_y]) and _g[_y][_x] in "89":  # (deep snow, marsh mud: each step takes twice as long)
                self.anim = STEP_FRAMES * 2
            if dy < 0 and self._downhill(before):  # (pedalling up the Cycling Road's slope: each step takes twice as long)
                self.anim = STEP_FRAMES * 2
            self.partner_from, self.partner = self.partner, before  # it steps where you were
            self.steps += 1
            self._copy_step(dx, dy)
            self._note_area()
            self._contest_tick()
            if getattr(self, "safari", None) and self.safari["steps"] > 0:
                self.safari["steps"] -= 1
        self._handle(events)

    def wait_turn(self):
        if self.mode == "MAP" and not self.dialogue_box.visible and self._downhill() and not self.braking:
            self.braking = True  # (the brake, at any moment, mid-roll too: you stay in place on the slope till you move again)
            self.walk_goal = None
            self.flash("You brake, and hold still on the slope.", 80)
            return
        if self._ready():
            self._contest_tick()
            self._handle(self.run.wait())

    def _handle(self, events):
        if getattr(self.game, "coop_host_down", False):  # (nothing to fight with: nothing starts a fight)
            events = [ev for ev in events if ev[0] not in ("ambush", "spotted") and not (ev[0] == "bump" and ev[1].kind in ("wild", "trainer"))]
        for ev in events:
            kind = ev[0]
            if kind == "blocked":
                self.walk_goal = None
                self._read_sign()  # (walked into a sign: read it)
            elif kind == "item":
                self._pick_up(ev[1])
            elif kind == "tm":
                self.walk_goal = None
                self._pick_up_tm(ev[1])
            elif kind == "exit":
                self.walk_goal = None
                self._try_exit(ev[1])
                return
            elif kind == "stairs":
                self.walk_goal = None
                if self._stairs_blocked():  # (Hyperspace: not until the floor is clear)
                    self._step_back()
                    return
                from src.coop import travel
                if travel.held(self.game, self._floor_name(self.run.index + 1), lambda: self._handle([ev]), self._step_back):
                    return
                self.say([self._stairs_line(self.run.index + 1)], then=self._descend)
                return
            elif kind == "warp":  # a passage to another floor (a map's "links")
                self.walk_goal = None
                _i, _x, _y = (int(v) for v in ev[1].split(":")[1:4])
                if ev[1].endswith(":fall"):  # (a hole in the floor: down you go, onto the spot below)
                    self.say(["Whoa! You fell through a hole in the floor!"], then=lambda: self._warp(_i, _x, _y, land=True))
                elif _i == self.run.index or self._indoors(_i) or self._indoors(self.run.index):  # (a warp panel: across the same floor; a house's door or mat: straight in or out)
                    self._warp(_i, _x, _y)
                else:
                    self.say([f"You went through to {self._floor_name(_i)}."], then=lambda: self._warp(_i, _x, _y))
                return
            elif kind == "stairs_up":
                self.walk_goal = None
                from src.coop import travel
                if travel.held(self.game, self._floor_name(self.run.index - 1), lambda: self._handle([ev]), self._step_back):
                    return
                self.say([self._stairs_line(self.run.index - 1)], then=self._ascend)
                return
            elif kind == "bump" and ev[1].kind == "figure":
                self._use_figure(ev[1])
                return
            elif kind in ("bump", "ambush") and ev[1].kind == "wild":
                self._meet_wild(ev[1])
                return
            elif kind in ("bump", "spotted") and ev[1].kind == "trainer":
                self._meet_trainer(ev[1], spotted=(kind == "spotted"))
                return
        # stop a long walk when a wild Pokemon comes close
        px, py = self.run.player
        if self.walk_goal and any(m.kind == "wild" and m.alert and abs(m.x - px) + abs(m.y - py) <= 3
                                  for m in self.run.floor.movers):
            self.walk_goal = None

    def _indoors(self, index):
        """A floor of our own map marked "indoors": a room (no wild Pokemon; the zone you came in from)."""
        lay = (getattr(self, "recipe", None) or {}).get("layout") or []
        return bool(0 <= index < len(lay) and isinstance(lay[index], dict) and lay[index].get("indoors"))

    def _floor_name(self, index):
        """A floor's name: its zone's ("Area 1 (East)", "B2F"; on a wide floor, its areas'), else 1F, 2F..."""
        own = ((self.recipe.get("art") or {}).get("floor_names") or []) if hasattr(self, "recipe") else []
        if self._indoors(index) and index < len(own):  # (a room on the map: the Safari Zone's rest houses)
            return own[index]
        if self.zones:
            per = getattr(self, "per_floor", 1)
            names = [self._zone_name(i) for i in range(index * per, min(len(self.zones), (index + 1) * per))]
            return " / ".join(names) if names else f"{index + 1}F"
        names = ((self.recipe.get("art") or {}).get("floor_names") or []) if hasattr(self, "recipe") else []
        if index < len(names):  # (our map's own: Rock Tunnel's 1F, B1F, 1F)
            return names[index]
        return f"B{index}F" if index and self._descending() else f"{index + 1}F"

    def _descending(self):
        """True where the floors go down (a cave: 1F, B1F... the Seafoam Islands), not up (a tower)."""
        return bool(self.area_data.get("zones_descend") or self.recipe.get("descend"))

    def _stairs_blocked(self):
        """True (and says why) when the stairs down can't be taken yet."""
        return False

    def _stairs_line(self, index):
        name = self._floor_name(index)
        if self.zones and not self.area_data.get("zones_linear"):  # the Safari Zone's areas
            return f"You headed over to {name}."
        deeper = index > self.run.index
        if self._descending():
            return f"You went {'down' if deeper else 'back up'} the stairs to {name}."
        return f"You went {'up' if deeper else 'back down'} the stairs to {name}."

    def _descend(self):
        self._set_zone(self.run.index + 1)
        self.run.descend()
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.run.player
        self.banner = 120

    def _warp(self, index, x, y, land=False):
        if self.zones and self._indoors(self.run.index) and not self._indoors(index):  # (out of a house: the area its door is in, said nothing)
            self.game.story_manager.story_flags[f"zone_{self.area_key}"] = self.zones[self._zone_index(index, x, y)]
        else:
            self._set_zone(index)
        self.run.warp(index, x, y, land=land)
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.run.player
        self.banner = 120

    def _ascend(self):
        self._set_zone(self.run.index - 1)
        self.run.ascend()
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.run.player
        self.banner = 120

    # ---------------------------------------------------------------- story gates on the map (Jordan, 11-06)
    # A way out that needs an HM (or the bike, or the route's boss beaten) has what's in the way standing on
    # it until you have it: a small tree (Cut), a cracked rock (Rock Smash), a boulder (Strength), water
    # (Surf, Dive), a waterfall, a whirlpool, a dark cave mouth (Flash), the cycling gate, Snorlax asleep.
    GATES = {"HM_CUT": ("tree", "CUT"), "HM_ROCK_SMASH": ("rock", "ROCK SMASH"), "ROCK_SMASHER": ("rock", None),
             "HM_STRENGTH": ("boulder", "STRENGTH"), "HM_SURF": ("water", "SURF"), "HM_DIVE": ("water", "DIVE"),
             "HM_WATERFALL": ("waterfall", "WATERFALL"), "HM_WHIRLPOOL": ("whirlpool", "WHIRLPOOL"),
             "HM_FLASH": ("dark", "FLASH"), "BICYCLE": ("bike", None), "HM_ROCK_CLIMB": ("rock", "ROCK CLIMB")}

    def _gate(self, target):
        """(kind, move, met) for a way out with something in the way, else None."""
        if target == "BOSS":
            return "boss", None, False
        item = self.exit_items.get(target)
        if not item or (self.recipe.get("art") or {}).get("boss_spot"):  # (the boss is on its own tile of the map, not across a way out)
            if not item:
                return None
            cond = item.get("condition")
            conds = [str(c) for c in (cond if isinstance(cond, list) else [cond] if cond else []) if str(c) != "boss_defeated"]
            for c in conds:
                if c.startswith("has_item:") and c[9:] in self.GATES:
                    kind, move = self.GATES[c[9:]]
                    return kind, move, self._check_route_condition(c, False, item)
            return None
        cond = item.get("condition")
        conds = [str(c) for c in (cond if isinstance(cond, list) else [cond] if cond else [])]
        if "boss_defeated" in conds and self.area_data.get("area_boss")                 and not self._check_route_condition("boss_defeated", False, item):
            return "boss", None, False  # (asleep in the way comes first: Route 16's Snorlax, then the Bicycle)
        for c in conds:
            if c.startswith("has_item:") and c[9:] in self.GATES:
                kind, move = self.GATES[c[9:]]
                return kind, move, self._check_route_condition(c, False, item)
            if c == "boss_defeated" and self.area_data.get("area_boss"):
                return "boss", None, self._check_route_condition(c, False, item)
        return None

    def _boss_item(self):
        return next((i for i in self.area_data.get("route_menu", []) if i.get("action") == "BOSS"), None)

    def _try_exit(self, target):
        if target == "BOSS":  # the boss asleep on its own tile: wake it (the Poke Flute) and battle, else it won't budge
            self._step_back()
            boss = self._boss_item()
            if boss and self._check_route_condition(boss.get("condition"), False, boss):
                self._get_route_callback(boss)()
                return
            name = (self.area_data.get("area_boss") or {}).get("name", "A Pokemon")
            self.say([f"A {name} is sound asleep, right in the way!", "It won't budge. Maybe a sound would wake it..."])
            return
        same = [t for t, v in self.run.floor.exits.items() if v == target]
        _to = (self._here_art() or {}).get("edge_to", {}).get("%d,%d" % tuple(self.run.player))
        self.game.arrive_edge = (self.area_key, target, tuple(_to)) if _to else None  # (out by an edge tile: in at its partner there)
        core.ENTRANCE_INDEX = same.index(tuple(self.run.player)) if tuple(self.run.player) in same else 0
        core.ENTRANCE_COUNT = len(same)  # (how many tiles that way out has here: the far side takes the matching place along its own)
        if len(same) > 1:  # (out to a town with as many ways back: in by the matching one, Victory Road's two mouths at Ever Grande)
            self.game.walk_town_exit = (self.area_key, core.ENTRANCE_INDEX, len(same))
        _all = (self.recipe.get("exit_floors_all") or {}).get(target) or []
        if len(_all) > 1 and self.run.index in _all:  # (the same place from several floors: out by this floor's own way there)
            core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = _all.index(self.run.index), len(_all)
            core.ENTRANCE_SPREAD = True
        if self.contest:  # leaving by the gate ends the contest: the judging first
            self._step_back()
            self._contest_end()
            return
        item = self.exit_items.get(target)
        story = self.game.story_manager
        pool = self.area_data.get("trainer_pool", [])
        left = any(not story.is_trainer_defeated(self.area_key, i) for i in range(len(pool)))
        gate = self._gate(target)
        if item is not None and self._exit_block(item, left) == "story":
            self._step_back()
            boss = self._boss_item()
            if gate and gate[0] == "boss" and not gate[2] and boss and \
                    self._check_route_condition(boss.get("condition"), False, boss):
                self._get_route_callback(boss)()  # it's in the way: wake it (the Poke Flute) and battle
                return
            if gate and gate[0] == "boss" and not gate[2]:
                name = (self.area_data.get("area_boss") or {}).get("name", "A Pokemon")
                self.say([f"A {name} is sound asleep, right in the way!", "It won't budge. Maybe a sound would wake it..."])
                return
            self._exit_locked(item)  # says what's needed (then show_progression_menu: the map)
            return
        from src.coop import travel
        if travel.held(self.game, self._area_name(target), lambda: self._try_exit(target), self._step_back):
            return  # (co-op: the others have a say)
        flag = f"gate_used_{self.area_key}_{target}"
        story = self.game.story_manager
        if gate and gate[1] and gate[2] and not story.story_flags.get(flag):  # the HM, the first time through
            story.story_flags[flag] = True
            lead = self.lead()
            who = lead.display_name.upper() if lead else self.game.player_name
            self.walk_goal = None
            self.say([f"{who} used {gate[1]}!"], then=lambda: self._leave(target))
            return
        self._leave(target)

    def _step_back(self):
        """Off an exit you can't take yet, back onto the tile you came from."""
        self.run.player = self.anim_from
        self.anim = 0

    # ---- items
    HONEY_PACK = "HONEY_x3"   # Jordan (11-06): Honey matters; three of it on every floor with wild Pokemon

    MAX_REVIVE_BADGES = 6  # (late in a region's story a Max Revive can lie on a floor; trainers never give one)

    def _floor_loot(self, loot):
        def roll(rng):  # (asked as each floor is made)
            items = core.roll_loot(rng, loot)
            from src.states.overworld.route_encounters import _story_badges
            if _story_badges(self.game) >= self.MAX_REVIVE_BADGES and rng.random() < 0.2:
                items.append("MAX_REVIVE")
            wild = bool(self._get_wild_pool(self.area_data)) and not getattr(self, "contest", None)
            return items + [self.HONEY_PACK] if wild else items
        return roll

    def _pick_up(self, key):
        story = self.game.story_manager
        if key == catching.POKE:
            story.balls_left += 1
            name = "POKE BALL"
        elif key == self.HONEY_PACK:
            story.inventory["HONEY"] = story.inventory.get("HONEY", 0) + 3
            if self.game.assets.heal_sfx:
                self.game.assets.heal_sfx.play()
            self.flash(f"You found 3 HONEY! (You have {story.inventory['HONEY']}.)")
            return
        else:
            story.add_item(key)
            name = forms.item_label(key).upper()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.flash(f"You found a {name}!")

    def _pick_up_tm(self, spot):
        story = self.game.story_manager
        seed = story.story_flags.setdefault("dungeon_seed", random.randrange(1 << 30))
        region = story.get_current_region()
        badges = len(story.badges.get(region, []))
        tm = core.pick_tm(seed, spot, tms.table(self.game), tms.owned(story), badges)
        story.story_flags[f"dungeon_tm_{spot}"] = tm or "RARE_CANDY"
        if tm:
            story.add_item(tm)
            lines = [f"You found {tms.label(self.game, tm)}!", "Your Pokemon that can learn it now have the move to pick."]
        else:  # every TM owned already
            story.add_item("RARE_CANDY")
            lines = ["You found a RARE CANDY!"]
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.say(lines)

    # ---------------------------------------------------------------- meeting a wild Pokemon
    def _can_catch(self):
        if self.contest:
            return self.contest["balls"] > 0
        if getattr(self, "safari", None):
            return self.safari["balls"] > 0
        story = self.game.story_manager
        return catching.total_balls(story) > 0 and story.catch_unlocked()

    def _meet_wild(self, mover):
        self.walk_goal = None
        self.encounter = mover
        self.choice = 0 if self._can_catch() else 1
        p = mover.payload
        self.game.data.mark_seen(p.id)
        if p.cry:
            p.cry.play()
        self.mode = "CHOICE"

    def _pick(self, which):
        if which == 0:
            if not self._can_catch():
                story = self.game.story_manager
                if not story.catch_unlocked():
                    self.flash("You can't catch Pokemon yet!")
                else:
                    self.flash("You're out of Poke Balls!")
                return
            self._start_math()
        elif self.contest:
            self.flash("In the contest, you catch with MATH!")
        elif getattr(self, "safari", None):
            self.flash("No battling in the Safari Zone. Catch with MATH!")
        else:
            self._battle_wild(self.encounter)

    def _start_math(self):
        self.mode = "MATH"
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught, num_options=3)
        self.math_timer = self.math_full = self.game.story_manager.timer_frames(MATH_SECONDS)

    def _answer(self, idx):
        if self.mode != "MATH" or idx >= len(self.options):
            return
        story = self.game.story_manager
        p = self.encounter.payload
        if self.contest:  # a Sport Ball (the contest's own)
            ball = "SPORT_BALL"
            self.contest["balls"] -= 1
        elif getattr(self, "safari", None):  # a Safari Ball (this visit's own)
            ball = "SAFARI_BALL"
            self.safari["balls"] -= 1
        else:
            ball = catching.selected(story)
            catching.use(story, ball)
        self._thrown_ball = ball
        right = self.options[idx] == self.correct_ans
        story.note_answer(self.problem_str, right, (self.math_full - self.math_timer) < QUICK_SECONDS * FPS)
        shiny_pass = bool(p.is_shiny) and not right  # a shiny is caught even on a wrong answer (as on the route)
        self.was_shiny_override = shiny_pass
        if right or shiny_pass:
            quick = (self.math_full - self.math_timer) < QUICK_SECONDS * FPS
            max_hp = p.get_max_hp()
            roll = catching.window_throw(self.game, p, ball, guaranteed=balance.is_legendary(p.id) or shiny_pass,
                                         hp=1 if quick else max(1, max_hp // 4), max_hp=max_hp,
                                         terrain=self.area_data.get("battle_type", ""))
            self.throw_result = "caught" if roll[0] else "broke"
        else:
            self.current_streak = 0
            self.throw_result = "wrong"
        self.mode, self.throw_timer = "THROW", int(FPS * 1.2)

    def _resolve_throw(self):
        mover, p = self.encounter, self.encounter.payload
        name = p.display_name.upper()
        self.run.remove(mover)
        self.encounter = None
        if self.throw_result == "caught" and self.contest:
            if p.cry:
                p.cry.play()
            self.mode = "MAP"
            self._contest_keep(p)
            return
        if self.throw_result == "caught":
            if p.cry:
                p.cry.play()
            self.mode = "MAP"
            self.p_data = [None, p, None]
            self.ball_target = [self.game.width // 2, self.game.height // 2]
            self.complete_catch(1)  # the route's own: party or PC, Pokedex, streak, milestones, save
            catching.after_catch(self.game, p, getattr(self, "_thrown_ball", None))
            self.pause_timer = 0
            self.p_data = [None] * 3
            evolve = self.dialogue_box.callback  # (the route checks for a catch evolution after)
            self.say(self.dialogue_box.text_lines, then=evolve)
            return
        self.mode = "MAP"
        if self.throw_result == "broke":
            self.say([f"Oh no! {name} broke free!", f"{name} ran away!"])
        elif self.throw_result == "timeout":
            self.say([f"Too slow! {name} ran away!"])
        else:
            self.say([f"That's not it! {name} ran away!"])

    def _battle_wild(self, mover):
        from src.states.battle import WildBattleState
        self.pending = ("wild", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        battle = WildBattleState(self.game, mover.payload, self.area_key,
                                 background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        if self._ow_on():  # Options > BATTLE STYLE: OVERWORLD: fought here on the map
            from src.states.overworld.overworld_battle import OverworldView
            battle.overworld = OverworldView(self, mover)
        pygame.event.clear()
        self.game.change_state(battle)

    def _play_data(self):
        return {"balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False, "dungeon": True}

    # ---------------------------------------------------------------- trainers
    def _meet_trainer(self, mover, spotted=False):
        self.walk_goal = None
        self.encounter = mover
        if spotted:
            self.mode, self.spot_timer = "SPOTTED", int(FPS * 0.8)
            sfx = getattr(self.game.assets, "ui_sfx", None)
            sound = sfx.get("select") if isinstance(sfx, dict) else None
            if sound:
                sound.play()
        else:
            self._battle_trainer(mover)

    def _battle_trainer(self, mover):
        if self._ow_on():  # Options > BATTLE STYLE: OVERWORLD (src/states/overworld/overworld_battle.py)
            self._ow_trainer(mover)
            return
        self.pending = ("trainer", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        self.trigger_trainer_battle(specific_index=mover.payload[0])  # intro, battle, rewards: the route's own

    # ---------------------------------------------------------------- Sweet Scent and Honey
    def _scent_source(self):
        """What draws three wild Pokemon here: "SWEET SCENT" (a party Pokemon's move, once a floor),
        "HONEY" (used up), or None."""
        story = self.game.story_manager
        if not self._can_catch() or not self._get_wild_pool(self.area_data):
            return None
        knows = any(p and p.current_hp > 0 and any(str(m).upper().replace(" ", "-") == "SWEET-SCENT"
                                                   for m in (getattr(p, "moves", None) or []))
                    for p in story.player_team)
        if knows and self.scent_floor != self.run.index:
            return "SWEET SCENT"
        if story.inventory.get("HONEY", 0) > 0:
            return "HONEY"
        return None

    # ---------------------------------------------------------------- the Bug-Catching Contest
    def _contest_keep(self, p):
        """A contest catch: kept if it scores higher than the one you have (the other is let go)."""
        c = self.contest
        self.game.data.mark_seen(p.id)
        score = contest_score(p)
        name = p.display_name.upper()
        if c["best"] is None or score > c["score"]:
            old = c["best"]
            c["best"], c["score"] = p, score
            lines = [f"Gotcha! {name} was caught!"]
            if old is not None:
                lines.append(f"You kept {name} and let {old.display_name.upper()} go.")
        else:
            lines = [f"Gotcha! {name} was caught!",
                     f"Your {c['best'].display_name.upper()} is better. {name} was let go."]
        self.say(lines, then=self._contest_check)

    def _contest_tick(self):
        """A turn of the contest gone (a step, or WAIT)."""
        if self.contest and self.contest["turns"] > 0:
            self.contest["turns"] -= 1

    def _safari_check(self):
        """The Safari Game: its welcome on arrival; out of steps or Safari Balls, the visit is over."""
        sf = getattr(self, "safari", None)
        if not sf or not self._ready() or self.dialogue_box.visible:
            return
        if sf.pop("hello", False):
            self.say([f"Welcome to the Safari Zone! Here are {sf['balls']} Safari Balls.",
                      f"You have {sf['steps']} steps to catch what you can. Catch with MATH: no battling here!"])
            return
        if sf["steps"] <= 0 or sf["balls"] <= 0:
            self.safari = None
            self.say(["Ding-dong! Time's up!" if sf["steps"] <= 0 else "You're out of Safari Balls!",
                      "Your Safari Game is over. Please come again!"],
                     then=lambda: self._leave(next(iter(self.recipe.get("exit_floors") or self.exit_items or [self.area_data.get("next_area")]))))

    def _contest_check(self):
        """Time's up, or no Sport Balls left: the judging."""
        c = self.contest
        if c and (c["turns"] <= 0 or c["balls"] <= 0) and self._ready():
            self._contest_end()

    def _contest_end(self, then_leave=True):
        """The judges score your best catch against the other contestants'; prizes; you keep your bug."""
        c, self.contest = self.contest, None
        story = self.game.story_manager
        lines = ["Time's up! The Bug-Catching Contest is over." if c["turns"] <= 0 or c["balls"] <= 0
                 else "You left the contest early. Let's see how you did!"]
        if c["best"] is None:
            lines.append("You didn't catch any Bug Pokemon this time. Better luck next contest!")
        else:
            rng = random.Random()
            board = sorted([(rng.randint(70, 190), n) for n in CONTEST_RIVALS] + [(c["score"], None)],
                       key=lambda t: t[0], reverse=True)  # (a tie: by score alone)
            place = next(i for i, (_s, n) in enumerate(board) if n is None)
            best = c["best"].display_name.upper()
            lines.append(f"Your {best} scored {c['score']} points!")
            if place < 3:
                prize = CONTEST_PRIZES[place]
                lines.append(["You won 1st place!", "You took 2nd place!", "You took 3rd place!"][place])
                lines.append(f"You received the {forms.item_label(prize).upper()}!")
                story.add_item(prize)
                if place == 0:
                    story.story_flags["won_bug_contest"] = True
            else:
                winner = board[0][1]
                lines.append(f"{winner} won with {board[0][0]} points. You came in {place + 1}th.")
                lines.append("Here's a POTION for taking part!")
                story.add_item("POTION")
            self.p_data = [None, c["best"], None]  # you keep your bug (the route's own catch: party or PC)
            self.was_shiny_override = False
            self.complete_catch(1)
            catching.after_catch(self.game, c["best"], "SPORT_BALL")
            self.p_data = [None] * 3
            lines.append(f"{best} is yours to keep!")
        self.say(lines, then=(lambda: self._leave(self.exit_items and next(iter(self.exit_items)) or "NATIONAL_PARK"))
                 if then_leave else None)

    def use_scent(self, source=None):
        """Draw in three wild Pokemon: Sweet Scent (a party Pokemon's, once a floor) or Honey (source "HONEY":
        used from the Bag)."""
        if not self._ready():
            return
        if self.contest:
            self.flash("Not during the contest!")
            return
        if source in ("HONEY", "WHITE_FLUTE") and not (self._can_catch() and self._get_wild_pool(self.area_data)
                                                       and self.game.story_manager.inventory.get(source, 0) > 0):
            source = None
        source = source or self._scent_source()
        story = self.game.story_manager
        if source is None:
            if not self._get_wild_pool(self.area_data):  # (a building, a lab: Sweet Scent and Honey do nothing)
                self.flash("No wild Pokemon live here, so nothing comes to the sweet smell.")
            elif not self._can_catch():
                self.flash("You need Poke Balls to catch here.")
            else:
                self.flash("No HONEY, and no Pokemon that knows SWEET SCENT.")
            return
        if source == "HONEY":
            story.inventory["HONEY"] -= 1
            first = f"{self.game.player_name} spread some HONEY around..."
        elif source == "WHITE_FLUTE":
            first = f"{self.game.player_name} played the WHITE FLUTE..."
        else:
            self.scent_floor = self.run.index
            first = "A sweet scent drifted through the air..."
        self.walk_goal = None

        def begin():
            self.route_bg = self._map_backdrop()  # (this very map behind the Pokemon the Honey drew in)
            self.mode = "CATCH"
            self.is_progression_paused = False
            self.pending_wild_encounters = 0
            self.input_delay = 20
            self.trigger_wild_encounter()  # the route's three-Pokemon catch, then show_progression_menu
        self.say([first, "Wild Pokemon were drawn in!"], then=begin)

    def _starter_walk_up(self):
        """After the starter battle, whoever the scene stood far off walks up to you, says their piece, and then you head home
        (starter_event "walk_up": {"look": the look of their blocker on this floor, "flag": set once done, "lines"}; Lake Verity's
        Professor Rowan). True while it plays."""
        ev = self.area_data.get("starter_event") or {}
        spec, story = ev.get("walk_up"), self.game.story_manager
        boss_flag = (ev.get("boss") or {}).get("victory_flag")
        if not spec or not story.story_flags.get(boss_flag) or story.story_flags.get(spec["flag"]) or not hasattr(self, "run"):
            return False
        f = self.run.floor
        if not hasattr(self, "_bars"):  # (the map hasn't been drawn yet: its blockers straight from the map)
            m = self.run.recipe.get("art") or {}
            here = m["floors"][self.run.index] if m.get("floors") else m
            self._bars = {tuple(t): bar for bar in here.get("barred", []) for t in bar.get("tiles", [])}
        start = next((t for t, bar in self._bars.items() if bar.get("look") == spec["look"]), None)
        story.story_flags[spec["flag"]] = True
        if start is None or not str(spec["look"]).startswith("sheet:"):
            return False
        for t, bar in list(self._bars.items()):  # (they leave their spots: nobody is standing there any more)
            if (bar.get("until") or {}).get("flag_condition") == spec["flag"] and str(f.decor.get(t, "")).startswith("barrier:"):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR
        goal = tuple(self.run.player)
        prev, todo = {start: None}, [start]
        while todo:  # the shortest way over open ground to beside you
            cur = todo.pop(0)
            if abs(cur[0] - goal[0]) + abs(cur[1] - goal[1]) == 1:
                break
            for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                n = (cur[0] + dx, cur[1] + dy)
                if n not in prev and 0 <= n[0] < f.w and 0 <= n[1] < f.h and f.walkable(*n) and n != goal:
                    prev[n] = cur
                    todo.append(n)
        else:
            cur = start
        path = []
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        self._walker = {"sheet": spec["look"][6:], "path": path[::-1], "i": 0.0, "lines": list(spec.get("lines") or []),
                        "with": str(spec.get("with") or "")[6:] or None}  # ("with": someone who comes along two steps behind, and leaves with them)
        self.walk_goal = None
        return True

    def _walker_step(self):
        w = self._walker
        last = float(len(w["path"]) - 1)
        if w.get("leaving"):  # (said their piece: they walk off the way they came, out of sight, and then you head home)
            w["i"] -= 0.14
            if w["i"] <= max(0.0, last - 9):
                self._walker = None
                self._starter_return()
            return
        if w.get("spoke"):  # (saying their piece: wait for it)
            return
        w["i"] += 0.14
        if w["i"] >= last:
            w["i"] = last
            if not w.get("spoke"):
                w["spoke"] = True

                def off():
                    w["leaving"] = True
                if w["lines"]:
                    self.say(w["lines"], then=off)
                else:
                    off()

    def _bag_from_map(self):
        self.is_resuming = True  # (back from the Bag you are where you were)
        self._open_bag()

    # ---------------------------------------------------------------- input
    def _buttons(self):
        """The map's own buttons (bottom right): (rect, label, colour, action, enabled, small text)."""
        w, h = self.game.width, self.game.height
        side = side_buttons(self.game)  # (stacked in the right band, beside the map)
        buttons = [
            (self._qp_button_rect(), theme.pokemon_word("POKEMON"), theme.POKEMON,
             self._qp_toggle, True, None),  # (its list opens beside it: src/states/overworld/overworld_battle.py)
            (side[2], theme.pokemon_word("POKEDEX"), theme.BAG,
             self._open_pokedex, True, None),
            (side[5], "BAG", (198, 132, 60), self._bag_from_map, True, None),
            (side[1], "HONEY", (226, 170, 40), self.use_scent,
             bool(self._scent_source()) if hasattr(self, "run") else False, self._honey_note()),
            (side[0], "BRAKE" if self._downhill() and not self.braking else "WAIT", theme.RUN, self.wait_turn, True,
             "hold still" if self._downhill() and not self.braking else "a turn"),
        ]
        mega = self._map_mega_button() if hasattr(self, "run") and not self.contest else None
        if mega:  # (as in Legends: Z-A: Mega Evolve the Pokemon following you, right here)
            buttons.append(mega)
        act = self._act_here() if hasattr(self, "run") else None
        if act:  # beside water or a tree
            sub = {"DIVE": "the deep sea here", "SURFACE": "up to the sea above",
                   "FISH": "the water here", "HEADBUTT": "this tree", "TALK": "the clerk",
                   "PLAY SLOTS": "this machine"}.get(act[0])
            buttons.append((side[4], act[0], (232, 132, 40), act[1], True, sub))
        return buttons

    def _honey_note(self):
        """The HONEY button's small line: how much you have (or Sweet Scent's turn)."""
        n = self.game.story_manager.inventory.get("HONEY", 0)
        if hasattr(self, "run") and not self._get_wild_pool(self.area_data):
            return "no wild here"
        if hasattr(self, "run") and self._scent_source() == "SWEET SCENT":
            return "Sweet Scent"
        return f"x{n}" if n else "none"

    def _choice_rects(self):
        w, h = self.game.width, self.game.height
        return [pygame.Rect(w // 2 - 330, int(h * 0.62), 300, 120), pygame.Rect(w // 2 + 30, int(h * 0.62), 300, 120)]

    def _answer_rects(self):
        w, h = self.game.width, self.game.height
        bw = 230
        x0 = w // 2 - (3 * bw + 2 * 30) // 2
        return [pygame.Rect(x0 + i * (bw + 30), int(h * 0.66), bw, 110) for i in range(3)]

    def _camera(self):
        """The pixel the screen is centred on (the player, mid-step)."""
        px, py = self.run.player
        if self.anim > 0:
            k = 1 - self.anim / STEP_FRAMES
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        focus = getattr(self, "_focus", None) if self._backdrop else None
        if focus:  # (an OVERWORLD-style battle: the fight, a bit above the middle, clear of the battle's text box)
            cx, cy = focus[0], focus[1] + self.game.height * 0.14
        if hasattr(self, "run") and (self.run.recipe.get("image") or self.run.recipe.get("art")):  # (no black past it)
            W, H = self._view().size
            mw, mh = self.run.floor.w * TILE, self.run.floor.h * TILE
            cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
            cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return cx, cy

    def _view(self):
        """Where the map is drawn: the frame (the whole screen under an OVERWORLD-style battle)."""
        if self._backdrop:
            return self.game.screen.get_rect()
        return map_view(self.game)

    def _origin(self):
        cx, cy = self._camera()
        v = self._view()
        return int(v.centerx - cx), int(v.centery - cy)

    def _tile_at(self, pos):
        ox, oy = self._origin()
        return int((pos[0] - ox) // TILE), int((pos[1] - oy) // TILE)

    KEYS = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}

    def handle_events(self, events):
        if self.mode == "CATCH":
            return super().handle_events(events)
        if getattr(self, "_walker", None) and (not self._walker.get("spoke") or self._walker.get("leaving")):  # (someone is walking up to you, or off again: wait for them)
            return
        events = [e for e in events if not self._qp_event(e)]  # (the POKEMON button and its list first)
        for e in events:
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self._map_press = False
            if self.dialogue_box.visible:  # a tap anywhere (or Enter) moves the text on
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                        (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogue_box.advance()
                continue
            if self.mode == "MAP":
                self._map_event(e)
            elif self.mode == "CHOICE":
                self._choice_event(e)
            elif self.mode == "MATH":
                self._math_event(e)

    def _map_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in self.KEYS:
                self.walk_goal = None
                self.step(*self.KEYS[e.key])
            elif e.key in (pygame.K_PERIOD, pygame.K_z):
                self.wait_turn()
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_f):
                act = self._act_here()
                if act:
                    act[1]()
            elif e.key == pygame.K_h:
                self.use_scent()
            elif e.key == pygame.K_p:
                self._open_party()
            elif e.key == pygame.K_x:
                self._open_pokedex()
            elif e.key in (pygame.K_ESCAPE, pygame.K_m) and self.hud_buttons:
                self.hud_buttons[0].callback()  # MENU
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, _label, _color, action, ok, _sub in self._buttons():
                if rect.collidepoint(e.pos):
                    action()
                    return
            if self._minimap_rect().collidepoint(e.pos):
                return
            jr = self._journal_rect()
            if jr is not None and jr.collidepoint(e.pos):  # (a tap on the mission: the Journal)
                from src.states.systems.journal import JournalState
                self.game.change_state(JournalState(self.game, self))
                return
            if not self._view().collidepoint(e.pos):  # (the black round the map: nothing there)
                return
            tx, ty = self._tile_at(e.pos)
            self.tap_mark = [(tx, ty), self.run.floor.walkable(tx, ty), TAP_FRAMES]
            px, py = self.run.player
            if abs(tx - px) + abs(ty - py) == 1 and not self.run.floor.walkable(tx, ty):
                self.facing = (tx - px, ty - py)  # a tap on the water or a tree beside you: fish or Headbutt
                if self._read_sign():  # (or a sign: read it)
                    return
                act = self._act_here()
                if act and (tx, ty) == self._beside("water" if act[0] == "FISH" else "tree"):
                    act[1]()
                    return
            if (tx, ty) == (px, py):
                self.wait_turn()
            elif abs(tx - px) + abs(ty - py) == 1:
                self.walk_goal = None
                self.step(tx - px, ty - py)
            elif self.run.floor.walkable(tx, ty) and (tx, ty) in self.run.floor.seen:
                self.walk_goal = (tx, ty)
                self._map_press = True  # (held: it keeps walking toward the finger)
            else:  # somewhere unseen: one step that way
                dx, dy = tx - px, ty - py
                self.walk_goal = None
                self.step(*((1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)))

    def _follow_hold(self):
        """Held down (Jordan, 11-07): an arrow key keeps you walking; a held finger on the map keeps you
        heading for it, steering as it moves."""
        if self.dialogue_box.visible or self.anim > 0:
            return
        way = held_way(self.KEYS)
        if way:
            self.walk_goal = None
            if self.mode == "MAP":
                self.step(*way)
            return
        at = held_pointer() if getattr(self, "_map_press", False) else None
        if at is None:
            self._map_press = False
            return
        if not self._view().collidepoint(at):
            return
        goal = self._tile_at(at)
        if goal != self.run.player and self.run.floor.walkable(*goal) and goal in self.run.floor.seen:
            self.walk_goal = goal

    def _cabin(self, opt, door):
        """A cabin's door (the S.S. Anne's): its trainer steps out and battles; once beaten, it's empty."""
        idx = int(opt.get("trainer", -1))
        pool = self.area_data.get("trainer_pool", [])
        story = self.game.story_manager
        if not (0 <= idx < len(pool)) or story.is_trainer_defeated(self.area_key, idx):
            self.say(opt.get("empty") or ["Nobody's in this cabin now."])
            return
        mover = core.Mover("trainer", door[0], door[1], (idx, pool[idx]), (0, 1))
        self.run.floor.movers.append(mover)
        self._battle_trainer(mover)

    def _flag_ok(self, item):
        fc = str(item.get("flag_condition") or "").split()
        flags = self.game.story_manager.story_flags
        if len(fc) == 2 and fc[0] == "not":
            return not flags.get(fc[1])
        return not fc or bool(flags.get(fc[0]))

    def _boulder_flag(self, t):
        return f"boulder_{self.area_key}_{self.run.index}_{t[0]}_{t[1]}"

    def _overheads(self):
        """This floor's overhead parts, drawn once: [(image, (x px, y px))] (Route 110: the Cycling Road above the path)."""
        key = (self.area_key, self.run.index)
        if getattr(self, "_over_key", None) != key:
            from src.dungeon import art as _art
            m = self.run.recipe.get("art") or {}
            here = m["floors"][self.run.index] if m.get("floors") else m
            self._over_key, self._over = key, [_art.overhead(o, TILE) for o in here.get("overheads", []) or []]
        return self._over

    def _drops(self, index):
        """A floor's boulders that drop through its holes: [[boulder], [hole], [where it lands below]]."""
        floors = (self.run.recipe.get("art") or {}).get("floors") or []
        return floors[index].get("drops", []) if 0 <= index < len(floors) else []

    def _until_met(self, u):
        """A blocker's "until": {"flag_condition": "x" | "not x", "item_condition": item, "condition": name or [names]}, all met."""
        story = self.game.story_manager
        parts = str(u.get("flag_condition") or "").split()
        if len(parts) == 2 and parts[0] == "not" and story.story_flags.get(parts[1]):
            return False
        if len(parts) == 1 and not story.story_flags.get(parts[0]):
            return False
        if u.get("item_condition") and story.inventory.get(u["item_condition"], 0) <= 0:
            return False
        if u.get("area_cleared"):  # (every trainer of another area beaten: the Meadow's grunts, for the Works Key)
            pool = (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(u["area_cleared"]) or {}).get("trainer_pool") or []
            if len(story.defeated_trainers.get(u["area_cleared"], set())) < len(pool):
                return False
        cond = u.get("condition")
        return all(self._check_route_condition(c, False, u) for c in (cond if isinstance(cond, list) else [cond] if cond else []))

    def _clear_boulders(self):
        """Boulders pushed aside stay out of the way (a story flag each)."""
        f = self.run.floor
        flags = self.game.story_manager.story_flags
        for b, _hole, land in self._drops(self.run.index - 1):  # (dropped from above: a rock on the ice here)
            t = tuple(land)
            if t not in f.decor and flags.get(f"boulder_{self.area_key}_{self.run.index - 1}_{b[0]}_{b[1]}"):
                f.decor[t] = f"fallen:{t[0]},{t[1]}"
                f.tiles[t[1]][t[0]] = core.WALL
        floors = (self.run.recipe.get("art") or {}).get("floors") or []
        here = floors[self.run.index] if 0 <= self.run.index < len(floors) else (self.run.recipe.get("art") or {})
        for i, bx, by, x, y in here.get("fallen", []):  # (a boulder pushed down from any floor above lands here: Seafoam's, down through its holes)
            if (x, y) not in f.decor and flags.get(f"boulder_{self.area_key}_{i}_{bx}_{by}"):
                f.decor[(x, y)] = f"fallen:{x},{y}"
                f.tiles[y][x] = core.WALL
                f.current.pop((x, y), None)
        calm = here.get("calm")  # (the floor's current stops once these boulders have been pushed down: [[floor, x, y], ...])
        if calm and f.current and all(flags.get(f"boulder_{self.area_key}_{i}_{bx}_{by}") for i, bx, by in calm):
            f.current.clear()
        def _met(bar):
            if bar.get("when") and not self.npc_shown(bar["when"]):
                return True  # (not here yet: as good as gone)
            return self.game.story_manager.inventory.get(bar["item"], 0) > 0 if bar.get("item") else \
                self._until_met(bar["until"]) if bar.get("until") else bool(flags.get(bar.get("flag")))
        _order = sorted(here.get("barred", []), key=lambda b: not _met(b))  # (gone ones first: two on a tile, the one there now wins)
        self._bars = {tuple(t): bar for bar in _order for t in bar.get("tiles", [])}
        self._soil = {(int(x), int(y)): b for x, y, b in here.get("berry_soil", [])}  # (soft soil: src/world/berries.py)
        for t in self._soil:
            if str(f.decor.get(t, "building")) in ("building", "") :  # (soil drawn into the map's picture: the patch stands there)
                f.decor[t] = f"soil:{t[0]},{t[1]}"
                f.tiles[t[1]][t[0]] = core.WALL
        for bar in _order:  # (a rockslide in the way until a story flag: Granite Cave's short way back, once you've met Steven)
            for t in map(tuple, bar.get("tiles", [])):
                kind = "barrier" if bar.get("item") or bar.get("look") else "rubble"  # (or till you carry something: the Cycling Road's gates and the Bicycle)
                met = _met(bar)  # (until: someone in the way till a badge, flag or item: Route 210's Psyduck)
                if met:
                    if str(f.decor.get(t, "")).startswith(kind + ":"):
                        del f.decor[t]
                        f.tiles[t[1]][t[0]] = core.FLOOR
                elif t not in f.decor or (f.decor[t] == "building" and bar.get("look")):  # (or on the picture's own solid ground: the legend asleep in its pool)
                    f.decor[t] = f"{kind}:{t[0]},{t[1]}"
                    f.tiles[t[1]][t[0]] = core.WALL
        for t, what in list(f.decor.items()):
            if str(what).startswith(("boulder:", "crate:")) and flags.get(self._boulder_flag(t)):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR
            elif str(what).startswith("falls:") and self.game.story_manager.inventory.get("HM_WATERFALL", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.SURF  # (you climb it: water you Surf up)
            elif str(what).startswith("cut:") and self.game.story_manager.inventory.get("HM_CUT", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (your Pokemon cuts it down)
            elif str(what).startswith("slope:") and self.game.story_manager.inventory.get("BICYCLE", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you ride up it)
            elif str(what).startswith("stones:") and self.game.story_manager.inventory.get("BICYCLE", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you hop across them on the Bicycle: the Jagged Pass's round stones)
                self.__dict__.setdefault("_stones", set()).add(t)
            elif str(what).startswith("crack:") and self.game.story_manager.inventory.get("HM_ROCK_SMASH", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (your Pokemon breaks it)
            elif str(what).startswith("climb:") and self.game.story_manager.inventory.get("HM_ROCK_CLIMB", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you scale it)
            elif str(what).startswith("whirl:") and flags.get(self._boulder_flag(t)):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.SURF  # (open water now)
                self._floor_surf = None

    def _whirlpool(self, t):
        """Walked into a whirlpool (Jordan, 11-09): it bars the way until you clear it with Whirlpool."""
        story = self.game.story_manager
        if story.inventory.get("HM_WHIRLPOOL", 0) <= 0:
            self.say(["A fierce whirlpool blocks the way!", "A Pokemon that knows Whirlpool could calm it."])
            return
        f = self.run.floor
        todo, seen = [t], {t}
        while todo:  # (the whole whirlpool, however many tiles it spreads over)
            x, y = todo.pop()
            story.story_flags[self._boulder_flag((x, y))] = True
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in seen and str(f.decor.get(n, "")).startswith("whirl:"):
                    seen.add(n)
                    todo.append(n)
        self._clear_boulders()
        self.say(["Your Pokemon used Whirlpool!", "The water calmed. The way is clear!"])

    def _crate_img(self):
        """A crate as the region's own art draws it (assets/tiles/<folder>/ow_crate.png: Orre's, from the fan game's sheet),
        else a plain wooden box."""
        if getattr(self, "_crate", None) is None:
            from src.dungeon import art as _art
            m = (self.run.recipe.get("art") or {})
            fl = (m.get("floors") or [m])[self.run.index] if m.get("floors") else m
            own = _art._ow(_art.spec_folder(fl.get("roofs") or m.get("roofs")), "crate", TILE)
            if own is None:
                own = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                pygame.draw.rect(own, (150, 104, 56), own.get_rect().inflate(-4, -4), border_radius=3)
                pygame.draw.rect(own, (90, 60, 30), own.get_rect().inflate(-4, -4), 3, border_radius=3)
            self._crate = own
        return self._crate

    def _boulder(self, t, crate=False):
        """Walked into a boulder (Jordan, 11-07): with Strength, push it aside by solving the slide puzzle. A crate
        (crate=True: Orre's S.S. Libra, Jordan 11-12) takes the puzzle alone, no Strength."""
        story = self.game.story_manager
        if crate:
            from src.states.slide_puzzle import SlidePuzzleState

            def shoved(solved):
                self.is_resuming = True
                self.game.change_state(self)
                if solved:
                    story.story_flags[self._boulder_flag(t)] = True
                    self._clear_boulders()
                    self.say(["You shoved the crate out of the way!"])
                else:
                    self.say(["The crate didn't budge. Try again any time!"])
            self.say(["A heavy crate is in the way.", "Push it? Slide the numbers into order!"],
                     then=lambda: self.game.change_state(SlidePuzzleState(self.game, shoved)))
            return
        if story.inventory.get("HM_STRENGTH", 0) <= 0:
            self.say(["A huge boulder is in the way.", "A Pokemon that knows Strength could push it!"])
            return
        from src.states.slide_puzzle import SlidePuzzleState

        def done(solved):
            self.is_resuming = True
            self.game.change_state(self)
            if solved:
                story.story_flags[self._boulder_flag(t)] = True
                self._clear_boulders()
                if any(tuple(b) == tuple(t) for b, _h, _l in self._drops(self.run.index)):
                    self.say(["Your Pokemon used Strength!", "The boulder dropped through the hole!", "It landed on the floor below."])
                else:
                    self.say(["Your Pokemon used Strength!", "The boulder slid out of the way!"])
            else:
                self.say(["The boulder didn't budge. Try again any time!"])

        def go():
            self.game.change_state(SlidePuzzleState(self.game, done))
        self.say(["A huge boulder is in the way.", "Use Strength to push it? Slide the numbers into order!"], then=go)

    def _read_sign(self):
        """The sign (or door) you face on one of our own maps: read it out (or go in)."""
        f = self.run.floor
        px, py = self.run.player
        t = (px + self.facing[0], py + self.facing[1])
        what = str(f.decor.get(t, ""))
        m = self.run.recipe.get("art") or {}
        if m.get("floors"):  # (a map of floors: this floor's signs)
            m = dict(m, signs=m["floors"][self.run.index].get("signs", []))
        if what.startswith("whirl:"):  # a whirlpool in the way: Whirlpool clears it
            self._whirlpool(t)
            return True
        if what.startswith("boulder:"):  # a boulder in the way: Strength, then the slide puzzle
            self._boulder(t)
            return True
        if what.startswith("crate:"):  # a crate in the way: the slide puzzle alone (Jordan, 11-12: the S.S. Libra's crates, no HM)
            self._boulder(t, crate=True)
            return True
        if what.startswith("cut:"):
            self.say(["A small tree is in the way.", "A Pokemon that knows Cut could cut it down."])
            return True
        if what.startswith("slope:"):
            self.say(["A steep, muddy slope.", "You could ride up it on a Bicycle."])
            return True
        if what.startswith("stones:"):
            self.say(["Round stones, in a row.", "On a Bicycle, you could hop across them!"])
            return True
        if what.startswith("crack:"):
            self.say(["A cracked rock is in the way.", "A Pokemon that knows Rock Smash could break it."])
            return True
        if what.startswith("falls:"):
            self.say(["A wall of rushing water!", "A Pokemon that knows Waterfall could climb it."])
            return True
        if what.startswith("climb:"):
            self.say(["A steep rock wall, with footholds.", "A Pokemon that knows Rock Climb could scale it."])
            return True
        if what.startswith("hole:"):
            self.say(["There's a hole in the floor.", "A boulder pushed in would drop to the floor below."])
            return True
        if what.startswith("barrier:"):
            bar = getattr(self, "_bars", {}).get(tuple(t), {})
            if bar.get("boss"):  # (it battles you: the Kecleon the Devon Scope shows, a wild Pokemon in the way)
                self.action_challenge_boss(dict(bar["boss"]))
                return True
            self.say(bar.get("lines") or ["The Cycling Road is for bicycles only.", "Come back with a Bicycle."])
            return True
        if what.startswith("rubble:"):
            self.say(["Fallen rocks block the way.", "Maybe there's another way around."])
            return True
        if what.startswith("fallen:"):
            self.say(["A boulder that fell from above.", "It's frozen fast in the ice."])
            return True
        if what.startswith("soil:"):  # soft soil: pick, water or plant (src/world/berries.py)
            self._soil_patch(t)
            return True
        if what.startswith("door:"):  # a house on the route (Oak's aide's): its route option, by its "door"
            opt = next((o for o in self.area_data.get("route_menu", []) if o.get("door") == what[5:]
                        and self._check_route_condition(o.get("condition"), False, o)
                        and self._flag_ok(o)), None)
            if opt is None:
                self.say(["The door is locked."])
            elif opt.get("action") == "CABIN":  # a ship's cabin: its trainer comes out to battle
                self._cabin(opt, t)
            else:
                self._get_route_callback(opt)()
            return True
        if what.startswith("sign:"):
            lines = (m.get("signs") or [])[int(what[5:])] if int(what[5:]) < len(m.get("signs") or []) else []
            if lines:
                from src.states.overworld.common import _fill_names
                self.say([_fill_names(self.game, line) for line in lines])
                return True
        return False

    def _soil_patch(self, t):
        from src.world import berries
        story = self.game.story_manager
        first = getattr(self, "_soil", {}).get(tuple(t))
        lines, empty = berries.touch(story, self.area_key, t, first)
        if not empty:
            self.say(lines)
            return
        if not berries.plantable(story):
            self.say(lines + ["You could plant a Berry here, if you had one."])
            return

        def ask():
            from src.states.berry_patch import PlantBerryState
            self.game.change_state(PlantBerryState(self.game, self, lambda b: self.say(berries.plant(story, self.area_key, t, b))))
        self.say(lines + ["Plant a Berry here?"], ask)

    def _berry_img(self, rec, st):
        """A patch's picture: soil (damp once watered), and the plant at its stage (Essentials' Berry-tree sheets)."""
        from src.world import berries
        cache = self.__dict__.setdefault("_berry_imgs", {})

        def load(name):
            if name not in cache:
                try:
                    cache[name] = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "berries", name + ".png")).convert_alpha()
                except (pygame.error, FileNotFoundError):
                    cache[name] = None
            return cache[name]
        soil = load("_damp") if berries.watered(rec) else None  # (dry soil is the map picture's own; damp once watered)
        plant = None
        if st is not None:
            sheet = load("_planted" if st == 0 else str(rec["berry"]).replace("_BERRY", "").lower())
            if sheet is not None:
                fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
                row = 0 if st == 0 else st - 1
                col = (pygame.time.get_ticks() // 400) % 4 if st == berries.RIPE else 0
                plant = sheet.subsurface((col * fw, row * fh, fw, fh))
        return soil, plant

    def _choice_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, rect in enumerate(self._choice_rects()):
                if rect.collidepoint(e.pos):
                    self._pick(i)
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.choice = 1 - self.choice
            elif e.key in (pygame.K_1, pygame.K_KP1):
                self._pick(0)
            elif e.key in (pygame.K_2, pygame.K_KP2):
                self._pick(1)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self._pick(self.choice)

    def _math_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, rect in enumerate(self._answer_rects()):
                if rect.collidepoint(e.pos):
                    self._answer(i)
                    return
        elif e.type == pygame.KEYDOWN:
            keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
            if e.key in keys:
                self._answer(keys[e.key])

    # ---------------------------------------------------------------- each frame
    def update(self):
        if self.mode == "CATCH":
            return super().update()
        if hasattr(self, "run"):
            self._clear_boulders()
        if self.dialogue_box.visible:
            self.dialogue_box.update()
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if self.banner > 0:
            self.banner -= 1
        if self.anim > 0:
            self.anim -= 1
        if getattr(self, "_walker", None):
            self._walker_step()
            return
        if self.mode == "MAP" and hasattr(self, "run") and not self.dialogue_box.visible:
            self._npc_tick()
        if self.mode == "MAP":
            self._contest_check()
            self._safari_check()
            self._follow_hold()
            if self.sliding and self._ready():  # (still sliding on the ice)
                self.step(*self.sliding)
            elif not self.walk_goal and self._ready() and self._downhill():  # (the Cycling Road: you roll on downhill)
                self._roll()
            elif self.walk_goal and self._ready():
                if self.run.player == self.walk_goal:
                    self.walk_goal = None
                else:
                    step = self.run.walk_toward(self.walk_goal)
                    if step is None:
                        self.walk_goal = None
                    else:
                        self.step(*step)
        elif self.mode == "MATH":
            self.math_timer -= 1
            if self.math_timer <= 0:
                self.throw_result = "timeout"
                self._resolve_throw()
        elif self.mode == "THROW":
            self.throw_timer -= 1
            if self.throw_timer <= 0:
                self._resolve_throw()
        elif self.mode == "SPOTTED":
            self.spot_timer -= 1
            if self.spot_timer <= 0:
                m = self.encounter
                mo = self._motion(m)
                if abs(m.x - self.run.player[0]) + abs(m.y - self.run.player[1]) > 1 and mo is not None:
                    mo.walk(self.run.player, lambda t: self._npc_free(t, m))   # (they walk up to you, as in the games)
                    self.mode = "APPROACH"
                else:
                    self._battle_trainer(m)
        elif self.mode == "APPROACH":
            m = self.encounter
            mo = self._motion(m)
            mo.tick(lambda t: self._npc_free(t, m))
            m.x, m.y = mo.pos
            m.facing = mo.facing
            if mo.idle():
                mo.face(self.run.player)
                m.facing = mo.facing
                self.facing = (-m.facing[0], -m.facing[1])
                self._battle_trainer(m)

    # ---------------------------------------------------------------- drawing
    tap_mark = None
    math_full = MATH_SECONDS * FPS

    def _draw_tap_marks(self, screen, at):
        """Where you tapped: your destination stays lit till you get there."""
        if self.walk_goal:
            theme.tap_marker(screen, at(*self.walk_goal))
        if self.tap_mark and self.tap_mark[2] > 0 and self.tap_mark[0] != self.walk_goal:
            theme.tap_marker(screen, at(*self.tap_mark[0]), self.tap_mark[1])
            self.tap_mark[2] -= 1

    def _render_floor(self):
        f = self.run.floor
        if self.run.recipe.get("art"):  # one of our own maps, in its own art
            from src.dungeon import art as _art
            m = self.run.recipe["art"]
            grid = m["floors"][self.run.index]["art"] if m.get("floors") else m["art"]
            flags = self.game.story_manager.story_flags
            if any(c == "x" for row in grid for c in row):  # (a whirlpool cleared is open sea)
                grid = ["".join("o" if c == "x" and flags.get(self._boulder_flag((i, j))) else c for i, c in enumerate(row)) for j, row in enumerate(grid)]
            if self.game.story_manager.inventory.get("HM_ROCK_SMASH", 0) > 0 and any("0" in row for row in grid):  # (cracked rocks, broken)
                grid = [row.replace("0", ".") for row in grid]
            if self.game.story_manager.inventory.get("HM_CUT", 0) > 0 and any("2" in row for row in grid):  # (small trees, cut down)
                grid = [row.replace("2", ".") for row in grid]
            own = m["floors"][self.run.index].get("theme") if m.get("floors") else None  # (a floor's own look: the seabed under a sea route)
            own_roofs = m["floors"][self.run.index].get("roofs") if m.get("floors") else None  # (a floor's own room look: its floor and wall colours, its furniture)
            self._floor_surf = _art.surface(grid, m.get("buildings", {}), TILE, own_roofs or m.get("roofs"), own or m.get("theme"))
            self._floor_index = self.run.index
            return
        if self.run.recipe.get("image"):  # a real map: its own picture, a tile for a tile
            path = os.path.join(self.game.assets.assets_dir or "", "walk_routes", f"{self.run.recipe['image']}.png")
            img = pygame.image.load(path).convert()
            self._floor_surf = pygame.transform.scale(img, (f.w * TILE, f.h * TILE))
            self._floor_index = self.run.index
            return
        floor_c, grass_c, wall_c, top_c = COLORS.get(f.style, COLORS["field"])
        surf = pygame.Surface((f.w * TILE, f.h * TILE))
        surf.fill(wall_c)
        rng = random.Random(self.run.index * 7919 + f.w)
        for y in range(f.h):
            for x in range(f.w):
                r = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                t = f.tiles[y][x]
                if t == core.WATER:
                    pygame.draw.rect(surf, floor_c, r)
                    pygame.draw.rect(surf, WATER_C[0], r.inflate(-2, -2), border_radius=8)
                    for i in range(2):
                        yy = r.y + 16 + i * 20
                        pygame.draw.arc(surf, WATER_C[1], (r.x + 8 + i * 10, yy, 22, 10), 0.3, 2.8, 2)
                    continue
                if (x, y) in f.decor:  # a slot machine, the counter
                    body, top = DECOR_C.get(f.decor[(x, y)], ((120, 120, 140), (180, 180, 200)))
                    pygame.draw.rect(surf, floor_c, r)
                    if f.decor[(x, y)] == "slot":
                        pygame.draw.rect(surf, body, r.inflate(-10, -4), border_radius=8)
                        pygame.draw.rect(surf, (30, 30, 40), (r.x + 12, r.y + 10, TILE - 24, 18), border_radius=4)
                        for i in range(3):
                            pygame.draw.circle(surf, top, (r.x + 17 + i * 11, r.y + 19), 4)
                        pygame.draw.rect(surf, top, (r.x + 10, r.bottom - 16, TILE - 20, 6), border_radius=3)
                    elif f.decor[(x, y)] == "poster":  # a poster on the wall (the Game Corner's, with the switch behind it)
                        pygame.draw.rect(surf, top_c, r)
                        pygame.draw.rect(surf, theme.shade(top_c, 1.2), (r.x, r.y, TILE, 8))
                        pygame.draw.line(surf, theme.shade(wall_c, 0.8), (r.x, r.bottom - 1), (r.right, r.bottom - 1), 2)
                        p = pygame.Rect(r.x + 8, r.y + 12, TILE - 16, TILE - 20)
                        pygame.draw.rect(surf, top, p)
                        pygame.draw.rect(surf, body, p, 3)
                        pygame.draw.circle(surf, body, p.center, 7)
                        pygame.draw.circle(surf, (250, 250, 250), p.center, 3)
                    else:
                        pygame.draw.rect(surf, body, r)
                        pygame.draw.rect(surf, top, (r.x, r.y, TILE, 18))
                    continue
                if t == core.WALL and f.style == "building":  # a wall, not a tree
                    near = any(f.walkable(x + dx, y + dy) for dx, dy in core.DIRS)
                    pygame.draw.rect(surf, top_c if near else wall_c, r)
                    if near:
                        pygame.draw.rect(surf, theme.shade(top_c, 1.2), (r.x, r.y, TILE, 8))
                        pygame.draw.line(surf, theme.shade(wall_c, 0.8), (r.x, r.bottom - 1), (r.right, r.bottom - 1), 2)
                    continue
                if t == core.WALL:
                    near = any(f.walkable(x + dx, y + dy) for dx, dy in core.DIRS)
                    if near or rng.random() < 0.5:  # a tree (or a boulder in a cave)
                        pygame.draw.circle(surf, theme.shade(wall_c, 0.7), (r.centerx, r.centery + 6), TILE // 2 - 2)
                        pygame.draw.circle(surf, top_c, (r.centerx, r.centery - 2), TILE // 2 - 6)
                        pygame.draw.circle(surf, theme.shade(top_c, 1.25), (r.centerx - 8, r.centery - 10), TILE // 6)
                    continue
                pygame.draw.rect(surf, floor_c, r)
                if t == core.GRASS:
                    pygame.draw.rect(surf, grass_c, r.inflate(-2, -2), border_radius=6)
                    dark = theme.shade(grass_c, 0.7)
                    for i in range(4):
                        bx = r.x + 8 + i * 11
                        by = r.y + 14 + (i % 2) * 18
                        pygame.draw.polygon(surf, dark, [(bx, by + 14), (bx + 5, by), (bx + 10, by + 14)])
                elif f.style == "sea" and rng.random() < 0.12:  # waves
                    pygame.draw.arc(surf, (190, 220, 250), (r.x + rng.randint(4, 24), r.y + rng.randint(8, 34), 24, 10),
                                    0.3, 2.8, 2)
                elif f.style.startswith("hyper"):  # Hyperspace: a glowing grid, sparks here and there
                    pygame.draw.rect(surf, top_c, r, 1)
                    if rng.random() < 0.04:
                        pygame.draw.circle(surf, theme.shade(top_c, 1.25), (r.x + rng.randint(8, TILE - 8), r.y + rng.randint(8, TILE - 8)), 3)
                elif f.style == "building" and (x + y) % 2 == 0:  # floor tiles
                    pygame.draw.rect(surf, theme.shade(floor_c, 0.95), r)
                elif f.style == "field" and rng.random() < 0.06:  # a few flowers
                    c = rng.choice([(240, 240, 240), (250, 210, 80), (240, 120, 140)])
                    pygame.draw.circle(surf, c, (r.x + rng.randint(10, TILE - 10), r.y + rng.randint(10, TILE - 10)), 4)
        self._floor_surf, self._floor_index = surf, self.run.index

    def _map_backdrop(self):
        """The map around you, sized for the part of the screen above the text box."""
        if self._floor_index != self.run.index or self._floor_surf is None:
            self._render_floor()
        W, top = self.game.width, Utils.get_full_dialogue_rect(self.game).top
        mw, mh = self._floor_surf.get_size()
        cx, cy = self.run.player[0] * TILE + TILE / 2, self.run.player[1] * TILE + TILE / 2
        cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
        cy = mh / 2 if mh <= top else min(max(cy, top / 2), mh - top / 2)
        out = pygame.Surface((W, top))
        out.fill((10, 14, 24))
        out.blit(self._floor_surf, (int(W / 2 - cx), int(top / 2 - cy)))
        return out

    def _sprite(self, key, make):
        sprites = self.__dict__.setdefault("_sprites", {})
        if key not in sprites:
            try:
                self._sprites[key] = make()
            except (pygame.error, OSError, ValueError, TypeError):
                self._sprites[key] = None
        return self._sprites[key]

    def _icon(self, pokemon, size=TILE, flip=False, facing=None):
        """A Pokemon on the map: its overworld sprite (Jordan, 11-06: Everlasting X's following Pokemon,
        stepping, facing its way, as big next to your trainer as in the games), else its party icon."""
        img = self._follower_img(pokemon, facing or ((-1, 0) if flip else (1, 0)))
        if img is not None:
            return img
        from src.minigames.base import icon
        return icon(self.game, pokemon.id, size, flip=flip)

    def _trainer_scale(self):
        """The whole-number scale your trainer's sheet is drawn at (the Pokemon use the same)."""
        if not hasattr(self, "_t_scale"):
            self._t_scale = 2
            try:
                players = sprite_map(self.game).get("players") or {}
                sheet = next(iter(v for v in players.values() if isinstance(v, str)), None)
                if sheet:
                    img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "characters", sheet))
                    cell = img.subsurface((0, 0, img.get_width() // 4, img.get_height() // 4))
                    h = cell.get_bounding_rect().h or cell.get_height()
                    self._t_scale = max(1, round((TILE + 22) / max(1, h)))
            except (pygame.error, OSError, StopIteration):
                pass
        return self._t_scale

    def _follower_img(self, pokemon, facing):
        pid = int(getattr(pokemon, "meta_id", None) or pokemon.id) if int(pokemon.id) >= 2000 else int(pokemon.id)
        shiny = bool(getattr(pokemon, "is_shiny", False))
        frame = (pygame.time.get_ticks() // 160) % 4  # (stepping, as following Pokemon do)
        row = FACING_ROW.get(tuple(facing), 0)

        female = getattr(pokemon, "gender", None) == "F" and str(getattr(pokemon, "form", "normal") or "normal").lower() == "normal"

        def sheet():
            base = os.path.join(self.game.assets.assets_dir, "dungeon", "followers")
            ids = list(dict.fromkeys([int(pokemon.id), pid]))  # (a form's own sheet first: Paldean Tauros)
            form = str(getattr(pokemon, "form", "normal") or "normal").lower()
            names = ([f"{pid}_{form}"] if form != "normal" else []) + [str(i) for i in ids]  # (71_mega, 1017_water_mask)
            if female:  # (Pikachu's heart tail: its own sheet, for the species that have one)
                names.insert(0, f"{pid}_female")
            paths = [os.path.join(base, "shiny", f"{n}.png") for n in names] if shiny else []
            for path in paths + [os.path.join(base, f"{n}.png") for n in names]:
                if os.path.isfile(path):
                    img = pygame.image.load(path).convert_alpha()
                    cw, ch = img.get_width() // 4, img.get_height() // 4
                    box = None  # (the same box for every frame, so it doesn't jitter)
                    for c in range(4):
                        for r in range(4):
                            b = img.subsurface((c * cw, r * ch, cw, ch)).get_bounding_rect()
                            if b.w and b.h:
                                box = b if box is None else box.union(b)
                    return img, cw, ch, box
            return None
        form_key = str(getattr(pokemon, "form", "normal") or "normal").lower()
        data = self._sprite(("follower_sheet", int(pokemon.id), form_key, shiny, female), sheet)
        if not data:
            return None

        def make():
            img, cw, ch, box = data
            box = box or pygame.Rect(0, 0, cw, ch)
            cell = img.subsurface((frame * cw + box.x, row * ch + box.y, box.w, box.h))
            if form_key == "gmax":  # Gigantamax: jumbo, over 2 x 2 tiles (Jordan, 11-06)
                return self._jumbo(cell)
            k = self._trainer_scale()
            return pygame.transform.scale(cell, (cell.get_width() * k, cell.get_height() * k))
        return self._sprite(("follower", int(pokemon.id), form_key, shiny, row, frame, female), make)

    def _sheet_frame(self, sheet, facing=(0, 1), col=None, frame=0, height=None):
        """One cell of a Pokemon Journeys overworld sheet (4 x 4): a person's walking frame (col None: the
        columns are steps), or a Pokemon's (col: whose column), the row by the way it faces."""
        height = height or TILE + 22

        def make():
            img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "characters", sheet)).convert_alpha()
            cw, ch = img.get_width() // 4, img.get_height() // 4
            cell = img.subsurface(((frame if col is None else col) * cw, FACING_ROW.get(facing, 0) * ch, cw, ch))
            box = cell.get_bounding_rect()
            cell = cell.subsurface(box) if box.w and box.h else cell
            k = max(1, round(height / max(1, cell.get_height())))  # whole steps: crisp pixels
            return pygame.transform.scale(cell, (max(1, int(cell.get_width() * k)), max(1, int(cell.get_height() * k))))
        return self._sprite(("sheet", sheet, facing, col, frame, height), make)

    def _surf_draw(self, me, pr, at, k):
        """(bottom, image, rect) for you surfing: the Pokemon carrying you (Pokemon Orre's base_surf sheet,
        bobbing), you on its back; stepping on or off the sea you hop across (an arc) while it stays put."""
        frame = (pygame.time.get_ticks() // 160) % 4
        base = self._sheet_frame("base_surf.png", self.facing, col=frame, height=int(TILE * 0.95))
        bob = int(2 * math.sin(pygame.time.get_ticks() / 180))
        was, now = (self._on_surf(self.anim_from) if self.anim > 0 else True), self._on_surf()
        if was and now:  # riding: it moves with you
            spot, lift = pr, 16 + bob
        elif now:  # hopping on: it waits on the water you hop to
            spot, lift = at(*self.run.player), int(16 * k + 30 * math.sin(k * math.pi))
        else:  # hopping off: it stays on the water you leave
            spot, lift = at(*self.anim_from), int(16 * (1 - k) + 30 * math.sin(k * math.pi))
        out = [(spot.bottom - 1, base, base.get_rect(midbottom=(spot.centerx, spot.bottom + 4 + bob)))]
        out.append((max(pr.bottom, spot.bottom), me, me.get_rect(midbottom=(pr.centerx, pr.bottom - lift))))
        return out

    def _bike_img(self, front=False):
        """The Bicycle under you, drawn (we have no sheet of one): side on, two wheels and a red frame; from the front or
        behind, one wheel and the handlebars. front: only the parts that pass in front of your legs (side on)."""
        side = bool(self.facing[0])
        spin = (self.steps + (1 if self.anim > STEP_FRAMES // 2 else 0)) % 2
        key = ("bike", side, self.facing, front, spin)

        def make():
            s = pygame.Surface((TILE + 8, TILE // 2 + 10), pygame.SRCALPHA)
            w, h = s.get_size()
            tyre, rim, frame = (40, 42, 52), (196, 200, 212), (214, 64, 56)
            if side:
                rad = max(8, h // 2 - 8)  # (two small wheels, well apart)
                for cx in (rad + 3, w - rad - 3):
                    pygame.draw.circle(s, tyre, (cx, h - rad - 2), rad, 3)
                    pygame.draw.circle(s, rim, (cx, h - rad - 2), 2)
                    a = (1, 1) if spin else (1, -1)  # (the spokes turn as you go)
                    pygame.draw.line(s, rim, (cx - a[0] * (rad - 4), h - rad - 2 - a[1] * (rad - 4)), (cx + a[0] * (rad - 4), h - rad - 2 + a[1] * (rad - 4)), 1)
                y0 = h - rad - 2
                way = 1 if self.facing[0] > 0 else -1
                back, fore = (w // 2 - way * (w // 2 - rad - 3), w // 2 + way * (w // 2 - rad - 3))
                pygame.draw.line(s, frame, (back, y0), (w // 2, y0 - rad + 2), 4)
                pygame.draw.line(s, frame, (w // 2, y0 - rad + 2), (fore - way * 4, y0 - rad), 4)
                pygame.draw.line(s, frame, (fore - way * 4, y0 - rad - 4), (fore, y0), 3)
                pygame.draw.line(s, (60, 62, 74), (fore - way * 8, y0 - rad - 5), (fore - way * 1, y0 - rad - 5), 3)
                if not front:
                    pygame.draw.line(s, frame, (back, y0), (w // 2 + way * 2, y0), 3)
            elif not front:  # (head on or from behind: the one wheel you see, under you, and its red mudguard)
                pygame.draw.ellipse(s, tyre, (w // 2 - 7, 2, 14, h - 2))
                pygame.draw.ellipse(s, rim, (w // 2 - 2, 7, 4, h - 12))
                pygame.draw.rect(s, frame, (w // 2 - 8, 2, 16, 6), border_radius=3)
            else:  # (the handlebars, in front of you when you ride towards the camera)
                pygame.draw.line(s, (60, 62, 74), (w // 2 - 17, 6), (w // 2 + 17, 6), 4)
                for gx in (w // 2 - 19, w // 2 + 13):
                    pygame.draw.rect(s, (30, 30, 38), (gx, 3, 6, 7), border_radius=2)
                pygame.draw.rect(s, frame, (w // 2 - 3, 4, 6, 8), border_radius=2)
            return s
        return self._sprite(key, make)

    def _on_stones(self, t=None):
        """Are you on the Jagged Pass's round stones (on the Bicycle: you ride onto them, a wheelie, a hop a stone)?"""
        return tuple(t if t is not None else self.run.player) in getattr(self, "_stones", ())

    def _acro_sheet(self):
        """Emerald's Acro Bike wheelie and hop for Brendan and May (em_acro_<you>.png), else None (the drawn bike)."""
        char = str(getattr(self.game, "player_character", "") or "").lower()
        if char not in ("brendan", "may"):
            return None
        name = f"em_acro_{char}.png"
        return name if os.path.exists(os.path.join(self.game.assets.assets_dir, "dungeon", "characters", name)) else None

    def _player_img(self):
        """You on the map: your trainer's Journeys overworld sprite (yours, else a boy's or a girl's),
        facing the way you go, its feet moving while you step. On the round stones: your wheelie (still) and hop."""
        on = getattr(self, "_on_stones", None) if hasattr(self, "run") else None   # (towns borrow this: no stones there)
        acro = self._acro_sheet() if on and (on() or (self.anim > 0 and on(self.anim_from))) else None
        if acro:
            k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 0
            return self._sheet_frame(acro, self.facing, frame=(0 if self.anim == 0 else 1 if k < 0.5 else 3))
        players = sprite_map(self.game).get("players") or {}
        char = str(getattr(self.game, "player_character", "") or "red").lower()
        sheet = players.get(char) or players.get("female" if char in players.get("girls", []) else "male")
        if not sheet:
            return None
        frame = (1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0
        return self._sheet_frame(sheet, self.facing, frame=frame)

    def _figure_img(self, item, facing=(0, 1), frame=0):
        """A story figure's look: its own sheet ("AREA:TEXT" in dungeon_sprites.json), a boss's Pokemon
        (its overworld sprite, else its party icon), or a townsperson; facing its way, at that step (src/dungeon/npc.py)."""
        sm = sprite_map(self.game)
        spec = (sm.get("figures") or {}).get(f"{self.area_key}:{item.get('text')}") or {}
        if spec.get("item"):
            return self._item_img(spec["item"], 40) or self._sheet_frame("Object ball.png", col=0, height=36)
        if spec.get("draw") == "ghost":  # (the Tower's unknown spirit: nobody can tell what it is yet)
            return self._sprite("ghost_figure", ghost_figure)
        if item.get("action") == "ARRIVAL":
            return self._trainer_img(item["event"].get("trainer") or {}, facing, frame)
        if item.get("action") == "MAX_RAID":  # the den's next raid Pokemon, jumbo (Jordan, 11-06)
            img = self._raid_img()
            if img is not None:
                return img
        pid = spec.get("pokemon")
        if pid is None and item.get("action") == "BOSS" and not spec.get("sheet"):   # (a boss with a sheet of its own: the legend, Emerald's)
            pid = (item.get("boss") or self.area_data.get("area_boss") or {}).get("id")
        if pid is not None:
            ow = (sm.get("pokemon") or {}).get(str(pid))
            if ow:
                return self._sheet_frame(ow[0], (0, 1), col=ow[1], height=TILE + 26)
            from src.minigames.base import icon
            return icon(self.game, int(pid), TILE + 10)
        return self._sheet_frame(scene_sheet(self.game, spec.get("sheet")) or sm.get("townsperson") or "NPC 17.png", tuple(facing), frame=frame)

    JUMBO = TILE * 2 + 34  # a jumbo Pokemon's height on the map (2 x 2 tiles, standing a little over)

    def _raid_img(self):
        rolled = self.roll_raid()
        if not rolled:
            return None
        star, pick = rolled
        gmax = pick.endswith("-gmax")
        pid = int(pick.split("-")[0])

        class _Look:  # (just what the walking sheet needs)
            def __init__(self):
                self.id, self.form, self.is_shiny = pid, "gmax" if gmax else "normal", False
        img = self._follower_img(_Look(), (0, 1))
        if img is None:
            from src.minigames.base import icon
            img = icon(self.game, pid, TILE * 2)
        return self._jumbo(img)

    def _jumbo(self, img):
        """A sprite grown (or shrunk) to the jumbo height, its pixels kept square where they can be."""
        def make():  # (a whole number of times, so its pixels stay square; at least 2 tiles tall)
            k = max(1, round(self.JUMBO / max(1, img.get_height())))
            return pygame.transform.scale(img, (img.get_width() * k, img.get_height() * k))
        return self._sprite(("jumbo", id(img)), make)  # (the frames it's made from are kept: their ids hold)

    def _fit_jumbo(self, m):
        """A Max Raid den's figure takes up 2 x 2 tiles: moved, once, to where all four are free."""
        if getattr(m, "size", 1) > 1 or not isinstance(m.payload, dict) or m.payload.get("action") != "MAX_RAID":
            return
        f = self.run.floor
        px, py = self.run.player

        def fits(x, y):
            tiles = [(x + i, y + j) for i in range(2) for j in range(2)]
            return all(f.walkable(*t) and t not in f.exits and (t == (m.x, m.y) or not f.occupied(*t))
                       and t != (px, py) for t in tiles)
        spots = sorted(((x, y) for x in range(1, f.w - 2) for y in range(1, f.h - 2)),
                       key=lambda t: abs(t[0] - m.x) + abs(t[1] - m.y))
        spot = next((t for t in spots[:400] if fits(*t)), None)
        if spot:
            m.x, m.y = spot
            m.size = 2

    def _trainer_img(self, info, facing=(0, 1), frame=0):
        name = info.get("sprite") or "rival.png"
        sm = sprite_map(self.game)
        own = sm.get("trainers_" + str(self.area_data.get("region") or "")) or {}
        for _role in ("rival", "friend"):  # (this save's rival or friend: their own walking sheet, where the region has one: Hoenn's Brendan and May)
            _who = str(getattr(self.game, f"{_role}_character", "") or "").lower()
            if name == "{%s_character}" % _role and _who and f"{_who}.png" in own:
                name = f"{_who}.png"
        sheet = own.get(name) or (sm.get("trainers") or {}).get(name)  # (the class as this region's own game draws it, where we have that: "trainers_SINNOH")
        if sheet:  # its Pokemon Journeys overworld sprite, looking the way it faces (mid-step: its stepping frame)
            return self._sheet_frame(sheet, tuple(facing), frame=frame)

        def make():
            img = _trainer_sprite(self.game, name)
            if img is None:
                return None
            box = img.get_bounding_rect()
            img = img.subsurface(box) if box.w and box.h else img
            k = (TILE + 18) / max(1, img.get_height())
            return pygame.transform.smoothscale(img, (max(1, int(img.get_width() * k)), TILE + 18))
        return self._sprite(("trainer", name), make)

    def _item_img(self, key, size=34):
        def make():
            img = self.game.assets.get_item_image("POKE_BALL" if key == catching.POKE else
                                                  "HONEY" if key == self.HONEY_PACK else key)
            if img is None:
                return None
            return pygame.transform.smoothscale(img, (size, size))
        return self._sprite(("item", key, size), make)

    def _ball_img(self, size=34):
        return self._sprite(("ball", size), lambda: pygame.transform.smoothscale(self.game.assets.ball_imgs[0], (size, size)))

    def _area_name(self, key):
        item = self.exit_items.get(key)
        if item:
            return travel_label(self.game, item)
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        return (prog.get(key) or {}).get("route_name") or key.replace("_", " ").title()

    def lead(self):
        team = self.game.story_manager.player_team
        return next((p for p in team if p and p.current_hp > 0), team[0] if team else None)

    _backdrop = False
    _ow_foe = None  # (the wild Pokemon an OVERWORLD-style battle is drawing itself)

    def draw_backdrop(self, screen):
        """Just the map (its tiles, the people on it, you): behind an OVERWORLD-style battle."""
        self._backdrop = True
        try:
            self.draw()
        finally:
            self._backdrop = False

    def draw(self):
        if self.mode == "CATCH":
            return super().draw()
        screen = self.game.screen
        W, H = self.game.width, self.game.height
        f = self.run.floor
        view = self._view()
        screen.fill(FRAME_BLACK)
        screen.fill((10, 14, 24), view)  # (the fog's colour: the unknown edge of the map)
        screen.set_clip(view)  # (the map stays in its frame)
        if self._floor_index != self.run.index or self._floor_surf is None:
            self._render_floor()
        ox, oy = self._origin()
        screen.blit(self._floor_surf, (ox, oy))
        x0, y0 = max(0, (view.x - ox) // TILE - 1), max(0, (view.y - oy) // TILE - 1)
        x1, y1 = min(f.w, (view.right - ox) // TILE + 2), min(f.h, (view.bottom - oy) // TILE + 2)
        fonts = self.game.assets.fonts

        def at(x, y):
            return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

        self._draw_tap_marks(screen, at)

        # things lying about (in tiles you've seen)
        real = self.run.recipe.get("image") or self.run.recipe.get("art")
        signs = []  # (drawn over the map's things, last)
        if real:  # a real map's ways out: the road itself, and one sign over it saying where it goes
            ways = {}
            for (x, y), target in f.exits.items():
                if str(target).startswith("WARP:") or target == "BOSS":  # (a passage between floors, a sleeping boss: no road sign)
                    continue
                ways.setdefault(target, []).append((x, y))
            for target, tiles in ways.items():
                tiles.sort()
                x, y = tiles[len(tiles) // 2]
                r = at(x, y)
                name = (self._floor_name(self.run.index + (1 if target == core.STAIRS else -1))
                        if target in (core.STAIRS, core.STAIRS_UP) else self._area_name(target))
                tag = fonts["caption"].render(theme.pokemon_word(str(name).upper()), True, (255, 255, 255))
                pill = tag.get_rect(center=r.center).inflate(12, 6)  # (on the road itself, out of your way)
                if not view.inflate(120, 120).colliderect(pill):
                    continue  # (off screen: no sign piling up at the edge)
                pill.clamp_ip(view.inflate(-8, -8))
                signs.append((pill, tag))
        for (x, y), target in f.exits.items():
            if (x, y) not in f.seen:
                continue
            if real:  # (our own maps: no signpost, but what's in the way shows: a Cut tree, a rock, till it's used)
                gate = self._gate(target)
                used = self.game.story_manager.story_flags.get(f"gate_used_{self.area_key}_{target}")
                if gate and (not gate[2] or (gate[1] and not used)):
                    self._draw_gate(screen, at(x, y), gate[0])
                continue
            r = at(x, y)
            if target in (core.STAIRS, core.STAIRS_UP) and self.run.recipe.get("open"):
                # an opening in the edge: a signpost with an arrow, the next area's name
                to = self.run.index + (1 if target == core.STAIRS else -1)
                pygame.draw.rect(screen, (150, 104, 60), (r.centerx - 4, r.y + 22, 8, TILE - 24))
                pygame.draw.rect(screen, (214, 172, 104), (r.x + 4, r.y + 6, TILE - 8, 22), border_radius=5)
                tip = r.right - 10 if target == core.STAIRS else r.x + 10
                tail = r.x + 12 if target == core.STAIRS else r.right - 12
                pygame.draw.line(screen, (110, 72, 40), (tail, r.y + 17), (tip, r.y + 17), 3)
                d = -1 if target == core.STAIRS else 1
                pygame.draw.polygon(screen, (110, 72, 40), [(tip, r.y + 17), (tip + 7 * d, r.y + 11), (tip + 7 * d, r.y + 23)])
                name = self._floor_name(to) if self.per_floor == 1 else self._zone_name(self._zone_index(
                    to, 0 if target == core.STAIRS else 10 ** 6))
                label = (name + "  >") if target == core.STAIRS else ("<  " + name)
            elif target in (core.STAIRS, core.STAIRS_UP):
                pygame.draw.rect(screen, (60, 52, 44), r.inflate(-6, -6), border_radius=6)
                for i in range(4):
                    pygame.draw.line(screen, (196, 180, 150), (r.x + 10, r.y + 12 + i * 9), (r.right - 10, r.y + 12 + i * 9), 3)
                to = self.run.index + (1 if target == core.STAIRS else -1)
                label = self._floor_name(to) if self.zones else ("UP" if target == core.STAIRS_UP else "STAIRS")
            else:
                gate = self._gate(target)
                if gate and not gate[2]:
                    self._draw_gate(screen, r, gate[0])
                else:
                    pygame.draw.rect(screen, (150, 104, 60), (r.centerx - 4, r.y + 20, 8, TILE - 22))
                    pygame.draw.rect(screen, (214, 172, 104), (r.x + 4, r.y + 4, TILE - 8, 24), border_radius=5)
                    pygame.draw.rect(screen, (110, 72, 40), (r.x + 4, r.y + 4, TILE - 8, 24), 2, border_radius=5)
                label = self._area_name(target)
            tag = fonts["caption"].render(theme.pokemon_word(label.upper()), True, (255, 255, 255))
            pill = tag.get_rect(midbottom=(r.centerx, r.y - 2)).inflate(12, 6)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
            screen.blit(tag, tag.get_rect(center=pill.center))
        if getattr(self, "per_floor", 1) > 1 and self.zones and not (self.recipe.get("art") or {}).get("zone_rects"):
            per = self.per_floor
            for part in range(1, per):
                gx = part * f.w // per
                if self._zone_index(self.run.index, gx) == self._zone_index(self.run.index, gx - 1):
                    continue
                for gy in range(y0, y1):
                    if f.walkable(gx, gy) and (gx, gy) in f.seen:
                        r = at(gx, gy)
                        pygame.draw.line(screen, (250, 220, 90), (r.x + 2, r.y), (r.x + 2, r.bottom), 5)
                        pygame.draw.line(screen, (120, 80, 30), (r.x + 6, r.y), (r.x + 6, r.bottom), 2)
                top = next((gy for gy in range(f.h) if f.walkable(gx, gy)), None)
                if top is not None:
                    name = self._zone_name(self._zone_index(self.run.index, gx))
                    tag = fonts["caption"].render(theme.pokemon_word(name.upper()) + " >", True, (255, 255, 255))
                    pill = tag.get_rect(midbottom=(at(gx, top).centerx, at(gx, top).y - 2)).inflate(12, 6)
                    pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
                    screen.blit(tag, tag.get_rect(center=pill.center))
        for (x, y), key in f.items.items():
            if (x, y) in f.seen:
                img = self._item_img(key) or self._ball_img()
                screen.blit(img, img.get_rect(center=at(x, y).center))
        bob = int(3 * math.sin(pygame.time.get_ticks() / 180))
        for (x, y) in f.tm_spots:
            if (x, y) in f.seen:
                img = self._ball_img(38)
                glow = at(x, y).inflate(-8, -8)
                pygame.draw.ellipse(screen, (255, 236, 140), glow, 3)
                screen.blit(img, img.get_rect(center=(glow.centerx, glow.centery + bob)))
        for (x, y), what in f.decor.items():  # boulders (Strength and the slide puzzle push them aside)
            if str(what).startswith("soil:") and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:  # (soft soil and its Berry tree)
                from src.world import berries as _berries
                r = at(x, y)
                _rec = _berries.record(self.game.story_manager, self.area_key, (x, y), getattr(self, "_soil", {}).get((x, y)))
                _soil, _plant = self._berry_img(_rec, _berries.stage(_rec))
                if _soil is not None:
                    s2 = pygame.transform.scale(_soil, (r.w, r.h))
                    s2.set_alpha(170)
                    screen.blit(s2, r)
                if _plant is not None:
                    k = r.w / _plant.get_width()
                    p2 = pygame.transform.scale(_plant, (r.w, int(_plant.get_height() * k)))
                    screen.blit(p2, p2.get_rect(midbottom=(r.centerx, r.bottom - 2)))
                continue
            if str(what).startswith("crate:") and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:  # (a crate: the map's own crate picture)
                r = at(x, y)
                img = self._crate_img()
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom)))
                continue
            if str(what).startswith(("boulder:", "fallen:", "rubble:")) and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:
                r = at(x, y)
                img = self._sheet_frame("Object boulder.png", col=0, height=TILE - 4)
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
            elif str(what).startswith("barrier:") and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:  # (the cycling gate's striped bar)
                r = at(x, y)
                if getattr(self, "_bars", {}).get((x, y), {}).get("look") == "hidden":  # (a door you can't see: plain rock, like the wall around it)
                    if getattr(self, "_rock_tile", None) is None:
                        from src.dungeon import art as _art
                        self._rock_tile = _art.surface(["ccc", "ccc", "ccc"], {}, TILE, None, None).subsurface((TILE, TILE, TILE, TILE)).copy()
                    screen.blit(self._rock_tile, r)
                    continue
                _look = str(getattr(self, "_bars", {}).get((x, y), {}).get("look") or "")
                if _look == "unseen":  # (something invisible in the way: Route 120's Kecleon, till the Devon Scope)
                    continue
                if _look.startswith(("sheet:", "ow:", "mon:", "ribbon:")):  # (someone or something standing there: "sheet:<walking sheet>", "ow:<folder>:<thing>" of a real game's own, "mon:<species number>": a scene's people, a briefcase, a wild Pokemon)
                    img = self._stand_in_img(_look, self._bars.get((x, y), {}))
                    if img:
                        screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
                    continue
                if getattr(self, "_bars", {}).get((x, y), {}).get("look") in ("psyduck", "grunt", "guard", "person"):  # (someone standing in the way)
                    from src.dungeon import art as _art
                    _art.blocker(screen, r, self._bars[(x, y)]["look"])
                    continue
                if getattr(self, "_bars", {}).get((x, y), {}).get("look") == "storm":  # (a sandstorm in the way: Route 111's desert)
                    tt = pygame.time.get_ticks() / 140
                    veil = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                    veil.fill((214, 190, 120, 150))
                    for k4 in range(4):
                        yy = int((k4 * r.h / 4 + tt * 3 + x * 7) % r.h)
                        xx = int((tt * 9 + k4 * 13 + y * 5) % r.w)
                        pygame.draw.line(veil, (246, 232, 180, 220), (xx, yy), (min(r.w, xx + r.w // 2), max(0, yy - 4)), 2)
                    screen.blit(veil, r)
                    continue
                pygame.draw.rect(screen, (90, 90, 100), (r.x + 4, r.centery - 2, 6, r.h // 2))
                pygame.draw.rect(screen, (90, 90, 100), (r.right - 10, r.centery - 2, 6, r.h // 2))
                for k4 in range(4):
                    pygame.draw.rect(screen, (220, 50, 50) if k4 % 2 else (245, 245, 245), (r.x + 4 + k4 * (r.w - 8) // 4, r.centery - 8, (r.w - 8) // 4, 10))
        # wild Pokemon and trainers you can see
        emotes = []
        for m in f.movers:
            if not self.run.visible(m.x, m.y) or m is self._ow_foe:
                continue
            r = at(m.x, m.y)
            mo = getattr(m, "motion", None)
            if mo is not None:  # (a person mid-step: between the two tiles)
                ax, ay = mo.at()
                r = r.move(int(round((ax - m.x) * TILE)), int(round((ay - m.y) * TILE)))
                if mo.emote > 0:
                    emotes.append(r)
            if m.kind == "wild":
                img = self._icon(m.payload, TILE, flip=(m.x < self.run.player[0]), facing=getattr(m, "facing", None))
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom + 4)))
                if m.payload.is_shiny:
                    pygame.draw.circle(screen, (255, 230, 90), (r.right - 8, r.y + 8), 5)
                if m.alert:
                    theme.shadow_text(screen, "!", fonts["label"], r.right - 6, r.y - 18, color=(220, 60, 50))
            elif m.kind == "figure":
                self._fit_jumbo(m)
                img = self._figure_img(m.payload, mo.facing, mo.frame()) if mo is not None else self._figure_img(m.payload)
                if img and getattr(m, "size", 1) > 1:  # a Max Raid's Pokemon: jumbo, over its 2 x 2 tiles
                    bob = int(3 * math.sin(pygame.time.get_ticks() / 400))
                    glow = pygame.Rect(r.x, r.y, TILE * 2, TILE * 2).inflate(-6, -30).move(0, 22)
                    pygame.draw.ellipse(screen, (200, 60, 120), glow, 4)
                    screen.blit(img, img.get_rect(midbottom=(r.right, r.bottom + TILE - 4 + bob)))
                    theme.shadow_text(screen, "!", fonts["label"], r.right + TILE - 6, r.y - 30, color=(250, 90, 160))
                    continue
                if img:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
                else:
                    pygame.draw.circle(screen, (200, 170, 60), r.center, TILE // 3)
                theme.shadow_text(screen, "!", fonts["label"], r.right - 4, r.y - 20, color=(250, 210, 60))
                what = str(m.payload.get("text", ""))
                if what.startswith("TAKE "):  # a thing to pick (Mt. Moon's two fossils): its name under it
                    tag = fonts["small"].render(what[5:], True, (255, 255, 255))
                    pill = tag.get_rect(midtop=(r.centerx, r.bottom + 2)).inflate(10, 4)
                    pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=6)
                    screen.blit(tag, tag.get_rect(center=pill.center))
                continue
            else:
                img = self._trainer_img(m.payload[1], m.facing, mo.frame() if mo is not None else 0)
                lift = 0
                if f.tile(m.x, m.y) == core.SURF:  # (out on the sea: riding a Pokemon too)
                    frame = (pygame.time.get_ticks() // 160 + m.x) % 4
                    base = self._sheet_frame("base_surf.png", m.facing, col=frame, height=int(TILE * 0.95))
                    bob = int(2 * math.sin(pygame.time.get_ticks() / 180 + m.x))
                    screen.blit(base, base.get_rect(midbottom=(r.centerx, r.bottom + 4 + bob)))
                    lift = 16 + bob
                if img:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - lift)))
                else:
                    pygame.draw.circle(screen, (90, 90, 160), r.center, TILE // 3)
                # which way it's looking
                fx, fy = m.facing
                tip = (r.centerx + fx * (TILE // 2 + 6), r.centery + fy * (TILE // 2 + 6))
                pygame.draw.circle(screen, (255, 255, 255), tip, 5)
                pygame.draw.circle(screen, (40, 40, 60), tip, 5, 2)
        for a in (self._scenes().actors if hasattr(self, "run") else []):  # a scene's cast, walking in and out
            ax, ay = a["m"].at()
            if not self.run.visible(int(round(ax)), int(round(ay))):  # (in the fog, like everyone else)
                continue
            ar = at(int(round(ax)), int(round(ay))).move(int(round((ax - round(ax)) * TILE)), int(round((ay - round(ay)) * TILE)))
            img = self._actor_img(a["sheet"], a["m"].facing, a["m"].frame())
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(ar.centerx, ar.bottom - 2)))
        for er in emotes:  # (someone has noticed you: a "!" over them)
            theme.shadow_text(screen, "!", fonts["label"], er.centerx - 4, er.y - 34, color=(230, 60, 50))
        # you, your trainer, with your lead Pokemon a step behind
        k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 1
        lead = self.lead()
        pr = pygame.Rect(0, 0, TILE, TILE)
        (fx0, fy0), (tx0, ty0) = (self.anim_from if self.anim > 0 else self.run.player), self.run.player
        pr.topleft = (int(ox + (fx0 + (tx0 - fx0) * k) * TILE), int(oy + (fy0 + (ty0 - fy0) * k) * TILE))  # (you, mid-step)
        stones = self._on_stones() or (self.anim > 0 and self._on_stones(self.anim_from))
        if self.hop and self.anim > 0:  # (over a ledge: up and down again; from stone to stone on the Bicycle, a smaller hop)
            pr.y -= int(math.sin(math.pi * k) * TILE * (0.3 if stones else 0.55))
        elif self.hop:
            self.hop = False
        if stones and self.anim == 0:  # (on a stone, balanced on the back wheel: a little bounce)
            pr.y -= int(abs(math.sin(pygame.time.get_ticks() / 140)) * 5)
        me = self._player_img()
        drawn = []  # (bottom, image, rect): the lower one in front
        surfing = self._on_surf() or (self.anim > 0 and self._on_surf(self.anim_from))
        if lead and self.partner != self.run.player and me is not None and not self._backdrop and not surfing:
            # (a battle draws its own; while you surf your Pokemon is the one carrying you)
            (fx, fy), (tx, ty) = self.partner_from, self.partner
            pk = k
            r = pygame.Rect(int(ox + (fx + (tx - fx) * pk) * TILE), int(oy + (fy + (ty - fy) * pk) * TILE), TILE, TILE)
            look = self.run.player
            way = (look[0] - tx, look[1] - ty)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            img = self._icon(lead, TILE, flip=(self.run.player[0] > tx), facing=way)
            drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
        if me is not None and surfing:  # on the sea: you ride your Pokemon (a hop on and off)
            drawn += self._surf_draw(me, pr, at, k)
        elif me is not None and stones and self._acro_sheet():  # (on the round stones: your own wheelie, Emerald's Acro Bike frames)
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
        elif me is not None and (stones or self._cycling() or (self.anim > 0 and self._cycling(self.anim_from))):  # riding the Bicycle
            bike = self._bike_img()
            drawn.append((pr.bottom - 1, bike, bike.get_rect(midbottom=(pr.centerx, pr.bottom + (2 if self.facing[0] else 8)))))
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom - 8))))
            if self.facing[0]:  # (side on: the near wheel and the frame pass in front of your legs)
                front = self._bike_img(front=True)
                drawn.append((pr.bottom + 1, front, front.get_rect(midbottom=(pr.centerx, pr.bottom + 2))))
            elif self.facing[1] > 0:  # (towards the camera: the handlebars in front of you)
                front = self._bike_img(front=True)
                drawn.append((pr.bottom + 1, front, front.get_rect(midtop=(pr.centerx, pr.bottom - 30))))
        elif me is not None:
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
        elif lead:  # (no trainer sprite: your lead Pokemon walks for you)
            img = self._icon(lead, TILE + 8, flip=(self.facing[0] > 0), facing=self.facing)
            drawn.append((pr.bottom, img, img.get_rect(center=(pr.centerx, pr.centery - 4))))
        wk = getattr(self, "_walker", None)
        if wk:  # (someone walking up to you: between two tiles of their path)
            i = min(int(wk["i"]), len(wk["path"]) - 1)
            a, b = wk["path"][i], wk["path"][min(i + 1, len(wk["path"]) - 1)]
            fr = wk["i"] - i
            ra, rb = at(*a), at(*b)
            wx, wy = ra.centerx + (rb.centerx - ra.centerx) * fr, ra.bottom + (rb.bottom - ra.bottom) * fr
            way = (b[0] - a[0], b[1] - a[1]) if a != b else (self.run.player[0] - a[0], self.run.player[1] - a[1])
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            if wk.get("leaving"):
                way = (-way[0], -way[1])
            wimg = self._sheet_frame(wk["sheet"], way, frame=int(wk["i"] * 2) % 4 if a != b and (wk["i"] < len(wk["path"]) - 1 or wk.get("leaving")) else 0)
            if wimg is not None:
                drawn.append((wy, wimg, wimg.get_rect(midbottom=(int(wx), int(wy) - 2))))
            if wk.get("with"):  # (their companion: the same way, two steps behind going, two ahead leaving)
                j = max(0.0, wk["i"] - 2.0)
                i2 = min(int(j), len(wk["path"]) - 1)
                a2, b2 = wk["path"][i2], wk["path"][min(i2 + 1, len(wk["path"]) - 1)]
                f2 = j - i2
                ra2, rb2 = at(*a2), at(*b2)
                x2, y2 = ra2.centerx + (rb2.centerx - ra2.centerx) * f2, ra2.bottom + (rb2.bottom - ra2.bottom) * f2
                way2 = (b2[0] - a2[0], b2[1] - a2[1]) if a2 != b2 else way
                way2 = (max(-1, min(1, way2[0])), 0) if way2[0] else (0, max(-1, min(1, way2[1])) or 1)
                if wk.get("leaving"):
                    way2 = (-way2[0], -way2[1])
                img2 = self._sheet_frame(wk["with"], way2, frame=int(j * 2) % 4 if (wk["i"] < len(wk["path"]) - 1 or wk.get("leaving")) and j > 0 else 0)
                drawn.append((y2, img2, img2.get_rect(midbottom=(int(x2), int(y2) - 2))))
        for _b, img, rect in sorted(drawn, key=lambda t: t[0]):
            screen.blit(img, rect)
        spans = getattr(self.run.floor, "bridge", None)
        _pic = ((self.run.recipe.get("art") or {}).get("roofs") or {}).get("_picture")  # (a map drawn from its game's picture: its own top layer goes over you)
        if spans and not self.run.deck and self.run.recipe.get("art") and not _pic:  # (passing under a log bridge: it goes over your head)
            from src.dungeon import art as _art
            for t in {self.run.player, self.anim_from if self.anim > 0 else self.run.player}:
                if t in spans:
                    _art.bridge(screen, at(*t), "|" if spans[t] == (0, 1) else ";")
        for img, (bx, by) in self._overheads():  # (what passes over your head: you walk under it, out of view)
            screen.blit(img, (ox + bx, oy + by))
        # the fog: unseen tiles are dark, seen ones you can't see right now are dimmed
        fog = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        fog.fill((10, 14, 24, 150))
        for y in range(y0, y1):
            for x in range(x0, x1):
                r = at(x, y)
                if (x, y) not in f.seen:
                    screen.fill((10, 14, 24), r)
                elif not self.run.visible(x, y):
                    screen.blit(fog, r)

        for pill, tag in signs:  # where the ways out go
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
            screen.blit(tag, tag.get_rect(center=pill.center))
        if self.run.explore:  # (a first visit: what you haven't seen yet)
            seen = f.seen
            for gy in range(y0, y1):
                for gx in range(x0, x1):
                    if (gx, gy) not in seen:
                        screen.fill((10, 14, 24), at(gx, gy))
        if self._backdrop:  # (only the map: an OVERWORLD-style battle is drawn over it)
            screen.set_clip(None)
            return
        if self.mode == "MAP":
            self._draw_guide(screen, at)
        screen.set_clip(None)
        draw_frame(screen, view)
        self._draw_hud(screen)
        self._draw_qparty(screen)
        if self.mode in ("CHOICE", "MATH", "THROW"):
            self._draw_encounter(screen)
        elif self.mode == "SPOTTED" and self.encounter:
            m = self.encounter
            r = at(m.x, m.y)
            bubble = pygame.Rect(0, 0, 40, 46)
            bubble.midbottom = (r.centerx, r.y - 22)
            pygame.draw.rect(screen, (255, 255, 255), bubble, border_radius=10)
            pygame.draw.rect(screen, (40, 40, 60), bubble, 3, border_radius=10)
            theme.shadow_text(screen, "!", fonts["button"], bubble.centerx, bubble.centery, color=(220, 60, 50), align="center")
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)
        for b in self.hud_buttons:
            b.draw(screen)

    # ---------------------------------------------------------------- the way to go (Jordan, 11-06)
    def _guide_spot(self):
        """(tile, label) on this floor for the Journal's tracked mission: a story figure or boss here that
        does what it needs, else the way out toward its next stop, else the stairs toward the floor with
        that way out. None when there's nowhere to point."""
        from src.world import guide
        key = (self.run.index, self.run.turn, len(self.run.floor.movers), pygame.time.get_ticks() // 1000)
        if getattr(self, "_guide_key", None) == key:
            return self._guide_hit
        self._guide_key, self._guide_hit = key, None
        f = self.run.floor
        story = self.game.story_manager
        mission = guide.tracked_mission(self.game)
        need = {f for f in story.mission_flags(mission or {}) if not story.story_flags.get(f)}
        for m in f.movers:  # someone here the mission needs
            if m.kind == "figure" and isinstance(m.payload, dict) and guide.advances_goal(self.game, self.area_key, m.payload):
                self._guide_hit = ((m.x, m.y), m.payload.get("text") or "Here")
                return self._guide_hit
            if m.kind == "trainer" and need and isinstance(m.payload, tuple) and \
                    (m.payload[1] or {}).get("victory_flag") in need:
                self._guide_hit = ((m.x, m.y), "Battle")
                return self._guide_hit
        hop = guide.cached(self.game, "hop")
        if not hop or hop == self.area_key:
            return None
        if self.run.n_floors == 1:  # (one floor: the map's own way out with the shortest trip, if the next stop isn't one)
            hop = guide.map_hop(self.game, f.exits.values()) or hop
        px, py = self.run.player
        spot = min((t for t, target in f.exits.items() if target == hop),
                   key=lambda t: abs(t[0] - px) + abs(t[1] - py), default=None)  # (the nearest of them)
        if spot:
            self._guide_hit = (spot, self._exit_label(hop))
            return self._guide_hit
        # the way out is on another floor: the stairs toward it
        if self.run.n_floors > 1:
            there = None
            if self.run.exits_by_floor:
                there = next((k for k, (ent, fwd) in self.run.exits_by_floor.items() if hop == ent or hop in fwd), None)
            if there is None:
                there = 0 if hop == self.run.entrance else self.run.n_floors - 1
            if there != self.run.index:
                want = core.STAIRS if there > self.run.index else core.STAIRS_UP
                stairs = next((t for t, target in f.exits.items() if target == want), None)
                if stairs:
                    self._guide_hit = (stairs, "Upstairs" if want == core.STAIRS_UP else "Downstairs")
                    return self._guide_hit
        return None

    def _draw_gate(self, screen, r, kind):
        """What stands in a locked way out, on its tile."""
        t = pygame.time.get_ticks()
        cx, cy = r.center
        if kind == "tree":  # a small, cuttable tree
            pygame.draw.rect(screen, (96, 64, 40), (cx - 4, cy + 4, 8, r.h // 2 - 4))
            for dx, dy, rad, col in ((0, -2, 17, (30, 92, 54)), (-7, 2, 11, (44, 122, 64)), (7, 2, 11, (44, 122, 64)),
                                     (0, -8, 10, (70, 156, 80)), (-4, -12, 4, (150, 210, 120))):
                pygame.draw.circle(screen, col, (cx + dx, cy + dy), rad)
        elif kind == "rock":  # a cracked rock
            pygame.draw.ellipse(screen, (80, 72, 70), r.inflate(-6, -10).move(0, 4))
            pygame.draw.ellipse(screen, (150, 140, 130), r.inflate(-10, -16).move(0, 2))
            pygame.draw.lines(screen, (70, 62, 60), False, [(cx - 10, cy - 6), (cx - 2, cy + 2), (cx + 4, cy - 4), (cx + 12, cy + 6)], 3)
        elif kind == "boulder":  # a big round boulder
            pygame.draw.circle(screen, (70, 64, 66), (cx, cy + 2), r.w // 2 - 2)
            pygame.draw.circle(screen, (136, 128, 124), (cx - 2, cy), r.w // 2 - 6)
            pygame.draw.circle(screen, (180, 172, 164), (cx - 8, cy - 8), 6)
        elif kind in ("water", "whirlpool", "waterfall"):
            pygame.draw.rect(screen, (40, 110, 200), r)
            if kind == "waterfall":
                for x in range(r.x + 4, r.right - 2, 8):
                    y0 = (t // 40 + x) % 16
                    for y in range(r.y - 16 + y0, r.bottom, 16):
                        pygame.draw.line(screen, (220, 240, 255), (x, max(r.y, y)), (x, min(r.bottom, y + 8)), 3)
            elif kind == "whirlpool":
                a = t / 300
                for k in range(3):
                    rad = r.w // 2 - 4 - k * 7
                    pygame.draw.arc(screen, (220, 240, 255), (cx - rad, cy - rad, 2 * rad, 2 * rad), a + k, a + k + 3.6, 3)
            else:
                for k in range(2):
                    y = r.y + 14 + k * 18 + int(2 * math.sin(t / 250 + k))
                    pygame.draw.arc(screen, (180, 220, 255), (r.x + 6, y, 14, 8), 0, 3.14, 2)
                    pygame.draw.arc(screen, (180, 220, 255), (r.x + 22, y + 4, 14, 8), 0, 3.14, 2)
        elif kind == "dark":  # a pitch-dark cave mouth
            pygame.draw.ellipse(screen, (60, 50, 44), r.inflate(-2, 4).move(0, 4))
            pygame.draw.ellipse(screen, (6, 6, 10), r.inflate(-12, -6).move(0, 8))
        elif kind == "bike":  # the cycling gate's barrier
            pygame.draw.rect(screen, (90, 90, 100), (r.x + 4, cy - 2, 6, r.h // 2))
            pygame.draw.rect(screen, (90, 90, 100), (r.right - 10, cy - 2, 6, r.h // 2))
            for k in range(4):
                pygame.draw.rect(screen, (220, 50, 50) if k % 2 else (245, 245, 245), (r.x + 4 + k * (r.w - 8) // 4, cy - 8, (r.w - 8) // 4, 10))
        elif kind == "boss":  # the route's Pokemon, asleep across the way
            pid = (self.area_data.get("area_boss") or {}).get("id")
            img = self._boss_sprite(pid) if pid else None
            if img:
                bob = int(2 * math.sin(t / 600))
                screen.blit(img, img.get_rect(midbottom=(cx, r.bottom + 6 + bob)))
                if (t // 700) % 2:  # Zzz
                    z = self.game.assets.fonts["caption"].render("Z z", True, (255, 255, 255))
                    screen.blit(z, (r.right - 6, r.y - 18))

    def _boss_sprite(self, pid):
        def make():
            img = self.game.assets.get_pokemon_image(pid, "normal", False)
            if img is None:
                return None
            box = img.get_bounding_rect()
            img = img.subsurface(box) if box.w and box.h else img
            k = (TILE * 1.9) / max(img.get_width(), img.get_height())
            return pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
        return self._sprite(("boss_gate", pid), make)

    def _exit_label(self, key):
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        return theme.pokemon_word((prog.get(key) or {}).get("route_name") or key.replace("_", " ").title())

    def _draw_guide(self, screen, at):
        """A gold marker on the tile to go to (bobbing, once you've seen it), or an arrow at the edge of
        the screen pointing to it, with where it leads."""
        hit = self._guide_spot()
        if not hit:
            return
        (gx, gy), label = hit
        v = self._view()
        fonts = self.game.assets.fonts
        t = pygame.time.get_ticks()
        r = at(gx, gy)
        gold, dark = (255, 214, 64), (60, 40, 10)
        on_screen = r.right > v.x and r.left < v.right and r.bottom > v.y + 2 and r.top < v.bottom - 20
        if on_screen:
            pulse = 4 + int(3 * (1 + math.sin(t / 160)))
            pygame.draw.rect(screen, gold, r.inflate(pulse, pulse), 4, border_radius=10)
            bob = int(6 * math.sin(t / 180))
            lift = self._guide_lift((gx, gy))  # (a tile already named: the arrow goes above its name)
            is_exit = lift is not None
            tip = (r.centerx, r.top - (lift if is_exit else 10) + bob)
            pts = [tip, (tip[0] - 14, tip[1] - 20), (tip[0] + 14, tip[1] - 20)]
            pygame.draw.polygon(screen, dark, [(x + 2, y + 2) for x, y in pts])
            pygame.draw.polygon(screen, gold, pts)
            if is_exit:
                return
            tag = fonts["caption"].render(label, True, (255, 255, 255))
            pill = tag.get_rect(midbottom=(r.centerx, tip[1] - 24)).inflate(14, 6)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
            pygame.draw.rect(screen, gold, pill, 2, border_radius=8)
            screen.blit(tag, tag.get_rect(center=pill.center))
            return
        # off screen: an arrow on the edge, toward it
        cx, cy = v.center
        dx, dy = r.centerx - cx, r.centery - cy
        n = math.hypot(dx, dy) or 1
        ux, uy = dx / n, dy / n
        room_x, room_y = v.w / 2 - 50, v.h / 2 - 50
        k = min(room_x / abs(ux) if ux else 1e9, room_y / abs(uy) if uy else 1e9)
        ax, ay = cx + ux * k, cy + uy * k + 10
        size = 26 + 4 * math.sin(t / 160)
        px, py = -uy, ux
        pts = [(ax + ux * size, ay + uy * size), (ax - ux * size * 0.6 + px * size * 0.8, ay - uy * size * 0.6 + py * size * 0.8),
               (ax - ux * size * 0.6 - px * size * 0.8, ay - uy * size * 0.6 - py * size * 0.8)]
        pygame.draw.polygon(screen, dark, [(x + 3, y + 3) for x, y in pts])
        pygame.draw.polygon(screen, gold, pts)
        pygame.draw.polygon(screen, (255, 255, 255), pts, 2)
        tag = fonts["caption"].render(label, True, (255, 255, 255))
        pill = tag.get_rect(center=(ax - ux * (size + 30), ay - uy * (size + 22))).inflate(14, 6)
        pill.clamp_ip(v.inflate(-8, -8))
        pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
        pygame.draw.rect(screen, gold, pill, 2, border_radius=8)
        screen.blit(tag, tag.get_rect(center=pill.center))

    def _guide_lift(self, t):
        """How far above a tile the guide's arrow sits when the tile has its own name (None: it doesn't)."""
        return 44 if t in self.run.floor.exits else None

    def _journal_mission(self):
        """The Journal's tracked mission (looked up once a second), or None."""
        from src.world import guide
        now = pygame.time.get_ticks() // 1000
        if getattr(self, "_journal_at", None) != now:
            self._journal_at, self._journal = now, guide.tracked_mission(self.game)
        return self._journal

    def _journal_rect(self):
        """The Journal's tracked mission, kept on screen under MENU (Jordan, 11-07), or None."""
        if getattr(self, "contest", None) or not self._journal_mission():
            return None
        return pygame.Rect(16, 126, FRAME_LEFT - 32, 106)  # (in the left band, beside the map)

    def _mini_room(self):
        """The left band's space for the mini-map: (top, width, height), under the Journal, above MEGA."""
        jr = self._journal_rect()
        top = jr.bottom + 10 if jr else 128  # (under MENU, and the Journal's mission)
        return top, FRAME_LEFT - 32, self.game.height - 196 - top

    def _mini_scale(self):
        f = self.run.floor
        _top, rw, rh = self._mini_room()
        return mini_scale(f.w, f.h, rw, rh)

    def _minimap_rect(self):
        f = self.run.floor
        s = self._mini_scale()
        top = self._mini_room()[0]
        return pygame.Rect(16, top, f.w * s + 8, f.h * s + 8)

    def _draw_journal(self, screen):
        r = self._journal_rect()
        if r is None:
            return
        m = self._journal_mission()
        fonts = self.game.assets.fonts
        panel = pygame.Surface(r.size, pygame.SRCALPHA)
        panel.fill((10, 14, 24, 190))
        screen.blit(panel, r.topleft)
        main = str(m.get("type", "")).upper() == "MAIN"
        pygame.draw.rect(screen, (250, 210, 60) if main else (120, 200, 255), r, 2, border_radius=8)
        title = theme.pokemon_word(str(m.get("text") or m.get("title") or "Journal"))
        font = fonts["caption"]
        while font.size(title)[0] > r.w - 24 and len(title) > 4:
            title = title[:-2].rstrip() + "."
        theme.shadow_text(screen, title, font, r.x + 12, r.y + 6, color=(250, 220, 110) if main else (170, 220, 255))
        words, lines, line = theme.pokemon_word(str(m.get("desc") or m.get("description") or "")).split(), [], ""
        small = fonts["small"]
        for w in words:  # (two lines of what to do; the Journal has the rest)
            test = (line + " " + w).strip()
            if small.size(test)[0] <= r.w - 24:
                line = test
                continue
            lines.append(line)
            line = w
            if len(lines) == 3:
                break
        if line and len(lines) < 3:
            lines.append(line)
        elif len(lines) == 3 and len(" ".join(lines).split()) < len(words):
            last = lines[2]
            while small.size(last + "...")[0] > r.w - 24 and len(last) > 3:
                last = last[:-1]
            lines[2] = last.rstrip() + "..."
        for k, text in enumerate(lines):
            screen.blit(small.render(text, True, (235, 235, 245)), (r.x + 12, r.y + 34 + k * 22))

    def _draw_hud(self, screen):
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        story = self.game.story_manager
        view = map_view(self.game)
        bar = pygame.Rect(view.x, 12, view.w, 64)  # (over the map's frame)
        theme.draw_textbox(screen, bar)
        name = self.area_data.get("route_name", self.area_key.replace("_", " ").title())
        floor_txt = f"  {self._floor_name(self.run.index)}" if self.run.n_floors > 1 else ""
        if getattr(self, "per_floor", 1) > 1 and self.zones:  # (a wide floor: the area you're in)
            floor_txt = "  " + self._zone_name(self._zone_index(self.run.index, self.run.player[0], self.run.player[1]))
        title = theme.pokemon_word(name) + floor_txt
        room = bar.right - 380 - bar.x - 36  # (up to the ball count)
        font = fonts["button"] if fonts["button"].size(title)[0] <= room else fonts["label"]
        while font.size(title)[0] > room and len(title) > 4:  # a long name: shortened
            title = title[:-2].rstrip() + "."
        theme.shadow_text(screen, title, font, bar.x + 20, bar.centery - font.get_height() // 2)
        sf = getattr(self, "safari", None)
        ball = "SPORT_BALL" if self.contest else "SAFARI_BALL" if sf else catching.selected(story)
        bimg = self._item_img(ball, 30) or self._ball_img(30)
        bx = bar.right - 380
        screen.blit(bimg, (bx, bar.centery - 15))
        count = self.contest["balls"] if self.contest else sf["balls"] if sf else catching.owned(story, ball)
        if sf:  # (the Safari Game: the steps left)
            t = fonts["label"].render(f"STEPS {sf['steps']}", True, (255, 255, 255))
            pill = t.get_rect(midtop=(bar.centerx, bar.bottom + 8)).inflate(24, 10)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=10)
            pygame.draw.rect(screen, theme.POKEMON if sf["steps"] > 50 else theme.FIGHT, pill, 2, border_radius=10)
            screen.blit(t, t.get_rect(center=pill.center))
        theme.shadow_text(screen, f"x{count}", fonts["label"], bx + 36, bar.centery - 12)
        if self.contest:  # the time left, and your best catch so far
            c = self.contest
            info = f"TIME {c['turns']}" + (f"   BEST: {c['best'].display_name.upper()} ({c['score']})" if c["best"] else "")
            t = fonts["label"].render(info, True, (255, 255, 255))
            pill = t.get_rect(midtop=(bar.centerx, bar.bottom + 8)).inflate(24, 10)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=10)
            pygame.draw.rect(screen, theme.POKEMON if c["turns"] > 30 else theme.FIGHT, pill, 2, border_radius=10)
            screen.blit(t, t.get_rect(center=pill.center))
        lead = self.lead()
        if lead:  # (right-aligned: a long name, MEGA VENUSAUR, stays in the bar)
            text = f"{lead.display_name.upper()} Lv{lead.level}"
            font = fonts["caption"]
            room = bar.right - 20 - (bx + 100)
            if font.size(text)[0] > room:
                font = fonts["small"]
            t = font.render(text, True, (255, 255, 255))
            theme.shadow_text(screen, text, font, bar.right - 20 - t.get_width(), bar.y + 10)
            theme.hp_bar(screen, bar.right - 240, bar.y + 36, 220, lead.current_hp, lead.get_max_hp())
        self._draw_journal(screen)
        # the mini-map
        f = self.run.floor
        mm = self._minimap_rect()
        panel = pygame.Surface(mm.size, pygame.SRCALPHA)
        panel.fill((10, 14, 24, 170))
        screen.blit(panel, mm.topleft)
        s = self._mini_scale()
        for (x, y) in f.seen:
            if f.walkable(x, y):
                screen.fill((150, 190, 230), (mm.x + 4 + x * s, mm.y + 4 + y * s, s, s))
        for (x, y), target in f.exits.items():
            if (x, y) in f.seen:
                screen.fill((250, 200, 60), (mm.x + 3 + x * s, mm.y + 3 + y * s, s + 2, s + 2))
        for (x, y) in list(f.items) + list(f.tm_spots):
            if (x, y) in f.seen:
                screen.fill((90, 220, 120), (mm.x + 4 + x * s, mm.y + 4 + y * s, s, s))
        for m in f.movers:
            if self.run.visible(m.x, m.y) or (m.kind == "figure" and (m.x, m.y) in f.seen):
                color = {"wild": (230, 80, 70), "figure": (250, 210, 60)}.get(m.kind, (170, 110, 230))
                screen.fill(color, (mm.x + 4 + m.x * s, mm.y + 4 + m.y * s, s, s))
        hit = self._guide_spot() if self.mode == "MAP" else None
        if hit and (pygame.time.get_ticks() // 300) % 2:
            gx, gy = hit[0]
            pygame.draw.rect(screen, (255, 214, 64), (mm.x + 2 + gx * s, mm.y + 2 + gy * s, s + 4, s + 4))
        px, py = self.run.player
        pygame.draw.circle(screen, (255, 255, 255), (mm.x + 4 + px * s + s // 2, mm.y + 4 + py * s + s // 2), 3)
        # the buttons
        if self.mode == "MAP" and not self.dialogue_box.visible:
            mouse = pygame.mouse.get_pos()
            for rect, label, color, _a, ok, sub in self._buttons():
                font = fonts["caption"] if fonts["caption"].size(label)[0] <= rect.w - 14 else fonts["label"]
                if font.size(label)[0] > rect.w - 14:  # (a long word in the narrow band: PLAY SLOTS)
                    font = fonts["small"]
                theme.command_button(screen, rect, label, font, color if ok else theme.BACK,
                                     hover=rect.collidepoint(mouse), small=fonts["small"], sub=sub or None)
        # a found item, and the area's name on arrival
        if self.toast_timer > 0:
            t = fonts["label"].render(self.toast, True, (255, 255, 255))
            r = t.get_rect(midtop=(map_view(self.game).centerx, 100)).inflate(28, 14)
            pygame.draw.rect(screen, (30, 36, 58), r, border_radius=12)
            pygame.draw.rect(screen, theme.BAG, r, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=r.center))
        if self.banner > 0 and self.mode == "MAP":
            word = theme.pokemon_word(self.area_data.get("route_name", "")) + \
                (f"  {self._floor_name(self.run.index)}" if self.run.n_floors > 1 else "")
            t = fonts["big"].render(word, True, (255, 255, 255))
            r = t.get_rect(center=(map_view(self.game).centerx, int(H * 0.3))).inflate(60, 24)
            panel = pygame.Surface(r.size, pygame.SRCALPHA)
            panel.fill((10, 14, 24, min(200, self.banner * 4)))
            screen.blit(panel, r.topleft)
            t.set_alpha(min(255, self.banner * 5))
            screen.blit(t, t.get_rect(center=r.center))

    def _draw_encounter(self, screen):
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        screen.blit(shade, (0, 0))
        p = self.encounter.payload if self.encounter else None
        if p is None:
            return
        card = pygame.Rect(0, 0, 760, 120)
        card.midtop = (W // 2, 96)
        theme.draw_textbox(screen, card)
        theme.shadow_text(screen, f"A wild {p.display_name.upper()} (Lv{p.level}) appeared!", fonts["button"],
                          card.centerx, card.centery - 18, align="center")
        if self.mode == "CHOICE":
            sub = "Pick MATH to try a quick catch, or BATTLE." if self._can_catch() else "Pick BATTLE."
        elif self.mode == "MATH":
            sub = "Answer right to throw a ball!"
        else:
            sub = ""
        if sub:
            theme.shadow_text(screen, sub, fonts["label"], card.centerx, card.centery + 22, align="center")
        img = p.image
        y_mid = int(H * 0.42)
        if self.mode == "THROW":
            k = 1 - self.throw_timer / (FPS * 1.2)
            if self.throw_result in ("caught", "broke") or k < 0.5:
                ball = self._ball_img(48)
                bx = W // 2 + int((1 - min(1, k * 2)) * 260)
                by = y_mid + int((1 - min(1, k * 2)) * 220) - int(math.sin(min(1, k * 2) * math.pi) * 120)
                if k >= 0.5 and self.throw_result in ("caught", "broke"):  # in the ball, shaking
                    bx += int(math.sin(k * 40) * 8)
                    img = None
                screen.blit(ball, ball.get_rect(center=(bx, by)))
        if img is not None:
            screen.blit(img, img.get_rect(center=(W // 2, y_mid)))
        mouse = pygame.mouse.get_pos()
        if self.mode == "CHOICE":
            can = self._can_catch()
            labels = [("MATH", "1 question: catch it!" if can else "No balls / no Pokedex", theme.RUN if can else theme.BACK),
                      ("BATTLE", "Fight it in a battle", theme.FIGHT)]
            for i, (rect, (label, small, color)) in enumerate(zip(self._choice_rects(), labels)):
                theme.command_button(screen, rect, label, fonts["button"], color,
                                     hover=rect.collidepoint(mouse) or self.choice == i, small=fonts["caption"], sub=small)
        elif self.mode == "MATH":
            q = pygame.Rect(0, 0, max(380, fonts["big"].size(self.problem_str)[0] + 120), 92)
            q.center = (W // 2, int(H * 0.58))
            theme.draw_textbox(screen, q)
            theme.math_text(screen, self.problem_str, fonts["big"], q.centerx, q.centery)
            for i, rect in enumerate(self._answer_rects()):
                theme.card(screen, rect, hover=rect.collidepoint(mouse), accent=theme.RUN)
                theme.answer_text(screen, self.options[i], fonts["num"], rect.centerx, rect.centery)
            k = max(0.0, self.math_timer / self.math_full)
            track = pygame.Rect(W // 2 - 300, int(H * 0.66) + 126, 600, 14)
            pygame.draw.rect(screen, (60, 64, 80), track, border_radius=7)
            pygame.draw.rect(screen, theme.POKEMON if k > 0.33 else theme.FIGHT,
                             (track.x, track.y, max(8, int(track.w * k)), track.h), border_radius=7)
