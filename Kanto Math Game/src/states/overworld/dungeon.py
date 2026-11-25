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
import weakref

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


def _flat_people(people):
    """A map's people, a spot's list of several (one at a time, by their conditions) laid out one by one."""
    out = []
    for p in people or []:
        out.extend(p if isinstance(p, list) else [p])
    return out


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
                  "SNAG", "MAX_RAID", "DIVE", "GAME_CORNER", "BUG_CONTEST",
                  "FRONTIER")   # (FRONTIER: a Battle Frontier attendant, src/world/frontier.py)
DECOR_C = {"slot": ((200, 60, 70), (250, 230, 120)), "counter": ((150, 100, 60), (204, 156, 100)),
           "poster": ((60, 60, 80), (236, 226, 200))}
FACING_ROW = {(0, 1): 0, (-1, 0): 1, (1, 0): 2, (0, -1): 3}  # a sheet's rows: down, left, right, up
# Forms whose sheet isn't named <species>_<FORM_MAP form>: the two-Mega Pokemon (their form is just "mega")
FORM_SHEETS = {3002: "6_mega_x", 3003: "6_mega_y", 3007: "26_mega_x", 3008: "26_mega_y", 3020: "150_mega_x",
               3021: "150_mega_y"}


def follower_names(game, pokemon):
    """The assets/dungeon/followers sheet names (no .png) to try for a Pokemon, best first (Jordan, 11-17: every
    form its own sheet). A form: <species>_<form> (12_pinkan, 479_heat, 201_b, 6_mega_x), then its own id's
    (2008: Alolan Diglett), then the species'. Works from a bare id too (a map's boss or "mon:9103"): an id of
    2000 and up is looked up in FORM_MAP, a species with a form gets its id from there."""
    raw = int(pokemon.id)
    form = str(getattr(pokemon, "form", "normal") or "normal").lower()
    species, own = raw, None
    try:
        fm = game.loader.area_data.get("FORM_MAP", {}) or {}
    except AttributeError:
        fm = {}
    if raw >= 2000:
        own = raw
        entry = fm.get(str(raw)) or {}
        meta = getattr(pokemon, "meta_id", None)
        species = int(meta) if meta and int(meta) != raw else int(entry.get("id", raw))
        if form == "normal" and entry.get("form"):
            form = str(entry["form"]).lower()
    elif form != "normal":
        own = next((int(k) for k, m in fm.items() if int(m.get("id", 0)) == raw
                    and str(m.get("form", "")).lower() == form), None)
    names = [FORM_SHEETS[own]] if own in FORM_SHEETS else []
    variant = str(((getattr(pokemon, "_form_state", None) or {}).get("form")) or "").lower()
    if form in ("mega", "gmax") and variant in ("pinkan", "valencia"):   # (a Mega Pinkan: 15_pinkan_mega, Jordan 11-23)
        names.append(f"{species}_{variant}_{form}")
    if form != "normal":
        names.append(f"{species}_{form}")
    if own:
        names.append(str(own))
    names.append(str(species))
    if getattr(pokemon, "gender", None) == "F" and form == "normal":  # (Pikachu's heart tail: its own sheet)
        names.insert(0, f"{species}_female")
    return list(dict.fromkeys(names))

def region_sheet_paths(game, names, shiny=False):
    """Where to look for a following Pokemon's walking sheet, best first (Jordan 11-23: a game-built region's own
    overworld sheets first, assets/dungeon/followers as the fallback). For each of its names (follower_names: its exact
    form first): the shiny follower sheet (a region's own sheets have no shiny colours), this region's own sheet
    (dungeon_sprites.json "region_followers"), the follower sheet, then any other region's own sheet for that name - so a
    form only one region drew (a Shadow form, an island variant) keeps that look wherever it follows you - and only then
    the next, plainer name."""
    assets = getattr(game.assets, "assets_dir", None) or "assets"
    base, chars = os.path.join(assets, "dungeon", "followers"), os.path.join(assets, "dungeon", "characters")
    own = {r: d for r, d in (sprite_map(game).get("region_followers") or {}).items() if isinstance(d, dict)}
    try:
        here = str(game.story_manager.get_current_region() or "").upper()
    except AttributeError:
        here = ""
    out = []
    for n in names:
        if shiny:
            out.append(os.path.join(base, "shiny", f"{n}.png"))
        if (own.get(here) or {}).get(n):
            out.append(os.path.join(chars, own[here][n]))
        out.append(os.path.join(base, f"{n}.png"))
        out += [os.path.join(chars, d[n]) for r, d in sorted(own.items()) if r != here and d.get(n)]
    return list(dict.fromkeys(out))


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
    show(["Contest helper: Welcome to the Bug-Catching Contest check-in desk!",
          "Contest helper: The rules are simple. Catch the best Bug-type Pokemon you can in the park before time runs out.",
          f"Contest helper: Here are {CONTEST_BALLS} Sport Balls. Use only these. When time's up, the judges score your best catch.",
          "Contest helper: You can keep the one you choose. The other contestants are already out there. Good luck!"],
         callback=lambda: game.change_state(AreaTransitionState(game, "BUG_CONTEST")))


def running():
    """Shift held down (Jordan, 11-14: hold Shift while moving to run; no shoes needed): each step takes half the time."""
    try:
        return bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
    except pygame.error:
        return False


def held_way(keys_map):
    """The way a held arrow key (or WASD) points, or None (Jordan, 11-07: hold to keep walking)."""
    from src.vfx import area_changes as _ac
    if _ac.ACTIVE is not None and _ac.ACTIVE.t > 0:   # (a door's wipe playing on screen: no one walks on)
        return None
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


def shake_dx(state):
    """The screen's sideways jolt while a map shakes (state._shake_until: a tremor, 5.7's special 0x136), else 0."""
    until = getattr(state, "_shake_until", 0)
    if not until:
        return 0
    now = pygame.time.get_ticks()
    if now >= until:
        state._shake_until = 0
        return 0
    return 4 if (now // 45) % 2 else -4


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
        try:   # (an overlay's own looks: Hoenn's ORAS items and the people who give them, assets/hoenn_oras.json "FIGURES")
            with open(os.path.join(game.assets.assets_dir or "", "hoenn_oras.json"), encoding="utf-8") as f:
                _sprite_map["all"].setdefault("figures", {}).update(json.load(f).get("FIGURES") or {})
        except (OSError, ValueError):
            pass
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


def _upstairs(rooms, floors, names, where):
    """Rooms reached from other rooms ("exits" {"v": "ROOM:gate_2"}: a gatehouse's stairs up) become floors too, after
    the rest; each such stairs tile leads onto the tile beside the other room's stairs back."""
    refs = lambda r: [str(t)[5:] for t in (r.get("exits") or {}).values() if str(t).startswith("ROOM:")]
    grew = True
    while grew:
        grew = False
        for name, room in rooms.items():
            if name in where or not any(name in refs(rooms[o]) for o in where):
                continue
            where[name] = len(floors)
            own = {k: v for k, v in room.items() if k not in ("art", "exits", "links", "land", "enter")}
            floors.append(dict(own, art=list(room["art"]), exits={}, links={}, boss_spot=None, parts=True, indoors=True,
                               pool="NO_WILD_INDOORS_PERCENTAGES", buildings=room.get("buildings") or {}))
            names.append(str(room.get("title") or name).title())
            grew = True

    def stairs(name, to):
        art = rooms[name]["art"]
        chs = [ch for ch, t in (rooms[name].get("exits") or {}).items() if str(t) == f"ROOM:{to}"]
        return [(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c in chs]

    for name, j in where.items():
        f = floors[j]
        art = [list(r) for r in f["art"]]
        links, keep = dict(f.get("links") or {}), dict(f.get("exits") or {})
        for ch, target in (rooms[name].get("exits") or {}).items():
            to = str(target)[5:] if str(target).startswith("ROOM:") else None
            if to not in where:
                continue
            keep.pop(ch, None)
            back = stairs(to, name)
            if not back:
                continue
            bx, by = back[0]
            tart = rooms[to]["art"]
            near = next(((x, y) for x, y in ((bx, by - 1), (bx - 1, by), (bx + 1, by), (bx, by + 1))
                         if 0 <= y < len(tart) and 0 <= x < len(tart[y]) and tart[y][x] in ".N"), (bx, by))
            for ry, row in enumerate(art):
                for rx, c in enumerate(row):
                    if c == ch:
                        row[rx] = "1"
                        links[f"{rx},{ry}"] = [where[to], near[0], near[1]]
        floors[j] = dict(f, art=["".join(r) for r in art], links=links, exits=keep)


def with_rooms(m):
    """A route map with buildings you walk into (Jordan, 11-12: "buildings on routes"), in the towns' own words: "rooms"
    {name: a map of its own (theme "room", its mats' "exits" {"v": "OUT:x,y"}, "people": route options by their text)}
    and "inside" {"x,y" of a door: room name} on the map (or on a floor of it). Each room becomes a floor of the area
    after its own, joined to its door: in at the door you stand on the room's mat, out by the mat you stand below the
    door. No wild Pokemon indoors, unless the room has its own "wild_tables" (src/world/wild_tables.py's shape: Relic Castle's
    Baltoy rooms, Black 2). The map itself is not changed."""
    rooms = m.get("rooms") or {}
    if not rooms:
        return m
    floors = [dict(f) for f in m["floors"]] if m.get("floors") else [
        {k: m[k] for k in ("art", "exits", "signs", "people", "trainer_spots", "links", "overheads", "parts", "boss_spot", "inside", "stops",
                           "barred", "moves", "scenes", "berry_soil", "sign_scenes", "edge_to", "dive", "dive_links", "surface", "pool", "hidden", "cycling", "downhill", "heights") if k in m}]   # (the map's own floor keeps everything of its own: who's in the way, how people move)
    n0 = len(floors)
    names = list(m.get("floor_names") or [""] * n0)
    where, doors = {}, {}
    for i, f in enumerate(floors):
        for d, name in (f.get("inside") or (m.get("inside") if n0 == 1 else None) or {}).items():
            if name in rooms:
                doors.setdefault(name, []).append((i, d))
    include = [n for n in rooms if n in doors]   # (and the rooms those lead on to by their own pads: the Battle Maison's
    k = 0                                         #  corridor and battle room, behind its lobby)
    while k < len(include):
        for v in (rooms[include[k]].get("links") or {}).values():
            if isinstance(v, list) and v and isinstance(v[0], str) and v[0] in rooms and v[0] not in include:
                include.append(v[0])
        k += 1
    for idx, name in enumerate(include):
        where[name] = n0 + idx
    for name in include:
        room = rooms[name]
        j = where[name]
        art = [list(r) for r in room["art"]]
        links = {k: [where[v[0]], v[1], v[2]] for k, v in (room.get("links") or {}).items()
                 if isinstance(v, list) and v and isinstance(v[0], str) and v[0] in where}   # (a pad to another room: its floor)
        for k in links:   # (its tile a passage, as the mats below: the walk only takes a link from a "1" - the docked Plasma
            lx, ly = (int(v) for v in k.split(","))   #  Frigate's stern pad to Kyurem's room did nothing; Journal, 11-25)
            if 0 <= ly < len(art) and 0 <= lx < len(art[ly]) and art[ly][lx] == ".":
                art[ly][lx] = "1"
        mats = {}
        land, enter, keep = room.get("land") or {}, room.get("enter") or {}, {}
        # (Kanto's gatehouses: a mat that is a real way out to the next area stays one; "land" {door: where you stand
        # outside it}, "enter" {door: where you stand inside}: a door in a building's side or back, or two tiles wide)
        for ch, target in (room.get("exits") or {}).items():
            if not str(target).startswith("OUT:"):
                keep[ch] = target
                continue
            x, y = (int(v) for v in str(target)[4:].split(","))
            back = next((i for i, d in doors.get(name, []) if d == f"{x},{y}"), (doors.get(name) or [(0, None)])[0][0])
            for ry, row in enumerate(art):
                for rx, c in enumerate(row):
                    if c == ch:
                        row[rx] = "1"
                        links[f"{rx},{ry}"] = [back, land[f"{x},{y}"][0], land[f"{x},{y}"][1] + 1] if f"{x},{y}" in land else [back, x, y + 1]
                        mats.setdefault(f"{x},{y}", (rx, ry))
        own = {k: v for k, v in room.items() if k not in ("art", "exits", "links", "land", "enter")}
        floors.append(dict(own, art=["".join(r) for r in art], exits=keep, links=links, boss_spot=None, parts=True, indoors=True,
                           pool=None if room.get("wild_tables") else "NO_WILD_INDOORS_PERCENTAGES", buildings=room.get("buildings") or {}))
        names.append(str(room.get("title") or name).title())
        for i, d in doors.get(name, []):  # (the door outside: onto the room's mat for it)
            mat = (enter[d][0], enter[d][1] + 1) if d in enter else mats.get(d) or next(iter(mats.values()), None)
            if mat:
                floors[i] = dict(floors[i], links=dict(floors[i].get("links") or {}, **{d: [j, mat[0], mat[1]]}))
    _upstairs(rooms, floors, names, where)
    on = dict(m.get("figure_floors") or {})
    for i, f in enumerate(floors):  # (everyone stays on the floor their spot is on: a figure with no floor named would be put on the last, a room)
        for t in list(f.get("people") or []) + list(f.get("trainer_spots") or []):
            if isinstance(t, str):
                on.setdefault(t, i)
    out = {k: v for k, v in m.items() if k not in ("art", "exits", "signs", "people", "trainer_spots", "links", "overheads", "parts", "inside", "stops", "rooms")}  # (boss_spot stays: the map's own)
    out.update(floors=floors, floor_names=names, figure_floors=on, room_floors=where, outdoor_floors=n0)
    return out


def way_on_water(recipe, floor, target):
    """Is a floor's way out to target on the water (True), on land (False), or not known (None)? A room's (indoors) door is land."""
    floors = ((recipe.get("art") or {}).get("floors")) or []
    if not 0 <= floor < len(floors):
        return None
    f = floors[floor]
    if f.get("indoors"):
        return False
    from src.dungeon import art as _art
    grid, letters = f.get("art") or [], {c for c, t in (f.get("exits") or {}).items() if t == target}
    wet = [c in "wu" or _art.at_sea(grid, x, y) for y, row in enumerate(grid) for x, c in enumerate(row) if c in letters]
    return None if not wet else all(wet) if all(wet) or not any(wet) else None


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
            for k in ("dive", "dive_at", "dive_links", "surface", "pool", "exit_order", "indoors", "wild_tables"):  # (Dive: the seabed floor under this one, the surface over it, its own wild Pokemon)
                if m["floors"][i].get(k) is not None:
                    out["layout"][i][k] = m["floors"][i][k]
        out["floors"] = len(parts)
        out["exit_floors"] = {}
        for i, f in enumerate(m["floors"]):  # (a target on two floors: you come back on the lower-numbered one)
            for t in f.get("exits", {}).values():
                out["exit_floors"].setdefault(t, i)
        out["people_floors"] = {}   # (everyone on the floor their spot is on: a figure no "figure_floors" names went to the last floor)
        for i, f in enumerate(m["floors"]):
            for t in f.get("people") or []:   # (people only: trainers keep their own placing, one name on several floors)
                if isinstance(t, str):
                    out["people_floors"].setdefault(t, i)
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
            if f"{x},{y}" in (m.get("decor") or {}):  # (a thing drawn in the map's picture that does something: a slot machine, the poster's switch)
                ch = chr(0x2D80 + len(legend))
                legend[ch] = {"decor": m["decor"][f"{x},{y}"]}
                out.append(ch)
            elif [x, y] == list(m.get("boss_spot") or ()):  # the area's boss asleep on this very tile (the map's "boss_spot": Snorlax on Route 12)
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
                if isinstance(who, list):   # (one spot, several people in turn, by their conditions: Route 20's Hiker Jerome, 11-20)
                    legend[ch] = {"figure": [w.get("text") if isinstance(w, dict) else w for w in who]}
                else:
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
            elif c == ":" and m.get("surface") is not None:  # on a seabed: its sunlit floor, where you can come up (dive_links)
                legend["\u2c11"] = {"deep": True}
                out.append("\u2c11")
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
            elif c in _art.RAMPS:  # a bike ramp: in the way, but on the Bicycle you jump off it its one way (ramp:<dx>,<dy>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": "ramp:%d,%d" % _art.RAMPS[c]}
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
            "style": m.get("style") or "field", "floors": 1}  # (open, unless the map keeps its fog: the Pokemon Tower's; a map's own "style": the Trackless Forest's)


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


_SPECIES = {}


def species_named(game, text):
    """The species a figure's name is ("Poliwrath", "WIGGLYTUFF", "Nidoran"), else None: a Pokemon standing about."""
    if not _SPECIES:
        names = getattr(game.assets, "pokemon_names", None) or {}
        for k, v in names.items():
            try:
                _SPECIES.setdefault(str(v).lower(), int(k))
            except ValueError:
                pass
        _SPECIES.setdefault("nidoran", 29)   # (FireRed's own: the female one)
        _SPECIES.setdefault("mr. mime", 122)
        _SPECIES.setdefault("farfetch'd", 83)
    t = str(text or "").strip().lower()
    return _SPECIES.get(t) if t else None


def recipe_for(game, area_key):
    """DEFAULT, then the area's own recipe; an area without one gets its look from its battle type
    (a cave, a building, the sea...), ponds where you can fish, a smaller map for a small place.
    A route with a real map (Jordan, 11-06: Route 1 first) is walked on it: its picture, its grass, its
    ways out, wide open."""
    all_ = recipes(game)
    recipe = dict(all_.get("DEFAULT", {}))
    from src.states.overworld.walk_town import custom, story_map
    mine = story_map(game, area_key) if (custom(game).get(area_key) or {}).get("story_maps") else custom(game).get(area_key)   # (a route's
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})   # other map while its conditions stand: Route 20 in autumn, 11-20)
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
            if isinstance(mine.get("dark"), dict):   # (a map's "dark" {"radius": [r]}: black but a small light round you, as
                recipe["dark_radius"] = int((mine["dark"].get("radius") or [2])[0])   #  the towns' dark rooms; Mistralton Cave, Unova 11-24)
                recipe["fog"] = False
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
    if key == "HOENN_SOARING_IN_THE_SKY":  # (Soaring in the Sky, 3D: the flight over ORAS's Hoenn, not a map)
        from src.states.overworld.soaring3d import Soaring3DState
        cur = getattr(game, "soaring3d_state", None)
        if restore_data and cur is not None and getattr(cur, "area_key", None) == key:
            return cur
        return object.__new__(Soaring3DState)
    cur = getattr(game, "dungeon_state", None)
    if restore_data and cur is not None and getattr(cur, "area_key", None) == key:
        return cur
    if (game.loader.area_data.get("STORY_PROGRESSION", {}).get(key) or {}).get("mystery_dungeon"):
        from src.states.overworld.mystery_dungeon import MysteryDungeonState  # (the Giant Volcano, as a Charmander)
        return object.__new__(MysteryDungeonState)
    if (game.loader.area_data.get("STORY_PROGRESSION", {}).get(key) or {}).get("hyperspace"):
        from src.states.overworld.hyperspace import HyperspaceState  # (Hyperspace Lumiose's zones)
        return object.__new__(HyperspaceState)
    return object.__new__(DungeonState)


# ---------------------------------------------------------------- the screen
def terminal_figure():
    """A computer terminal on a stand, its screen glowing (ours: New Mauville's security computer)."""
    w, h = TILE, TILE + 10
    img = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(6, 10, w - 12, h - 18)
    pygame.draw.rect(img, (96, 104, 120), body, border_radius=4)
    pygame.draw.rect(img, (52, 58, 70), body, 2, border_radius=4)
    screen = pygame.Rect(body.x + 5, body.y + 5, body.w - 10, body.h // 2)
    pygame.draw.rect(img, (70, 210, 230), screen, border_radius=2)
    for k in range(3):
        pygame.draw.line(img, (190, 250, 255), (screen.x + 3, screen.y + 4 + k * 5), (screen.right - 6 - k * 4, screen.y + 4 + k * 5), 2)
    for k in range(4):
        pygame.draw.rect(img, (220, 200, 90) if k == 1 else (170, 176, 190), (body.x + 6 + k * 8, body.bottom - 10, 5, 4))
    pygame.draw.rect(img, (70, 76, 90), (w // 2 - 4, h - 9, 8, 6))
    return img


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


# (sheets drawn at their own size beside a person, not stretched to one: Black 2's item ball, Jordan 11-20)
CELL_SIZED = {"b2_item_ball.png"}
# People from every sprite set stand one height (Jordan 11-23, Johto's 3D review: "the size difference between player and npc
# is big"): each set draws an adult a different number of pixels tall (SoulSilver/Platinum 24, Black 2 28, the GBA sets 20,
# the Pokemon Journeys and Orre sheets 40), and a whole-number scale per sheet left a Journeys player 1.6x SoulSilver's
# people. A person-shaped frame from a known set is scaled so its set's adult comes out PERSON_H pixels tall (children stay
# shorter, a big man taller); anything else - Pokemon, items, a set not listed - keeps the whole-number scale.
PERSON_H = 72   # (Jordan's pick: about 1.3 tiles; SoulSilver's and Platinum's people at exactly 3x)
SET_ADULT = (("hg_", 24), ("pt_", 24), ("b2_", 28), ("fr_", 20), ("em_", 20), ("oi_", 20), ("trchar", 40), ("NPC ", 40), ("orre_", 40))


# Live 3D (11-23, Johto: people stood 1.5x too tall in 3D once they were 72 px on the map): the 3D view sizes a figure by its
# picture, so a person's picture is remembered here as it's made, and stands LIVE_PERSON tiles tall for a PERSON_H adult in
# the world, whatever its set (Black 2's people stood exactly that tall before; the DS shows people about 1.5 tiles).
PERSON_FRAMES = weakref.WeakSet()
LIVE_PERSON = 1.5


def live_height(img, live_sprite):
    """A figure's height in the 3D world, in tiles: a person by PERSON_H (one adult height for every set), else by its
    picture's height (live_sprite tiles per tile of picture), as before."""
    if img in PERSON_FRAMES:
        return img.get_height() / PERSON_H * LIVE_PERSON
    return img.get_height() / TILE * live_sprite


def same_kind(new, old):
    """new (a pose's scaled copy of old, say) counts as a person when old does. Returns new."""
    if old is not None and new is not None and old in PERSON_FRAMES:
        PERSON_FRAMES.add(new)
    return new


def person_scale(sheet, cw, ch):
    """The scale for a person-shaped frame (taller than wide) of a known sprite set, else None."""
    if ch < cw * 1.4:
        return None
    ref = next((r for p, r in SET_ADULT if str(sheet).startswith(p)), None)
    return PERSON_H / ref if ref else None


from src.states.overworld.dungeon_live import RouteLive   # (the live 3D camera on the route maps, 11-21)
from src.states.overworld.wild_walkup import WildWalkUps   # (Honey's and the swarms' Pokemon walking up to you: region/systems 11-23)


class DungeonState(WildWalkUps, RouteLive, OverworldBattles, PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_dungeon_ready", False):  # the walk going on, back from a battle
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._dungeon_ready = True
        story = game.story_manager
        self.area_key = story.current_area_key
        _ferry = (game.loader.area_data.get("STORY_PROGRESSION", {}).get(self.area_key) or {}).get("ferry") or {}
        if getattr(story, "last_area_key", None) in _ferry:   # (a ferry: the port you boarded at, so its sailor still knows where you're bound after a reload; a loaded save: none)
            story.story_flags[f"ferry_from_{self.area_key}"] = story.last_area_key
        self.recipe = recipe_for(game, self.area_key)
        if getattr(story, "last_area_key", None) != self.area_key:   # (a floor's "boxes_fresh": its pushed boulders back where they
            for _i, _f in enumerate((self.recipe.get("art") or {}).get("floors") or []):   # started each time you come into the place,
                if _f.get("boxes_fresh"):                                               # as Platinum's Strength boulders; Sinnoh 11-24)
                    story.story_flags.pop(f"boxes_{self.area_key}_{_i}", None)
        _hms = __import__("src.world.hms", fromlist=["usable"])
        if self.recipe.get("dark") and (_hms.usable(story, "HM_FLASH") or _hms.by_move(story, "HM_FLASH")):  # (Flash lights a dark cave:
            self.recipe = dict(self.recipe, fog=False, dark_radius=None)                                     #  the HM, or the TM's move in Gen 5+)
        if (self.recipe.get("art") or {}).get("fog") == "defog":  # (thick fog: you see only what is near, till Defog clears it: the Lost Tower)
            self.recipe = dict(self.recipe, fog=story.inventory.get("HM_DEFOG", 0) <= 0)
        if (self.recipe.get("art") or {}).get("fog_floors") is not None:   # (fog on some floors only: the map's "fog_floors")
            self.recipe = dict(self.recipe, fog_floors=list(self.recipe["art"]["fog_floors"]))
        if (self.recipe.get("art") or {}).get("fog_box"):   # (fog on part of a map only: "fog_box" [[x0, y0, x1, y1], ...])
            self.recipe = dict(self.recipe, fog_box=[list(b) for b in self.recipe["art"]["fog_box"]])
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
        _art = self.recipe.get("art") or {}
        _drawn = [t for f in ([_art] + list(_art.get("floors") or [])) for t in (f.get("exits") or {}).values()
                  if isinstance(t, str) and not t.startswith(("OUT:", "ROOM:", "FLOOR:", "WARP:"))]
        if came and came not in exits and came in _drawn:   # (a walked map with no menu buttons left: in by its own way from
            exits.append(came)                               #  where you came, a door inside the map too - Unova 11-24)
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
            if (recipe.get("art") or {}).get("start_floor_flag"):   # (a map of alternative floors, each holding all the zones: the Johto Safari's layouts)
                recipe["floors"] = len((recipe.get("art") or {}).get("floors") or []) or recipe["floors"]
            if self.per_floor > 1:  # a wide floor: the areas side by side
                w, h = recipe.get("size", (40, 26))
                recipe["size"] = [w * self.per_floor, h]
        self.recipe = recipe
        n = max(1, int(recipe.get("floors", 1)))
        exits_by_floor, start = None, 0
        if recipe.get("exit_floors") and entrance in recipe["exit_floors"]:  # (our map of floors: in by its floor)
            start = recipe["exit_floors"][entrance]
            _all = (recipe.get("exit_floors_all") or {}).get(entrance) or []
            _wet = core.ENTRANCE_WATER
            core.ENTRANCE_WATER = None
            _match = [i for i in _all if way_on_water(recipe, i, entrance) is _wet] if len(_all) > 1 and _wet is not None else []
            if len(_match) == 1:   # (by sea or by land, as you left: the floor whose way back is the same kind; Sinnoh 11-24)
                start = _match[0]
                core.ENTRANCE_INDEX = core.ENTRANCE_COUNT = 0
            elif len(_all) > 1 and core.ENTRANCE_COUNT >= len(_all):  # (in by the matching way: the far side has as many ways here as we have floors with one, or doors several tiles wide: Viridian Forest's gates)
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
            story.story_flags[f"zone_{self.area_key}"] = self.zones[min(len(self.zones) - 1, start * self.per_floor)]

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
        _drop = getattr(game, "arrive_floor", None)   # (an elevator ride: (area, floor, [x, y]) - Goldenrod Dept. Store's lift down to B1F)
        if _drop and _drop[0] == self.area_key:
            start = int(_drop[1])
        _sf = (recipe.get("art") or {}).get("start_floor_flag")   # (a map of alternatives, the floor a story flag picks: the Johto Safari
        if _sf:                                                     #  Zone's ten layouts, chosen at its Area Setup desk; 11-16)
            start = max(0, min(n - 1, int(story.story_flags.get(_sf) or 0)))
            if self.zones:
                _fz = ((recipe.get("art") or {}).get("floors") or [{}])[start].get("zone_at") or []
                if _fz:
                    story.story_flags[f"zone_{self.area_key}"] = _fz[-1][4]
        self.run = core.Run(recipe, random.Random(), entrance=entrance, forwards=forwards,
                            make_wild=self._make_wild, trainers=trainers,
                            loot_for=self._floor_loot(loot), tm_spots=spots, figures=figures,
                            floor_of=lambda t: self._floor_of(t, None), exits_by_floor=exits_by_floor,
                            start_floor=start)

        at_edge = getattr(game, "arrive_edge", None)  # (out by an edge tile there: in beside its own partner here)
        game.arrive_edge = None
        _mirage = ((game.loader.area_data.get("STORY_PROGRESSION", {}).get(at_edge[1]) or {}).get("mirage") or {}).get("area") if at_edge else None
        if at_edge and at_edge[0] == entrance and (at_edge[1] == self.area_key or _mirage == self.area_key):   # (Mirage Island: Route 130's own shape)
            p2, f = tuple(at_edge[2]), self.run.floor
            own = [e for e, v in f.exits.items() if v == entrance]
            t = min(own, key=lambda e: abs(e[0] - p2[0]) + abs(e[1] - p2[1])) if own else None  # (its partner, or the nearest to it)
            if t is not None:
                step = (1, 0) if t[0] == 0 else (-1, 0) if t[0] == f.w - 1 else (0, 1) if t[1] == 0 else (0, -1)
                inn = (t[0] + step[0], t[1] + step[1])
                if f.walkable(*inn) and inn not in f.exits:
                    self.run.player = inn
                else:   # (a door inside the map, rock straight in from it: beside it, any open side - Unova 11-24)
                    near = next(((t[0] + dx, t[1] + dy) for dx, dy in core.DIRS if f.walkable(t[0] + dx, t[1] + dy)
                                 and (t[0] + dx, t[1] + dy) not in f.exits), None)
                    if near:
                        self.run.player = near
        _arr = ((self.recipe.get("art") or {}).get("arrive") or {}).get(came) if not at_edge else None
        if _arr and self.run.index == 0 and self.run.floor.walkable(*_arr):   # (a map's "arrive" {area: [x, y]}: off a ferry with
            self.run.player = tuple(_arr)                                       #  no tile of its own, onto the dock: the Battle Frontier)
        if _drop and _drop[0] == self.area_key:
            game.arrive_floor = None
            if self.run.floor.walkable(*_drop[2]):
                self.run.player = tuple(_drop[2])
        if came not in exits and not at_edge and not _arr and self._on_surf() and not self._can_surf():
            # (no known way in - a load, a skip, the fallback arrival - put you on a water way in without Surf: ashore, or you'd
            #  swim without it: Valley Windworks from Route 205's river, 11-23. Walking or surfing in keeps its own tile.)
            self.run.player = self._nearest_land() or self.run.player
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
        self._reset_trail()                  # (companions walking behind your Pokemon: Lance and Dragonite in the Rocket Hideout)
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
        self.sign, self._sign_due = None, True   # (a region with its game's profile: that game's sign instead, src/vfx/area_changes.py)
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
        floors = dict(self.recipe.get("people_floors") or {})   # (the floor whose people list names it, unless a figure_floors says)
        floors.update(self.recipe.get("figure_floors") or {})
        floors.update((self.recipe.get("art") or {}).get("figure_floors") or {})
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
        _art = (getattr(self, "recipe", None) or {}).get("art") or {}
        _fl = _art["floors"][index] if _art.get("floors") and index < len(_art["floors"]) else {}
        if self.zones and _fl.get("zone_at") and x is not None:   # (each floor its own areas: [x, y, w, h, zone key] - the Safari's layouts)
            yy = y if y is not None else (self.run.player[1] if hasattr(self, "run") else 0)
            for rx, ry, rw, rh, key in _fl["zone_at"]:
                if rx <= x < rx + rw and ry <= yy < ry + rh and key in self.zones:
                    return self.zones.index(key)
        rects = _art.get("zone_rects")
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
            if (item.get("action") not in FIGURE_ACTIONS and not (item.get("action") == "SHOP" and item.get("door") and item.get("text") in indoors)) \
                    or (item.get("door") and item.get("text") not in indoors):   # (a SHOP stands only behind its built room's counter: Hamlin's Mart, Orange 11-18)
                continue  # (a house's option is through its door, not someone standing about; unless its room is built: then they stand in it)
            if boss_in_way and item.get("action") == "BOSS":
                continue  # (it sleeps across the way out: see _gate)
            if item.get("not_on_map"):
                continue  # (the map stands it there itself, as a stand-in: the Cave of Origin's legend on its rock)
            fc = item.get("flag_condition")
            stays = item.get("stays") and any(item is p for p in getattr(self, "placed", ()))  # (done, but still here till you leave)
            if fc and not stays:
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
            from src.states.battle import legend_back
            rematch = item.get("action") == "BOSS" and legend_back(flags, self._boss_flag_for(item))
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
                    for p in _flat_people(_f.get("people")) if isinstance(p, dict) and p.get("text") and self.npc_shown(p)]
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

    # ---------------------------------------------------------------- companions (Jordan 11-16: "have lance and dragonite follow the player")
    # Someone walking with you, a step behind your Pokemon: Lance and his Dragonite through the Rocket Hideout, from his talk in the
    # souvenir shop till he gives you Whirlpool. Their standing figures on the floors are lifted while they walk with you; talking to
    # the walking Lance plays the line his figure on this floor has (B1F: he patches up your team; B2F: Whirlpool).
    COMPANIONS = {"ROCKET_HQ": {"names": ("Lance", "Dragonite"), "while": ["defeated_red_gyarados"], "until": "got_hm_whirlpool_lance"}}

    def _companions(self):
        from src.world import walk_partners   # (Platinum's walking partners: Cheryl, Mira, Riley, Buck, Marley)
        wp = walk_partners.active(self.game.story_manager, getattr(self, "area_key", None))
        if wp:
            return (walk_partners.figure(wp),)
        from src.world import rui as _rui   # (Orre: Rui walks with you from Phenac on, Q4)
        if _rui.active(self.game.story_manager):
            return (_rui.NAME,)
        c = self.COMPANIONS.get(getattr(self, "area_key", None))
        flags = self.game.story_manager.story_flags
        if not c or not all(flags.get(f) for f in c["while"]) or flags.get(c["until"]):
            return ()
        return c["names"]

    def _reset_trail(self):
        here = self.run.player if hasattr(self, "run") else (0, 0)
        self._ctrail = [here] * 4
        self._ctrail_from = list(self._ctrail)
        self._hide_followed()
        if hasattr(self, "run"):   # (a new floor: Buck waits at the door of Heatran's chamber)
            from src.world import walk_partners
            said = walk_partners.on_floor(self.game.story_manager, self.area_key, self.run.index)
            if said:
                self.say(said)
                self._sync_figures()

    def _hide_followed(self):
        """While they walk with you, their figures standing on the floors step off."""
        names = self._companions()
        if not names or not hasattr(self, "run"):
            return
        for f in getattr(self.run, "floors", None) or [self.run.floor]:
            f.movers = [m for m in f.movers if not (m.kind == "figure" and isinstance(m.payload, dict)
                                                    and str(m.payload.get("text", "")).strip() in names)]

    def _companion_at(self, tile):
        names = self._companions()
        for i, who in enumerate(names):
            if i + 1 < len(self._ctrail) and self._ctrail[i + 1] == tile and tile != self.run.player and tile != self.partner:
                return who
        return None

    def _talk_companion(self, who):
        """Talking to someone walking with you: this floor's line of theirs (their figure's), else a word in passing."""
        from src.world import walk_partners, rui as _rui
        if who == _rui.NAME and _rui.active(self.game.story_manager):
            self.say(_rui.chat(self.game.story_manager))
            return
        wp = walk_partners.active(self.game.story_manager, self.area_key)
        if wp and walk_partners.figure(wp) == who:
            self.say(list(walk_partners.PARTNERS[wp].get("chat") or ["..."]))
            return
        art = (getattr(self, "recipe", None) or {}).get("art") or {}
        fl = art["floors"][self.run.index] if art.get("floors") and self.run.index < len(art["floors"]) else art
        item = next((p for p in _flat_people(fl.get("people")) if isinstance(p, dict) and str(p.get("text", "")).strip() == who
                     and self.npc_shown(p)), None)
        if item is not None:
            class _M:   # (as a standing figure would be)
                pass
            m = _M(); m.payload, m.motion, m.kind = item, None, "figure"
            self._use_figure(m)
            return
        self.say(["DRAGONITE: Gyaoo!"] if who == "Dragonite" else ["Lance: Stay sharp. Team Rocket could be around any corner."])

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
        self._hide_followed()

    def _sync_partners(self):
        """The important people here (src/world/partners.py) with their partner Pokemon beside them, following them; a
        partner whose trainer has left (beaten, gone) leaves too. Checked when the floor's people change."""
        f = self.run.floor
        key = (id(f), len(f.movers))
        if getattr(self, "_partners_key", None) == key:
            return
        from src.world import partners
        from src.dungeon import npc
        owners = {id(m) for m in f.movers}
        f.movers[:] = [m for m in f.movers if getattr(m, "_partner_of", None) is None or id(m._partner_of) in owners]
        have = {id(m._partner_of) for m in f.movers if getattr(m, "_partner_of", None) is not None}
        for m in list(f.movers):
            if m.kind not in ("figure", "trainer") or id(m) in have or getattr(m, "_partner_of", None) is not None:
                continue
            info = m.payload if m.kind == "figure" else (m.payload[1] if isinstance(m.payload, tuple) else None)
            if not isinstance(info, dict):
                continue
            text = info.get("text") if m.kind == "figure" else info.get("name")
            if any(getattr(o, "motion", None) is not None and getattr(o.motion, "leader", None) == text for o in f.movers):
                continue   # (the map gives it one already)
            got = partners.partner_for(self.game, self.area_data, info)
            if not got:
                continue
            _free = lambda t: (0 <= t[0] < f.w and 0 <= t[1] < f.h and f.walkable(*t) and not f.occupied(*t)
                               and f.tile(*t) != core.SURF and t != tuple(self.run.player))
            _ground = lambda t: (0 <= t[0] < f.w and 0 <= t[1] < f.h and f.tile(*t) != core.SURF
                                 and (f.walkable(*t) or str(f.decor.get(tuple(t), "")).startswith("barrier")
                                      or any((o.x, o.y) == tuple(t) for o in f.movers)))   # (a barrier, a person: the way)
            spot = partners.pick_spot((m.x, m.y), _free, self.run.player, _ground)   # (never the owner's last side you can reach,
                                                                                     #  nor the one way into a room: Ein's Golbat)
            if spot is None:
                continue
            species, owner = got
            p = core.Mover("figure", spot[0], spot[1], {"text": species, "action": "EVENT",
                                                         "event": {"lines": partners.line(owner, species)}})
            p._partner_of = m
            p.motion = npc.Motion(spot, {"m": "trail", "who": text}, seed=self.area_key)
            f.movers.append(p)
        self._partners_key = (id(f), len(f.movers))

    def _boss_spot(self):
        """The tile the area's boss sleeps on (the map's "boss_spot"), while it is still there."""
        art = self.recipe.get("art") or {}
        spot = art.get("boss_spot")
        if not spot and art.get("floors") and hasattr(self, "run") and self.run.index < len(art["floors"]):
            spot = art["floors"][self.run.index].get("boss_spot")   # (a boss on one floor of a place of floors: the Pokemon Tower's ghost on 6F)
        boss = self.area_data.get("area_boss") or {}
        if not spot or not boss or self.game.story_manager.story_flags.get(boss.get("victory_flag")):
            return None
        return tuple(spot)

    def _sync_boss_spot(self):
        _art = self.recipe.get("art") or {}
        _has = _art.get("boss_spot") or any(f.get("boss_spot") for f in (_art.get("floors") or []))
        if _has and hasattr(self, "run") and not self._boss_spot():
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

    def flip_statue(self):
        """A statue with a switch (the floor's "switch": {"flag", "on", "off"}: the Pokémon Mansion's): each press flips
        the flag, and with it every gate the flag shuts or opens (the floor's "barred", its "picture_when")."""
        sw = self._here_art().get("switch") or {}
        flags = self.game.story_manager.story_flags
        if not self._ready() or not sw.get("flag"):
            return
        self.walk_goal = None

        def press():
            on = not flags.get(sw["flag"])
            flags[sw["flag"]] = on
            self._clear_boulders()
            self._floor_surf = None
            self.say(sw.get("on" if on else "off") or ["Click! Something moved somewhere."])
        if sw.get("ask"):   # (asked first: "ask" lines, then yes / no; Orange 5.7's lab statues, 11-18)
            self._ask_press(sw, press)
            return
        press()

    PRESS_TITLE = "PRESS THE SWITCH?"

    def _ask_press(self, sw, press):
        """A switch that asks first (Orange 5.7, Jordan 11-18): its "ask" lines, then the game's yes / no list; No (or
        BACK): its "later" lines ("Maybe later.")."""
        from src.states.systems.pick_list import PickListState
        ask = sw.get("ask") if isinstance(sw.get("ask"), list) else ["There's a secret switch here! Do you want to press it?"]

        def answer(v):
            if v:
                press()
            else:
                self.say(sw.get("later") or ["Maybe later."])
        self.say(ask, lambda: self.game.change_state(PickListState(self.game, self, self.PRESS_TITLE, [("Yes", True), ("No", False)], answer)))

    def shake(self, ms=700):
        """The screen shakes a moment (5.7's tremor as a switch moves the rocks: its special 0x136)."""
        self._shake_until = pygame.time.get_ticks() + int(ms)

    def press_secret(self, t):
        """A secret switch pressed once (the floor's "secret_switches" {"x,y": {"flag", "lines", "done"}} on a "secret"
        decor tile: Orange 5.7's island caves): sets its flag, and with it every gate the flag opens (its "barred", its
        "picture_when"). Pressed already: its "done" words."""
        sw = (self._here_art().get("secret_switches") or {}).get("%d,%d" % tuple(t)) or {}
        flags = self.game.story_manager.story_flags
        if not self._ready() or not sw.get("flag"):
            return
        self.walk_goal = None
        if flags.get(sw["flag"]):
            self.say(sw.get("done") or ["The switch has been pressed already."])
            return

        def press():
            flags[sw["flag"]] = True
            self._clear_boulders()
            self._floor_surf = None
            self._over_key = None
            if sw.get("shake"):   # (5.7's small tremor: the screen shakes as the rocks move)
                self.shake(sw["shake"] if isinstance(sw["shake"], int) and sw["shake"] > 1 else 700)
            self.say(sw.get("lines") or ["Click! Something moved somewhere."])
        if sw.get("ask"):   # (Jordan 11-18: asked first, as 5.7 does: "Do you want to press it?", No: "Maybe later.")
            self._ask_press(sw, press)
            return
        press()

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
            return self._mon_img(int(look[4:]), fc) or icon(self.game, int(look[4:]), TILE + 6)
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
        _leads = None
        for m in list(f.movers):
            mo = self._motion(m)
            if mo is None:
                continue
            if mo.kind == "trail":   # (a Pokemon at its trainer's heels: into the tile they just left)
                if _leads is None:
                    _leads = {o.payload.get("text"): self._motion(o) for o in f.movers if o.kind == "figure" and isinstance(o.payload, dict)}
                    _leads.update({(o.payload[1] or {}).get("name"): self._motion(o) for o in f.movers   # (a trainer's partner: partners.py)
                                   if o.kind == "trainer" and isinstance(o.payload, tuple) and isinstance(o.payload[1], dict)})
                from src.dungeon import npc as _npc
                _npc.trail(mo, _leads.get(mo.leader), lambda t, m=m: self._npc_free(t, m))
                m.x, m.y = mo.pos
                m.facing = mo.facing
                continue
            if mo.gone:  # (sent away after a scene, out of view: npc.Scenes.sweep)
                self.run.remove(m)
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
        sc.sweep()
        if sc.busy():
            sc.tick()
            if not sc.busy():  # (a scene just ended: whoever it held and whose story step is done leaves: the beaten rival)
                self._sync_figures()
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

    def npc_cue(self):
        """A story scene starts: the alert chime (src/dungeon/npc.py Scenes.start)."""
        snd = getattr(self.game.assets, "alert_sfx", None)
        if snd:
            snd.play()

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

    def _actor_img(self, sheet, facing, frame, native=False):
        """A scene's walker: a person's walking sheet, or a Pokemon ("mon:<species>": its following sprite). native: drawn
        at the source game's own size (its 16-pixel tiles as our tiles: 5.7's Lugia in flight, Orange 11-18)."""
        if native and not str(sheet).startswith("mon:"):
            return self._sheet_frame(sheet, facing, frame=frame, scale=max(1, round(TILE / 16)))
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
        self.run.reveal()   # (walked by a scene: you see where you go, 11-18)

    def npc_lock(self, on):
        self._scene_lock = on
        if on:
            self.walk_goal = None
        if not on:
            if getattr(self, "_cam_focus", None):
                self._cam_ease_until = pygame.time.get_ticks() + 1500   # (gliding back to you)
            self._cam_focus = None   # (the scene's over: the view back on you)
            self._scene_zoom = None   # (and the camera back to its usual distance)

    def npc_ground(self, t):
        """The map's character at a tile on this floor (npc.route), None off the map or with no drawn map."""
        grid = (self._here_art() or {}).get("art") or []
        x, y = t
        return grid[y][x] if 0 <= y < len(grid) and 0 <= x < len(grid[0]) else None

    def npc_look(self, t):
        """A scene moves the view to a tile (None: back to you); what it looks at is seen (the fog lifts there)."""
        self._cam_ease_until = pygame.time.get_ticks() + 1500   # (it glides there)
        self._cam_focus = tuple(t) if t else None
        if t and hasattr(self, "run"):
            self.run.reveal_at(int(t[0]), int(t[1]))

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
        if isinstance(item, dict) and item.get("stays") and not self._flag_ok(item):  # (their part is done: they just chat till you go)
            self.say(item["stays"])
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
        if action == "FISH":   # (no FISH button in the area's menu: any area with rod Pokemon still lets you cast - 11-19)
            item = {"text": "FISH", "action": "FISH", "condition": "can_fish"}
            if self._check_route_condition("can_fish", False, item):
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
        pz = self._move_puzzle()
        if pz:
            return pz["label"], lambda: self._try_move_puzzle(pz)
        plan = self._plan()
        if plan.get("dive") is not None and self.run.player in getattr(self.run.floor, "deep", ()):
            return "DIVE", self.dive_here
        if plan.get("surface") is not None and (not getattr(self.run.floor, "deep", None) or self.run.player in self.run.floor.deep):   # (a seabed with sunlit tiles: up from those only)
            return "SURFACE", self.surface_here
        if self._beside("decor:slot"):
            return "PLAY SLOTS", self.play_slots
        if (self.recipe.get("gate") or {}).get("switch") and self._beside("decor:" + self.recipe["gate"]["switch"]):
            return "CHECK", self.push_switch
        sec = self._beside("decor:secret") if self._here_art().get("secret_switches") else None
        if sec:
            return "CHECK", lambda: self.press_secret(sec)
        if self._here_art().get("switch") and self._beside("decor:statue"):
            return "CHECK", self.flip_statue
        if self._beside("water") and self._menu_item("FISH"):
            return "FISH", self.fish_here
        if self._beside("tree") and self._menu_item("HEADBUTT"):
            return "HEADBUTT", self.headbutt_here
        return None

    # ---------------------------------------------------------------- braille puzzles (Emerald's Regi caves)
    def _puzzles(self, kind):
        """This floor's open puzzles of a kind (map "puzzles": "move": use a field move on the right spot, "at", with the
        HM "item", anywhere in "zone" [x0, y0, x1, y1]; "lap": read the braille at "read", then walk past every one of
        "tiles": the Desert Ruins' Rock Smash, the Ancient Tomb's Flash, the Island Cave's lap of the walls)."""
        flags = self.game.story_manager.story_flags
        return [pz for pz in (self._here_art().get("puzzles") or []) if pz.get("kind") == kind and not flags.get(pz["flag"])]

    def _move_puzzle(self):
        x, y = self.run.player
        inv = self.game.story_manager.inventory
        for pz in self._puzzles("move"):
            x0, y0, x1, y1 = pz["zone"]
            if x0 <= x <= x1 and y0 <= y <= y1 and inv.get(pz["item"], 0) > 0:
                return pz
        return None

    def _try_move_puzzle(self, pz):
        if not self._ready():
            return
        self._pose_start("field")   # (your own field-move pose, if you have one: Orange 5.7's Ash)
        if tuple(self.run.player) == tuple(pz["at"]):
            self._open_puzzle(pz)
        else:
            self.say(pz.get("miss") or ["Nothing happened."])

    def _read_puzzle(self, t):
        """Braille read at t: a lap puzzle starts (walk past its tiles from here on)."""
        for pz in self._puzzles("lap"):
            if tuple(pz["read"]) == tuple(t):
                self._lap = {"flag": pz["flag"], "pz": pz, "left": {tuple(v) for v in pz["tiles"]}}

    def _lap_step(self):
        lap = getattr(self, "_lap", None)
        if lap and not self.game.story_manager.story_flags.get(lap["flag"]):
            lap["left"].discard(tuple(self.run.player))
            if not lap["left"]:
                self._open_puzzle(lap["pz"])

    def _open_puzzle(self, pz):
        self.game.story_manager.story_flags[pz["flag"]] = True
        self._lap = None
        self._clear_boulders()   # (its door's bar: "until" the flag)
        self._floor_surf = None
        self._over_key = None
        self.say(pz.get("lines") or ["Something opened!"])

    # ---------------------------------------------------------------- Dive (Hoenn's deep sea)
    def _plan(self):
        """This floor's own plan (a drawn map's: its Dive floor, its surface, its wild pool), else {}."""
        layout = self.run.recipe.get("layout") if hasattr(self, "run") else None
        return layout[self.run.index] if layout and self.run.index < len(layout) else {}

    def dive_here(self):
        """On deep, dark sea: Dive to the seabed floor, the same spot below."""
        if not self._ready():
            return
        if self.game.story_manager.inventory.get("HM_DIVE", 0) <= 0 and self.game.story_manager.inventory.get("SCUBA_GEAR", 0) <= 0:   # (Orange 5.7: the Scuba Gear dives, 11-18)
            self.say(["The sea is deep and dark here.", "A Pokemon could DIVE down to the seabed."])
            return
        plan = self._plan()
        to, spot = plan["dive"], tuple(plan.get("dive_at") or self.run.player)   # (dive_at: you swim through to a spot of its own: the Abandoned Ship's flooded cabin, to its hidden floor)
        below = self.run.made(to)
        if plan.get("dive_links") and not plan.get("dive_at"):   # (a seabed of its own size: this dark patch leads to its own sunlit patch below)
            spot = self._linked_spot(plan["dive_links"], "up", "down", self.run.player,
                                     lambda x, y: (x, y) in below.deep and below.walkable(x, y) and not below.mover_at(x, y))
            if spot is None:
                self.flash("There's rock right under you here.", 100)
                return
        if below.mover_at(*spot) and below.walkable(*spot):   # (someone's on the spot you come down on - a wild Pokemon swimming there, 11-24: the nearest free one, not "rock")
            near = sorted(((x, y) for y in range(spot[1] - 2, spot[1] + 3) for x in range(spot[0] - 2, spot[0] + 3)
                           if below.walkable(x, y) and not below.mover_at(x, y)),
                          key=lambda t: abs(t[0] - spot[0]) + abs(t[1] - spot[1]))
            spot = near[0] if near else spot
        if not below.walkable(*spot) or below.mover_at(*spot):
            self.flash("There's rock right under you here.", 100)
            return
        self.walk_goal = self.sliding = None
        self.run.jump_floor(to, spot)
        self.partner = self.partner_from = spot
        self._floor_surf = None
        self.flash("You dived down and swam through to somewhere else!" if plan.get("dive_at") else "You dived down to the seabed!", 110)

    def surface_here(self):
        """On the seabed: back up to the sea right above you (only where there's open water overhead)."""
        if not self._ready():
            return
        to, spot = self._plan()["surface"], self.run.player
        above = self.run.made(to)
        links = (self.run.recipe.get("layout") or [{}])[to].get("dive_links")
        if links:   # (a seabed of its own size: up from a sunlit tile only, to the matching place in its own dark patch above)
            spot = None if spot not in self.run.floor.deep else self._linked_spot(
                links, "down", "up", spot, lambda x, y: (x, y) in above.deep and above.tile(x, y) == core.SURF
                and not above.mover_at(x, y) and (x, y) not in above.exits)
        if spot is None or above.tile(*spot) != core.SURF or above.mover_at(*spot) or spot in above.exits:
            self.flash("There's no open water above you here.", 100)
            return
        self.walk_goal = self.sliding = None
        self.run.jump_floor(to, spot)
        self.partner = self.partner_from = spot
        self._floor_surf = None
        self.flash("You came up to the surface!", 110)

    @staticmethod
    def _linked_spot(links, a, b, here, ok):
        """A floor's "dive_links" [{"up": [x0, y0, x1, y1], "down": [...]}]: the link whose `a` rectangle holds here; its
        tile at the same place across the `b` rectangle, or the nearest there that ok(x, y) allows. None: no link, no tile."""
        for lk in links:
            x0, y0, x1, y1 = lk[a]
            if x0 <= here[0] <= x1 and y0 <= here[1] <= y1:
                X0, Y0, X1, Y1 = lk[b]
                tx = X0 + int((here[0] - x0 + 0.5) * (X1 - X0 + 1) / (x1 - x0 + 1))
                ty = Y0 + int((here[1] - y0 + 0.5) * (Y1 - Y0 + 1) / (y1 - y0 + 1))
                got = [(x, y) for y in range(Y0, Y1 + 1) for x in range(X0, X1 + 1) if ok(x, y)]
                return min(got, key=lambda t: (abs(t[0] - tx) + abs(t[1] - ty), t[1], t[0])) if got else None
        return None

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
            from src.world import phenomena as _phen
            self._fish_ripple = _phen.is_ripple(self, self._beside("water"))   # (casting into rippling water: its own bites)
            if self._player_extra("fish"):   # (your own casting frames, Orange 5.7's Ash: face the water, cast, then the bite)
                w = self._beside("water")
                self.facing = (w[0] - self.run.player[0], w[1] - self.run.player[1])
                self._pose_start("fish")
                self._pose_then = self.action_fish
                return
            self.action_fish()  # the route's own: a bite, a battle, then back to the map

    def headbutt_here(self):
        if self._ready() and self._beside("tree") and self._menu_item("HEADBUTT"):
            self.walk_goal = None
            self.action_headbutt()

    # ---------------------------------------------------------------- wild Pokemon
    def _make_wild(self, rng, spot=None):
        """A wild Pokemon for the area (on a wide floor: for the part of it where it will stand)."""
        story = self.game.story_manager
        from src.world import poke_snacks as _snacks
        if self.area_key in _snacks.SPOTS:   # (a Poke Spot: only what came for the snacks, once - XD; Orre batch 8d)
            if getattr(self, "_snack_spawned", False):   # (one visitor a visit: the map's other wild slots stay empty)
                return None
            mon = _snacks.visitor_mon(self.game, self.area_key)
            self._snack_spawned = mon is not None
            return mon
        flag = f"zone_{self.area_key}"
        keep = story.story_flags.get(flag)
        if spot is not None and getattr(self, "per_floor", 1) > 1 and self.zones:
            index = self.run.index if hasattr(self, "run") else 0  # (the first floor, while the walk is made)
            story.story_flags[flag] = self.zones[self._zone_index(index, spot[0], spot[1])]
        self._wild_spot = tuple(spot) if spot is not None else None   # (where it will stand: dark grass or not, 11-20)
        try:
            if self.area_data.get("safari_game") and core.CURRENT_TILE not in (core.SURF, core.WATER):
                from src.world import hordes as _hordes   # (the Safari Game has no battles: a horde's Pokemon walks the map
                if _hordes.roll(self.game, self.area_data, rng):   # on its own, caught with Safari Balls - Hoenn Q16, 11-24)
                    got = _hordes.one(self.game, self.area_key, self.area_data, rng)
                    if got is not None:
                        return got
            return self._wild_for_pool(rng)
        finally:
            if keep is not None:
                story.story_flags[flag] = keep

    def _wild_for_pool(self, rng, kind=None):
        """kind "smash": the area's Rock Smash Pokemon; on a sea tile (core.CURRENT_TILE) its surfing Pokemon (Jordan,
        11-14: the games' own pools, "rock_smash_pool_percentages" / "surf_pool_percentages"), else its usual pool."""
        from src.world import wild_tables as _wt
        if (_wt.tables(self.area_data) or self._floor_tables()) and kind != "smash":   # (the place's own game's slots, levels and seasons: B2W2's, 11-20)
            got = self._from_wild_tables(rng)
            if got is not None:
                return got
        area = self.area_data
        own_kind = {"smash": "rock_smash_pool_percentages", "surf": "surf_pool_percentages"}.get(
            kind or ("surf" if core.CURRENT_TILE in (core.SURF, core.WATER) else None))
        if own_kind and area.get(own_kind) and self.game.loader.area_data.get(area[own_kind]):
            area = {k: v for k, v in dict(area, wild_pool_percentages=area[own_kind]).items()
                    if k not in ("zone_pools", "morning_pool_percentages", "day_pool_percentages", "night_pool_percentages")}
        layout = self.recipe.get("layout") if isinstance(getattr(self, "recipe", None), dict) else None
        own = layout[core.CURRENT_FLOOR].get("pool") if layout and core.CURRENT_FLOOR < len(layout) else None
        if not own and not own_kind:   # (a walked floor's own land Pokemon: "floor_pools" {"<floor>": pool} - Dark Cave's two sides)
            own = (area.get("floor_pools") or {}).get(str(core.CURRENT_FLOOR))
        if own:  # (this floor's own Pokemon: the seabed's; a floor_pools one all day, as the game's)
            area = {k: v for k, v in dict(area, wild_pool_percentages=own).items() if k not in (
                "zone_pools", "morning_pool_percentages", "day_pool_percentages", "night_pool_percentages")}
        pool = self._get_wild_pool(area)
        if pool and own_kind == "surf_pool_percentages" and area.get("wild_pool_percentages") == self.area_data.get(own_kind):
            from src.world import swarms as _swarms   # (a swarm out on the water: Route 27's Luvdisc, SoulSilver; 11-19)
            pool = _swarms.adjust(self.game, pool, self.area_key, "surf")
        if not pool:
            return None
        pid = int(Utils.weighted_random_choice(pool))
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)
        if not raw or raw.get("id", 0) == 0:
            return None
        p = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, p, self.area_key)
        return p

    def _dark_tiles(self):
        art = (getattr(getattr(self, "run", None), "recipe", None) or getattr(self, "recipe", None) or {}).get("art") or {}
        return {tuple(t) for t in (art.get("dark_grass") or [])}

    def _floor_tables(self):
        """This floor's own "wild_tables" (a room of the map with its own wild Pokemon), else None."""
        layout = self.recipe.get("layout") if isinstance(getattr(self, "recipe", None), dict) else None
        f = layout[core.CURRENT_FLOOR] if layout and 0 <= core.CURRENT_FLOOR < len(layout) else None
        return (f.get("wild_tables") or None) if isinstance(f, dict) else None

    def _from_wild_tables(self, rng):
        """A wild Pokemon from the area's "wild_tables" (src/world/wild_tables.py): on the water its surfing slots, in dark
        grass its dark grass slots, at a phenomenon its own (rustling grass, rippling water), else the tall grass's."""
        from src.world import wild_tables as _wt
        on_water = core.CURRENT_TILE in (core.SURF, getattr(core, "WATER", None))
        kind = getattr(self, "_phenom_kind", None) or ("surf" if on_water else
                                                       "dark" if getattr(self, "_wild_spot", None) in self._dark_tiles() else "grass")
        place = {"wild_tables": self._floor_tables()} if self._floor_tables() else self.area_data   # (a room's own: Relic Castle's Baltoy rooms)
        got = _wt.pick(place, kind, rng) or (_wt.pick(place, "grass", rng) if kind in ("dark", "rustle") else None)
        if got is None:
            return None
        pid, level = got
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)
        if not raw or raw.get("id", 0) == 0:
            return None
        p = Pokemon(raw, self.game.assets, size_mult=3.125)
        p.level = level
        p.current_hp = p.get_max_hp()
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
        home = self.__dict__.pop("_ow_home", None)
        if mover is not None:
            if kind == "wild":
                if getattr(mover.payload, "snack_visitor", None):   # (the snack tray's visitor: gone - Orre batch 8d)
                    from src.world import poke_snacks as _snacks
                    _snacks.visitor_gone(self.game, mover.payload.snack_visitor)
                self.run.remove(mover)
            elif kind == "trainer":
                idx = mover.payload[0]
                if self.game.story_manager.beaten_today(self.area_key, idx):
                    self.run.remove(mover)
                    from src.world import vs_seeker as _vs
                    _rematch_won = _vs.is_ready(self.game.story_manager, self.area_key, idx)
                    if _vs.is_ready(self.game.story_manager, self.area_key, idx):   # (a VS Seeker rematch won)
                        _pool0 = self.area_data.get("trainer_pool", [])
                        _vs.won(self.game.story_manager, self.area_key, idx,
                                _vs.stage_for(self.game.story_manager, self.area_key, idx, _pool0[idx] if 0 <= idx < len(_pool0) else {}))
                    from src.world import phone as _phone   # (a phone trainer asks for your number; a rematch's gift is given)
                    _pool = self.area_data.get("trainer_pool", [])
                    _info = _pool[idx] if 0 <= idx < len(_pool) and isinstance(_pool[idx], dict) else {}
                    _re = _phone.rematch_info(self.game, self.area_key, idx, _info)
                    if _rematch_won or (_re.get("team") and _re.get("team") != _info.get("team")):   # (a Feat: rematches won, VS Seeker or phone; J6 11-24)
                        from src.world import feats as _feats
                        _feats.note(self.game.story_manager, "rematches")
                    if _re.get("_phone_gift"):
                        _pg = _re["_phone_gift"]
                        for _f in (_pg if isinstance(_pg, list) else [_pg]):
                            self.game.story_manager.story_flags[_f] = True
                    _lines = _phone.register_after_win(self.game, self.area_key, _info)
                    if _lines:
                        self._phone_say = _lines
                else:  # lost (or ran out of Pokemon): it looks away, so you can get past
                    mover.facing = (-mover.facing[0], -mover.facing[1])
        self.encounter = None
        self.mode = "MAP"
        self.walk_goal = None
        self._sync_figures()
        if home:   # (the battle stood on open ground nearby: everyone walks back where they met; Jordan 11-24)
            m = home["mover"]
            goals = [("me", home["player"])] + ([(m, home["at"])] if m in self.run.floor.movers else [])
            hf = home["mover_facing"]

            def there():
                self.facing = home["facing"]
            self._ow_walk_start(goals, there)
            if m in self.run.floor.movers:   # (a trainer you lost to: back on its spot, looking away, as before)
                self._ow_walk["end_face"] = (m, (-hf[0], -hf[1]))

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
        for b in self.hud_buttons:   # (hidden while the catch screen was over the map)
            b.set_visibility(True)
        self.walkup_catch_over()   # (Honey's three: the one you caught is gone, the others run off)
        self._sync_figures()

    def _leave(self, target):
        from src.world import walk_partners   # (a walking partner says goodbye where Platinum has them, or waits)
        said = walk_partners.on_leave(self.game.story_manager, self.area_key, target)
        if said:
            self.say(said, then=lambda: self._leave_now(target))
            return
        self._leave_now(target)

    def _leave_now(self, target):
        self.game.dungeon_state = None
        if hasattr(self, "run"):   # (how you leave: over the map's edge, or by a door or a cave's mouth: the area change's wipe)
            from src.vfx import area_changes
            (_x, _y), _f = self.run.player, self.run.floor
            _art = (self._here_art() or {}).get("art") or []
            _ch = _art[_y][_x] if 0 <= _y < len(_art) and isinstance(_art[_y], str) and 0 <= _x < len(_art[_y]) else None
            area_changes.note_leave(self.game, self.area_key, room=self._indoors(self.run.index),
                                    edge=area_changes.edge_exit(_ch, (_x, _y), (_f.w, _f.h)))
        boat = self.area_data.get("boat_home") or {}   # (an island two regions share: the boat takes you back the way you came,
        if target == boat.get("dock"):                 #  Navel Rock and Birth Island: Lilycove from Hoenn, One Island from Sevii)
            target = boat.get(self.game.story_manager.get_current_region(), target)
        from src.coop import travel
        travel.passing(self.game, lambda: self.action_exit_route(target))

    # ---------------------------------------------------------------- talking
    def show_dialogue(self, lines, callback=None):
        """The route menu's dialogue (a boss's lines before its battle: Berry Forest's Hypno), as say(): the box goes away when
        it's done. (11-17: the route menu's own left it up, finished, with no callback: you could never move again.)"""
        if self.game.current_state is not self and isinstance(getattr(self.game.current_state, "dialogue_box", None), type(self.dialogue_box)):
            return super().show_dialogue(lines, callback)
        self.say(lines, then=callback)
        return self.dialogue_box

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
        return self.mode == "MAP" and self.anim == 0 and not self.dialogue_box.visible and not getattr(self, "_scene_lock", False) \
            and not getattr(self, "_pose_then", None) \
            and not getattr(self, "_ride", None)   # (mid-cast: see fish_here; riding a platform or hook, or falling: Citadark 11-21)

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

    def _may_run(self):
        """Running (Shift held), on foot only: not surfing, riding, hopping, sliding on ice, or following someone in a scene."""
        if not running() or not hasattr(self, "run") or getattr(self, "hop", None) or getattr(self, "sliding", None) or getattr(self, "_scene_lock", False):
            return False
        try:
            if self.run.floor.tile(*self.run.player) == core.SURF or self._cycling():
                return False
        except Exception:
            return False
        return True

    def _ramp_far(self):
        """Top gear on the Bicycle (Shift held): off a bike ramp you fly the far way (Platinum's fourth gear)."""
        return running()

    def _ramp_landing(self, ramp, dx, dy):
        """Where riding (dx, dy) onto the bike ramp at ramp lands you, or None (not a ramp that way, no Bicycle, or
        nowhere clear to land: someone or something there)."""
        f = self.run.floor
        if str(f.decor.get(tuple(ramp), "")) != f"ramp:{dx},{dy}" or self.game.story_manager.inventory.get("BICYCLE", 0) <= 0:
            return None
        from src.dungeon import art as _art
        k = _art.RAMP_JUMP[1 if self._ramp_far() else 0]
        land = (ramp[0] + dx * k, ramp[1] + dy * k)
        if not f.walkable(*land) or f.mover_at(*land) is not None or str(f.decor.get(land, "")):
            return None
        return land

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
        return __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_SURF")   # (Kanto: with the Soul Badge, FireRed's rule)

    def _on_surf(self, t=None):
        f = self.run.floor
        return f.tile(*(t or self.run.player)) == core.SURF

    def _nearest_land(self):
        """The nearest tile you can stand on without Surf (not water, not a way out), going through water and land, or None."""
        f = self.run.floor
        start = tuple(self.run.player)
        seen, todo = {start}, [start]
        while todo:
            nxt = []
            for x, y in todo:
                if (x, y) != start and f.walkable(x, y) and f.tile(x, y) != core.SURF and (x, y) not in f.exits:
                    return (x, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < f.w and 0 <= ny < f.h and (nx, ny) not in seen and (f.walkable(nx, ny) or f.tile(nx, ny) == core.SURF):
                        seen.add((nx, ny))
                        nxt.append((nx, ny))
            todo = nxt
        return None

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
        if self._level_edge(tuple(before), tuple(to)) or self._height_edge(tuple(before), tuple(to)):   # (a drop between two levels: no stepping off it, as in Black 2; a Gen 3 cliff: 11-23)
            self.walk_goal = None
            return
        if self._on_surf(to) and not self._on_surf(before) and not self._can_surf():
            self.walk_goal = None  # (the open sea: Surf it, Routes 19-21)
            self.flash("The sea is deep. You need Surf to cross it!", 100)
            return
        if str(self.run.floor.decor.get(to, "")).startswith("box:"):   # (a crate you push by walking into it: XD's Key Lair, 11-21)
            self._push_box(to, dx, dy)
        if str(self.run.floor.decor.get(to, "")).startswith("stone:"):   # (a stone, 3 x 3: it slides till it stops - Chargestone, 11-24)
            self._push_stone(int(str(self.run.floor.decor[to]).split(":")[1]), dx, dy)
        if self._board_platform(to):   # (a moving platform's track ahead of you: it carries you across: Citadark's volcano, 11-21)
            return
        hopped = False
        if str(self.run.floor.decor.get(to, "")) == f"ledge:{dx},{dy}":  # (a ledge, from its high side: hop over it)
            over = (to[0] + dx, to[1] + dy)
            if self.run.floor.walkable(*over) and self.run.floor.mover_at(*over) is None:
                self.run.player = to
                hopped = True
        ramp = self._ramp_landing(to, dx, dy)
        if ramp:   # (a bike ramp, ridden its way: you jump off it, one tile on in normal gear, three in top gear: Platinum)
            self.run.player = (ramp[0] - dx, ramp[1] - dy)
            hopped = True
        events = self.run.step(dx, dy)
        if hopped and self.run.player == to:  # (couldn't land after all)
            self.run.player = before
        if ramp and tuple(self.run.player) != ramp:
            self.run.player = before
        self.hop = (hopped or tuple(self.run.player) in getattr(self, "_stones", ()) or tuple(before) in getattr(self, "_stones", ()))             and self.run.player != before  # (a ledge; onto, along and off the round stones, hopping on the Bicycle)
        leaving = any(ev[0] in ("exit", "stairs", "stairs_up") for ev in events)
        on_ice = self.run.player != before and self.run.player in getattr(self.run.floor, "ice", ())
        self.sliding = (dx, dy) if on_ice and not leaving else None
        swept = getattr(self.run.floor, "current", {}).get(self.run.player) if self.run.player != before and not leaving else None
        if swept and self.run.player != before and self._whirl_pull(dx, dy):
            swept = None  # (Orange 5.7: the Whirlpuller carries you straight across a flowing whirlpool, 11-17)
        if swept and (self.run.player[0] + swept[0], self.run.player[1] + swept[1]) != before:
            self.sliding = swept  # (a sea current: it carries you its own way, whichever way you came onto it; never straight back and forth)
        if self.sliding and tuple(self.run.player) in self._stop_tiles():
            self.sliding = None  # (a stop tile: a spin tile's slide ends here: the Rocket Hideout's maze)
        if self.sliding:
            self.walk_goal = None
        if self.run.player != before and not leaving:
            self._ride_from_tile(tuple(self.run.player))   # (onto a hook's pad, a glowing drop tile, a lift: Citadark, 11-21)
        if self.run.player != before:
            self.anim_from, self.anim = before, STEP_FRAMES
            _m = self.run.recipe.get("art") or {}
            _g = (_m["floors"][self.run.index]["art"] if _m.get("floors") else _m.get("art")) or []
            _x, _y = self.run.player
            if 0 <= _y < len(_g) and 0 <= _x < len(_g[_y]) and _g[_y][_x] in "89":  # (deep snow, marsh mud: each step takes twice as long)
                self.anim = STEP_FRAMES * 2
            if dy < 0 and self._downhill(before):  # (pedalling up the Cycling Road's slope: each step takes twice as long)
                self.anim = STEP_FRAMES * 2
            if ramp:   # (through the air off a bike ramp: longer the further you fly)
                self.anim = STEP_FRAMES * (2 if abs(ramp[0] - before[0]) + abs(ramp[1] - before[1]) <= 2 else 3)
                self.flash("You jumped the ramp!" if self._ramp_far() else "A short hop off the ramp!", 45)
            self.partner_from, self.partner = self.partner, before  # it steps where you were
            self._ctrail_from = list(self._ctrail); self._ctrail = [before] + self._ctrail[:3]   # (companions: a step behind each other)
            self.steps += 1
            from src.world import vs_seeker as _vs
            _vs.step(self.game.story_manager)   # (the VS Seeker charges as you walk)
            from src.world import shadow as _shadow, purify_chamber as _chamber
            from src.world import poke_snacks as _snacks
            _said = _shadow.walked(self.game) + _chamber.walked(self.game) + _snacks.walked(self.game)   # (Orre: walking opens a Shadow Pokemon's heart, with
            if _said:                                                       #  you or in the Purify Chamber; 11-21 - the party's was
                self.flash(_said[-1], 150)                                  #  never called before)
            from src.world import feats as _feats
            _feats.note(self.game.story_manager, "steps")   # (a Feat: steps walked)
            self._lap_step()
            if not self._hidden_item(self.run.player):
                self._cracked_floor(self.run.player) or self._thin_ice(self.run.player)
                self._itemfinder(self.run.player)
            self._copy_step(dx, dy)
            self._note_area()
            self._contest_tick()
            if getattr(self, "safari", None) and self.safari["steps"] > 0:
                self.safari["steps"] -= 1
            from src.world import poke_radar as _radar
            if _radar.on_step(self):   # (into a shaking patch: a wild Pokemon jumps out; Platinum's Poke Radar, 11-19)
                return
            from src.world import dexnav as _dexnav
            if _dexnav.on_step(self):   # (onto a hidden Pokemon's spot: ORAS's DexNav, Hoenn; 11-19)
                return
            from src.world import phenomena as _phen
            if _phen.on_step(self):   # (into rustling grass, onto rippling water: B2W2's phenomena, 11-20)
                return
            from src.world import ambush as _amb
            if _amb.on_step(self):   # (into shaking grass, a dust puff, ripples: an ambush spot, 11-24)
                return
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
                if self._canon_changes():   # (as the games: no words, the floor's fade and its sign)
                    __import__("src.vfx.area_changes", fromlist=["change"]).change(self, "stairs", self._descend)
                    return
                self.say([self._stairs_line(self.run.index + 1)], then=self._descend)
                return
            elif kind == "warp":  # a passage to another floor (a map's "links")
                self.walk_goal = None
                _i, _x, _y = (int(v) for v in ev[1].split(":")[1:4])
                _ww = (self.recipe.get("art") or {}).get("warp_world") if isinstance(self.recipe.get("art"), dict) else None
                if _ww:   # (a place whose passages lead somewhere new each time: its region module picks - src/world/<warp_world>.py
                    _to = __import__("importlib").import_module("src.world." + str(_ww)).warp(   # warp(state, door, (floor, x, y))
                        self, tuple(self.run.player), (_i, _x, _y))                              # -> (floor, x, y[, lines said on arrival]);
                    if _to:                                                                      # Platinum's Turnback Cave, Sinnoh 11-24)
                        _i, _x, _y = _to[:3]
                        self._warp_say = list(_to[3]) if len(_to) > 3 and _to[3] else None
                if self._canon_changes():   # (as the games: the door's, panel's, hole's or stairs' fade, no words)
                    _ac = __import__("src.vfx.area_changes", fromlist=["change"])
                    _fall = ev[1].endswith(":fall")
                    _kind = ("fall" if _fall else "door_in" if self._indoors(_i) and not self._indoors(self.run.index)
                             else "door_out" if self._indoors(self.run.index) and not self._indoors(_i)
                             else "warp" if _i == self.run.index else "stairs")
                    if _fall:   # (a hole: said, as before, then the fall's fade)
                        self.say(["Whoa! You fell through a hole in the floor!"],
                                 then=lambda: _ac.change(self, "fall", lambda: self._warp(_i, _x, _y, land=True)))
                    else:
                        _ac.change(self, _kind, lambda: self._warp(_i, _x, _y, land=_fall))
                    return
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
                if self._canon_changes():
                    __import__("src.vfx.area_changes", fromlist=["change"]).change(self, "stairs", self._ascend)
                    return
                self.say([self._stairs_line(self.run.index - 1)], then=self._ascend)
                return
            elif kind == "bump" and ev[1].kind == "escort":   # (Jessie & James's Meowth: talking to it is talking to them)
                from src.world import escorts as _esc
                lead = _esc.leader_of(ev[1])
                if lead is not None and lead in self.run.floor.movers:
                    self._handle([("bump", lead)])
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
        if index < len(names) and names[index]:  # (our map's own: Rock Tunnel's 1F, B1F, 1F)
            return names[index]
        if index < len(names):  # (a route's outdoors, with its rooms as floors: "To Route 2" from the Forest Gate, 11-21)
            return self._exit_label(self.area_key)
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
        self._reset_trail()
        self.banner = 120
        self._floor_sign(True)

    def _warp(self, index, x, y, land=False):
        if self.zones and self._indoors(self.run.index) and not self._indoors(index):  # (out of a house: the area its door is in, said nothing)
            self.game.story_manager.story_flags[f"zone_{self.area_key}"] = self.zones[self._zone_index(index, x, y)]
        else:
            self._set_zone(index)
        _was = self.run.index
        self.run.warp(index, x, y, land=land)
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.run.player
        self._reset_trail()
        self.banner = 120
        self._floor_sign(index != _was)
        _say = getattr(self, "_warp_say", None)   # (what a warp_world module said comes with the passage: a pillar's carving)
        if _say:
            self._warp_say = None
            self.say(_say)

    def _ascend(self):
        self._set_zone(self.run.index - 1)
        self.run.ascend()
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.run.player
        self._reset_trail()
        self.banner = 120
        self._floor_sign(True)

    def _canon_changes(self):
        """True in a region with its game's profile (src/vfx/area_changes.py): floors change as that game does."""
        from src.vfx import area_changes
        return bool(area_changes.here_key(self.game))

    def _sign_word(self, floor_too=True):
        """The name on the sign: the place's, and the floor (FireRed's B1F; a zone's own name: the Safari Zone's areas)."""
        _fn = self._floor_name(self.run.index)
        if " / " in _fn and self.zones:
            _fn = self._zone_name(self._zone_index(self.run.index, *self.run.player))
        base = theme.pokemon_word(self.area_data.get("route_name", "") or self.area_key.replace("_", " ").title())
        if self.run.n_floors > 1 and not self.area_data.get("route_name", "").endswith(_fn) and (floor_too or self.zones):
            return f"{base}  {_fn}" if floor_too else f"{base} - {_fn}"
        return base

    def _sign_text(self):
        from src.vfx import area_changes
        return self._sign_word(floor_too=area_changes.here_key(self.game) in ("frlg", "orre"))

    def _floor_sign(self, changed):
        """Up or down a floor, or out of a building: the sign again where this region's game shows it."""
        from src.vfx import area_changes
        got = area_changes.floor_sign(self, self._sign_text, inside=self._indoors(self.run.index), changed=changed)
        if got is not False:
            self.banner = 0
            if got is not None or changed:
                self.sign = got

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
            self.say((self.area_data.get("area_boss") or {}).get("blocked_lines")   # (its own words: the Pokemon Tower's ghost)
                     or [f"A {name} is sound asleep, right in the way!", "It won't budge. Maybe a sound would wake it..."])
            return
        same = [t for t, v in self.run.floor.exits.items() if v == target]
        _hit = getattr(self, "_guide_hit", None)   # (did the Journal's marker point this way? None: there was no marker; 11-21)
        self.game.story_manager._guide_left = (self.area_key, target, None if not _hit else tuple(_hit[0]) in same)
        _to = (self._here_art() or {}).get("edge_to", {}).get("%d,%d" % tuple(self.run.player))
        self.game.arrive_edge = (self.area_key, target, tuple(_to)) if _to else None  # (out by an edge tile: in at its partner there)
        core.ENTRANCE_INDEX = same.index(tuple(self.run.player)) if tuple(self.run.player) in same else 0
        core.ENTRANCE_COUNT = len(same)  # (how many tiles that way out has here: the far side takes the matching place along its own)
        core.ENTRANCE_WATER = None
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

    def _cracked_floor(self, t):
        """A cracked floor (a map's "cracked" {"to": floor below, "tiles": ["x,y"]}, Emerald's Sky Pillar): on foot it crumbles
        under you; on the Bicycle you're over it while you keep riding (Emerald's Mach Bike) - stop on it and it gives
        (update(): _crack_stop). Either way you fall to the floor below, onto the same spot (11-24: riding over every crack
        made Sky Pillar's falls - the way up past 4F - impossible with a Bicycle)."""
        cr = self._here_art().get("cracked") or {}
        if f"{t[0]},{t[1]}" not in set(cr.get("tiles") or ()):
            self._on_crack = None
            return False
        if self._cycling(t):
            self._on_crack = (self.run.index, tuple(t))   # (riding over it: it holds while you keep going)
            return False
        return self._fall_through(t)

    def _crack_stop(self):
        """Riding, stopped on a cracked tile a moment (8 frames: a step on is still riding on): it gives way."""
        oc = getattr(self, "_on_crack", None)
        if not oc or getattr(self, "anim", 0) or self.walk_goal or self.dialogue_box.visible:
            self._crack_wait = 0
            return
        self._crack_wait = getattr(self, "_crack_wait", 0) + 1
        if self._crack_wait < 8:
            return
        self._on_crack, self._crack_wait = None, 0
        if oc == (self.run.index, tuple(self.run.player)):
            self._fall_through(oc[1])

    def _fall_through(self, t):
        cr = self._here_art().get("cracked") or {}
        to = int(cr["to"])
        below = self.run.made(to)
        x, y = min(t[0], below.w - 2), min(t[1], below.h - 2)   # (a smaller floor below: the nearest spot on it)
        self.walk_goal = None
        self.say(["The cracked floor crumbled under your feet!", "You fell through to the floor below!"],
                 then=lambda: self._warp(to, x, y, land=True))
        return True

    def _thin_ice(self, t):
        """Thin ice (a floor's "thin_ice" {"to": floor below, "tiles": ["x,y"]}, FireRed's Icefall Cave 1F): the first step
        cracks it, a second step on the cracked tile drops you to the floor below, onto the same spot (11-17)."""
        ti = self._here_art().get("thin_ice") or {}
        if f"{t[0]},{t[1]}" not in set(ti.get("tiles") or ()):
            return False
        cracked = self.__dict__.setdefault("_ice_cracked", set())
        key = (self.area_key, self.run.index, tuple(t))
        if key not in cracked:
            cracked.add(key)
            self.flash("The thin ice cracked!")
            return False
        cracked.discard(key)
        to, (x, y) = int(ti["to"]), t
        self.walk_goal = None
        self.say(["The thin ice gave way!", "You fell through to the floor below!"], then=lambda: self._warp(to, x, y, land=True))
        return True

    def _hidden_item(self, t):
        """An item hidden on this floor (a map's "hidden" {"x,y": item}, the game's own hidden items): found by stepping on
        its spot, or by walking into it where the spot is solid. Once each."""
        m = self.run.recipe.get("art") or {}
        if m.get("floors"):
            m = m["floors"][self.run.index] if self.run.index < len(m["floors"]) else {}
        item = (m.get("hidden") or {}).get(f"{t[0]},{t[1]}")
        story = self.game.story_manager
        flag = f"hidden_{self.area_key}_{self.run.index}_{t[0]}_{t[1]}"
        if not item or story.story_flags.get(flag):
            return False
        story.story_flags[flag] = True
        if item == "POKE_BALLS":  # (Poke Balls are the one ball count)
            story.balls_left = getattr(story, "balls_left", 0) + 1
        else:
            story.add_item(item)
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.walk_goal = None
        self.say([f"Something was hidden here... You found a {forms.item_label(item).upper()}!"])
        return True

    def _itemfinder(self, here):
        """With the Itemfinder, a hidden item on screen makes it beep (once each visit to the floor)."""
        from src.world import itemfinder
        m = self.run.recipe.get("art") or {}
        if m.get("floors"):
            m = m["floors"][self.run.index] if self.run.index < len(m["floors"]) else {}
        heard = self.__dict__.setdefault("_heard", {}).setdefault(self.run.index, set())
        line = itemfinder.beep(self.game.story_manager, m.get("hidden"), here,
                               lambda x, y: f"hidden_{self.area_key}_{self.run.index}_{x}_{y}", heard)
        if line:
            self.flash(line, 150)

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
        if self.swarm_call(mover):   # (today's swarm here: it calls two friends over, and they battle you on the map)
            return
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
        if getattr(p, "snack_visitor", None):   # (a Poke Spot's snack visitor: caught or gone - Orre batch 8d)
            from src.world import poke_snacks as _snacks
            _snacks.visitor_gone(self.game, p.snack_visitor)
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

    DARK_DOUBLE = 0.1   # (how often a dark-grass meeting is two wild Pokemon: about 1 in 10, Gen 5; an area may set "dark_double_rate")

    def _battle_wild(self, mover):
        from src.states.battle import WildBattleState
        self.pending = ("wild", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        from src.world import walk_partners, hordes
        wp = walk_partners.active(self.game.story_manager, self.area_key)
        if not wp and hordes.roll(self.game, self.area_data):   # (a horde: five at once, ORAS; the area's horde pool and rate)
            horde = hordes.make(self.game, self.area_key, self.area_data)
            if horde:
                from src.states.battle_horde import HordeBattleState
                battle = HordeBattleState(self.game, horde, self.area_key,
                                          background_image=self._get_battle_background_for_area())
                battle.play_state_data = self._play_data()
                pygame.event.clear()
                self.game.change_state(battle)
                return
        if wp:   # (a partner with you: wild Pokemon come two at a time, as in Platinum)
            other = self._make_wild(random.Random(), (mover.x, mover.y))
            if other is not None:
                from src.states.battle_wild_double import WildDoubleBattleState
                battle = WildDoubleBattleState(self.game, [mover.payload, other], self.area_key,
                                               partner=walk_partners.battle_partner(wp),
                                               background_image=self._get_battle_background_for_area())
                battle.play_state_data = self._play_data()
                pygame.event.clear()
                self.game.change_state(battle)
                return
        if (mover.x, mover.y) in self._dark_tiles() and random.random() < float(self.area_data.get("dark_double_rate", self.DARK_DOUBLE)):
            # (dark grass: now and then two wild Pokemon at once, a wild double battle - Gen 5; Unova 11-24. A ball can be
            #  thrown only once one of them is down, as in the games: battle_wild_double.py)
            other = self._make_wild(random.Random(), (mover.x, mover.y))
            if other is not None:
                from src.states.battle_wild_double import WildDoubleBattleState
                battle = WildDoubleBattleState(self.game, [mover.payload, other], self.area_key,
                                               background_image=self._get_battle_background_for_area())
                battle.play_state_data = self._play_data()
                pygame.event.clear()
                self.game.change_state(battle)
                return
        battle = WildBattleState(self.game, mover.payload, self.area_key,
                                 background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        if self._ow_on():  # Options > BATTLE STYLE: OVERWORLD: fought here on the map
            from src.states.overworld.overworld_battle import OverworldView

            def go():
                battle.overworld = OverworldView(self, mover)
                pygame.event.clear()
                self.game.change_state(battle)
            self.ow_walk_to_battle(mover, False, go)   # (over to open ground first, if it stands there: walked)
            return
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

    STORY_CLASSES = ("RIVAL", "ROCKET_LEADER", "GYM_LEADER", "ELITE_FOUR", "CHAMPION")

    @classmethod
    def story_battle(cls, info):
        """An important story battle - a Leader, a villain team's boss, the rival, the Elite Four, the Champion: always on
        the battle screen, whatever the BATTLE STYLE (Jordan 11-24: "the important story battles, as always classic")."""
        info = info if isinstance(info, dict) else {}
        return bool(info.get("is_boss_battle") or info.get("villain") == "leader"
                    or str(info.get("class") or info.get("trainer_class") or "").upper() in cls.STORY_CLASSES)

    def _battle_trainer(self, mover):
        info = mover.payload[1] if isinstance(mover.payload, (list, tuple)) and len(mover.payload) > 1 else {}
        if self._ow_on() and not self.story_battle(info):  # Options > BATTLE STYLE: OVERWORLD (src/states/overworld/overworld_battle.py)
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

    def _phone_check(self):
        """The phone (src/world/phone.py): a number to register after a win; on arriving, a call when a trainer's next team is ready."""
        if hasattr(self, "run"):   # (the radio's March / Lullaby: src/world/radio.py)
            from src.world import radio as _radio
            self.run.radio = _radio.encounter_effect(self.game.story_manager)
        if not self._ready() or self.dialogue_box.visible:
            return
        if getattr(self, "_phone_say", None):
            lines, self._phone_say = self._phone_say, None
            self.say(lines)
            return
        from src.vfx import area_changes as _ac   # (what the old in-between screen said: said here on arrival)
        _said = _ac.take_arrival_lines(self.game, self.area_key)
        if _said:
            self.say(_said)
            return
        if getattr(self, "_phone_area", None) != self.area_key:
            self._phone_area = self.area_key
            from src.world import phone, vs_seeker
            lines = phone.ring(self.game, self.area_key) or vs_seeker.gift(self.game, self.area_key)
            if lines:
                self.say(lines)

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
        from src.world import feats as _feats
        _feats.note(story, "contests")   # (a Feat: Bug-Catching Contests entered)
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
                    _feats.note(story, "contest_wins")   # (a Feat: contests won)
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

    # The VS Seeker as FireRed plays it (11-19, Jordan: "build Vs Seeker screens and animations"): you turn to face us and
    # hold it up (FireRed's own frames: player_extra "vsseeker" / "vsseeker_bike"), then every trainer in view reacts with
    # a speech bubble - "!!" one back for a rematch (they step out as it pops), "!" one you haven't beaten, "X" one beaten
    # who won't battle again yet - and then the message. Nothing else moves while it plays.
    VS_RAISE = [0, 4, 5, 6, 7, 8]          # (FireRed's walking pose: still, then the device out and up; each 100 ms)
    VS_RAISE_BIKE = [0, 2, 3, 4, 5, 5]     # (on the Bicycle)
    VS_POP, VS_HOLD = 600, 1300            # (the bubbles pop when it's up; then they stay a moment before the message)

    def use_vs_seeker(self):
        """The VS Seeker used here (from the Bag or its button): some trainers you beat today in view come back."""
        from src.world import vs_seeker
        res = vs_seeker.seek(self)
        if not res.get("charged"):
            self.say(res["lines"])
            return
        for m in res["rematch"]:
            m._vs_hidden = True   # (they step out as the bubbles pop)
        self.facing = (0, 1)
        self._vs_anim = {"t": pygame.time.get_ticks(), "res": res, "popped": False,
                         "bike": bool(hasattr(self, "run") and self._cycling())}

    def _vs_tick(self):
        a = getattr(self, "_vs_anim", None)
        if not a:
            return
        t = pygame.time.get_ticks() - a["t"]
        if t >= self.VS_POP and not a["popped"]:
            a["popped"] = True
            for m in a["res"]["rematch"]:
                m._vs_hidden = False
            snd = getattr(self.game.assets, "alert_sfx", None)
            if snd is not None and (a["res"]["rematch"] or a["res"]["seen"]):
                try:
                    snd.play()
                except Exception:
                    pass
        if t >= self.VS_POP + self.VS_HOLD:
            self._vs_anim = None
            self.say(a["res"]["lines"])

    def _vs_pose(self):
        """Your VS Seeker frame while it plays (None without the sheet: you just face us)."""
        a = getattr(self, "_vs_anim", None)
        if not a:
            return None
        seq = self.VS_RAISE_BIKE if a["bike"] else self.VS_RAISE
        k = min(len(seq) - 1, (pygame.time.get_ticks() - a["t"]) // 100)
        return self._extra_frame("vsseeker_bike" if a["bike"] else "vsseeker", (0, 1), seq[k]) \
            or (self._extra_frame("vsseeker", (0, 1), self.VS_RAISE[k]) if a["bike"] else None)

    def _vs_bubbles(self):
        """{mover: kind} with a bubble over them now: "!!", "!", "X"."""
        a = getattr(self, "_vs_anim", None)
        if not a or not a["popped"]:
            return {}
        out = {m: "!!" for m in a["res"]["rematch"]}
        out.update({m: k for m, k in a["res"]["seen"]})
        return out

    def _draw_vs_bubble(self, screen, r, kind):
        """FireRed's emote bubble over someone: white, black-edged, a little tail, the mark inside; it pops up."""
        a = getattr(self, "_vs_anim", None)
        age = pygame.time.get_ticks() - a["t"] - self.VS_POP if a else 999
        px = 3   # (one of the bubble's pixels on screen)
        pop = min(1.0, 0.45 + age / 220)
        w, h = int(12 * px * pop), int(11 * px * pop)
        if w < 6:
            return
        bob = -2 if (age // 180) % 2 else 0
        box = pygame.Rect(0, 0, w, h)
        box.midbottom = (r.centerx + px * 2, r.y - px * 2 + bob)
        pygame.draw.rect(screen, (24, 24, 24), box.inflate(px * 2, px * 2), border_radius=px * 2)
        pygame.draw.rect(screen, (250, 250, 250), box, border_radius=px * 2)
        tail = [(box.x + px * 2, box.bottom - 1), (box.x + px * 5, box.bottom - 1), (box.x + px * 2, box.bottom + px * 3)]
        pygame.draw.polygon(screen, (24, 24, 24), [(tail[0][0] - px, tail[0][1]), (tail[1][0] + px, tail[1][1]), (tail[2][0] - px, tail[2][1] + px)])
        pygame.draw.polygon(screen, (250, 250, 250), tail)
        if pop < 1.0:
            return
        ink = (200, 40, 40) if kind == "!!" else (24, 24, 24)
        cx, top = box.centerx, box.y + px * 2
        if kind == "X":
            pygame.draw.line(screen, ink, (cx - px * 2, top), (cx + px * 2, top + px * 6), px + 1)
            pygame.draw.line(screen, ink, (cx + px * 2, top), (cx - px * 2, top + px * 6), px + 1)
            return
        for dx in ((-px * 2, px * 2) if kind == "!!" else (0,)):
            pygame.draw.rect(screen, ink, (cx + dx - px // 2 - 1, top, px + 1, px * 4))
            pygame.draw.rect(screen, ink, (cx + dx - px // 2 - 1, top + px * 5, px + 1, px + 1))

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

        def catch(picked=None):
            self.route_bg = None   # (the live map under the catch screen: _draw_catch_layer)
            self.mode = "CATCH"
            for b in self.hud_buttons:   # (only the catch screen takes taps while it's up)
                b.set_visibility(False)
            self.is_progression_paused = False
            self.pending_wild_encounters = 0
            self.input_delay = 20
            self._preset_catch = picked
            self.trigger_wild_encounter()  # the route's three-Pokemon catch, then show_progression_menu

        def begin():
            picked = self.pick_catch_three() if catching.total_balls(story) > 0 else None
            if not picked or not any(picked[1]):
                catch()
                return
            self.walkup_start([p for p in picked[1] if p is not None], lambda: catch(picked))   # (they walk up first)
            self._wu["kind"] = "catch"
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
        elif hasattr(self, "run") and self._vs_button():   # (the VS Seeker registered, as FireRed's Select button: 11-19)
            from src.world import vs_seeker as _vsb
            n = _vsb.charge(self.game.story_manager)
            buttons.append((side[4], "VS SEEKER", (200, 70, 60), self.use_vs_seeker, n >= _vsb.CHARGE,
                            "ready" if n >= _vsb.CHARGE else f"{_vsb.CHARGE - n} steps"))
        elif hasattr(self, "run") and self._radar_ready():   # (the Poke Radar, in tall grass: Platinum's)
            from src.world import poke_radar as _radar
            n = _radar.charge(self.game.story_manager)
            buttons.append((side[4], "RADAR", (90, 170, 80), self.use_radar, n >= _radar.CHARGE,
                            "ready" if n >= _radar.CHARGE else f"{_radar.CHARGE - n} steps"))
        return buttons

    def _vs_button(self):
        """The VS SEEKER button: you have it, here has trainers, and the Poke Radar doesn't want that spot."""
        from src.world import vs_seeker as _vsb
        story = self.game.story_manager
        return (_vsb.has(story) and not self.contest and bool(self.area_data.get("trainer_pool"))
                and not getattr(self, "_vs_anim", None) and not self._radar_ready())

    def _radar_ready(self):
        from src.world import poke_radar as _radar
        from src.dungeon import core as _core
        story = self.game.story_manager
        return (_radar.owned(story) and not self.contest and self.run.floor.tile(*self.run.player) == _core.GRASS
                and not (getattr(self, "_radar", None) or {}).get("patches"))

    def use_radar(self):
        """The Poke Radar (the Bag or the RADAR button): four patches of grass nearby shake (src/world/poke_radar.py)."""
        if not self._ready():
            return
        from src.world import poke_radar as _radar
        said = _radar.shake(self)
        if said:
            self.say(said)

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
        if getattr(self, "_cam_focus", None):   # (a scene looking somewhere else: 5.7's camera pans)
            px, py = self._cam_focus
        elif self.anim > 0:
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
            top = 0
            _zone = None if (focus or getattr(self, "_cam_focus", None)) else self._cam_zone(px, py)
            if _zone:   # (a strip where Black 2's camera moves as you cross it: the view slides with you)
                cx, cy = cx + _zone[1][0] * TILE, cy + _zone[1][1] * TILE
            c3 = getattr(self, "cam3d", None)
            if c3 and not focus:   # (B2W2's camera: the view follows you up and down the stairs, and shows the raised ground)
                cy -= c3.lift(px, py) * TILE
                top, mh = c3.span()
            cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
            if focus:   # (a battle on the map: only the part above its text box shows, so the map's foot may come up to
                #  the box's top - a fight at a map's bottom edge was drawn under the box; Jordan 11-24)
                band = Utils.get_full_dialogue_rect(self.game).top - self._view().top
                lo, hi = top + H / 2, mh - H / 2 + (H - band)
                cy = (top + mh) / 2 + (H - band) / 2 if mh - top <= band else min(max(cy, lo), hi)
            else:
                cy = (top + mh) / 2 if mh - top <= H else min(max(cy, top + H / 2), mh - H / 2)
        ease = getattr(self, "_cam_ease", None)
        if ease is not None:   # (a scene's pan: the view glides there and back)
            return ease
        return cx, cy

    def _cam_tick(self):
        """Once a frame (as the towns' walk_town.WalkTownState._cam_tick): a scene's pan glides, the zoom eases."""
        now = pygame.time.get_ticks()
        if getattr(self, "_cam_focus", None) or now < getattr(self, "_cam_ease_until", 0):
            self._cam_ease = None
            goal = self._camera()
            cur = getattr(self, "_cam_cur", None) or goal
            cur = (cur[0] + (goal[0] - cur[0]) * 0.12, cur[1] + (goal[1] - cur[1]) * 0.12)
            if abs(cur[0] - goal[0]) < 1 and abs(cur[1] - goal[1]) < 1 and not getattr(self, "_cam_focus", None):
                self._cam_ease_until = 0
            self._cam_ease = self._cam_cur = cur
        else:
            self._cam_ease = None
            self._cam_cur = self._camera()
        want = getattr(self, "_scene_zoom", None) or self._zoom_goal()
        z = getattr(self, "zoom", 1.0)
        self.zoom = want if abs(want - z) < 0.004 else z + (want - z) * 0.1

    def _zoom_goal(self):
        """The map's own zoom ("camera_zoom"), or a camera zone's where you stand ("cameras" [{"rect", "zoom"}])."""
        m = (self.run.recipe.get("art") or {}) if hasattr(self, "run") else {}
        if self._backdrop or self.mode == "CATCH":
            return 1.0
        px, py = self.run.player
        if self.anim > 0:
            k = 1 - self.anim / STEP_FRAMES
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        _zone = self._cam_zone(px, py)
        return _zone[0] if _zone else float(m.get("camera_zoom") or 1.0)

    def _cam_zone(self, fx, fy):
        """(zoom, pan) of the map's camera zone at (fx, fy), else None (camera3d.camera_zone)."""
        m = (self.run.recipe.get("art") or {}) if hasattr(self, "run") else {}
        from src.dungeon import camera3d as _c3
        return _c3.camera_zone(m.get("cameras"), fx, fy)

    def npc_zoom(self, z):
        """A scene moves the camera in or out (None or 1: back to the map's)."""
        self._scene_zoom = float(z) if z and float(z) != 1.0 else None

    def _view(self):
        """Where the map is drawn: the frame (the whole screen under an OVERWORLD-style battle)."""
        if getattr(self, "_view_override", None) is not None:   # (drawing zoomed: the smaller picture scaled into the frame)
            return self._view_override
        if self._backdrop:
            return self.game.screen.get_rect()
        return map_view(self.game)

    def _origin(self):
        cx, cy = self._camera()
        v = self._view()
        return int(v.centerx - cx) + shake_dx(self), int(v.centery - cy)

    def _tile_at(self, pos):
        if self._dl_live():   # (the live camera: the tile under the finger, on the ground where you stand)
            return self._dl_tile_at(pos)
        z = getattr(self, "zoom", 1.0)
        if abs(z - 1.0) > 0.01:   # (zoomed: the point in the map's own picture first)
            v = self._view()
            self._view_override = pygame.Rect(0, 0, round(v.w / z), round(v.h / z))
            try:
                ox, oy = self._origin()
            finally:
                self._view_override = None
            pos = ((pos[0] - v.x) / z, (pos[1] - v.y) / z)
        else:
            ox, oy = self._origin()
        ox -= shake_dx(self)
        if getattr(self, "cam3d", None):   # (raised ground is drawn higher: the tile whose lifted square is under the finger)
            return self.cam3d.tile_at(pos[0] - ox, pos[1] - oy)
        return int((pos[0] - ox) // TILE), int((pos[1] - oy) // TILE)

    KEYS = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}

    def handle_events(self, events):
        if self.mode == "CATCH":
            return super().handle_events(events)
        if getattr(self, "_walker", None) and (not self._walker.get("spoke") or self._walker.get("leaving")):  # (someone is walking up to you, or off again: wait for them)
            return
        if getattr(self, "_vs_anim", None):   # (the VS Seeker is playing: wait for it)
            return
        if self.mode not in ("WALKUP", "SWARM", "OWWALK"):   # (not while wild ones walk up to you, battle you on the map, or you walk to a battle)
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
            elif self.mode == "SWARM":
                self._sw_event(e)

    def _map_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in self.KEYS:
                self.walk_goal = None
                self.step(*self.KEYS[e.key])
            elif e.key in (pygame.K_PERIOD, pygame.K_z):
                self.wait_turn()
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_f):
                _cw = self._companion_at((self.run.player[0] + self.facing[0], self.run.player[1] + self.facing[1]))
                if _cw:
                    self._talk_companion(_cw)
                    return
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
        if u.get("item_condition") and not __import__("src.world.hms", fromlist=["field"]).field(story, u["item_condition"]):
            return False
        if u.get("area_cleared"):  # (every trainer of another area beaten: the Meadow's grunts, for the Works Key)
            pool = (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(u["area_cleared"]) or {}).get("trainer_pool") or []
            if len(story.defeated_trainers.get(u["area_cleared"], set())) < len(pool):
                return False
        if u.get("trainers_beaten"):  # (Mt. Battle: the way up opens once this area's trainers - the ones here now - are all beaten;
            pre, flags = str(u["trainers_beaten"]), story.story_flags   #  by their spot names, "Area 3 ", so starting over shuts it again)
            for i, t in enumerate(self.area_data.get("trainer_pool", [])):
                if not str(t.get("spot_name") or t.get("name") or "").startswith(pre):
                    continue
                if any(not flags.get(f) for f in t.get("when_flags") or []) or any(flags.get(f) for f in t.get("gone_flags") or []):
                    continue
                if not story.is_trainer_defeated(self.area_key, i):
                    return False
        cond = u.get("condition")
        return all(self._check_route_condition(c, False, u) for c in (cond if isinstance(cond, list) else [cond] if cond else []))

    def _switches(self):
        """This floor's "boulder_switches": [{"on": [x, y] the switch, "boulders": [[x, y], ...] the ones that can reach it
        (the source game's), "flag": set once one is on it, "lines"}] (FireRed's Victory Road: each holds a rock barrier down)."""
        m = self.run.recipe.get("art") or {}
        here = m["floors"][self.run.index] if m.get("floors") and self.run.index < len(m["floors"]) else m
        return here.get("boulder_switches") or []

    def _switch_for(self, t):
        """The switch a boulder at t rolls onto when pushed (one still empty), else None."""
        flags = self.game.story_manager.story_flags
        return next((sw for sw in self._switches() if not flags.get(sw["flag"])
                     and any(tuple(b) == tuple(t) for b in sw.get("boulders", []))), None)

    def _clear_boulders(self):
        """Boulders pushed aside stay out of the way (a story flag each)."""
        f = self.run.floor
        flags = self.game.story_manager.story_flags
        self._place_boxes()
        for sw in self._switches():   # (a boulder sitting on its switch)
            t = tuple(sw["on"])
            if flags.get(sw["flag"]) and t not in f.decor:
                f.decor[t] = f"pressed:{t[0]},{t[1]}"
                f.tiles[t[1]][t[0]] = core.WALL
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
            elif str(what).startswith("falls:") and __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_WATERFALL"):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.SURF  # (you climb it: water you Surf up)
            elif str(what).startswith("cut:") and __import__("src.world.hms", fromlist=["usable"]).usable(self.game.story_manager, "HM_CUT"):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (your Pokemon cuts it down)
            elif str(what).startswith("slope:") and self.game.story_manager.inventory.get("BICYCLE", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you ride up it)
            elif str(what).startswith("stones:") and self.game.story_manager.inventory.get("BICYCLE", 0) > 0:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you hop across them on the Bicycle: the Jagged Pass's round stones)
                self.__dict__.setdefault("_stones", set()).add(t)
            elif str(what).startswith("crack:") and __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_ROCK_SMASH") \
                    and not (self.run.recipe.get("art") or {}).get("smash_wild"):   # (Soaring's Mirage spots: broken one at a time)
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (your Pokemon breaks it)
            elif str(what).startswith("climb:") and (self.game.story_manager.inventory.get("HM_ROCK_CLIMB", 0) > 0
                                                     or self.game.story_manager.inventory.get("CLIMB_KIT", 0) > 0):   # (Orange 5.7's Climb Kit: the same walls, 11-17)
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR  # (you scale it)
            elif str(what).startswith("whirl:") and flags.get(self._boulder_flag(t)):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.SURF  # (open water now)
                self._floor_surf = None

    def _whirl_pull(self, dx, dy):
        """On a flowing whirlpool's tile (the map's "whirl": Orange 5.7's, ogen.py) with the Whirlpuller: True, and you're
        carried on the way you came, through the whirlpool and off its far side (5.7's Whirlpuller: through a row of them)."""
        m = self.run.recipe.get("art") or {}
        if m.get("floors"):
            m = m["floors"][self.run.index]
        wh = {tuple(t) for t in m.get("whirl") or ()}
        p = tuple(self.run.player)
        if p not in wh or self.game.story_manager.inventory.get("WHIRLPULLER", 0) <= 0:
            return False
        if (p[0] - dx, p[1] - dy) not in wh:
            self.flash("The Whirlpuller pulls you through the whirlpool!", 60)
        self.sliding = (dx, dy)
        return True

    def _whirlpool(self, t):
        """Walked into a whirlpool (Jordan, 11-09): it bars the way until you clear it with Whirlpool."""
        story = self.game.story_manager
        if story.inventory.get("HM_WHIRLPOOL", 0) <= 0 and story.inventory.get("WHIRLPULLER", 0) <= 0:   # (Orange 5.7's Whirlpuller does it too, 11-17)
            self.say(["A fierce whirlpool blocks the way!", "A Pokemon that knows Whirlpool could calm it."
                      if self.area_data.get("region") != "ORANGE" else "A Whirlpuller would get you across it."])
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

    # ---------------------------------------------------------------- crates you push (XD's Cipher Key Lair, Jordan 11-21)
    # A floor's "boxes": [[x, y], ...] where its crates start; walk into one and it slides a tile ahead, if the tile beyond
    # is plain open floor. Where they stand is kept (story flag boxes_<area>_<floor>: a list), so a solved room stays
    # solved; "clear_flags" on that flag (the room's reset panel) puts them back. "box_switches": [{"on": [x, y], "flag",
    # "lines"}]: a crate pushed onto the switch sets its flag for good (the moon door's "barred" until it).
    def _box_key(self):
        return f"boxes_{self.area_key}_{self.run.index}"

    def _box_spots(self):
        start = [list(t) for t in (self._here_art().get("boxes") or [])]
        now = self.game.story_manager.story_flags.get(self._box_key())
        return [tuple(t) for t in (now if isinstance(now, list) and len(now) == len(start) else start)]

    def _box_shown(self, i):
        """A crate standing on the floor now: not pushed off out of sight ("gone": [-1, -1]), and its floor's "box_when" /
        "box_unless" (a flag per crate, or null) as the story stands - Platinum's Distortion World boulders: on B5F till you
        push them off their slab, on B6F once they've fallen there (Sinnoh 11-24)."""
        art, flags = self._here_art(), self.game.story_manager.story_flags
        spots = self._box_spots()
        if i >= len(spots) or tuple(spots[i]) == (-1, -1):
            return False
        w = (art.get("box_when") or [])[i:i + 1]
        u = (art.get("box_unless") or [])[i:i + 1]
        return (not w or not w[0] or bool(flags.get(w[0]))) and (not u or not u[0] or not flags.get(u[0]))

    def _place_boxes(self):
        """Put this floor's crates where they stand now (and free the tiles they've left)."""
        self._place_stones()
        if not self._here_art().get("boxes"):
            return
        f = self.run.floor
        spots = {t for i, t in enumerate(self._box_spots()) if self._box_shown(i)}
        into = {tuple(sw["on"]) for sw in (self._here_art().get("box_switches") or []) if sw.get("into")}   # (a pit: void again once empty)
        for t, what in list(f.decor.items()):
            if str(what).startswith("box:") and t not in spots:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.WALL if t in into else core.FLOOR
        for t in spots:
            if t not in f.decor:
                f.decor[t] = f"box:{t[0]},{t[1]}"
                f.tiles[t[1]][t[0]] = core.WALL

    # ---------------------------------------------------------------- stones you push (Black 2's Chargestone Cave; Unova 11-24)
    # A floor's "stones": [[x, y] or [x, y, model], ...] - each the middle of a 3 x 3 block of rock (its picture the map's
    # "stone_model", e.g. "b2:195_110_0", drawn at the middle). Walk into a stone's edge and the whole block slides that way
    # till the next row it would cover isn't open floor (or holds a person, an item, a way out). Where they stand is kept
    # (story flag stones_<area>_<floor>), as the crates are.
    def _stone_key(self):
        return f"stones_{self.area_key}_{self.run.index}"

    def _stone_start(self):
        return [(int(s[0]), int(s[1])) for s in (self._here_art().get("stones") or [])]

    def _stone_spots(self):
        start = self._stone_start()
        now = self.game.story_manager.story_flags.get(self._stone_key())
        return [tuple(t) for t in now] if isinstance(now, list) and len(now) == len(start) else start

    def _stone_model(self, i):
        s = (self._here_art().get("stones") or [])[i]
        return s[2] if len(s) > 2 else self._here_art().get("stone_model")

    def _place_stones(self):
        """Put this floor's stones where they stand now: their 3 x 3 rock, and open floor where they've left."""
        if not self._here_art().get("stones"):
            return
        f = self.run.floor
        cover = {}
        for i, (cx, cy) in enumerate(self._stone_spots()):
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    cover[(cx + a, cy + b)] = f"stone:{i}:{cx},{cy}"

        def inside(t):
            return 0 <= t[0] < f.w and 0 <= t[1] < f.h
        for t, what in list(f.decor.items()):
            if str(what).startswith("stone:") and t not in cover:
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR
        for cx, cy in self._stone_start():   # (where a stone stood in the game's grid, rock: open floor once it has moved)
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    t = (cx + a, cy + b)
                    if inside(t) and t not in cover and t not in f.decor and f.tile(*t) == core.WALL:
                        f.tiles[t[1]][t[0]] = core.FLOOR
        for t, what in cover.items():
            if inside(t):
                f.decor[t] = what
                f.tiles[t[1]][t[0]] = core.WALL

    def _push_stone(self, i, dx, dy):
        """Walked into a stone: it slides that way till something stops it. False if it can't move at all."""
        f = self.run.floor
        story = self.game.story_manager
        art = self._here_art()
        links = {tuple(int(v) for v in k.split(",")) for k in (art.get("links") or {})}
        spots = self._stone_spots()
        cx, cy = spots[i]
        mine = {(cx + a, cy + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        moved = 0
        while moved < 200:
            ahead = {(x + dx, y + dy) for x, y in mine} - mine
            if any(not (0 <= x < f.w and 0 <= y < f.h) or f.tile(x, y) != core.FLOOR or (x, y) in f.decor or f.mover_at(x, y)
                   or (x, y) == tuple(self.run.player) or (x, y) in f.exits or (x, y) in f.items or (x, y) in f.tm_spots
                   or (x, y) in links for x, y in ahead):
                break
            mine = {(x + dx, y + dy) for x, y in mine}
            cx, cy = cx + dx, cy + dy
            moved += 1
        if not moved:
            self.flash("It won't budge.")
            return False
        spots[i] = (cx, cy)
        story.story_flags[self._stone_key()] = [list(u) for u in spots]
        self._place_stones()
        self._floor_surf = None
        self._over_key = None
        return True

    def _draw_stone(self, screen, i, r):
        """A stone's picture at its middle tile r (the game's own model, else a drawn glowing rock)."""
        key = self._stone_model(i)
        from src.dungeon import art as _art
        got = _art._model(key) if key else None
        if got:
            mp, ox, oy = got
            cache = self.__dict__.setdefault("_stone_imgs", {})
            ck = (key, TILE)
            if ck not in cache:
                cache[ck] = mp if TILE == 32 else pygame.transform.scale(mp, (max(1, mp.get_width() * TILE // 32), max(1, mp.get_height() * TILE // 32)))
            screen.blit(cache[ck], (int(r.x + TILE / 2 - ox * TILE / 32), int(r.y + TILE / 2 - oy * TILE / 32)))
        else:
            box = r.inflate(TILE * 2 - 6, TILE * 2 - 6)
            pygame.draw.ellipse(screen, (70, 90, 150), box)
            pygame.draw.ellipse(screen, (150, 200, 255), box.inflate(-TILE, -TILE))
            pygame.draw.ellipse(screen, (30, 40, 80), box, 3)

    def _push_box(self, t, dx, dy):
        """Walked into a crate: it slides one tile on, if that tile is open floor with nothing on it. A floor's "box_look":
        "boulder" draws them as Strength boulders and "box_strength" asks for Strength (Platinum's Distortion World). A
        switch with "into": true is a pit or a drop the crate is pushed into although it isn't floor; "gone": true, it
        drops out of sight there; "reset": {"clear": [flags], "boxes": [[floor, i], ...]}: a wrong pit - the flags cleared and
        those crates (this one too) put back where they started, with its "lines" (Sinnoh 11-24)."""
        f = self.run.floor
        story = self.game.story_manager
        to = (t[0] + dx, t[1] + dy)
        art = self._here_art()
        if art.get("box_strength") and not __import__("src.world.hms", fromlist=["field"]).field(story, "HM_STRENGTH"):
            self.say(["A huge boulder. A Pokemon that knows Strength could push it!"])
            return False
        sws = [sw for sw in art.get("box_switches") or [] if tuple(sw["on"]) == to]
        pit = any(sw.get("into") for sw in sws)
        links = {tuple(int(v) for v in k.split(",")) for k in (art.get("links") or {})}
        blocked_here = to in f.decor and not (pit and not str(f.decor[to]).startswith("box:"))
        if not (0 <= to[0] < f.w and 0 <= to[1] < f.h) or (f.tile(*to) != core.FLOOR and not pit) or blocked_here \
                or f.mover_at(*to) or to in f.exits or to in f.items or to in f.tm_spots or to in links:
            self.flash("It won't budge any further that way.")
            return False
        spots = self._box_spots()
        i = spots.index(tuple(t))
        spots[i] = to
        story.story_flags[self._box_key()] = [list(u) for u in spots]
        if pit:
            f.decor.pop(to, None)
        for sw in sws:
            if sw.get("reset"):   # (a wrong pit: the boulder falls away, back where it started)
                rs = sw["reset"]
                for fl in rs.get("clear") or []:
                    story.story_flags.pop(fl, None)
                floors = (self.recipe.get("art") or {}).get("floors") or []
                for fi, bi in [[self.run.index, i]] + [list(b) for b in rs.get("boxes") or []]:
                    key = f"boxes_{self.area_key}_{fi}"
                    start = [list(u) for u in ((floors[fi] if fi < len(floors) else {}).get("boxes") or [])]
                    now = story.story_flags.get(key)
                    now = [list(u) for u in now] if isinstance(now, list) and len(now) == len(start) else [list(u) for u in start]
                    if bi < len(start):
                        now[bi] = start[bi]
                    story.story_flags[key] = now
                self._place_boxes()
                self.say(sw.get("lines") or ["The boulder dropped into the pit... and fell away below!"])
                return True
            if sw.get("gone"):   # (pushed off the edge: out of sight)
                spots[i] = (-1, -1)
                story.story_flags[self._box_key()] = [list(u) for u in spots]
        self._place_boxes()
        for sw in sws:
            if not story.story_flags.get(sw["flag"]):
                story.story_flags[sw["flag"]] = True
                self._clear_boulders()
                self._floor_surf = None
                self._over_key = None
                self.say(sw.get("lines") or ["The crate pressed the floor switch down.", "Something opened somewhere!"])
        return True

    # ---------------------------------------------------------------- rides: platforms, hooks, drops (Citadark Isle, Jordan 11-21)
    # A floor's "platforms": [{"track": [[x, y], ...]}] - tiles over lava; the platform waits at one end; walk into either end
    # and it carries you along to the other, where you step off onto the ground beside it. "hooks": [{"colour", "a": [x, y],
    # "b": [x, y]}] - two pads across a pit; walk onto one and the hook lifts you over to the other. "warps": [{"at", "to",
    # "kind": "drop" | "lift", "lines"}] - a glowing tile you drop through, or a lift, to another spot on the same floor.
    HOOK_COLOURS = {"yellow": (240, 210, 60), "pink": (240, 130, 190), "red": (220, 70, 60), "orange": (240, 150, 50),
                    "cyan": (80, 210, 230)}

    def _rides(self, key):
        return self._here_art().get(key) or []

    def _ride_art(self, name, w, h):
        """Ride art from the fan sheets (assets/tiles/orre_ride, Jordan 11-21): platform.png (Orre Mt. Battle's square lift),
        pad_<colour>.png (Orre's coloured warp pads), hook.png (the Sinnoh crane's hook). None if missing: shapes are drawn."""
        cache = self.__dict__.setdefault("_ride_art_cache", {})
        key = (name, int(w), int(h))
        if key not in cache:
            img = None
            try:
                import os
                path = os.path.join(self.game.assets.assets_dir, "tiles", "orre_ride", name)
                if os.path.exists(path):
                    img = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (int(w), int(h)))
            except Exception:
                img = None
            cache[key] = img
        return cache[key]

    def _platform_at(self):
        return self.__dict__.setdefault("_platform_end", {})

    def _board_platform(self, to):
        for i, pl in enumerate(self._rides("platforms")):
            track = [tuple(t) for t in pl["track"]]
            if to not in (track[0], track[-1]) or tuple(self.run.player) in track:
                continue
            path = track if to == track[0] else track[::-1]
            far = path[-1]
            f = self.run.floor
            off = next(((far[0] + dx, far[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if (far[0] + dx, far[1] + dy) not in track and f.walkable(far[0] + dx, far[1] + dy)), None)
            if off is None:
                return False
            self.walk_goal = None
            self._ride = {"kind": "platform", "path": path + [off], "id": i, "end": 1 if to == track[0] else 0}
            return True
        return False

    def _ride_from_tile(self, t):
        if getattr(self, "_ride", None):
            return
        for hk in self._rides("hooks"):
            a, b = tuple(hk["a"]), tuple(hk["b"])
            if t in (a, b):
                other = b if t == a else a
                dx = (other[0] > t[0]) - (other[0] < t[0])
                dy = (other[1] > t[1]) - (other[1] < t[1])
                path, c = [], t
                while c != other:
                    c = (c[0] + dx, c[1] + dy)
                    path.append(c)
                self.walk_goal = None
                self._ride = {"kind": "hook", "path": path, "colour": hk.get("colour", "yellow")}
                return
        for w in self._rides("warps"):
            if tuple(w["at"]) == t:
                self.walk_goal = None
                self._ride = {"kind": w.get("kind", "drop"), "path": [tuple(w["to"])], "lines": w.get("lines")}
                return

    def _ride_step(self):
        r = self._ride
        if not r["path"]:
            self._ride = None
            if r["kind"] == "platform":
                self._platform_at()[r["id"]] = r["end"]
            self._reset_trail()
            self.partner = self.partner_from = self.run.player
            if r.get("lines"):
                self.say(r["lines"])
            return
        nxt = r["path"].pop(0)
        if r["kind"] in ("drop", "lift"):   # (you fall through, or the lift takes you: no walking between)
            if r["kind"] == "drop" and hasattr(self, "shake"):
                self.shake(300)
            self.run.player = nxt
            self.anim_from, self.anim = nxt, 0
            self.run.floor.seen.add(nxt)
            return
        self.anim_from = tuple(self.run.player)
        self.run.player = nxt
        self.anim = STEP_FRAMES
        if r["kind"] == "platform" and not r["path"]:
            r["carried"] = True

    def _draw_rides(self, screen, at, late=False):
        """The hook pads and the glowing drop tiles (late=False); the platforms, where they wait or under you as they carry you
        (late=True: after the map's top layer, whose lava would hide them - the player is drawn again over them after)."""
        f = self.run.floor
        if late:
            return self._draw_platforms(screen, at)
        r = getattr(self, "_ride", None)
        t = pygame.time.get_ticks()
        for hk in self._rides("hooks"):
            col = self.HOOK_COLOURS.get(hk.get("colour"), (200, 200, 200))
            for pad in (hk["a"], hk["b"]):
                if tuple(pad) in f.seen:
                    rr = at(*pad)
                    art = self._ride_art(f"pad_{hk.get('colour', 'yellow')}.png", rr.w, rr.h)
                    if art is not None:   # (Orre's own coloured warp pads)
                        screen.blit(art, rr)
                        continue
                    rr = rr.inflate(-8, -8)
                    pygame.draw.rect(screen, (60, 62, 72), rr, border_radius=5)
                    pygame.draw.rect(screen, col, rr, 3, border_radius=5)
        for w in self._rides("warps"):
            if w.get("kind", "drop") == "drop" and tuple(w["at"]) in f.seen:
                rr = at(*w["at"])
                glow = pygame.Surface(rr.size, pygame.SRCALPHA)
                a = 110 + int(70 * math.sin(t / 220))
                pygame.draw.rect(glow, (90, 200, 255, max(0, min(255, a))), glow.get_rect().inflate(-4, -4), border_radius=6)
                screen.blit(glow, rr)

        if r and r["kind"] == "hook":
            k = 1 - self.anim / STEP_FRAMES if self.anim else 1
            fx, fy = self.anim_from
            px, py = self.run.player
            o = at(0, 0)
            cx = (fx + (px - fx) * k) * TILE + TILE / 2 + o.x
            cy = (fy + (py - fy) * k) * TILE + TILE / 2 + o.y
            col = self.HOOK_COLOURS.get(r.get("colour"), (200, 200, 200))
            hook = self._ride_art("hook.png", TILE, TILE * 3)
            if hook is not None:   # (the Sinnoh crane's hook and its striped cable, the hook at your shoulders; cable on up)
                top = int(cy) - TILE // 3 - hook.get_height()
                pygame.draw.line(screen, (40, 40, 46), (int(cx), 0), (int(cx), max(0, top + TILE // 2)), 3)
                screen.blit(hook, (int(cx) - TILE * 7 // 8, top))   # (the crop's hook hangs at its right edge, 24-32 px of 32)
            else:
                pygame.draw.line(screen, (40, 40, 46), (int(cx), 0), (int(cx), int(cy) - TILE // 2), 3)
                pygame.draw.circle(screen, col, (int(cx), int(cy) - TILE // 2), 6, 3)

    def _draw_platforms(self, screen, at):
        r = getattr(self, "_ride", None)

        def plate(px, py):
            art = self._ride_art("platform.png", TILE, TILE * 3 // 2)
            if art is not None:   # (Orre Mt. Battle's square lift: its deck under your feet, its underside hanging below)
                screen.blit(art, (int(px) - TILE // 2, int(py) - TILE // 2 + 2))
                return
            rr = pygame.Rect(0, 0, TILE - 4, TILE - 10)
            rr.center = (int(px), int(py) + 6)
            pygame.draw.rect(screen, (96, 100, 112), rr, border_radius=4)
            pygame.draw.rect(screen, (170, 176, 190), rr, 2, border_radius=4)
            pygame.draw.line(screen, (60, 62, 72), (rr.left + 4, rr.bottom - 3), (rr.right - 4, rr.bottom - 3), 2)

        riding_pl = r["id"] if r and r["kind"] == "platform" and not r.get("carried") else None
        for i, pl in enumerate(self._rides("platforms")):
            if i == riding_pl:
                continue
            end = self._platform_at().get(i, 0)
            rr = at(*pl["track"][-1 if end else 0])
            plate(rr.centerx, rr.centery)
        if r and r["kind"] == "platform" and not r.get("carried"):
            k = 1 - self.anim / STEP_FRAMES if self.anim else 1
            fx, fy = self.anim_from
            px, py = self.run.player
            o = at(0, 0)
            plate((fx + (px - fx) * k) * TILE + TILE / 2 + o.x, (fy + (py - fy) * k) * TILE + TILE / 2 + o.y)

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
        if not __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_STRENGTH"):
            _b = __import__("src.world.hms", fromlist=["badge_wanted"]).badge_wanted(story, "HM_STRENGTH")   # (you carry the HM: it's the badge that's missing)
            self.say(["A huge boulder is in the way.", f"Strength can't be used here without the {_b} Badge." if _b else "A Pokemon that knows Strength could push it!"])
            return
        from src.states.slide_puzzle import SlidePuzzleState

        def done(solved):
            self.is_resuming = True
            self.game.change_state(self)
            if solved:
                story.story_flags[self._boulder_flag(t)] = True
                self._pose_start("field")   # (your own field-move pose through "used Strength!", if you have one: Orange 5.7's Ash)
                sw = self._switch_for(t)
                if sw:   # (it rolls onto its floor switch: Victory Road's, and the rock barrier it holds up drops)
                    story.story_flags[sw["flag"]] = True
                self._clear_boulders()
                if sw:
                    self._floor_surf = None
                    self._over_key = None   # (the floor's picture: the barrier gone)
                    self.say(sw.get("lines") or ["Your Pokemon used Strength!", "The boulder rolled onto the floor switch!",
                                                 "Click! Somewhere, a rock barrier sank into the ground."])
                elif any(tuple(b) == tuple(t) for b, _h, _l in self._drops(self.run.index)):
                    self.say(["Your Pokemon used Strength!", "The boulder dropped through the hole!", "It landed on the floor below."])
                else:
                    self.say(["Your Pokemon used Strength!", "The boulder slid out of the way!"])
            else:
                self.say(["The boulder didn't budge. Try again any time!"])

        def go():
            self.game.change_state(SlidePuzzleState(self.game, done))
        self.say(["A huge boulder is in the way.", "Use Strength to push it? Slide the numbers into order!"], then=go)

    SMASH_WILD = 0.4   # (how often a broken rock hides a wild Pokemon: ORAS's Rock Smash, the area's own Pokemon)

    def _smash(self, t):
        """Your Pokemon breaks a cracked rock (Soaring's Mirage spots, map "smash_wild"); a wild Pokemon may jump out."""
        f = self.run.floor
        f.decor.pop(t, None)
        f.tiles[t[1]][t[0]] = core.FLOOR
        self.__dict__.setdefault("_smashed", {}).setdefault(self.run.index, set()).add(t)
        self._floor_surf = None
        self._pose_start("field")   # (your own field-move pose, if you have one: Orange 5.7's Ash)
        rng = random.Random()
        if rng.random() >= self.SMASH_WILD:
            self.say(["Your Pokemon used Rock Smash!", "The rock crumbled away."])
            return
        mon = self._wild_for_pool(rng, "smash")
        if mon is None:
            self.say(["Your Pokemon used Rock Smash!", "The rock crumbled away."])
            return
        mover = core.Mover("wild", t[0], t[1], payload=mon)
        f.movers.append(mover)
        from src.world import feats as _feats
        _feats.note(self.game.story_manager, "finds")   # (a Feat: Pokemon found by Headbutt / Rock Smash)
        _feats.note(self.game.story_manager, "smash")   # (Johto counts its Rock Smash finds on their own)
        self.say(["Your Pokemon used Rock Smash!", f"A wild {getattr(mon, 'display_name', 'Pokemon')} jumped out!"],
                 then=lambda: self._meet_wild(mover))

    def _read_sign(self):
        """The sign (or door) you face on one of our own maps: read it out (or go in)."""
        f = self.run.floor
        px, py = self.run.player
        t = (px + self.facing[0], py + self.facing[1])
        what = str(f.decor.get(t, ""))
        m = self.run.recipe.get("art") or {}
        if m.get("floors"):  # (a map of floors: this floor's signs)
            m = dict(m, signs=m["floors"][self.run.index].get("signs", []))
        if self._hidden_item(t):  # (an item hidden in something solid: the Abandoned Ship's Rm. 6 Key)
            return True
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
        if what.startswith("ramp:"):
            way = "west" if what.startswith("ramp:-1") else "east" if what.startswith("ramp:1") else "on"
            if self.game.story_manager.inventory.get("BICYCLE", 0) <= 0:
                self.say(["A bike ramp, sloping up to the " + way + ".", "On a Bicycle, you could jump off it!"])
            else:
                self.say(["A bike ramp, sloping up to the " + way + ".", "Ride at it heading " + way + ": a short hop in normal gear,",
                          "or hold Shift for top gear and a long jump."])
            return True
        if what.startswith("stones:"):
            self.say(["Round stones, in a row.", "On a Bicycle, you could hop across them!"])
            return True
        if what.startswith("crack:"):
            if m.get("smash_wild") and __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_ROCK_SMASH"):
                self._smash(t)
                return True
            self.say(["A cracked rock is in the way.", "A Pokemon that knows Rock Smash could break it."])
            return True
        if what.startswith("falls:"):
            self.say(["A wall of rushing water!", "A Pokemon that knows Waterfall could climb it."])
            return True
        if what.startswith("climb:"):
            self.say(["A steep rock wall, with footholds.", "A Pokemon that knows Rock Climb could scale it."
                      if self.area_data.get("region") != "ORANGE" else "A Climb Kit would get you up it."])
            return True
        if what.startswith("hole:"):
            self.say(["There's a hole in the floor.", "A boulder pushed in would drop to the floor below."])
            return True
        if what.startswith("barrier:"):
            bar = getattr(self, "_bars", {}).get(tuple(t), {})
            if bar.get("boss"):  # (it battles you: the Kecleon the Devon Scope shows, a wild Pokemon in the way)
                self.action_challenge_boss(dict(bar["boss"]))
                return True
            ow = bar.get("open_with")   # (it gives way once you meet its condition: the Sealed Chamber's walls, Dig, Wailord and Relicanth)
            if ow and all(self._check_route_condition(c, False, ow) for c in (ow.get("condition") or [])):
                self.game.story_manager.story_flags[ow["flag"]] = True
                self._clear_boulders()   # (the bars again: this one's "until" is met now)
                self._floor_surf = None
                self._over_key = None   # (its picture may change too: a picture "until" the flag)
                self.say(ow.get("lines") or ["Something gave way!"])
                return True
            self._read_puzzle(t)
            self.say(bar.get("lines") or ["The Cycling Road is for bicycles only.", "Come back with a Bicycle."])
            return True
        if what.startswith("rubble:"):
            self.say(["Fallen rocks block the way.", "Maybe there's another way around."])
            return True
        if what.startswith("pressed:"):
            self.say(["The boulder sits on the floor switch.", "It's holding the switch down."])
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
            _fl = m["floors"][self.run.index] if m.get("floors") and self.run.index < len(m["floors"]) else m
            _ev = (_fl.get("sign_events") or {}).get(f"{t[0]},{t[1]}")   # (a panel you press, not a sign you read: a lift's floor
            if isinstance(_ev, str):                                       #  buttons, FireRed's; {"x,y": a route option or its text}, 11-23)
                _ev = next((o for o in self.area_data.get("route_menu", []) if o.get("text") == _ev), None)
            if _ev and self._check_route_condition(_ev.get("condition"), False, _ev) and self._flag_ok(_ev):
                self._get_route_callback(_ev)()
                return True
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
        if getattr(self, "_ride", None) and getattr(self, "anim", 0) == 0 and getattr(self, "run", None) is not None:
            self._ride_step()
        if getattr(self, "run", None) is not None and self._here_art().get("stones") and not self._here_art().get("boxes"):
            _sk = (self.run.index, tuple(self._stone_spots()))
            if getattr(self, "_stones_seen", None) != _sk:
                self._stones_seen = _sk
                self._place_stones()
        if getattr(self, "run", None) is not None and self._here_art().get("boxes"):
            _bk = (self.run.index, tuple(self._box_spots()), tuple(self._box_shown(i) for i in range(len(self._box_spots()))))   # (and which stand now)
            if getattr(self, "_boxes_seen", None) != _bk:
                self._boxes_seen = _bk
                self._place_boxes()
        if self.mode == "CATCH":
            if hasattr(self, "run"):
                self._npc_tick()   # (the map under the catch screen keeps going: people walk about; none can spot you)
            return super().update()
        if hasattr(self, "run") and self.run.player:   # (where you stand, kept for the save file: Continue puts you back here; Jordan 11-20)
            self.game.last_spot = {"area": self.area_key, "kind": "map", "floor": int(self.run.index),
                                   "x": int(self.run.player[0]), "y": int(self.run.player[1]), "face": list(getattr(self, "facing", (0, 1)))}
        self._vs_tick()   # (the VS Seeker playing: the pose, the bubbles, then its message)
        then = getattr(self, "_pose_then", None)
        if then and pygame.time.get_ticks() - (getattr(self, "_pose", None) or (None, 0))[1] >= 650:   # (the cast is out: now the bite)
            self._pose_then = None
            then()
        if hasattr(self, "run"):
            from src.world import poke_radar as _radar
            _radar.tick(self)   # (back from a radar meeting: the grass shakes again)
            from src.world import ambush as _amb
            _amb.tick(self)   # (shaking grass, dust, ripples now and then: src/world/ambush.py, 11-24)
            self.run.lead_level = next((m.level for m in self.game.story_manager.player_team if getattr(m, "current_hp", 1) > 0), None)
            from src.world import escorts as _esc
            _esc.sync(self)   # (who goes everywhere with someone: Jessie & James's Meowth, 11-19)
            _fl = self.game.story_manager.story_flags   # (each frame only when something may have changed - a flag, the floor, the
            _bk = (self.run.index, id(self.run.floor), len(_fl), sum(1 for _v in _fl.values() if _v),   #  map's things - else every
                   len(self.run.floor.decor), len(self.game.story_manager.inventory))                     #  quarter second; a step
            self.__dict__["_bk_tick"] = self.__dict__.get("_bk_tick", 0) + 1                             #  still checks every time
            if _bk != self.__dict__.get("_bk_seen") or self._bk_tick >= 15:                               #  (the Checks branch's C4))
                self._bk_seen, self._bk_tick = _bk, 0
                self._clear_boulders()
            if getattr(self, "_boss_synced", None) != self.run.index:   # (up or down a floor: a beaten boss's tile there is clear too, the Tower's 6F)
                self._boss_synced = self.run.index
                self._sync_boss_spot()
        if self.dialogue_box.visible:
            self.dialogue_box.update()
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if getattr(self, "_sign_due", False) and hasattr(self, "run"):   # (arrived: this region's game's sign, src/vfx/area_changes.py)
            self._sign_due = False
            from src.vfx import area_changes
            _got = area_changes.arrival(self, self._sign_text, inside=self._indoors(self.run.index))
            if _got is not False:
                self.sign, self.banner = _got, 0
        if getattr(self, "sign", None):
            self.sign.tick(busy=self.dialogue_box.visible or self.mode != "MAP")
        if self.banner > 0:
            self.banner -= 1
        if self.anim > 0:
            self.anim = max(0, self.anim - (2 if self._may_run() else 1))
        if getattr(self, "_walker", None):
            self._walker_step()
            return
        if hasattr(self, "run"):
            self._wu_leavers_tick()   # (wild ones running off: Honey's, a swarm's)
            if self.mode == "OWWALK":   # (walking over to where a map battle stands, or back: overworld_battle.py)
                self._ow_walk_tick()
                return
            if self.mode in ("WALKUP", "SWARM"):   # (walking up to you; the swarm's battle on the map)
                self._npc_tick()
                self._wu_tick() if self.mode == "WALKUP" else self._sw_tick()
                return
        if self.mode == "MAP" and hasattr(self, "run") and not self.dialogue_box.visible:
            self._sync_partners()
            self._npc_tick()
        if self.mode == "MAP":
            self._contest_check()
            self._safari_check()
            if self.area_key == "ROYAL_UNOVA":   # (the voyage's clock and whistles: src/world/royal_unova.py, 11-21)
                __import__("src.world.royal_unova", fromlist=["tick"]).tick(self)
            self._phone_check()
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
            if getattr(self, "_on_crack", None):   # (after this frame's walking and held keys: stopped on a cracked floor
                self._crack_stop()                  #  on the Bicycle, it gives way)
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
            if m.get("smash_wild"):  # (rocks broken one at a time, a wild Pokemon behind some: Soaring's Mirage spots)
                gone = self.__dict__.get("_smashed", {}).get(self.run.index, set())
                grid = ["".join("." if c == "0" and (i, j) in gone else c for i, c in enumerate(row)) for j, row in enumerate(grid)]
            elif __import__("src.world.hms", fromlist=["field"]).field(self.game.story_manager, "HM_ROCK_SMASH") and any("0" in row for row in grid):  # (cracked rocks, broken)
                grid = [row.replace("0", ".") for row in grid]
            if __import__("src.world.hms", fromlist=["usable"]).usable(self.game.story_manager, "HM_CUT") and any("2" in row for row in grid):  # (small trees, cut down)
                grid = [row.replace("2", ".") for row in grid]
            own = m["floors"][self.run.index].get("theme") if m.get("floors") else None  # (a floor's own look: the seabed under a sea route)
            own_roofs = m["floors"][self.run.index].get("roofs") if m.get("floors") else None  # (a floor's own room look: its floor and wall colours, its furniture)
            self._floor_surf = _art.surface(grid, m.get("buildings", {}), TILE, own_roofs or m.get("roofs"), own or m.get("theme"))
            self._floor_index = self.run.index
            _roofs = own_roofs or m.get("roofs") or {}
            self._live_roofs, self._live_grid, self._live_map = _roofs, grid, m   # (the live 3D camera's: dungeon_live.py)
            self.cam3d = None   # (B2W2's maps: seen as the DS camera sees them, src/dungeon/camera3d.py)
            if _roofs.get("_cam"):
                from src.dungeon import camera3d as _c3
                try:
                    self.cam3d = _c3.Cam3D(_roofs["_cam"], _roofs.get("_objects") or [], TILE, len(grid[0]), len(grid), set(_art.doors(grid)))
                except (pygame.error, OSError, KeyError, ValueError):
                    self.cam3d = None
            self.shadows = bool(_roofs.get("_shadows"))
            return
        if self.run.recipe.get("image"):  # a real map: its own picture, a tile for a tile
            path = os.path.join(self.game.assets.assets_dir or "", "walk_routes", f"{self.run.recipe['image']}.png")
            img = pygame.image.load(path).convert()
            self._floor_surf = pygame.transform.scale(img, (f.w * TILE, f.h * TILE))
            self._floor_index = self.run.index
            return
        self.cam3d, self.shadows = None, False
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
        """The whole-number scale the following Pokemon are drawn at: the one a Journeys trainer sheet ("male") is drawn at,
        the size their sheets were made to stand beside. (Not whichever player sheet comes first: Black 2's Nate is a
        shorter sprite drawn at 3x, which made every follower half as big again; Jordan 11-20.)"""
        if not hasattr(self, "_t_scale"):
            self._t_scale = 2
            try:
                players = sprite_map(self.game).get("players") or {}
                sheet = players.get("male") or next(iter(v for v in players.values() if isinstance(v, str)), None)
                if sheet:
                    img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "characters", sheet))
                    cell = img.subsurface((0, 0, img.get_width() // 4, img.get_height() // 4))
                    h = cell.get_bounding_rect().h or cell.get_height()
                    self._t_scale = max(1, round((TILE + 22) / max(1, h)))
            except (pygame.error, OSError, StopIteration):
                pass
        return self._t_scale

    def _mon_img(self, pid, facing=(0, 1), form=None, shiny=False):
        """Species pid's following-Pokemon sheet (assets/dungeon/followers), facing its way, stepping; None if it has none."""
        class _Mon:  # (just what the walking sheet needs)
            pass
        m = _Mon()
        m.id, m.form, m.is_shiny, m.gender = int(pid), form or "normal", bool(shiny), None
        try:
            return self._follower_img(m, facing)
        except (pygame.error, OSError, ValueError, TypeError):
            return None

    def _follower_img(self, pokemon, facing):
        pid = int(getattr(pokemon, "meta_id", None) or pokemon.id) if int(pokemon.id) >= 2000 else int(pokemon.id)
        shiny = bool(getattr(pokemon, "is_shiny", False))
        frame = (pygame.time.get_ticks() // 160) % 4  # (stepping, as following Pokemon do)
        row = FACING_ROW.get(tuple(facing), 0)

        female = getattr(pokemon, "gender", None) == "F" and str(getattr(pokemon, "form", "normal") or "normal").lower() == "normal"

        def sheet():
            names = follower_names(self.game, pokemon)  # (a form's own sheet first: 12_pinkan, 2055 Paldean Tauros)
            for path in region_sheet_paths(self.game, names, shiny):   # (the region's own sheet first, Jordan 11-23)
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
        _here = str(getattr(self.game.story_manager, "get_current_region", lambda: "")() or "")   # (a region's own sheet differs by region)
        data = self._sprite(("follower_sheet", int(pokemon.id), pid, form_key, shiny, female, _here), sheet)
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
        return self._sprite(("follower", int(pokemon.id), pid, form_key, shiny, row, frame, female, _here), make)

    def _sheet_frame(self, sheet, facing=(0, 1), col=None, frame=0, height=None, scale=None):
        """One cell of a Pokemon Journeys overworld sheet (4 x 4): a person's walking frame (col None: the
        columns are steps), or a Pokemon's (col: whose column), the row by the way it faces."""
        as_person = height is None and scale is None and col is None   # (a person at the usual size: PERSON_H, by its set)
        height = height or TILE + 22

        if "+" in str(sheet):   # (a pair who always go together, side by side: "oi_74.png+oi_75.png" = Orange 5.7's James and Jessie;
            def part(s):   #  Jordan 11-19 - Kanto's Jessie & James were one figure; "+mon:52": their Meowth follows them too, its follower sprite)
                if s.startswith("mon:"):
                    class _Mon:
                        id, form, is_shiny, gender = int(s[4:]), "normal", False, None
                    return self._follower_img(_Mon(), tuple(facing))
                return self._sheet_frame(s, facing, col=col, frame=frame, height=height, scale=scale)

            def make_pair():
                parts = [p for p in (part(s) for s in str(sheet).split("+")) if p is not None]
                gap = max(2, TILE // 14)
                w, h = sum(p.get_width() for p in parts) + gap * (len(parts) - 1), max(p.get_height() for p in parts)
                out = pygame.Surface((w, h), pygame.SRCALPHA)
                x = 0
                order = parts[::-1] if tuple(facing) == (1, 0) else parts   # (facing right, the second walks in front)
                for p in order:
                    out.blit(p, (x, h - p.get_height()))
                    x += p.get_width() + gap
                if any(p_ in PERSON_FRAMES for p_ in parts):   # (two people together: a person in 3D too)
                    PERSON_FRAMES.add(out)
                return out
            if "mon:" in str(sheet):   # (a Pokemon in it steps all the time: made fresh each look)
                return make_pair()
            return self._sprite(("sheet_pair", sheet, facing, col, frame, height, scale), make_pair)

        def make():
            img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "dungeon", "characters", sheet)).convert_alpha()
            cw, ch = img.get_width() // 4, img.get_height() // 4
            cell = img.subsurface(((frame if col is None else col) * cw, FACING_ROW.get(facing, 0) * ch, cw, ch))
            box = cell.get_bounding_rect()
            cell = cell.subsurface(box) if box.w and box.h else cell
            tall = cell.get_height() if col is not None else max(cell.get_height(), int(ch * 0.8))   # (11-20: something short in
            tall = ch if sheet in CELL_SIZED else tall   # its frame - an item ball - keeps its size beside people; Black 2's own ball sheet by its cell)
            k = scale or max(1, round(height / max(1, tall)))   # (whole steps: crisp pixels; "scale": a fixed one)
            pk = person_scale(sheet, cw, ch) if as_person and sheet not in CELL_SIZED else None
            if pk:   # (a person from a known set: its set's adult PERSON_H tall, 11-23)
                out_ = pygame.transform.scale(cell, (max(1, round(cell.get_width() * pk)), max(1, round(cell.get_height() * pk))))
                PERSON_FRAMES.add(out_)   # (and LIVE_PERSON tall in the 3D world)
                return out_
            return pygame.transform.scale(cell, (max(1, int(cell.get_width() * k)), max(1, int(cell.get_height() * k))))
        return self._sprite(("sheet", sheet, facing, col, frame, height, scale, as_person), make)

    def _surf_draw(self, me, pr, at, k):
        """(bottom, image, rect) for you surfing: the Pokemon carrying you (Pokemon Orre's base_surf sheet,
        bobbing), you on its back; stepping on or off the sea you hop across (an arc) while it stays put."""
        frame = (pygame.time.get_ticks() // 160) % 4
        from src.pokemon import rowdy   # (Pokemon Yellow: with the rowdy Pikachu along, you ride its surfboard; Jordan's sheet, 11-16)
        pika = self._pika_surf(frame) if rowdy.in_party(self.game.story_manager) is not None else None
        base, pika_top = pika if pika else (self._sheet_frame("base_surf.png", self.facing, col=frame, height=int(TILE * 0.95)), None)
        if not pika:   # (your own sitting frame, player_extra "surf": Orange 5.7's Ash, 11-17; on Pikachu's board you stand)
            me = self._extra_frame("surf", self.facing, 0) or me
        bob = int(2 * math.sin(pygame.time.get_ticks() / 180))
        was, now = (self._on_surf(self.anim_from) if self.anim > 0 else True), self._on_surf()
        if was and now:  # riding: it moves with you
            spot, lift = pr, 16 + bob
        elif now:  # hopping on: it waits on the water you hop to
            spot, lift = at(*self.run.player), int(16 * k + 30 * math.sin(k * math.pi))
        else:  # hopping off: it stays on the water you leave
            spot, lift = at(*self.anim_from), int(16 * (1 - k) + 30 * math.sin(k * math.pi))
        out = [(spot.bottom - 1, base, base.get_rect(midbottom=(spot.centerx, spot.bottom + 4 + bob)))]
        mx = pr.centerx
        if pika_top is not None and self.facing[0]:   # (side on: you stand at the back of the board, a leg past Pikachu; Jordan 11-16)
            mx -= int(self.facing[0] * TILE * 0.27)
        out.append((max(pr.bottom, spot.bottom), me, me.get_rect(midbottom=(mx, pr.bottom - lift))))
        if pika_top is not None and self.facing != (0, -1):   # (Pikachu again, over you: you stand behind it on the board; Jordan 11-16. Heading up, it's ahead of you)
            out.append((max(pr.bottom, spot.bottom) + 1, pika_top, pika_top.get_rect(midbottom=(spot.centerx, spot.bottom + 4 + bob))))
        return out

    def _pika_surf(self, col):
        """The Surfing Pikachu's board (Jordan's sheet, pikachu_surf.png) and Pikachu alone (pikachu_surf_top.png), cut
        and scaled the same way so the two lie exactly on each other."""
        def make():
            d = os.path.join(self.game.assets.assets_dir, "dungeon", "characters")
            full = pygame.image.load(os.path.join(d, "pikachu_surf.png")).convert_alpha()
            top = pygame.image.load(os.path.join(d, "pikachu_surf_top.png")).convert_alpha()
            cw, ch = full.get_width() // 4, full.get_height() // 4
            cell = pygame.Rect(col * cw, FACING_ROW.get(self.facing, 0) * ch, cw, ch)
            box = full.subsurface(cell).get_bounding_rect().move(cell.topleft)
            k = max(1, round(TILE * 1.05 / max(1, box.h))) * 1.5   # (Jordan 11-16: half as big again; the sheet is drawn at 2x, so 1.5 = 3 px an art pixel)
            size = (int(box.w * k), int(box.h * k))
            return (pygame.transform.scale(full.subsurface(box), size), pygame.transform.scale(top.subsurface(box), size))
        return self._sprite(("pika_surf", self.facing, col), make)

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

    def _player_extra(self, kind):
        """Your trainer's own sheet of a kind (dungeon_sprites.json "player_extra": bike, surf, fish, field, dive, run;
        Orange Islands 5.7's Ash, 11-17), else None: the walking sheet as before."""
        char = str(getattr(self.game, "player_character", "") or "red").lower()
        return ((sprite_map(self.game).get("player_extra") or {}).get(char) or {}).get(kind) or None

    def _extra_frame(self, kind, facing=(0, 1), col=0):
        """One frame of your player_extra sheet (a 4 x 4 sheet, its row by the way you face, or a strip {file, cols, rows}),
        at your walking sheet's own scale; cut round the cell's middle (a rod held out doesn't push you sideways), down
        to its lowest pixel, like the walking frames. None without one."""
        ent = self._player_extra(kind)
        if not ent:
            return None
        name, cols, rows = (ent, 4, 4) if isinstance(ent, str) else (ent.get("file"), int(ent.get("cols", 4)), int(ent.get("rows", 4)))
        big = 1 if isinstance(ent, str) else int(ent.get("scale", 1))   # (a sheet drawn at half the walking sheet's pixel size: FireRed's frames beside Journeys' Red)

        def make():
            d = os.path.join(self.game.assets.assets_dir, "dungeon", "characters")
            img = pygame.image.load(os.path.join(d, name)).convert_alpha()
            players = sprite_map(self.game).get("players") or {}
            char = str(getattr(self.game, "player_character", "") or "red").lower()
            walk = players.get(char) or players.get("female" if char in players.get("girls", []) else "male")
            k = 2
            if walk:   # (the walking sheet's scale, as _sheet_frame works it out: the same size of pixel)
                w_img = pygame.image.load(os.path.join(d, walk))
                w_box = w_img.subsurface((0, 0, w_img.get_width() // 4, w_img.get_height() // 4)).get_bounding_rect()
                k = person_scale(walk, w_img.get_width() // 4, w_img.get_height() // 4) or max(1, round((TILE + 22) / max(1, w_box.h)))   # (as the
                # walking frames are scaled: a known set's people at PERSON_H, 11-23)
            cw, ch = img.get_width() // cols, img.get_height() // rows
            cell = img.subsurface(((col % cols) * cw, (FACING_ROW.get(facing, 0) if rows == 4 else 0) * ch, cw, ch))
            box = cell.get_bounding_rect()
            if not (box.w and box.h):
                return None
            half = max(cw // 2 - box.x, box.right - cw // 2)
            part = cell.subsurface((cw // 2 - half, box.y, 2 * half, box.h))
            out_ = pygame.transform.scale(part, (max(1, round(part.get_width() * k * big)), max(1, round(part.get_height() * k * big))))
            if walk and person_scale(walk, w_img.get_width() // 4, w_img.get_height() // 4):
                PERSON_FRAMES.add(out_)   # (your run / dive / fish frames: a person in 3D, as your walking ones)
            return out_
        return self._sprite(("player_extra", name, facing, col % cols), make)

    def _pose_start(self, kind):
        """Show your own pose for a moment (player_extra "field": using a field move; "fish": casting), if you have one."""
        if self._player_extra(kind):
            self._pose = (kind, pygame.time.get_ticks())

    def _pose_img(self):
        """Your pose (see _pose_start) while it lasts: through its message, or a moment; a step ends it."""
        pose = getattr(self, "_pose", None)
        if not pose:
            return None
        t = pygame.time.get_ticks() - pose[1]
        box = getattr(self, "dialogue_box", None)
        if self.anim > 0 or (t > 1600 and not (box is not None and box.visible) and not getattr(self, "npc_active", False)):   # (npc_active: a town's message)
            self._pose = None
            return None
        if pose[0] == "fish":   # (the cast: rod back, over, out, in the water; the way you face)
            return self._extra_frame("fish", self.facing, min(3, t // 150))
        return self._extra_frame(pose[0], self.facing, min(4, t // 110))   # (field: the Poke Ball out, held up)

    def _player_img(self):
        """You on the map: your trainer's Journeys overworld sprite (yours, else a boy's or a girl's),
        facing the way you go, its feet moving while you step. On the round stones: your wheelie (still) and hop."""
        on = getattr(self, "_on_stones", None) if hasattr(self, "run") else None   # (towns borrow this: no stones there)
        acro = self._acro_sheet() if on and (on() or (self.anim > 0 and on(self.anim_from))) else None
        if acro:
            k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 0
            return self._sheet_frame(acro, self.facing, frame=(0 if self.anim == 0 else 1 if k < 0.5 else 3))
        vs = self._vs_pose() if getattr(self, "_vs_anim", None) else None
        if vs is not None:   # (holding up the VS Seeker: FireRed's own frames)
            return vs
        players = sprite_map(self.game).get("players") or {}
        char = str(getattr(self.game, "player_character", "") or "red").lower()
        sheet = players.get(char) or players.get("female" if char in players.get("girls", []) else "male")
        if not sheet:
            return None
        frame = (1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0
        _surf = getattr(self, "_on_surf", None) if hasattr(self, "run") else None
        if _surf and (_surf() or (self.anim > 0 and _surf(self.anim_from))):
            frame = 0   # (riding a Pokemon on the water: you sit still, no walking steps - Jordan 11-16)
        elif self._player_extra("field") or self._player_extra("fish") or self._player_extra("dive") or self._player_extra("run"):
            # (your own sheets, player_extra: Orange 5.7's Ash, 11-17)
            own = self._pose_img()
            if own is None and hasattr(self, "run") and self._player_extra("dive") and self._plan().get("surface") is not None:
                own = self._extra_frame("dive", self.facing, frame)   # (on the seabed: swimming)
            if own is None and self.anim > 0 and self._player_extra("run") and getattr(self, "_may_run", None) and self._may_run():
                own = self._extra_frame("run", self.facing, frame)   # (Shift held: running)
            if own is not None:
                return own
        return self._sheet_frame(sheet, self.facing, frame=frame)

    def _ring_spot(self, f):
        """A map with Hoopa's ring (its floor's "ring" [x, y], dev/builders/town_maps/soaring.py): where the empty ring floats
        when no legend stands at the back (else None; a legend out stands in front of a ring of its own)."""
        m = (getattr(self, "recipe", None) or {}).get("art") or {}
        fl = m["floors"][self.run.index] if m.get("floors") and self.run.index < len(m["floors"]) else m
        spot = fl.get("ring")
        if not spot:
            return None
        if any(mv.kind == "figure" and isinstance(mv.payload, dict) and mv.payload.get("action") == "BOSS" for mv in f.movers):
            return ()
        return tuple(spot)

    def _draw_ring(self, screen, r):
        """Hoopa's ring floating over a tile (the Hyperspace Fury picture, Pokemon Orre's animation set: assets/soaring)."""
        def make():
            img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "soaring", "hoopa_ring.png")).convert_alpha()
            side = int(TILE * 2.1)
            return pygame.transform.smoothscale(img, (side, side))
        img = self._sprite(("hoopa_ring",), make)
        if img is None:
            return
        bob = int(3 * math.sin(pygame.time.get_ticks() / 500))
        screen.blit(img, img.get_rect(center=(r.centerx, r.centery - int(TILE * 0.75) + bob)))

    def _figure_img(self, item, facing=(0, 1), frame=0):
        """A story figure's look: its own sheet ("AREA:TEXT" in dungeon_sprites.json), a boss's Pokemon
        (its overworld sprite, else its party icon), or a townsperson; facing its way, at that step (src/dungeon/npc.py)."""
        sm = sprite_map(self.game)
        spec = (sm.get("figures") or {}).get(f"{self.area_key}:{item.get('text')}") or {}
        if spec.get("item"):
            return self._item_img(spec["item"], 40) or self._sheet_frame("Object ball.png", col=0, height=36)
        if spec.get("pic"):  # (a thing the game stands on its map, drawn from its own picture: an Apricorn tree, SoulSilver's; 11-15)
            def _make(path=spec["pic"]):
                full = os.path.join(self.game.assets.assets_dir or "", path)
                if not os.path.exists(full):
                    return None
                img = pygame.image.load(full).convert_alpha()
                h = TILE * 2 if img.get_height() > img.get_width() * 1.2 else TILE + 14
                return pygame.transform.smoothscale(img, (round(img.get_width() * h / img.get_height()), h))
            got = self._sprite(("pic", spec["pic"]), _make)
            if got is not None:
                return got
        if spec.get("draw") == "none":  # (a spot to look at, not a person: a bookshelf, a bell heard on the trail - nothing drawn; 11-23)
            return self._sprite("no_figure", lambda: pygame.Surface((1, 1), pygame.SRCALPHA))
        if spec.get("draw") == "ghost":  # (the Tower's unknown spirit: nobody can tell what it is yet)
            return self._sprite("ghost_figure", ghost_figure)
        if spec.get("draw") == "terminal":  # (a computer you use: New Mauville's security check)
            return self._sprite("terminal_figure", terminal_figure)
        if item.get("action") == "ARRIVAL":
            return self._trainer_img(item["event"].get("trainer") or {}, facing, frame)
        if item.get("action") == "MAX_RAID":  # the den's next raid Pokemon, jumbo (Jordan, 11-06)
            img = self._raid_img()
            if img is not None:
                return img
        pid = spec.get("pokemon")
        if pid == "eon":  # (your Eon, waiting where it set you down: the one that carries you, src/world/soaring.py)
            from src.world import soaring
            pid = soaring.mount(self.game)[0]
        if pid is None and item.get("action") == "BOSS" and not spec.get("sheet"):   # (a boss with a sheet of its own: the legend, Emerald's)
            pid = (item.get("boss") or self.area_data.get("area_boss") or {}).get("id")
        if pid is None and str(spec.get("sheet") or "").startswith("mon:"):
            pid = int(str(spec["sheet"])[4:])
        if pid is None:   # (someone standing about who is a Pokemon: "Poliwrath", "Cubone")
            pid = species_named(self.game, item.get("text"))
        if pid is not None:
            boss = (item.get("boss") or self.area_data.get("area_boss") or {}) if item.get("action") == "BOSS" else {}  # (a shiny boss shiny on the map too: the Red Gyarados, the Giant Volcano's Moltres)
            turns = spec.get("face", item.get("action") != "BOSS")   # (11-18: a Pokemon standing about turns like a person, to you
            img = self._mon_img(pid, tuple(facing) if turns else (0, 1), boss.get("form"), boss.get("is_shiny"))   #  as you talk; a boss keeps facing out)
            if img is not None:   # (every Pokemon on the maps: its following-Pokemon sheet, Jordan 11-14)
                return img
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
        _reg = self.area_data.get("region") or self.game.story_manager.get_current_region() or ""   # (Kanto's areas carry no "region")
        own = sm.get("trainers_" + str(_reg)) or {}
        for _role in ("rival", "friend"):  # (this save's rival or friend: their own walking sheet, where the region has one: Hoenn's Brendan and May)
            _who = str(getattr(self.game, f"{_role}_character", "") or "").lower()
            if name == "{%s_character}" % _role and _who and f"{_who}.png" in own:
                name = f"{_who}.png"
        if name == "{rival_character}" and "rival.png" in own:  # (the region's own rival sheet: FireRed's Blue)
            name = "rival.png"
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

    def follower(self):
        """The Pokemon walking behind you: the rowdy Pikachu whenever it's in the party (Yellow), else your lead."""
        from src.pokemon import rowdy
        return rowdy.in_party(self.game.story_manager) or self.lead()

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
        if self.mode == "CATCH" and not getattr(self, "_under_catch", False):
            return self._draw_catch_layer()
        screen = self.game.screen
        view = self._view()
        fonts = self.game.assets.fonts
        screen.fill(FRAME_BLACK)
        if self._floor_index != self.run.index or self._floor_surf is None:
            self._render_floor()
        z = getattr(self, "zoom", 1.0)
        if abs(z - 1.0) > 0.01 and not self._backdrop and not self._dl_live():   # (the camera in closer or further: drawn smaller, scaled into the frame; the live camera has its own distance)
            small = pygame.Rect(0, 0, max(1, round(view.w / z)), max(1, round(view.h / z)))
            off = pygame.Surface(small.size)
            self._view_override = small
            try:
                self._cam_tick()
                at0 = self._draw_world(off, small, fonts)
            finally:
                self._view_override = None
            screen.blit(pygame.transform.smoothscale(off, view.size), view.topleft)

            def at(x, y):
                r = at0(x, y)
                return pygame.Rect(view.x + round(r.x * z), view.y + round(r.y * z), round(r.w * z), round(r.h * z))
        else:
            self._cam_tick()
            at = self._draw_world(screen, view, fonts)
        if self._backdrop:  # (only the map: an OVERWORLD-style battle is drawn over it)
            return
        if getattr(self, "_under_catch", False):   # (the map in its frame: the catch screen is drawn over it)
            draw_frame(screen, view)
            return
        self._draw_rest(screen, view, fonts, at)

    CATCH_TINT = (8, 12, 24, 150)   # (how dark the map is under the catch screen)

    def _draw_catch_layer(self):
        """The route's catch screen as a see-through layer: the live map (its people, the Pokemon round you), darkened,
        then the catch screen's own pieces over it. Its taps and keys never reach the map (handle_events)."""
        screen = self.game.screen
        self._under_catch = True
        try:
            self.draw()
        finally:
            self._under_catch = False
        tint = getattr(self, "_catch_tint", None)
        if tint is None or tint.get_size() != screen.get_size():
            tint = self._catch_tint = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            tint.fill(self.CATCH_TINT)
        self.route_bg, self._catch_over_map = tint, True
        try:
            return super().draw()
        finally:
            self.route_bg, self._catch_over_map = None, False

    def _draw_world(self, screen, view, fonts):
        """The map in its frame (draw() adds the frame, the HUD, the encounter): its tile-to-screen function."""
        if self._dl_live():   # (Black 2's own models from a moving camera: dungeon_live.py, 11-21)
            return self._draw_world_live(screen, view, fonts)
        f = self.run.floor
        screen.fill((10, 14, 24), view)  # (the fog's colour: the unknown edge of the map)
        screen.set_clip(view)  # (the map stays in its frame)
        ox, oy = self._origin()
        c3 = getattr(self, "cam3d", None)

        def lp(fx, fy):   # (how many px the ground there is raised on screen: B2W2's terraces and stairs)
            return round(c3.lift(fx, fy) * TILE) if c3 else 0

        if c3:
            c3.draw_ground(screen, ox, oy)
        else:
            screen.blit(self._floor_surf, (ox, oy))
        x0, y0 = max(0, (view.x - ox) // TILE - 1), max(0, (view.y - oy) // TILE - 1)
        x1, y1 = min(f.w, (view.right - ox) // TILE + 2), min(f.h, (view.bottom - oy) // TILE + 2)
        if c3:   # (raised ground is drawn higher: tiles further down the map can show at the top of the frame)
            y1 = min(f.h, y1 + int(c3.top // TILE) + 2)
        _shadow = None
        if getattr(self, "shadows", False):
            from src.dungeon import camera3d as _c3s
            _shadow = _c3s.shadow(TILE)

        def at(x, y):
            return pygame.Rect(ox + x * TILE, oy + y * TILE - lp(x, y), TILE, TILE)

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
        from src.world import poke_radar as _radar
        _radar.draw(self, screen, at)   # (the Poke Radar's shaking grass)
        from src.world import dexnav as _dexnav
        _dexnav.draw(self, screen, at)   # (a hidden Pokemon's tail in the grass, ripples on the water)
        from src.world import phenomena as _phen
        _phen.draw(self, screen, at)   # (rustling grass, rippling water: B2W2's phenomena)
        from src.world import ambush as _amb
        _amb.draw(self, screen, at)   # (an ambush spot: shaking grass, dust, ripples)
        bob = int(3 * math.sin(pygame.time.get_ticks() / 180))
        for (x, y) in f.tm_spots:
            if (x, y) in f.seen:
                img = self._ball_img(38)
                glow = at(x, y).inflate(-8, -8)
                pygame.draw.ellipse(screen, (255, 236, 140), glow, 3)
                screen.blit(img, img.get_rect(center=(glow.centerx, glow.centery + bob)))
        self._draw_rides(screen, at)
        for sw in self._here_art().get("box_switches") or []:   # (a crate's floor switch: a steel plate, lit once pressed)
            if sw.get("into"):
                continue   # (a pit or a drop: the map's own picture)
            x, y = sw["on"]
            if (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:
                r = at(x, y).inflate(-6, -6)
                lit = self.game.story_manager.story_flags.get(sw.get("flag"))
                pygame.draw.rect(screen, (70, 74, 92), r, border_radius=4)
                pygame.draw.rect(screen, (250, 220, 110) if lit else (150, 156, 180), r, 2, border_radius=4)
                c = r.center
                pygame.draw.circle(screen, (250, 220, 110) if lit else (190, 196, 220), c, max(3, r.w // 4))
                pygame.draw.circle(screen, (70, 74, 92), (c[0] + max(2, r.w // 8), c[1] - 1), max(3, r.w // 4))   # (a crescent moon)
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
            if str(what).startswith("stone:"):   # (a stone: its picture once, at its middle tile)
                _si, _sc = str(what).split(":")[1:3]
                if _sc == f"{x},{y}" and (x, y) in f.seen:
                    self._draw_stone(screen, int(_si), at(x, y))
                continue
            if str(what).startswith(("crate:", "box:")) and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:  # (a crate: the map's own crate picture)
                r = at(x, y)
                img = self._sheet_frame("Object boulder.png", col=0, height=TILE - 4) if self._here_art().get("box_look") == "boulder" \
                    else self._crate_img()   # (a boulder you push: Platinum's Distortion World)
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom)))
                continue
            if str(what).startswith(("boulder:", "fallen:", "rubble:", "pressed:")) and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:
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
        _movers_drawn = []   # (redrawn over the top layer when their feet aren't under it: art.over_uncovered)
        from src.world import vs_seeker as _vsm   # (a trainer the VS Seeker called back: a red "!" over it)
        _vs_ready = lambda m: m.kind == "trainer" and isinstance(m.payload, tuple) and _vsm.is_ready(self.game.story_manager, self.area_key, m.payload[0])
        _ring = self._ring_spot(f)   # (Soaring's Mirage spots: Hoopa's ring at the back, empty on a quiet visit)
        if _ring and self.run.visible(*_ring):
            self._draw_ring(screen, at(*_ring))
        _bubbles = self._vs_bubbles()
        for m in f.movers:
            if not self.run.visible(m.x, m.y) or m is self._ow_foe or getattr(m, "_vs_hidden", False):
                continue
            r = at(m.x, m.y)
            mo = getattr(m, "motion", None)
            if mo is not None:  # (a person mid-step: between the two tiles)
                ax, ay = mo.at()
                r = r.move(int(round((ax - m.x) * TILE)), int(round((ay - m.y) * TILE)))
                if mo.emote > 0:
                    emotes.append(r)
            if _shadow is not None:   # (B2W2's oval under everyone's feet)
                screen.blit(_shadow, _shadow.get_rect(center=(r.centerx, r.bottom - 3)))
            if m.kind in ("wild", "walkup"):   # (walkup: drawn in by Honey or a swarm - wild_walkup.py: it hops out, faints, fades)
                img = self._icon(m.payload, TILE, flip=(m.x < self.run.player[0]), facing=getattr(m, "facing", None))
                _lift, _alpha = (self._wu_lift(m), getattr(m, "_wu_alpha", 255)) if m.kind == "walkup" else (0, 255)
                if m.kind == "walkup" and getattr(m, "_wu_off", None):   # (lunging or knocked back in the swarm's battle)
                    r = r.move(*m._wu_off)
                    if getattr(m, "_wu_flash", False):
                        from src.vfx.map_attacks import white
                        img = white(img)
                if _alpha <= 0:
                    continue
                if _alpha < 255:
                    img = img.copy()
                    img.set_alpha(_alpha)
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom + 4 - _lift)))
                _movers_drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom + 4 - _lift))))
                if m.payload.is_shiny:
                    pygame.draw.circle(screen, (255, 230, 90), (r.right - 8, r.y + 8), 5)
                if m.alert:
                    theme.shadow_text(screen, "!", fonts["label"], r.right - 6, r.y - 18, color=(220, 60, 50))
            elif m.kind == "escort":
                from src.world import escorts as _esc
                _lm = getattr(_esc.leader_of(m), "motion", None)
                img = _esc.image(self, m, _lm.frame() if _lm is not None else 0)
                if img:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
                    _movers_drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
                continue
            elif m.kind == "figure":
                self._fit_jumbo(m)
                if _ring is not None and m.payload.get("action") == "BOSS":
                    self._draw_ring(screen, r)   # (the legend come out of it, in front)
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
                    _movers_drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
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
                _wet = f.tile(m.x, m.y) == core.SURF
                img = self._trainer_img(m.payload[1], m.facing, mo.frame() if mo is not None and not _wet else 0)   # (on the water: still, no steps)
                lift = 0
                if _wet:  # (out on the sea: riding a Pokemon too)
                    frame = (pygame.time.get_ticks() // 160 + m.x) % 4
                    base = self._sheet_frame("base_surf.png", m.facing, col=frame, height=int(TILE * 0.95))
                    bob = int(2 * math.sin(pygame.time.get_ticks() / 180 + m.x))
                    screen.blit(base, base.get_rect(midbottom=(r.centerx, r.bottom + 4 + bob)))
                    lift = 16 + bob
                if img:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - lift)))
                    _movers_drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - lift))))
                else:
                    pygame.draw.circle(screen, (90, 90, 160), r.center, TILE // 3)
                if m in _bubbles:   # (the VS Seeker just used: its bubble, FireRed's)
                    self._draw_vs_bubble(screen, r, _bubbles[m])
                elif _vs_ready(m):   # (the VS Seeker called it back: it wants a rematch)
                    theme.shadow_text(screen, "!", fonts["label"], r.right - 6, r.y - 22, color=(230, 70, 60))
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
            img = self._actor_img(a["sheet"], a["m"].facing, a["m"].frame(), native=bool(a.get("native")))
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(ar.centerx, ar.bottom - 2)))
        for er in emotes:  # (someone has noticed you: a "!" over them)
            theme.shadow_text(screen, "!", fonts["label"], er.centerx - 4, er.y - 34, color=(230, 60, 50))
        # you, your trainer, with your lead Pokemon a step behind
        k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 1
        lead = self.follower()
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
        _mine = len(drawn)   # (from here: you and your Pokemon, drawn again over the top layer while you're up on a bridge)
        _partner_at = None
        _trail = {}   # (index in drawn: (from, to) tiles, for your Pokemon and companions)
        if lead and self.partner != self.run.player and me is not None and not self._backdrop and not surfing:
            # (a battle draws its own; while you surf your Pokemon is the one carrying you)
            _partner_at = len(drawn)
            (fx, fy), (tx, ty) = self.partner_from, self.partner
            pk = k
            r = pygame.Rect(int(ox + (fx + (tx - fx) * pk) * TILE), int(oy + (fy + (ty - fy) * pk) * TILE), TILE, TILE)
            look = self.run.player
            way = (look[0] - tx, look[1] - ty)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            img = self._icon(lead, TILE, flip=(self.run.player[0] > tx), facing=way)
            if getattr(self, "_lead_off", None) and self.mode == "SWARM":   # (its lunge or recoil in the swarm's battle)
                r = r.move(*self._lead_off)
                if getattr(self, "_lead_flash", False) and img is not None:
                    from src.vfx.map_attacks import white
                    img = white(img)
            _trail[len(drawn)] = (self.partner_from, self.partner)
            drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
        for _ci, _who in enumerate(self._companions() if me is not None and not self._backdrop and not surfing else ()):
            (fx, fy), (tx, ty) = self._ctrail_from[_ci + 1], self._ctrail[_ci + 1]
            if (tx, ty) in (self.run.player, self.partner):
                continue                                  # (not out yet: they come out from behind you)
            r = pygame.Rect(int(ox + (fx + (tx - fx) * k) * TILE), int(oy + (fy + (ty - fy) * k) * TILE), TILE, TILE)
            ahead = self._ctrail[_ci] if _ci else self.partner
            way = (ahead[0] - tx, ahead[1] - ty)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            img = (self._mon_img(149, way) if _who == "Dragonite"
                   else self._sheet_frame("orre_partner_rui.png", way, frame=(1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0)
                   if _who == "Rui" else self._figure_img({"text": _who}, way, (1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0))
            if img is not None:
                _trail[len(drawn)] = (self._ctrail_from[_ci + 1], self._ctrail[_ci + 1])
                drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
        if me is not None and surfing:  # on the sea: you ride your Pokemon (a hop on and off)
            drawn += self._surf_draw(me, pr, at, k)
        elif me is not None and stones and self._acro_sheet():  # (on the round stones: your own wheelie, Emerald's Acro Bike frames)
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
        elif me is not None and self._player_extra("bike") and (stones or self._cycling() or (self.anim > 0 and self._cycling(self.anim_from))):
            # (riding your own Bicycle sheet, player_extra "bike": Orange 5.7's Ash, 11-17; pedalling while you go)
            ride = self._extra_frame("bike", self.facing, (1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0) or me
            drawn.append((pr.bottom, ride, ride.get_rect(midbottom=(pr.centerx, pr.bottom))))
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
        _feet = {}
        if c3 or _shadow is not None:   # (lifted by the ground under you, smoothly mid-step; a shadow at your feet)
            for _i in range(_mine, len(drawn)):
                _k0, _img0, _rc = drawn[_i]
                _ft = _trail.get(_i)
                if _ft is None:
                    (_a, _b), (_c, _d) = (self.anim_from if self.anim > 0 else self.run.player), self.run.player
                else:
                    (_a, _b), (_c, _d) = _ft
                _L = lp(_a + (_c - _a) * k, _b + (_d - _b) * k)
                _rc.move_ip(0, -_L)
                if _i == _mine or _ft is not None or _i == len(drawn) - 1:
                    _feet[id(_rc)] = (_rc.centerx, _rc.bottom - 2)
        _me_drawn = drawn[_mine:]
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
        _extra = c3.buildings_drawn(ox, oy, view) if c3 else []   # (the buildings, the trees and lamp posts: in depth order with you)
        for _b, img, rect in sorted(drawn + _extra, key=lambda t: t[0]):
            if _shadow is not None and id(rect) in _feet:
                screen.blit(_shadow, _shadow.get_rect(center=_feet[id(rect)]))
            screen.blit(img, rect)
        if _extra:   # (someone standing in front of a building or a tree, drawn before it: drawn again over it)
            for _mk, _mimg, _mrect in _movers_drawn:
                _mr = pygame.Rect(_mrect)
                if any(_ek < _mk and _mr.colliderect(pygame.Rect(_ep, _ei.get_size())) for _ek, _ei, _ep in _extra):
                    screen.blit(_mimg, _mrect)
        spans = getattr(self.run.floor, "bridge", None)
        _pic = ((self.run.recipe.get("art") or {}).get("roofs") or {}).get("_picture")  # (a map drawn from its game's picture: its own top layer goes over you)
        if spans and self.run.recipe.get("art") and not (_pic and self._overheads()):  # (passing under a bridge: it goes over your head; a picture with its own top layer: that does)
            from src.dungeon import art as _art   # (every tile you, your Pokemon and companions overlap: a wide bridge too)
            _fr = self.anim_from if self.anim > 0 else self.run.player
            _under = []
            for _i, (_b, _img, _rect) in enumerate(_me_drawn):
                _ft = _trail.get(_i + _mine)
                if _ft is None:
                    if _art.under_bridge(spans, _fr, self.run.player, self.run.deck):
                        _under.append(_rect)
                elif _art.under_bridge(spans, _ft[0], _ft[1], self.run.deck):
                    _under.append(_rect)
            _art.bridge_over(screen, spans, _under, (ox, oy), TILE, getattr(self, "_floor_surf", None))
        for img, (bx, by) in self._overheads():  # (what passes over your head: you walk under it, out of view)
            screen.blit(img, (ox + bx, oy + by))
        if self._here_art().get("platforms"):   # (Citadark's platforms over the lava: above the map's top layer, you over them)
            self._draw_rides(screen, lambda x, y: pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE), late=True)
            for _b, _img, _rect in sorted(_me_drawn, key=lambda t: t[0]):
                screen.blit(_img, _rect)
        from src.dungeon import art as _art_o
        _art_o.over_uncovered(screen, _movers_drawn + drawn, self._overheads(), (ox, oy))   # (a roof edge no longer hides the head of someone just south of it)
        if spans and self.run.deck and _pic:   # (up on a bridge of a map drawn from its game's picture (Route 120's): the
            _here = {self.run.player, self.anim_from if self.anim > 0 else self.run.player}   # bridge's top layer is under you)
            if _here & set(spans):
                _pt = {self.partner, self.partner_from}
                for _i, (_b, img, rect) in sorted(enumerate(_me_drawn), key=lambda e: e[1][0]):
                    if _partner_at is not None and _i == _partner_at - _mine and not (_pt & set(spans)):
                        continue   # (your Pokemon, still on the bank: under the top layer as before)
                    screen.blit(img, rect)
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

        self._draw_cave_light(screen, at(*self.run.player).center)
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
            return at
        if self.mode == "MAP":
            self._draw_guide(screen, at)
        screen.set_clip(None)
        return at

    def _draw_cave_light(self, screen, centre):
        """A dark cave with a light radius (recipe "dark_radius"): black but a soft circle round you, till Flash."""
        r = self.recipe.get("dark_radius") if isinstance(getattr(self, "recipe", None), dict) else None
        if not r:
            return
        area = screen.get_clip()
        veil = pygame.Surface(area.size, pygame.SRCALPHA)
        veil.fill((0, 0, 0, 250))
        cx, cy, rad = centre[0] - area.x, centre[1] - area.y, int(r * TILE)
        for i in range(6):  # (a soft edge)
            pygame.draw.circle(veil, (0, 0, 0, 250 - 40 * (i + 1)), (cx, cy), max(1, rad - i * TILE // 8))
        screen.blit(veil, area.topleft)

    def _draw_rest(self, screen, view, fonts, at):
        """Over the map: its frame, the HUD, the encounter, the dialogue."""
        draw_frame(screen, view)
        self._draw_hud(screen)
        self._draw_qparty(screen)
        if self.mode in ("CHOICE", "MATH", "THROW"):
            self._draw_encounter(screen)
        elif self.mode == "SWARM":
            self._draw_swarm(screen, at)
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
        step = self._guide_step(mission)
        if step:  # (the mission's own way-points in this place: Silph Co.'s Card Key, then the boardroom)
            self._guide_hit = step
            return step
        # (the search over every floor is for regions led over their walked maps (guide.WALKED_REGIONS: Kanto): elsewhere the
        #  marker stays as it was, on this floor's own people and ways out, till that region's playthrough check)
        walked = bool(self.run.recipe.get("layout")) and guide.map_ways(self.game, self.area_key) is not None
        if walked and mission:  # (a drawn map: someone the mission needs on any of its floors: the way to the nearest; 11-17)
            wanted = {}
            for i in range(self.run.n_floors):
                for m in self.run.made(i).movers:
                    if m.kind == "figure" and isinstance(m.payload, dict) and guide.advances_goal(self.game, self.area_key, m.payload, mission):
                        wanted[(i, m.x, m.y)] = m.payload.get("text") or "Here"
                    elif m.kind == "trainer" and need and isinstance(m.payload, tuple) and (m.payload[1] or {}).get("victory_flag") in need:
                        wanted[(i, m.x, m.y)] = "Battle"
            if wanted:
                start = (self.run.index, *self.run.player)
                fkey = (start, frozenset(wanted), tuple(sorted(k for k, v in story.inventory.items() if v)), len(story.story_flags), sum(1 for v in story.story_flags.values() if v))
                if getattr(self, "_fig_key", None) != fkey:
                    self._fig_key, self._fig_hit = fkey, self._guide_route(start, frozenset(wanted), "Here")
                if self._fig_hit:
                    t, label = self._fig_hit
                    self._guide_hit = (t, wanted.get((self.run.index, *t), label) if label == "Here" else label)
                    return self._guide_hit
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
        _item = getattr(self, "exit_items", {}).get(hop) or {}
        _cond = _item.get("condition")
        if "no_trainers" in (_cond if isinstance(_cond, list) else [_cond]):  # (that way opens once every trainer here is beaten: Nugget Bridge: the nearest one left)
            px, py = self.run.player
            left = [m for m in f.movers if m.kind == "trainer"]
            if left:
                m = min(left, key=lambda m: abs(m.x - px) + abs(m.y - py))
                self._guide_hit = ((m.x, m.y), "Battle")
                return self._guide_hit
        if walked:  # (a drawn map: the way out toward the next stop that you can walk to, over every floor and room: Mt. Moon's ladders; 11-17)
            start = (self.run.index, *self.run.player)
            wkey = (start, hop, (mission or {}).get("id"), tuple(sorted(k for k, v in story.inventory.items() if v)), len(story.story_flags), sum(1 for v in story.story_flags.values() if v))
            if getattr(self, "_way_key", None) != wkey:
                self._way_key, self._way_hit = wkey, self._guide_way(start, hop, mission)
            if self._way_hit:
                self._guide_hit = self._way_hit
                return self._guide_hit
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

    def _guide_way(self, start, hop, mission):
        """(tile, label) toward the way out of this place that leads on to the Journal's next stop, over its floors and
        rooms. The next stop's own way out if this place has one you could get to (not the one you just came in by,
        when it has another: Viridian Forest's two gates both lead to Route 2); else, of the ways out you could get
        to, the one with the shortest trip on from there (Route 2's south half: through the Forest). When someone or
        something stands in the way, the marker goes on that first (see _guide_route)."""
        from src.world import guide
        story, run = self.game.story_manager, self.run
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        mid = (mission or {}).get("id")
        if not hasattr(run, "_guide_entry"):  # (where you came in, and what the Journal said then)
            run._guide_entry = (start, mid if getattr(self, "steps", 0) <= 1 else None)   # (only where you really came in: worked
            #  out later, after walking about under another mission's step marker, it isn't a door to avoid: Fairchild, 11-17)
            left = getattr(story, "_guide_left", None)   # (11-21: in by a door the marker didn't point to, against the way on:
            if left and left[:2] == (getattr(story, "last_area_key", None), self.area_key) and left[2] is False:   # backtracking,
                run._guide_entry = (start, None)   # so the way you came in by may well be the way on: Viridian Forest's north gate)
            first = story.__dict__.setdefault("_guide_entries", {})   # (11-21: the FIRST way in on this mission, kept while the
            #  game runs: out of Viridian Forest's north gate and back in, the way on is still north, not back south)
            if run._guide_entry[1] and getattr(story, "last_area_key", None):   # (walked in, not a load)
                run._guide_entry = first.setdefault((self.area_key, mid), run._guide_entry)
            elif not run._guide_entry[1]:
                run._guide_entry = first.get((self.area_key, mid), run._guide_entry)
        reach = self._step_route(start, frozenset(), None, reach=True, loose=True)
        outs = {}
        for i, x, y in reach:
            t = run.made(i).exits.get((x, y))
            if isinstance(t, str) and t in prog and (i, x, y) != start:
                outs.setdefault(t, []).append((i, x, y))
        if not outs:
            return None
        came = getattr(story, "last_area_key", None)
        if hop in outs:
            tiles = outs[hop]
            (e_i, e_x, e_y), e_mid = run._guide_entry
            if came == hop and e_mid == mid:
                far = [t for t in tiles if t[0] != e_i or abs(t[1] - e_x) + abs(t[2] - e_y) > 6]
                tiles = far or tiles
        else:
            goal, best = guide.goal_area(self.game), None
            for t in sorted(outs):
                path = [t] if t == goal else guide.path_to(self.game, t, goal, came=self.area_key)
                if path and (best is None or (len(path), t == came) < best[0]):
                    best = ((len(path), t == came), t)
            if best is None:
                return None
            hop = best[1]
            tiles = outs[hop]
        groups = guide.place_groups(self.game, hop)   # (the next place in parts: the ways out that land in the part that leads on -
        goal = guide.goal_area(self.game)              #  Hoenn's Routes 129-131, two seas each; 11-24)
        path = guide.path_to(self.game, hop, goal, came=self.area_key) if groups and goal and goal != hop else None
        nxt = path[1] if path and len(path) > 1 else None
        _good = guide.good_ways(self.game, self.area_key, [(x, y) for f_, x, y in tiles if f_ == 0], hop, nxt) if nxt else None
        if _good:
            tiles = [t for t in tiles if t[0] != 0 or (t[1], t[2]) in _good]
        return self._guide_route(start, frozenset(tiles), self._exit_label(hop))

    def _guide_route(self, start, goals, label):
        """(tile, label) to head for now, on the way from start to goals (one (floor, x, y) or a set): the goal itself or
        the stairs / pad that starts the shortest way you can walk. With no way you can walk yet: whoever or whatever
        stands across the shortest way there (someone to talk to, a boulder to push, the route's Pokemon asleep)."""
        hit = self._step_route(start, goals, label)
        if hit is None:
            hit = self._step_route(start, goals, label, loose=True)
        return hit

    def _guide_step(self, mission):
        """(tile, label) toward a Journal mission's next "steps" way-point in this place ({"floor", "at", "label",
        "done"}: Jordan, 11-14: Silph Co. guided floor by floor): on its floor, the spot itself; elsewhere, the stairs
        or warp pad that starts the shortest way there, through doors you can open now. None: no step here, or no
        way there yet."""
        from src.world import guide
        if not mission or not mission.get("steps") or not self.run.recipe.get("layout"):
            return None
        story = self.game.story_manager
        step = next((s for s in mission["steps"] if s.get("area", guide.mission_target(self.game, mission)) == self.area_key
                     and not (s.get("done") and guide._ok(story, s["done"])) and guide._ok(story, s.get("when"))), None)
        _rooms = (self.run.recipe.get("art") or {}).get("room_floors")   # (a route with rooms: its ground is floor 0, the rooms the rest -
        fl = step.get("floor", 0 if self.run.n_floors == 1 or _rooms else None) if step else None   #  a step with no floor is outdoors: Route 4's Colress, 11-24)
        if step and step.get("room"):  # (a room of the map, walked as a floor of its own: the S.S. Anne's Captain's cabin)
            fl = ((self.run.recipe.get("art") or {}).get("room_floors") or {}).get(step["room"])
        if fl is None or not 0 <= fl < self.run.n_floors or not step.get("at"):
            return None
        goal = (fl, *step["at"])
        start = (self.run.index, *self.run.player)
        key = (start, goal, tuple(sorted(k for k, v in story.inventory.items() if v)), len(story.story_flags), sum(1 for v in story.story_flags.values() if v))
        if getattr(self, "_step_key", None) != key:
            self._step_key, self._step_hit = key, self._guide_route(start, goal, step.get("label") or "Here")
            if self._step_hit is None:   # (the step is in a part of this place you can't reach from here: out, and round to a
                self._step_hit = self._guide_round(start, goal)   #  way in that reaches it - Team Galactic HQ's front door; 11-24)
        return self._step_hit

    def _guide_round(self, start, goal):
        """(tile, label): the way out of this place toward a way back in that reaches goal ((floor, x, y)), when goal can't be
        reached from where you stand (a place in parts: Team Galactic HQ's warehouse side and its front door). None: no such way."""
        from src.world import guide
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        run = self.run
        there = self._step_route(goal, frozenset(), None, reach=True, loose=True)
        ins = {run.made(i).exits.get((x, y)) for i, x, y in there}
        ins = {t for t in ins if isinstance(t, str) and t in prog and t != self.area_key}
        if not ins:
            return None
        reach = self._step_route(start, frozenset(), None, reach=True, loose=True)
        outs = {}
        for i, x, y in reach:
            t = run.made(i).exits.get((x, y))
            if isinstance(t, str) and t in prog and t != self.area_key and (i, x, y) != start:
                outs.setdefault(t, set()).add((i, x, y))
        best = None
        for o in sorted(outs):
            for a in sorted(ins):
                path = [o] if o == a else guide.path_to(self.game, o, a, avoid={self.area_key})
                if path and (best is None or len(path) < best[0]):
                    best = (len(path), o)
        if best is None:
            return None
        return self._guide_route(start, frozenset(outs[best[1]]), self._exit_label(best[1]))

    def _height_edge(self, a, b, index=None):
        """True when a -> b climbs or drops between two of a floor's levels the way the Gen 3 games forbid (11-23, FireRed's
        Victory Road, Seafoam, Cerulean Cave, the Sevii canyons): a floor's "heights" (one hex digit a tile, the game's own
        elevation) - a step between two land heights that differ is no step, unless one of them is 0 (stairs: any level)
        or 15 (a bridge: both). Height 1 is water: the Surf rules have it."""
        art = (getattr(self, "recipe", None) or {}).get("art") or {}
        i = self.run.index if index is None else index
        plan = (art.get("floors") or [art])[i] if i < len(art.get("floors") or [art]) else {}
        rows = plan.get("heights") if isinstance(plan, dict) else None
        if not rows:
            return False
        try:
            ha, hb = int(rows[a[1]][a[0]], 16), int(rows[b[1]][b[0]], 16)
        except (IndexError, ValueError):
            return False
        free = (0, 1, 15)
        return ha not in free and hb not in free and ha != hb

    def _step_route(self, start, goal, label, reach=False, loose=False):
        """The first tile to head for on the shortest way from start to beside goal ((floor, x, y) each; goal can be a
        set of them: the nearest is taken), by ways you can walk now: over ledges their one way, across water with
        Surf, round people, and pressing a statue switch where that swings the gates the right way (the Pokemon
        Mansion's: the search knows which way every gate stands after each press). reach: only how far you can get (the
        set of every (floor, x, y)). loose: as if nobody and nothing that can be moved stood in the way (people, a
        boulder with Strength, a rock barrier its boulder switch lowers, the route's Pokemon asleep): the way to the
        first of those on the shortest way there."""
        from collections import deque
        goals = goal if isinstance(goal, (set, frozenset)) else {goal}
        goal = None
        art = self.run.recipe.get("art") or {}
        plans = art.get("floors") or [art]
        floors = [self.run.made(i) for i in range(self.run.n_floors)]
        plan_of = lambda i: plans[i] if i < len(plans) and isinstance(plans[i], dict) else {}
        story = self.game.story_manager
        strength = __import__("src.world.hms", fromlist=["field"]).field(story, "HM_STRENGTH")
        surf = self._can_surf()
        _hms = __import__("src.world.hms", fromlist=["field", "usable"])
        clears = {k for k, on in (("falls", _hms.field(story, "HM_WATERFALL")), ("cut", _hms.usable(story, "HM_CUT")),
                                  ("whirl", _hms.field(story, "HM_WHIRLPOOL")),   # (a whirlpool you can clear: the way on, as a waterfall is; 11-23 Johto's Route 41 to the Whirl Islands)
                                  ("crack", _hms.field(story, "HM_ROCK_SMASH") and not art.get("smash_wild")),
                                  ("climb", story.inventory.get("HM_ROCK_CLIMB", 0) > 0 or story.inventory.get("CLIMB_KIT", 0) > 0),
                                  ("slope", story.inventory.get("BICYCLE", 0) > 0), ("stones", story.inventory.get("BICYCLE", 0) > 0)) if on}
        # (what a floor drawn before you had the HM still shows, cleared the next time you stand on it: Icefall Cave's
        #  entrance falls, seen first without Waterfall; 11-17)
        press = [(plan_of(i).get("switch") or {}).get("flag") for i in range(len(floors))]   # (each floor's statue switch flag)
        secrets = [{tuple(int(v) for v in k.split(",")): s["flag"] for k, s in (plan_of(i).get("secret_switches") or {}).items()}
                   for i in range(len(floors))]   # (each floor's secret switches, pressed once: Orange 5.7's island caves)
        flips = {f for f in press if f} | {f for s in secrets for f in s.values()}
        duels = {f: names for f, (area, names) in (getattr(story, "TRAINER_FLAGS", None) or {}).items() if area == self.area_key}   # (a door that opens once these trainers are beaten: the Hideout's B4F)
        bars, opened, soft, swing = [], [], [], []   # (each floor's barred tiles as they stand now: a floor last seen before you had the key keeps its doors drawn shut)
        for i in range(len(floors)):
            plan, shut, gone, wait, turn = plan_of(i), set(), set(), {}, []
            pushed = {sw["flag"]: sw for sw in plan.get("boulder_switches") or []}
            for bar in plan.get("barred", []):
                if bar.get("when") and not self.npc_shown(bar["when"]):   # (a bar only while its "when" holds, as the walk
                    continue                                                #  reads it: Route 21's "the ship has flown away"; 11-25)
                if bar.get("when") and not (bar.get("until") or bar.get("item") or bar.get("flag")):
                    shut.update(tuple(t) for t in bar.get("tiles", []))
                    continue
                u = bar.get("until") if isinstance(bar.get("until"), dict) else {}
                fc = str(u.get("flag_condition") or "").split()
                if len(u) == 1 and fc and fc[-1] in flips:  # (a gate a statue switch swings: shut or open by how the switch stands)
                    turn.append((frozenset(tuple(t) for t in bar.get("tiles", [])), fc[-1], len(fc) == 2))
                    continue
                met = story.inventory.get(bar["item"], 0) > 0 if bar.get("item") else \
                    self._until_met(bar["until"]) if bar.get("until") else bool(story.story_flags.get(bar.get("flag")))
                (gone if met else shut).update(tuple(t) for t in bar.get("tiles", []))
                sw = pushed.get(u.get("flag_condition"))
                if sw and not met:  # (a rock barrier: down once a boulder sits on its switch)
                    wait.update({tuple(t): sw for t in bar.get("tiles", [])})
                elif not met and u.get("flag_condition") in duels:
                    wait.update({tuple(t): {"trainers": duels[u["flag_condition"]]} for t in bar.get("tiles", [])})
            bars.append(shut)
            opened.append(gone - shut)
            soft.append(wait)
            swing.append(turn)
        gates = {}

        def swung(i, tog):
            """(tiles shut, tiles open) of floor i's swinging gates, with the switches in tog pressed once more."""
            if (i, tog) not in gates:
                shut, free = set(), set()
                for tiles, flag, neg in swing[i]:
                    on = bool(story.story_flags.get(flag)) != (flag in tog)
                    (free if on != neg else shut).update(tiles)
                gates[(i, tog)] = (shut, free - shut)
            return gates[(i, tog)]

        def hard(i, x, y, tog=frozenset()):
            """What stands on a tile that you can't walk through as things are (None: nothing)."""
            fl = floors[i]
            shut, free = swung(i, tog) if swing[i] else ((), ())
            if (x, y) in bars[i] or (x, y) in shut:
                return "bar"
            if not (fl.walkable(x, y) or (x, y) in opened[i] or (x, y) in free or str(fl.decor.get((x, y), "")).split(":")[0] in clears):
                return "boulder" if str(fl.decor.get((x, y), "")).startswith("boulder:") else "wall"
            m = fl.mover_at(x, y)
            if m is not None and m.kind not in ("trainer", "wild"):
                return "mover"
            return "boss" if fl.exits.get((x, y)) == "BOSS" else None

        def ok(i, x, y, tog):
            fl = floors[i]
            if not fl.inside(x, y):
                return False
            if (i, x, y) in goals:
                return True
            if (x, y) in cracks[i][1] and not (bike and plan_of(i).get("cycling")):   # (on foot a crack gives way: only the fall below)
                return False
            kind = hard(i, x, y, tog)
            if kind in (None, "boss"):
                return True
            if not loose:
                return False
            return kind == "mover" or (kind == "boulder" and strength) or \
                (kind == "bar" and (x, y) in soft[i] and (strength or "trainers" in soft[i][(x, y)]))

        stops = [{tuple(t) for t in (plan_of(i).get("stops") or [])} for i in range(len(floors))]
        thin = [(int((plan_of(i).get("thin_ice") or {}).get("to", -1)), {tuple(int(v) for v in k.split(",")) for k in (plan_of(i).get("thin_ice") or {}).get("tiles", [])})
                for i in range(len(floors))]
        cracks = [(int((plan_of(i).get("cracked") or {}).get("to", -1)), {tuple(int(v) for v in k.split(",")) for k in (plan_of(i).get("cracked") or {}).get("tiles", [])})
                  for i in range(len(floors))]   # (Sky Pillar's cracked floors: stepped onto, a fall to the floor below, the same spot; 11-24)   # (FireRed's thin ice: crossed once; stepped on again, a drop to the floor below: 11-17)

        def _can(c):   # (a lift panel's "requires": items and flags, as the route's own conditions)
            c = str(c)
            return story.inventory.get(c[9:], 0) > 0 if c.startswith("has_item:") else bool(story.story_flags.get(c))
        _opts = {o.get("text"): o for o in self.area_data.get("route_menu", [])}
        panels = []   # (each floor's lift panels: {tile: [(floor, x, y) the car stops at]} - FireRed's Silph Co. and Hideout lifts, 11-23)
        for i in range(len(floors)):
            pan = {}
            for k, ev in (plan_of(i).get("sign_events") or {}).items():
                ev = _opts.get(ev) if isinstance(ev, str) else ev
                el = ((ev or {}).get("event") or {}).get("elevator") if isinstance(ev, dict) else None
                if isinstance(el, dict) and el.get("area") == self.area_key and all(_can(c) for c in (ev.get("event") or {}).get("requires", [])):
                    pan[tuple(int(v) for v in k.split(","))] = [(int(f[1]), int(f[2][0]), int(f[2][1]), str(f[0])) for f in el.get("floors", [])
                                                                 if isinstance(f[1], int) and len(f) > 2 and f[1] != i and 0 <= f[1] < len(floors)]
            panels.append(pan)
        rides = {}   # (a node reached by riding a lift: the panel pressed for it)

        _puller = self.game.story_manager.inventory.get("WHIRLPULLER", 0) > 0   # (Orange 5.7: through flowing whirlpools, _whirl_pull)
        pulls = [({tuple(t) for t in (plan_of(i).get("whirl") or ())} if _puller else set()) for i in range(len(floors))]

        def slide(i, x, y, tog, dx, dy):
            """Where a step from (x, y) ends: over a ledge, or on a spin tile or ice you're carried on (the Rocket
            Hideout's maze). None: no step that way."""
            fl, at, seen = floors[i], (x + dx, y + dy), set()
            if str(fl.decor.get(at, "")) == "ledge:%d,%d" % (dx, dy):  # (a ledge, from its high side: you land beyond it)
                over = (at[0] + dx, at[1] + dy)
                return (i, *over, tog) if fl.inside(*over) and hard(i, *over, tog) is None else None
            if not ok(i, *at, tog):
                return None
            if fl.tile(*at) == core.SURF and fl.tile(x, y) != core.SURF and not surf:
                return None
            cur, ice = getattr(fl, "current", {}) or {}, getattr(fl, "ice", ()) or ()
            wh = pulls[i]
            while at not in seen and at not in fl.exits and at not in stops[i]:
                seen.add(at)
                d = ((dx, dy) if at in wh else None) or cur.get(at) or ((dx, dy) if at in ice else None)   # (the Whirlpuller's pull: straight on)
                if not d:
                    break
                nxt = (at[0] + d[0], at[1] + d[1])
                if not ok(i, *nxt, tog):
                    break
                at, (dx, dy) = nxt, d
            return (i, *at, tog)

        bike = story.inventory.get("BICYCLE", 0) > 0
        from src.dungeon import art as _art

        def ramp_lands(i, x, y, tog):
            """Off a bike ramp beside you, ridden its way: both landings (normal gear and top gear) where clear."""
            out, fl = [], floors[i]
            for dx, dy in core.DIRS:
                at = (x + dx, y + dy)
                if bike and str(fl.decor.get(at, "")) == "ramp:%d,%d" % (dx, dy):
                    for k in _art.RAMP_JUMP:
                        land = (at[0] + dx * k, at[1] + dy * k)
                        if fl.inside(*land) and hard(i, *land, tog) is None:
                            out.append((i, *land, tog))
            return out

        def beside(i, spot, tog):
            """Where you stand, come out of a passage at spot: as the game puts you (core.Run._beside). A wild Pokemon
            that happens to stand there now doesn't count: it will have wandered off by the time you get there."""
            fl = floors[i]

            def taken(x, y):
                m = fl.mover_at(x, y)
                return (x, y) in fl.exits or (x, y) in fl.items or (x, y) in fl.tm_spots or (m is not None and m.kind != "wild")
            t = next(((spot[0] + dx, spot[1] + dy) for dx, dy in core.beside_order(fl, spot)
                      if not taken(spot[0] + dx, spot[1] + dy)), fl.start)
            return [(i, t[0], t[1], tog)]

        def ladders(i, kind):
            return sorted((s for s, v in floors[i].exits.items() if v == kind), key=lambda s: (s[1], s[0]))

        def onward(i, x, y, tog):  # (a passage on this tile: where you come out: ladders pair up in reading order, or by the floor's own "ladders")
            t = floors[i].exits.get((x, y))
            if t == core.STAIRS and i + 1 < len(floors):
                mine, far, order = ladders(i, core.STAIRS), ladders(i + 1, core.STAIRS_UP), plan_of(i).get("ladders")
                nth = mine.index((x, y))
                nth = order[nth] if order and nth < len(order) else nth
                return beside(i + 1, far[nth] if nth < len(far) else far[0], tog) if far else []
            if t == core.STAIRS_UP and i > 0:
                mine, far, order = ladders(i, core.STAIRS_UP), ladders(i - 1, core.STAIRS), plan_of(i - 1).get("ladders")
                nth = mine.index((x, y))
                nth = order.index(nth) if order and nth in order else nth
                return beside(i - 1, far[nth] if nth < len(far) else far[0], tog) if far else []
            if isinstance(t, str) and t.startswith("WARP:"):
                f2, x2, y2 = (int(v) for v in t.split(":")[1:4])
                if 0 <= f2 < len(floors):
                    fl = floors[f2]
                    if t.endswith(":fall") and (x2, y2) not in fl.exits and fl.walkable(x2, y2):
                        return [(f2, x2, y2, tog)]   # (a hole: onto that very spot)
                    return beside(f2, (x2, y2), tog)
            return []

        def statue(i, x, y):
            """The statue switch beside a tile, or None."""
            if not press[i]:
                return None
            return next(((x + dx, y + dy) for dx, dy in core.DIRS if floors[i].decor.get((x + dx, y + dy)) == "statue"), None)

        _diver = story.inventory.get("HM_DIVE", 0) > 0 or story.inventory.get("SCUBA_GEAR", 0) > 0
        dives = {}   # (a node reached by Dive or by coming up: (the tile you do it on, "Dive" / "Surface"); 11-24, Hoenn)
        _lay = self.run.recipe.get("layout") or []
        lay = lambda j: _lay[j] if j < len(_lay) and isinstance(_lay[j], dict) else {}   # (the Dive keys live in the recipe's layout, as dive_here reads them)

        def dive_to(i, x, y):
            """Down from deep sea at (x, y), or up from the seabed's sunlit floor: (floor, x, y) where you come out, as
            dive_here / surface_here put you. None: no Dive here."""
            plan = lay(i)
            up_free = plan.get("surface") is not None and not lay(plan["surface"]).get("dive_links") if plan.get("surface") is not None and 0 <= plan["surface"] < len(_lay) else False
            if not _diver or ((x, y) not in (getattr(floors[i], "deep", None) or ()) and not up_free):
                return None   # (Dive only on deep sea; up from a seabed's sunlit floor - or anywhere with open sea above, on a seabed without links, as surface_here)
            if plan.get("dive") is not None and not plan.get("dive_at") and 0 <= plan["dive"] < len(floors):
                to, below = plan["dive"], floors[plan["dive"]]
                spot = (x, y)
                if plan.get("dive_links"):
                    spot = self._linked_spot(plan["dive_links"], "up", "down", (x, y),
                                             lambda a, b: (a, b) in below.deep and below.walkable(a, b))
                return (to, *spot) if spot and below.walkable(*spot) else None
            if plan.get("surface") is not None and 0 <= plan["surface"] < len(floors):
                to, above = plan["surface"], floors[plan["surface"]]
                links = lay(to).get("dive_links")
                spot = self._linked_spot(links, "down", "up", (x, y), lambda a, b: (a, b) in above.deep and above.tile(a, b) == core.SURF
                                         and (a, b) not in above.exits) if links else (x, y)
                return (to, *spot) if spot and above.tile(*spot) == core.SURF and spot not in above.exits else None
            return None

        first = (*start, frozenset())
        prev, q, passed = {first: None}, deque([first]), set()
        while q:
            cur = q.popleft()
            if cur[:3] in goals:
                goal = cur
                break
            i, x, y, tog = cur
            through = cur != first and (x, y) in floors[i].exits and not (loose and floors[i].exits[(x, y)] == "BOSS")   # (stairs or a pad: on through it)
            nxt = onward(i, x, y, tog) if through else [slide(i, x, y, tog, dx, dy) for dx, dy in core.DIRS] + ramp_lands(i, x, y, tog)
            if not through and thin[i][1]:   # (onto a thin-ice tile beside you, once more: down to the floor below, the same spot)
                to = thin[i][0]
                for dx, dy in core.DIRS:
                    t2 = (x + dx, y + dy)
                    if t2 in thin[i][1] and 0 <= to < len(floors) and floors[to].walkable(*t2):
                        nxt.append((to, t2[0], t2[1], tog))
            if not through and cracks[i][1]:   # (onto a cracked tile beside you from a stop: down to the floor below, the same spot)
                to = cracks[i][0]
                for dx, dy in core.DIRS:
                    t2 = (x + dx, y + dy)
                    if t2 in cracks[i][1] and 0 <= to < len(floors):
                        land = (min(t2[0], floors[to].w - 2), min(t2[1], floors[to].h - 2))
                        if floors[to].walkable(*land):
                            nxt.append((to, land[0], land[1], tog))
            if not through and _diver:   # (Dive down from deep sea, or up from the seabed's sunlit floor)
                d2 = dive_to(i, x, y)
                if d2 is not None:
                    n2 = (*d2, tog)
                    if n2 not in prev:
                        dives[n2] = ((x, y), "Dive" if lay(i).get("dive") is not None else "Surface")
                        nxt.append(n2)
            if not through and panels[i]:   # (a lift panel beside you: ride to any floor it serves, onto the car's spot there)
                for dx, dy in core.DIRS:
                    for f2, x2, y2, lab in panels[i].get((x + dx, y + dy), ()):
                        n2 = (f2, x2, y2, tog)
                        if n2 not in prev:
                            rides[n2] = ((x + dx, y + dy), lab)
                            nxt.append(n2)
            if not through and statue(i, x, y) is not None:  # (press it: every gate of its flag swings)
                nxt.append((i, x, y, tog ^ {press[i]}))
            if not through and secrets[i]:   # (a secret switch beside you, not yet pressed: press it once)
                for dx, dy in core.DIRS:
                    sf = secrets[i].get((x + dx, y + dy))
                    if sf and sf not in tog and not story.story_flags.get(sf):
                        nxt.append((i, x, y, tog | {sf}))
            for n in nxt:
                if n is not None and not through and n[0] == i == self.run.index and self._level_edge((x, y), (n[1], n[2])):
                    continue   # (no route off one level onto another: dungeon_live._level_edge)
                if n is not None and not through and n[0] == i and self._height_edge((x, y), (n[1], n[2]), i):
                    continue   # (nor up or down a Gen 3 cliff: _height_edge)
                if n is not None and n not in prev:
                    prev[n] = cur
                    if through:
                        passed.add(cur)
                    q.append(n)
        if reach:   # (asked only how far you can get: every tile, over every floor)
            return {n[:3] for n in prev}
        if goal is None:
            return None
        path, c = [], goal
        while c is not None:
            path.append(c)
            c = prev[c]
        path.reverse()
        if loose:   # (who or what stands across the way: the way to the first of them)
            for node in path[1:]:
                kind = None if node[:3] in goals else hard(*node)
                if kind is None:
                    continue
                i, x, y, _tog = node
                if kind == "bar":
                    sw = soft[i].get((x, y)) or {}
                    if sw.get("trainers"):  # (the guards whose defeat opens it: the nearest still standing)
                        guards = frozenset((j, m.x, m.y) for j, fl in enumerate(floors) for m in fl.movers if m.kind == "trainer"
                                           and isinstance(m.payload, tuple) and ((m.payload[1] or {}).get("spot_name") or (m.payload[1] or {}).get("name")) in sw["trainers"])
                        return self._step_route(start, guards, "Battle") if guards else None
                    rocks = frozenset((i, bx, by) for bx, by in sw.get("boulders", []) if str(floors[i].decor.get((bx, by), "")).startswith("boulder:"))
                    return self._step_route(start, rocks, "Boulder") if rocks else None
                m = floors[i].mover_at(x, y)
                name = "Boulder" if kind == "boulder" else (self.area_data.get("area_boss") or {}).get("name") or "In the way" if kind == "boss" \
                    else (m.payload.get("text") if m is not None and isinstance(m.payload, dict) else None) or "In the way"
                return self._step_route(start, node[:3], name)
            return None
        for a, b in zip(path, path[1:]):  # (the first thing to do on the way: a statue to press, the stairs or pad to take)
            if a[3] != b[3]:
                sf = next(iter(a[3] ^ b[3]))
                spot = next((t for t, f in secrets[a[0]].items() if f == sf and abs(t[0] - a[1]) + abs(t[1] - a[2]) == 1), None) \
                    or statue(*a[:3])
                return (spot, "Switch") if a[0] == self.run.index else None
            if a in passed and prev.get(b) == a:
                return ((a[1], a[2]), "To " + self._floor_name(b[0]) if b[0] != a[0] else "Warp") if a[0] == self.run.index else None
            if b[0] != a[0] and dives.get(b) and prev.get(b) == a:   # (Dive / come up: the tile to do it on)
                return (dives[b][0], dives[b][1]) if a[0] == self.run.index else None
            if b[0] != a[0] and a not in passed and rides.get(b) and prev.get(b) == a:   # (a lift ride: its panel, and the floor to pick)
                if a[0] != self.run.index:
                    return None
                self._lift_plan = b[0]
                return (rides[b][0], "Lift to " + rides[b][1])
            if b[0] != a[0] and a not in passed and (b[1], b[2]) in cracks[a[0]][1]:   # (a drop through a cracked floor: stop on it)
                return ((b[1], b[2]), "Cracked floor: stop on it") if a[0] == self.run.index else None
            if b[0] != a[0] and a not in passed:   # (a drop through thin ice: the tile to step onto, again)
                if a[0] != self.run.index:
                    return None
                if (b[1], b[2]) == tuple(self.run.player):   # (standing on it, cracked: off it, then back on)
                    return ((a[1], a[2]), "Step off the cracked ice")
                cracked = (self.area_key, a[0], (b[1], b[2])) in self.__dict__.get("_ice_cracked", ())
                return ((b[1], b[2]), "Cracked ice: step on" if cracked else "Thin ice")
        return ((goal[1], goal[2]), label) if goal[0] == self.run.index else None

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
        from src.world import itemfinder as _ifd   # (the Dowsing MCHN's screen while it's on, 11-21)
        if _ifd.dowsing_on(story) and hasattr(self, "run"):
            _m = self.run.recipe.get("art") or {}
            _m = (_m["floors"][self.run.index] if self.run.index < len(_m["floors"]) else {}) if _m.get("floors") else _m
            _ifd.draw_dowsing(screen, pygame.Rect(view.x + 12, view.bottom - 112, 132, 100), _ifd.dowse(story, _m.get("hidden"), tuple(self.run.player),
                              lambda x, y: f"hidden_{self.area_key}_{self.run.index}_{x}_{y}"), fonts)
        name = self.area_data.get("route_name", self.area_key.replace("_", " ").title())
        floor_txt = f"  {self._floor_name(self.run.index)}" if self.run.n_floors > 1 and not name.endswith(self._floor_name(self.run.index)) else ""   # (a floor named as the place itself, the Sewers': once, 11-21; or as its last word, Goldenrod Tunnel's "Tunnel", 11-22)
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
        if getattr(self, "sign", None) and self.mode == "MAP":   # (this region's game's sign: src/vfx/area_changes.py)
            self.sign.draw(screen, map_view(self.game))
        if self.banner > 0 and self.mode == "MAP":
            _fn = self._floor_name(self.run.index)
            if " / " in _fn and self.zones:   # (a floor of several areas: the one you're in, not all of them in a row running off
                _fn = self._zone_name(self._zone_index(self.run.index, *self.run.player))   # the screen: the Safari Zone, 11-22)
            word = theme.pokemon_word(self.area_data.get("route_name", "")) + \
                (f"  {_fn}" if self.run.n_floors > 1 and not self.area_data.get("route_name", "").endswith(_fn) else "")
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
