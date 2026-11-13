"""Walkable towns (Jordan, 11-06): a town you walk around, on its Pokemon Journeys V18 map, like the route
maps but wide open (no fog, no narrow halls). The town screen underneath is the same (CityState: its
people, its events, the Center, the Mart, the Gym), only reached by walking:
- walk into a building's door: what's inside (the Pokemon Center, the Mart, the Gym, Oak's Lab, your home);
- the town's other people stand about (a tap, or walk into them, to talk);
- walk off the map's edge: the route that side (its conditions and all);
- no TRAVEL button (Jordan, 11-10: you walk now): boats are a harbour's door, Fly is in MENU.
The maps come from dev/builders/build_walk_towns.py (assets/walk_towns.json and assets/walk_towns/).
CityState(game) is this when the town has a map (its __new__); headless, only with game.walk_towns = True."""
import json
import os
from collections import deque

import pygame

from src.config import FPS
from src.ui import theme
from src.states.overworld.town import CityState
from src.states.overworld import dungeon as dn

TILE, STEP = dn.TILE, dn.STEP_FRAMES
DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))
KEYS = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
        pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}
LABELS = {"steven": "STEVEN'S HOUSE", "space": "SPACE CENTER", "cozmo": "PROF. COZMO'S HOUSE", "wally": "WALLY'S UNCLE'S HOUSE", "contest": "CONTEST HALL", "shipyard": "STERN'S SHIPYARD", "market": "SLATEPORT MARKET", "devon": "DEVON CORP.", "center": "POKEMON CENTER", "mart": "POKE MART", "gym": "GYM", "lab": "LAB", "home": "HOME",
          "school": "TRAINER SCHOOL", "rival": "RIVAL'S HOUSE", "assistant": "ASSISTANT'S HOUSE", "poketch": "POKETCH CO.", "gts": "GLOBAL TERMINAL", "tv": "JUBILIFE TV", "condo": "CONDOMINIUMS", "flower": "FLOWER SHOP", "library": "CANALAVE LIBRARY", "poffin": "POFFIN HOUSE", "ruins": "CELESTIC RUINS", "elder": "ELDER'S HOUSE", "lighthouse": "VISTA LIGHTHOUSE", "amity": "AMITY SQUARE", "museum": "MUSEUM", "bike": "BIKE SHOP", "mayor": "MAYOR'S HOUSE", "cycle": "YOUR BIKE", "realgam": "REALGAM TOWER",
          "harbor": "HARBOR", "fanclub": "FAN CLUB", "radio": "RADIO TOWER", "ptower": "POKEMON TOWER",
          "fuji": "MR. FUJI'S HOUSE", "dept": "DEPT. STORE", "mansion": "CELADON MANSION", "hotel": "CELADON HOTEL",
          "game corner": "GAME CORNER", "prize corner": "PRIZE CORNER", "tower": "POKEMON TOWER", "mansion": "MANSION", "silph": "SILPH CO.",
          "warden": "WARDEN'S HOUSE", "brother": "FISHING HOUSE", "safari": "SAFARI ZONE",
          "fossil": "POKEMON LAB", "copycat": "COPYCAT'S HOUSE", "dojo": "FIGHTING DOJO", "station": "MAGNET TRAIN",
          "league": "ELITE FOUR", "johto": "TO JOHTO", "sprout": "SPROUT TOWER", "kurt": "KURT'S HOUSE", "ruins": "THE RUINS", "kabuto": "KABUTO CHAMBER", "omanyte": "OMANYTE CHAMBER",
          "aerodactyl": "AERODACTYL CHAMBER", "hooh": "HO-OH CHAMBER",
          "flower": "FLOWER SHOP", "bill": "BILL'S HOUSE",
          "burned": "BURNED TOWER", "bellchime": "BELLCHIME TRAIL", "theater": "DANCE THEATER", "pharmacy": "PHARMACY", "souvenir": "SOUVENIR SHOP", "leaguegate": "VICTORY ROAD", "dome": "POKEATHLON DOME"}
_DATA = {}


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


def data(game):
    if "all" not in _DATA:
        path = os.path.join(game.assets.assets_dir or "assets", "walk_towns.json")
        try:
            with open(path, encoding="utf-8") as f:
                _DATA["all"] = json.load(f)
        except (OSError, ValueError):
            _DATA["all"] = {}
    return _DATA["all"]


def custom(game):
    """Our own maps (assets/town_maps.json, dev/builders/build_town_maps.py): towns and routes."""
    if "all" not in _CUSTOM:
        path = os.path.join(game.assets.assets_dir or "assets", "town_maps.json")
        try:
            with open(path, encoding="utf-8") as f:
                _CUSTOM["all"] = json.load(f)
        except (OSError, ValueError):
            _CUSTOM["all"] = {}
    return _CUSTOM["all"]


_CUSTOM = {}


def available(game, key):
    if not getattr(game, "walk_towns", os.environ.get("SDL_VIDEODRIVER") != "dummy"):
        return False
    return bool(key) and (key in custom(game) or key in data(game))


def option_kind(opt):
    """Which building a town option is in (None: someone standing outside)."""
    if opt.get("door"):  # (said in the town's data: which house it's in)
        return opt["door"]
    a = str(opt.get("action") or "").upper()
    t = str(opt.get("text") or "").lower()
    if a in ("HEAL", "CENTER") or "pokemon center" in t:
        return "center"
    if a == "SHOP" or "mart" in t or "dept" in t:
        return "mart"
    if a == "GYM":
        return "gym"
    if a == "GAMECORNER" or "game corner" in t:
        return "game corner"
    if "mansion" in t:
        return "mansion"
    if "tower" in t:
        return "tower"
    if "rocket" in t or "silph" in t:
        return "silph"
    if "lab" in t or "oak" in t:
        return "lab"
    if "mom" in t:
        return "home"
    return None


class WalkTownState(CityState):
    HONEY_PACK = dn.DungeonState.HONEY_PACK
    # (the route map's own drawing: your trainer, the Pokemon following you, townsfolk)
    _sprite = dn.DungeonState._sprite
    _sheet_frame = dn.DungeonState._sheet_frame
    _player_img = dn.DungeonState._player_img
    _follower_img = dn.DungeonState._follower_img
    _icon = dn.DungeonState._icon
    _trainer_scale = dn.DungeonState._trainer_scale
    _jumbo = dn.DungeonState._jumbo
    _figure_img = dn.DungeonState._figure_img
    _stand_in_img = dn.DungeonState._stand_in_img
    _actor_img = dn.DungeonState._actor_img
    _trainer_img = dn.DungeonState._trainer_img
    _item_img = dn.DungeonState._item_img
    # (the Journal's mission under MENU, and the gold marker toward it: as on the route maps, Jordan 11-10)
    _journal_mission = dn.DungeonState._journal_mission
    _journal_rect = dn.DungeonState._journal_rect
    _draw_journal = dn.DungeonState._draw_journal
    _exit_label = dn.DungeonState._exit_label

    def __init__(self, game):
        super().__init__(game)
        self._sprites = {}
        self.facing, self.anim, self.steps = (0, 1), 0, 0
        self.walk_goal = None
        self.toast, self.toast_timer, self.banner = "", 0, 120
        self.signs, self.water_exits, self.locked = {}, set(), {}
        mine = custom(game).get(self.area_key)
        self.own_map = bool(mine)
        self.town_map, self.room = mine, None
        if mine:  # our own map (the way forward: Jordan, 11-06)
            # (back from a screen or a battle begun inside one of its buildings: inside it again)
            was, room = getattr(game, "walk_town_pos", None), getattr(game, "walk_town_room", None)
            if was and room and was[0] == room[0] == self.area_key and room[1] in (mine.get("rooms") or {}):
                self.room = room[1]
            elif not (was and was[0] == self.area_key):  # (a place made of rooms, come into from outside: the room whose way out leads back there)
                came = getattr(game.story_manager, "last_area_key", None)
                if came and came not in (mine.get("exits") or {}).values():
                    self.room = next((n for n, r in (mine.get("rooms") or {}).items() if came in (r.get("exits") or {}).values()), None)
            self._from_art(mine["rooms"][self.room] if self.room else mine)
        else:  # a Pokemon Journeys town picture (the Kanto pilot)
            self.walk = data(game)[self.area_key]
            self.rows = self.walk["rows"]
            self.w, self.h = self.walk["w"], self.walk["h"]
            self.map_img = self._map_image()
            self._place_things()
        self._arrive()

    def _from_art(self, m):
        from src.dungeon import art
        grid = m["art"]
        # what stands in the way till you have the move for it, as on the routes: small trees (Cut), cracked rocks (Rock Smash), muddy slopes (the Bicycle)
        _inv = self.game.story_manager.inventory
        self._cleared = "".join(c for c, item in (("2", "HM_CUT"), ("0", "HM_ROCK_SMASH"), ("7", "BICYCLE")) if _inv.get(item, 0) > 0)
        for _c in self._cleared:
            grid = [row.replace(_c, ".") for row in grid]
        self.h, self.w = len(grid), len(grid[0])
        self.grid = grid  # (kept for its ledges: hopped over one way, as on the routes)
        kinds = m.get("buildings", {})
        doors = art.doors(grid)
        self.doors, self.exits, self.people = {}, {}, {}
        for (x, y), letter in doors.items():  # (a building's door can be a way out: {"Q": "DIGGLETT_CAVE"})
            target = m.get("exits", {}).get(letter) or (m.get("exits", {}).get("D") if kinds.get(letter) == "gate" else None)
            if target:
                self.exits[(x, y)] = target
            else:
                self.doors[(x, y)] = kinds.get(letter, "house")
        deep = art.SEA_CHARS if m.get("surf") else ""  # (a map with "surf": its sea is crossed with Surf, as on the routes; else a town's sea is walked like its ground, as before)
        self.rows = ["".join("D" if (x, y) in doors else "$" if c == "$" else "o" if c in deep else "2" if c == "2" else ("." if c in art.OPEN and (not m.get("walk_on") or c in m["walk_on"]) else "#") for x, c in enumerate(row))
                     for y, row in enumerate(grid)]
        self.locked = dict(m.get("locked", {}))  # (a shut door's own words: the Radio Tower with no power)
        # a warp pad (tile 1 with the map's "links" {"x,y": [floor, x, y]}, as on the routes): step on it and you stand on its far pad
        self.links = {tuple(int(v) for v in k.split(",")): (to[1], to[2]) for k, to in (m.get("links") or {}).items()}
        self.stops = {tuple(t) for t in m.get("stops", [])}  # (where a spin tile's slide ends: Viridian Gym's stop tiles)
        # someone standing in the way till the story moves on (the map's "barred", as on the routes: Snowpoint Temple's guard)
        self._bar_list = m.get("barred", [])
        self._edge_to = m.get("edge_to") or {}  # (out by this edge tile: in at its partner on the next map, Emerald's own connection)
        self.barred = {tuple(t): bar for bar in m.get("barred", []) if not self._bar_met(bar) and self._bar_here(bar) for t in bar.get("tiles", [])}
        self.sign_scenes = {tuple(int(v) for v in k.split(",")): s for k, s in (m.get("sign_scenes") or {}).items()}  # (reading this sign starts a scene)
        # a bridge in town has two levels, like a route's: its deck, crossed along its length, and the street under it, crossed along its width
        self.bridge = {(x, y): art.BRIDGES[c] for y, row in enumerate(grid) for x, c in enumerate(row) if c in art.BRIDGES}
        self.deck = True
        names = list(m.get("people", []))
        options = {o.get("text"): o for o in self.area_data.get("explore_options", [])}
        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c in art.EXIT_CHARS and c in m.get("exits", {}):
                    self.exits[(x, y)] = m["exits"][c]
                    if c in "wu" or art.at_sea(grid, x, y):
                        self.water_exits.add((x, y))
                elif c == "N" and names:
                    who = names.pop(0)  # (a town option by its text, or an option of its own: Oak at the gap)
                    opt = who if isinstance(who, dict) else None if isinstance(who, list) else options.get(who)
                    if isinstance(who, str) and who.startswith("door:"):  # (whoever runs a building from inside it: everything its door would offer; a harbour's sailor and the boats)
                        kind = who[5:]
                        opt = {"any": [o for o in self.area_data.get("explore_options", []) if option_kind(o) == kind]
                               + [dict(o, action="TRAVEL") for o in self.area_data.get("travel_options", []) if o.get("door") == kind]}
                    if isinstance(who, list):  # (someone with several things to say or do, by the story: the first of these options showing now)
                        opt = {"any": [w if isinstance(w, dict) else options[w] for w in who if isinstance(w, dict) or w in options]}
                    if opt:
                        self.people[(x, y)] = opt
        for spot, lines in zip(art.signs(grid), m.get("signs", [])):
            self.signs[spot] = lines
        for (x, y) in self.exits:  # (a way out is walked onto)
            self.rows[y] = self.rows[y][:x] + "." + self.rows[y][x + 1:]
        cache = self.game.__dict__.setdefault("_walk_town_imgs", {})
        _ck = self.area_key + ("|" + self._cleared if self._cleared else "")  # (redrawn once a tree is cut or a rock broken)
        if getattr(self, "room", None):
            _ck += "|room:" + self.room  # (a room inside one of its buildings: its own picture)
        if _ck not in cache:
            cache.clear()
            cache[_ck] = art.surface(grid, kinds, TILE, m.get("roofs"), m.get("theme"))
        self.map_img = cache[_ck]
        self.overheads = [(o, *art.overhead(o, TILE)) for o in m.get("overheads", [])]
        self._npc_init(m)

    # ---------------------------------------------------------------- people who move (src/dungeon/npc.py)
    def _npc_init(self, m):
        """Each person's way of moving (the map's "moves", by their spot) and the map's story scenes."""
        from src.dungeon import npc
        self.motions = {home: npc.Motion(home, npc.spec_at(m.get("moves"), home), seed=self.area_key) for home in self.people}
        self.scenes = npc.Scenes(m.get("scenes"), self)
        self._scene_lock = False
        # (an arrival event a scene acts out in its place: Norman outside the Gym instead of the old text)
        self._scene_instead = {s["instead_of"] for s in self.scenes.list if s.get("instead_of") and self.scenes.pending(s)}

    def _home_at(self, spot):
        """The spot a person was placed on (their key in self.people), from where they stand now."""
        for home, mo in getattr(self, "motions", {}).items():
            if mo.pos == tuple(spot) and not mo.gone:
                return home
        return tuple(spot)

    def _npc_free(self, t, mover=None):
        """Can someone step onto t now: plain open ground, nobody there or arriving, not you, not a door, sign or way out."""
        x, y = t
        if not (0 <= x < self.w and 0 <= y < self.h) or self.rows[y][x] != "." or t in self.exits or t in self.doors or t in self.signs \
                or t in getattr(self, "barred", {}) or (getattr(self, "grid", None) and self.grid[y][x] in "_()"):
            return False
        if t == tuple(self.player) or (self.anim > 0 and t == tuple(self.anim_from)) or t == tuple(getattr(self, "partner", ())):
            return False
        return not any(o is not mover and not o.gone and t in (o.pos, o.frm) for o in self.motions.values())

    def _npc_tick(self):
        if not getattr(self, "motions", None):
            return
        shown = set(self._people())
        for home, mo in self.motions.items():
            if mo.pos in shown or mo.moving() or mo.path:
                mo.tick(lambda t, mo=mo: self._npc_free(t, mo))
        if self.scenes.busy():
            self.scenes.tick()
        elif self.anim == 0 and not self._busy():
            self.scenes.check()

    # (the scene runner's host: src/dungeon/npc.py Scenes)
    def npc_person(self, who):
        for home, opt in self.people.items():
            texts = [o.get("text") for o in opt.get("any", [opt])]
            if who in texts and self._shown(opt):
                return self.motions.get(home)
        return None

    def npc_player(self):
        return tuple(self.player)

    def npc_passable(self, t, m):
        return self._npc_free(t, m)

    def npc_shown(self, scene):
        return self._shown(scene)

    def npc_flag(self, name):
        self.game.story_manager.story_flags[name] = True
        # (a scene that moves the story on: stand-ins come and go at once, the Shroomish back beside its girl)
        self.barred = {tuple(t): bar for bar in getattr(self, "_bar_list", []) if not self._bar_met(bar) and self._bar_here(bar) for t in bar.get("tiles", [])}

    def npc_flagged(self, name):
        return bool(self.game.story_manager.story_flags.get(name))

    def npc_say(self, lines, then):
        from src.states.overworld.common import _fill_names

        def done():
            self.end_npc_interaction()
            then()
        self.show_message([_fill_names(self.game, line) for line in lines], callback=done)

    def npc_run(self, who):
        home = next((h for h, o in self.people.items() if who in [p.get("text") for p in o.get("any", [o])]), None)
        if home is not None and home in self.motions:
            self._talk(self.motions[home].pos)

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
        _run_story_event(self, key, self._check_menu_condition, show)
        if not shown:  # (a battle or a scene of its own began instead: the scene carries on once you're back)
            then()

    def npc_heal(self):
        for p in self.game.story_manager.player_team:
            if p:
                p.heal_full()
        if getattr(self.game.assets, "heal_sfx", None):
            self.game.assets.heal_sfx.play()

    def npc_sheet(self, token):
        return dn.scene_sheet(self.game, token)

    def npc_follow(self, t):
        t = tuple(t)
        if abs(t[0] - self.player[0]) + abs(t[1] - self.player[1]) != 1:
            return
        self.facing = (t[0] - self.player[0], t[1] - self.player[1])
        self.anim_from, self.anim = self.player, STEP
        self.partner_from, self.partner = self.partner, self.player
        self.player = t
        self._remember()

    def npc_lock(self, on):
        self._scene_lock = on
        if on:
            self.walk_goal = None

    def npc_open(self, t):
        return 0 <= t[0] < self.w and 0 <= t[1] < self.h and self.rows[t[1]][t[0]] == "." and t not in self.signs

    def npc_face_player(self, spot):
        self.facing = (max(-1, min(1, spot[0] - self.player[0])), max(-1, min(1, spot[1] - self.player[1])))

    def npc_edge(self, m):
        edge = [(x, y) for (x, y) in self.exits if not (x, y) in self.water_exits]
        return min(edge, key=lambda t: abs(t[0] - m.pos[0]) + abs(t[1] - m.pos[1]), default=None)

    # ---------------------------------------------------------------- the map
    def _map_image(self):
        cache = self.game.__dict__.setdefault("_walk_town_imgs", {})
        if self.area_key not in cache:
            cache.clear()  # (one town at a time)
            img = pygame.image.load(os.path.join(self.game.assets.assets_dir or "assets", "walk_towns",
                                                 f"{self.area_key}.png")).convert()
            cache[self.area_key] = pygame.transform.scale(img, (self.w * TILE, self.h * TILE))
        return cache[self.area_key]

    def _options(self):
        """The town's EXPLORE options shown right now (their conditions met), as the menu would list them."""
        from src.states.overworld.pokecenter import center_entrance, combined_center
        options = self.area_data.get("explore_options", [])
        if combined_center(self.game):
            options = center_entrance(options)
        return [o for o in options if self._shown(o)]

    def _bar_here(self, bar):
        """A stand-in that only turns up once the story says so ("when": its conditions, as an option's): the Shroomish back with its girl."""
        return not bar.get("when") or self._shown(bar["when"])

    def _bar_met(self, bar):
        story = self.game.story_manager
        if bar.get("until_any"):  # (gone once any of these is true: the Museum queue, once you've seen Dock or cleared the Museum)
            return any(self._shown(u) for u in bar["until_any"])
        if bar.get("item"):
            return story.inventory.get(bar["item"], 0) > 0
        if bar.get("until"):
            u = bar["until"]
            if u.get("area_cleared"):
                pool = (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(u["area_cleared"]) or {}).get("trainer_pool") or []
                if len(story.defeated_trainers.get(u["area_cleared"], set())) < len(pool):
                    return False
            return self._shown(u)
        return bool(story.story_flags.get(bar.get("flag")))

    def _shown(self, opt):
        if "any" in opt:
            return any(self._shown(o) for o in opt["any"])
        story = self.game.story_manager
        fc = opt.get("flag_condition")
        if fc:
            parts = fc.split()
            if len(parts) == 2 and parts[0] == "not" and story.story_flags.get(parts[1]):
                return False
            if len(parts) == 1 and not story.story_flags.get(parts[0]):
                return False
        if opt.get("item_condition") and story.inventory.get(opt["item_condition"], 0) <= 0:
            return False
        return not opt.get("condition") or self._check_menu_condition(opt["condition"])

    def _place_things(self):
        """Doors (the buildings' options), the ways out (the edges), and the people standing about."""
        self.doors = {}  # (x, y) -> kind
        self.exits = {}  # (x, y) -> area key
        for d in self.walk.get("doors", []):
            x, y = d["x"], d["y"]
            if not (0 <= x < self.w and 0 <= y < self.h):
                continue
            side = "north" if y == 0 else "south" if y == self.h - 1 else "west" if x == 0 else \
                "east" if x == self.w - 1 else None
            if side and side in self.walk.get("edges", {}):  # (a warp on the edge: the way out that side)
                self.exits[(x, y)] = self.walk["edges"][side]
            else:
                self.doors[(x, y)] = d.get("kind", "house")
        for side, target in self.walk.get("edges", {}).items():
            for t in self._edge_tiles(side):
                self.exits[t] = target
        # the first home door is yours (Mom's), the first lab Oak's
        self.people = {}  # (x, y) -> option
        kinds = set(self.doors.values())
        loose = [o for o in self.area_data.get("explore_options", []) if option_kind(o) not in kinds]
        for opt, spot in zip(loose, self._free_spots(len(loose))):
            self.people[spot] = opt
        self._npc_init({})

    def _edge_tiles(self, side):
        cells = {"north": [(x, 0) for x in range(self.w)], "south": [(x, self.h - 1) for x in range(self.w)],
                 "west": [(0, y) for y in range(self.h)], "east": [(self.w - 1, y) for y in range(self.h)]}[side]
        return [c for c in cells if self.rows[c[1]][c[0]] == "."]

    def _free_spots(self, n):
        """n tiles for people to stand on: open ground near the middle, apart, off the paths to doors."""
        cx, cy = self.w / 2, self.h / 2
        near_door = {(x + dx, y + dy) for (x, y) in self.doors for dx in (-1, 0, 1) for dy in (0, 1, 2)}
        ok = [(x, y) for y in range(2, self.h - 2) for x in range(2, self.w - 2)
              if self.rows[y][x] == "." and (x, y) not in near_door
              and all(self.rows[y + dy][x + dx] == "." for dx, dy in DIRS)]
        ok.sort(key=lambda t: (t[0] - cx) ** 2 + (t[1] - cy) ** 2)
        out = []
        for t in ok:
            if len(out) >= n:
                break
            if all(abs(t[0] - o[0]) + abs(t[1] - o[1]) >= 4 for o in out):
                out.append(t)
        return out

    def _arrive(self):
        """Where you stand: as you left it (back from a building or a battle), else at the edge you came
        in by, else outside the Pokemon Center (or in the middle)."""
        story = self.game.story_manager
        was = getattr(self.game, "walk_town_pos", None)
        if was and was[0] == self.area_key and self._open(was[1]):
            self.player, self.facing = tuple(was[1]), tuple(was[2])
        else:
            came = getattr(story, "last_area_key", None)  # (a loaded save hasn't come from anywhere)
            edge = [t for t, target in self.exits.items() if target == came]
            if edge:
                land = [t for t in edge if t not in self.water_exits]  # (a place entered by land and by sea: by land, unless you came in at a matching tile)
                t = (land or edge)[len(land or edge) // 2]
                used = getattr(self.game, "walk_town_exit", None)  # (several ways between two places: in by the matching one: Mauville's four staircases)
                if used and used[0] == came and used[2] == len(edge):
                    t = edge[used[1]]
                at_edge = getattr(self.game, "arrive_edge", None)  # (out by an edge tile there: in at its own partner here)
                self.game.arrive_edge = None
                if at_edge and at_edge[0] == came and at_edge[1] == self.area_key:  # (its partner, or the nearest of these to it)
                    p2 = tuple(at_edge[2])
                    t = min(edge, key=lambda e: abs(e[0] - p2[0]) + abs(e[1] - p2[1]))
                self.game.walk_town_exit = None
                inward = next(((t[0] + dx, t[1] + dy) for dx, dy in DIRS if self._open((t[0] + dx, t[1] + dy))
                               and (t[0] + dx, t[1] + dy) not in self.exits), t)
                self.player = inward
                self.facing = (inward[0] - t[0], inward[1] - t[1]) if inward != t else (0, 1)
            else:
                via = next((o.get("door") for o in self.area_data.get("travel_options", []) if o.get("door")
                            and (o.get("target_area") or o.get("target")) == came), None)  # (back from a place you reach through a door here: at that door: the Reception Gate's great door)
                own = [t for t, k in self.doors.items() if came and (k == via or k.upper().replace(" ", "_") in came)]
                own = sorted(own, key=lambda t: (self.doors[t] != via, -t[1]))
                door = (own[0] if own else None) or next((t for t, k in self.doors.items() if k == "center"), None) or \
                    next((t for t, k in self.doors.items() if k == "home"), None)  # (out of a building that's an area of its own, the Game Corner: at its own door)
                spot = (door[0], door[1] + 1) if door else (self.w // 2, self.h // 2)
                self.player = spot if self._open(spot) else self._nearest_open(spot)
                self.facing = (0, 1)
        self.anim_from = self.partner = self.partner_from = self.player
        self._remember()

    def _people(self):
        """The people standing about now (each option's conditions met)."""
        mos = getattr(self, "motions", {})
        out = {}
        for spot, opt in self.people.items():
            if not self._shown(opt) or (spot in mos and mos[spot].gone):
                continue
            out[mos[spot].pos if spot in mos else spot] = next(o for o in opt["any"] if self._shown(o)) if "any" in opt else opt
        return out

    def _open(self, t):
        x, y = t
        return 0 <= x < self.w and 0 <= y < self.h and (self.rows[y][x] == "." or tuple(t) in self.exits or (self.rows[y][x] == "$" and self._has_waterfall())
                                                       or (self.rows[y][x] == "o" and self._has("HM_SURF")) or (self.rows[y][x] == "2" and self._has("HM_CUT")))             and tuple(t) not in self._people() and tuple(t) not in getattr(self, "barred", {})

    def _has(self, item):
        return self.game.story_manager.inventory.get(item, 0) > 0

    def _has_waterfall(self):
        return self.game.story_manager.inventory.get("HM_WATERFALL", 0) > 0

    def _nearest_open(self, t):
        best = min(((x, y) for y in range(self.h) for x in range(self.w) if self._open((x, y)) and (x, y) not in self.exits),
                   key=lambda c: abs(c[0] - t[0]) + abs(c[1] - t[1]), default=(0, 0))
        return best

    def _remember(self):
        self.game.walk_town_pos = (self.area_key, self.player, self.facing)
        self.game.walk_town_room = (self.area_key, self.room) if getattr(self, "room", None) else None

    # ---------------------------------------------------------------- rooms (Jordan, 11-11: the insides of a town's buildings, walked)
    # A town map's "rooms" {name: a map of its own (art, people, signs, theme "room")} and "inside" {"x,y" of a door: room name}.
    # A room's ways out lead "OUT:x,y" (back outside, below that door) or "ROOM:name" (stairs to another room). The town's
    # options are the same inside: the people standing in a room are its options (the nurse: Heal; the clerk: Shop).
    def _room_for(self, door):
        if getattr(self, "room", None) or not getattr(self, "town_map", None):
            return None
        return (self.town_map.get("inside") or {}).get("%d,%d" % tuple(door))

    def _go(self, room, came):
        """Into a room (or back out to the town: room None), arriving by the way out there that leads back to came."""
        self.room = room
        self.signs, self.water_exits = {}, set()
        self._mini = None
        self.walk_goal = None
        self._from_art(self.town_map["rooms"][room] if room else self.town_map)
        if room is None and came.startswith("OUT:"):  # back outside: below the door you went in by
            x, y = (int(v) for v in came.split(":", 1)[1].split(","))
            spot = (x, y + 1)
            back = not self._open(spot) and self._open((x, y - 1))  # (a back door, on the far side of its building: out above it: Fuchsia's fishing house)
            if back:
                spot = (x, y - 1)
            self.player = spot if self._open(spot) else self._nearest_open(spot)
            self.facing = (0, -1) if back else (0, 1)
        else:
            mats = [t for t, target in self.exits.items() if target == came]
            t = mats[len(mats) // 2] if mats else self._nearest_open((self.w // 2, self.h - 2))
            inward = next(((t[0] + dx, t[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
                           if self._open((t[0] + dx, t[1] + dy)) and (t[0] + dx, t[1] + dy) not in self.exits), t)
            self.player = inward
            self.facing = (inward[0] - t[0], inward[1] - t[1]) if inward != t else (0, -1)
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.player
        self._remember()

    def start(self):
        super().start()
        if self.action_menu in self.game.ui_manager.elements:  # (the map's own buttons instead)
            self.game.ui_manager.elements.remove(self.action_menu)

    # ---------------------------------------------------------------- walking
    def _busy(self):
        return self.npc_active or bool(self.hover_menu_active) or getattr(self, "_scene_lock", False)

    def flash(self, text, frames=90):
        self.toast, self.toast_timer = text, frames

    def step(self, dx, dy):
        if self._busy() or self.anim > 0:
            return
        self.facing = (dx, dy)
        to = (self.player[0] + dx, self.player[1] + dy)
        from src.coop import roster
        if roster.host_tethered(self.game, to):
            self.walk_goal = None
            return self.flash("Your team fainted: stay close to a friend.")
        if roster.world.occupied(self.game, to):
            self.walk_goal = None  # (a friend or their Pokemon is standing there)
            return
        if tuple(to) in getattr(self, "barred", {}):
            self.walk_goal = None
            return self.flash((self.barred[tuple(to)].get("lines") or ["Someone is standing in the way."])[0], 130)
        if to in self.signs:
            self.walk_goal = None
            return self._read(to)
        if to in self._people():
            self.walk_goal = None
            return self._talk(to)
        if getattr(self, "room", None) and 0 <= to[0] < self.w and 0 <= to[1] < self.h and self.grid[to[1]][to[0]] == "m":
            across = (to[0] + dx, to[1] + dy)  # (someone behind a counter: talk across it, as in the original)
            if across in self._people():
                self.walk_goal = None
                return self._talk(across)
            far = (to[0] + 2 * dx, to[1] + 2 * dy)  # (a counter two tiles deep: the nurse stands clear of its top)
            if 0 <= across[1] < self.h and 0 <= across[0] < self.w and self.grid[across[1]][across[0]] == "m" and far in self._people():
                self.walk_goal = None
                return self._talk(far)
        if to in self.doors:
            self.walk_goal = None
            return self._enter(to)
        grid = getattr(self, "grid", None)
        if grid and 0 <= to[0] < self.w and 0 <= to[1] < self.h:
            from src.dungeon import art as _art
            if _art.LEDGES.get(grid[to[1]][to[0]]) == (dx, dy):  # (a ledge, from its high side: hop over it)
                over = (to[0] + dx, to[1] + dy)
                if self._open(over) and over not in self.doors and over not in self.signs:
                    to = over
        if grid and 0 <= to[0] < self.w and 0 <= to[1] < self.h and grid[to[1]][to[0]] in "207":
            self.walk_goal = None
            return self.flash({"2": "A small tree is in the way. CUT could cut it down!", "0": "A cracked rock is in the way. ROCK SMASH could break it!",
                               "7": "A steep, muddy slope. A BICYCLE could ride up it!"}[grid[to[1]][to[0]]], 110)
        if 0 <= to[0] < self.w and 0 <= to[1] < self.h and self.rows[to[1]][to[0]] == "$" and not self._has_waterfall():
            self.walk_goal = None  # (a waterfall in town: Ever Grande's, below the League)
            return self.flash("The water pours down too hard. WATERFALL could climb it!", 110)
        if not self._open(to):
            self.walk_goal = None
            if 0 <= to[0] < self.w and 0 <= to[1] < self.h and self.rows[to[1]][to[0]] in "o2" and to not in self._people():
                self.flash("The water's deep here. You'll need Surf to cross it!" if self.rows[to[1]][to[0]] == "o" else "A small tree is in the way. CUT could clear it!", 110)
            return
        spans = getattr(self, "bridge", None)
        if spans:
            here = tuple(self.player)
            if here in spans and tuple(to) not in spans and ((abs(dx), abs(dy)) == spans[here]) != self.deck:
                self.walk_goal = None  # (off a bridge only the way you came onto it: along its deck, or out from under it)
                return
            if tuple(to) in spans and here not in spans:
                self.deck = (abs(dx), abs(dy)) == spans[tuple(to)]
            elif tuple(to) not in spans:
                self.deck = True
        self.anim_from, self.anim = self.player, STEP
        if grid and 0 <= to[1] < len(grid) and 0 <= to[0] < len(grid[to[1]]) and grid[to[1]][to[0]] in "89":
            self.anim = STEP * 2  # (deep snow, marsh mud: each step takes twice as long)
        self.partner_from, self.partner = self.partner, self.player
        self.player = to
        self.steps += 1
        self._remember()
        if to in self.exits:
            self.walk_goal = None
            self._leave(self.exits[to])
        elif to in getattr(self, "links", {}):  # a warp pad: on to its far pad (no stepping back through by itself)
            self.walk_goal = None
            self.player = self.partner = self.partner_from = self.anim_from = self.links[to]
            self.anim = 0
            self._remember()
        elif grid and grid[to[1]][to[0]] in "3456":  # a spin tile: it carries you its way till something stops you, or a stop tile does
            self.walk_goal = None
            way = {"3": (-1, 0), "4": (1, 0), "5": (0, -1), "6": (0, 1)}
            d, cur = way[grid[to[1]][to[0]]], to
            for _ in range(self.w * self.h):
                nxt = (cur[0] + d[0], cur[1] + d[1])
                if not self._open(nxt) or nxt in self.doors or nxt in self.signs:
                    break
                cur = nxt
                if grid[cur[1]][cur[0]] in way:
                    d = way[grid[cur[1]][cur[0]]]
                elif cur in self.stops or cur in self.exits or cur in self.links:
                    break
            self.player = cur
            self.facing = d
            self._remember()
            if cur in self.exits:
                self._leave(self.exits[cur])

    def _path(self, goal):
        """The steps to goal (a door or a person: up to it), or []."""
        start = self.player
        target = set()
        people = dict(self._people())
        people.update({s: None for s in self.signs})  # (walk up to a sign to read it)
        if goal in self.doors or goal in people:
            target = {(goal[0] + dx, goal[1] + dy) for dx, dy in DIRS}
        elif self._open(goal):
            target = {goal}
        prev, q = {start: None}, deque([start])
        while q:
            cur = q.popleft()
            if cur in target:
                out = []
                while cur != start:
                    out.append(cur)
                    cur = prev[cur]
                return out[::-1] + ([goal] if goal in self.doors or goal in people else [])
            for dx, dy in DIRS:
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt not in prev and self._open(nxt) and (nxt not in self.exits or nxt == goal):
                    prev[nxt] = cur
                    q.append(nxt)
        return []

    # ---------------------------------------------------------------- doors, people, ways out
    def _door_options(self, kind):
        """What's through a door: the town's options of that kind; a harbour's, its boats (the travel options
        marked "door": "harbor", each shown only when you can take it)."""
        opts = [o for o in self._options() if option_kind(o) == kind]
        opts += [dict(o, action="TRAVEL") for o in self.area_data.get("travel_options", [])
                 if o.get("door") == kind and self._shown(o)]
        return opts

    def _enter(self, door):
        kind = self.doors[door]
        inside = self._room_for(door)
        if inside:  # (a building with its inside built: walk in)
            return self._go(inside, "OUT:%d,%d" % tuple(door))
        if kind == "home":  # (the first home is yours; the others aren't open)
            first = min((t for t, k in self.doors.items() if k == "home"), default=None)
            if door != first:
                return self.flash("Nobody seems to be home.")
        opts = self._door_options(kind)
        if not opts:
            if kind in self.locked:
                return self.flash(self.locked[kind])
            if kind == "house":
                return self.flash("The door is locked.")
            if kind in LABELS:
                return self.flash(f"{LABELS[kind].title()}: nothing to do here right now.")
            return self.flash("Nobody seems to be home.")
        if len(opts) == 1:
            cb = self._get_callback_for_option(opts[0])
            if cb:
                cb()
            return
        self._create_hover_menu(opts, None)  # (a building with several things inside: pick one)

    def _read(self, spot):
        sc = getattr(self, "sign_scenes", {}).get(tuple(spot))
        if sc and getattr(self, "scenes", None) and not self.scenes.busy() and self.scenes.pending(sc):  # (something behind the sign)
            self.scenes.start(sc, None)
            return
        return self._read_plain(spot)

    def _read_plain(self, spot):
        from src.states.overworld.common import _fill_names
        self.show_message([_fill_names(self.game, line) for line in self.signs[spot]])

    def _get_callback_for_option(self, opt_data):
        """As the town's, but on the walked map nothing opens a scene of its own (Jordan, 11-12: those are the old map
        style's): the nurse heals your team where you stand and says so from the map."""
        if str(opt_data.get("action") or "").upper() == "HEAL":
            return self._heal_here
        return super()._get_callback_for_option(opt_data)

    def _heal_here(self):
        story = self.game.story_manager
        story.last_center = story.current_area_key
        for p in story.player_team:
            p.heal_full()
        if hasattr(self.game, "music"):
            self.game.music.jingle("pokemon_healed")
        self.show_message(["Welcome to the Pokémon Center!", "We've restored your team to full health."])

    def _talk(self, spot):
        home = self._home_at(spot)
        mo = getattr(self, "motions", {}).get(home)
        if mo is not None:  # (they stop and turn to you)
            if mo.moving():
                return
            mo.path = []
            mo.face(self.player)
            mo.hold = 150
        opt = self.people[home]
        if not self._shown(opt):
            return self.flash("They don't have anything to say right now.")
        if "any" in opt:
            now = [o for o in opt["any"] if self._shown(o)]
            if len(now) > 1:  # (several things to do with them right now: pick one, as at a door)
                return self._create_hover_menu(now, None)
            opt = now[0]
        if getattr(self, "scenes", None) and self.scenes.on_talk(opt.get("text")):  # (a scene of theirs plays instead: the clerk shows you round)
            return
        cb = self._get_callback_for_option(opt)
        if cb:
            cb()

    def _travel_option(self, target):
        return next((o for o in self.area_data.get("travel_options", [])
                     if (o.get("target_area") or o.get("target")) == target), None)

    def _leave(self, target):
        if str(target).startswith("OUT:"):  # (out of a room, back to the town)
            return self._go(None, target)
        if str(target).startswith("ROOM:"):  # (stairs to another room of the building; "ROOM:MAIN" is the place's own first map)
            return self._go(None if target[5:] == "MAIN" else target[5:], "ROOM:" + (self.room or "MAIN"))
        opt = self._travel_option(target)
        if opt is None or not self._shown(opt):
            here = self.player
            self.flash(self.locked.get(target) or ("The water's deep here. You'll need Surf to cross it!"
                       if here in self.water_exits else "You can't go that way yet."))
            return self._step_back()
        cb = self._get_callback_for_option(dict(opt, action="TRAVEL"))
        if not cb:
            return self._step_back()
        from src.coop import travel
        if travel.held(self.game, travel.area_name(self.game, target), lambda: self._leave(target), self._step_back):
            return  # (co-op: the others have a say)
        self.game.walk_town_pos = None  # (next time: in by the way you come)
        same = [t for t, v in self.exits.items() if v == target]
        at = tuple(self.player)
        self.game.walk_town_exit = (self.area_key, same.index(at), len(same)) if at in same else None
        _to = getattr(self, "_edge_to", {}).get(f"{at[0]},{at[1]}")
        self.game.arrive_edge = (self.area_key, target, tuple(_to)) if _to else None
        dn.core.ENTRANCE_INDEX = same.index(at) if at in same and len(same) > 1 else 0  # (the same, into a route or cave)
        dn.core.ENTRANCE_COUNT = len(same) if at in same else 0
        cb()

    def _step_back(self):
        self.player, self.anim = self.anim_from, 0
        self.partner = self.partner_from
        self._remember()

    # ---------------------------------------------------------------- input
    def _buttons(self):
        side = dn.side_buttons(self.game)  # (stacked in the right band, beside the map)
        return [(side[3].move(0, -70).inflate(0, -14).move(0, 7), "BAG", (198, 132, 60), self._open_bag),  # (Jordan, 11-12: the Bag one press away on the map, with the others)
                (side[3], theme.pokemon_word("POKEMON"), theme.POKEMON, self._open_party),
                (side[2], theme.pokemon_word("POKEDEX"), theme.BAG, self._open_pokedex)]

    def _camera(self):
        px, py = self.player
        if self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        W, H = self._view().size
        mw, mh = self.w * TILE, self.h * TILE  # (the map fills its frame: no black past its edges)
        cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
        cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return cx, cy

    def _view(self):
        return dn.map_view(self.game)  # (the map's frame: src/states/overworld/dungeon.py)

    def _origin(self):
        cx, cy = self._camera()
        v = self._view()
        return int(v.centerx - cx), int(v.centery - cy)

    def _tile_at(self, pos):
        ox, oy = self._origin()
        return int((pos[0] - ox) // TILE), int((pos[1] - oy) // TILE)

    def _facing_tile(self):
        return (self.player[0] + self.facing[0], self.player[1] + self.facing[1])

    def handle_events(self, events):
        if self._busy():
            return super().handle_events(events)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in KEYS:
                    self.walk_goal = None
                    self.step(*KEYS[e.key])
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_f):
                    t = self._facing_tile()
                    if t in self.signs:
                        self._read(t)
                    elif t in self._people():
                        self._talk(t)
                    elif t in self.doors:
                        self._enter(t)
                elif e.key == pygame.K_p:
                    self._open_party()
                elif e.key in (pygame.K_ESCAPE, pygame.K_m) and self.hud_buttons:
                    self.hud_buttons[0].callback()  # MENU
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if any(b.rect.collidepoint(e.pos) for b in self.hud_buttons):
                    continue
                jr = self._journal_rect()
                if jr is not None and jr.collidepoint(e.pos):  # (a tap on the mission: the Journal)
                    from src.states.systems.journal import JournalState
                    self.game.change_state(JournalState(self.game, self))
                    return
                hit = next((b for b in self._buttons() if b[0].collidepoint(e.pos)), None)
                if hit:
                    hit[3]()
                    return
                goal = self._tile_at(e.pos)
                if self._minimap_rect().collidepoint(e.pos) or not self._view().collidepoint(e.pos):
                    continue  # (the black round the map: nothing there)
                self.tap_mark = [goal, bool(self._open(goal)) or goal in self.doors or goal in self.signs or goal in self._people(), 12]
                if goal == self.player:
                    continue
                if abs(goal[0] - self.player[0]) + abs(goal[1] - self.player[1]) == 1:
                    self.walk_goal = None
                    self.step(goal[0] - self.player[0], goal[1] - self.player[1])
                elif goal in self.doors or goal in self._people() or goal in self.signs or self._open(goal):
                    self.walk_goal = goal
                self._map_press = True  # (held: it keeps walking toward the finger)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self._map_press = False

    def update(self):
        if self.npc_active:
            return super().update()
        self._npc_tick()
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if self.banner > 0:
            self.banner -= 1
        if self.anim > 0:
            self.anim -= 1
            return
        if not self._busy():  # held down: keep walking (a key), or keep heading for the finger
            way = held_way(KEYS)
            if way:
                self.walk_goal = None
                return self.step(*way)
            at = held_pointer() if getattr(self, "_map_press", False) else None
            if at is None:
                self._map_press = False
            elif self._view().collidepoint(at):
                goal = self._tile_at(at)
                if goal != self.player and (self._open(goal) or goal in self.doors or goal in self._people()):
                    self.walk_goal = goal
        if self.walk_goal and not self._busy():
            path = self._path(self.walk_goal)
            if not path:
                self.walk_goal = None
                return
            nxt = path[0]
            if nxt == self.walk_goal and (nxt in self.doors or nxt in self._people() or nxt in self.signs):
                self.walk_goal = None
            self.step(nxt[0] - self.player[0], nxt[1] - self.player[1])
            if self.player == self.walk_goal:
                self.walk_goal = None

    # ---------------------------------------------------------------- drawing
    def lead(self):
        team = self.game.story_manager.player_team
        return next((p for p in team if p and p.current_hp > 0), team[0] if team else None)

    def draw(self):
        # (Jordan, 11-12: no separate scene for someone you talk to: no other background, no picture sliding in. They speak from the map)
        screen = self.game.screen
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        view = self._view()
        screen.fill(dn.FRAME_BLACK)
        screen.fill((10, 14, 24), view)
        screen.set_clip(view)  # (the map stays in its frame)
        ox, oy = self._origin()
        screen.blit(self.map_img, (ox, oy))

        def at(t):
            return pygame.Rect(ox + t[0] * TILE, oy + t[1] * TILE, TILE, TILE)

        if self.walk_goal:
            theme.tap_marker(screen, at(self.walk_goal))
        if self.tap_mark and self.tap_mark[2] > 0 and self.tap_mark[0] != self.walk_goal:
            theme.tap_marker(screen, at(self.tap_mark[0]), self.tap_mark[1])
            self.tap_mark[2] -= 1
        drawn = []
        people = self._people()
        mos = getattr(self, "motions", {})
        by_pos = {mo.pos: mo for mo in mos.values() if not mo.gone}
        emotes = []
        for spot, opt in people.items():
            mo = by_pos.get(spot)
            img = self._figure_img(opt, mo.facing, mo.frame()) if mo else self._figure_img(opt)
            if mo:  # (mid-step: between the two tiles)
                fx, fy = mo.at()
                r = pygame.Rect(int(ox + fx * TILE), int(oy + fy * TILE), TILE, TILE)
            else:
                r = at(spot)
            if img is not None:
                drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
            if mo and mo.emote > 0:  # (they've noticed you: a "!" over them, drawn after everyone)
                emotes.append((r.centerx - 4, r.y - 34))
        k = 1 - self.anim / STEP if self.anim > 0 else 1
        lead = self.lead()
        me = self._player_img()
        pr = pygame.Rect(0, 0, TILE, TILE)
        fx, fy = self.anim_from
        tx, ty = self.player
        pr.topleft = (int(ox + (fx + (tx - fx) * k) * TILE), int(oy + (fy + (ty - fy) * k) * TILE))
        if lead and self.partner != self.player:
            (ax, ay), (bx, by) = self.partner_from, self.partner
            r = pygame.Rect(int(ox + (ax + (bx - ax) * k) * TILE), int(oy + (ay + (by - ay) * k) * TILE), TILE, TILE)
            way = (tx - bx, ty - by)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            img = self._icon(lead, TILE, flip=(tx > bx), facing=way)
            if img is not None:
                drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
        if me is not None:
            drawn.append((pr.bottom, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
        for _b, img, rect in sorted(drawn, key=lambda t: t[0]):
            screen.blit(img, rect)
        for a in (self.scenes.actors if getattr(self, "scenes", None) else []):  # a scene's cast, walking in and out
            ax, ay = a["m"].at()
            img = self._actor_img(a["sheet"], a["m"].facing, a["m"].frame())
            if img is not None:
                r = pygame.Rect(int(ox + ax * TILE), int(oy + ay * TILE), TILE, TILE)
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
        for ex, ey in emotes:
            theme.shadow_text(screen, "!", fonts["label"], ex, ey, color=(230, 60, 50))
        for _t, _bar in getattr(self, "barred", {}).items():
            _look = str(_bar.get("look") or "person")
            _img = self._stand_in_img(_look, _bar) if _look.startswith(("sheet:", "ow:", "mon:")) else None
            if _img is not None:  # (a real game's own sprite: a boat at the pier, someone in the way)
                screen.blit(_img, _img.get_rect(midbottom=(at(_t).centerx, at(_t).bottom - 2)))
                continue
            from src.dungeon import art
            art.blocker(screen, at(_t), _look)
        if getattr(self, "bridge", None) and not self.deck and tuple(self.player) in self.bridge:  # (passing under a bridge: it goes over your head)
            art.bridge(screen, at(tuple(self.player)), "|" if self.bridge[tuple(self.player)] == (0, 1) else ";")
        for _o, img, (bx, by) in getattr(self, "overheads", []):  # (solid, over you: you walk under it, out of view)
            screen.blit(img, (ox + bx, oy + by))
        # the buildings' names over their doors, who the people are, where the ways out go
        for spot, kind in self.doors.items():
            if kind == "house" or (kind == "home" and spot != min(t for t, k2 in self.doors.items() if k2 == "home")):
                continue
            label = LABELS.get(kind) or next((o.get("text", "") for o in self.area_data.get("explore_options", [])
                                              if o.get("door") == kind), kind).upper()
            self._pill(screen, label, at(spot).centerx, at(spot).y - 6, fonts)
        ways = {}
        for spot, target in self.exits.items():
            ways.setdefault(target, []).append(spot)
        for target, tiles in ways.items():
            tiles.sort()
            t = tiles[len(tiles) // 2]
            name = (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(target) or {}).get("route_name") or target
            if str(target).startswith(("OUT:", "ROOM:")):  # (a room's mat or stairs: no place of their own to name)
                name = "EXIT" if str(target).startswith("OUT:") else "STAIRS"
            self._pill(screen, str(name).upper(), at(t).centerx, at(t).centery + 10, fonts)
        from src.states.overworld.common import _fill_names
        taken = []  # (name tags that would sit on top of one another: the one with something to do is shown: a row of clerks)
        for spot, opt in sorted(people.items(), key=lambda kv: (kv[1].get("action") == "EVENT" and not (kv[1].get("event") or {}).get("battle"), kv[0])):
            self._pill(screen, _fill_names(self.game, opt.get("text", "")).upper()[:28], at(spot).centerx,
                       at(spot).y - 34, fonts, taken)
        if not self._busy():
            self._draw_guide(screen, at)
        screen.set_clip(None)
        dn.draw_frame(screen, view)
        self._draw_hud(screen, fonts)
        if self.hover_menu_active and self.hover_bg_rect:
            pygame.draw.rect(screen, (255, 255, 255), self.hover_bg_rect, border_radius=12)
            pygame.draw.rect(screen, (0, 0, 0), self.hover_bg_rect, 6, border_radius=12)
        if self.npc_active and self.npc_dialogue:
            self.npc_dialogue.draw(screen)
        self.game.ui_manager.draw(screen)

    @staticmethod
    def _pill(screen, text, cx, bottom, fonts, taken=None):
        box = screen.get_clip()  # (the map's frame, while the map is drawn)
        if not (box.x - 60 <= cx <= box.right + 60 and box.y - 40 <= bottom <= box.bottom + 60):
            return  # (off screen: no tag piling up at the edge)
        tag = fonts["caption"].render(theme.pokemon_word(text), True, (255, 255, 255))
        pill = tag.get_rect(midbottom=(cx, bottom)).inflate(12, 6)
        pill.clamp_ip(box.inflate(-8, -8))  # (one at the very edge stays in the frame)
        if taken is not None:
            if pill.collidelist(taken) >= 0:
                return
            taken.append(pill)
        pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
        screen.blit(tag, tag.get_rect(center=pill.center))

    tap_mark = None

    def _mini_scale(self):
        jr = self._journal_rect()
        top = jr.bottom + 10 if jr else 128
        return dn.mini_scale(self.w, self.h, dn.FRAME_LEFT - 32, self.game.height - 24 - top)

    def _minimap_rect(self):
        jr = self._journal_rect()
        s = self._mini_scale()
        return pygame.Rect(16, jr.bottom + 10 if jr else 128, self.w * s + 8, self.h * s + 8)

    # ---------------------------------------------------------------- the way to go
    def _guide_spot(self):
        """(tile, label) for the Journal's tracked mission: a door or person here that does what it needs,
        else the nearest way out toward its next stop. None when there's nowhere to point."""
        from src.world import guide
        key = (self.player, pygame.time.get_ticks() // 1000)
        if getattr(self, "_guide_key", None) == key:
            return self._guide_hit
        self._guide_key, self._guide_hit = key, None
        if not guide.tracked_mission(self.game):
            return None
        px, py = self.player
        near = lambda t: abs(t[0] - px) + abs(t[1] - py)
        for spot, opt in sorted(self._people().items(), key=lambda kv: near(kv[0])):
            if guide.advances_goal(self.game, self.area_key, opt):
                self._guide_hit = (spot, "Here")
                return self._guide_hit
        for spot, kind in sorted(self.doors.items(), key=lambda kv: near(kv[0])):
            if any(guide.advances_goal(self.game, self.area_key, o) for o in self._door_options(kind)):
                self._guide_hit = (spot, "Here")
                return self._guide_hit
        inside = {}  # (a building that is an area of its own: Celadon's Game Corner)
        for spot, kind in self.doors.items():
            for o in self._door_options(kind):
                to = guide.leads_to(self.game, self.area_key, o)
                if to:
                    inside.setdefault(to, spot)
        hop = guide.map_hop(self.game, list(self.exits.values()) + list(inside))
        if not hop or hop == self.area_key:
            return None
        if hop in inside and hop not in self.exits.values():
            self._guide_hit = (inside[hop], "Here")
            return self._guide_hit
        spot = min((t for t, target in self.exits.items() if target == hop), key=near, default=None)
        if spot:
            self._guide_hit = (spot, self._exit_label(hop))
        return self._guide_hit

    def _guide_lift(self, t):
        if t in self._people():
            return 70  # (over the person's name)
        if t in self.doors or t in self.exits:
            return 44  # (over the building's name; a way out's name sits low on its tile)
        return None

    def _draw_guide(self, screen, at):
        dn.DungeonState._draw_guide(self, screen, lambda x, y: at((x, y)))

    def _draw_minimap(self, screen):
        mm, s = self._minimap_rect(), self._mini_scale()
        if getattr(self, "_mini", None) is None or self._mini.get_size() != mm.size:
            self._mini = pygame.Surface(mm.size, pygame.SRCALPHA)
            self._mini.fill((10, 14, 24, 170))
            for y, row in enumerate(self.rows):
                for x, c in enumerate(row):
                    if c == ".":
                        self._mini.fill((150, 190, 230), (4 + x * s, 4 + y * s, s, s))
            for x, y in self.exits:
                self._mini.fill((250, 200, 60), (3 + x * s, 3 + y * s, s + 2, s + 2))
            for x, y in self.doors:
                self._mini.fill((240, 120, 90), (3 + x * s, 3 + y * s, s + 2, s + 2))
        screen.blit(self._mini, mm.topleft)
        for (x, y) in self._people():
            screen.fill((250, 210, 60), (mm.x + 4 + x * s, mm.y + 4 + y * s, s, s))
        pygame.draw.circle(screen, (255, 255, 255), (mm.x + 4 + self.player[0] * s + s // 2, mm.y + 4 + self.player[1] * s + s // 2), 3)

    def _draw_hud(self, screen, fonts):
        self._draw_journal(screen)
        self._draw_minimap(screen)
        W, H = self.game.width, self.game.height
        name = theme.pokemon_word(self.area_data.get("route_name") or self.area_key.replace("_", " ").title())
        if self.banner > 0:
            t = fonts["big"].render(name, True, (255, 255, 255))
            r = t.get_rect(center=(dn.map_view(self.game).centerx, int(H * 0.3))).inflate(60, 24)
            panel = pygame.Surface(r.size, pygame.SRCALPHA)
            panel.fill((10, 14, 24, min(200, self.banner * 4)))
            screen.blit(panel, r.topleft)
            t.set_alpha(min(255, self.banner * 5))
            screen.blit(t, t.get_rect(center=r.center))
        if not self._busy():
            mouse = pygame.mouse.get_pos()
            for rect, label, color, _a in self._buttons():
                theme.command_button(screen, rect, label, fonts["caption"], color, hover=rect.collidepoint(mouse))
        if self.toast_timer > 0:
            t = fonts["label"].render(self.toast, True, (255, 255, 255))
            r = t.get_rect(midtop=(dn.map_view(self.game).centerx, 100)).inflate(28, 14)
            pygame.draw.rect(screen, (30, 36, 58), r, border_radius=12)
            pygame.draw.rect(screen, theme.BAG, r, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=r.center))
