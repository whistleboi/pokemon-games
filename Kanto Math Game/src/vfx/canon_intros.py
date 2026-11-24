"""Battle intros as each walked region's own game plays them (Jordan 11-24, region/systems).

Every walked region plays the intros of the game it is built from, picked the way that game picks them:
- Kanto, Sevii (its areas report KANTO) and the Orange Islands: FireRed/LeafGreen;
- Hoenn: Emerald;  Johto: HeartGold/SoulSilver;  Sinnoh: Platinum;
- Orre: Pokemon Orre 2.1.1 (Pokemon Essentials v21.1, the game its maps come from).
Unova and the menu regions (Kalos, Alola, Galar, Paldea, Decolore...) keep the older intros in transitions.py.

The numbers come from kanto_handoff/transitions_research: GEN3_FRLG_EMERALD.md (pret's pokefirered and
pokeemerald), GEN4_HGSS_PLATINUM.md (pret's pokeplatinum and pokeheartgold) and GEN5_B2W2_AND_ORRE.md
(Orre: the game's own Transitions.rb). Frame counts there are the games' 60 fps frames; they play at the
same real speed here (src.config.FPS). Every effect is drawn in code; the only art reused is the battle's own
trainer sprite, the player's sprite, the wild Pokemon's sprite and, for Orre, the Essentials water and VS
pictures already in assets/transitions. Team logos (Galactic G, Rocket R, Aqua, Magma) are drawn simply.

To add a game (Unova: Black 2, once measured): a select_<game>(c) returning (effect, params, flash), its
effect classes in EFFECTS, and its line in REGION_GAME."""
import math
import random
import re

import pygame

from src.config import FPS

REGION_GAME = {"KANTO": "frlg", "SEVII": "frlg", "ORANGE": "frlg", "HOENN": "emerald", "JOHTO": "hgss",
               "SINNOH": "platinum", "ORRE": "orre"}
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
FEMALE = {"leaf", "may", "dawn", "lyra", "kris", "hilda", "rosa", "serena", "selene", "gloria", "juliana",
          "misty", "female", "girl", "marina", "lucy"}


# ---------------------------------------------------------------------------------------------- what the games look at
class Ctx:
    """What the games look at when they pick an intro (context() fills it from the battle and where you are)."""
    def __init__(self, **kw):
        self.wild, self.double = True, False
        self.foe_levels, self.my_levels = [5], [5]
        self.surfing = self.fished = self.on_map = False
        self.area = "outside"           # outside / inside / cave / water (the area's battle_type)
        self.dark = self.unlit = self.in_room = False   # a dark cave; still dark (no Flash yet); inside a building
        self.night = False
        self.cls, self.name, self.species = "", "", 0
        self.battle_type, self.region = "", ""
        self.foe_sprite = self.foe_image = None
        self.__dict__.update(kw)

    def has(self, *words):
        """The trainer's name holds one of these words (whole words, any case)."""
        return any(re.search(r"\b" + re.escape(w) + r"\b", self.name, re.I) for w in words)


def context(game, target, now=None):
    from src.states.battle import WildBattleState
    from src.pokemon import evolution
    battle = getattr(target, "next_state", None) or target
    story = game.story_manager
    cur = getattr(game, "current_state", None)
    cls = str(getattr(battle, "trainer_class", "") or "").upper()
    foes = [p for p in (getattr(battle, "opponent_team", None) or []) if p is not None]
    mine = [p for p in (story.player_team or []) if p is not None and not p.__dict__.get("is_egg") and p.current_hp > 0]
    on_map = getattr(cur, "run", None) is not None and hasattr(cur, "_on_surf")
    data = story.get_current_area_data() or {}
    bt = str(data.get("battle_type") or "").lower()
    area = {"cave": "cave", "ocean": "water", "water": "water", "sea": "water", "indoor": "inside"}.get(bt, "outside")
    name = str(data.get("route_name") or story.current_area_key or "").lower()
    if bt == "mountain" and "route" not in name:   # (Mt. Moon, Rock Tunnel, Mt. Coronet: caves, under a mountain
        area = "cave"                              #  battle type; a mountain route is out in the open)
    surfing = False
    if on_map:
        try:
            surfing = bool(cur._on_surf())   # (the tile you stand on: the games check the same)
        except Exception:
            surfing = False
    else:
        surfing = area == "water"   # (the route menu, no map: a sea route's battles are on the water)
    recipe = getattr(cur, "recipe", None) if on_map else None
    recipe = recipe if isinstance(recipe, dict) else {}
    dark = bool(recipe.get("dark")) if on_map else bool(getattr(cur, "dark", None))
    unlit = dark and (bool(recipe.get("fog")) if on_map else True)   # (dungeon: Flash clears a dark cave's fog)
    foe = getattr(battle, "opponent_pokemon", None) or (foes[0] if foes else None)
    try:
        species = evolution.base_id(foe) if foe is not None else 0
    except Exception:
        species = int(getattr(foe, "id", 0) or 0)
    try:
        region = str(story.get_current_region() or "").upper()
    except Exception:
        region = ""
    return Ctx(wild=isinstance(battle, WildBattleState) or cls == "WILD",
               double=bool(getattr(battle, "is_doubles", False)),
               foe_levels=[int(getattr(p, "level", 1) or 1) for p in foes] or [1],
               my_levels=[int(getattr(p, "level", 1) or 1) for p in mine] or [1],
               surfing=surfing, fished=bool(getattr(battle, "fished", False)), on_map=on_map, area=area,
               dark=dark, unlit=unlit, in_room=bool(getattr(cur, "room", None)), night=evolution.is_night(now),
               cls=cls, name=str(getattr(battle, "trainer_name", "") or ""), species=int(species or 0),
               battle_type=str(getattr(battle, "battle_type", "") or "").lower(), region=region,
               foe_sprite=getattr(battle, "trainer_sprite", None), foe_image=getattr(foe, "image", None))


class Plan:
    def __init__(self, game_key, effect, params, flash, ctx):
        self.game_key, self.effect, self.params, self.flash, self.ctx = game_key, effect, dict(params), flash, ctx

    def __repr__(self):
        return f"Plan({self.game_key}: {self.effect} {self.params} flash={self.flash})"


def game_for(region):
    return REGION_GAME.get(str(region or "").upper())


def pick(game, target, now=None, ctx=None):
    """The intro this battle gets in this region's game (a Plan), or None (a region without a profile)."""
    c = ctx or context(game, target, now)
    key = game_for(c.region)
    sel = SELECT.get(key)
    if sel is None:
        return None
    effect, params, flash = sel(c)
    return Plan(key, effect, params, flash, c)


def select_for(key, c):
    """For the checks: (effect, params, flash) for a made-up Ctx in game key."""
    return SELECT[key](c)


# ---------------------------------------------------------------------------------------------- Gen 3 (FRLG, Emerald)
G3_WILD = {"normal": ("slice", "white_bars"), "cave": ("clockwise", "grid"), "flash": ("blur", "grid"),
           "water": ("wave", "ripple")}
G3_TRAINER = {"normal": ("balls_trail", "angled"), "cave": ("shuffle", "big_ball"), "flash": ("blur", "grid"),
              "water": ("swirl", "ripple")}
FRLG_LEGENDS = {144, 145, 146, 150, 249, 250, 386}   # StartLegendaryBattle: Blur, whatever the music
E4_FRLG = ("lorelei", "bruno", "agatha", "lance")
E4_EM = ("sidney", "phoebe", "glacia", "drake")


def _g3_place(c, emerald):
    """GetBattleTransitionTypeByMap: a dark map first (FRLG: only till Flash lights it; Emerald's Flash leaves the
    flash level at 1, so every dark cave stays dark), then the water you stand on, then a cave."""
    if c.dark and (emerald or c.unlit):
        return "flash"
    if c.surfing:
        return "water"
    if c.area == "cave" or c.dark:
        return "cave"
    return "normal"


def _g3_table(c, emerald):
    n = 2 if c.double and not c.wild else 1   # (a double trainer: the sum of the first two on each side)
    weaker = sum(c.foe_levels[:n]) < sum(c.my_levels[:n])   # (ties count as stronger)
    row = (G3_WILD if c.wild else G3_TRAINER)[_g3_place(c, emerald)]
    return row[0 if weaker else 1]


def select_frlg(c):
    grey = ("gen3", 2)   # two grey pulses before every FRLG intro
    if not c.wild and c.cls in ("ELITE_FOUR", "CHAMPION"):
        who = next((w for w in E4_FRLG if c.has(w)), "champion") if c.cls == "ELITE_FOUR" else "champion"
        return "mugshot", {"em": False, "who": who}, grey
    if c.wild and c.species in FRLG_LEGENDS:
        return "blur", {"em": False}, grey
    return _g3_table(c, False), {"em": False}, grey


def _em_team(c):
    """Magma or Aqua (Emerald's MAGMA / AQUA intros), from the class or the name it battles under."""
    if c.cls == "TEAM_MAGMA" or c.has("magma", "tabitha", "courtney", "maxie"):
        return "magma"
    if c.cls == "TEAM_AQUA" or c.has("aqua", "matt", "shelly", "archie"):
        return "aqua"
    return None


def select_emerald(c):
    grey = ("gen3", 3)   # three grey pulses in Emerald
    if not c.wild:
        if c.cls in ("ELITE_FOUR", "CHAMPION"):
            who = next((w for w in E4_EM if c.has(w)), "champion") if c.cls == "ELITE_FOUR" else "champion"
            return "mugshot", {"em": True, "who": who}, grey
        team = _em_team(c)
        if team:
            return "big_ball", {"em": True, "art": team, "hold": 60}, grey
        return _g3_table(c, True), {"em": True}, grey
    s = c.species
    if s in (382, 383):
        return "legend_art", {"who": "kyogre" if s == 382 else "groudon"}, grey
    if s == 384:
        return "rayquaza", {}, grey
    if s in (377, 378, 379):
        return "big_ball", {"em": True, "art": {377: "regirock", 378: "regice", 379: "registeel"}[s]}, grey
    if s == 151:
        return "grid", {"em": True}, grey
    if s in (386, 249, 250):
        return "blur", {"em": True}, grey
    return _g3_table(c, True), {"em": True}, grey


# ---------------------------------------------------------------------------------------------- Gen 4 (Platinum, HGSS)
PT_MYTHICAL = {492, 486, 485, 491, 479, 487, 377, 378, 379}   # Shaymin, Regigigas, Heatran, Darkrai, Rotom, Giratina, Regis
PT_LEGENDARY = {483, 484, 480, 482, 493}                       # Dialga, Palkia, Uxie, Azelf, Arceus
GALACTIC_BOSSES = ("mars", "jupiter", "saturn", "cyrus")


def _gen4_base(c):
    """CutInEffects_ForBattle's terrain: water (surfing or fishing), cave, or 'grass' for everything else."""
    if c.surfing or c.fished:
        return "water"
    if c.area == "cave":
        return "cave"
    return "grass"


def select_platinum(c):
    if not c.wild:
        galactic = c.cls in ("GALACTIC", "GALACTIC_GRUNT", "GALACTIC_BOSS", "COMMANDER") or c.has("galactic")
        if galactic:   # (Galactic wins even in a double battle: Mars and Jupiter's tag battle)
            if c.cls in ("GALACTIC_BOSS", "COMMANDER") or c.has(*GALACTIC_BOSSES):
                return "galactic_boss", {}, ("ds", WHITE, 2)
            return "logo_rain", {"logo": "galactic"}, ("ds", BLACK, 2)
        if c.double:   # (a double drops every special intro, Gym Leaders' too)
            return "ds_double", {}, ("ds", WHITE, 2)
        if c.cls == "GYM_LEADER":
            return "leader_banner", {}, ("ds", WHITE, 1)
        if c.cls in ("ELITE_FOUR", "CHAMPION"):
            return "e4_vs", {}, ("ds", WHITE, 1)
    else:
        if c.species in PT_MYTHICAL:
            return "mythical", {}, ("ds", WHITE, 1)
        if c.species in PT_LEGENDARY:
            return "legendary", {"push": 2350}, ("ds", WHITE, 1)
        if c.double:
            return "ds_double", {}, ("ds", WHITE, 2)
    higher = c.foe_levels[0] > c.my_levels[0]   # (strictly higher; a tie is the lower version)
    flash = ("ds", WHITE if higher else BLACK, 2)
    base = _gen4_base(c)
    if c.wild:
        return {"grass": "pt_grass", "water": "pt_water", "cave": "pt_cave"}[base], {"higher": higher}, flash
    return {"grass": "tr_grass", "water": "tr_water", "cave": "tr_cave"}[base], {"higher": higher}, flash


ROCKET_ADMINS = ("petrel", "proton", "archer", "ariana", "giovanni")


def select_hgss(c):
    if not c.wild:
        rocket = c.cls in ("ROCKET", "TEAM_ROCKET", "ROCKET_GRUNT", "ROCKET_ADMIN", "ROCKET_LEADER") or c.has("rocket")
        if rocket and (c.cls in ("ROCKET_ADMIN", "ROCKET_LEADER") or c.has(*ROCKET_ADMINS)):
            return "rocket_admin", {}, ("ds", WHITE, 1)
        if rocket:
            return "logo_rain", {"logo": "rocket"}, ("ds", BLACK, 2)
        if c.cls == "KIMONO_GIRL":
            return "kimono", {}, ("ds", BLACK, 2)
        if c.has("red") and c.cls in ("PKMN_TRAINER", "CHAMPION", "RED"):
            return "red_tiles", {}, ("ds", BLACK, 2)
        if c.double:
            return "ds_double", {}, ("ds", WHITE, 2)
        if c.cls == "GYM_LEADER" or c.cls == "RIVAL" or c.battle_type == "rival":
            return "leader_banner", {}, ("ds", WHITE, 1)   # (HGSS gives Silver the Gym Leaders' banner too)
        if c.cls in ("ELITE_FOUR", "CHAMPION"):
            return "e4_vs", {}, ("ds", WHITE, 1)
    else:
        if c.species == 250:
            return "legendary", {"push": 660}, ("ds", WHITE, 1)   # Ho-Oh
        if c.species == 249:
            return "legendary", {"push": 550}, ("ds", WHITE, 1)   # Lugia
        if c.species in (382, 383, 384, 150, 380, 381):
            return "mythical", {}, ("ds", WHITE, 1)   # the "ancient" ones: Platinum's sixteen camera cuts
        if c.double:
            return "ds_double", {}, ("ds", WHITE, 2)
    flash = ("ds", BLACK if c.night else WHITE, 2)   # HGSS: the time of day, not the levels
    base = _gen4_base(c)
    if c.wild:
        return {"grass": "hg_grass", "water": "hg_water", "cave": "hg_cave"}[base], {"night": c.night}, flash
    # (trainers: Platinum's six, day = its 'higher' version, night = its 'lower')
    return {"grass": "tr_grass", "water": "tr_water", "cave": "tr_cave"}[base], {"higher": not c.night}, flash


# ---------------------------------------------------------------------------------------------- Orre (Essentials v21.1)
ORRE_WILD_DAY = ("or_snake", ("or_diagonal", 0), ("or_diagonal", 3), "or_splash")
ORRE_WILD_NIGHT = ("or_snake", ("or_diagonal", 3), ("or_diagonal", 3), "or_splash")
ORRE_TRAINER_DAY = ("or_two_ball", "or_three_ball_down", "or_ball_down", "or_wavy_three_ball")
ORRE_TRAINER_NIGHT = ("or_spin_split", "or_ball_down", "or_ball_down", "or_wavy_spin")


def _orre_location(c):
    """pbBattleAnimation's location: 3 water (surfing, fishing), 2 a cave, 1 not an outdoor map, else 0."""
    if c.surfing or c.fished:
        return 3
    if c.area == "cave":
        return 2
    if c.area == "inside" or c.in_room:
        return 1
    return 0


def select_orre(c):
    loc = _orre_location(c)
    colour = BLACK if loc == 2 or c.night else WHITE
    if not c.wild and not c.double:   # (the fan game ships VS cards for these bosses, single battles only)
        if c.has("miror", "evice", "vesper") or c.cls in ("MT_BATTLE_MASTER", "MT_BTLMASTER") or c.has("vander"):
            return "or_vs_trainer", {}, ("orre", colour, 1)
        if c.cls == "CHAMPION":
            return "or_vs_e4", {}, None
    if not c.wild and c.double:
        return "or_four_ball", {}, ("orre", colour, 2)
    table = (ORRE_WILD_NIGHT if c.night else ORRE_WILD_DAY) if c.wild else \
        (ORRE_TRAINER_NIGHT if c.night else ORRE_TRAINER_DAY)
    pick_ = table[loc]
    if isinstance(pick_, tuple):
        return pick_[0], {"origin": pick_[1]}, ("orre", colour, 2)
    return pick_, {}, ("orre", colour, 2)


SELECT = {"frlg": select_frlg, "emerald": select_emerald, "platinum": select_platinum, "hgss": select_hgss,
          "orre": select_orre}


# ---------------------------------------------------------------------------------------------- drawing helpers
def _clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def _quad(x0, x1, v0, n, t):
    """Gen 4's QuadraticInterpolationTaskFX32: x(t) = x0 + v0 t + a t^2 / 2, with a chosen so x(n) = x1."""
    t = _clamp(t, 0.0, float(n))
    a = 2.0 * (x1 - x0 - v0 * n) / float(n * n)
    return x0 + v0 * t + 0.5 * a * t * t


_VEILS = {}


def _veil(screen, colour, alpha, rect=None):
    """A see-through layer of colour (alpha 0-255) over the screen, or part of it."""
    alpha = int(alpha)
    if alpha <= 0:
        return
    r = pygame.Rect(rect) if rect is not None else screen.get_rect()
    if alpha >= 255:
        screen.fill(colour, r)
        return
    key = (r.size, colour)
    s = _VEILS.get(key)
    if s is None:
        s = _VEILS[key] = pygame.Surface(r.size)
        s.fill(colour)
    s.set_alpha(alpha)
    screen.blit(s, r)


def _zoom_into(dst, snap, z, cx=None, cy=None):
    """snap drawn into dst zoomed z times about (cx, cy) (the screen's middle): a camera pushing in, or pulling back."""
    W, H = snap.get_size()
    cx = W / 2 if cx is None else cx
    cy = H / 2 if cy is None else cy
    if abs(z - 1.0) < 0.004:
        dst.blit(snap, (0, 0))
        return
    if z > 1:
        w, h = max(2, int(W / z)), max(2, int(H / z))
        x = int(_clamp(cx - w * cx / W, 0, W - w))
        y = int(_clamp(cy - h * cy / H, 0, H - h))
        pygame.transform.scale(snap.subsurface((x, y, w, h)), (W, H), dst)
    else:
        dst.fill(BLACK)
        img = pygame.transform.scale(snap, (max(1, int(W * z)), max(1, int(H * z))))
        dst.blit(img, img.get_rect(center=(int(cx), int(cy))))


def _bands(screen, src, n, dx=None, dy=None, wrap=True):
    """src drawn as n horizontal bands (the source's scanlines): band i moved dx(i) across (wrapping round, as a GBA or
    DS background does), or showing the band dy(i) further down."""
    W, H = src.get_size()
    for i in range(n):
        y0, y1 = i * H // n, (i + 1) * H // n
        if y1 <= y0:
            continue
        if dy is not None:
            r = int(round(i + dy(i))) % n
            screen.blit(src, (0, y0), (0, r * H // n, W, y1 - y0))
            continue
        x = int(dx(i))
        if wrap:
            x %= W
            screen.blit(src, (x, y0), (0, y0, W, y1 - y0))
            if x:
                screen.blit(src, (x - W, y0), (0, y0, W, y1 - y0))
        else:
            screen.blit(src, (x, y0), (0, y0, W, y1 - y0))


_IRIS = {}


def _iris(screen, cx, cy, r, colour=BLACK, inside=False):
    """Colour everywhere outside the circle (inside=True: inside it): the hardware window wipes."""
    W, H = screen.get_size()
    if inside:
        if r > 0:
            pygame.draw.circle(screen, colour, (int(cx), int(cy)), int(r))
        return
    if r <= 0:
        screen.fill(colour)
        return
    key = ((W, H), colour)
    s = _IRIS.get(key)
    if s is None:
        s = _IRIS[key] = pygame.Surface((W, H))
        s.set_colorkey((1, 2, 3))
    s.fill(colour)
    pygame.draw.circle(s, (1, 2, 3), (int(cx), int(cy)), int(r))
    screen.blit(s, (0, 0))


_BALLS = {}


def _ball(d):
    """A Poke Ball, drawn in code (red top, white bottom, the black band and button), d pixels across."""
    d = max(6, int(d))
    if d in _BALLS:
        return _BALLS[d]
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    r = d / 2.0
    c = (int(r), int(r))
    pygame.draw.circle(s, (248, 248, 248), c, int(r))
    top = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(top, (228, 32, 32), c, int(r))
    pygame.draw.circle(top, (248, 96, 80), (int(r * 0.72), int(r * 0.62)), max(1, int(r * 0.22)))   # (a shine)
    top.fill((0, 0, 0, 0), (0, int(r), d, d))
    s.blit(top, (0, 0))
    band = max(2, int(d * 0.09))
    pygame.draw.rect(s, (24, 24, 24), (0, int(r - band / 2), d, band))
    pygame.draw.circle(s, (24, 24, 24), c, max(2, int(r * 0.3)))
    pygame.draw.circle(s, (248, 248, 248), c, max(1, int(r * 0.19)))
    edge = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(edge, (24, 24, 24), c, int(r), max(2, d // 20))
    s.blit(edge, (0, 0))
    _BALLS[d] = s
    return s


def _blit_rot(screen, img, center, angle=0.0, scale=1.0, alpha=255):
    """img drawn centred on center, turned angle degrees and scaled."""
    if img is None or scale <= 0.005 or alpha <= 0:
        return
    if abs(angle) > 0.01 or abs(scale - 1.0) > 0.01:
        img = pygame.transform.rotozoom(img, angle, scale)
    if alpha < 255:
        img = img.copy()
        img.set_alpha(int(alpha))
    screen.blit(img, img.get_rect(center=(int(center[0]), int(center[1]))))


_FONTS = {}


def _font(size):
    size = max(8, int(size))
    if size not in _FONTS:
        _FONTS[size] = pygame.font.Font(None, size)
        _FONTS[size].set_bold(True)
    return _FONTS[size]


_EMBLEMS = {}


def _emblem(kind, d):
    """The villain teams' marks, drawn simply in code: Galactic's G, Rocket's R, Aqua's and Magma's."""
    d = max(8, int(d))
    key = (kind, d)
    if key in _EMBLEMS:
        return _EMBLEMS[key]
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c, r = (d // 2, d // 2), d // 2

    def letter(ch, colour, edge, size=0.92):
        f = _font(d * size)
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            t = f.render(ch, True, edge)
            s.blit(t, t.get_rect(center=(c[0] + ox * d / 120, c[1] + oy * d / 120 + d * 0.04)))
        t = f.render(ch, True, colour)
        s.blit(t, t.get_rect(center=(c[0], c[1] + d * 0.04)))
    if kind == "galactic":   # (a teal G in a gold ring)
        pygame.draw.circle(s, (216, 184, 72), c, r, max(2, d // 14))
        letter("G", (64, 176, 200), (16, 40, 64), 1.0)
    elif kind == "rocket":   # (the red R)
        letter("R", (224, 24, 24), (16, 16, 16), 1.1)
    elif kind == "aqua":     # (a white A over the sea, in a navy ring)
        pygame.draw.circle(s, (24, 40, 112), c, r)
        pygame.draw.circle(s, (72, 136, 232), c, int(r * 0.86), max(2, d // 18))
        for k in range(3):
            y = int(d * (0.62 + 0.09 * k))
            pts = [(int(d * (0.2 + 0.6 * i / 12)), int(y + math.sin(i * 1.4) * d * 0.02)) for i in range(13)]
            pygame.draw.lines(s, (120, 184, 248), False, pts, max(1, d // 40))
        letter("A", (240, 240, 248), (24, 40, 112), 0.8)
    elif kind == "magma":    # (a dark peak with a fire top, in red)
        pygame.draw.circle(s, (176, 32, 24), c, r)
        pygame.draw.circle(s, (240, 120, 48), c, int(r * 0.86), max(2, d // 18))
        pygame.draw.polygon(s, (48, 24, 24), [(int(d * 0.18), int(d * 0.74)), (int(d * 0.4), int(d * 0.36)),
                                              (int(d * 0.5), int(d * 0.48)), (int(d * 0.62), int(d * 0.3)),
                                              (int(d * 0.84), int(d * 0.74))])
        pygame.draw.polygon(s, (248, 184, 64), [(int(d * 0.55), int(d * 0.36)), (int(d * 0.62), int(d * 0.16)),
                                                (int(d * 0.69), int(d * 0.36))])
    _EMBLEMS[key] = s
    return s


def _crop(img):
    if not isinstance(img, pygame.Surface):
        return None
    r = img.get_bounding_rect()
    if r.w < 2 or r.h < 2:
        return None
    return img.subsurface(r).copy()


def _fit(img, h):
    if img is None:
        return None
    w = max(1, int(img.get_width() * h / max(1, img.get_height())))
    return pygame.transform.scale(img, (w, max(1, int(h))))


def _shade(img, k):
    """img darkened toward black by k (0 = as it is, 1 = a black silhouette)."""
    if img is None:
        return None
    out = img.copy()
    v = int(255 * (1 - _clamp(k)))
    out.fill((v, v, v, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _tinted(img, colour):
    """A one-colour silhouette of img."""
    if img is None:
        return None
    out = img.copy()
    out.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    out.fill(colour + (0,), special_flags=pygame.BLEND_RGBA_ADD)
    return out


def _player_img(game):
    try:
        img = game.assets.get_player_image(getattr(game, "player_character", "red") or "red")
    except Exception:
        img = None
    return _crop(img)


def _text(screen, s, size, pos, colour=(248, 248, 248), shadow=(72, 80, 80), anchor="topleft"):
    f = _font(size)
    sh = f.render(str(s), True, shadow)
    tx = f.render(str(s), True, colour)
    r = tx.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    screen.blit(sh, r.move(max(1, size // 14), max(1, size // 14)))
    screen.blit(tx, r)


def _wedge(screen, cx, cy, a0, a1, colour=BLACK, R=3000):
    """A filled slice of a circle round (cx, cy) from angle a0 to a1 (degrees, 0 = right, counter-clockwise up)."""
    if abs(a1 - a0) < 0.01:
        return
    steps = max(2, int(abs(a1 - a0) / 6) + 1)
    pts = [(cx, cy)]
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        pts.append((cx + R * math.cos(a), cy - R * math.sin(a)))
    pygame.draw.polygon(screen, colour, pts)


# ---------------------------------------------------------------------------------------------- effects
class Effect:
    """One game's intro effect. f is in 60 fps frames from the effect's start; LEN is how long it runs."""
    SRC = (256, 192)   # the source game's screen (GBA 240x160, DS 256x192, Orre's 512x384)
    LEN = 30
    END = BLACK        # the colour it ends on (the battle comes in from it)

    def __init__(self, game, snap, c, **p):
        self.game, self.snap, self.c, self.p = game, snap, c, p
        self.W, self.H = snap.get_size()
        self.sx, self.sy = self.W / float(self.SRC[0]), self.H / float(self.SRC[1])
        self.s = min(self.sx, self.sy)   # (sprites keep their shape: scaled by the smaller side)
        self.rng = random.Random(p.get("seed", 7))
        self.buf = pygame.Surface((self.W, self.H))
        self.setup()

    def setup(self):
        pass

    def X(self, x):
        return x * self.sx

    def Y(self, y):
        return y * self.sy

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))


# ---- Gen 3 (GBA 240x160) ------------------------------------------------------------------------------------------
class G3(Effect):
    SRC = (240, 160)

    def setup(self):
        self.em = bool(self.p.get("em"))
        self.setup3()

    def setup3(self):
        pass


class Blur(G3):
    """BLUR: the map pixelates, a step every 3 frames (Emerald 5); from step 10 it fades to black."""
    def setup3(self):
        self.per = 5 if self.em else 3
        self.LEN = max(15 * self.per, 10 * self.per + 13) + 1

    def draw(self, screen, f):
        n = int(f // self.per)
        b = max(1, int(round((n + 1) * self.s)))
        small = pygame.transform.scale(self.snap, (max(1, self.W // b), max(1, self.H // b)))
        pygame.transform.scale(small, (self.W, self.H), screen)
        if n >= 10:
            _veil(screen, BLACK, 255 * (f - 10 * self.per) / 13.0)


class Swirl(G3):
    """SWIRL: each scanline swings sideways on a sine that grows 8 px a frame, while the screen fades to black."""
    LEN = 49

    def draw(self, screen, f):
        screen.fill(BLACK)
        amp, ph = 8 * f * self.sx, 4 * f
        _bands(screen, self.snap, 160, dx=lambda i: amp * math.sin(2 * math.pi * (ph + 2 * i) / 256.0))
        _veil(screen, BLACK, 255 * f / 49.0)


class Shuffle(G3):
    """SHUFFLE: as Swirl but up and down: each scanline shows a line further down on a growing sine."""
    LEN = 49

    def draw(self, screen, f):
        amp = 1.5 * f
        _bands(screen, self.snap, 160, dy=lambda i: amp * math.sin(2 * math.pi * (16.5 * f + 16.5 * i) / 256.0))
        _veil(screen, BLACK, 255 * f / 49.0)


class Ripple(G3):
    """RIPPLE: a gentle up-and-down ripple, growing 1.5 px a frame to 32; then a quick fade (FRLG at 41, Emerald 81)."""
    def setup3(self):
        self.at, self.fade = (81, 9) if self.em else (41, 5)
        self.LEN = self.at + self.fade + 1

    def draw(self, screen, f):
        amp = min(32.0, 1.5 * f)
        _bands(screen, self.snap, 160, dy=lambda i: amp * math.sin(2 * math.pi * (4 * f + 1.5 * i) / 256.0) * 0.25)
        if f >= self.at:
            _veil(screen, BLACK, 255 * (f - self.at) / float(self.fade))


class Wave(G3):
    """WAVE: black comes in from the left 8 px a frame, its edge wavy (40 px, moving)."""
    LEN = 36

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        X, ph = 8 * f, 16 * f
        pts = [(0, 0)] + [(self.X(X + 40 * math.sin(2 * math.pi * (ph + 4 * i) / 256.0)), self.Y(i)) for i in range(161)] \
            + [(0, self.H)]
        pygame.draw.polygon(screen, BLACK, pts)


class Slice(G3):
    """SLICE: odd scanlines slide right and even ones left, faster and faster (to 16 px a frame), over black."""
    def setup3(self):
        off, spd, acc, self.offs = 0, 256, 1, [0.0]
        while off < 240 * 256:
            off += spd
            spd = min(spd + acc, 16 * 256)
            acc = min(acc * 2, 128)
            self.offs.append(off / 256.0)
        self.LEN = len(self.offs)

    def draw(self, screen, f):
        o = self.offs[min(len(self.offs) - 1, int(f))] * self.sx
        screen.fill(BLACK)
        _bands(screen, self.snap, 160, dx=lambda i: o if i % 2 else -o, wrap=False)


class WhiteBars(G3):
    """WHITE_BARS_FADE: bars (FRLG 6, Emerald 8) whiten from the right, each after its own wait; then white goes black."""
    def setup3(self):
        if self.em:
            self.delays, self.speed, self.rate = [0, 20, 15, 40, 10, 25, 35, 5], 16, 1 / 32.0
        else:
            self.delays, self.speed, self.rate = [0, 9, 15, 6, 12, 3], 24, 3 / 64.0
        self.white = max(self.delays) + max(1 / self.rate, 240.0 / self.speed)
        self.LEN = int(self.white + 17) + 1

    def draw(self, screen, f):
        if f >= self.white:
            v = int(255 * (1 - _clamp((f - self.white) / 17.0)))
            screen.fill((v, v, v))
            return
        screen.blit(self.snap, (0, 0))
        n = len(self.delays)
        for b, d in enumerate(self.delays):
            u = f - d
            if u <= 0:
                continue
            w = min(240.0, self.speed * u)
            y0, y1 = int(self.H * b / n), int(self.H * (b + 1) / n)
            _veil(screen, WHITE, 255 * _clamp(u * self.rate), (int(self.X(240 - w)), y0, int(self.X(w)) + 1, y1 - y0))


class Grid(G3):
    """GRID_SQUARES: the screen under a grid of 8x8 black squares that shrink a step every 3 frames (14 steps), a
    16-frame wait, then black. (Read from pokeemerald's code; not yet checked against a capture: see the research.)"""
    LEN = 14 * 3 + 16 + 1

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        step = min(14, int(f // 3))
        size = 8.0 * (14 - step) / 14.0
        if size <= 0:
            return
        w, h = self.X(size), self.Y(size)
        for gy in range(20):
            for gx in range(30):
                cx, cy = self.X(gx * 8 + 4), self.Y(gy * 8 + 4)
                screen.fill(BLACK, (int(cx - w / 2), int(cy - h / 2), int(math.ceil(w)), int(math.ceil(h))))


class Angled(G3):
    """ANGLED_WIPES: seven diagonal black slashes, each traced 16 points a frame, blacking one side of each scanline."""
    WIPES = [(56, 0, 0, 160, 0), (104, 160, 240, 88, 1), (240, 72, 56, 0, 1), (0, 32, 144, 160, 0),
             (144, 160, 184, 0, 1), (56, 0, 168, 160, 0), (168, 160, 48, 0, 1)]

    def setup3(self):
        gaps = [8, 4, 2, 1, 1, 1] if self.em else [1] * 6
        L, R, self.frames = [0] * 160, [240] * 160, []
        for w, (x0, y0, x1, y1, d) in enumerate(self.WIPES):
            n = max(abs(x1 - x0), abs(y1 - y0))
            pts = [(x0 + (x1 - x0) * k / float(n), y0 + (y1 - y0) * k / float(n)) for k in range(n + 1)]
            for i in range(0, len(pts), 16):
                for x, y in pts[i:i + 16]:
                    y = int(round(y))
                    if 0 <= y < 160:
                        if d == 0:
                            L[y] = min(max(L[y], int(x)), R[y])
                        else:
                            R[y] = max(min(R[y], int(x)), L[y])
                self.frames.append((L[:], R[:]))
            for _ in range(gaps[w] if w < len(gaps) else 0):
                self.frames.append((L[:], R[:]))
        self.LEN = len(self.frames) + 1

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        L, R = self.frames[min(len(self.frames) - 1, int(f))]
        for y in range(160):
            y0, y1 = int(self.Y(y)), int(self.Y(y + 1))
            if L[y] > 0:
                screen.fill(BLACK, (0, y0, int(self.X(L[y])) + 1, y1 - y0))
            if R[y] < 240:
                x = int(self.X(R[y]))
                screen.fill(BLACK, (x, y0, self.W - x, y1 - y0))


class Clockwise(G3):
    """CLOCKWISE_WIPE: a black wedge sweeps round the middle like a clock hand from 12 o'clock (about 71 frames)."""
    PATH = [(120, 0), (240, 0), (240, 160), (0, 160), (0, 0), (120, 0)]
    SPEED = [16, 8, 16, 8, 16]
    LEN = 72

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        pts, left = [(120, 80), self.PATH[0]], f
        for (a, b), v in zip(zip(self.PATH, self.PATH[1:]), self.SPEED):
            seg = math.hypot(b[0] - a[0], b[1] - a[1]) / v
            if left >= seg:
                pts.append(b)
                left -= seg
                continue
            k = left / seg
            pts.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
            break
        if len(pts) >= 3:
            pygame.draw.polygon(screen, BLACK, [(self.X(x), self.Y(y)) for x, y in pts])


class BallsTrail(G3):
    """POKEBALLS_TRAIL: five Poke Balls roll across 8 px a frame, from alternate sides, each leaving a black strip."""
    def setup3(self):
        self.delays = [0, 32, 64, 18, 48] if self.em else [0, 16, 32, 8, 24]
        self.first = self.rng.choice((-1, 1))
        self.LEN = max(self.delays) + 36

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        d = self.Y(30)
        for r, delay in enumerate(self.delays):
            u = f - delay
            if u < 0:
                continue
            side = self.first if r % 2 == 0 else -self.first   # (-1: from the left)
            x = (-16 + 8 * u) if side < 0 else (256 - 8 * u)
            y0 = self.Y(r * 32)
            if side < 0:
                screen.fill(BLACK, (0, int(y0), int(self.X(max(0, x))), int(math.ceil(self.Y(32)))))
            else:
                xx = int(self.X(min(240, x)))
                screen.fill(BLACK, (xx, int(y0), self.W - xx, int(math.ceil(self.Y(32)))))
            _blit_rot(screen, _ball(d), (self.X(x), self.Y(r * 32 + 16)), angle=-side * 360 * 4 / 256.0 * u)


class BigBall(G3):
    """The pattern weave (BIG_POKEBALL; Emerald's Aqua, Magma and Regi intros too): a full-screen picture fades in over
    the map, its scanlines shimmering apart and settling; the map behind fades out; then a circle closes on it."""
    def setup3(self):
        self.art = self.p.get("art", "ball")
        self.img = self._art()
        self.rate = 1.0 if self.em else 1.5
        self.t_in = 32 if self.em else 16
        settle = max(64 / self.rate, self.t_in + 32)
        self.iris_at = settle + self.p.get("hold", 0)
        r, v, acc, cap, self.radii = 160.0, 1.0, (0.5 if self.em else 1.0), (4 if self.em else 8), []
        while r > 0:
            r -= v
            v = min(cap, v + acc)
            self.radii.append(max(0.0, r))
        self.LEN = int(self.iris_at) + len(self.radii) + 1

    def _art(self):
        W, H = self.W, self.H
        img = pygame.Surface((W, H), pygame.SRCALPHA)
        if self.art == "ball":   # (big_pokeball: a large Poke Ball in its red (246,8,0) / dark red (148,0,0))
            d = int(H * 0.9)
            ball = pygame.Surface((d, d), pygame.SRCALPHA)
            r = d // 2
            pygame.draw.circle(ball, (248, 248, 248), (r, r), r)
            top = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(top, (148, 0, 0), (r, r), r)
            pygame.draw.circle(top, (246, 8, 0), (r, r), int(r * 0.88))
            top.fill((0, 0, 0, 0), (0, r, d, d))
            ball.blit(top, (0, 0))
            pygame.draw.circle(ball, (176, 176, 184), (r, r), r, max(3, d // 40))
            pygame.draw.rect(ball, (16, 16, 16), (0, r - d // 22, d, d // 11))
            pygame.draw.circle(ball, (16, 16, 16), (r, r), int(r * 0.32))
            pygame.draw.circle(ball, (208, 208, 216), (r, r), int(r * 0.22))
            pygame.draw.circle(ball, (248, 248, 248), (r, r), int(r * 0.14))
            img.blit(ball, ball.get_rect(center=(W // 2, H // 2)))
        elif self.art in ("aqua", "magma"):
            e = _emblem(self.art, H * 0.86)
            img.blit(e, e.get_rect(center=(W // 2, H // 2)))
        else:   # (regis.png: braille dots, in that Regi's colours)
            col = {"regirock": ((200, 112, 56), (120, 56, 24)), "regice": ((168, 224, 248), (72, 136, 200)),
                   "registeel": ((176, 176, 192), (88, 88, 112))}.get(self.art, ((200, 200, 200), (100, 100, 100)))
            img.fill(col[1] + (255,))
            dot = max(3, int(self.s * 3))
            rng = random.Random(self.art)
            for gy in range(0, 160, 10):
                for gx in range(0, 240, 8):
                    for k in range(6):
                        if rng.random() < 0.55:
                            pygame.draw.circle(img, col[0], (int(self.X(gx + 2 + (k % 2) * 4)), int(self.Y(gy + 2 + (k // 2) * 3))), dot // 2)
        return img

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        _veil(screen, BLACK, 255 * _clamp((f - self.t_in) / 32.0))
        amp = max(0.0, 64 - self.rate * f) * self.sx
        self.img.set_alpha(int(255 * _clamp(f / float(self.t_in))))
        _bands(screen, self.img, 160, dx=lambda i: amp * math.sin(2 * math.pi * (8 * f + 132 * i) / 256.0))
        self.img.set_alpha(None)
        if f >= self.iris_at:
            r = self.radii[min(len(self.radii) - 1, int(f - self.iris_at))]
            _iris(screen, self.W / 2, self.H / 2, r * (self.sx + self.sy) / 2)


MUGSHOT_COLOURS = {"lorelei": ((189, 0, 189), (255, 65, 255)), "sidney": ((189, 0, 189), (255, 65, 255)),
                   "bruno": ((8, 213, 8), (123, 255, 123)), "phoebe": ((8, 213, 8), (123, 255, 123)),
                   "agatha": ((255, 82, 172), (255, 148, 238)), "glacia": ((255, 82, 172), (255, 148, 238)),
                   "lance": ((0, 0, 131), (65, 65, 197)), "drake": ((0, 0, 131), (65, 65, 197)),
                   "champion": ((197, 197, 65), (255, 255, 131))}
PLAYER_MUGSHOT = {"m": ((106, 180, 213), (172, 246, 255)), "f": ((230, 123, 139), (255, 189, 205))}


class Mugshot(G3):
    """The Elite Four / Champion VS screen: the striped banner closes in (top from the left, bottom from the right),
    the foe slides in, then you (mirrored), a white spreads out from the middle line, then black."""
    def setup3(self):
        foe = MUGSHOT_COLOURS.get(self.p.get("who", "champion"), MUGSHOT_COLOURS["champion"])
        me = PLAYER_MUGSHOT["f" if str(getattr(self.game, "player_character", "")).lower() in FEMALE else "m"]
        self.top, self.bottom = self._stripes(foe), self._stripes(me)
        h = self.Y(78)
        self.foe = _fit(_crop(self.c.foe_sprite), h)
        self.me = _fit(_player_img(self.game), h)
        if self.me is not None:
            self.me = pygame.transform.flip(self.me, True, False)

        def slide(x, v, past, sign):
            out = []
            while v > 0:
                x += sign * v
                if (x > past) if sign > 0 else (x < past):
                    v -= 1
                out.append(x)
            return out
        self.foe_x = slide(-32, 12, 103, 1)
        self.me_x = slide(272, 12, 133, -1)
        self.t_foe = 30
        self.t_me = self.t_foe + len(self.foe_x)
        self.t_white = self.t_me + len(self.me_x)
        self.LEN = self.t_white + 56 + 16 + 1

    def _stripes(self, cols):
        """A half-screen of slanted stripes in five steps from one colour to the other, wide enough to scroll."""
        a, b = cols
        steps = [tuple(int(a[k] + (b[k] - a[k]) * i / 4.0) for k in range(3)) for i in range(5)]
        seq = steps + steps[-2:0:-1]
        bw = self.X(8)
        self.period = int(bw * len(seq))
        h = self.H // 2
        s = pygame.Surface((self.W + self.period * 2, h))
        for i in range(int((self.W + self.period * 2 + h) / bw) + 2):
            x = i * bw - h
            pygame.draw.polygon(s, seq[i % len(seq)], [(x, h), (x + bw, h), (x + bw + h, 0), (x + h, 0)])
        return s

    def draw(self, screen, f):
        W, H, h = self.W, self.H, self.H // 2
        screen.blit(self.snap, (0, 0))
        scroll = int(self.X(8 * f)) % self.period
        for half, src, sign in ((0, self.top, 1), (1, self.bottom, -1)):
            off = -scroll if sign > 0 else scroll - self.period
            for i in range(80):
                line = half * 80 + i
                y0, y1 = int(self.Y(line)), int(self.Y(line + 1))
                wx = self.X(8 * f + 16 * math.sin(2 * math.pi * (8 * f + 8 * i) / 256.0) - 16)
                if wx <= 0:
                    continue
                wx = int(min(W, wx))
                ys = y0 - half * h
                if half == 0:
                    screen.blit(src, (0, y0), (-off, ys, wx, y1 - y0))
                else:
                    screen.blit(src, (W - wx, y0), (W - wx - off, ys, wx, y1 - y0))
        if f >= 30:
            screen.fill(BLACK, (0, h - int(self.Y(1)), W, int(self.Y(2))))
        if self.foe is not None and f >= self.t_foe:
            x = self.foe_x[min(len(self.foe_x) - 1, int(f - self.t_foe))]
            screen.blit(self.foe, self.foe.get_rect(midbottom=(int(self.X(x)), h - int(self.Y(1)))))
        if self.me is not None and f >= self.t_me:
            x = self.me_x[min(len(self.me_x) - 1, int(f - self.t_me))]
            screen.blit(self.me, self.me.get_rect(midbottom=(int(self.X(x)), H)))
        if f >= self.t_white:   # (the white spreads two lines a frame from the middle, each line whitening in turn)
            u = f - self.t_white
            if u >= 56:
                v = int(255 * (1 - _clamp((u - 56) / 16.0)))
                screen.fill((v, v, v))
                return
            col = pygame.Surface((1, 160), pygame.SRCALPHA)
            for y in range(160):
                a = _clamp((u - abs(y - 80) / 2.0) / 16.0)
                col.set_at((0, y), (255, 255, 255, int(255 * a)))
            screen.blit(pygame.transform.scale(col, (W, H)), (0, 0))


class LegendArt(G3):
    """KYOGRE / GROUDON: the map goes black, the legend's picture glows through ten flashing palettes, brightens,
    holds, and fades to black. (The ROM's artwork isn't here: the wild Pokemon's own sprite stands in for it.)"""
    LEN = 25 + 59 + 69 + 30 + 25 + 1

    def setup3(self):
        who = self.p.get("who", "kyogre")
        self.base, self.glow = ((16, 32, 104), (255, 72, 72)) if who == "kyogre" else ((104, 24, 16), (72, 168, 255))
        img = _fit(_crop(self.c.foe_image), self.H * 0.78)
        self.img = img
        self.sil = _tinted(img, self.base)
        self.rim = _tinted(img, self.glow)

    def _art(self, screen, glow, lit, fade):
        if self.img is None:
            return
        at = self.img.get_rect(center=(self.W // 2, self.H // 2))
        for dx, dy in ((-6, 0), (6, 0), (0, -6), (0, 6)):
            r = self.rim.copy()
            r.set_alpha(int(255 * glow))
            screen.blit(r, at.move(dx, dy))
        screen.blit(self.sil, at)
        if lit > 0:
            body = self.img.copy()
            body.set_alpha(int(255 * lit))
            screen.blit(body, at)
        if fade > 0:
            _veil(screen, BLACK, 255 * fade, at)

    def draw(self, screen, f):
        if f < 25:
            screen.blit(self.snap, (0, 0))
            _veil(screen, BLACK, 255 * f / 25.0)
            return
        screen.fill(BLACK)
        if f < 84:
            idx = int((f - 25) // 3) % 10
            self._art(screen, 0.35 + 0.65 * abs(math.sin(idx * math.pi / 5)), 0.0, 0.0)
        elif f < 153:
            self._art(screen, 1.0, int((f - 84) // 5) / 13.0 * 0.85, 0.0)
        elif f < 183:
            self._art(screen, 1.0, 0.85, 0.0)
        else:
            self._art(screen, 1.0, 0.85, _clamp((f - 183) / 25.0))


class Rayquaza(LegendArt):
    """RAYQUAZA: the map goes black, Rayquaza flashes in green, fades; the map at half brightness with three rings
    cycling, a dark 'black hole' that shudders smaller, then black grows from the middle over everything."""
    def setup3(self):
        self.p["who"] = "rayquaza"
        img = _fit(_crop(self.c.foe_image), self.H * 0.78)
        self.img, self.base, self.glow = img, (16, 64, 24), (120, 248, 120)
        self.sil, self.rim = _tinted(img, self.base), _tinted(img, self.glow)
        r, k, self.hole = 48.0, 0, []
        while r >= 9:
            r += -6 if k % 2 == 0 else 4
            k += 1
            self.hole.append(r)
        g, v, self.grow = 0.0, 0.0, []
        while g < 160:
            v = min(4.0, v + 0.5)
            g += v
            self.grow.append(g)
        self.t_rings = 25 + 40 + 20 + 33
        self.t_hole = self.t_rings + 40
        self.t_grow = self.t_hole + len(self.hole)
        self.LEN = self.t_grow + len(self.grow) + 1

    def draw(self, screen, f):
        if f < 25:
            screen.blit(self.snap, (0, 0))
            _veil(screen, BLACK, 255 * f / 25.0)
            return
        if f < self.t_rings:
            screen.fill(BLACK)
            if f < 65:
                self._art(screen, 1.0 if int((f - 25) // 4) % 2 == 0 else 0.3, 0.0, 0.0)
            elif f < 85:
                self._art(screen, 0.6, 0.0, 0.0)
            else:
                self._art(screen, 0.6, 0.0, _clamp((f - 85) / 33.0))
            return
        screen.blit(self.snap, (0, 0))
        _veil(screen, BLACK, 128)
        cx, cy, k = self.W / 2, self.H / 2, (self.sx + self.sy) / 2
        for i in range(3):   # (the tri-ring palette cycle)
            lit = (int(f // 3) + i) % 3 == 0
            pygame.draw.circle(screen, (120, 248, 120) if lit else (24, 96, 40), (int(cx), int(cy)), int(k * (36 + 18 * i)), max(2, int(k * 3)))
        if f >= self.t_hole:
            r = self.hole[min(len(self.hole) - 1, int(f - self.t_hole))]
            pygame.draw.circle(screen, BLACK, (int(cx), int(cy)), int(r * k))
            pygame.draw.circle(screen, (88, 200, 104), (int(cx), int(cy)), int(r * k), max(2, int(k)))
        if f >= self.t_grow:
            g = self.grow[min(len(self.grow) - 1, int(f - self.t_grow))]
            pygame.draw.circle(screen, BLACK, (int(cx), int(cy)), int(g * k))


# ---- Gen 4 (DS 256x192) -------------------------------------------------------------------------------------------
class G4(Effect):
    SRC = (256, 192)
    BALL = 32   # (the encounter effect's Poke Ball sprite, DS pixels)

    def setup(self):
        self.higher = bool(self.p.get("higher"))
        self.setup4()

    def setup4(self):
        pass

    def cam(self, z):
        """The field under the camera: z > 1 pushes in (Gen 4's camera distance, roughly 1 + push/1000)."""
        _zoom_into(self.buf, self.snap, z)
        return self.buf

    def ball(self, screen, x, y, angle=0.0, scale=1.0, alpha=255):
        _blit_rot(screen, _ball(self.BALL * self.s), (self.X(x), self.Y(y)), angle, scale, alpha)

    def x_close(self, screen, k):
        """Fade type 34: black wedges grow from the middle up, down, left and right until they meet on the diagonals."""
        a = 45 * _clamp(k)
        cx, cy = self.W / 2, self.H / 2
        for axis in (0, 90, 180, 270):
            _wedge(screen, cx, cy, axis - a, axis + a)

    def wave(self, screen, src, periods, amp, f, interlace=False):
        ph = 800 / 65536.0 * f
        _bands(screen, src, 192, dx=lambda i: (-1 if interlace and (i // 2) % 2 else 1)
               * self.X(amp) * math.sin(2 * math.pi * (periods * i / 192.0 + ph)))


class PtGrass(G4):
    """Platinum wild, on land: the field cut into strips (5 px; foe higher: 2 px) that jitter, then fly apart left
    and right, while the camera pulls back and pushes in."""
    LEN = 14

    def draw(self, screen, f):
        h = 2 if self.higher else 5
        n = 192 // h
        if f < 7:
            d = _quad(0, -(3 if self.higher else 2), 12, 7, f)
            z = 1 - _quad(0, 50, 30, 7, f) / 1000.0
        else:
            d = _quad(-2, 255, 30, 6, f - 7)
            z = 1 - _quad(50, 0 if self.higher else 20, -30, 6, f - 7) / 1000.0
        src = self.cam(z)
        screen.fill(BLACK)
        _bands(screen, src, n, dx=lambda i: self.X(d) * (1 if i % 2 == 0 else -1), wrap=False)


class PtWater(G4):
    """Platinum wild, on the water: the field sways on a sine (2 waves, 12 px; foe higher: 3 and 15), then the
    three-slat blind closes it to black."""
    LEN = 21

    def draw(self, screen, f):
        screen.fill(BLACK)
        self.wave(screen, self.snap, 3 if self.higher else 2, 15 if self.higher else 12, f)
        if f >= 12:
            k = _clamp((f - 12) / 8.0)
            for b in range(3):
                screen.fill(BLACK, (0, int(self.Y(b * 64)), self.W, int(math.ceil(self.Y(64 * k)))))


class PtCave(G4):
    """Platinum wild, in a cave: a circle closes to black while the camera pushes in."""
    LEN = 13

    def draw(self, screen, f):
        push = 800 if self.higher else 400
        z = 1 + _quad(0, push, 5 if self.higher else 2, 12, f) / 1000.0
        screen.blit(self.cam(z), (0, 0))
        _iris(screen, self.W / 2, self.H / 2, self.s * 256 * (1 - _clamp(f / 12.0)))


class TrGrass(G4):
    """Trainers on land. Lower (Platinum foe not higher; HGSS night): two Poke Balls grow and spin at the middle, then
    the top half slides right and the bottom half left. Higher (HGSS day): two balls cross, then the halves shrink
    away to opposite corners. The camera pushes in."""
    def setup4(self):
        self.LEN = 17 if self.higher else 18

    def draw(self, screen, f):
        screen.fill(BLACK)
        W, H = self.W, self.H
        if not self.higher:
            if f < 10:
                screen.blit(self.snap, (0, 0))
                sc = _clamp(_quad(0.01, 1.0, 0, 10, f))
                self.ball(screen, 128, 96, -360 * f / 10.0 + 24, sc)
                self.ball(screen, 128, 96, -360 * f / 10.0, sc)
                return
            k = f - 10
            d = _quad(0, 255, 10, 6, k)
            src = self.cam(1 + _quad(0, 500, 0, 6, k) / 1000.0)
            screen.blit(src, (int(self.X(d)), 0), (0, 0, W, H // 2))
            screen.blit(src, (-int(self.X(d)), H // 2), (0, H // 2, W, H - H // 2))
            self.ball(screen, 128 + d, 96)
            self.ball(screen, 128 - d, 96)
            return
        if f < 8:
            screen.blit(self.snap, (0, 0))
            self.ball(screen, 320 - 384 * f / 8.0, 64, 720 * f / 8.0)
            self.ball(screen, -64 + 384 * f / 8.0, 128, -720 * f / 8.0)
            return
        k = _clamp(_quad(0, 1, 0, 8, f - 8))
        src = self.cam(1 + 0.5 * k)
        w, h = int(W * (1 - k)), int(H / 2 * (1 - k))
        if w > 0 and h > 0:
            screen.blit(src, (0, 0), (0, 0, w, h))
            screen.blit(src, (W - w, H - h), (W - w, H - h, w, h))


class TrWater(G4):
    """Trainers on the water. Lower: the field sways in interlaced bands, two balls fade in spinning, then shrink while
    a black box grows from the middle. Higher: three balls rise from below, each dragging a black column up."""
    def setup4(self):
        self.LEN = 22 if not self.higher else 20

    def draw(self, screen, f):
        screen.fill(BLACK)
        z = 1 + _quad(0, 500, 0, 16 if self.higher else 20, f) / 1000.0
        src = self.cam(z)
        if not self.higher:
            self.wave(screen, src, 2, 12, f, interlace=True)
            if f >= 4:
                u = f - 4
                if u < 8:
                    for x in (88, 168):
                        self.ball(screen, x, 96, -360 * u / 8.0, 1.0, 255 * u / 8.0)
                else:
                    k = _clamp((u - 8) / 8.0)
                    for x in (88, 168):
                        self.ball(screen, x, 96, 0, max(0.01, 1 - k))
                    w, h = self.W * k, self.H * k
                    screen.fill(BLACK, (int((self.W - w) / 2), int((self.H - h) / 2), int(w) + 1, int(h) + 1))
            return
        self.wave(screen, src, 3, 15, f)
        for x, start, spin in ((43, 2, 1), (215, 6, -1), (129, 8, 1)):
            u = f - start
            if u < 0:
                continue
            y = _quad(231, -32, 0, 6, u)
            top = int(self.Y(max(0, y)))
            screen.fill(BLACK, (int(self.X(x - 43)), top, int(math.ceil(self.X(86))), self.H - top))
            if u <= 6:
                self.ball(screen, x, y, spin * 360 * u / 6.0)


class TrCave(G4):
    """Trainers in a cave. Lower: one ball falls, growing and spinning, then an arched black curtain drops. Higher:
    three balls fall, then black 32 px tiles fill the screen from the bottom row up, one a frame."""
    ORDER = [0, 2, 5, 7, 1, 6, 3, 4]

    def setup4(self):
        self.LEN = 21 if not self.higher else 8 + 48 + 1

    def draw(self, screen, f):
        z = 1 + _quad(0, 1000, 10, 20 if not self.higher else 64, f) / 1000.0
        screen.blit(self.cam(z), (0, 0))
        if not self.higher:
            if f < 12:
                self.ball(screen, 128, _quad(-32, 224, 2, 12, f), 360 * f / 12.0, 0.1 + 1.9 * f / 12.0)
                return
            k = _clamp((f - 12) / 8.0)
            _iris(screen, self.X(128), self.Y(288), self.s * 512 * (1 - k))
            return
        for x, start, spin in ((128, 0, 1), (208, 1, -1), (48, 3, 1)):
            u = f - start
            if 0 <= u <= 5:
                self.ball(screen, x, -32 + 256 * u / 5.0, spin * 360 * u / 5.0)
        n = int(f - 8)
        for t in range(min(48, max(0, n + 1))):
            row, col = 5 - t // 8, self.ORDER[t % 8]
            screen.fill(BLACK, (int(self.X(col * 32)), int(self.Y(row * 32)), int(math.ceil(self.X(32))) + 1, int(math.ceil(self.Y(32))) + 1))


class DsDouble(G4):
    """Any double battle (Platinum and HGSS): four Poke Balls burst out from the middle, then the four-wedge X close."""
    LEN = 13

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        k = _quad(0, 1, 0, 4, f)
        for dx, dy in ((0, -128), (0, 128), (-160, 0), (160, 0)):
            self.ball(screen, 128 + dx * k, 96 + dy * k)
        if f >= 4:
            self.x_close(screen, (f - 4) / 8.0)


class LogoRain(G4):
    """Galactic Grunts (Platinum) and Rocket Grunts (HGSS): six logos fly in one after another from the edges,
    spinning and shrinking to the middle, then the four-wedge X close. (HGSS's art isn't decoded: its R stands in.)"""
    STARTS = [(260, 0, 2), (-16, 160, 1), (0, -16, -3), (140, 160, -2), (260, 80, -3), (0, 160, 1)]
    DELAYS = [0, 4, 7, 11, 13, 16]
    LEN = 16 + 8 + 12 + 1

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        logo = _emblem(self.p.get("logo", "galactic"), 32 * self.s)
        for (x0, y0, turns), d in zip(self.STARTS, self.DELAYS):
            u = f - d
            if 0 <= u <= 8:
                k = _quad(0, 1, 0, 8, u)
                _blit_rot(screen, logo, (self.X(x0 + (128 - x0) * k), self.Y(y0 + (100 - y0) * k)),
                          360 * turns * u / 8.0, 2.0 - 1.99 * u / 8.0)
        if f >= 24:
            self.x_close(screen, (f - 24) / 12.0)


class GalacticBoss(G4):
    """Mars, Jupiter, Saturn and Cyrus: the big Galactic logo fades in, holds, pixelates, while eight black blades fan
    out from the middle."""
    LEN = 15 + 16 + 16 + 1
    PAIRS = [(0, 23), (45, 22), (45, 68), (90, 67), (91, 113), (135, 112), (135, 158), (180, 157)]

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        logo = _emblem("galactic", 120 * self.s)
        if f >= 31:
            m = int(14 * _clamp((f - 31) / 16.0)) + 1
            if m > 1:
                small = pygame.transform.scale(logo, (max(1, logo.get_width() // m), max(1, logo.get_height() // m)))
                logo = pygame.transform.scale(small, logo.get_size())
        _blit_rot(screen, logo, (self.W / 2, self.H / 2), alpha=255 * _clamp(f / 15.0))
        if f >= 31:
            k = _clamp((f - 31) / 16.0)
            cx, cy = self.W / 2, self.H / 2
            for a0, a1 in self.PAIRS:
                a = a0 + (a1 - a0) * k
                _wedge(screen, cx, cy, a0, a)
                _wedge(screen, cx, cy, -a0, -a)
            screen.fill(BLACK, (0, int(self.Y(93)), self.W, int(math.ceil(self.Y(6)))))


LEADER_COLOURS = {"roark": (176, 112, 64), "gardenia": (72, 168, 72), "wake": (64, 128, 224), "maylene": (224, 104, 80),
                  "fantina": (152, 88, 184), "candice": (136, 200, 232), "byron": (144, 152, 168), "volkner": (232, 200, 56),
                  "falkner": (120, 168, 232), "bugsy": (136, 184, 40), "whitney": (240, 128, 176), "morty": (120, 88, 168),
                  "chuck": (200, 104, 56), "jasmine": (168, 176, 192), "pryce": (152, 208, 224), "clair": (96, 72, 200),
                  "brock": (168, 136, 88), "misty": (72, 152, 232), "surge": (232, 192, 48), "erika": (96, 184, 96),
                  "janine": (168, 72, 168), "sabrina": (216, 96, 160), "blaine": (224, 72, 48), "blue": (72, 120, 200)}


class LeaderBanner(G4):
    """Platinum's Gym Leader intro (HGSS: its leaders and Silver): the leader's banner wipes in from the right with a
    saw-tooth edge, scrolling; an emblem pops; the leader slides in as a silhouette; a white flash and they're in
    colour, the field dims, their name shows; a hold, then white. (Banner colours stand in for the ROM's art.)"""
    LEN = 96
    END = WHITE

    def setup4(self):
        name = self.c.name.lower()
        rival = self.c.cls == "RIVAL" or self.c.battle_type == "rival"
        self.colour = (200, 48, 56) if rival else next((v for k, v in LEADER_COLOURS.items() if k in name), (88, 120, 200))
        self.band = pygame.Rect(0, int(self.Y(34)), self.W, int(self.Y(80)))
        stripes = pygame.Surface((self.W * 2, self.band.h))
        dark = tuple(int(v * 0.62) for v in self.colour)
        stripes.fill(dark)
        bw = int(self.X(10))
        for i in range(-2, self.W * 2 // bw + 4, 2):
            x = i * bw
            pygame.draw.polygon(stripes, self.colour, [(x, self.band.h), (x + bw, self.band.h), (x + bw + self.band.h, 0), (x + self.band.h, 0)])
        self.stripes = stripes
        foe = _fit(_crop(self.c.foe_sprite), self.band.h * 1.25)
        self.foe = foe
        self.dark = _shade(foe, 14 / 16.0)

    def draw(self, screen, f):
        W, b = self.W, self.band
        screen.blit(self.snap, (0, 0))
        lit = f >= 51
        if lit:
            _veil(screen, BLACK, 224)
        k = _clamp(f / 6.0)
        edge = W * (1 - k)
        off = int(self.X(30 * f)) % W
        rows = 10
        for r in range(rows):
            y0 = b.top + b.h * r // rows
            y1 = b.top + b.h * (r + 1) // rows
            tooth = self.X(16) * ((r % 4) / 3.0)   # (teeth 8 rows tall, 16 px deep)
            x = int(max(0, edge - tooth)) if k < 1 else 0
            if x < W:
                screen.blit(self.stripes, (x, y0), (W - off + x, y0 - b.top, W - x, y1 - y0))
        for i in range(4):   # (the emblem: four pieces pop in, one every 3 frames, each 2.0 -> 1.0)
            u = f - 16 - 3 * i
            if u >= 0:
                sc = 2.0 - _clamp(u / 6.0)
                cx, cy = self.X(72), self.Y(74)
                pts = []
                for j in range(8):
                    rr = (22 - i * 4) * self.s * sc * (1 if j % 2 == 0 else 0.45)
                    a = math.radians(j * 45 + i * 22.5)
                    pts.append((cx + rr * math.cos(a), cy - rr * math.sin(a)))
                pygame.draw.polygon(screen, (255, 255, 255) if i % 2 == 0 else (255, 232, 120), pts)
        if self.foe is not None and f >= 34:
            x = _quad(272, 214, -64, 4, f - 34)
            img = self.foe if lit else self.dark
            clip = screen.get_clip()
            screen.set_clip(b)
            screen.blit(img, img.get_rect(midbottom=(int(self.X(x)), b.bottom)))
            screen.set_clip(clip)
        if lit:
            _text(screen, self.c.name.upper() or "LEADER", int(self.Y(14)), (self.X(16), b.bottom + self.Y(4)))
        if 48 <= f < 54:
            _veil(screen, WHITE, 255 * (1 - abs(f - 51) / 3.0))
        if f >= 80:
            _veil(screen, WHITE, 255 * _clamp((f - 80) / 15.0))


class E4Vs(G4):
    """Platinum's (and HGSS's) Elite Four / Champion intro: you and the foe slide in from opposite sides as
    silhouettes, a white flash colours you both, you shake face to face, then fly apart into white. (The 3D backdrop
    behind isn't decoded: a two-tone panel stands in.)"""
    LEN = 72
    END = WHITE

    def setup4(self):
        h = self.Y(84)
        self.foe = _fit(_crop(self.c.foe_sprite), h)
        self.me = _fit(_player_img(self.game), h)
        self.foe_d, self.me_d = _shade(self.foe, 14 / 16.0), _shade(self.me, 14 / 16.0)

    def draw(self, screen, f):
        W, H = self.W, self.H
        screen.fill((16, 16, 40))
        pygame.draw.polygon(screen, (40, 72, 152), [(0, 0), (W * 0.62, 0), (W * 0.38, H), (0, H)])
        pygame.draw.polygon(screen, (152, 40, 56), [(W * 0.62, 0), (W, 0), (W, H), (W * 0.38, H)])
        lit = f >= 9
        px = _quad(-128, 56, 80, 6, f)
        fx = _quad(384, 200, -80, 6, f)
        py = fy = 92
        if 23 <= f < 55:
            j = 2 if int(f // 2) % 2 else -2
            px, fx = px + j, fx - j
        if f >= 55:
            k = _clamp((f - 55) / 16.0)
            px, py = px - 136 * k, py - 136 * k
            fx, fy = fx + 136 * k, fy + 136 * k
        for img, dark, x, y, sign in ((self.me, self.me_d, px, py, 1), (self.foe, self.foe_d, fx, fy, -1)):
            if img is not None:
                pic = img if lit else dark
                screen.blit(pic, pic.get_rect(center=(int(self.X(x)), int(self.Y(y)))))
        _text(screen, "VS", int(self.Y(14)), (self.X(128), self.Y(96)), colour=(255, 232, 96),   # (once, between them)
              shadow=(40, 24, 8), anchor="center")
        if lit and f < 55:
            _text(screen, self.c.name.upper(), int(self.Y(14)), (self.X(168), self.Y(150)))
        if 6 <= f < 15:
            _veil(screen, WHITE, 255 * (_clamp((f - 6) / 3.0) if f < 9 else 1 - _clamp((f - 9) / 6.0)))
        if f >= 63:
            _veil(screen, WHITE, 255 * _clamp((f - 63) / 8.0))


class Mythical(G4):
    """Platinum's 'mythical' intro (HGSS's ancient ones): sixteen hard camera cuts round you, each held a little less,
    with motion blur, then white. (The 3D angles aren't reproduced: each cut turns and zooms the field instead.)"""
    HOLDS = [4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1]
    ANGLES = [12, -18, 24, -8, 30, -26, 16, -34, 8, -20, 36, -12, 28, -40, 20, -6]
    ZOOMS = [1.25, 1.4, 1.15, 1.6, 1.3, 1.5, 1.2, 1.7, 1.35, 1.45, 1.25, 1.8, 1.4, 1.6, 1.3, 1.9]
    END = WHITE

    def setup4(self):
        self.starts = [sum(self.HOLDS[:i]) for i in range(len(self.HOLDS))]
        self.LEN = sum(self.HOLDS) + 10 + 1
        self.cuts = {}
        self.small = pygame.transform.scale(self.snap, (self.W // 2, self.H // 2))
        self.prev = None

    def _cut(self, i):
        if i not in self.cuts:
            img = pygame.transform.rotozoom(self.small, self.ANGLES[i], self.ZOOMS[i])
            out = pygame.Surface((self.W // 2, self.H // 2))
            out.blit(img, img.get_rect(center=(self.W // 4, self.H // 4)))
            self.cuts[i] = pygame.transform.scale(out, (self.W, self.H))
        return self.cuts[i]

    def draw(self, screen, f):
        total = sum(self.HOLDS)
        i = max(k for k, s in enumerate(self.starts) if s <= min(f, total - 0.01))
        screen.blit(self._cut(i), (0, 0))
        if self.prev is not None:
            self.prev.set_alpha(96)
            screen.blit(self.prev, (0, 0))
        self.prev = screen.copy()
        if f >= total:
            _veil(screen, WHITE, 255 * _clamp((f - total) / 10.0))


class Legendary(G4):
    """Platinum's legendary intro (HGSS: Ho-Oh, Lugia): the view widens slowly, then the camera lunges in, and a long
    white fade (60 frames), with motion blur."""
    LEN = 40 + 5 + 8 + 60 + 1
    END = WHITE

    def setup4(self):
        self.push = self.p.get("push", 2350) / 1000.0
        self.prev = None

    def draw(self, screen, f):
        if f < 40:
            z = 1 - 0.06 * f / 40.0
        elif f < 45:
            z = 0.94
        else:
            z = 0.94 + _quad(0, self.push, 0, 8, f - 45)
        screen.blit(self.cam(z), (0, 0))
        if self.prev is not None:
            self.prev.set_alpha(110)
            screen.blit(self.prev, (0, 0))
        self.prev = screen.copy()
        if f >= 53:
            _veil(screen, WHITE, 255 * _clamp((f - 53) / 60.0))


class HgGrid(G4):
    """HGSS wild intros: 48 black cells on an 8 x 6 grid. On land they close like shutters in a snake from two corners
    that meets in the middle (day from the top left, night from the top right); in a cave they grow from dots along
    the diagonals (day from the top left, night from the bottom right). Red's intro: the cells in a random order."""
    def setup4(self):
        mode = self.p.get("mode", "grass")
        night = bool(self.p.get("night"))
        self.grow = "x" if mode == "grass" else "xy"
        start = {}
        if mode == "grass":
            order = []
            for row in range(3):
                cols = list(range(8)) if (row % 2 == 0) != night else list(range(7, -1, -1))
                order += [row * 8 + c for c in cols]
            for k, cell in enumerate(order):
                start[cell] = k
                start[47 - cell] = k
        elif mode == "cave":
            cells = sorted(range(48), key=lambda n: (n % 8 + n // 8, n // 8))
            for rank, cell in enumerate(cells):
                start[47 - cell if night else cell] = rank // 2
        else:   # (Red: shuffled)
            cells = list(range(48))
            self.rng.shuffle(cells)
            for rank, cell in enumerate(cells):
                start[cell] = rank // 2
        self.start = start
        self.LEN = max(start.values()) + 4 + 1

    def cells(self, screen, f):
        cw, ch = self.W / 8.0, self.H / 6.0
        for cell, s in self.start.items():
            k = _clamp((f - s) / 4.0)
            if k <= 0:
                continue
            col, row = cell % 8, cell // 8
            cx, cy = (col + 0.5) * cw, (row + 0.5) * ch
            w = cw * k
            h = ch * (k if self.grow == "xy" else 1.0)
            screen.fill(BLACK, (int(cx - w / 2), int(cy - h / 2), int(math.ceil(w)) + 1, int(math.ceil(h)) + 1))

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        self.cells(screen, f)


class RedTiles(HgGrid):
    """Red (HGSS): the 48 cells in a random order, with a radial wipe from about 200 degrees and a box from the middle
    running at the same time (the exact order of those isn't decoded)."""
    def setup4(self):
        self.p["mode"] = "red"
        HgGrid.setup4(self)
        self.LEN = 29

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        self.cells(screen, f)
        k = _clamp(f / 28.0)
        _wedge(screen, self.W / 2, self.H / 2, 200, 200 - 360 * k)
        w, h = self.W * k, self.H * k
        screen.fill(BLACK, (int((self.W - w) / 2), int((self.H - h) / 2), int(w), int(h)))


class HgWater(G4):
    """HGSS wild, on the water: two layers of waves slide across over the field (one from rest, one at 8 px a frame)
    while they blend in, then black. (The ROM's wave picture isn't decoded: waves are drawn in code.)"""
    LEN = 31

    def setup4(self):
        W, H = self.W, self.H
        self.back = pygame.Surface((W * 2, H))
        self.back.fill((24, 56, 136) if not self.p.get("night") else (16, 32, 88))
        self.front = pygame.Surface((W * 2, H), pygame.SRCALPHA)
        for row in range(12):
            y0 = H * row / 12.0
            pts = [(x, y0 + math.sin(x / (W / 6.0) + row) * H / 40) for x in range(0, W * 2 + 20, 20)]
            pygame.draw.lines(self.back, (56, 104, 192), False, pts, max(2, int(self.Y(3))))
            pygame.draw.lines(self.front, (200, 232, 255, 200), False, [(x, y + H / 48) for x, y in pts], max(2, int(self.Y(2))))

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        a = _clamp(math.sin(_clamp(f / 15.0) * math.pi / 2))
        x3 = 320 * _clamp(f / 18.0) ** 2
        x1 = _quad(0, 320, 8, 30, f)
        self.back.set_alpha(int(255 * a))
        screen.blit(self.back, (-int(self.X(x3)) % self.W - self.W, 0))
        self.front.set_alpha(int(255 * a))
        screen.blit(self.front, (-int(self.X(x1)) % self.W - self.W, 0))
        if f >= 24:
            _veil(screen, BLACK, 255 * _clamp((f - 24) / 6.0))


class RocketAdmin(G4):
    """HGSS's Rocket executives and Giovanni: a name banner with their name printed, their portrait, a shake, a white
    flash, then white. (pokeheartgold hasn't decoded these motions: this follows its parts list, timings ours.)"""
    LEN = 62
    END = WHITE

    def setup4(self):
        self.band = pygame.Rect(0, int(self.Y(48)), self.W, int(self.Y(84)))
        foe = _fit(_crop(self.c.foe_sprite), self.band.h * 1.2)
        self.foe, self.dark = foe, _shade(foe, 14 / 16.0)

    def draw(self, screen, f):
        b = self.band
        shake = int(self.Y(4) * (1 if int(f) % 2 else -1) * (1 - _clamp((f - 20) / 12.0))) if 20 <= f < 32 else 0
        screen.blit(self.snap, (0, shake))
        lit = f >= 18
        if lit:
            _veil(screen, BLACK, 200)
        w = int(self.W * _clamp(f / 6.0))
        bb = b.move(0, shake)
        screen.fill((16, 16, 20), (0, bb.top, w, bb.h))
        screen.fill((200, 24, 24), (0, bb.top, w, int(self.Y(4))))
        screen.fill((200, 24, 24), (0, bb.bottom - int(self.Y(4)), w, int(self.Y(4))))
        if f >= 6:
            _blit_rot(screen, _emblem("rocket", self.Y(70)), (self.X(60), bb.centery), 0, 2.0 - _clamp((f - 6) / 6.0))
        if self.foe is not None and f >= 10:
            x = _quad(300, 196, -40, 6, f - 10)
            img = self.foe if lit else self.dark
            clip = screen.get_clip()
            screen.set_clip(bb)
            screen.blit(img, img.get_rect(midbottom=(int(self.X(x)), bb.bottom)))
            screen.set_clip(clip)
        if lit:
            _text(screen, self.c.name.upper(), int(self.Y(16)), (self.X(100), bb.centery), anchor="midleft")
        if 15 <= f < 21:
            _veil(screen, WHITE, 255 * (1 - abs(f - 18) / 3.0))
        if f >= 56:
            _veil(screen, WHITE, 255 * _clamp((f - 56) / 4.0))


class Kimono(G4):
    """HGSS's Kimono Girls: two patterned layers slide in from opposite sides and meet, then black. (The art and
    motion aren't decoded: a kimono pattern drawn in code.)"""
    LEN = 44

    def setup4(self):
        W, H = self.W, self.H
        self.pat = pygame.Surface((W, H // 2 + 1))
        self.pat.fill((168, 32, 72))
        r = int(self.Y(10))
        for gy in range(-1, int(H / 2 / (r * 3)) + 2):
            for gx in range(-1, int(W / (r * 3)) + 2):
                cx, cy = gx * r * 3 + (r * 1.5 if gy % 2 else 0), gy * r * 3
                for j in range(5):
                    a = math.radians(j * 72)
                    pygame.draw.circle(self.pat, (232, 192, 96), (int(cx + r * 0.6 * math.cos(a)), int(cy + r * 0.6 * math.sin(a))), max(2, r // 2))
                pygame.draw.circle(self.pat, (248, 232, 200), (int(cx), int(cy)), max(2, r // 3))

    def draw(self, screen, f):
        screen.blit(self.snap, (0, 0))
        k = _quad(0, 1, 0, 16, f)
        drift = int(self.X(2 * f))
        h = self.H // 2
        x = int(-self.W * (1 - k))
        screen.blit(self.pat, (x + drift % 8, 0))
        screen.blit(self.pat, (-x - drift % 8, h))
        if f >= 30:
            _veil(screen, BLACK, 255 * _clamp((f - 30) / 12.0))


# ---- Orre: Pokemon Orre 2.1.1's Essentials v21.1 transitions (512x384, timed in seconds) ---------------------------
class Orre(Effect):
    SRC = (512, 384)
    DURATION = 1.0

    def setup(self):
        self.LEN = int(math.ceil(self.DURATION * 60)) + 1
        self.small = 128 * self.s   # ball_small (128 px)
        self.large = 256 * self.s   # ball_large (256 px)
        self.setup_o()

    def setup_o(self):
        pass

    def draw(self, screen, f):
        self.tick(screen, min(self.DURATION, f / 60.0))

    def tick(self, screen, t):
        screen.blit(self.snap, (0, 0))

    def zoom_world(self, screen, z):
        _zoom_into(screen, self.snap, z)

    def strips(self, screen, h, amp, speed, spacing, t, alternate=False):
        a = amp * min(t / 0.1, 1.0)
        n = 384 // h
        _bands(screen, self.snap, n, dx=lambda i: (1 - (i % 2) * 2 if alternate else 1) * self.X(a) * math.sin(t * speed + i * spacing),
               wrap=False)


class OrSnake(Orre):
    """SnakeSquares (1.25 s): 8 x 6 black squares grow sideways in a snake from the top left and, mirrored, from the
    bottom right, meeting in the middle."""
    DURATION = 1.25

    def setup_o(self):
        gap = (self.DURATION - 0.2) * 2 / 47.0
        self.cells = []
        for j in range(6):
            for i in range(8):
                idx = j * 8 + i
                col = (i if j % 2 else 7 - i) if idx >= 24 else (i if j % 2 == 0 else 7 - i)
                self.cells.append((col, j, gap * (idx if idx < 24 else 47 - idx)))

    def tick(self, screen, t):
        screen.blit(self.snap, (0, 0))
        cw, ch = self.W / 8.0, self.H / 6.0
        for col, row, start in self.cells:
            if t >= start:
                w = cw * _clamp((t - start) / 0.2)
                screen.fill(BLACK, (int((col + 0.5) * cw - w / 2), int(row * ch), int(math.ceil(w)) + 1, int(math.ceil(ch)) + 1))


class OrDiagonal(Orre):
    """DiagonalBubble (1.25 s): the same squares grow from dots in a wave across from one corner (0 top left, 3 bottom
    right)."""
    DURATION = 1.25

    def setup_o(self):
        origin = self.p.get("origin", 0)
        self.cells = []
        for j in range(6):
            for i in range(8):
                dist = i + j * 7 / 5.0
                start = dist / 14.0 * (self.DURATION - 0.2)
                ci, cj = (i, j) if origin == 0 else (7 - i, 5 - j) if origin == 3 else (7 - i, j) if origin == 1 else (i, 5 - j)
                self.cells.append((ci, cj, start))

    def tick(self, screen, t):
        screen.blit(self.snap, (0, 0))
        cw, ch = self.W / 8.0, self.H / 6.0
        for col, row, start in self.cells:
            if t >= start:
                k = _clamp((t - start) / 0.2)
                w, h = cw * k, ch * k
                screen.fill(BLACK, (int((col + 0.5) * cw - w / 2), int((row + 0.5) * ch - h / 2), int(math.ceil(w)) + 1, int(math.ceil(h)) + 1))


class OrSplash(Orre):
    """RisingSplash (1.25 s): the field sways in 2 px rows, bubbles rise, a splash rises from halfway, and black comes
    up from 90% (the bubble and splash pictures are Essentials' own, in assets/transitions)."""
    DURATION = 1.25

    def setup_o(self):
        from src.vfx.transitions import image
        self.bub, self.spl = image(self.game, "water_1.png"), image(self.game, "water_2.png")
        if self.bub is not None:
            self.bub = pygame.transform.scale(self.bub, (int(self.X(640)), int(self.Y(640))))
        if self.spl is not None:
            self.spl = pygame.transform.scale(self.spl, (int(self.X(512)), int(self.Y(640))))

    def tick(self, screen, t):
        screen.fill(BLACK)
        self.strips(screen, 2, 6, math.pi * 10, math.pi / 10, t)
        if self.bub is not None:
            x = (self.W - self.bub.get_width()) / 2 + self.X(-32) * math.sin(t * math.pi * 2)
            screen.blit(self.bub, (int(x), int(self.H * (1 - t * 1.2))))
        if self.spl is not None and t >= self.DURATION * 0.5:
            k = (t - self.DURATION * 0.5) / (self.DURATION * 0.5)
            screen.blit(self.spl, (0, int(self.H * (1 - k * 2))))
        if t >= self.DURATION * 0.9:
            k = (t - self.DURATION * 0.9) / (self.DURATION * 0.1)
            y = int(self.H * (1 - k))
            screen.fill(BLACK, (0, y, self.W, self.H - y))


class OrTwoBall(Orre):
    """TwoBallPass (1.0 s): two balls roll across the other way, then the field zooms to 2x while black bars slide in
    from the sides and a third opens from the middle."""
    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.small
        if t <= 0.4:
            screen.blit(self.snap, (0, 0))
            k = t / 0.4
            for i in (0, 1):
                x0 = W + b / 2 if i == 0 else -b / 2
                x = x0 + (2 * i - 1) * (W + b) * k
                y = (H + (2 * i - 1) * b) / 2
                _blit_rot(screen, _ball(b), (x, y), -(2 * i - 1) * 720 * k)
            return
        k = (t - 0.4) / 0.6
        self.zoom_world(screen, 1 + k * k)
        screen.fill(BLACK, (int(W * (1 - k * k)), 0, W, H // 2))
        screen.fill(BLACK, (int(W * (k * k - 1)), H // 2, W, H - H // 2))
        h = H / 2 * 2 * k * k
        screen.fill(BLACK, (0, int(H / 2 - h / 2), W, int(h)))


class OrSpinSplit(Orre):
    """SpinBallSplit (1.0 s): a big ball spins in, then the field and the ball split into top and bottom halves that
    move apart, zooming to 2x, with black following them in."""
    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.large
        ball = _ball(b)
        if t < 0.5:
            screen.blit(self.snap, (0, 0))
            k = min(1.0, t / 0.4)
            _blit_rot(screen, ball, (W / 2, H / 2), 360 * (1 - k), k)
            return
        k = (t - 0.5) / 0.5
        z = 1 + k * k
        screen.fill(BLACK)
        for i in (0, 1):
            x = (0.5 + (i * 2 - 1) * k * k) * W
            half = self.snap.subsurface((0, i * H // 2, W, H // 2))
            img = pygame.transform.scale(half, (int(W * z), int(H / 2 * z)))
            r = img.get_rect(midbottom=(int(x), H // 2)) if i == 0 else img.get_rect(midtop=(int(x), H // 2))
            screen.blit(img, r)
            bh = ball.subsurface((0, i * ball.get_height() // 2, ball.get_width(), ball.get_height() // 2))
            br = bh.get_rect(midbottom=(int(x), H // 2)) if i == 0 else bh.get_rect(midtop=(int(x), H // 2))
            screen.blit(bh, br)
            edge = int(x + (1 - i * 2) * W / 2)
            if i == 0:
                screen.fill(BLACK, (edge, 0, W, H // 2))
            else:
                screen.fill(BLACK, (0, H // 2, max(0, edge), H - H // 2))


class OrThreeBallDown(Orre):
    """ThreeBallDown (2.0 s): three balls drop spinning; then black squares fill in a set order from the bottom row
    up while the field zooms to 2x."""
    DURATION = 2.0
    ORDER = [0, 4, 1, 6, 7, 2, 5, 3]
    OFFS = [400, 0, 100]

    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.small
        if t < 0.4:
            screen.blit(self.snap, (0, 0))
            k = t / 0.4
            for i in range(3):
                y = -128 - self.OFFS[i] + (384 + max(self.OFFS) + 256) * k
                _blit_rot(screen, _ball(b), (W / 2 + self.X((i - 1) * 160), self.Y(y)), 1.5 * 360 * k * (1 if i == 2 else -1))
            return
        k = (t - 0.4) / 1.6
        self.zoom_world(screen, 1 + k * k)
        cw, ch = W / 8.0, H / 6.0
        for j in range(6):
            for i in range(8):
                start = 0.4 + 1.6 * ((5 - j) * 8 + self.ORDER[i]) / 48.0
                if t >= start:
                    screen.fill(BLACK, (int(i * cw), int(j * ch), int(math.ceil(cw)) + 1, int(math.ceil(ch)) + 1))


class OrBallDown(Orre):
    """BallDown (0.9 s): one ball drops, zooming to 3x and spinning; then black with a curved edge comes down while
    the field zooms to 2x."""
    DURATION = 0.9

    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.small
        if t <= 0.63:
            screen.blit(self.snap, (0, 0))
            k = t / 0.63
            _blit_rot(screen, _ball(b), (W / 2, self.Y(-64 + (384 + 384) * k * k)), -540 * k, 3 * k * k)
            return
        k = (t - 0.63) / 0.27
        self.zoom_world(screen, 1 + k * k)
        y = self.Y(-96 + (384 + 96) * k)
        screen.fill(BLACK, (0, 0, W, int(y)))
        pygame.draw.ellipse(screen, BLACK, (-W * 0.1, int(y - self.Y(96)), W * 1.2, int(self.Y(192))))


class OrWavyThreeBall(Orre):
    """WavyThreeBallUp (1.1 s): the field waves in 4 px rows; three balls rise spinning, trailing black."""
    DURATION = 1.1
    OFFS = [1.5, 3.25, 2.5]

    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.small
        screen.fill(BLACK)
        self.strips(screen, 4, 24, math.pi * 4, math.pi / 24, t, alternate=True)
        if t >= self.DURATION * 0.4:
            k = (t - self.DURATION * 0.4) / (self.DURATION * 0.6)
            for i in range(3):
                y = self.OFFS[i] * H - H * 3.5 * k
                x = (2 * i + 1) * W / 6.0
                top = max(0, int(y))
                screen.fill(BLACK, (int((i - 1) * W * 2 / 3.0), top, W, H - top))
                _blit_rot(screen, _ball(b), (x, y), [-1, -1, 1][i] * 720 * k)
        else:
            for i in range(3):
                _blit_rot(screen, _ball(b), ((2 * i + 1) * W / 6.0, self.OFFS[i] * H))


class OrWavySpin(Orre):
    """WavySpinBall (1.0 s): the field waves; a big ball fades in spinning; then black spreads from the middle."""
    def tick(self, screen, t):
        W, H = self.W, self.H
        screen.fill(BLACK)
        self.strips(screen, 4, 24, math.pi * 4, math.pi / 24, t, alternate=True)
        if t <= 0.4:
            _blit_rot(screen, _ball(self.large), (W / 2, H / 2), -360 * t / 0.4, 1.0, 255 * t / 0.4)
        else:
            _blit_rot(screen, _ball(self.large), (W / 2, H / 2))
        if t > 0.5:
            k = (t - 0.5) / 0.5
            w, h = W * k, H * k
            screen.fill(BLACK, (int(W / 2 - w / 2), int(H / 2 - h / 2), int(w) + 1, int(h) + 1))


class OrFourBall(Orre):
    """FourBallBurst (0.9 s; any double trainer battle): four balls fly out from the middle to the edges, then four
    black wedges grow from the middle to fill the screen."""
    DURATION = 0.9

    def tick(self, screen, t):
        W, H, b = self.W, self.H, self.small
        screen.blit(self.snap, (0, 0))
        if t <= 0.36:
            k = t / 0.36
            tx, ty = (W + b * 2) / 2, (H + b * 2) / 2
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                _blit_rot(screen, _ball(b), (W / 2 + dx * tx * k, H / 2 + dy * ty * k))
            return
        k = (t - 0.36) / 0.54
        cx, cy = W / 2, H / 2
        hw, hh = self.X(192) * k, self.Y(256) * k
        pygame.draw.polygon(screen, BLACK, [(cx, cy), (cx - hw, H), (cx + hw, H)])
        pygame.draw.polygon(screen, BLACK, [(cx, cy), (cx - hw, 0), (cx + hw, 0)])
        pygame.draw.polygon(screen, BLACK, [(cx, cy), (0, cy - hh), (0, cy + hh)])
        pygame.draw.polygon(screen, BLACK, [(cx, cy), (W, cy - hh), (W, cy + hh)])


ORRE_BARS = {"miror": (168, 72, 200), "evice": (200, 40, 40), "vesper": (72, 120, 216), "vander": (232, 136, 40),
             "battlus": (232, 136, 40)}


def _vs_logo(game, h):
    from src.vfx.transitions import image
    vs = image(game, "vs.png")
    return _fit(vs, h) if vs is not None else None


class OrVsTrainer(Orre):
    """VSTrainer (4.0 s; Miror B., Evice, Vesper, the Mt. Battle master): a bar wipes in at y 80 and streams left at
    1800 px/s, VS lands, the foe slides in as a silhouette, a white flash puts them in colour with their name, then
    white and black. (The bar is drawn in code; the fan game's bar and portrait art are its own.)"""
    DURATION = 4.0
    MASK = [8, 7, 6, 5, 4, 3, 2, 1, 0, 1, 2, 3, 4, 5, 6, 7]

    def setup_o(self):
        tint = next((v for k, v in ORRE_BARS.items() if k in self.c.name.lower()), (200, 200, 200))
        bw, bh = int(self.X(512)), int(self.Y(128))
        self.bar = pygame.Surface((bw, bh))
        self.bar.fill((40, 40, 40))
        rng = random.Random(3)
        for _ in range(40):
            y = rng.randrange(0, bh)
            x = rng.randrange(0, bw)
            ln = rng.randrange(bw // 12, bw // 3)
            pygame.draw.line(self.bar, tint if rng.random() < 0.5 else (248, 248, 248), (x, y), (x + ln, y), max(1, int(self.Y(rng.choice((1, 2, 3))))))
        self.foe = _fit(_crop(self.c.foe_sprite), bh)
        self.dark = _shade(self.foe, 1.0)
        self.vs = _vs_logo(self.game, self.Y(110))

    def tick(self, screen, t):
        W, H = self.W, self.H
        screen.blit(self.snap, (0, 0))
        lit = t >= 1.9 + 0.125
        if lit:
            _veil(screen, BLACK, 224)
        by = int(self.Y(80))
        bw = self.bar.get_width()
        x0 = -int(self.X(t * 1800)) % bw
        for k in range(-1, W // bw + 2):
            screen.blit(self.bar, (x0 + k * bw, by))
        if t < 0.2:   # (the bar comes in from the right, its edge notched by BAR_MASK)
            start = W * (1 - t / 0.2)
            rows = self.bar.get_height() // max(1, int(self.Y(2)))
            for i in range(rows):
                y = by + i * int(self.Y(2))
                x = int(start - self.X(self.MASK[i % 16] * 4))
                screen.blit(self.snap, (0, y), (0, y, max(0, x), int(self.Y(2))))
        if self.vs is not None and t >= 0.7:
            jx, jy = [(0, 0), (4, 0), (0, -4)][int(t * 30) % 3]
            if t < 1.1:
                for lag in (0.0, 0.1):
                    sc = 2.0 - 0.8 * _clamp((t - 0.7 - lag) / 0.2)
                    if t >= 0.7 + lag and sc > 1.2:
                        _blit_rot(screen, self.vs, (self.X(144), by + self.Y(64)), 0, sc, 160)
            _blit_rot(screen, self.vs, (self.X(144 + jx), by + self.Y(64 + jy)))
        if self.foe is not None and t >= 1.25:
            fw = self.foe.get_width()
            if t < 1.4:
                start = W + fw / 2
                x = start + (self.X(384) - start) * (t - 1.25) / 0.15
            else:
                x = self.X(428)
            img = self.foe if lit else self.dark
            screen.blit(img, img.get_rect(midbottom=(int(x), by + self.bar.get_height() - int(self.Y(12)))))
        if lit and t < 3.0:
            _text(screen, self.c.name, int(self.Y(26)), (self.X(244), by + self.Y(6)))
        if 1.9 <= t < 2.15:
            p = (t - 1.9) / 0.25
            _veil(screen, WHITE, min(255, 320 * 2 * (p if p < 0.5 else 1 - p)))
        if t >= 3.8:
            screen.fill(BLACK)
            _veil(screen, WHITE, 255 * (1 - (t - 3.8) / 0.2))
        elif t >= 3.0:
            _veil(screen, WHITE, 255 * _clamp((t - 3.0) / 0.5))


class OrVsE4(Orre):
    """VSEliteFour (3.5 s; the Champion card, with Wes): your bar and the foe's slide in from opposite sides with you
    both as silhouettes, VS shudders in the middle, a white flash colours you both, then you slide off into white."""
    DURATION = 3.5

    def setup_o(self):
        bw, bh = int(self.X(384)), int(self.Y(192))
        self.pbar, self.fbar = pygame.Surface((bw, bh)), pygame.Surface((bw, bh))
        for bar, col in ((self.pbar, (56, 96, 200)), (self.fbar, (200, 56, 64))):
            bar.fill((32, 32, 40))
            for i in range(-bh, bw, int(self.X(24))):
                pygame.draw.polygon(bar, col, [(i, bh), (i + self.X(10), bh), (i + self.X(10) + bh, 0), (i + bh, 0)])
        h = self.Y(128)
        self.me, self.foe = _fit(_player_img(self.game), h), _fit(_crop(self.c.foe_sprite), h)
        self.me_d, self.foe_d = _shade(self.me, 1.0), _shade(self.foe, 1.0)
        self.vs = _vs_logo(self.game, self.Y(110))

    def tick(self, screen, t):
        W, H = self.W, self.H
        screen.blit(self.snap, (0, 0))
        if t >= 0.125:
            _veil(screen, BLACK, 192)
        px, fx = -48.0, 512 + 48 - 384.0
        py, fy = 64.0, 384 - 192 - 64.0
        if t <= 0.5:
            px, fx = px - 384, fx + 384
        elif t <= 0.7:
            k = math.sqrt((t - 0.5) / 0.2)
            px = -432 + (-48 + 20 + 432) * k
            fx = 560 + (176 - 20 - 560) * k
        if t >= 2.7:
            k = _clamp((t - 2.7) / 0.3)
            px, py = px - 256 * k, py - 256 * k
            fx, fy = fx + 256 * k, fy + 256 * k
        lit = t >= 1.7 + 0.33 * 0.35
        screen.blit(self.pbar, (int(self.X(px)), int(self.Y(py))))
        screen.blit(self.fbar, (int(self.X(fx)), int(self.Y(fy))))
        for img, dark, x, y in ((self.me, self.me_d, px + 160, py + 192 - 8), (self.foe, self.foe_d, fx + 224, fy + 128 - 8)):
            if img is not None:
                pic = img if lit else dark
                screen.blit(pic, pic.get_rect(midbottom=(int(self.X(x)), int(self.Y(y)))))
        if lit and t < 2.7:
            _text(screen, self.c.name, int(self.Y(26)), (self.X(fx + 160 - 120), self.Y(fy + 86 + 40)))
        if self.vs is not None and t >= 0.6:
            jx, jy = [(0, 0), (4, 0), (0, -4)][int(t * 30) % 3]
            sc = 2.0 - 1.0 * _clamp((t - 0.6) / 0.4)
            _blit_rot(screen, self.vs, (W / 2 + self.X(jx), H / 2 + self.Y(jy)), 0, sc)
        if t < 0.25:
            p = t / 0.25
            _veil(screen, WHITE, min(255, 320 * 2 * (p if p < 0.5 else 1 - p)))
        if 1.7 <= t < 2.05:
            p = (t - 1.7) / 0.35
            _veil(screen, WHITE, min(255, 320 * 3 * p if p < 0.33 else 320 * 3 * (1 - p) / 2))
        if t >= 3.3:
            screen.fill(BLACK)
            _veil(screen, WHITE, 255 * (1 - (t - 3.3) / 0.2))
        elif t >= 2.7:
            _veil(screen, WHITE, 255 * _clamp((t - 2.7) / 0.3))


EFFECTS = {
    # FireRed/LeafGreen and Emerald
    "blur": Blur, "swirl": Swirl, "shuffle": Shuffle, "ripple": Ripple, "wave": Wave, "slice": Slice,
    "white_bars": WhiteBars, "grid": Grid, "angled": Angled, "clockwise": Clockwise, "balls_trail": BallsTrail,
    "big_ball": BigBall, "mugshot": Mugshot, "legend_art": LegendArt, "rayquaza": Rayquaza,
    # Platinum (and HGSS's shared ones)
    "pt_grass": PtGrass, "pt_water": PtWater, "pt_cave": PtCave, "tr_grass": TrGrass, "tr_water": TrWater,
    "tr_cave": TrCave, "ds_double": DsDouble, "logo_rain": LogoRain, "galactic_boss": GalacticBoss,
    "leader_banner": LeaderBanner, "e4_vs": E4Vs, "mythical": Mythical, "legendary": Legendary,
    # HeartGold/SoulSilver
    "hg_grass": HgGrid, "hg_cave": HgGrid, "hg_water": HgWater, "rocket_admin": RocketAdmin, "kimono": Kimono,
    "red_tiles": RedTiles,
    # Pokemon Orre 2.1.1 (Essentials v21.1)
    "or_snake": OrSnake, "or_diagonal": OrDiagonal, "or_splash": OrSplash, "or_two_ball": OrTwoBall,
    "or_spin_split": OrSpinSplit, "or_three_ball_down": OrThreeBallDown, "or_ball_down": OrBallDown,
    "or_wavy_three_ball": OrWavyThreeBall, "or_wavy_spin": OrWavySpin, "or_four_ball": OrFourBall,
    "or_vs_trainer": OrVsTrainer, "or_vs_e4": OrVsE4,
}
# (the HGSS grids share one class: which one, from the effect's name)
_GRID_MODES = {"hg_grass": "grass", "hg_cave": "cave"}
# (effects that start during the flash, frames from the flash's start: Platinum's water waves come in under it)
_STARTS_AT = {"pt_water": 10, "tr_water": 12}
FLASH_FRAMES = {"gen3": 16, "ds": 8, "orre": 24}   # one pulse: FRLG/Emerald grey 8 in + 8 out; DS 4 + 4; Orre 0.2 s + 0.2 s
HOLD = 4   # black frames before the battle (Orre waits 0.1 s: its own HOLD below)


class Intro:
    """A Plan played: the game's flash(es), then its effect, then a moment of the colour it ends on. t is the
    battle intro's own frame count at the game's FPS; everything inside runs on the source's 60 fps frames."""
    def __init__(self, game, snapshot, plan):
        self.plan = plan
        params = dict(plan.params)
        if plan.effect in _GRID_MODES:
            params.setdefault("mode", _GRID_MODES[plan.effect])
        self.fx = EFFECTS[plan.effect](game, snapshot, plan.ctx, **params)
        kind, colour, count = (plan.flash[0], plan.flash[1], plan.flash[2]) if plan.flash and len(plan.flash) == 3 \
            else (plan.flash[0], (90, 90, 90), plan.flash[1]) if plan.flash else (None, None, 0)
        self.flash_kind, self.flash_colour, self.flash_count = kind, colour, count
        self.flash_len = FLASH_FRAMES.get(kind, 0) * count
        self.start = _STARTS_AT.get(plan.effect, self.flash_len)
        self.hold = 6 if plan.game_key == "orre" else HOLD
        self.total = max(self.flash_len, self.start + self.fx.LEN) + self.hold
        self.length = int(math.ceil(self.total * FPS / 60.0)) + 1

    def frame60(self, t):
        return t * 60.0 / FPS

    def draw(self, screen, t):
        f = self.frame60(t)
        fx = self.fx
        if f < self.start:
            screen.blit(fx.snap, (0, 0))
        elif f < self.start + fx.LEN:
            fx.draw(screen, f - self.start)
        else:
            screen.fill(fx.END)
        if f < self.flash_len:
            per = FLASH_FRAMES[self.flash_kind]
            p = f % per
            _veil(screen, self.flash_colour, 255 * (1 - abs(per / 2.0 - p) / (per / 2.0)))
