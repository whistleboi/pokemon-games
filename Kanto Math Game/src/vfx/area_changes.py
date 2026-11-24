"""Doors, area changes and the area name sign as each walked region's own game does them (Jordan 11-24, region/systems).

The region picks the game as for the battle intros (canon_intros.REGION_GAME): Kanto, Sevii and Orange FireRed/LeafGreen,
Hoenn Emerald, Johto HeartGold/SoulSilver, Sinnoh Platinum, Orre Pokemon Orre 2.1.1 (Essentials v21.1), and Unova
Platinum's (Jordan 11-24: Black 2 would need an emulator to measure). The menu regions keep the old screens.

Numbers from kanto_handoff/transitions_research (GEN3_FRLG_EMERALD.md 3.1-3.8, GEN4_HGSS_PLATINUM.md 3a-3d,
GEN5_B2W2_AND_ORRE.md B3 and orre_essentials_v21_scripts). They are the games' 60 fps frames, played at the same real
speed here (src.config.FPS).

Two parts:
- a screen wipe (Wipe): the old screen is caught (the frame on screen when the change starts), the change itself happens
  at once (so nothing that sets story state waits on a picture), and the wipe plays over the screen: the old picture
  fading out ("out" segments: the map waits, nothing moves), then the new place showing through ("in" segments). Started
  by change(state, kind, then) on the maps, and by the area change (AreaTransitionState, which no longer shows its
  in-between screen for these regions: quick()). Drawn by Game._frame (draw(game)).
- the name sign (Sign): each game's look and timing, made by arrival()/floor_sign() and drawn by the map.

Not drawn: door opening sprites (no door art in our tiles), FireRed's and HGSS's dungeon preview pictures (no pictures),
the player's own spins and drops (Escape Rope, warp panels, holes), the side stairs' slide, the DS camera push. The sign
plates are drawn in code in each game's colours (the games' plate art is ROM graphics)."""
import math

import pygame

from src.config import FPS
from src.vfx.canon_intros import REGION_GAME

BLACK, WHITE = (0, 0, 0), (255, 255, 255)
ACTIVE = None   # the wipe playing (held keys walk no one while it plays: dungeon.held_way)


def game_key(region):
    return REGION_GAME.get(str(region or "").upper())


def here_key(game):
    try:
        return game_key(game.story_manager.get_current_region())
    except Exception:
        return None


def frames(n60):
    """60 fps frames -> this game's frames (the same real time)."""
    return max(1, int(round(n60 * FPS / 60.0)))


# ---------------------------------------------------------------------------------------------- what kind of place
def place_class(game, key):
    """"cave", "inside" or "outside" for an area (its battle type: a mountain that isn't a route is a cave, as for the intros)."""
    data = (game.loader.area_data.get("STORY_PROGRESSION", {}) or {}).get(key) or {}
    bt = str(data.get("battle_type") or "").lower()
    name = str(data.get("route_name") or key or "").lower()
    if bt == "cave" or (bt == "mountain" and "route" not in name) or bt == "distortion":
        return "cave"
    if bt == "indoor":
        return "inside"
    return "outside"


# ---------------------------------------------------------------------------------------------- each game's wipes
# A plan: (out segments, in segments). A segment: (style, 60 fps frames, params).
def _fade(n, c):
    return ("fade", n, {"to": c})


def _fade_in(n, c):
    return ("fade_in", n, {"from": c})


def plan(key, kind, cave_from=False):
    """The wipe for one change. kind: door_in (into a building), door_out (out of one, outdoors), stairs (floor to floor,
    room to room, lifts), warp (a warp panel), fall (a hole), cave_in, cave_out, escape (Escape Rope), fly, walk (over an
    edge into the next outdoor area). None: no wipe (the game's own quick crossfade between screens plays)."""
    if key in ("frlg", "emerald"):   # 3.1: black both ways; caves to and from white; ~17 frames each way (delay 0)
        F = 17
        if kind == "walk":
            return None   # (3.6: the next map streams in, no fade at all)
        if kind == "cave_in":    # (to WHITE, then the cave "enter" ramp white -> black, its layer blending away, fade in from black)
            return [_fade(F, WHITE)], [("ramp", 8, {"from": WHITE, "to": BLACK}), ("hold", 16, {"c": BLACK}), _fade_in(F, BLACK)]
        if kind == "cave_out" or (kind == "escape" and cave_from):   # (to black, the exit ramp to white, fade in from WHITE)
            return [_fade(F, BLACK)], [("hold", 17, {"c": BLACK}), ("ramp", 8, {"from": BLACK, "to": WHITE}),
                                       ("hold", 8, {"c": WHITE}), _fade_in(F, WHITE)]
        if kind == "door_out" and key == "frlg":   # (3.4: FireRed's barn door: open from a centre slit, a slow fade in, delay 3)
            return [_fade(F, BLACK)], [("barn", 41, {"from": BLACK})]
        return [_fade(F, BLACK)], [_fade_in(F, BLACK)]
    if key in ("hgss", "platinum"):   # 3a-3c: 6-frame brightness fades
        F = 6
        if kind == "walk":
            return None
        if kind == "cave_in":    # (type 4: an iris closing on the middle)
            return [("iris", F, {"to": BLACK})], [_fade_in(F, BLACK)]
        if kind in ("cave_out", "escape", "fly"):   # (type 5, Escape Rope/Dig, Fly: WHITE)
            return [_fade(F, WHITE)], [_fade_in(F, WHITE)]
        if kind == "door_out":   # (out of a door: the picture opens from the centre line, "camera shutter open")
            return [_fade(F, BLACK)], [("shutter", F, {"from": BLACK})]
        return [_fade(F, BLACK)], [_fade_in(F, BLACK)]
    if key == "orre":   # B3: Transfer Player's 0.4 s crossfade; pbCaveEntrance/Exit's 15 bands first
        if kind == "cave_in":
            return [("bands", 24, {"from": 255, "to": 0}), _fade(24, BLACK), ("hold", 6, {"c": BLACK})], [("cross", 24, {})]
        if kind == "cave_out":
            return [("bands", 24, {"from": 0, "to": 255}), _fade(24, WHITE), ("hold", 6, {"c": WHITE})], [("cross", 24, {})]
        return [], [("cross", 24, {})]
    return None


def length60(p):
    return sum(s[1] for s in p[0] + p[1]) if p else 0


class Wipe:
    """One screen wipe, playing over whatever the game draws. t counts this game's frames."""
    def __init__(self, game, snap, out, into, kind="", key=""):
        self.game, self.kind, self.key = game, kind, key
        self.snap = snap
        self.base = snap.copy()        # (what the out part last showed: the crossfade comes in from it)
        self.out, self.into = list(out), list(into)
        self.out_len = sum(s[1] for s in self.out)
        self.total = self.out_len + sum(s[1] for s in self.into)
        self.length = int(math.ceil(self.total * FPS / 60.0)) + (1 if self.into else 0)
        self.t = 0
        self.log = []   # (what each frame drew: style, how far, colour; the checks read it)

    def f60(self):
        return self.t * 60.0 / FPS

    def holding(self):
        """True while the old picture fades out: the game waits (no update)."""
        return self.f60() < self.out_len

    def done(self):
        return self.t >= self.length

    def _seg(self, f):
        segs = self.out + self.into
        at = 0
        for i, s in enumerate(segs):
            if f < at + s[1]:
                return i, s, (f - at) / float(s[1])
            at += s[1]
        return len(segs) - 1, segs[-1], 1.0

    def draw(self, screen):
        if not (self.out or self.into):
            return
        f = self.f60()
        if f < self.out_len:   # (the old picture's part reaches its full colour on its last frame, however few frames it has)
            f = min(self.out_len - 1e-6, f + 60.0 / FPS)
        i, (style, n, p), k = self._seg(f)
        k = max(0.0, min(1.0, k))
        view = _view(self.game)
        if i < len(self.out):   # the old picture going: drawn from the caught frame (or what the segment before left)
            if getattr(self, "_seg_i", None) != i:
                self._seg_i = i
                self._seg_base = getattr(self, "_prev_out", None) or self.snap
            base = self._seg_base
            if style == "fade":
                screen.blit(base, (0, 0))
                _veil(screen, p["to"], 255 * k)
            elif style == "iris":
                screen.blit(base, (0, 0))
                _outside_circle(screen, p["to"], view.center, (1 - k) * 256 * view.h / 192.0 * 1.25)
            elif style == "bands":
                screen.blit(base, (0, 0))
                _bands(screen, p["from"], p["to"], k, n)
            elif style == "hold":
                screen.fill(p["c"])
            elif style == "ramp":
                screen.fill(_mix(p["from"], p["to"], k))
            self._prev_out = screen.copy()
        else:   # the new place showing through
            if style == "fade_in":
                _veil(screen, p["from"], 255 * (1 - k))
            elif style == "hold":
                screen.fill(p["c"])
            elif style == "ramp":
                screen.fill(_mix(p["from"], p["to"], k))
            elif style == "barn":   # FireRed 3.4: edges 2 px/frame for 15 frames, then 4 px/frame; a delay-3 fade in under it
                fr = k * n
                half = (2 * fr if fr <= 15 else 30 + 4 * (fr - 15)) * view.w / 240.0
                _veil(screen, p["from"], 255 * max(0.0, 1 - fr / 41.0))
                left = pygame.Rect(0, 0, max(0, int(view.centerx - half)), screen.get_height())
                right = pygame.Rect(int(view.centerx + half), 0, screen.get_width(), screen.get_height())
                screen.fill(p["from"], left)
                if right.x < screen.get_width():
                    screen.fill(p["from"], right)
            elif style == "shutter":   # Gen 4 type 9: from the centre line out to the top and bottom
                half = k * view.h / 2.0
                top = int(view.centery - half)
                screen.fill(p["from"], (0, 0, screen.get_width(), max(0, top)))
                bot = int(view.centery + half)
                if bot < screen.get_height():
                    screen.fill(p["from"], (0, bot, screen.get_width(), screen.get_height() - bot))
            elif style == "cross":   # Essentials' Graphics.transition: the frozen old frame crossfades into the new
                old = getattr(self, "_prev_out", None) or self.snap
                old.set_alpha(int(255 * (1 - k)))
                screen.blit(old, (0, 0))
                old.set_alpha(None)
        self.log.append((style, round(k, 3), i < len(self.out)))


def _view(game):
    try:
        from src.states.overworld.dungeon import map_view
        return map_view(game)
    except Exception:
        return game.screen.get_rect()


def _mix(a, b, k):
    return tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))


def _veil(screen, colour, alpha):
    alpha = int(max(0, min(255, alpha)))
    if alpha <= 0:
        return
    if alpha >= 255:
        screen.fill(colour)
        return
    s = pygame.Surface(screen.get_size())
    s.fill(colour)
    s.set_alpha(alpha)
    screen.blit(s, (0, 0))


def _outside_circle(screen, colour, centre, r):
    W, H = screen.get_size()
    if r <= 0:
        screen.fill(colour)
        return
    m = pygame.Surface((W, H))
    m.fill(colour)
    m.set_colorkey((255, 0, 255))
    pygame.draw.circle(m, (255, 0, 255), (int(centre[0]), int(centre[1])), int(r))
    screen.blit(m, (0, 0))


def _bands(screen, g0, g1, k, n):
    """Essentials' pbCaveEntranceEx: 15 nested rectangles over the whole screen, each going from g0 to g1 over 0.4 s,
    the outer ones first (k*0.4/15 s apart): the screen goes dark (or light) from the edges in."""
    W, H = screen.get_size()
    total = 15
    bh, bw = ((H / 2.0) - 10) / total, ((W / 2.0) - 12) / total
    x = y = 0.0
    w, h = float(W), float(H)
    for b in range(total):
        kk = max(0.0, min(1.0, k - b / float(total)))   # (each band starts b/15 of the time later; the time is 0.4 s)
        v = int(g0 + (g1 - g0) * kk)
        screen.fill((v, v, v), (int(x), int(y), int(math.ceil(w)), int(math.ceil(h))))
        x += bw
        y += bh
        w -= bw * 2
        h -= bh * 2


def start(game, kind, key=None, snap=None, cave_from=False):
    """Start a wipe of this kind in this game (key: the region's game). Returns the Wipe, or None (no wipe here)."""
    global ACTIVE
    key = key or here_key(game)
    if not key or getattr(game, "FADE_FRAMES", 6) == 0 or getattr(game, "screen", None) is None:
        return None   # (Options > Screen fade off: changes are instant)
    p = plan(key, kind, cave_from=cave_from)
    if not p or not (p[0] or p[1]):
        return None
    w = Wipe(game, snap if snap is not None else game.screen.copy(), p[0], p[1], kind, key)
    game.area_wipe = ACTIVE = w
    game._fade_left = 0   # (the plain crossfade between screens is not played on top)
    game.__dict__.setdefault("area_wipes_log", []).append((key, kind, p))
    return w


def busy(game=None):
    w = getattr(game, "area_wipe", None) if game is not None else ACTIVE
    return w is not None and not w.done()


def draw(game):
    """Game._frame: the wipe over this frame, then a frame on."""
    global ACTIVE
    w = getattr(game, "area_wipe", None)
    if w is None:
        return
    w.draw(game.screen)
    w.t += 1
    if w.done():
        game.area_wipe = None
        if ACTIVE is w:
            ACTIVE = None


def change(state, kind, then, sign=None):
    """A change on a map (a door, stairs, a warp, a hole): in a region with a profile the wipe plays and the change happens
    at once under it; elsewhere just the change. Returns then()'s result."""
    game = state.game
    key = here_key(game)
    snap = game.screen.copy() if key and getattr(game, "screen", None) is not None else None
    out = then()
    if key:
        start(game, kind, key, snap=snap)
    return out


# ---------------------------------------------------------------------------------------------- the area change
def note_leave(game, area_key, edge=False, room=False, kind=None):
    """A map says how you're leaving it (over its edge, from a room), for the area change that follows."""
    game.area_leave = {"area": area_key, "edge": bool(edge), "room": bool(room), "kind": kind}


EDGE_CHARS = "<>^vw"   # (a map's ways out over its edge: west, east, north, south, and over the water; a letter is a door)


def edge_exit(ch, at, size):
    """True if the way out you stand on goes over the map's edge (not through a door): its letter on the map, else
    whether it is on the map's outer ring."""
    if isinstance(ch, str) and ch:
        if ch in EDGE_CHARS:
            return True
        if ch.isalpha() or ch == "D":
            return False
    x, y = at
    w, h = size
    return x <= 0 or y <= 0 or x >= w - 1 or y >= h - 1


def leave_kind(game, from_key, to_key):
    """The kind of change for leaving from_key for to_key (the note the map left, else the two places' kinds)."""
    note = game.__dict__.pop("area_leave", None) or {}
    if note.get("area") not in (None, from_key):
        note = {}
    fr = "inside" if note.get("room") else place_class(game, from_key)
    to = place_class(game, to_key)
    if note.get("kind"):
        return note["kind"], fr == "cave"
    if fr == "outside" and to == "outside" and note.get("edge"):
        return "walk", False
    if to == "cave" and fr != "cave":
        return "cave_in", False
    if fr == "cave" and to != "cave":
        return "cave_out", True
    if to == "outside":
        return "door_out", False
    if fr == to:
        return "stairs", False
    return "door_in", False


def walked(game, key):
    """True if the place is walked on a map (a route or cave map, or a town's own map)."""
    try:
        from src.states.overworld import dungeon, walk_town
        return bool(dungeon.enabled(game, key) or walk_town.available(game, key))
    except Exception:
        return False


def on_map(state):
    try:
        from src.states.overworld.dungeon import DungeonState
        from src.states.overworld.walk_town import WalkTownState
    except Exception:
        return False
    if type(state).__name__ in ("MysteryDungeonState", "HyperspaceState", "Soaring3DState"):
        return False
    return isinstance(state, (DungeonState, WalkTownState))


def quick(game, from_key, to_key, initial_message=None, heal=None, ride=False, travel_lines=None):
    """For AreaTransitionState: (kind, game key) when this change skips the in-between screen (a profiled region, walked
    maps both ends, left from the map itself (or by Fly / an Escape Rope), no ride, no trip to another region's party, no
    professor scene), else None."""
    story = game.story_manager
    note = getattr(game, "area_leave", None) or {}
    from_map = on_map(getattr(game, "current_state", None)) or note.get("kind") in ("escape", "fly")
    if not from_map or ride or heal or travel_lines:
        return None
    if isinstance(initial_message, str) and ("Oak" in initial_message or "Elm" in initial_message):
        return None
    key_from, key_to = game_key(story.area_region(from_key)) if from_key else None, game_key(story.area_region(to_key))
    try:
        key_from = game_key(story.get_current_region()) or key_from
    except Exception:
        pass
    if not key_to or not key_from or not walked(game, to_key):
        return None
    prog = game.loader.area_data.get("STORY_PROGRESSION", {}) or {}
    if any((prog.get(k) or {}).get("mystery_dungeon") or (prog.get(k) or {}).get("hyperspace") for k in (from_key, to_key)):
        return None
    kind, cave_from = leave_kind(game, from_key, to_key)
    return kind, key_to, cave_from


def arrival_lines(game, area_key, lines):
    """Words the in-between screen used to say, said by the map on arrival (its own text box)."""
    lines = [l for l in (lines or []) if l]
    if lines:
        game.arrival_lines = (area_key, list(lines))


def take_arrival_lines(game, area_key):
    got = getattr(game, "arrival_lines", None)
    if got and got[0] == area_key:
        game.arrival_lines = None
        return got[1]
    return None


# ---------------------------------------------------------------------------------------------- the name sign
# Timings in 60 fps frames: (wait, in, hold, out).
SIGN_TIMES = {"frlg": (0, 12, 120, 12), "emerald": (30, 20, 120, 20), "hgss": (0, 10, 60, 10),
              "platinum": (0, 10, 60, 10), "orre": (0, 24, 96, 24)}
SIGN_SRC = {"frlg": 16, "emerald": 16, "hgss": 16, "platinum": 16, "orre": 32}   # (the source game's tile, in its pixels)

EM_MARBLE = ("SLATEPORT", "MAUVILLE", "RUSTBORO", "LILYCOVE", "SOOTOPOLIS", "BATTLE_FRONTIER")
EM_BRICK = ("PETALBURG_CITY", "FORTREE", "MOSSDEEP", "EVER_GRANDE")
EM_SEA = {105, 106, 107, 108, 109, 122} | set(range(124, 135))
EM_THEMES = {   # (frame, inside, text): drawn simply in each sign's colours
    "wood": ((152, 96, 48), (240, 216, 160), (72, 48, 24)),
    "marble": ((184, 184, 200), (248, 248, 248), (64, 64, 80)),
    "brick": ((176, 72, 48), (248, 224, 200), (80, 32, 24)),
    "stone": ((112, 112, 120), (216, 216, 208), (48, 48, 56)),
    "underwater": ((48, 96, 192), (200, 224, 248), (24, 48, 112)),
    "stone2": ((40, 96, 112), (176, 216, 216), (16, 48, 56)),
}
G4_TYPES = {   # (plate, edge, text) by area type: City, Town, Route, Cave, Forest, Water, Park, Lake
    "city": ((80, 120, 200), (40, 64, 128)), "town": ((88, 168, 96), (40, 104, 56)),
    "route": ((216, 168, 80), (144, 96, 40)), "cave": ((152, 120, 96), (88, 64, 48)),
    "forest": ((64, 136, 72), (24, 80, 40)), "water": ((72, 152, 216), (32, 88, 152)),
    "park": ((216, 120, 152), (152, 64, 96)), "lake": ((96, 184, 200), (40, 112, 136)),
}


def em_theme(game, key):
    """Emerald's map-name signboard style for a place (map_name_popup.c's themes by map section)."""
    k = str(key or "").upper()
    data = (game.loader.area_data.get("STORY_PROGRESSION", {}) or {}).get(key) or {}
    if any(w in k for w in ("UNDERWATER", "SEAFLOOR")):
        return "stone2"
    if any(w in k for w in EM_MARBLE):
        return "marble"
    if any(k.endswith(w) or w in k for w in EM_BRICK):
        return "brick"
    num = "".join(ch for ch in k.split("ROUTE_")[-1] if ch.isdigit()) if "ROUTE_" in k else ""
    if num and int(num) in EM_SEA:
        return "underwater"
    if place_class(game, key) in ("cave", "inside") and not any(w in k for w in ("ABANDONED_SHIP", "SAFARI")):
        return "stone"
    return "wood"


def g4_type(game, key):
    data = (game.loader.area_data.get("STORY_PROGRESSION", {}) or {}).get(key) or {}
    k, name = str(key or "").upper(), str(data.get("route_name") or "").lower()
    bt = str(data.get("battle_type") or "").lower()
    if data.get("area_type") == "town":
        return "city" if "city" in name else "town"
    if "lake" in name:
        return "lake"
    if "safari" in name or "park" in name:
        return "park"
    if place_class(game, key) != "outside":
        return "cave"
    if bt == "forest" or "forest" in name or "woods" in name:
        return "forest"
    if bt in ("ocean", "water"):
        return "water"
    return "route"


class Sign:
    """The name on arrival, as the game shows it. t counts this game's frames; wait/in/hold/out are 60 fps frames."""
    def __init__(self, game, key, text, area_key=None):
        self.game, self.key, self.text, self.area_key = game, key, text, area_key
        self.wait, self.tin, self.hold, self.tout = SIGN_TIMES[key]
        self.total = self.wait + self.tin + self.hold + self.tout
        self.t = 0
        self.gone = False
        self.theme = em_theme(game, area_key) if key == "emerald" else g4_type(game, area_key) if key in ("hgss", "platinum") else None
        self._img = None

    def f60(self):
        return self.t * 60.0 / FPS

    def tick(self, busy=False):
        """A frame on (not while a wipe plays: it comes once the new place shows). busy: a text box or an event is up:
        Gen 4's plate and Orre's window go at once (3d, B3)."""
        if self.gone:
            return
        if busy and self.key in ("hgss", "platinum", "orre") and self.f60() >= self.wait:
            self.gone = True
            return
        if ACTIVE is not None and ACTIVE.game is self.game and not ACTIVE.done():
            return
        self.t += 1
        if self.f60() >= self.total:
            self.gone = True

    def phase(self):
        """(phase, how far): wait / in / hold / out / gone."""
        f = self.f60()
        if self.gone:
            return "gone", 1.0
        for name, n in (("wait", self.wait), ("in", self.tin), ("hold", self.hold), ("out", self.tout)):
            if f < n:
                return name, f / float(max(1, n))
            f -= n
        return "gone", 1.0

    def shown(self):
        """How far down it is (0 hidden, 1 all the way)."""
        ph, k = self.phase()
        return {"wait": 0.0, "in": k, "hold": 1.0, "out": 1 - k}.get(ph, 0.0)

    def scale(self):
        try:
            from src.states.overworld.dungeon import TILE
        except Exception:
            TILE = 56
        return TILE / float(SIGN_SRC[self.key])

    def _font(self, px):
        cache = self.game.__dict__.setdefault("_sign_fonts", {})
        if px not in cache:
            try:
                cache[px] = self.game.assets._load_font(px, bold=True)
            except Exception:
                cache[px] = pygame.font.Font(None, px)
        return cache[px]

    def _fit(self, px, width):
        while px > 12:
            f = self._font(px)
            if f.size(self.text)[0] <= width:
                return f
            px -= 2
        return self._font(px)

    def image(self):
        if self._img is None:
            self._img = self._make()
        return self._img

    def _make(self):
        s = self.scale()
        key = self.key
        if key == "frlg":   # a standard text window, white, black words, centred; 14 tiles (19 with a floor, 22 rooftop)
            tiles = 22 if "roof" in self.text.lower() else 19 if any(ch.isdigit() for ch in self.text[-4:]) else 14
            w, h = int(tiles * 8 * s), int(24 * s)
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            r = img.get_rect()
            pygame.draw.rect(img, (88, 88, 96), r, border_radius=int(3 * s))
            pygame.draw.rect(img, (248, 248, 248), r.inflate(-int(2 * s), -int(2 * s)), border_radius=int(2 * s))
            pygame.draw.rect(img, (168, 184, 200), r.inflate(-int(4 * s), -int(4 * s)), max(1, int(s * 0.6)), border_radius=int(2 * s))
            f = self._fit(int(12 * s), w - int(12 * s))
            _shadow_text(img, f, self.text, (72, 72, 80), (208, 208, 200), r.center, int(max(1, s * 0.5)))
            return img
        if key == "emerald":   # a themed signboard: 80x24 inside its frame, the narrow font, centred
            frame, inner, ink = EM_THEMES[self.theme]
            w, h = int(96 * s), int(40 * s)
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            r = img.get_rect()
            pygame.draw.rect(img, frame, r, border_radius=int(3 * s))
            dark = tuple(max(0, c - 50) for c in frame)
            pygame.draw.rect(img, dark, r, max(1, int(s)), border_radius=int(3 * s))
            if self.theme == "wood":   # (planks)
                for yy in range(int(4 * s), h, int(6 * s)):
                    pygame.draw.line(img, dark, (int(2 * s), yy), (w - int(2 * s), yy), max(1, int(s * 0.4)))
            elif self.theme == "brick":
                for row, yy in enumerate(range(0, h, int(6 * s))):
                    pygame.draw.line(img, (232, 200, 176), (0, yy), (w, yy), max(1, int(s * 0.4)))
                    for xx in range((row % 2) * int(6 * s), w, int(12 * s)):
                        pygame.draw.line(img, (232, 200, 176), (xx, yy), (xx, yy + int(6 * s)), max(1, int(s * 0.4)))
            elif self.theme in ("stone", "stone2"):
                for xx in range(int(10 * s), w, int(20 * s)):
                    pygame.draw.line(img, dark, (xx, 0), (xx, int(8 * s)), max(1, int(s * 0.4)))
                    pygame.draw.line(img, dark, (xx + int(10 * s), h - int(8 * s)), (xx + int(10 * s), h), max(1, int(s * 0.4)))
            elif self.theme == "marble":
                pygame.draw.line(img, (150, 150, 170), (int(6 * s), int(3 * s)), (int(30 * s), int(6 * s)), max(1, int(s * 0.4)))
                pygame.draw.line(img, (150, 150, 170), (w - int(30 * s), h - int(4 * s)), (w - int(6 * s), h - int(7 * s)), max(1, int(s * 0.4)))
            box = pygame.Rect(int(8 * s), int(8 * s), int(80 * s), int(24 * s))
            pygame.draw.rect(img, inner, box, border_radius=int(2 * s))
            f = self._fit(int(11 * s), box.w - int(6 * s))
            _shadow_text(img, f, self.text, ink, tuple(min(255, c + 40) for c in inner), box.center, int(max(1, s * 0.5)))
            return img
        if key in ("hgss", "platinum"):   # a plate, 17 tiles wide (136), 4 tiles tall in HGSS, 5 in Platinum
            plate, edge = G4_TYPES[self.theme]
            w, h = int(136 * s), int((32 if key == "hgss" else 40) * s)
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            r = img.get_rect()
            pygame.draw.rect(img, edge, r, border_radius=int(4 * s))
            pygame.draw.rect(img, plate, r.inflate(-int(3 * s), -int(3 * s)), border_radius=int(3 * s))
            if key == "platinum":   # (Platinum's taller plate: a band along its top in the plate's colour, the name below)
                inner = pygame.Rect(int(4 * s), int(10 * s), w - int(8 * s), h - int(14 * s))
            else:
                inner = pygame.Rect(int(4 * s), int(5 * s), w - int(8 * s), h - int(10 * s))
            pygame.draw.rect(img, (248, 248, 240), inner, border_radius=int(2 * s))
            f = self._fit(int(12 * s), inner.w - int(8 * s))
            _shadow_text(img, f, self.text, (64, 64, 64), (200, 200, 192), inner.center, int(max(1, s * 0.5)))
            return img
        # orre: Essentials' message-style window sized to the name, at x = 0
        f = self._font(int(26 * s))
        tw, th = f.size(self.text)
        w, h = tw + int(32 * s), th + int(28 * s)
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        r = img.get_rect()
        pygame.draw.rect(img, (40, 56, 104), r, border_radius=int(6 * s))
        pygame.draw.rect(img, (248, 248, 248), r.inflate(-int(6 * s), -int(6 * s)), border_radius=int(5 * s))
        _shadow_text(img, f, self.text, (80, 80, 88), (184, 184, 192), r.center, int(max(1, s)))
        return img

    def rect(self, view):
        """Where it is now (top-left of the map, slid down as far as it has come)."""
        img = self.image()
        s = self.scale()
        x0 = view.x + (int(8 * s) if self.key == "frlg" else 0)
        rest = view.y + (0 if self.key in ("frlg", "hgss", "platinum", "orre") else 0)
        hide = img.get_height() + (0 if self.key != "emerald" else 0)
        y = rest - int(hide * (1 - self.shown()))
        return pygame.Rect(x0, y, img.get_width(), img.get_height())

    def draw(self, screen, view):
        if self.gone or self.shown() <= 0:
            return
        r = self.rect(view)
        clip = screen.get_clip()
        screen.set_clip(view)
        screen.blit(self.image(), r.topleft)
        screen.set_clip(clip)


def _shadow_text(img, font, text, ink, shade, centre, off):
    sh = font.render(text, True, shade)
    tx = font.render(text, True, ink)
    r = tx.get_rect(center=centre)
    img.blit(sh, (r.x + off, r.y + off))
    img.blit(tx, r.topleft)


def arrival(state, text_fn, inside=False):
    """A map just came up: its sign, if this region's game would show one here. Returns the Sign (or None); the old big
    banner is off for these regions (the caller sets its timer to 0 when this returns anything but False).
    The same place again (back from a battle, a menu) shows none."""
    game = state.game
    key = here_key(game)
    if not key:
        return False
    area = getattr(state, "area_key", None)
    last = getattr(game, "_sign_area", None)
    game._sign_area = area
    if inside:
        game._sign_text = None
    if inside or last == area:
        return None
    return _make_sign(game, key, area, text_fn)


def _make_sign(game, key, area, text_fn):
    try:
        text = text_fn() if callable(text_fn) else text_fn
    except Exception:
        text = None
    if not text:
        return None
    if key in ("hgss", "platinum") and place_class(game, area) == "inside" and not any(
            w in str(text).lower() for w in ("tower", "ruins", "hideout", "warehouse", "chateau")):
        return None   # (Gen 4: never for buildings; towers and ruins are dungeons there)
    if key == "orre" and getattr(game, "_sign_text", None) == text:
        return None   # (Essentials: only when the name differs from the last map's)
    game._sign_text = text
    return Sign(game, key, str(text), area)


def floor_sign(state, text_fn, inside=False, changed=True):
    """Up or down a floor, through a door back outside: the sign again where the game shows one (FireRed with the floor,
    the others the place's name; never inside a building). False: not a profiled region (keep the old banner)."""
    game = state.game
    key = here_key(game)
    if not key:
        return False
    if inside:
        game._sign_text = None   # (Essentials: a building's map has its own name; out again, the town's shows)
    if inside or not changed:
        return None
    return _make_sign(game, key, getattr(state, "area_key", None), text_fn)
