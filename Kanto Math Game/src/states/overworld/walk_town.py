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
LABELS = {"steven": "STEVEN'S HOUSE", "space": "SPACE CENTER", "cozmo": "PROF. COZMO'S HOUSE", "wally": "WALLY'S UNCLE'S HOUSE", "contest": "CONTEST HALL", "shipyard": "STERN'S SHIPYARD", "market": "SLATEPORT MARKET", "devon": "DEVON CORP.", "center": "POKEMON CENTER", "mart": "POKE MART", "gym": "GYM", "lab": "LAB", "home": "HOME", "fire_station": "FIRE STATION", "festival": "FESTIVAL HOUSE", "stadium": "PUMMELO STADIUM", "palace": "PALACE OF VICTORY",
          "school": "TRAINER SCHOOL", "rival": "RIVAL'S HOUSE", "assistant": "ASSISTANT'S HOUSE", "poketch": "POKETCH CO.", "gts": "GLOBAL TERMINAL", "tv": "JUBILIFE TV", "condo": "CONDOMINIUMS", "flower": "FLOWER SHOP", "library": "CANALAVE LIBRARY", "poffin": "POFFIN HOUSE", "ruins": "CELESTIC RUINS", "elder": "ELDER'S HOUSE", "lighthouse": "VISTA LIGHTHOUSE", "amity": "AMITY SQUARE", "museum": "MUSEUM", "bike": "BIKE SHOP", "mayor": "MAYOR'S HOUSE", "mayor_office": "MAYOR'S OFFICE", "cycle": "YOUR BIKE", "realgam": "REALGAM TOWER",
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

# Name tags (Jordan, 11-14: "nametags only show overhead for important places and people, it overcrowds the screen"):
# a building is named when it's a landmark (LABELS) or a story option names it; a person when they do something (heal,
# sell, a story errand, a gift, a trade, a quest); not the townsfolk who only chat, the trainers, things lying about.
_ERRANDS = ("gift_item", "trade", "heal", "requires", "starter", "pay", "gift_pokemon", "give", "take_item", "story")


def important_person(opt):
    if isinstance(opt, dict) and "any" in opt:   # (one spot, the story's versions of them: the first that has a tag decides)
        return any(important_person(o) for o in opt["any"])
    if not isinstance(opt, dict) or opt.get("found") or opt.get("no_tag"):   # (no_tag: a thing, not a person - an Apricorn tree)
        return False
    if opt.get("action") not in (None, "EVENT"):
        return True
    ev = opt.get("event") or {}
    if ev.get("battle") and not opt.get("door") and set(ev) <= {"lines", "battle", "flag", "done", "requires", "fail"}:
        return False   # (a trainer who only battles: no tag, as on the routes. 11-17, Jordan: Seven Island's Psychics)
    return opt.get("color") == "GOLD" or any(k in ev for k in _ERRANDS)


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
        from src.world import mystery_dungeon   # (the Giant Volcano easter egg's lab scientist and walk, laid over Cinnabar)
        mystery_dungeon.overlay(_CUSTOM["all"])
    return _CUSTOM["all"]


_CUSTOM = {}


def _flags_hold(game, when):
    """Every condition holds: a flag, "not:flag", or one of the story's own ("season:AUTUMN": Route 20's autumn map, 11-20)."""
    sm = getattr(game, "story_manager", None)
    flags = getattr(sm, "story_flags", None) or {}

    def one(c):
        c = str(c)
        if c.startswith("not:"):
            return not one(c[4:])
        special = sm.special_condition(c) if sm is not None and ":" in c else None
        return bool(special) if special is not None else bool(flags.get(c))
    return all(one(c) for c in (when or []))


def story_map(game, key):
    """The map an area is walked on now (Orange 5.7, 11-18): its own, or the one its "story_maps" [{"when": [flag,
    "not:flag", ...], "map": {a whole map}}] swaps in while those flags stand, the first that does. The swapped-in map
    is drawn in the same frame (same size, same tiles for the same spots: story data, scenes and the Journal's steps
    need no change); its "view_top" keeps the view off rows it leaves empty. Shamouti in the storm: 5.7's 3.60, from
    the force that carries you to the shrine until Lugia's song."""
    m = custom(game).get(key)
    if isinstance(m, dict):
        flags = getattr(getattr(game, "story_manager", None), "story_flags", None) or {}
        for sw in m.get("story_maps") or []:
            if isinstance(sw.get("map"), dict) and _flags_hold(game, sw.get("when")) and (not sw.get("via") or flags.get(on_story_flag(key))):
                return sw["map"]
    return m


def on_story_flag(key):
    return "on_story_map_" + str(key)


def mark_story_arrival(game, key, room=None):
    """A story map with "via" (Orange 5.7, Jordan's Q59: the storm map 3.60 only by the caves, the festival house and the
    force; Fly or the sea bring you to Shamouti as it is): arriving from one of its "via" areas, or out of one of its
    "via_rooms", puts you on it (a story flag, kept in the save: back from a battle you're still there); arriving any
    other way, on the place's own map."""
    m = custom(game).get(key)
    sws = [sw for sw in ((m or {}).get("story_maps") or []) if sw.get("via") or sw.get("via_rooms")] if isinstance(m, dict) else []
    if not sws:
        return
    story = game.story_manager
    sw = next((w for w in sws if _flags_hold(game, w.get("when"))), None)
    if room is not None:   # (out of a building)
        if sw and room in (sw.get("via_rooms") or []):
            story.story_flags[on_story_flag(key)] = True
        return
    came = getattr(story, "last_area_key", None)
    was = getattr(game, "walk_town_pos", None)
    if sw and came in (sw.get("via") or []):
        story.story_flags[on_story_flag(key)] = True
    elif not (was and was[0] == key):
        story.story_flags.pop(on_story_flag(key), None)


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
    _player_extra = dn.DungeonState._player_extra   # (your own extra sheets: running, the fishing cast; Orange 5.7's Ash)
    _extra_frame = dn.DungeonState._extra_frame
    _pose_start = dn.DungeonState._pose_start
    _pose_img = dn.DungeonState._pose_img
    _follower_img = dn.DungeonState._follower_img
    _icon = dn.DungeonState._icon
    _trainer_scale = dn.DungeonState._trainer_scale
    _jumbo = dn.DungeonState._jumbo
    _figure_img = dn.DungeonState._figure_img
    _stand_in_img = dn.DungeonState._stand_in_img
    _mon_img = dn.DungeonState._mon_img
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
        mark_story_arrival(game, self.area_key)
        mine = story_map(game, self.area_key)   # (its own map, or the one the story swaps in now: Shamouti in the storm)
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
        from src.world.hms import usable as _usable
        self._cleared = "".join(c for c, item in (("2", "HM_CUT"), ("0", "HM_ROCK_SMASH"), ("7", "BICYCLE")) if _usable(self.game.story_manager, item))
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
        deep = art.SEA_CHARS if m.get("surf", True) else ""  # (a town's water is crossed with Surf, as on the routes (11-18: every town and room, as in the games: Cerulean
        wade = {tuple(t) for t in m.get("wade", [])}   # and Mikan Gyms' pools too); "surf": false walks it. "wade": water tiles walked anyway, Tangelo's to Lapras)
        self.rows = ["".join("D" if (x, y) in doors else "$" if c == "$" else "o" if c in deep and (x, y) not in wade else "2" if c == "2" else ("." if c in art.OPEN and (not m.get("walk_on") or c in m["walk_on"]) else "#") for x, c in enumerate(row))
                     for y, row in enumerate(grid)]
        self.locked = dict(m.get("locked", {}))  # (a shut door's own words: the Radio Tower with no power)
        # a warp pad (tile 1 with the map's "links" {"x,y": [floor, x, y]}, as on the routes): step on it and you stand on its far pad
        self.links = {tuple(int(v) for v in k.split(",")): (to[1], to[2]) for k, to in (m.get("links") or {}).items()}
        self.room_links = {tuple(int(v) for v in k.split(",")): to[0] for k, to in (m.get("links") or {}).items()
                           if isinstance(to[0], str)}  # (a pad into another room, the same spot there: Lavaridge Gym's sand holes)
        self.stops = {tuple(t) for t in m.get("stops", [])}  # (where a spin tile's slide ends: Viridian Gym's stop tiles)
        self.switches = m.get("switches")  # (floor switches: step on one and every barrier flips: Mauville Gym)
        self.cocoons = dict(m.get("cocoons") or {})  # (Castelia Gym's cocoons, Black 2: walk into one facing a way and its thread carries you on: "x,y,d": [room, x, y, face, condition])
        self.dark = m.get("dark")  # (a dark room: only a circle round you lit, wider with each of its flags: Dewford Gym's trainers)
        # someone standing in the way till the story moves on (the map's "barred", as on the routes: Snowpoint Temple's guard)
        self._bar_list = m.get("barred", [])
        self._edge_to = m.get("edge_to") or {}  # (out by this edge tile: in at its partner on the next map, Emerald's own connection)
        self.thin_ice = m.get("thin_ice")  # (Sootopolis Gym's: crack every tile of a section and its stairs open; twice, and you fall)
        self.pits = m.get("pits")  # (a pit round the path: step off it and you fall back to "to", HGSS's Ecruteak Gym: {"chars", "to", "lines"})
        self.turnstiles = m.get("turnstiles")  # (Emerald's rotating gates: Fortree Gym's, turned by walking into an arm)
        self.rotators = m.get("rotators")  # (Emerald's rotating tile puzzle: Mossdeep Gym's blocks, turned by its coloured switches)
        self.barred = {tuple(t): bar for bar in m.get("barred", []) if not self._bar_met(bar) and self._bar_here(bar) for t in bar.get("tiles", [])}
        self.barred.update(self._rot_bars())
        self.sign_scenes = {tuple(int(v) for v in k.split(",")): s for k, s in (m.get("sign_scenes") or {}).items()}  # (reading this sign starts a scene)
        self.sign_events = {tuple(int(v) for v in k.split(",")): e for k, e in (m.get("sign_events") or {}).items()}  # (reading this sign runs an event till its flag is set: Cinnabar Gym's quiz machines)
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
        _pic = (m.get("roofs") or {}).get("_picture")
        if _pic and (_pic.get("until") or _pic.get("when") or _pic.get("by_version")):
            _ck += "|pic:" + art._version_file(_pic)  # (a picture that changes with a flag: Mauville Gym's barriers, flipped by its switches)
        if _ck not in cache:
            cache.clear()
            cache[_ck] = art.surface(grid, kinds, TILE, m.get("roofs"), m.get("theme"))
        self.map_img = cache[_ck]
        self.overheads = [(o, *art.overhead(o, TILE)) for o in m.get("overheads", [])]
        self._pic_now = art._version_file(_pic) if _pic else None
        # seen as the DS camera sees it (B2W2's towns: src/dungeon/camera3d.py): the ground lifted by height, leaning buildings
        self.cam3d = None
        _c = (m.get("roofs") or {}).get("_cam")
        if _c:
            from src.dungeon import camera3d
            try:
                self.cam3d = camera3d.Cam3D(_c, (m.get("roofs") or {}).get("_objects") or [], TILE, self.w, self.h,
                                             set(art.doors(grid)))
            except (pygame.error, OSError, KeyError, ValueError):
                self.cam3d = None
        self.live = None   # (Black 2's own models through a moving camera, src/dungeon/live3d.py: the zone the picture was made from)
        self._live_cam = None
        _zone = os.path.basename(str((_c or {}).get("picture") or "")).split("_")[0]
        if self.cam3d and _zone.isdigit():
            _npz = os.path.join(self.game.assets.assets_dir or "assets", "b2_3d", _zone + ".npz")
            if os.path.exists(_npz):
                from src.dungeon import live3d
                try:
                    _pitch, _fov = live3d.zone_camera(_npz)
                    self.live = {"zone": int(_zone), "pitch": _pitch, "fov": _fov, "base": float(_c.get("base") or 0.0),
                                 "lift_k": float(_c.get("lift_k") or 1.0)}
                except (OSError, KeyError, ValueError, IndexError):
                    self.live = None
        self.shadows = bool((m.get("roofs") or {}).get("_shadows"))   # (an oval under everyone's feet, as the DS games)
        self.cameras = m.get("cameras") or []   # (the camera closer or further: the map's "camera_zoom", its "cameras" [{"rect": [x, y, w, h], "zoom"}])
        self.zoom_base = float(m.get("camera_zoom") or 1.0)
        self._npc_init(m)

    def _swap_story_map(self):
        """A flag changed which map the area is walked on (story_map: Lugia's song ends Shamouti's storm): the new one,
        you standing where you were (the same frame), its people and scenes from the start."""
        if not getattr(self, "own_map", False) or getattr(self, "room", None):
            return
        new = story_map(self.game, self.area_key)
        if not isinstance(new, dict) or new is self.town_map:
            return
        keep, face = tuple(self.player), self.facing
        self.town_map = new
        self.__dict__.pop("_guide_parts", None)
        self.game.__dict__.setdefault("_walk_town_imgs", {}).clear()
        self._from_art(new)
        self.player = keep if self._open(keep) else self._nearest_open(keep)
        self.facing = face
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.player
        self._mini = None
        self._remember()

    def _refresh_picture(self):
        """A flag changed the picture of the map you're on (the S.S. Anne sails out of the harbour): draw the new one,
        without starting its people and scenes over."""
        from src.dungeon import art
        m = ((self.town_map.get("rooms") or {}).get(self.room) if getattr(self, "room", None) else self.town_map) if getattr(self, "town_map", None) else None
        pic = ((m or {}).get("roofs") or {}).get("_picture")
        if not pic or not (pic.get("until") or pic.get("when")) or art._version_file(pic) == getattr(self, "_pic_now", None):
            return
        self._pic_now = art._version_file(pic)
        self.map_img = art.surface(self.grid, m.get("buildings", {}), TILE, m.get("roofs"), m.get("theme"))
        self.overheads = [(o, *art.overhead(o, TILE)) for o in m.get("overheads", [])]

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
        shown = getattr(self, "_shown_homes", None)   # (someone not here yet doesn't stand in the way: Oak before he walks into his Lab)
        return not any(o is not mover and not o.gone and t in (o.pos, o.frm) and (shown is None or h in shown) for h, o in self.motions.items())

    def _npc_tick(self):
        self._bar_tick = getattr(self, "_bar_tick", 0) + 1
        if self._bar_tick % 20 == 0 and not self._busy() and getattr(self, "_bar_list", None):   # (a gift or a battle moved the story on:
            self.barred = {tuple(t): bar for bar in self._bar_list if not self._bar_met(bar) and self._bar_here(bar) for t in bar.get("tiles", [])}   # the Amber gone from its case)
            self.barred.update(self._rot_bars())
            self._refresh_picture()   # (and its picture: a quiz machine answered, a Cinnabar Gym gate drawn open)
        if not getattr(self, "motions", None):
            return
        self._shown_homes = {h for h, o in self.people.items() if self._shown(o)}
        shown = set(self._people())
        _leads = None
        for home, mo in self.motions.items():
            if mo.kind == "trail":   # (a Pokemon at its trainer's heels, at their side when they stop: npc.trail)
                if _leads is None:
                    _leads = {(o.get("text") if isinstance(o, dict) else o): self.motions.get(h) for h, o in self.people.items()}
                from src.dungeon import npc as _npc
                _npc.trail(mo, _leads.get(mo.leader), lambda t, mo=mo: self._npc_free(t, mo))
                continue
            if mo.pos in shown or mo.moving() or mo.path:
                mo.tick(lambda t, mo=mo: self._npc_free(t, mo))
        self.scenes.sweep()
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

    def npc_cue(self):
        """A story scene starts: the alert chime (src/dungeon/npc.py Scenes.start)."""
        snd = getattr(self.game.assets, "alert_sfx", None)
        if snd:
            snd.play()

    def npc_player(self):
        return tuple(self.player)

    def npc_passable(self, t, m):
        return self._npc_free(t, m)

    def npc_shown(self, scene):
        return self._shown(scene)

    def npc_flag(self, name):
        self.game.story_manager.story_flags[name] = True
        self._swap_story_map()
        self._refresh_picture()
        # (a scene that moves the story on: stand-ins come and go at once, the Shroomish back beside its girl)
        self.barred = {tuple(t): bar for bar in getattr(self, "_bar_list", []) if not self._bar_met(bar) and self._bar_here(bar) for t in bar.get("tiles", [])}
        self.barred.update(self._rot_bars())

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
        else:
            if getattr(self, "_cam_focus", None):
                self._cam_ease_until = pygame.time.get_ticks() + 1500   # (gliding back to you)
            self._cam_focus = None   # (the scene's over: the view back on you)
            self._scene_zoom = None
            if hasattr(self, "_own_img"):   # (and the map drawn as it is again)
                self.npc_picture(None)

    def npc_ground(self, t):
        """The map's character at a tile (what a scene's walker or swimmer may cross: npc.route), None off the map."""
        x, y = t
        return self.grid[y][x] if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]) else None

    def npc_look(self, t):
        """A scene moves the view to a tile (None: back to you)."""
        self._cam_ease_until = pygame.time.get_ticks() + 1500
        self._cam_focus = tuple(t) if t else None

    def npc_picture(self, name):
        """A scene draws the map with another picture of it (oi_ground/<name>.png and oi_top/<name>.png), None: its own again."""
        from src.dungeon import art
        m = ((self.town_map.get("rooms") or {}).get(self.room) if getattr(self, "room", None) else self.town_map) or {}
        if not hasattr(self, "_own_img"):
            self._own_img = (self.map_img, self.overheads)
        if not name:
            self.map_img, self.overheads = self.__dict__.pop("_own_img")
            return
        roofs = dict(m.get("roofs") or {})
        pic = dict(roofs.get("_picture") or {})
        pic = {"f": f"oi_ground/{name}.png", "at": pic.get("at", [0, 0])}
        roofs["_picture"] = pic
        self.map_img = art.surface(self.grid, m.get("buildings", {}), TILE, roofs, m.get("theme"))
        tops = [dict({k: v for k, v in o.items() if k not in ("when", "until", "by_version")}, f=f"oi_top/{name}.png") if o.get("kind") == "picture" else o
                for o in m.get("overheads", [])]
        self.overheads = [(o, *art.overhead(o, TILE)) for o in tops]

    def npc_open(self, t):
        return 0 <= t[0] < self.w and 0 <= t[1] < self.h and self.rows[t[1]][t[0]] == "." and t not in self.signs

    def npc_face_player(self, spot):
        self.facing = (max(-1, min(1, spot[0] - self.player[0])), max(-1, min(1, spot[1] - self.player[1])))

    def npc_edge(self, m):
        edge = [(x, y) for (x, y) in self.exits if not (x, y) in self.water_exits]
        return min(edge, key=lambda t: abs(t[0] - m.pos[0]) + abs(t[1] - m.pos[1]), default=None)

    def _may_run(self):
        """Running (Shift held) on foot: not surfing, not following someone in a scene."""
        if not dn.running() or getattr(self, "_scene_lock", False):
            return False
        x, y = self.player
        return not (0 <= y < self.h and 0 <= x < self.w and self.rows[y][x] == "o")

    def _trash_can(self, t):
        """A room's "trashcans" {"cans": [[x, y]...] in rows of "cols", "first": flag, "open": flag} (FireRed's Vermilion
        Gym): two switches hide in the cans, the second always beside the first (left, right, up or down in the grid).
        Find the first and one lock opens; the second next opens the door; a wrong can after the first resets both and
        hides the switches somewhere new. Returns True when t was a can."""
        tc = (((self.town_map or {}).get("rooms") or {}).get(getattr(self, "room", None)) or {}).get("trashcans") if getattr(self, "town_map", None) else None
        if not tc or [t[0], t[1]] not in tc["cans"]:
            return False
        import random
        story = self.game.story_manager
        flags = story.story_flags
        cans, cols = [tuple(c) for c in tc["cans"]], int(tc.get("cols", 5))
        i = cans.index(tuple(t))

        def hide():
            first = random.randrange(len(cans))
            r, c = divmod(first, cols)
            near = [rr * cols + cc for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if 0 <= cc < cols and 0 <= rr * cols + cc < len(cans) and 0 <= rr]
            flags[tc["first"] + "_where"] = [first, random.choice(near)]
        if flags.get(tc["open"]):
            self.show_message(["Nope, there's only trash in here."])
            return True
        if not flags.get(tc["first"] + "_where"):
            hide()
        first, second = flags[tc["first"] + "_where"]
        if not flags.get(tc["first"]):
            self._can_first, self._cans_tried = (i, set()) if i == first else (None, getattr(self, "_cans_tried", set()) | {i})  # (for the Journal's marker: which cans you've looked in)
            if i == first:
                flags[tc["first"]] = True
                self._from_art(self.town_map["rooms"][self.room])
                self.show_message(["Hey! There's a switch under the trash!", "Click! The first electric lock opened!"])
            else:
                self.show_message(["Nope, there's only trash in here."])
            return True
        if i == second:
            flags[tc["open"]] = True
            self._from_art(self.town_map["rooms"][self.room])
            self.show_message(["There's another switch under the trash!", "Click! The second electric lock opened! The door to the Leader is open!"])
        else:
            flags.pop(tc["first"], None)
            self._can_first, self._cans_tried = None, set()
            hide()
            self._from_art(self.town_map["rooms"][self.room])
            self.show_message(["Nope, there's only trash in here.", "Hey! The electric locks were reset!"])
        return True

    def _town_hidden(self, t):
        """An item hidden in town (the map's or room's "hidden" {"x,y": item}: the game's own hidden items, as on the
        routes): found by stepping on its spot, or walking into it where it's solid (or into whoever stands on it). Once each.
        "hidden_when" {"x,y": conditions}: not there to find till they are met (Viridian Gym's Macho Brace, once Giovanni is beaten)."""
        item = self._hidden_now().get(f"{t[0]},{t[1]}")
        story = self.game.story_manager
        flag = f"hidden_{self.area_key}_{getattr(self, 'room', None) or ''}_{t[0]}_{t[1]}"
        if not item or story.story_flags.get(flag):
            return False
        story.story_flags[flag] = True
        if item == "POKE_BALLS":   # (Poke Balls are the one ball count)
            story.balls_left = getattr(story, "balls_left", 0) + 1
        else:
            story.add_item(item)
        from src.pokemon import forms as _forms
        self.walk_goal = None
        self.show_message([f"Something was hidden here... You found a {_forms.item_label(item).upper()}!"])
        return True

    def _hidden_now(self):
        """This map's (or room's) hidden items that are there to find now: {"x,y": item}."""
        m = ((self.town_map.get("rooms") or {}).get(self.room) if getattr(self, "room", None) else self.town_map) if getattr(self, "town_map", None) else None
        when = (m or {}).get("hidden_when") or {}
        return {k: v for k, v in ((m or {}).get("hidden") or {}).items() if k not in when or self._check_menu_condition(when[k])}

    def _itemfinder(self, here):
        """With the Itemfinder, a hidden item on screen makes it beep (once each visit)."""
        from src.world import itemfinder
        heard = self.__dict__.setdefault("_heard", {}).setdefault(getattr(self, "room", None) or "", set())
        line = itemfinder.beep(self.game.story_manager, self._hidden_now(), here,
                               lambda x, y: f"hidden_{self.area_key}_{getattr(self, 'room', None) or ''}_{x}_{y}", heard)
        if line:
            self.flash(line, 150)

    def npc_room(self, room, x, y):
        """A scene ends with you inside one of the town's rooms, standing at (x, y) (Oak walks you into his Lab)."""
        if room not in ((getattr(self, "town_map", None) or {}).get("rooms") or {}):
            return
        self._go(room, "")
        self.player, self.facing = (x, y), (0, -1)
        self.anim = 0
        self.anim_from = self.partner = self.partner_from = self.player
        self._remember()

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
        if opt.get("item_condition") and not __import__("src.world.hms", fromlist=["field"]).field(story, opt["item_condition"]):   # (an HM: Kanto asks for its badge too)
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
        landing, self.game.fly_landing = getattr(self.game, "fly_landing", None), None   # (Fly, Orange 11-17: down outside the Center's door)
        fly_door = next((t for t, k in self.doors.items() if k == "center"), None) if landing == self.area_key else None
        if fly_door:   # (every region, 11-18: Fly lands you outside the Center)
            spot = (fly_door[0], fly_door[1] + 1)
            self.player, self.facing = (spot if self._open(spot) else self._nearest_open(spot)), (0, 1)
        elif was and was[0] == self.area_key and self._open(was[1]):
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
                _out = [(t[0] + dx, t[1] + dy, dx, dy) for dx, dy in DIRS if self._open((t[0] + dx, t[1] + dy))
                        and (t[0] + dx, t[1] + dy) not in self.exits]
                _out.sort(key=lambda o: self._open((t[0] - o[2], t[1] - o[3])))   # (out the way the door faces: away from its building. A gatehouse's side door, Saffron's)
                inward = (_out[0][0], _out[0][1]) if _out else t
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
        from src.world.hms import usable
        return usable(self.game.story_manager, item)

    def _has_waterfall(self):
        from src.world.hms import field
        return field(self.game.story_manager, "HM_WATERFALL")   # (Kanto: with the Volcano Badge, FireRed's rule)

    def _nearest_open(self, t):
        best = min(((x, y) for y in range(self.h) for x in range(self.w) if self._open((x, y)) and (x, y) not in self.exits),
                   key=lambda c: abs(c[0] - t[0]) + abs(c[1] - t[1]), default=(0, 0))
        return best

    def _remember(self):
        self.game.walk_town_pos = (self.area_key, self.player, self.facing)
        self.game.walk_town_room = (self.area_key, self.room) if getattr(self, "room", None) else None
        self.game.last_spot = {"area": self.area_key, "kind": "town", "room": getattr(self, "room", None),   # (for the save file:
                               "x": int(self.player[0]), "y": int(self.player[1]), "face": list(self.facing)}   #  Continue puts you back; 11-20)

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
        if room is None and getattr(self, "room", None):   # (out of a building the story map is entered by: the festival house)
            mark_story_arrival(self.game, self.area_key, room=self.room)
            new = story_map(self.game, self.area_key)
            if isinstance(new, dict) and new is not self.town_map:
                self.town_map = new
                self.game.__dict__.setdefault("_walk_town_imgs", {}).clear()
        self.room = room
        _dyn = ((self.town_map.get("rooms") or {}).get(room) or {}).get("dynamic_exit") if room else None
        if _dyn and str(came).startswith("ROOM:"):   # (into a lift car: its doors are on the floor you came from, till it rides)
            self.game.story_manager.story_flags[_dyn["flag"]] = came[5:]
        self.signs, self.water_exits = {}, set()
        self._mini = None
        self.walk_goal = None
        self._ice_cracked = set()  # (the ice is whole again each time you come in)
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
            came = ((self.town_map["rooms"][room] if room else self.town_map).get("arrive_as") or {}).get(came, came)   # (out of a lift car
            mats = [t for t, target in self.exits.items() if target == came]   #  that rode up: at the floor's own lift door, Kumquat's)
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
        return self.npc_active or bool(self.hover_menu_active) or getattr(self, "_scene_lock", False) or bool(getattr(self, "_ride", None))

    def _cocoon_ride(self, c):
        """Into a cocoon: its silk thread pulls you up or down to another floor (Castelia Gym, Black 2's gym_insect overlay)."""
        room, x, y = c[0], int(c[1]), int(c[2])
        face = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}.get(c[3] if len(c) > 3 else "d", (0, 1))
        self.walk_goal = None
        into = (self.player[0] + self.facing[0], self.player[1] + self.facing[1])
        self._ride = {"n": 0, "room": room, "to": (x, y), "face": face, "into": into, "moved": False}   # (played out: _ride_tick, drawn in draw)

    RIDE_IN, RIDE_GO, RIDE_OUT = 26, 22, 26   # (frames: drawn into the cocoon, along the thread, out of the other)

    def _ride_tick(self):
        r = self._ride
        r["n"] += 1
        if r["n"] == self.RIDE_IN + self.RIDE_GO // 2 and not r["moved"]:   # (halfway along the thread: the other floor)
            r["moved"] = True
            if r["room"] != getattr(self, "room", None):
                self._go(r["room"], "COCOON")
            self.player = self.anim_from = self.partner = self.partner_from = r["to"]
            self.facing = r["face"]
            self.anim = 0
            self._remember()
        if r["n"] >= self.RIDE_IN + self.RIDE_GO + self.RIDE_OUT:
            self._ride = None

    def _ride_pose(self):
        """(dx, dy tiles from your tile, scale, hidden) for the cocoon ride now."""
        r = self._ride
        n = r["n"]
        if n < self.RIDE_IN:   # (pulled in: toward the cocoon, shrinking into it)
            t = n / self.RIDE_IN
            ix, iy = r["into"][0] - self.player[0], r["into"][1] - self.player[1]
            return ix * t * 0.9, iy * t * 0.9 - 0.4 * t * (1 - t) * 4, max(0.08, 1 - t * 0.95), False
        if n < self.RIDE_IN + self.RIDE_GO:
            return 0, 0, 0, True
        t = (n - self.RIDE_IN - self.RIDE_GO) / self.RIDE_OUT   # (set down: out of the cocoon in front of you)
        fx, fy = self.facing
        return fx * (1 - t), fy * (1 - t) - 0.4 * t * (1 - t) * 4, 0.08 + 0.92 * t, False

    def _draw_ride_silk(self, screen, ox, oy):
        """Silk round the cocoon as it pulls you in or lets you out; along the thread, the view streams with silk."""
        import math
        r = self._ride
        n = r["n"]
        view = self._view()
        if self.RIDE_IN <= n < self.RIDE_IN + self.RIDE_GO:
            t = (n - self.RIDE_IN) / self.RIDE_GO
            veil = pygame.Surface(view.size, pygame.SRCALPHA)
            veil.fill((246, 246, 252, int(235 * math.sin(math.pi * t))))
            up = -1 if r["face"][1] <= 0 else 1
            for i in range(22):   # (threads streaming past)
                x = (i * 53 + 17) % view.w
                y = int(((i * 97 + n * 38 * up) % (view.h + 120)) - 60)
                pygame.draw.line(veil, (150, 158, 190, 255), (x, y), (x + 6, y + 110), 6)
                pygame.draw.line(veil, (255, 255, 255, 255), (x, y), (x + 6, y + 110), 2)
            screen.blit(veil, view.topleft)
            return
        cx, cy = (r["into"] if n < self.RIDE_IN else (self.player[0] + self.facing[0], self.player[1] + self.facing[1]))
        px, py = int(ox + (cx + 0.5) * TILE), int(oy + (cy + 0.5) * TILE)
        spin = n * 0.35
        for i in range(6):   # (the cocoon's silk winding round)
            a = spin + i * math.pi / 3
            rad = TILE * (0.55 + 0.15 * math.sin(n * 0.4 + i))
            box = pygame.Rect(px - rad, py - rad, rad * 2, rad * 2)
            pygame.draw.arc(screen, (120, 128, 160), box.inflate(4, 4), a, a + 1.1, 6)   # (an outline: silk shows on the white floor)
            pygame.draw.arc(screen, (250, 250, 255), box, a, a + 1.1, 3)

    def flash(self, text, frames=90):
        self.toast, self.toast_timer = text, frames

    def step(self, dx, dy):
        if self._busy() or self.anim > 0:
            return
        self.facing = (dx, dy)
        to = (self.player[0] + dx, self.player[1] + dy)
        _coc = getattr(self, "cocoons", None) and self.cocoons.get("%d,%d,%s" % (to[0], to[1], {(0, -1): "u", (0, 1): "d", (-1, 0): "l", (1, 0): "r"}[(dx, dy)]))
        if _coc and (len(_coc) < 5 or not _coc[4] or self._check_menu_condition(_coc[4])):
            return self._cocoon_ride(_coc)
        if getattr(self, "turnstiles", None):
            arm = self._gate_edges().get(frozenset((tuple(self.player), tuple(to))))
            if arm is not None and not self._turn_gate(arm, (dx, dy)):
                self.walk_goal = None
                return self.flash("The gate won't turn that way.", 80)
        from src.coop import roster
        if roster.host_tethered(self.game, to):
            self.walk_goal = None
            return self.flash("Your team fainted: stay close to a friend.")
        if roster.world.occupied(self.game, to):
            self.walk_goal = None  # (a friend or their Pokemon is standing there)
            return
        if self._trash_can(to):   # (Vermilion Gym's trash cans: search one by walking into it)
            self.walk_goal = None
            return
        if tuple(to) in getattr(self, "barred", {}):
            self.walk_goal = None
            bar = self.barred[tuple(to)]
            if bar.get("ambush") and self._gym_ambush_due():   # (Viridian: Jessie & James jump you at the locked Gym; Jordan's)
                return self.start_gym_battle()
            if bar.get("on_bump"):  # (walking into it moves the story: Fortree's Kecleon, seen with the Devon Scope, runs off)
                ob = bar["on_bump"]
                if ob.get("flag"):
                    self.npc_flag(ob["flag"])
                from src.states.overworld.common import _fill_names
                return self.show_message([_fill_names(self.game, x) for x in ob.get("lines") or ["..."]])
            if str(bar.get("look") or "").startswith("ribbon:"):  # (a portrait: who it shows, in the words under it)
                p = self.game.story_manager.ribbon_holder(bar["look"][7:])
                from src.states.overworld.common import _fill_names
                name = getattr(p, "display_name", None) or getattr(p, "name", "") if p else ""
                return self.show_message([_fill_names(self.game, x).replace("{ribbon_mon}", str(name)) for x in bar.get("lines") or ["..."]])
            return self.flash((self.barred[tuple(to)].get("lines") or ["Someone is standing in the way."])[0], 130)
        if to in self.signs:
            self.walk_goal = None
            return self._read(to)
        if to in self._people():
            self.walk_goal = None
            if self._town_hidden(to):   # (an item hidden on the tile they stand on: found first, once)
                return
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
        pits = getattr(self, "pits", None)
        if pits and grid and 0 <= to[0] < self.w and 0 <= to[1] < self.h and grid[to[1]][to[0]] in pits.get("chars", "m"):
            self.walk_goal = None   # (off the unseen path: you fall, and land back at the start)
            self.player = self.partner = self.partner_from = self.anim_from = tuple(pits["to"])
            self.anim = 0
            self.facing = (0, -1)
            self._remember()
            return self.show_message(list(pits.get("lines") or ["You stepped into the dark... and fell!", "You landed back by the entrance."]))
        if not self._open(to):
            self.walk_goal = None
            if self._town_hidden(to):   # (an item hidden in something solid: walk into it)
                return
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
        from src.world import vs_seeker as _vs
        _vs.step(self.game.story_manager)
        self._remember()
        if not self._town_hidden(to):
            self._itemfinder(to)
        if getattr(self, "thin_ice", None) and self._step_ice(to):
            return
        self._step_switch(to)
        if to not in self.exits and (self._surf_wild(to) or self._grass_wild(to)):
            return
        if to in self.exits:
            self.walk_goal = None
            self._leave(self.exits[to])
        elif to in getattr(self, "links", {}):  # a warp pad: on to its far pad (no stepping back through by itself)
            self.walk_goal = None
            far = self.links[to]
            if to in getattr(self, "room_links", {}):  # (in another room: Lavaridge Gym's holes down, its vents up)
                self._go(self.room_links[to], "")
            self.player = self.partner = self.partner_from = self.anim_from = far
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
        ev = getattr(self, "sign_events", {}).get(tuple(spot))
        if ev and not self.game.story_manager.story_flags.get((ev.get("event") or {}).get("flag")):
            cb = self._get_callback_for_option(ev)
            if cb:
                cb()
                return
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
        if str(opt_data.get("action") or "").upper() == "LEAGUE":  # (an Elite Four member, or the Champion, in their own room)
            from src.states.overworld.gym_lobby import league_member
            return lambda: league_member(self, opt_data)
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
        opt = next((o for o in self.area_data.get("travel_options", [])
                    if (o.get("target_area") or o.get("target")) == target), None)
        if opt is None:   # (a place listed with the town's own things to do: Cinnabar's Pokemon Mansion, whose door is a way out; 11-16)
            opt = next((o for o in self.area_data.get("explore_options", [])
                        if o.get("action") == "TRAVEL" and o.get("target_area") == target), None)
        return opt

    def _leave(self, target):
        if str(target).startswith("OUT:"):  # (out of a room, back to the town)
            return self._go(None, target)
        if str(target).startswith("ROOM:") and self._car_floor(getattr(self, "room", None)):   # (out of a lift car: on the floor it's at)
            target = "ROOM:" + self._car_floor(self.room)
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
    # ---------------------------------------------------------------- fishing from the town's shore (Jordan, 11-17: as the games)
    def _fish_spot(self):
        """The water beside you (the way you face first) that you can fish in, or None: the town has rod Pokemon (its
        "can_fish"), you have a rod, and you're outdoors on our own map, or in a room of it that is out of doors (the
        room's own "can_fish": Vermilion's harbour)."""
        from src.states.overworld.route_actions import RouteActions as _RA
        if not self.own_map or not _RA.fishable(self.game, self.area_key, self.area_data):
            return None
        if getattr(self, "room", None) and not ((self.town_map.get("rooms") or {}).get(self.room) or {}).get("can_fish"):
            return None
        inv = self.game.story_manager.inventory
        if not any(inv.get(r, 0) > 0 for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD")):
            return None
        from src.dungeon import art
        for dx, dy in [self.facing] + [d for d in DIRS if d != self.facing]:
            x, y = self.player[0] + dx, self.player[1] + dy
            if 0 <= x < self.w and 0 <= y < self.h and (self.grid[y][x] == "~" or self.grid[y][x] in art.SEA_CHARS or (x, y) in self.water_exits):
                return (x, y)
        return None

    SURF_RATE = 0.05   # (a wild Pokemon each step on a town's water: about one in twenty, near the games' own sea rate)
    COMMON_SURF = {"72": 85, "73": 15}   # (the last resort: Tentacool, now and then Tentacruel, as on almost every sea)

    def _surf_wild(self, to):
        """Surfing on a town's water (11-18, Jordan: "if a player is able to Surf it in the game ... able to Surf it in
        our game"): a wild Pokemon now and then, as out at sea. Not on the first step in, not in a building, not with a
        Repel going. Returns True if a battle starts."""
        import random
        if getattr(self, "room", None) or self.anim_from == to or getattr(self.game.story_manager, "repel_routes", 0) > 0:
            return False
        rows = self.rows
        x0, y0 = self.anim_from
        if rows[to[1]][to[0]] != "o" or rows[y0][x0] != "o" or random.random() >= self.SURF_RATE:
            return False
        mon = self._surf_mon()
        if mon is None:
            return False
        self.walk_goal = None
        self.anim = 0
        self._remember()
        from src.states.battle import WildBattleState
        battle = WildBattleState(self.game, mon, self.area_key,
                                 background_image=random.choice(["battle_ocean1.png", "battle_ocean2.png", "battle_ocean3.png"]))
        battle.back_to_town = True
        self.game.change_state(battle)
        return True

    def _surf_table(self):
        """(pool {id: weight}, the area its levels come from) for this town's water: its own Surf table; else the
        nearest place its ways out lead to with one (a sea route's whole table, out by the water); else Tentacool."""
        data = self.game.loader.area_data
        places = data.get("STORY_PROGRESSION", {})

        def own(key, by_sea=False):
            entry = places.get(key) or {}
            for name in (entry.get("surf_pool_percentages"), f"{key}_SURF_PERCENTAGES"):
                if name and isinstance(data.get(name), dict) and data[name]:
                    return data[name]
            if by_sea and isinstance(data.get(entry.get("wild_pool_percentages")), dict):
                return data[entry["wild_pool_percentages"]] or None
            return None
        pool = own(self.area_key)
        if pool:
            return pool, self.area_key
        seen, todo = {self.area_key}, [(self.area_key, 0)]
        maps = custom(self.game)
        while todo:   # (the nearest water a step or two out: the next route, then the one past it)
            key, depth = todo.pop(0)
            m = maps.get(key) if isinstance(maps.get(key), dict) else {}
            exits = dict(m.get("exits") or {})
            for c, target in sorted(exits.items(), key=lambda kv: kv[0] not in "wu"):
                if not isinstance(target, str) or target in seen or target.startswith(("ROOM:", "OUT:")):
                    continue
                seen.add(target)
                pool = own(target, by_sea=(c in "wu" or self._sea_route(target)))
                if pool:
                    return pool, target
                if depth < 2:
                    todo.append((target, depth + 1))
        return dict(self.COMMON_SURF), self.area_key

    def _sea_route(self, key):
        """A route that is mostly sea (its whole table is what you meet surfing: Hoenn's Route 124)."""
        m = custom(self.game).get(key)
        if not isinstance(m, dict) or "art" not in m:
            return False
        from src.dungeon import art
        cells = [c for r in m["art"] for c in r]
        return bool(cells) and sum(c in art.SEA_CHARS for c in cells) * 2 > len(cells)

    GRASS_RATE = 0.1   # (a town's tall grass: about one step in ten, like a route's)

    def _grass_wild(self, to):
        """A town's own tall grass (the area's "grass_pool_percentages"; 11-19, Jordan: the Ruins of Alph's outside grass has
        SoulSilver's Natu and Smeargle, its Unown only inside). Not in a building, not with a Repel going. True if a battle starts."""
        import random
        from src.utils import Utils
        from src.world import levels
        from src.pokemon.data import Pokemon
        if getattr(self, "room", None) or self.anim_from == to or getattr(self.game.story_manager, "repel_routes", 0) > 0:
            return False
        data = self.game.loader.area_data
        name = (data.get("STORY_PROGRESSION", {}).get(self.area_key) or {}).get("grass_pool_percentages")
        pool = data.get(name) if name else None
        if not isinstance(pool, dict) or not pool or (getattr(self, "grid", None) or self.rows)[to[1]][to[0]] != '"' or random.random() >= self.GRASS_RATE:
            return False
        raw = self.game.loader.fetch_specific(int(Utils.weighted_random_choice(pool)))
        if not raw:
            return False
        mon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, mon, self.area_key)
        self.walk_goal = None
        self.anim = 0
        self._remember()
        from src.states.battle import WildBattleState
        battle = WildBattleState(self.game, mon, self.area_key)
        battle.back_to_town = True
        self.game.change_state(battle)
        return True

    def _surf_mon(self):
        """A wild Pokemon from this town's water, at its place's level."""
        from src.utils import Utils
        from src.world import seasons, levels, regional_forms
        from src.pokemon.data import Pokemon
        pool, level_key = self._surf_table()
        if level_key == self.area_key:
            from src.world import swarms as _swarms   # (a swarm on this town's water, 11-19)
            pool = _swarms.adjust(self.game, pool, self.area_key, "surf")
        pool = seasons.adjust_pool(self.game, regional_forms.extend_pool(self.game, pool), self.area_key)
        if not pool:
            return None
        raw = self.game.loader.fetch_specific(int(Utils.weighted_random_choice(pool)))
        if not raw:
            return None
        mon = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, mon, level_key)
        return mon

    def _fishing_pool(self, rod):
        from src.states.overworld.route_actions import RouteActions
        return RouteActions._fishing_pool(self, rod)

    def fish_here(self):
        """Cast into the water beside you: a bite is a wild battle (the town's own rod Pokemon), then back here."""
        spot = self._fish_spot()
        if not spot or self._busy() or self.anim > 0:
            return
        from src.states.overworld.route_actions import RouteActions
        self.walk_goal = None
        self.facing = (spot[0] - self.player[0], spot[1] - self.player[1])
        self._pose_start("fish")   # (your own casting frames, if you have them: Orange 5.7's Ash)
        mon = RouteActions._fish_bite(self)
        if mon is None:
            return self.flash("Not even a nibble...")
        self._remember()

        def bite():
            import random
            from src.states.battle import WildBattleState
            battle = WildBattleState(self.game, mon, self.area_key,
                                     background_image=random.choice(["battle_ocean1.png", "battle_ocean2.png", "battle_ocean3.png"]))
            battle.back_to_town = True
            self.game.change_state(battle)
        self.show_message(["Oh! A bite!"], callback=bite)

    def _buttons(self):
        side = dn.side_buttons(self.game)  # (stacked in the right band, beside the map)
        out = [(side[3].move(0, -70).inflate(0, -14).move(0, 7), "BAG", (198, 132, 60), self._open_bag),  # (Jordan, 11-12: the Bag one press away on the map, with the others)
               (side[3], theme.pokemon_word("POKEMON"), theme.POKEMON, self._open_party),
               (side[2], theme.pokemon_word("POKEDEX"), theme.BAG, self._open_pokedex)]
        if self._fish_spot():   # (beside the water with a rod, as on the routes)
            out.append((side[1], "FISH", (232, 132, 40), self.fish_here))
        mega = self._map_mega_button()   # (Jordan 11-15: the MEGA button in towns too; the Mega's own clock carries between areas)
        if mega:
            r, label, col, fn, enabled, sub = mega
            out.append((r, f"{label} {sub}" if not enabled and sub else label, col, fn if enabled else (lambda: None)))
        return out

    # the map's MEGA button, as on the routes (src/states/overworld/overworld_battle.py; src/pokemon/mega_clock.py)
    from src.states.overworld.overworld_battle import OverworldBattles as _OB
    _mega_rect = _OB._mega_rect
    _map_mega_button = _OB._map_mega_button
    _map_mega = _OB._map_mega
    del _OB

    def _camera(self):
        px, py = self.player
        if getattr(self, "_cam_focus", None):   # (a scene looking somewhere else: 5.7's camera pans)
            px, py = self._cam_focus
        elif self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        _zone = None if getattr(self, "_cam_focus", None) else self._cam_zone(px, py)
        if _zone:   # (a strip where Black 2's camera moves as you cross it: the view slides with you)
            cx, cy = cx + _zone[1][0] * TILE, cy + _zone[1][1] * TILE
        W, H = self._view().size
        mw, mh = self.w * TILE, self.h * TILE  # (the map fills its frame: no black past its edges)
        top = int(((self.town_map or {}).get("view_top") or 0) if not getattr(self, "room", None) and isinstance(getattr(self, "town_map", None), dict) else 0) * TILE
        c3 = getattr(self, "cam3d", None)
        if c3:   # (the view follows you up and down the stairs, and shows the raised ground above row 0)
            cy -= c3.lift(px, py) * TILE
            top, mh = c3.span()
        cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)   # ("view_top": rows left empty above a swapped-in story map)
        cy = (top + mh) / 2 if mh - top <= H else min(max(cy, top + H / 2), mh - H / 2)
        ease = getattr(self, "_cam_ease", None)
        if ease is not None:   # (a scene's pan: the view glides there and back, as the DS camera does)
            return ease
        return cx, cy

    def _cam_tick(self):
        """Once a frame: the view glides toward where it should be while a scene pans it (and back after), and the zoom
        eases toward the map's, its camera zone's or the scene's."""
        now = pygame.time.get_ticks()
        if getattr(self, "_cam_focus", None) or now < getattr(self, "_cam_ease_until", 0):
            self._cam_ease = None
            goal = self._camera()
            cur = getattr(self, "_cam_cur", None) or goal
            cur = (cur[0] + (goal[0] - cur[0]) * 0.12, cur[1] + (goal[1] - cur[1]) * 0.12)
            if abs(cur[0] - goal[0]) < 1 and abs(cur[1] - goal[1]) < 1 and not getattr(self, "_cam_focus", None):
                self._cam_ease_until = 0
            self._cam_ease = cur
            self._cam_cur = cur
        else:
            self._cam_ease = None
            self._cam_cur = self._camera()
        want = getattr(self, "_scene_zoom", None) or self.zoom_now_goal()
        z = getattr(self, "zoom", 1.0)
        self.zoom = want if abs(want - z) < 0.004 else z + (want - z) * 0.1

    def zoom_now_goal(self):
        """The zoom where you stand: a camera zone's (the map's "cameras"), else the map's own (a room's its own)."""
        px, py = self.player
        if self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        _zone = self._cam_zone(px, py)
        return _zone[0] if _zone else getattr(self, "zoom_base", 1.0)

    def _cam_zone(self, fx, fy):
        """(zoom, pan) of the camera zone at (fx, fy), else None (camera3d.camera_zone)."""
        from src.dungeon import camera3d as _c3
        return _c3.camera_zone(getattr(self, "cameras", None), fx, fy)

    def npc_zoom(self, z):
        """A scene moves the camera in or out (None or 1: back to the map's)."""
        self._scene_zoom = float(z) if z and float(z) != 1.0 else None

    def _view(self):
        if getattr(self, "_view_override", None) is not None:   # (drawing zoomed: the smaller picture that's scaled up into the frame)
            return self._view_override
        return dn.map_view(self.game)  # (the map's frame: src/states/overworld/dungeon.py)

    def _origin(self):
        cx, cy = self._camera()
        v = self._view()
        return int(v.centerx - cx) + dn.shake_dx(self), int(v.centery - cy)

    def shake(self, ms=700):
        """The screen shakes a moment (a story scene's tremor)."""
        self._shake_until = pygame.time.get_ticks() + int(ms)

    def _tile_at(self, pos):
        if getattr(self, "_live_cam", None) and self._live():   # (the live camera: the ground under the finger, at your level)
            sc, size, cam, plane, (vx, vy) = self._live_cam
            p = sc.unproject(size, cam, (pos[0] - vx, pos[1] - vy), plane)
            if p is not None:
                return int(p[0] // 1), int(p[1] // 1)
        z = getattr(self, "zoom", 1.0)
        if abs(z - 1.0) > 0.01:   # (the camera zoomed: the point in the map's own picture first)
            v = self._view()
            self._view_override = pygame.Rect(0, 0, round(v.w / z), round(v.h / z))
            try:
                ox, oy = self._origin()
            finally:
                self._view_override = None
            pos = ((pos[0] - v.x) / z, (pos[1] - v.y) / z)
        else:
            ox, oy = self._origin()
        ox -= dn.shake_dx(self)
        if getattr(self, "cam3d", None):   # (raised ground is drawn higher: the tile whose lifted square is under the finger)
            return self.cam3d.tile_at(pos[0] - ox, pos[1] - oy)
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
                    elif self._fish_spot() == t:
                        self.fish_here()
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
                    if self.player != goal and self.anim == 0 and not self._busy() and self._fish_spot() == goal \
                            and not self._open(goal):
                        self.toast_timer = 0   # (a tap on water beside you that you can't walk onto: fish, as on the routes)
                        self.fish_here()
                elif goal in self.doors or goal in self._people() or goal in self.signs or self._open(goal):
                    self.walk_goal = goal
                self._map_press = True  # (held: it keeps walking toward the finger)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self._map_press = False

    def update(self):
        if self.npc_active:
            return super().update()
        self._npc_tick()
        if getattr(self, "_ride", None):   # (riding a cocoon's thread: Castelia Gym)
            return self._ride_tick()
        if not self._busy() and getattr(self, "_phone_area", None) != self.area_key:   # (the phone: a call as you arrive; src/world/phone.py)
            self._phone_area = self.area_key
            from src.world import phone as _phone, vs_seeker as _vs
            _lines = _phone.ring(self.game, self.area_key) or _vs.gift(self.game, self.area_key)   # (the VS Seeker: Vermilion, or a 2nd badge)
            if _lines:
                self.show_message(_lines)
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if self.banner > 0:
            self.banner -= 1
        if self.anim > 0:
            self.anim = max(0, self.anim - (2 if self._may_run() else 1))   # (Shift held: running, Jordan 11-14)
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

    def follower(self):
        """The Pokemon walking behind you: the rowdy Pikachu whenever it's in the party (Yellow), else your lead."""
        from src.pokemon import rowdy
        return rowdy.in_party(self.game.story_manager) or self.lead()

    GATE_ARMS = [[1, 0, 1, 0, 0, 0, 0, 0], [1, 1, 1, 0, 0, 0, 0, 0], [1, 0, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0],
                 [1, 0, 1, 0, 1, 0, 0, 0], [1, 1, 1, 0, 1, 0, 0, 0], [1, 0, 1, 1, 1, 0, 0, 0], [1, 0, 1, 0, 1, 1, 0, 0]]  # (Emerald's own: per shape, N E S W arms, 1 or 2 long)
    GATE_DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    # (Emerald's own, ROM 0x592038 / 0x592058: the tile each arm's near and far half sweeps through, turning each way)
    GATE_SWEEP_CW = [(0, -1), (1, -2), (0, 0), (1, 0), (-1, 0), (-1, 1), (-1, -1), (-2, -1)]
    GATE_SWEEP_ACW = [(-1, -1), (-1, -2), (0, -1), (1, -1), (0, 0), (0, 1), (-1, 0), (-2, 0)]

    def _gate_turn(self, i):
        g = self.turnstiles["gates"][i]
        return int(self.game.story_manager.story_flags.get(f"{self.turnstiles['flag']}_{i}", g["orient"])) % 4

    def _gate_arms(self, i, turn=None):
        """A gate's arms now: [(direction, length)]; its pivot is the top-left corner of its tile "at"."""
        g = self.turnstiles["gates"][i]
        turn = self._gate_turn(i) if turn is None else turn
        row = self.GATE_ARMS[g["shape"]]
        return [((d + turn) % 4, 2 if row[d * 2 + 1] else 1) for d in range(4) if row[d * 2]]

    def _gate_edges(self):
        """The tile edges the gates' arms lie on: {frozenset(tile, tile): (gate, arm direction, its length)}."""
        out = {}
        for i, g in enumerate(self.turnstiles["gates"]):
            px, py = g["at"]
            for d, n in self._gate_arms(i):
                for k in range(1, n + 1):
                    a, b = {0: ((px - 1, py - k), (px, py - k)), 2: ((px - 1, py + k - 1), (px, py + k - 1)),
                            1: ((px + k - 1, py - 1), (px + k - 1, py)), 3: ((px - k, py - 1), (px - k, py))}[d]
                    out[frozenset((a, b))] = (i, d, n)
        return out

    def _turn_gate(self, arm, move):
        """Walking across an arm pushes its gate a quarter turn (its way: the side you push from), if every arm has room
        to swing (Emerald's: the tiles each arm sweeps through)."""
        i, d, _n = arm
        ax, ay = self.GATE_DIRS[d]
        cw = ax * move[1] - ay * move[0] > 0
        if ax * move[1] - ay * move[0] == 0:
            return False
        px, py = self.turnstiles["gates"][i]["at"]
        sweep = self.GATE_SWEEP_CW if cw else self.GATE_SWEEP_ACW
        for d0, n in self._gate_arms(i):
            for k in range(n):
                ox, oy = sweep[d0 * 2 + k]
                t = (px + ox, py + oy)
                if not (0 <= t[0] < self.w and 0 <= t[1] < self.h) or self.rows[t[1]][t[0]] != "." or t in self._people():
                    return False
        flags = self.game.story_manager.story_flags
        flags[f"{self.turnstiles['flag']}_{i}"] = (self._gate_turn(i) + (1 if cw else -1)) % 4
        return True

    def _gate_pieces(self):
        """Emerald's own gate pictures (kanto_handoff em_gate_art.py): a short arm, a long arm (pointing north, the pivot at
        their bottom edge) and the pivot, at this map's scale; each arm turned to each way it can point."""
        cache = self.game.__dict__.setdefault("_gate_pieces", {})
        if TILE not in cache:
            base = os.path.join(self.game.assets.assets_dir, "dungeon", "characters")
            k = TILE / 16
            load = lambda n: pygame.image.load(os.path.join(base, f"em_gate_{n}.png")).convert_alpha()
            arms = {}
            for n, name in ((1, "arm1"), (2, "arm2")):
                img = load(name)
                img = pygame.transform.scale(img, (round(img.get_width() * k), round(img.get_height() * k)))
                arms[n] = {d: pygame.transform.rotate(img, (0, -90, 180, 90)[d]) for d in range(4)}
            piv = load("pivot")
            cache[TILE] = (arms, pygame.transform.scale(piv, (round(piv.get_width() * k), round(piv.get_height() * k))))
        return cache[TILE]

    def _draw_gates(self, screen, ox, oy):
        try:
            arms, piv = self._gate_pieces()
        except (pygame.error, FileNotFoundError):
            return
        for i, g in enumerate(self.turnstiles["gates"]):
            c = (ox + g["at"][0] * TILE, oy + g["at"][1] * TILE)
            for d, n in self._gate_arms(i):
                img = arms[n][d]
                r = img.get_rect()
                setattr(r, ("midbottom", "midleft", "midtop", "midright")[d], c)
                screen.blit(img, r)
            screen.blit(piv, piv.get_rect(center=c))

    def _step_ice(self, t):
        """Onto thin ice (the room's "thin_ice": {"sections": [{"tiles", "flag"}], "fall": the room below, "lines"}): it
        cracks; a cracked one breaks, and you fall to the same spot below. Every tile of a section cracked: its flag (its
        stairs open). True if you fell."""
        ice = self.thin_ice
        cracked = self.__dict__.setdefault("_ice_cracked", set())
        sec = next((s for s in ice["sections"] if list(t) in s["tiles"]), None)
        if sec is None:
            return False
        if tuple(t) in cracked:
            spot = tuple(t)
            self._go(ice["fall"], "")
            self.player = self.partner = self.partner_from = self.anim_from = spot
            self.anim = 0
            self._remember()
            self.flash("The ice broke! You fell to the floor below!", 120)
            return True
        cracked.add(tuple(t))
        flags = self.game.story_manager.story_flags
        if not flags.get(sec["flag"]) and all(tuple(v) in cracked for v in sec["tiles"]):
            flags[sec["flag"]] = True
            keep = (self.player, self.facing)
            self._from_art(self.town_map["rooms"][self.room] if self.room else self.town_map)
            self.player, self.facing = keep
            self.flash("Every tile is cracked! The stairs opened!", 120)
        return False

    def _draw_ice(self, screen, at):
        for t in getattr(self, "_ice_cracked", ()):
            r = at(t)
            c = (236, 248, 255)
            pygame.draw.line(screen, c, (r.x + r.w * 0.2, r.y + r.h * 0.25), (r.centerx, r.centery), 2)
            pygame.draw.line(screen, c, (r.centerx, r.centery), (r.right - r.w * 0.15, r.y + r.h * 0.4), 2)
            pygame.draw.line(screen, c, (r.centerx, r.centery), (r.x + r.w * 0.45, r.bottom - r.h * 0.15), 2)
            pygame.draw.line(screen, (150, 190, 220), (r.x + r.w * 0.45, r.bottom - r.h * 0.15), (r.x + r.w * 0.2, r.bottom - r.h * 0.3), 2)

    def _rot_bars(self):
        """Where the rotating puzzle's blocks stand now (the room's "rotators": {"blocks": {colour: [[TL, BL, BR, TR], ...]}
        each square's corners in the order its arrows carry a block round, "objects": the blocks' first spots, "switches":
        {"x,y": colour}, "flag", "look", "lines"}): each block, as many corners on round its square as its colour's switches
        have been stepped on."""
        rot = getattr(self, "rotators", None)
        if not rot:
            return {}
        flags = self.game.story_manager.story_flags
        out = {}
        for x, y in rot["objects"]:
            spot = (x, y)
            for colour, squares in rot["blocks"].items():
                for sq in squares:
                    cyc = [tuple(c) for c in sq]
                    if spot in cyc:
                        turns = int(flags.get(f"{rot['flag']}_{colour}", 0)) % 4
                        spot = cyc[(cyc.index(spot) + turns) % 4]
            out[spot] = {"look": rot.get("look", "boulder"), "lines": rot.get("lines") or ["It won't budge."]}
        return out

    def _step_switch(self, t):
        rot = getattr(self, "rotators", None)
        if rot and "%d,%d" % tuple(t) in rot.get("switches", {}):  # (a coloured switch: that colour's blocks go round one corner)
            colour = rot["switches"]["%d,%d" % tuple(t)]
            flags = self.game.story_manager.story_flags
            key = f"{rot['flag']}_{colour}"
            flags[key] = (int(flags.get(key, 0)) + 1) % 4
            self.barred = {tuple(tl): bar for bar in getattr(self, "_bar_list", []) if not self._bar_met(bar) and self._bar_here(bar) for tl in bar.get("tiles", [])}
            self.barred.update(self._rot_bars())
            self.flash("Click! The blocks turned!")
            return
        self._mauville_switch(t)

    def _mauville_switch(self, t):
        """On a floor switch (the room's "switches": {"tiles", "flag" flipped, "pressed": the flag that keeps which one is
        down, "start": the one down to begin with, "lines"}): if it isn't down already, it goes down, the rest pop up, and
        the flag flips (the room's barriers and its picture with it)."""
        sw = getattr(self, "switches", None)
        if not sw:
            return
        tiles = [tuple(v) for v in sw["tiles"]]
        if tuple(t) not in tiles:
            return
        flags = self.game.story_manager.story_flags
        i = tiles.index(tuple(t)) + 1
        if flags.get(sw["pressed"], sw.get("start", 0)) == i:
            return
        flags[sw["pressed"]] = i
        flags[sw["flag"]] = not flags.get(sw["flag"])
        self._from_art(self.town_map["rooms"][self.room] if self.room else self.town_map)
        self.flash((sw.get("lines") or ["Click! The barriers changed!"])[0])

    def _gym_ambush_due(self):
        """The Gym's story battle at its door is still to come (its pre_battle_event's flag), before the region's first badge."""
        pe = (self.area_data.get("gym") or {}).get("pre_battle_event") or {}
        if not pe.get("trainer"):
            return False
        story = self.game.story_manager
        if story.badges.get(story.get_current_region()):
            return False
        on = bool(story.story_flags.get(pe.get("flag_check")))
        return (not on) if pe.get("invert_flag") else on

    def start_gym_battle(self):
        """The Leader, in their Gym's room: they want a game first (src/states/overworld/gym_lobby.py leader_in_room)."""
        if getattr(self, "room", None) and str(self.room).startswith(("gym", "league")):
            from src.states.overworld.gym_lobby import leader_in_room
            if self.gym_closed() or (self.area_data.get("gym") or {}).get("pre_battle_event"):
                return super().start_gym_battle()  # (not yet: the Gym's own "come back later"; a story battle first)
            return leader_in_room(self)
        return super().start_gym_battle()

    def light_radius(self):
        """A dark room's light, in tiles (None: fully lit): its "radius" list by how many of its "flags" are set."""
        d = self.dark or {}
        flags = self.game.story_manager.story_flags
        n = sum(1 for f in d.get("flags", []) if flags.get(f))
        radii = d.get("radius") or [2]
        return None if n >= len(radii) else radii[n]

    def _draw_dark(self, screen, view, centre):
        r = self.light_radius()
        if r is None:
            return
        veil = pygame.Surface(view.size, pygame.SRCALPHA)
        veil.fill((0, 0, 0, 250))
        cx, cy = centre[0] - view.x, centre[1] - view.y
        rad = int(r * TILE)
        for i in range(6):  # (a soft edge)
            pygame.draw.circle(veil, (0, 0, 0, 250 - 40 * (i + 1)), (cx, cy), max(1, rad - i * TILE // 8))
        screen.blit(veil, view.topleft)

    def _draw_story_weather(self, screen, view):
        """Weather the story brings to a town, drawn over it outdoors (the area's "story_weather" with "show": "snow": Orange
        5.7's storm over Shamouti during the spheres story; src/world/seasons.py story_weather): a grey sky and falling snow."""
        from src.world import seasons
        w = seasons.story_weather(self.game, self.area_key)
        if not w or w.get("show") not in ("snow", "rain") or getattr(self, "room", None):
            return
        if w.get("show") == "rain":   # (5.7's heavy rain over Shamouti while you look for the Fire Sphere: dark sky, streaks)
            veil = pygame.Surface(view.size, pygame.SRCALPHA)
            veil.fill((30, 40, 60, 90))
            t = pygame.time.get_ticks()
            for i in range(160):
                x = (i * 97 + int(t * 0.25)) % (view.w + 40) - 20
                y = (i * 61 + int(t * (0.9 + (i % 4) * 0.1))) % view.h
                pygame.draw.line(veil, (200, 215, 240, 170), (x, y), (x - 5, y + 14), 2)
            screen.blit(veil, view.topleft)
            return
        veil = pygame.Surface(view.size, pygame.SRCALPHA)
        veil.fill((60, 70, 95, 95))
        t = pygame.time.get_ticks()
        for i in range(140):   # (each flake drifts down and a little sideways, wrapping round the view)
            sp = 0.04 + (i % 5) * 0.012
            x = (i * 137 + int(t * sp * 0.4) + int(6 * ((t // 400 + i) % 3))) % view.w
            y = (i * 89 + int(t * sp)) % view.h
            pygame.draw.circle(veil, (245, 248, 255, 220), (x, y), 2 if i % 3 else 3)
        screen.blit(veil, view.topleft)

    def draw(self):
        # (Jordan, 11-12: no separate scene for someone you talk to: no other background, no picture sliding in. They speak from the map)
        screen = self.game.screen
        fonts = self.game.assets.fonts
        view = self._view()
        screen.fill(dn.FRAME_BLACK)
        z = getattr(self, "zoom", 1.0)
        live = self._live()
        if live:   # (the live camera: the scene drawn at the frame's own size, the zoom in the camera's distance)
            self._view_override = pygame.Rect(0, 0, max(1, round(view.w / z)), max(1, round(view.h / z)))
            try:
                self._cam_tick()
            finally:
                self._view_override = None
            self._draw_live(screen, view, fonts, live, z)
        elif abs(z - 1.0) > 0.01:   # (the camera in closer or further: the map drawn into a smaller or bigger picture, scaled into the frame)
            small = pygame.Rect(0, 0, max(1, round(view.w / z)), max(1, round(view.h / z)))
            off = pygame.Surface(small.size)
            self._view_override = small
            try:
                self._cam_tick()
                self._draw_world(off, small, fonts)
            finally:
                self._view_override = None
            screen.blit(pygame.transform.smoothscale(off, view.size), view.topleft)
        else:
            self._cam_tick()
            self._draw_world(screen, view, fonts)
        if not live:
            self._live_cam = None
        dn.draw_frame(screen, view)
        self._draw_hud(screen, fonts)
        if self.hover_menu_active and self.hover_bg_rect:
            pygame.draw.rect(screen, (255, 255, 255), self.hover_bg_rect, border_radius=12)
            pygame.draw.rect(screen, (0, 0, 0), self.hover_bg_rect, 6, border_radius=12)
        if self.npc_active and self.npc_dialogue:
            self.npc_dialogue.draw(screen)
        self.game.ui_manager.draw(screen)

    def _live(self):
        """(scene, the zone's camera) when this map is drawn by the live camera (Options: 3D camera; a card that draws 3D), else None."""
        lv = getattr(self, "live", None)
        if not lv:
            return None
        from src.core import settings
        from src.dungeon import live3d
        if not settings.get(self.game.story_manager, "live3d") or not live3d.available(self.game):
            return None
        try:
            sc = live3d.scene(self.game, lv["zone"])
        except Exception:   # (a card that can't take the scene: the flat pictures from now on)
            sc = None
        if sc is None:
            self.live = None
            return None
        return sc, lv

    def _draw_live(self, screen, view, fonts, live, z):
        """The map through the live camera (11-21): Black 2's models, everyone stood in them (buildings hide them), the
        camera on you at the zone's own pitch and field of view; then the tags, markers and blockers where tiles land."""
        from src.dungeon import live3d
        sc, lv = live
        c3 = self.cam3d
        T = TILE * z
        screen.fill((10, 14, 24), view)
        screen.set_clip(view)

        def ground(fx, fy):
            return lv["base"] + (c3.lift(fx, fy) / lv["lift_k"] if c3 else 0.0)

        def foot(fx, fy):
            return (fx + 0.5, ground(fx, fy), fy + 0.5)

        cx, cy = getattr(self, "_cam_cur", None) or self._camera()   # (the flat view's centre, gliding and edge-stopped as ever)
        gx, gy0 = cx / TILE - 0.5, cy / TILE - 0.5
        gy = gy0
        for _ in range(3):   # (the flat view draws raised ground higher: back to the tile)
            gy = gy0 + (c3.lift(gx, gy) if c3 else 0.0)
        cam = live3d.framed(foot(gx, gy), lv["pitch"], lv["fov"], T, view.h)
        size = view.size
        sprites, shadows, emotes = [], [], []

        def stand(img, fx, fy):
            if img is not None:
                sprites.append((img, foot(fx, fy), img.get_height() / TILE))
                shadows.append(foot(fx, fy))

        people = self._people()
        by_pos = {mo.pos: mo for mo in getattr(self, "motions", {}).values() if not mo.gone}
        for spot, opt in people.items():
            mo = by_pos.get(spot)
            img = self._figure_img(opt, mo.facing, mo.frame()) if mo else self._figure_img(opt)
            fx, fy = mo.at() if mo else spot
            stand(img, fx, fy)
            if mo and mo.emote > 0:
                emotes.append((fx, fy))
            _ev = next((o["event"] for o in ((opt.get("any") or [opt]) if isinstance(opt, dict) else [])
                        if isinstance(o, dict) and isinstance(o.get("event"), dict) and (o["event"].get("battle") or {}).get("rematch")), None)
            if _ev is not None:
                from src.world import vs_seeker as _vsm
                if _vsm.is_ready(self.game.story_manager, self.area_key, _vsm.town_key(_ev)):
                    emotes.append((fx, fy))
        k = 1 - self.anim / STEP if self.anim > 0 else 1
        (fx, fy), (tx, ty) = self.anim_from, self.player
        me_at = (fx + (tx - fx) * k, fy + (ty - fy) * k)
        lead = self.follower()
        if lead and self.partner != self.player:
            (ax, ay), (bx, by) = self.partner_from, self.partner
            way = (tx - bx, ty - by)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            stand(self._icon(lead, TILE, flip=(tx > bx), facing=way), ax + (bx - ax) * k, ay + (by - ay) * k)
        stand(self._player_img(), *me_at)
        for a in (self.scenes.actors if getattr(self, "scenes", None) else []):   # (a scene's cast, walking in and out)
            stand(self._actor_img(a["sheet"], a["m"].facing, a["m"].frame(), native=bool(a.get("native"))), *a["m"].at())
        flat_bars = []
        for _t, _bar in getattr(self, "barred", {}).items():
            _look = str(_bar.get("look") or "person")
            if _look == "unseen" or _look.startswith("img:"):
                continue
            _img = self._stand_in_img(_look, _bar) if _look.startswith(("sheet:", "ow:", "mon:", "ribbon:")) else None
            if _img is not None:
                stand(_img, *_t)
            elif not _look.startswith("ribbon:"):
                flat_bars.append((_t, _look))
        img = sc.render(size, cam, sprites, shadows=shadows if getattr(self, "shadows", False) else ())
        screen.blit(img, view.topleft)
        self._live_cam = (sc, size, cam, foot(gx, gy)[1], view.topleft)
        s = max(1, round(T))

        def at(t):
            p = sc.project(size, cam, foot(t[0], t[1]))
            if p is None:
                return pygame.Rect(-999, -999, s, s)
            return pygame.Rect(round(view.x + p[0] - s / 2), round(view.y + p[1] - s / 2), s, s)

        if self.walk_goal:
            theme.tap_marker(screen, at(self.walk_goal))
        if self.tap_mark and self.tap_mark[2] > 0 and self.tap_mark[0] != self.walk_goal:
            theme.tap_marker(screen, at(self.tap_mark[0]), self.tap_mark[1])
            self.tap_mark[2] -= 1
        from src.dungeon import art
        for _t, _look in flat_bars:
            art.blocker(screen, at(_t), _look)
        for ex, ey in emotes:
            r = at((ex, ey))
            theme.shadow_text(screen, "!", fonts["label"], r.centerx - 4, r.y - 34, color=(230, 60, 50))
        pr = at(me_at)
        self._me_drawn = (pr.copy(), (0, 0))   # (where you were drawn, for the checks)
        self._draw_tags(screen, view, fonts, at, people, pr.center)
        screen.set_clip(None)

    def _draw_world(self, screen, view, fonts):
        """The map in its frame: ground, people, buildings, tags, the guide (draw() adds the frame and the HUD)."""
        screen.fill((10, 14, 24), view)
        screen.set_clip(view)  # (the map stays in its frame)
        ox, oy = self._origin()
        c3 = getattr(self, "cam3d", None)

        def lp(fx, fy):   # (how many px the ground there is raised on screen: B2W2's terraces and stairs)
            return round(c3.lift(fx, fy) * TILE) if c3 else 0

        if c3:
            c3.draw_ground(screen, ox, oy)
        else:
            screen.blit(self.map_img, (ox, oy))

        def at(t):
            return pygame.Rect(ox + t[0] * TILE, oy + t[1] * TILE - lp(t[0], t[1]), TILE, TILE)

        feet = {}   # (whose shadow goes under them: id of their drawn rect -> where their feet are)

        if getattr(self, "thin_ice", None):
            self._draw_ice(screen, at)
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
                r = pygame.Rect(int(ox + fx * TILE), int(oy + fy * TILE) - lp(fx, fy), TILE, TILE)
            else:
                fx, fy = spot
                r = at(spot)
            if img is not None:
                drawn.append((int(oy + (fy + 1) * TILE), img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
                feet[id(drawn[-1][2])] = (r.centerx, r.bottom - 3)
            if mo and mo.emote > 0:  # (they've noticed you: a "!" over them, drawn after everyone)
                emotes.append((r.centerx - 4, r.y - 34))
            _ev = next((o["event"] for o in ((opt.get("any") or [opt]) if isinstance(opt, dict) else [])
                        if isinstance(o, dict) and isinstance(o.get("event"), dict) and (o["event"].get("battle") or {}).get("rematch")), None)
            if _ev is not None:   # (the VS Seeker called it back: Seven Island's Psychics; a "!" over them)
                from src.world import vs_seeker as _vsm
                if _vsm.is_ready(self.game.story_manager, self.area_key, _vsm.town_key(_ev)):
                    emotes.append((r.centerx - 4, r.y - 34))
        k = 1 - self.anim / STEP if self.anim > 0 else 1
        lead = self.follower()
        me = self._player_img()
        _pose = self._ride_pose() if getattr(self, "_ride", None) else None
        if _pose:   # (the cocoon ride: you shrink into one cocoon and grow out of the other; your Pokemon rides in your Ball)
            lead = None
            if _pose[3] or me is None:
                me = None
            else:
                me = pygame.transform.smoothscale(me, (max(1, int(me.get_width() * _pose[2])), max(1, int(me.get_height() * _pose[2]))))
        _mine_rects = []   # (you and your Pokemon: (rect, from, to), drawn under a bridge you pass beneath)
        pr = pygame.Rect(0, 0, TILE, TILE)
        fx, fy = self.anim_from
        tx, ty = self.player
        pr.topleft = (int(ox + (fx + (tx - fx) * k) * TILE), int(oy + (fy + (ty - fy) * k) * TILE))
        if _pose:
            pr.move_ip(int(_pose[0] * TILE), int(_pose[1] * TILE))
        _me_key = pr.bottom
        pr.y -= lp(fx + (tx - fx) * k, fy + (ty - fy) * k)   # (up and down the stairs, smoothly)
        self._me_drawn = (pr.copy(), (ox, oy))   # (where you were drawn, for the checks)
        if lead and self.partner != self.player:
            (ax, ay), (bx, by) = self.partner_from, self.partner
            r = pygame.Rect(int(ox + (ax + (bx - ax) * k) * TILE), int(oy + (ay + (by - ay) * k) * TILE), TILE, TILE)
            _key = r.bottom
            r.y -= lp(ax + (bx - ax) * k, ay + (by - ay) * k)
            way = (tx - bx, ty - by)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            img = self._icon(lead, TILE, flip=(tx > bx), facing=way)
            if img is not None:
                drawn.append((_key, img, img.get_rect(midbottom=(r.centerx, r.bottom - 2))))
                feet[id(drawn[-1][2])] = (r.centerx, r.bottom - 3)
                _mine_rects.append((drawn[-1][2], tuple(self.partner_from), tuple(self.partner)))
        if me is not None:
            drawn.append((_me_key, me, me.get_rect(midbottom=(pr.centerx, pr.bottom))))
            feet[id(drawn[-1][2])] = (pr.centerx, pr.bottom - 2)
            _mine_rects.append((drawn[-1][2], tuple(self.anim_from) if self.anim > 0 else tuple(self.player), tuple(self.player)))
        _shadow = None
        if getattr(self, "shadows", False):
            from src.dungeon import camera3d as _c3
            _shadow = _c3.shadow(TILE)
        _all = drawn + (c3.buildings_drawn(ox, oy, view) if c3 else [])   # (the buildings in depth order with everyone: you walk behind them)
        for _b, img, rect in sorted(_all, key=lambda t: t[0]):
            if _shadow is not None and id(rect) in feet:
                screen.blit(_shadow, _shadow.get_rect(center=feet[id(rect)]))
            screen.blit(img, rect)
        for a in (self.scenes.actors if getattr(self, "scenes", None) else []):  # a scene's cast, walking in and out
            ax, ay = a["m"].at()
            img = self._actor_img(a["sheet"], a["m"].facing, a["m"].frame(), native=bool(a.get("native")))
            if img is not None:
                r = pygame.Rect(int(ox + ax * TILE), int(oy + ay * TILE) - lp(ax, ay), TILE, TILE)
                if _shadow is not None:
                    screen.blit(_shadow, _shadow.get_rect(center=(r.centerx, r.bottom - 3)))
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
        for ex, ey in emotes:
            theme.shadow_text(screen, "!", fonts["label"], ex, ey, color=(230, 60, 50))
        if getattr(self, "_ride", None):
            self._draw_ride_silk(screen, ox, oy)
        for _t, _bar in getattr(self, "barred", {}).items():
            _look = str(_bar.get("look") or "person")
            if _look == "unseen":  # (something invisible in the way: Fortree's Kecleon, till the Devon Scope)
                continue
            if _look.startswith("img:"):  # (a still picture of the real game's own, a tile's size: Mossdeep Gym's blocks)
                _ic = self.game.__dict__.setdefault("_bar_imgs", {})
                if _look not in _ic:
                    try:
                        _ic[_look] = pygame.transform.scale(pygame.image.load(os.path.join(
                            self.game.assets.assets_dir, "dungeon", "characters", _look[4:])).convert_alpha(), (TILE, TILE))
                    except (pygame.error, FileNotFoundError):
                        _ic[_look] = None
                if _ic[_look] is not None:
                    screen.blit(_ic[_look], at(_t))
                continue
            _img = self._stand_in_img(_look, _bar) if _look.startswith(("sheet:", "ow:", "mon:", "ribbon:")) else None
            if _img is None and _look.startswith("ribbon:"):
                continue
            if _img is not None:  # (a real game's own sprite: a boat at the pier, someone in the way)
                _nx, _ny = _bar.get("nudge") or (0, 0)   # (drawn off its tile's centre, in tiles: a portrait across its two-tile frame)
                screen.blit(_img, _img.get_rect(midbottom=(int(at(_t).centerx + _nx * TILE), int(at(_t).bottom - 2 + _ny * TILE))))
                continue
            from src.dungeon import art
            art.blocker(screen, at(_t), _look)
        if getattr(self, "bridge", None):  # (passing under a bridge: it goes over your head, every tile you overlap; Virbank's
            #  underpass beneath its main street too, 11-20)
            from src.dungeon import art as _ab
            _under = [rc for rc, fr_, to_ in _mine_rects if _ab.under_bridge(self.bridge, fr_, to_, self.deck)]
            _ab.bridge_over(screen, self.bridge, _under, (ox, oy), TILE, self.map_img)
        for _o, img, (bx, by) in getattr(self, "overheads", []):  # (solid, over you: you walk under it, out of view)
            screen.blit(img, (ox + bx, oy + by))
        from src.dungeon import art as _art
        _art.over_uncovered(screen, drawn, [(img, at_) for _o, img, at_ in getattr(self, "overheads", [])], (ox, oy))
        self._draw_tags(screen, view, fonts, at, people, pr.center)
        screen.set_clip(None)

    def _draw_tags(self, screen, view, fonts, at, people, centre):
        """Over the map: the buildings' names, the ways out, who people are, gates, the dark, the weather, the guide (at(tile):
        where a tile is on screen: the flat picture's, or the live camera's)."""
        # the buildings' names over their doors, who the people are, where the ways out go
        _named = []   # (a building with several door tiles, the Dept. Store's two: its name once)
        for spot, kind in sorted(self.doors.items()):
            if kind == "house" or (kind == "home" and spot != min(t for t, k2 in self.doors.items() if k2 == "home")):
                continue
            if any(k2 == kind and abs(s2[0] - spot[0]) + abs(s2[1] - spot[1]) <= 6 for s2, k2 in _named):
                continue
            _named.append((spot, kind))
            label = LABELS.get(kind) or next((o.get("text", "") for o in self.area_data.get("explore_options", [])
                                              if o.get("door") == kind and o.get("action") not in (None, "EVENT")), "").upper()
            if label:   # (a landmark or a place the story names; a plain house or room has no tag)
                self._pill(screen, label, at(spot).centerx, at(spot).y - 6, fonts)
        ways = {}
        for spot, target in self.exits.items():
            ways.setdefault(target, []).append(spot)
        for target, tiles in ways.items():
            tiles.sort()
            t = tiles[len(tiles) // 2]
            name = (self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(target) or {}).get("route_name") or target
            if str(target).startswith(("OUT:", "ROOM:")):  # (a room's mat or stairs: no place of their own to name, no tag)
                continue
            self._pill(screen, str(name).upper(), at(t).centerx, at(t).centery + 10, fonts)
        from src.states.overworld.common import _fill_names
        taken = []  # (name tags that would sit on top of one another: the one with something to do is shown: a row of clerks)
        for spot, opt in sorted(people.items(), key=lambda kv: (kv[1].get("action") == "EVENT" and not (kv[1].get("event") or {}).get("battle"), kv[0])):
            if not important_person(opt):   # (townsfolk who only chat: no tag)
                continue
            self._pill(screen, _fill_names(self.game, opt.get("who") or opt.get("text", "")).upper()[:28], at(spot).centerx,  # ("who": the person, when the option says what they offer)
                       at(spot).y - 34, fonts, taken)
        if getattr(self, "turnstiles", None):
            self._draw_gates(screen, *self._origin())
        if getattr(self, "dark", None):
            self._draw_dark(screen, view, centre)
        if self.room is None:
            self._draw_story_weather(screen, view)
        if not self._busy():
            self._draw_guide(screen, at)

    @staticmethod
    def _pill(screen, text, cx, bottom, fonts, taken=None):
        box = screen.get_clip()  # (the map's frame, while the map is drawn)
        if not (box.x - 60 <= cx <= box.right + 60 and box.y - 40 <= bottom <= box.bottom + 60):
            return  # (off screen: no tag piling up at the edge)
        tag = fonts["caption"].render(theme.pokemon_word(text).replace("É", "é"), True, (255, 255, 255))  # (in capitals the game writes POKéMON: the font has no capital É)
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
        key = (self.player, getattr(self, "room", None), pygame.time.get_ticks() // 1000)
        if getattr(self, "_guide_key", None) == key:
            return self._guide_hit
        self._guide_key, self._guide_hit = key, None
        mission = guide.tracked_mission(self.game)
        if not mission:
            return None
        if getattr(self, "town_map", None):  # (our own maps: through the rooms too, 11-17)
            aim = self._guide_aim(mission)
            self._guide_hit = self._guide_toward(*aim) if aim else None
            return self._guide_hit
        if getattr(self, "room", None):   # (a room of the old picture towns: none there)
            return None
        px, py = self.player
        near = lambda t: abs(t[0] - px) + abs(t[1] - py)
        for spot, opt in sorted(self._people().items(), key=lambda kv: near(kv[0])):
            if guide.advances_goal(self.game, self.area_key, opt, mission):
                self._guide_hit = (spot, "Here")
                return self._guide_hit
        for spot, kind in sorted(self.doors.items(), key=lambda kv: near(kv[0])):
            if any(guide.advances_goal(self.game, self.area_key, o, mission) for o in self._door_options(kind)):
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

    # The Journal's marker through a place and its rooms (Jordan, 11-17: "the marker always leads the next step").
    # _guide_aim says where the mission's next thing is (a room of this place, or outside, and a tile); _guide_toward
    # gives the tile to head for from where you stand: that tile, or the door / mat / stairs that starts the way to it.
    def _car_floor(self, room):
        """A lift car's floor now (its "dynamic_exit" {"flag", "rooms", "default"}: Kumquat Hotel's, 5.7's 39.0), else None."""
        dyn = ((self.town_map.get("rooms") or {}).get(room) or {}).get("dynamic_exit") if room and isinstance(getattr(self, "town_map", None), dict) else None
        if not dyn:
            return None
        return str(self.game.story_manager.story_flags.get(dyn["flag"]) or dyn.get("default"))

    def _guide_part(self, room):
        """What a room of this place (None: the map itself) holds, read from its map without walking in: its ways out
        {tile: target}, doors {tile: kind}, people {tile: option} and pads {tile: room}."""
        from src.dungeon import art
        cache = self.__dict__.setdefault("_guide_parts", {})
        key = (room, getattr(self, "_cleared", ""), self._has("HM_SURF"), self._has_waterfall(), id(self.town_map), self._car_floor(room))
        if key in cache:
            return cache[key]
        m = self.town_map["rooms"][room] if room else self.town_map
        grid = m["art"]
        for c in getattr(self, "_cleared", ""):
            grid = [row.replace(c, ".") for row in grid]
        kinds, ways = m.get("buildings", {}), m.get("exits", {})
        part = {"exits": {}, "doors": {}, "people": {}, "pads": {}, "open": set(), "grid": grid, "stops": {tuple(t) for t in m.get("stops", [])}}
        deep = art.SEA_CHARS if m.get("surf", True) else ""   # (as _from_art: water needs Surf)
        wade = {tuple(t) for t in m.get("wade", [])}
        if m.get("dynamic_exit"):   # (a lift car: its doors open on the floor it's at now)
            ways = {c: ("ROOM:" + self._car_floor(room) if str(v).startswith("ROOM:") else v) for c, v in ways.items()}
        for (x, y), letter in art.doors(grid).items():
            target = ways.get(letter) or (ways.get("D") if kinds.get(letter) == "gate" else None)
            if target:
                part["exits"][(x, y)] = target
            else:
                part["doors"][(x, y)] = kinds.get(letter, "house")
        names = list(m.get("people", []))
        options = {o.get("text"): o for o in self.area_data.get("explore_options", [])}
        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c in art.EXIT_CHARS and c in ways:
                    part["exits"][(x, y)] = ways[c]
                elif c == "N" and names:
                    who = names.pop(0)
                    opt = who if isinstance(who, dict) else None if isinstance(who, list) else options.get(who)
                    if isinstance(who, str) and who.startswith("door:"):
                        opt = {"any": [o for o in self.area_data.get("explore_options", []) if option_kind(o) == who[5:]]
                               + [dict(o, action="TRAVEL") for o in self.area_data.get("travel_options", []) if o.get("door") == who[5:]]}
                    if isinstance(who, list):
                        opt = {"any": [w if isinstance(w, dict) else options[w] for w in who if isinstance(w, dict) or w in options]}
                    if opt:
                        part["people"][(x, y)] = opt
                if (key[3] if c == "$" else key[2] if c in deep and (x, y) not in wade else c in art.OPEN and (not m.get("walk_on") or c in m["walk_on"])) \
                        and (x, y) not in part["doors"]:
                    part["open"].add((x, y))
        part["open"] |= set(part["exits"])
        for k, to in (m.get("links") or {}).items():  # (a pad: to its far pad in this room (""), or into another room)
            part["pads"][tuple(int(v) for v in k.split(","))] = (to[0] if isinstance(to[0], str) else "", to[1], to[2])
        cache[key] = part
        return part

    def _guide_passages(self, room):
        """[(tile, the room it leads to (None: outside), what kind)] for a room's doors, mats, stairs and pads."""
        part, out = self._guide_part(room), []
        rooms = self.town_map.get("rooms") or {}
        for t, target in part["exits"].items():
            target = str(target)
            if target.startswith("OUT:"):
                out.append((t, None, "out"))
            elif target.startswith("ROOM:"):
                to = None if target[5:] == "MAIN" else target[5:]
                if to is None or to in rooms:
                    out.append((t, to, "stairs"))
        dyn = (rooms.get(room) or {}).get("dynamic_exit") if room else None
        if dyn:   # (a lift car leads to every floor it serves: its attendant takes you there)
            mat = next((t for t, target in part["exits"].items() if str(target).startswith("ROOM:")), None)
            out += [(mat, to, "stairs") for to in dyn.get("rooms") or [] if mat is not None and to in rooms and to != self._car_floor(room)]
        if room is None:
            for t in part["doors"]:
                to = (self.town_map.get("inside") or {}).get("%d,%d" % t)
                if to in rooms:
                    out.append((t, to, "door"))
        for t, (to, _x, _y) in part["pads"].items():
            if to in rooms:
                out.append((t, to, "pad"))
        return out

    def _guide_rooms(self):
        """{room: (how many passages from where you are, the passage of this room that starts the way)}."""
        here = getattr(self, "room", None)
        seen, q = {here: (0, None)}, deque([here])
        while q:
            cur = q.popleft()
            for t, to, kind in self._guide_passages(cur):
                if to not in seen:
                    seen[to] = (seen[cur][0] + 1, seen[cur][1] or (to, kind) if cur != here else (to, kind))
                    q.append(to)
        return seen

    def _guide_aim(self, mission):
        """(tiles, label) of what the tracked mission needs in this place, tiles a set of (room, tile) (room None: the
        map itself): its next step's spot, else someone or a door that does what it needs, else the ways out toward
        its next stop. None: nothing here."""
        from src.world import guide
        game, here = self.game, getattr(self, "room", None)
        rooms = self.town_map.get("rooms") or {}
        step = guide.current_step(game, mission)
        if step and step.get("at") and "floor" not in step and (step.get("room") is None or step["room"] in rooms) \
                and step.get("area", guide.mission_target(game, mission)) == self.area_key:
            return ({(step.get("room"), tuple(step["at"]))}, step.get("label") or "Here")
        reach = self._guide_rooms()
        px, py = self.player
        near = lambda t: abs(t[0] - px) + abs(t[1] - py)
        for room in sorted(reach, key=lambda r: (reach[r][0], str(r))):
            part = self._guide_part(room)
            people = self._people() if room == here else \
                {t: (next((o for o in opt["any"] if self._shown(o)), None) if "any" in opt else opt)
                 for t, opt in part["people"].items() if self._shown(opt)}
            for spot, opt in sorted(people.items(), key=lambda kv: near(kv[0])):
                if opt and guide.advances_goal(game, self.area_key, opt, mission):
                    return ({(room, spot)}, "Here")
            if room is None:
                for spot, kind in sorted(part["doors"].items(), key=lambda kv: near(kv[0])):
                    if any(guide.advances_goal(game, self.area_key, o, mission) for o in self._door_options(kind)):
                        return ({(room, spot)}, "Here")
        ways = {}   # area -> {(room, tile)}: the ways out of the place, from any of its rooms; a door that is a place of its own
        for room in reach:
            part = self._guide_part(room)
            for t, target in part["exits"].items():
                if not str(target).startswith(("OUT:", "ROOM:")):
                    ways.setdefault(target, set()).add((room, t))
            for t, opt in part["people"].items():   # (whoever runs a way out from inside its building: the harbour's sailor and the boats)
                for o in (opt["any"] if "any" in opt else [opt]):
                    to = guide.leads_to(game, self.area_key, o) if self._shown(o) else None
                    if to:
                        ways.setdefault(to, set()).add((room, t))
        if None in reach:
            for t, kind in self._guide_part(None)["doors"].items():
                for o in self._door_options(kind):
                    to = guide.leads_to(game, self.area_key, o)
                    if to and to not in ways:
                        ways[to] = {(None, t)}
        hop = guide.map_hop(game, list(ways))
        if not hop or hop == self.area_key or hop not in ways:
            return None
        return (ways[hop], self._exit_label(hop))

    def _guide_walk(self, goals):
        """The shortest walk from where you stand to one of goals ({(room, tile)}), over this place's rooms: through
        doors, mats, stairs and pads, round whoever and whatever stands in the way now. -> (the goal reached, the first
        door / mat / stairs / pad on the way and its kind, or None when the goal is in this room), or None: no way."""
        here = getattr(self, "room", None)
        rooms = self.town_map.get("rooms") or {}
        inside = self.town_map.get("inside") or {}
        shut, parts = {}, {}   # room -> tiles nobody can stand on now: its people, whatever bars the way
        P = lambda room: parts.get(room) or parts.setdefault(room, self._guide_part(room))
        busy = set(self._people()) | set(self._rot_bars())   # (what bars the way as the story stands this moment: the map's own list is looked at afresh, a gate just opened counts)
        for bar in getattr(self, "_bar_list", []):
            if not self._bar_met(bar) and self._bar_here(bar):
                busy.update(tuple(t) for t in bar.get("tiles", []))
        surf, cut, fall = self._has("HM_SURF"), self._has("HM_CUT"), self._has_waterfall()
        rows, ways = self.rows, self.exits

        def closed(room):
            if room not in shut:
                part = P(room)
                m = rooms[room] if room else self.town_map
                no = {t for t, opt in part["people"].items() if self._shown(opt)}
                for bar in m.get("barred", []):
                    if not self._bar_met(bar) and self._bar_here(bar):
                        no.update(tuple(t) for t in bar.get("tiles", []))
                shut[room] = no
            return shut[room]

        def free(room, t):
            if room == here:
                x, y = t
                if not (0 <= x < self.w and 0 <= y < self.h) or t in busy:
                    return False
                c = rows[y][x]
                return c == "." or t in ways or (c == "o" and surf) or (c == "2" and cut) or (c == "$" and fall)
            part = P(room)
            return t in part["open"] and t not in closed(room)

        def arrive(room, came):
            """Where you stand in a room, come in by its way out that leads back to came (as _go does)."""
            part = P(room)
            if room is None and came.startswith("OUT:"):
                x, y = (int(v) for v in came[4:].split(","))
                return (x, y + 1) if free(None, (x, y + 1)) else (x, y - 1) if free(None, (x, y - 1)) else None
            mats = sorted(t for t, target in part["exits"].items() if target == came)
            if not mats:
                return None
            t = mats[len(mats) // 2]
            return next(((t[0] + dx, t[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
                         if free(room, (t[0] + dx, t[1] + dy)) and (t[0] + dx, t[1] + dy) not in part["exits"]), None)

        def beyond(room, t):
            """(where a door, mat, stairs or pad on t takes you, its kind), or None."""
            part = P(room)
            target = part["exits"].get(t)
            if target is not None:
                target = str(target)
                if target.startswith("OUT:"):
                    return ((None, arrive(None, target)), "out")
                if target.startswith("ROOM:"):
                    to = None if target[5:] == "MAIN" else target[5:]
                    return ((to, arrive(to, "ROOM:" + (room or "MAIN"))), "stairs") if to is None or to in rooms else None
                return None
            if room is None and t in part["doors"]:
                to = inside.get("%d,%d" % t)
                return ((to, arrive(to, "OUT:%d,%d" % t)), "door") if to in rooms else None
            if t in part["pads"]:
                to, x, y = part["pads"][t]
                to = room if to == "" else to
                return ((to, (x, y)), "pad") if to == room or to in rooms else None
            return None

        start = (here, tuple(self.player))
        prev, q = {start: None}, deque([start])
        found = None
        while q and found is None:
            cur = q.popleft()
            room, (x, y) = cur
            part = P(room)
            grid = part["grid"]
            for dx, dy in DIRS:
                n = (x + dx, y + dy)
                if (room, n) in goals:
                    found = (room, n)
                    prev[found] = (cur, None)
                    break
                if 0 <= n[1] < len(grid) and 0 <= n[0] < len(grid[0]) and grid[n[1]][n[0]] == "m":   # (someone behind a counter: talked to across it)
                    over = next(((room, (n[0] + k * dx, n[1] + k * dy)) for k in (1, 2) if (room, (n[0] + k * dx, n[1] + k * dy)) in goals), None)
                    if over:
                        found = over
                        prev[found] = (cur, None)
                        break
                on = beyond(room, n)
                if on is not None:
                    dest, kind = on
                    if dest[1] is not None and dest not in prev:
                        prev[dest] = (cur, (n, kind))
                        q.append(dest)
                    continue
                if n not in part["exits"] and n not in part["doors"] and free(room, n):
                    if grid[n[1]][n[0]] in "3456":   # (a spin tile: it carries you its way till something stops you, or a stop tile does)
                        way = {"3": (-1, 0), "4": (1, 0), "5": (0, -1), "6": (0, 1)}
                        d = way[grid[n[1]][n[0]]]
                        for _ in range(len(grid) * len(grid[0])):
                            nxt = (n[0] + d[0], n[1] + d[1])
                            if not free(room, nxt) or nxt in part["doors"]:
                                break
                            n = nxt
                            if grid[n[1]][n[0]] in way:
                                d = way[grid[n[1]][n[0]]]
                            elif n in part["stops"] or n in part["exits"] or n in part["pads"]:
                                break
                        on = beyond(room, n) if n in part["exits"] else None
                        if on is not None:
                            if on[0][1] is not None and on[0] not in prev:
                                prev[on[0]] = (cur, (n, on[1]))
                                q.append(on[0])
                            continue
                    if (room, n) not in prev:
                        prev[(room, n)] = (cur, None)
                        q.append((room, n))
        if found is None:
            return None
        first, node = None, found
        while prev[node] is not None:
            node, via = prev[node]
            if via is not None:
                first = via
        return (found, first)

    def _guide_toward(self, goals, label):
        """The tile to head for now: the nearest of the goals you can walk to when it's in this room (a person: where
        they stand now), else the door, mat, stairs or pad that starts the way to it. With no way you can walk yet:
        what opens one in this room (a quiz machine, a trash can to search), else the goal itself, or the first
        passage toward its room."""
        here = getattr(self, "room", None)
        mos = getattr(self, "motions", {})
        live = lambda t: mos[t].pos if t in mos and not mos[t].gone else t   # (a person: where they stand now)
        goals = {(r, live(tuple(t)) if r == here else tuple(t)) for r, t in goals}
        px, py = self.player
        near = lambda t: (abs(t[0] - px) + abs(t[1] - py), t)
        names = {"out": "Way out", "stairs": "Stairs", "pad": "Warp", "door": "Here"}
        if (here, tuple(self.player)) in goals:
            return (tuple(self.player), label)
        hit = self._guide_walk(goals)
        if hit:
            (room, tile), first = hit
            if first is None:
                return (tile, label)
            if first[0] == tuple(self.player):   # (you're standing on the pad to take: step off it, then back on)
                off = next(((px + dx, py + dy) for dx, dy in DIRS if self._open((px + dx, py + dy)) and (px + dx, py + dy) not in self.exits
                            and (px + dx, py + dy) not in getattr(self, "links", {})), None)
                if off:
                    return (off, names[first[1]])
            return (first[0], label if first[1] == "door" and room != here and len({r for r, _t in goals}) == 1
                    and self._guide_rooms().get(room, (9, None))[0] == 1 else names[first[1]])
        mine = sorted((t for r, t in goals if r == here), key=near)
        if mine:   # (it's in this room, and there's no way to it yet)
            unlock = self._guide_unlock()
            return unlock or (mine[0], label)
        rooms = self._guide_rooms()
        room = min((r for r, _t in goals), key=lambda r: (rooms.get(r, (99, None))[0], str(r)))
        first = rooms.get(room, (0, None))[1]
        if not first:
            return None
        ways = {t for t, target in self.exits.items() if str(target).startswith(("OUT:", "ROOM:"))} | set(self.doors) | set(getattr(self, "room_links", {}))
        tiles = [(t, kind) for t, to, kind in self._guide_passages(here) if to == first[0] and t in ways]
        if not tiles:
            return None
        t, kind = min(tiles, key=lambda tk: near(tk[0]))
        return (t, names.get(kind, "Here"))

    def _guide_unlock(self):
        """(tile, label) of what opens the way on in this room, when the Journal's spot can't be walked to yet: the
        nearest quiz machine not answered that you can walk to (Cinnabar Gym's), the next trash can to search
        (Vermilion Gym's: the marker goes from can to can, it doesn't know where the switches are)."""
        px, py = self.player
        near = lambda t: (abs(t[0] - px) + abs(t[1] - py), t)
        flags = self.game.story_manager.story_flags
        here = getattr(self, "room", None)
        todo = [t for t, ev in getattr(self, "sign_events", {}).items()
                if not flags.get((ev.get("event") or {}).get("flag")) and (near(t)[0] == 1 or self._guide_walk({(here, t)}))]
        if todo:
            return (min(todo, key=near), "Quiz")
        room = (self.town_map.get("rooms") or {}).get(getattr(self, "room", None)) or {}
        tc = room.get("trashcans")
        if tc and not flags.get(tc["open"]):
            cans, cols = [tuple(c) for c in tc["cans"]], int(tc.get("cols", 5))
            tried = getattr(self, "_cans_tried", set())
            left = [i for i in range(len(cans)) if i not in tried]
            if flags.get(tc["first"]) and getattr(self, "_can_first", None) is not None:   # (the second switch is in a can next to the first)
                r, c = divmod(self._can_first, cols)
                beside = [rr * cols + cc for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                          if 0 <= cc < cols and 0 <= rr and rr * cols + cc < len(cans)]
                left = [i for i in beside if i not in tried] or beside
            if left:
                return (min((cans[i] for i in left), key=near), "Search")
        return None

    def _guide_lift(self, t):
        """How high the Journal's arrow sits over a tile that already has a name tag (None: no tag there, so the arrow
        brings its own)."""
        if t in self._people():
            return 70 if important_person(self._people()[t]) else None  # (over the person's name)
        if t in self.doors:
            kind = self.doors[t]
            named = kind not in ("house", "home") and (LABELS.get(kind) or any(o.get("door") == kind and o.get("action") not in (None, "EVENT")
                                                                             for o in self.area_data.get("explore_options", [])))
            return 44 if named else None  # (over the building's name)
        if t in self.exits and not str(self.exits[t]).startswith(("OUT:", "ROOM:")):
            return 44  # (a way out's name sits low on its tile)
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
        if not (getattr(self, "dark", None) and self.light_radius() is not None):  # (a dark room's map isn't given away)
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
