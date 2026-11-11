"""Walkable towns (Jordan, 11-06): a town you walk around, on its Pokemon Journeys V18 map, like the route
maps but wide open (no fog, no narrow halls). The town screen underneath is the same (CityState: its
people, its events, the Center, the Mart, the Gym), only reached by walking:
- walk into a building's door: what's inside (the Pokemon Center, the Mart, the Gym, Oak's Lab, your home);
- the town's other people stand about (a tap, or walk into them, to talk);
- walk off the map's edge: the route that side (as TRAVEL would take you, its conditions and all);
- TRAVEL (bottom right) still has every other way (the far towns, the boats).
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
LABELS = {"devon": "DEVON CORP.", "center": "POKEMON CENTER", "mart": "POKE MART", "gym": "GYM", "lab": "LAB", "home": "HOME",
          "school": "TRAINER SCHOOL", "rival": "RIVAL'S HOUSE", "museum": "MUSEUM", "bike": "BIKE SHOP",
          "harbor": "HARBOR", "fanclub": "FAN CLUB", "radio": "RADIO TOWER", "ptower": "POKEMON TOWER",
          "fuji": "MR. FUJI'S HOUSE", "dept": "DEPT. STORE", "mansion": "CELADON MANSION", "hotel": "CELADON HOTEL",
          "game corner": "GAME CORNER", "tower": "POKEMON TOWER", "mansion": "MANSION", "silph": "SILPH CO.",
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
    _trainer_img = dn.DungeonState._trainer_img
    _item_img = dn.DungeonState._item_img

    def __init__(self, game):
        super().__init__(game)
        self._sprites = {}
        self.facing, self.anim, self.steps = (0, 1), 0, 0
        self.walk_goal = None
        self.toast, self.toast_timer, self.banner = "", 0, 120
        self.signs, self.water_exits, self.locked = {}, set(), {}
        mine = custom(game).get(self.area_key)
        self.own_map = bool(mine)
        if mine:  # our own map (the way forward: Jordan, 11-06)
            self._from_art(mine)
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
        self.h, self.w = len(grid), len(grid[0])
        kinds = m.get("buildings", {})
        doors = art.doors(grid)
        self.doors, self.exits, self.people = {}, {}, {}
        for (x, y), letter in doors.items():  # (a building's door can be a way out: {"Q": "DIGGLETT_CAVE"})
            target = m.get("exits", {}).get(letter) or (m.get("exits", {}).get("D") if kinds.get(letter) == "gate" else None)
            if target:
                self.exits[(x, y)] = target
            else:
                self.doors[(x, y)] = kinds.get(letter, "house")
        self.rows = ["".join("D" if (x, y) in doors else ("." if c in art.OPEN else "#") for x, c in enumerate(row))
                     for y, row in enumerate(grid)]
        self.locked = dict(m.get("locked", {}))  # (a shut door's own words: the Radio Tower with no power)
        names = list(m.get("people", []))
        options = {o.get("text"): o for o in self.area_data.get("explore_options", [])}
        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c in art.EXIT_CHARS and c in m.get("exits", {}):
                    self.exits[(x, y)] = m["exits"][c]
                    if c in "wu":
                        self.water_exits.add((x, y))
                elif c == "N" and names:
                    who = names.pop(0)  # (a town option by its text, or an option of its own: Oak at the gap)
                    opt = who if isinstance(who, dict) else options.get(who)
                    if opt:
                        self.people[(x, y)] = opt
        for spot, lines in zip(art.signs(grid), m.get("signs", [])):
            self.signs[spot] = lines
        for (x, y) in self.exits:  # (a way out is walked onto)
            self.rows[y] = self.rows[y][:x] + "." + self.rows[y][x + 1:]
        cache = self.game.__dict__.setdefault("_walk_town_imgs", {})
        if self.area_key not in cache:
            cache.clear()
            cache[self.area_key] = art.surface(grid, kinds, TILE, m.get("roofs"), m.get("theme"))
        self.map_img = cache[self.area_key]
        self.overheads = [(o, *art.overhead(o, TILE)) for o in m.get("overheads", [])]

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

    def _shown(self, opt):
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
                t = edge[len(edge) // 2]
                inward = next(((t[0] + dx, t[1] + dy) for dx, dy in DIRS if self._open((t[0] + dx, t[1] + dy))
                               and (t[0] + dx, t[1] + dy) not in self.exits), t)
                self.player = inward
                self.facing = (inward[0] - t[0], inward[1] - t[1]) if inward != t else (0, 1)
            else:
                door = next((t for t, k in self.doors.items() if k == "center"), None) or \
                    next((t for t, k in self.doors.items() if k == "home"), None)
                spot = (door[0], door[1] + 1) if door else (self.w // 2, self.h // 2)
                self.player = spot if self._open(spot) else self._nearest_open(spot)
                self.facing = (0, 1)
        self.anim_from = self.partner = self.partner_from = self.player
        self._remember()

    def _people(self):
        """The people standing about now (each option's conditions met)."""
        return {spot: opt for spot, opt in self.people.items() if self._shown(opt)}

    def _open(self, t):
        x, y = t
        return 0 <= x < self.w and 0 <= y < self.h and (self.rows[y][x] == "." or tuple(t) in self.exits)             and tuple(t) not in self._people()

    def _nearest_open(self, t):
        best = min(((x, y) for y in range(self.h) for x in range(self.w) if self._open((x, y)) and (x, y) not in self.exits),
                   key=lambda c: abs(c[0] - t[0]) + abs(c[1] - t[1]), default=(0, 0))
        return best

    def _remember(self):
        self.game.walk_town_pos = (self.area_key, self.player, self.facing)

    def start(self):
        super().start()
        if self.action_menu in self.game.ui_manager.elements:  # (the map's own buttons instead)
            self.game.ui_manager.elements.remove(self.action_menu)

    # ---------------------------------------------------------------- walking
    def _busy(self):
        return self.npc_active or bool(self.hover_menu_active)

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
        if to in self.signs:
            self.walk_goal = None
            return self._read(to)
        if to in self._people():
            self.walk_goal = None
            return self._talk(to)
        if to in self.doors:
            self.walk_goal = None
            return self._enter(to)
        if not self._open(to):
            self.walk_goal = None
            return
        self.anim_from, self.anim = self.player, STEP
        self.partner_from, self.partner = self.partner, self.player
        self.player = to
        self.steps += 1
        self._remember()
        if to in self.exits:
            self.walk_goal = None
            self._leave(self.exits[to])

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
        from src.states.overworld.common import _fill_names
        self.show_message([_fill_names(self.game, line) for line in self.signs[spot]])

    def _talk(self, spot):
        opt = self.people[spot]
        if not self._shown(opt):
            return self.flash("They don't have anything to say right now.")
        cb = self._get_callback_for_option(opt)
        if cb:
            cb()

    def _travel_option(self, target):
        return next((o for o in self.area_data.get("travel_options", [])
                     if (o.get("target_area") or o.get("target")) == target), None)

    def _leave(self, target):
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
        cb()

    def _step_back(self):
        self.player, self.anim = self.anim_from, 0
        self.partner = self.partner_from
        self._remember()

    # ---------------------------------------------------------------- input
    def _buttons(self):
        w, h = self.game.width, self.game.height
        out = [(pygame.Rect(w - 280, h - 162, 126, 70), theme.pokemon_word("POKEMON"), theme.POKEMON, self._open_party),
               (pygame.Rect(w - 146, h - 162, 126, 70), theme.pokemon_word("POKEDEX"), theme.BAG, self._open_pokedex)]
        if not self.own_map:  # (our own maps: you walk wherever you go; Fly is in MENU. Jordan, 11-07)
            out.append((pygame.Rect(w - 280, h - 80, 260, 58), "TRAVEL", theme.FIGHT, self._open_travel))
        return out

    def _open_travel(self):
        options = self.area_data.get("travel_options", [])
        for opt in options:
            opt["action"] = "TRAVEL"
        self._create_hover_menu(options, None)

    def _camera(self):
        px, py = self.player
        if self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        W, H = self.game.width, self.game.height
        mw, mh = self.w * TILE, self.h * TILE  # (the map stays on screen: no black past its edges)
        cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
        cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return cx, cy

    def _origin(self):
        cx, cy = self._camera()
        return int(self.game.width / 2 - cx), int(self.game.height / 2 - cy)

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
                elif e.key == pygame.K_t and not self.own_map:
                    self._open_travel()
                elif e.key in (pygame.K_ESCAPE, pygame.K_m) and self.hud_buttons:
                    self.hud_buttons[0].callback()  # MENU
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if any(b.rect.collidepoint(e.pos) for b in self.hud_buttons):
                    continue
                hit = next((b for b in self._buttons() if b[0].collidepoint(e.pos)), None)
                if hit:
                    hit[3]()
                    return
                goal = self._tile_at(e.pos)
                if self._minimap_rect().collidepoint(e.pos):
                    continue
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
            else:
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
        if self.npc_active and getattr(self, "npc_bg", None):
            return super().draw()  # (someone's own scene: the town screen draws it)
        screen = self.game.screen
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        screen.fill((10, 14, 24))
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
        for spot, opt in people.items():
            img = self._figure_img(opt)
            r = at(spot)
            if img is not None:
                drawn.append((r.bottom, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
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
            self._pill(screen, str(name).upper(), at(t).centerx, at(t).centery + 10, fonts)
        from src.states.overworld.common import _fill_names
        for spot, opt in people.items():
            self._pill(screen, _fill_names(self.game, opt.get("text", "")).upper()[:28], at(spot).centerx,
                       at(spot).y - 34, fonts)
        self._draw_hud(screen, fonts)
        if self.hover_menu_active and self.hover_bg_rect:
            pygame.draw.rect(screen, (255, 255, 255), self.hover_bg_rect, border_radius=12)
            pygame.draw.rect(screen, (0, 0, 0), self.hover_bg_rect, 6, border_radius=12)
        if self.npc_active and self.npc_dialogue:
            self.npc_dialogue.draw(screen)
        self.game.ui_manager.draw(screen)

    @staticmethod
    def _pill(screen, text, cx, bottom, fonts):
        W, H = screen.get_size()
        if not (-60 <= cx <= W + 60 and -40 <= bottom <= H + 60):
            return  # (off screen: no tag piling up at the edge)
        tag = fonts["caption"].render(theme.pokemon_word(text), True, (255, 255, 255))
        pill = tag.get_rect(midbottom=(cx, bottom)).inflate(12, 6)
        pill.clamp_ip(screen.get_rect().inflate(-8, -8))  # (one at the very edge stays on screen)
        pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
        screen.blit(tag, tag.get_rect(center=pill.center))

    tap_mark = None

    def _minimap_rect(self):
        return pygame.Rect(20, 128, self.w * 4 + 8, self.h * 4 + 8)

    def _draw_minimap(self, screen):
        mm, s = self._minimap_rect(), 4
        if getattr(self, "_mini", None) is None:
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
        pygame.draw.circle(screen, (255, 255, 255), (mm.x + 6 + self.player[0] * s, mm.y + 6 + self.player[1] * s), 3)

    def _draw_hud(self, screen, fonts):
        self._draw_minimap(screen)
        W, H = self.game.width, self.game.height
        name = theme.pokemon_word(self.area_data.get("route_name") or self.area_key.replace("_", " ").title())
        if self.banner > 0:
            t = fonts["big"].render(name, True, (255, 255, 255))
            r = t.get_rect(center=(W // 2, int(H * 0.3))).inflate(60, 24)
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
            r = t.get_rect(midtop=(W // 2, 92)).inflate(28, 14)
            pygame.draw.rect(screen, (30, 36, 58), r, border_radius=12)
            pygame.draw.rect(screen, theme.BAG, r, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=r.center))
