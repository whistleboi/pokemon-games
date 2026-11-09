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
from src.pokemon.data import Pokemon
from src.states.overworld.common import _trainer_sprite, travel_label
from src.states.overworld.route import PlayState
from src.states.overworld.overworld_battle import OverworldBattles
from src.ui import theme
from src.utils import Utils
from src.world import levels

TILE = 56
STEP_FRAMES = 6          # frames a step takes (the walk animation)
MATH_SECONDS = 30
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
FIGURE_ACTIONS = ("BOSS", "EVENT", "NPC", "HOENN_EVENT", "DAYCARE", "BERRY", "CAMP", "REST", "WEATHER_DIRECTOR",
                  "SNAG", "MAX_RAID", "DIVE", "GAME_CORNER", "BUG_CONTEST")
DECOR_C = {"slot": ((200, 60, 70), (250, 230, 120)), "counter": ((150, 100, 60), (204, 156, 100))}
FACING_ROW = {(0, 1): 0, (-1, 0): 1, (1, 0): 2, (0, -1): 3}  # a sheet's rows: down, left, right, up

# The Bug-Catching Contest: its balls and turns, prizes for 1st, 2nd, 3rd (and the rest), how a catch scores
CONTEST_BALLS, CONTEST_TURNS = 20, 150
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
        out["floors"] = len(parts)
        out["exit_floors"] = {t: i for i, f in enumerate(m["floors"]) for t in f.get("exits", {}).values()}
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
            if c == "!":  # a sign: read it (sign:<its number>)
                ch = chr(0x2460 + signs[(x, y)])
                legend[ch] = {"decor": f"sign:{signs[(x, y)]}"}
                out.append(ch)
            elif c == "X" and standers:
                ch = chr(0x2700 + len(standers))
                legend[ch] = {"figure": f"trainer:{standers.pop(0)}"}
                out.append(ch)
            elif c == "N" and people:  # someone standing: a route option's figure, by its text
                ch = chr(0x2500 + len(people))
                legend[ch] = {"figure": people.pop(0)}
                out.append(ch)
            elif c == "D":  # a door: a way out (the building's own, or a gatehouse's), else walked into
                letter = doors.get((x, y))
                target = exits.get(letter) or (exits.get("D") if kinds.get(letter) == "gate" else None)
                ch = chr(0x2600 + len(legend))
                legend[ch] = {"exit": target} if target else {"decor": f"door:{kinds.get(letter, 'house')}"}
                out.append(ch)
            elif c in "+-":  # a ladder (a map of floors)
                out.append(c)
            elif c in exits and not c.isupper():  # (a building's letter in exits: only its door leads out)
                out.append(c)
            elif c == '"':
                out.append(",")
            elif c == "o":  # open sea: Surf across it
                out.append("o")
            elif c == "b":  # a boulder: Strength, then the slide puzzle (boulder:<x>,<y>)
                ch = chr(0x2800 + len(legend))
                legend[ch] = {"decor": f"boulder:{x},{y}"}
                out.append(ch)
            elif c in _art.OPEN:
                out.append(".")
            elif c == "~":
                out.append("~")
            elif c == "T":
                out.append("#")  # (a tree: Headbutt works on it)
            else:
                out.append({"#": "F", "k": "F", "i": "F", "r": "R", "q": "R", "l": "R", "h": "R", "m": "R", "g": "R", "j": "R", "y": "R", "z": "R"}.get(c, "B"))
        rows.append("".join(out))
    legend.update({c: {"exit": t} for c, t in exits.items() if not c.isupper()})
    for c in "wu":  # (a way out across the sea: you surf onto it)
        if c in exits:
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
            if self.per_floor > 1:  # a wide floor: the areas side by side
                w, h = recipe.get("size", (40, 26))
                recipe["size"] = [w * self.per_floor, h]
        self.recipe = recipe
        n = max(1, int(recipe.get("floors", 1)))
        exits_by_floor, start = None, 0
        if recipe.get("exit_floors") and entrance in recipe["exit_floors"]:  # (our map of floors: in by its floor)
            start = recipe["exit_floors"][entrance]
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

        pool = self.area_data.get("trainer_pool", [])
        cabins = set((self.recipe.get("art") or {}).get("cabin_trainers", []))  # (behind their doors: the S.S. Anne)
        trainers = [(i, t) for i, t in enumerate(pool) if not story.is_trainer_defeated(self.area_key, i) and i not in cabins]
        spots = [s for s in self.recipe.get("tm_spots", []) if not story.story_flags.get(f"dungeon_tm_{s}")]
        loot = self.recipe.get("loot") or {}
        self.placed = []  # the route's buttons standing on the map as figures
        figures = [(self._figure_floor(item, n), item) for item in self._figure_items()]
        self.placed = [item for _f, item in figures]
        self.run = core.Run(self.recipe, random.Random(), entrance=entrance, forwards=forwards,
                            make_wild=self._make_wild, trainers=trainers,
                            loot_for=self._floor_loot(loot), tm_spots=spots, figures=figures,
                            floor_of=lambda t: self._floor_of(t, None), exits_by_floor=exits_by_floor,
                            start_floor=start)

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
        floors = dict(self.recipe.get("figure_floors") or {}, **((self.recipe.get("art") or {}).get("figure_floors") or {}))
        on = (floors.get(item.get("text"), floors.get(item.get("name")))) if isinstance(item, dict) else None
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
        boss_in_way = any((self._gate(t) or ("",))[0] == "boss" for t in getattr(self, "exit_items", {}))
        for item in self.area_data.get("route_menu", []):
            if item.get("action") not in FIGURE_ACTIONS or item.get("door"):
                continue  # (a house's option is through its door, not someone standing about)
            if boss_in_way and item.get("action") == "BOSS":
                continue  # (it sleeps across the way out: see _gate)
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
            if rematch or self._check_route_condition(item.get("condition"), left, item):
                out.append(item)
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
        for item in [i for i in self.placed if not any(i is j for j in now)]:
            self.run.drop_figure(item)
        for item in [i for i in now if not any(i is j for j in self.placed)]:
            self.run.add_figure(self._figure_floor(item, self.run.n_floors), item)
        self.placed = now

    def _use_figure(self, mover):
        self.walk_goal = None
        item = mover.payload
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
        if self._beside("decor:slot"):
            return "PLAY SLOTS", self.play_slots
        if self._beside("water") and self._menu_item("FISH"):
            return "FISH", self.fish_here
        if self._beside("tree") and self._menu_item("HEADBUTT"):
            return "HEADBUTT", self.headbutt_here
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
        pool = self._get_wild_pool(self.area_data)
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
                if self.game.story_manager.is_trainer_defeated(self.area_key, idx):
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
        return self.mode == "MAP" and self.anim == 0 and not self.dialogue_box.visible

    def _can_surf(self):
        return self.game.story_manager.inventory.get("HM_SURF", 0) > 0

    def _on_surf(self, t=None):
        f = self.run.floor
        return f.tile(*(t or self.run.player)) == core.SURF

    def step(self, dx, dy):
        if not self._ready():
            return
        from src.coop import roster
        if roster.host_tethered(self.game, (self.run.player[0] + dx, self.run.player[1] + dy)):
            self.walk_goal = None
            self.flash("Your team fainted: stay close to a friend.")
            return
        self.facing = (dx, dy)
        self._clear_boulders()  # (one already pushed aside isn't in the way)
        before = self.run.player
        to = (before[0] + dx, before[1] + dy)
        if self._on_surf(to) and not self._on_surf(before) and not self._can_surf():
            self.walk_goal = None  # (the open sea: Surf it, Routes 19-21)
            self.flash("The sea is deep. You need Surf to cross it!", 100)
            return
        events = self.run.step(dx, dy)
        if self.run.player != before:
            self.anim_from, self.anim = before, STEP_FRAMES
            self.partner_from, self.partner = self.partner, before  # it steps where you were
            self.steps += 1
            self._note_area()
            self._contest_tick()
        self._handle(events)

    def wait_turn(self):
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

    def _floor_name(self, index):
        """A floor's name: its zone's ("Area 1 (East)", "B2F"; on a wide floor, its areas'), else 1F, 2F..."""
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
        item = self.exit_items.get(target)
        if not item:
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
        else:
            self._battle_wild(self.encounter)

    def _start_math(self):
        self.mode = "MATH"
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught, num_options=3)
        self.math_timer = MATH_SECONDS * FPS

    def _answer(self, idx):
        if self.mode != "MATH" or idx >= len(self.options):
            return
        story = self.game.story_manager
        p = self.encounter.payload
        if self.contest:  # a Sport Ball (the contest's own)
            ball = "SPORT_BALL"
            self.contest["balls"] -= 1
        else:
            ball = catching.selected(story)
            catching.use(story, ball)
        self._thrown_ball = ball
        right = self.options[idx] == self.correct_ans
        shiny_pass = bool(p.is_shiny) and not right  # a shiny is caught even on a wrong answer (as on the route)
        self.was_shiny_override = shiny_pass
        if right or shiny_pass:
            quick = (MATH_SECONDS * FPS - self.math_timer) < QUICK_SECONDS * FPS
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
        if source == "HONEY" and not (self._can_catch() and self._get_wild_pool(self.area_data)
                                      and self.game.story_manager.inventory.get("HONEY", 0) > 0):
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
        else:
            self.scent_floor = self.run.index
            first = "A sweet scent drifted through the air..."
        self.walk_goal = None

        def begin():
            self.mode = "CATCH"
            self.is_progression_paused = False
            self.pending_wild_encounters = 0
            self.input_delay = 20
            self.trigger_wild_encounter()  # the route's three-Pokemon catch, then show_progression_menu
        self.say([first, "Wild Pokemon were drawn in!"], then=begin)

    # ---------------------------------------------------------------- input
    def _buttons(self):
        """The map's own buttons (bottom right): (rect, label, colour, action, enabled, small text)."""
        w, h = self.game.width, self.game.height
        buttons = [
            (self._qp_button_rect(), theme.pokemon_word("POKEMON"), theme.POKEMON,
             self._qp_toggle, True, None),  # (its list opens above it: src/states/overworld/overworld_battle.py)
            (pygame.Rect(w - 146, h - 162, 126, 70), theme.pokemon_word("POKEDEX"), theme.BAG,
             self._open_pokedex, True, None),
            (pygame.Rect(w - 280, h - 80, 126, 58), "HONEY", (226, 170, 40), self.use_scent,
             bool(self._scent_source()) if hasattr(self, "run") else False, self._honey_note()),
            (pygame.Rect(w - 146, h - 80, 126, 58), "WAIT", theme.RUN, self.wait_turn, True, "a turn"),
        ]
        mega = self._map_mega_button() if hasattr(self, "run") and not self.contest else None
        if mega:  # (as in Legends: Z-A: Mega Evolve the Pokemon following you, right here)
            buttons.append(mega)
        act = self._act_here() if hasattr(self, "run") else None
        if act:  # beside water or a tree
            sub = {"FISH": "the water here", "HEADBUTT": "this tree", "TALK": "the clerk",
                   "PLAY SLOTS": "this machine"}.get(act[0])
            buttons.append((pygame.Rect(w - 280, h - 244, 260, 70), act[0], (232, 132, 40), act[1], True, sub))
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
            W, H = self.game.width, self.game.height
            mw, mh = self.run.floor.w * TILE, self.run.floor.h * TILE
            cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
            cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return cx, cy

    def _tile_at(self, pos):
        cx, cy = self._camera()
        ox, oy = self.game.width / 2 - cx, self.game.height / 2 - cy
        return int((pos[0] - ox) // TILE), int((pos[1] - oy) // TILE)

    KEYS = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}

    def handle_events(self, events):
        if self.mode == "CATCH":
            return super().handle_events(events)
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
            tx, ty = self._tile_at(e.pos)
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

    def _clear_boulders(self):
        """Boulders pushed aside stay out of the way (a story flag each)."""
        f = self.run.floor
        flags = self.game.story_manager.story_flags
        for t, what in list(f.decor.items()):
            if str(what).startswith("boulder:") and flags.get(self._boulder_flag(t)):
                del f.decor[t]
                f.tiles[t[1]][t[0]] = core.FLOOR

    def _boulder(self, t):
        """Walked into a boulder (Jordan, 11-07): with Strength, push it aside by solving the slide puzzle."""
        story = self.game.story_manager
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
        if what.startswith("boulder:"):  # a boulder in the way: Strength, then the slide puzzle
            self._boulder(t)
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
        if self.mode == "MAP":
            self._contest_check()
            self._follow_hold()
            if self.walk_goal and self._ready():
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
                self._battle_trainer(self.encounter)

    # ---------------------------------------------------------------- drawing
    def _render_floor(self):
        f = self.run.floor
        if self.run.recipe.get("art"):  # one of our own maps, in its own art
            from src.dungeon import art as _art
            m = self.run.recipe["art"]
            grid = m["floors"][self.run.index]["art"] if m.get("floors") else m["art"]
            self._floor_surf = _art.surface(grid, m.get("buildings", {}), TILE, m.get("roofs"), m.get("theme"))
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

    def _sprite(self, key, make):
        if key not in self._sprites:
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

        def sheet():
            base = os.path.join(self.game.assets.assets_dir, "dungeon", "followers")
            ids = list(dict.fromkeys([int(pokemon.id), pid]))  # (a form's own sheet first: Paldean Tauros)
            form = str(getattr(pokemon, "form", "normal") or "normal").lower()
            names = ([f"{pid}_{form}"] if form != "normal" else []) + [str(i) for i in ids]  # (71_mega, 1017_water_mask)
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
        data = self._sprite(("follower_sheet", int(pokemon.id), form_key, shiny), sheet)
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
        return self._sprite(("follower", int(pokemon.id), form_key, shiny, row, frame), make)

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

    def _player_img(self):
        """You on the map: your trainer's Journeys overworld sprite (yours, else a boy's or a girl's),
        facing the way you go, its feet moving while you step."""
        players = sprite_map(self.game).get("players") or {}
        char = str(getattr(self.game, "player_character", "") or "red").lower()
        sheet = players.get(char) or players.get("female" if char in players.get("girls", []) else "male")
        if not sheet:
            return None
        frame = (1 + 2 * (self.steps % 2)) if self.anim > STEP_FRAMES // 2 else 0
        return self._sheet_frame(sheet, self.facing, frame=frame)

    def _figure_img(self, item):
        """A story figure's look: its own sheet ("AREA:TEXT" in dungeon_sprites.json), a boss's Pokemon
        (its overworld sprite, else its party icon), or a townsperson."""
        sm = sprite_map(self.game)
        spec = (sm.get("figures") or {}).get(f"{self.area_key}:{item.get('text')}") or {}
        if spec.get("item"):
            return self._item_img(spec["item"], 40) or self._sheet_frame("Object ball.png", col=0, height=36)
        if item.get("action") == "ARRIVAL":
            return self._trainer_img(item["event"].get("trainer") or {})
        if item.get("action") == "MAX_RAID":  # the den's next raid Pokemon, jumbo (Jordan, 11-06)
            img = self._raid_img()
            if img is not None:
                return img
        pid = spec.get("pokemon")
        if pid is None and item.get("action") == "BOSS":
            pid = (item.get("boss") or self.area_data.get("area_boss") or {}).get("id")
        if pid is not None:
            ow = (sm.get("pokemon") or {}).get(str(pid))
            if ow:
                return self._sheet_frame(ow[0], (0, 1), col=ow[1], height=TILE + 26)
            from src.minigames.base import icon
            return icon(self.game, int(pid), TILE + 10)
        return self._sheet_frame(spec.get("sheet") or sm.get("townsperson") or "NPC 17.png")

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

    def _trainer_img(self, info, facing=(0, 1)):
        name = info.get("sprite") or "rival.png"
        sheet = (sprite_map(self.game).get("trainers") or {}).get(name)
        if sheet:  # its Pokemon Journeys overworld sprite, looking the way it faces
            return self._sheet_frame(sheet, facing)

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
        screen.fill((10, 14, 24))  # (the fog's colour: the unknown edge of the map)
        if self._floor_index != self.run.index or self._floor_surf is None:
            self._render_floor()
        cx, cy = self._camera()
        ox, oy = int(W / 2 - cx), int(H / 2 - cy)
        screen.blit(self._floor_surf, (ox, oy))
        x0, y0 = max(0, -ox // TILE - 1), max(0, -oy // TILE - 1)
        x1, y1 = min(f.w, (W - ox) // TILE + 2), min(f.h, (H - oy) // TILE + 2)
        fonts = self.game.assets.fonts

        def at(x, y):
            return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

        # things lying about (in tiles you've seen)
        real = self.run.recipe.get("image") or self.run.recipe.get("art")
        signs = []  # (drawn over the map's things, last)
        if real:  # a real map's ways out: the road itself, and one sign over it saying where it goes
            ways = {}
            for (x, y), target in f.exits.items():
                ways.setdefault(target, []).append((x, y))
            for target, tiles in ways.items():
                tiles.sort()
                x, y = tiles[len(tiles) // 2]
                r = at(x, y)
                name = (self._floor_name(self.run.index + (1 if target == core.STAIRS else -1))
                        if target in (core.STAIRS, core.STAIRS_UP) else self._area_name(target))
                tag = fonts["caption"].render(theme.pokemon_word(str(name).upper()), True, (255, 255, 255))
                pill = tag.get_rect(center=r.center).inflate(12, 6)  # (on the road itself, out of your way)
                if not screen.get_rect().inflate(120, 120).colliderect(pill):
                    continue  # (off screen: no sign piling up at the edge)
                pill.clamp_ip(screen.get_rect().inflate(-8, -8))
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
            if str(what).startswith("boulder:") and (x, y) in f.seen and x0 <= x < x1 and y0 <= y < y1:
                r = at(x, y)
                img = self._sheet_frame("Object boulder.png", col=0, height=TILE - 4)
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
        # wild Pokemon and trainers you can see
        for m in f.movers:
            if not self.run.visible(m.x, m.y) or m is self._ow_foe:
                continue
            r = at(m.x, m.y)
            if m.kind == "wild":
                img = self._icon(m.payload, TILE, flip=(m.x < self.run.player[0]), facing=getattr(m, "facing", None))
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom + 4)))
                if m.payload.is_shiny:
                    pygame.draw.circle(screen, (255, 230, 90), (r.right - 8, r.y + 8), 5)
                if m.alert:
                    theme.shadow_text(screen, "!", fonts["label"], r.right - 6, r.y - 18, color=(220, 60, 50))
            elif m.kind == "figure":
                self._fit_jumbo(m)
                img = self._figure_img(m.payload)
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
                img = self._trainer_img(m.payload[1], m.facing)
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
        # you, your trainer, with your lead Pokemon a step behind
        k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 1
        lead = self.lead()
        pr = pygame.Rect(0, 0, TILE, TILE)
        (fx0, fy0), (tx0, ty0) = (self.anim_from if self.anim > 0 else self.run.player), self.run.player
        pr.topleft = (int(ox + (fx0 + (tx0 - fx0) * k) * TILE), int(oy + (fy0 + (ty0 - fy0) * k) * TILE))  # (you, mid-step)
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
        elif me is not None:
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
        elif lead:  # (no trainer sprite: your lead Pokemon walks for you)
            img = self._icon(lead, TILE + 8, flip=(self.facing[0] > 0), facing=self.facing)
            drawn.append((pr.bottom, img, img.get_rect(center=(pr.centerx, pr.centery - 4))))
        for _b, img, rect in sorted(drawn, key=lambda t: t[0]):
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

        for pill, tag in signs:  # where the ways out go
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
            screen.blit(tag, tag.get_rect(center=pill.center))
        if self._backdrop:  # (only the map: an OVERWORLD-style battle is drawn over it)
            return
        if self.mode == "MAP":
            self._draw_guide(screen, at)
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
        spot = next((t for t, target in f.exits.items() if target == hop), None)
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
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        t = pygame.time.get_ticks()
        r = at(gx, gy)
        gold, dark = (255, 214, 64), (60, 40, 10)
        on_screen = r.right > 0 and r.left < W and r.bottom > 90 and r.top < H - 20
        if on_screen:
            pulse = 4 + int(3 * (1 + math.sin(t / 160)))
            pygame.draw.rect(screen, gold, r.inflate(pulse, pulse), 4, border_radius=10)
            bob = int(6 * math.sin(t / 180))
            is_exit = (gx, gy) in self.run.floor.exits  # (its sign names it already: the arrow goes above)
            tip = (r.centerx, r.top - (44 if is_exit else 10) + bob)
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
        cx, cy = W / 2, H / 2
        dx, dy = r.centerx - cx, r.centery - cy
        n = math.hypot(dx, dy) or 1
        ux, uy = dx / n, dy / n
        room_x, room_y = W / 2 - 70, H / 2 - 110
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
        pill.clamp_ip(pygame.Rect(8, 90, W - 16, H - 100))
        pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
        pygame.draw.rect(screen, gold, pill, 2, border_radius=8)
        screen.blit(tag, tag.get_rect(center=pill.center))

    def _journal_mission(self):
        """The Journal's tracked mission (looked up once a second), or None."""
        from src.world import guide
        now = pygame.time.get_ticks() // 1000
        if getattr(self, "_journal_at", None) != now:
            self._journal_at, self._journal = now, guide.tracked_mission(self.game)
        return self._journal

    def _journal_rect(self):
        """The Journal's tracked mission, kept on screen under MENU (Jordan, 11-07), or None."""
        if self.contest or not self._journal_mission():
            return None
        return pygame.Rect(20, 126, 380, 84)

    def _minimap_rect(self):
        f = self.run.floor
        s = 4
        jr = self._journal_rect()
        top = jr.bottom + 10 if jr else 128  # (under MENU, and the Journal's mission)
        return pygame.Rect(20, top, f.w * s + 8, f.h * s + 8)

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
            if len(lines) == 2:
                break
        if line and len(lines) < 2:
            lines.append(line)
        elif len(lines) == 2 and len(" ".join(lines).split()) < len(words):
            last = lines[1]
            while small.size(last + "...")[0] > r.w - 24 and len(last) > 3:
                last = last[:-1]
            lines[1] = last.rstrip() + "..."
        for k, text in enumerate(lines):
            screen.blit(small.render(text, True, (235, 235, 245)), (r.x + 12, r.y + 34 + k * 22))

    def _draw_hud(self, screen):
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        story = self.game.story_manager
        bar = pygame.Rect(210, 12, W - 420, 64)
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
        ball = "SPORT_BALL" if self.contest else catching.selected(story)
        bimg = self._item_img(ball, 30) or self._ball_img(30)
        bx = bar.right - 380
        screen.blit(bimg, (bx, bar.centery - 15))
        count = self.contest["balls"] if self.contest else catching.owned(story, ball)
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
        s = 4
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
        pygame.draw.circle(screen, (255, 255, 255), (mm.x + 4 + px * s + 2, mm.y + 4 + py * s + 2), 3)
        # the buttons
        if self.mode == "MAP" and not self.dialogue_box.visible:
            mouse = pygame.mouse.get_pos()
            for rect, label, color, _a, ok, sub in self._buttons():
                theme.command_button(screen, rect, label, fonts["caption"], color if ok else theme.BACK,
                                     hover=rect.collidepoint(mouse), small=fonts["small"], sub=sub or None)
        # a found item, and the area's name on arrival
        if self.toast_timer > 0:
            t = fonts["label"].render(self.toast, True, (255, 255, 255))
            r = t.get_rect(midtop=(W // 2, 92)).inflate(28, 14)
            pygame.draw.rect(screen, (30, 36, 58), r, border_radius=12)
            pygame.draw.rect(screen, theme.BAG, r, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=r.center))
        if self.banner > 0 and self.mode == "MAP":
            word = theme.pokemon_word(self.area_data.get("route_name", "")) + \
                (f"  {self._floor_name(self.run.index)}" if self.run.n_floors > 1 else "")
            t = fonts["big"].render(word, True, (255, 255, 255))
            r = t.get_rect(center=(W // 2, int(H * 0.3))).inflate(60, 24)
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
            k = max(0.0, self.math_timer / (MATH_SECONDS * FPS))
            track = pygame.Rect(W // 2 - 300, int(H * 0.66) + 126, 600, 14)
            pygame.draw.rect(screen, (60, 64, 80), track, border_radius=7)
            pygame.draw.rect(screen, theme.POKEMON if k > 0.33 else theme.FIGHT,
                             (track.x, track.y, max(8, int(track.w * k)), track.h), border_radius=7)
