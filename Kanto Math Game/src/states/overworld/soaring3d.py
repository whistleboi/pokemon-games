"""Soaring in the Sky, 3D (Jordan, 11-14: "baked 2.5D, phone-safe"): fly Mega Latios / Latias over Omega Ruby's
own Hoenn, seen from behind as in ORAS. Pygame only: no 3D library, so it runs in Pydroid as the rest does.

How it's drawn: the ground is the game's sky map baked flat from above (assets/soaring3d/ground*.jpg, made from
Jordan's Omega Ruby file by kanto_handoff/oras_rom_tools/bake_soaring3d.py) and laid out in perspective a row at a
time ("Mode 7"): each frame a square of the ground round you is turned so you face up, and every screen row below
the horizon is one strip of it, stretched. Nearer rows read a finer picture, farther rows coarser ones. The Eon is
Jordan's back sprite (the 2D version's), leaning into turns; or, with EON_LOOK = "model", one of the baked
pictures of Omega Ruby's model from behind (5 bank x 3 pitch angles). Spots, the rift, the storm
cloud and wild Pokemon are pictures standing in the world, smaller the farther they are.

Controls: Left / Right turn, Up / Down climb and dive, hold Space (or FAST) to speed up; with a finger or the mouse,
hold where you want to go (left/right turns, high climbs, low dives). LAND (or Esc) sets you down at the nearest town
you've been to. Fly over a Mirage place to land there; into the rift or the storm cloud to meet its legend; into a
flock to battle one of it.

This is the HOENN_SOARING_IN_THE_SKY area's screen (dungeon.dungeon_for hands it out): a route underneath, so
battles are the route's own and come back here, the flight going on where it was. Places: src/world/soaring3d.py.
"""
import json
import math
import os
import random
import time

import pygame

from src.config import FPS
from src.states.overworld.route import PlayState
from src.ui import theme
from src.world import soaring3d as S3

FOV = 70.0                       # degrees across
SPEEDS = (90.0, 150.0, 260.0)    # world units a frame: slow, cruising, fast (25 frames a second)
TURN = 2.6                       # degrees a frame at full turn
CLIMB = 45.0                     # world units a frame at full climb
ALT_MIN, ALT_MAX = 700.0, 4200.0
CROP = 320                       # half-size of the turned square of ground, in that level's pixels
FAR_CROP = 320
REACH = 0.72                     # how much of the square a row may use (the rest: room to move before turning anew)
HAZE = (176, 206, 236)
SEA = (40, 108, 184)
HUD_H = 76
SPRITE_SCALE = 5                 # Jordan's 31 x 30 back sprites, five times (as in the 2D version)
SPRITE_ROLL = 22.0               # degrees the sprite leans at full turn
WILD_EVERY = (FPS * 5, FPS * 9)
_cache = {}


def _load(game, name, alpha=True):
    key = ("img", name)
    if key not in _cache:
        try:
            img = pygame.image.load(os.path.join(game.assets.assets_dir, "soaring3d", name))
            _cache[key] = img.convert_alpha() if alpha else img.convert()
        except (pygame.error, FileNotFoundError):
            _cache[key] = None
    return _cache[key]


def storm_picture(seed=7, w=320, h=180):
    """A black storm cloud of our own: dark round puffs, a lighter top edge, soft at the rim."""
    rng = random.Random(seed)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    puffs = [(rng.randint(w // 6, 5 * w // 6), rng.randint(h // 3, 2 * h // 3), rng.randint(h // 5, h // 3))
             for _ in range(11)]
    for col, dy, grow in (((30, 26, 44, 120), 6, 8), ((58, 52, 78, 235), 0, 0), ((92, 86, 116, 235), -5, -9)):
        for x, y, r in puffs:
            pygame.draw.circle(s, col, (x, y + dy), max(2, r + grow))
    return s


def rift_picture(size=256):
    """The Dimensional Rift, ours: a dark hole with violet arms curling into it."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2
    for i in range(36, 0, -1):            # a soft violet glow, darker inwards
        k = i / 36
        pygame.draw.circle(s, (int(40 + 120 * k), int(10 + 40 * k), int(70 + 150 * k), int(200 * (1 - k) + 30)),
                           (int(c), int(c)), int(c * k * 0.95))
    for arm in range(4):                  # spiral arms
        pts = []
        for j in range(40):
            t = j / 39
            a = arm * math.pi / 2 + t * 4.2
            r = c * 0.92 * (1 - t) + 6
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
        pygame.draw.lines(s, (210, 170, 255, 210), False, pts, 5)
        pygame.draw.lines(s, (90, 40, 150, 230), False, pts, 2)
    pygame.draw.circle(s, (6, 0, 14, 255), (int(c), int(c)), int(c * 0.2))
    return s


def mount(game):
    """(species id, name) of the Eon you ride: one in your party first, else your version's, else Latios."""
    story = game.story_manager
    for p in getattr(story, "player_team", []) or []:
        if getattr(p, "id", None) in (380, 381):
            return p.id, ("Latias" if p.id == 380 else "Latios")
    try:
        from src.world import hoenn
        v = hoenn.info(story)
        if v and v.get("eon_id") in (380, 381):
            return v["eon_id"], v["eon"]
    except Exception:
        pass
    return 381, "Latios"


def follower(game, pid, size, row=0, frame=0):
    """A flying Pokemon in the world: its following-Pokemon sheet (assets/dungeon/followers, 4 x 4: rows down, left,
    right, up), cropped to the box all its frames share, at this height; the party icon if it has no sheet."""
    key = ("follower", pid)
    if key not in _cache:
        data = None
        path = os.path.join(game.assets.assets_dir, "dungeon", "followers", f"{int(pid)}.png")
        if os.path.isfile(path):
            img = pygame.image.load(path).convert_alpha()
            cw, ch = img.get_width() // 4, img.get_height() // 4
            box = None
            for c in range(4):
                for r in range(4):
                    bb = img.subsurface((c * cw, r * ch, cw, ch)).get_bounding_rect()
                    if bb.w and bb.h:
                        box = bb if box is None else box.union(bb)
            data = (img, cw, ch, box)
        _cache[key] = data
    data = _cache[key]
    if not data:
        from src.minigames.base import icon
        return icon(game, pid, size)
    img, cw, ch, box = data
    cell = img.subsurface((frame % 4 * cw + box.x, row * ch + box.y, box.w, box.h))
    return pygame.transform.scale(cell, (max(2, int(size * box.w / box.h)), max(2, int(size))))


class Level:
    """One picture of the ground (world rect, units per pixel) and its turned square, kept while it still fits."""

    def __init__(self, img, rect, crop, sea=None):
        self.img = img
        self.sea = sea or SEA
        self.x0, self.z0, x1, z1 = rect
        self.s = (x1 - self.x0) / img.get_width()
        self.crop = crop
        self.surf = None      # the turned square
        self.at = None        # (world x, z, heading) it was turned at

    def turned(self, x, z, heading):
        if self.at is not None:
            ox, oz, oh = self.at
            if abs(oh - heading) < 0.01 and math.hypot(x - ox, z - oz) < self.crop * self.s * (0.95 - REACH):
                return self.surf      # (still turned the right way, and you haven't flown off it)
        c = self.crop
        sq = pygame.Surface((2 * c, 2 * c))
        sq.fill(self.sea)
        px, pz = (x - self.x0) / self.s, (z - self.z0) / self.s
        sq.blit(self.img, (c - int(px), c - int(pz)))
        self.surf = pygame.transform.rotate(sq, heading)
        self.at = (int(px) * self.s + self.x0, int(pz) * self.s + self.z0, heading)  # (the pixel it's centred on)
        return self.surf


class Soaring3DState(PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_soar_ready", False):   # back from a battle: the flight goes on where it was
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._soar_ready = True
        game.soaring3d_state = self
        story = game.story_manager
        self.area_key = story.current_area_key
        self.W, self.H = game.width, game.height
        self.RW, self.RH = self.W // 2, self.H // 2        # the view is drawn at half size, then doubled
        self.F = (self.RW / 2) / math.tan(math.radians(FOV / 2))
        self.rng = random.Random()
        self.t = 0
        self._setup_pictures()
        self.eon_id, self.eon_name = self._mount()
        self.eon_imgs = {}
        self.rider = self._rider()
        came = getattr(story, "last_area_key", None) or "MOSSDEEP_CITY"
        start = S3.TOWNS.get(came) or S3.LAND_SPOTS.get(came, (None, None))[1] or S3.TOWNS.get("MOSSDEEP_CITY", (0, 0))
        self.x, self.z = float(start[0]), float(start[1]) + 2500   # (a little south, looking north at it)
        self.heading = 0.0       # degrees, 0 = north, clockwise
        self.alt = 1800.0
        self.speed = SPEEDS[1]
        self.bank = 0.0          # -1 .. 1 (left .. right)
        self.pitch = 0.0         # -1 .. 1 (dive .. climb)
        self.mode = "FLY"        # FLY, ASK (land / fly in?), PAUSE
        self.ask = None
        self.skip = set()
        self.held = None
        self.fast_held = False
        self.wilds = []
        self.next_wild = FPS * 2
        self.flash_text, self.flash_t = f"You're soaring on {self.eon_name}!", FPS * 3
        self.pool = self._get_wild_pool(self.area_data) or {"278": 1}
        self._refresh_spots()

    # ---------------------------------------------------------------- set-up
    def _setup_pictures(self):
        meta = {}
        try:
            with open(os.path.join(self.game.assets.assets_dir, "soaring3d", "soaring3d.json"), encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            pass
        self.levels = []
        self.sea = SEA
        near = _load(self.game, "map_ground.png", alpha=False) if S3.GROUND == "map" else None
        self.on_map = near is not None
        if self.on_map:
            S3.use_ground("map", self._map_points())
        else:                     # Omega Ruby's sky map (chosen, or the map picture is missing)
            S3.use_ground("oras")
            near = _load(self.game, "ground.jpg", alpha=False)
        if self.on_map:
            # the 2D version's map: crisp pixels, so its halves are picked, not blended; its own sea all round
            rect = S3.map_ground_rect(*near.get_size())
            self.sea = tuple(near.get_at((4, 4)))[:3]
            key = ("mips", "map")
            if key not in _cache:
                l1 = pygame.transform.scale(near, (near.get_width() // 2, near.get_height() // 2))
                l2 = pygame.transform.scale(l1, (l1.get_width() // 2, l1.get_height() // 2))
                l3 = pygame.transform.smoothscale(l2, (l2.get_width() // 2, l2.get_height() // 2))
                _cache[key] = (near, l1, l2, l3)
            for img in _cache[key]:
                self.levels.append(Level(img, rect, CROP, self.sea))
            m = 30000                                   # (open sea round it, then the edge of the sky)
            self.bounds = (rect[0] - m, rect[1] - m, rect[2] + m, rect[3] + m)
            self.mm_src, self.mm_rect = _cache[key][2], rect
        elif near is not None:
            far = _load(self.game, "ground_far.jpg", alpha=False)
            rect = tuple(meta.get("near", (-16000, -19000, 32000, 17000)))
            key = ("mips",)
            if key not in _cache:         # the finer pictures, halved and halved again
                l1 = pygame.transform.smoothscale(near, (near.get_width() // 2, near.get_height() // 2))
                l2 = pygame.transform.smoothscale(l1, (l1.get_width() // 2, l1.get_height() // 2))
                _cache[key] = (near, l1, l2)
            for img in _cache[key]:
                self.levels.append(Level(img, rect, CROP, self.sea))
            if far is not None:
                self.levels.append(Level(far, tuple(meta.get("far", (-56000, -50000, 64000, 40000))), FAR_CROP, self.sea))
            self.bounds = tuple(meta.get("far", (-56000, -50000, 64000, 40000)))
            self.mm_src, self.mm_rect = _cache[key][2], rect
        else:
            self.bounds = (-56000, -50000, 64000, 40000)
            self.mm_src, self.mm_rect = None, self.bounds
        self.minimap = None
        if self.mm_src is not None:               # the mini-map: Hoenn itself, not the open sea round it
            src = self.mm_src
            self.minimap = pygame.transform.smoothscale(src, (240, int(240 * src.get_height() / src.get_width())))
        self.banks = tuple(meta.get("banks", (-50, -25, 0, 25, 50)))
        self.pitches = tuple(meta.get("pitches", (-25, 0, 25)))
        self.view = pygame.Surface((self.RW, self.RH))
        self.band = 2           # screen rows per strip of ground; 3 if frames come slow (a slower phone)
        self.frame_ms = 0.0
        # the sky: a gradient, the game's own horizon clouds going round as you turn, and haze over the far ground
        self.sky = pygame.Surface((self.RW, self.RH))
        for y in range(self.RH):
            k = min(1.0, y / (self.RH * 0.45))
            self.sky.fill((int(70 + (HAZE[0] - 70) * k), int(120 + (HAZE[1] - 120) * k), int(205 + (HAZE[2] - 205) * k)),
                          (0, y, self.RW, 1))
        pano_w = int(self.RW * 360 / FOV)
        self.pano = pygame.Surface((pano_w, 64), pygame.SRCALPHA)
        for name, y in (("cloud_b.png", 4), ("cloud_a.png", 18)):
            img = _load(self.game, name)
            if img is None:
                continue
            img = pygame.transform.smoothscale(img, (pano_w // 6, 44))
            for i in range(6):
                self.pano.blit(img, (i * pano_w // 6 + (40 if y == 18 else 0), y))
        self.haze = pygame.Surface((self.RW, 90), pygame.SRCALPHA)
        for y in range(90):
            self.haze.fill(HAZE + (int(235 * (1 - y / 90) ** 1.6),), (0, y, self.RW, 1))
        self.rift_img = rift_picture()
        self.storm_img = storm_picture()

    def _map_points(self):
        try:
            with open(os.path.join(self.game.assets.assets_dir, "map_points.json"), encoding="utf-8") as f:
                return (json.load(f).get("region_maps", {}).get("HOENN") or {}).get("points") or {}
        except (OSError, ValueError):
            return {}

    def _mount(self):
        return mount(self.game)

    def _eon_sprite(self):
        """Jordan's Mega Latias / Latios from behind, five times (the 2D version's), or None."""
        key = ("sprite",)
        if key not in self.eon_imgs:
            img = _load(self.game, "mega_latias_back.png" if self.eon_id == 380 else "mega_latios_back.png")
            if img is not None:
                img = pygame.transform.scale(img, (img.get_width() * SPRITE_SCALE, img.get_height() * SPRITE_SCALE))
            self.eon_imgs[key] = img
        return self.eon_imgs[key]

    def _eon_img(self, bank_i, pitch_i):
        key = (bank_i, pitch_i)
        if key not in self.eon_imgs:
            img = _load(self.game, "eon_%d_%d_%d.png" % (self.eon_id, self.banks[bank_i], self.pitches[pitch_i]))
            if img is not None:
                w = int(self.W * 0.34)
                img = pygame.transform.smoothscale(img, (w, int(w * img.get_height() / img.get_width())))
            self.eon_imgs[key] = img
        return self.eon_imgs[key]

    def _rider(self):
        """You, from behind (your trainer's facing-up frame), cut off at the waist: sat on its back."""
        try:
            from src.coop import world
            char = str(getattr(self.game, "player_character", "") or "red")
            img = world.person_img(self.game, char, (0, -1), height=70 if S3.EON_LOOK == "sprite" else 60)
        except Exception:
            return None
        if img is None:
            return None
        return img.subsurface((0, 0, img.get_width(), int(img.get_height() * 0.72))).copy()

    def _refresh_spots(self):
        story = self.game.story_manager
        flags = story.story_flags
        progression = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        names = {k: (progression.get(k) or {}).get("route_name") for k in S3.LAND_SPOTS}
        self.land = S3.mark_beacons(S3.land_spots(self.area_data, flags, names), progression, flags)
        self.skyspots = S3.sky_spots(self.area_data, flags)
        self.visited = {k for k in S3.TOWNS if flags.get(f"visited_{k}")}

    # ---------------------------------------------------------------- the route underneath
    def _back_from_battle(self):
        self.mode = "FLY"
        self.dialogue_box.visible = False   # (the legend's line from before the battle)
        self.ask = None
        self.held = None
        self.fast_held = False
        self.wilds = []
        self.next_wild = self.rng.randint(*WILD_EVERY)
        self._refresh_spots()          # (a legend caught: the next one comes out, or the rift closes)

    def _play_data(self):
        return {"balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False, "soaring": True}

    def start(self):
        self.game.ui_manager.elements.clear()
        pygame.event.clear()
        self.game.story_manager.story_flags[f"visited_{self.area_key}"] = True

    def show_progression_menu(self):
        """A battle or its catch is over: fly on."""
        self.is_progression_paused = True
        self.p_data = [None] * 3
        self.catch_selection_active = False
        self.dialogue_box.visible = False
        self.mode = "FLY"
        self.ask = None

    # ---------------------------------------------------------------- input
    def handle_events(self, events):
        for e in events:
            if self.dialogue_box.visible:
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (
                        e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogue_box.advance()
                continue
            if self.mode == "ASK":
                self._ask_event(e)
                continue
            if self.mode != "FLY":
                continue
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_l, pygame.K_AC_BACK):
                self._ask_land()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._land_rect().collidepoint(e.pos):
                    self._ask_land()
                elif self._fast_rect().collidepoint(e.pos):
                    self.fast_held = True
                else:
                    self.held = e.pos
            elif e.type == pygame.MOUSEMOTION and self.held is not None:
                self.held = e.pos
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.held = None
                self.fast_held = False

    def _ask_event(self, e):
        _spot, buttons = self.ask
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, _label, _c, fn in buttons:
                if rect.collidepoint(e.pos):
                    return fn()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_y):
                return buttons[0][3]()
            if e.key in (pygame.K_ESCAPE, pygame.K_n, pygame.K_AC_BACK):
                return buttons[-1][3]()

    def _land_rect(self):
        return pygame.Rect(self.W - 190, 12, 172, HUD_H - 24)

    def _fast_rect(self):
        return pygame.Rect(self.W - 190, self.H - 120, 172, 96)

    # ---------------------------------------------------------------- choices
    def _ask_box(self, spot, line, yes, yes_fn, no="FLY ON"):
        cx, y = self.W // 2, HUD_H + 30
        buttons = [(pygame.Rect(cx - 330, y + 70, 300, 76), yes, theme.POKEMON, yes_fn),
                   (pygame.Rect(cx + 30, y + 70, 300, 76), no, theme.BACK, self._fly_on)]
        self.ask = (spot, buttons)
        self.ask_line = line
        self.mode = "ASK"

    def _fly_on(self):
        spot = self.ask[0] if self.ask else None
        if spot is not None:
            self.skip.add(spot["key"])
        self.ask = None
        self.mode = "FLY"

    def _ask_land(self):
        key, _d = S3.nearest_town(self.x, self.z, self.visited)
        name = S3.town_name(key)
        self._ask_box(None, f"Land at {name}?", "LAND",
                      lambda: self._land(key, f"{self.eon_name} set you down at {name}."), no="KEEP FLYING")

    def _land(self, key, line=None):
        self.game.soaring3d_state = None
        self.mode = "GONE"
        from src.states.overworld.area_transition import AreaTransitionState
        self.game.change_state(AreaTransitionState(self.game, key, initial_message=line))

    def _reach(self, spot):
        if spot["look"] in ("rift", "storm"):
            what = "A huge gap has opened in the sky!" if spot["look"] == "rift" else "A black cloud is crackling with power!"
            self._ask_box(spot, what, "FLY IN", lambda: self._legend(spot))
        else:
            self._ask_box(spot, f"{spot['name']} is below you!", "LAND", lambda: self._land_on(spot))

    def _land_on(self, spot):
        """Down onto a Mirage place: which legend is out, which place of its kind, today's hidden item (src/world/soaring.py)."""
        from src.world import soaring as landing
        place = (S3.SPOT_PLACES.get(spot["area"]) or (None, None, None))[2]   # (its point on the map picture)
        extra = landing.on_landing(self.game.story_manager, spot["area"], place, self.rng)
        self._land(spot["area"], f"{self.eon_name} landed on {spot['name']}.{extra}")

    def _legend(self, spot):
        self.ask = None
        self.mode = "PAUSE"
        self.wilds = []
        self.action_challenge_boss(dict(spot["next"]))

    def _wild(self, pid):
        """Into a flock: a battle with one of it (the route's own, back here after)."""
        from src.pokemon.data import Pokemon
        from src.states.battle import WildBattleState
        from src.world import levels
        self.mode = "PAUSE"
        self.rounds_completed += 1
        pokemon = Pokemon(self.game.loader.fetch_specific(int(pid)), self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.area_key)
        self.game.data.mark_seen(pokemon.id)
        battle = WildBattleState(self.game, pokemon, self.area_key, background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        pygame.event.clear()
        self.game.change_state(battle)

    # ---------------------------------------------------------------- the flight
    def _vectors(self):
        h = math.radians(self.heading)
        return (math.sin(h), -math.cos(h)), (math.cos(h), math.sin(h))   # forward, right (x, z)

    def update(self):
        self.t += 1
        if self.dialogue_box.visible:
            self.dialogue_box.update()
            return
        if self.flash_t > 0:
            self.flash_t -= 1
        if self.mode != "FLY":
            return
        keys = pygame.key.get_pressed()
        steer = climb = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            steer -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            climb += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            climb -= 1
        if self.held is not None:
            if not steer:
                steer = max(-1.0, min(1.0, (self.held[0] - self.W / 2) / (self.W * 0.25)))
            if not climb:
                climb = max(-1.0, min(1.0, (self.H * 0.6 - self.held[1]) / (self.H * 0.25)))
        fast = self.fast_held or keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]
        want = SPEEDS[2] if fast else SPEEDS[1]
        self.speed += (want - self.speed) * 0.08
        self.bank += (steer - self.bank) * 0.15
        self.pitch += (climb - self.pitch) * 0.15
        self.heading = (self.heading + self.bank * TURN) % 360
        self.alt = max(ALT_MIN, min(ALT_MAX, self.alt + self.pitch * CLIMB))
        f, _r = self._vectors()
        self.x += f[0] * self.speed
        self.z += f[1] * self.speed
        self._edge()
        self._spawn()
        self._move_wilds()
        self._check_spots()

    def _edge(self):
        """The edge of the sky (ORAS turns you back): a U-turn."""
        x0, z0, x1, z1 = self.bounds
        m = 9000
        if self.x < x0 + m or self.x > x1 - m or self.z < z0 + m or self.z > z1 - m:
            self.x = max(x0 + m, min(x1 - m, self.x))
            self.z = max(z0 + m, min(z1 - m, self.z))
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            self.heading = math.degrees(math.atan2(cx - self.x, -(cz - self.z))) % 360
            self.flash_text, self.flash_t = "You can't fly any farther! Turning back...", FPS * 2

    def _spawn(self):
        self.next_wild -= 1
        if self.next_wild > 0 or len(self.wilds) >= 3:
            return
        self.next_wild = self.rng.randint(*WILD_EVERY)
        from src.utils import Utils
        pid = int(Utils.weighted_random_choice(self.pool))
        f, r = self._vectors()
        ahead, side = self.rng.uniform(6000, 9000), self.rng.uniform(-2500, 2500)
        self.wilds.append({"pid": pid, "x": self.x + f[0] * ahead + r[0] * side, "z": self.z + f[1] * ahead + r[1] * side,
                           "alt": max(ALT_MIN, min(ALT_MAX, self.alt + self.rng.uniform(-500, 500))),
                           "dx": self.rng.uniform(-30, 30), "dz": self.rng.uniform(-30, 30), "ph": self.rng.random() * 6,
                           "n": self.rng.choice((1, 2, 3))})

    def _move_wilds(self):
        keep = []
        for w in self.wilds:
            w["x"] += w["dx"]
            w["z"] += w["dz"]
            dx, dz = w["x"] - self.x, w["z"] - self.z
            f, r = self._vectors()
            ahead = dx * f[0] + dz * f[1]
            if math.hypot(dx, dz) < 420 and abs(w["alt"] - self.alt) < 600:
                return self._wild(w["pid"])
            if -2000 < ahead < 14000:
                keep.append(w)
        self.wilds = keep

    def _check_spots(self):
        for spot in self.land + self.skyspots:
            d = math.hypot(spot["at"][0] - self.x, spot["at"][1] - self.z)
            near = d < (900 if spot["look"] in ("rift", "storm") else 1100)
            if spot["look"] in ("rift", "storm"):
                near = near and abs(self.alt - spot["alt"]) < 1200
            if not near:
                self.skip.discard(spot["key"])
            elif spot["key"] not in self.skip:
                return self._reach(spot)

    # ---------------------------------------------------------------- drawing
    def _horizon(self):
        return int(self.RH * 0.30 + self.pitch * self.RH * 0.06)

    def draw(self):
        screen = self.game.screen
        view = self.view
        hy = self._horizon()
        view.blit(self.sky, (0, 0), (0, self.RH * 0.45 - hy if hy < self.RH * 0.45 else 0, self.RW, self.RH))
        # the horizon clouds go round as you turn
        pw = self.pano.get_width()
        off = -int(self.heading / 360 * pw) % pw
        for k in (-1, 0, 1):
            view.blit(self.pano, (off + k * pw, hy - 52))
        t0 = time.perf_counter()
        self._draw_ground(view, hy)
        self.frame_ms += ((time.perf_counter() - t0) * 1000 - self.frame_ms) * 0.05
        self.band = 3 if self.frame_ms > 22 else 2 if self.frame_ms < 12 else self.band
        view.blit(self.haze, (0, hy - 6))
        self._draw_things(view, hy)
        pygame.transform.scale(view, (self.W, self.H), screen)
        self._draw_me(screen)
        self._draw_hud(screen)
        if self.mode == "ASK" and self.ask:
            self._draw_ask(screen)
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)

    def _draw_ground(self, view, hy):
        """Mode 7: every row below the horizon is a strip of ground, from the finest picture that reaches."""
        if not self.levels:
            view.fill(self.sea, (0, hy, self.RW, self.RH - hy))
            return
        turned = [None] * len(self.levels)
        half_w = self.RW / 2
        y = hy + 1
        band = self.band
        while y < self.RH:
            d = self.alt * self.F / (y + band / 2 - hy)            # how far ahead this row is
            lvl = None
            for i, L in enumerate(self.levels):
                # the finest picture whose turned square reaches this row, and not so fine that it shimmers
                if d * 1.25 < L.crop * L.s * REACH and (2 * half_w * d / self.F) / L.s <= self.RW * 2:
                    lvl = i
                    break
            if lvl is None:
                lvl = len(self.levels) - 1
            L = self.levels[lvl]
            if d * 1.25 > L.crop * L.s * REACH:                    # past the farthest picture: open sea
                view.fill(self.sea, (0, y, self.RW, band))
                y += band
                continue
            if turned[lvl] is None:
                turned[lvl] = L.turned(self.x, self.z, self.heading)
            surf = turned[lvl]
            cxs, czs = surf.get_width() / 2, surf.get_height() / 2
            # where you are in the turned square (it was turned a little way back, maybe)
            ox, oz, _h = L.at
            f, r = self._vectors()
            dx, dz = self.x - ox, self.z - oz
            mx = cxs + (dx * r[0] + dz * r[1]) / L.s
            my = czs - (dx * f[0] + dz * f[1]) / L.s
            sw = 2 * half_w * d / self.F / L.s
            sy = my - d / L.s
            src = pygame.Rect(int(mx - sw / 2), int(sy), max(1, int(sw)), 1)
            clip = src.clip(surf.get_rect())
            if clip.w > 0 and clip.h > 0:
                strip = surf.subsurface(clip)
                k = self.RW / src.w
                dx0 = int((clip.x - src.x) * k)
                dw = max(1, int(clip.w * k + 1))
                if clip.w < src.w:
                    view.fill(self.sea, (0, y, self.RW, band))
                view.blit(pygame.transform.scale(strip, (dw, band)), (dx0, y))
            else:
                view.fill(self.sea, (0, y, self.RW, band))
            y += band

    def _project(self, wx, wz, walt):
        """(screen x, y, scale, distance ahead) in the half-size view, or None if behind."""
        f, r = self._vectors()
        dx, dz = wx - self.x, wz - self.z
        ahead = dx * f[0] + dz * f[1]
        if ahead < 150:
            return None
        side = dx * r[0] + dz * r[1]
        k = self.F / ahead
        return self.RW / 2 + side * k, self._horizon() + (self.alt - walt) * k, k, ahead

    def _draw_things(self, view, hy):
        things = []
        for s in self.land:
            p = self._project(s["at"][0], s["at"][1], 0)
            if p:
                things.append((p[3], "land", s, p))
        for s in self.skyspots:
            p = self._project(s["at"][0], s["at"][1], s["alt"])
            if p:
                things.append((p[3], s["look"], s, p))
        for w in self.wilds:
            p = self._project(w["x"], w["z"], w["alt"])
            if p:
                things.append((p[3], "wild", w, p))
        for _d, kind, s, (sx, sy, k, ahead) in sorted(things, key=lambda t: -t[0]):
            if ahead > 40000 or not (-400 < sx < self.RW + 400):
                continue
            fade = max(0, min(255, int(255 * (1 - (ahead - 22000) / 18000)))) if ahead > 22000 else 255
            if kind == "land":
                self._draw_land_spot(view, s, sx, sy, k, fade)
            elif kind in ("rift", "storm"):
                img = self.rift_img if kind == "rift" else self.storm_img
                size = max(8, int((2600 if kind == "rift" else 4800) * k))
                if size < 900:
                    pic = pygame.transform.smoothscale(img, (size, int(size * img.get_height() / img.get_width())))
                    if kind == "rift":
                        pic = pygame.transform.rotate(pic, (self.t * 4) % 360)
                    pic.set_alpha(fade)
                    view.blit(pic, pic.get_rect(center=(int(sx), int(sy))))
                if kind == "storm" and (self.t // 3) % 7 == 0 and size > 20:
                    pts = [(sx - size * 0.05, sy + size * 0.1), (sx + size * 0.04, sy + size * 0.25),
                           (sx - size * 0.03, sy + size * 0.27), (sx + size * 0.06, sy + size * 0.45)]
                    pygame.draw.lines(view, (255, 240, 120), False, pts, max(1, size // 60))
            else:
                size = max(6, min(200, int(380 * k)))
                img = follower(self.game, s["pid"], size, row=0, frame=self.t // 4)   # (flying at you)
                bob = math.sin(self.t / 5 + s["ph"]) * size * 0.08
                for i in range(s["n"]):
                    ox = (i - (s["n"] - 1) / 2) * size * 0.7
                    oy = (abs(i - (s["n"] - 1) / 2)) * size * 0.25
                    view.blit(img, img.get_rect(center=(int(sx + ox), int(sy + oy + bob))))

    def _draw_land_spot(self, view, s, sx, sy, k, fade):
        """A Mirage place: a glowing ring on the ground, a shaft of light, and the red beacon while a legend's there."""
        rw = max(6, int(1500 * k))
        rh = max(3, int(rw * 0.3))
        pulse = 0.5 + 0.5 * math.sin(self.t / 6)
        ring = pygame.Surface((rw + 8, rh + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (255, 236, 150, int((110 + 120 * pulse) * fade / 255)), ring.get_rect(), max(2, rw // 25))
        view.blit(ring, ring.get_rect(center=(int(sx), int(sy))))
        bh = max(10, min(int(sy) + 10, int(2200 * k)))
        bw = max(2, min(26, int(110 * k)))
        beam = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for yy in range(bh):
            beam.fill((255, 244, 200, int(150 * (yy / bh) * fade / 255)), (0, yy, bw, 1))
        view.blit(beam, (int(sx - bw / 2), int(sy - bh)))
        if s.get("beacon"):
            by = sy - bh - max(6, int(300 * k)) - math.sin(self.t / 5) * 4
            r = max(4, int(170 * k))
            pts = [(sx, by - r), (sx + r * 0.66, by), (sx, by + r), (sx - r * 0.66, by)]
            pygame.draw.polygon(view, (230, 40, 50), pts)
            pygame.draw.polygon(view, (90, 10, 20), pts, 1)

    def _draw_me(self, screen):
        cx, cy = self.W // 2, int(self.H * 0.66 + 6 * math.sin(self.t / 6))
        sprite = self._eon_sprite() if S3.EON_LOOK == "sprite" else None
        if sprite is not None:
            # Jordan's back view, as the 2D version draws it: rolled into the turn, nudged up as you climb
            roll = -self.bank * SPRITE_ROLL
            img = pygame.transform.rotate(sprite, roll) if abs(roll) > 0.5 else sprite
            cy -= int(self.pitch * 10)
            screen.blit(img, img.get_rect(center=(cx, cy)))
            if self.rider is not None:
                r = pygame.transform.rotate(self.rider, roll * 0.8) if abs(roll) > 0.5 else self.rider
                a = math.radians(roll)
                up = 4 + r.get_height() / 2                        # (the rider's middle, above the sprite's middle)
                screen.blit(r, r.get_rect(center=(int(cx - math.sin(a) * up), int(cy - math.cos(a) * up))))
            return
        # (the baked models' bank: + is the left wing down, so turning left picks the + end)
        bi = min(len(self.banks) - 1, max(0, int(round((1 - self.bank) / 2 * (len(self.banks) - 1)))))
        pi = min(len(self.pitches) - 1, max(0, int(round((self.pitch + 1) / 2 * (len(self.pitches) - 1)))))
        img = self._eon_img(bi, pi)
        if img is not None:
            screen.blit(img, img.get_rect(center=(cx, cy)))
        else:
            pygame.draw.circle(screen, (150, 110, 210), (cx, cy), 50)
        if self.rider is not None:
            roll = self.banks[bi] * 0.8                      # sat on its back, leaning with it
            r = pygame.transform.rotate(self.rider, roll) if roll else self.rider
            up = self.H * 0.035 + self.pitch * 8 + self.rider.get_height() / 2
            a = math.radians(roll)
            at = (cx - math.sin(a) * up, cy - math.cos(a) * up)
            screen.blit(r, r.get_rect(center=(int(at[0]), int(at[1]))))

    def _draw_hud(self, screen):
        fonts = self.game.assets.fonts
        bar = pygame.Rect(12, 8, self.W - 214, HUD_H - 16)
        theme.draw_textbox(screen, bar)
        theme.shadow_text(screen, "Soaring in the Sky", fonts["button"], bar.x + 20,
                          bar.centery - fonts["button"].get_height() // 2)
        key, _d = S3.nearest_town(self.x, self.z)
        theme.shadow_text(screen, f"Near {S3.town_name(key)}   Height {int(self.alt / 10) * 10}", fonts["label"],
                          bar.right - 20, bar.centery - 12, align="right")
        mouse = pygame.mouse.get_pos()
        r = self._land_rect()
        theme.command_button(screen, r, "LAND", fonts["button"], theme.BACK, hover=r.collidepoint(mouse))
        r = self._fast_rect()
        theme.command_button(screen, r, "FAST", fonts["button"], theme.POKEMON, hover=self.fast_held)
        mm = self.minimap
        if mm is not None:
            at = pygame.Rect(16, self.H - mm.get_height() - 16, mm.get_width(), mm.get_height())
            screen.blit(mm, at)
            pygame.draw.rect(screen, theme.TEXTBOX_FRAME, at.inflate(4, 4), 3)
            x0, z0, x1, z1 = self.mm_rect
            kx, kz = mm.get_width() / (x1 - x0), mm.get_height() / (z1 - z0)
            for s in self.land:
                pygame.draw.circle(screen, (230, 40, 50) if s.get("beacon") else (255, 230, 120),
                                   (at.x + int((s["at"][0] - x0) * kx), at.y + int((s["at"][1] - z0) * kz)), 3)
            for s in self.skyspots:
                pygame.draw.circle(screen, (150, 80, 220), (at.x + int((s["at"][0] - x0) * kx), at.y + int((s["at"][1] - z0) * kz)), 4)
            me = (at.x + max(0, min(mm.get_width(), int((self.x - x0) * kx))),
                  at.y + max(0, min(mm.get_height(), int((self.z - z0) * kz))))
            f, _r = self._vectors()
            pygame.draw.line(screen, (20, 20, 30), me, (me[0] + int(f[0] * 10), me[1] + int(f[1] * 10)), 2)
            pygame.draw.circle(screen, (255, 255, 255) if (self.t // 6) % 2 else (20, 20, 30), me, 4)
        if self.flash_t > 0 and self.mode == "FLY":
            t = fonts["button"].render(self.flash_text, True, (255, 255, 255))
            pill = t.get_rect(center=(self.W // 2, HUD_H + 40)).inflate(30, 14)
            pygame.draw.rect(screen, (40, 30, 80), pill, border_radius=12)
            pygame.draw.rect(screen, (190, 150, 255), pill, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=pill.center))

    def _draw_ask(self, screen):
        fonts = self.game.assets.fonts
        _spot, buttons = self.ask
        card = pygame.Rect(0, 0, 760, 200)
        card.center = (self.W // 2, HUD_H + 90)
        theme.draw_textbox(screen, card)
        theme.shadow_text(screen, self.ask_line, fonts["button"], card.centerx, card.y + 26, align="center")
        mouse = pygame.mouse.get_pos()
        for rect, label, colour, _fn in buttons:
            theme.command_button(screen, rect, label, fonts["button"], colour, hover=rect.collidepoint(mouse))
