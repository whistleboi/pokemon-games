"""The MENU and its screens as each walked region's own game opens and closes them (Jordan 11-24, region/systems, step 3).

The region picks the game as for the battle intros and the doors (canon_intros.REGION_GAME): Kanto, Sevii and Orange
FireRed/LeafGreen, Hoenn Emerald, Johto HeartGold/SoulSilver, Sinnoh Platinum (Unova copies it), Orre Pokemon Orre 2.1.1
(Essentials v21.1). The menu regions keep today's quick crossfade between screens.

Numbers from kanto_handoff/transitions_research: GEN3_FRLG_EMERALD.md 0 + 4.1-4.2, GEN4_HGSS_PLATINUM.md 4,
GEN5_B2W2_AND_ORRE.md B4 (UI_PauseMenu.rb, Fades_pbFadeOutIn.rb). 60 fps frames, played at the same real time here.

- The MENU (the start menu) opens and closes at once in all of them: FireRed/Emerald's window is drawn in one go and
  erased at once, Platinum's and HGSS's too, Orre's command window just appears.
- Into a screen (Pokemon, Bag, Pokedex, Badges/Trainer Card, Options, Journal, PC, Map...), from the MENU or straight from
  the map: the menu fades to black, the screen fades in; out again: the screen fades to black, the menu (or the map)
  fades in. FireRed: ~17 frames (delay 0), its party ~9 (delay -2) and its Bag's black shutter (opening upward over the
  Bag, closing downward on the way out with the -2 fade); its Pokedex comes in from white. Emerald: ~17 everywhere.
  Platinum and HGSS: 6 frames, both screens (one here); HGSS's Pokegear apps (Map, Phone, Radio: the bottom screen's
  apps) swap with its 2-frame fade. Orre: Essentials' pbFadeOutIn, 0.4 s out and 0.4 s in.
- Save: no fade in any of them (the save box is drawn over the field): the save screen comes at once.

Played by area_changes' Wipe layer (Game._frame draws it): the change happens at once under it, the old screen's
fade-out holds the new one still, then the new one shows through."""
from src.vfx import area_changes as ac

MENU = ("HomeMenuState",)
SCREENS = {   # (the screen's kind, for the per-game numbers)
    "PokemonPartyMenuState": "party", "BagState": "bag", "PokedexState": "dex", "BadgeCaseState": "card",
    "OptionsState": "options", "JournalState": "journal", "PCState": "pc", "RegionMapState": "map",
    "PokeNavState": "nav", "PhoneState": "gear", "RadioState": "gear", "StatsState": "stats",
    "LoadState": "load", "SaveState": "save",
}
GEAR = ("map", "gear")   # (HGSS's Pokegear: its Map, Phone and Radio)
BLACK, WHITE = ac.BLACK, ac.WHITE


def role(state):
    """"map", "menu", "screen" (one the MENU opens) or None (anything else: a battle, a scene, a shop...)."""
    if state is None:
        return None
    name = type(state).__name__
    if name in MENU:
        return "menu"
    if name in SCREENS:
        return "screen"
    return "map" if ac.on_map(state) else None


def kind(state):
    return SCREENS.get(type(state).__name__, "screen")


def _f(n, c=BLACK):
    return ("fade", n, {"to": c})


def _i(n, c=BLACK):
    return ("fade_in", n, {"from": c})


def plan(key, way, what):
    """way: "open" (menu or map -> a screen) or "close" (a screen -> the menu or the map); what: the screen's kind.
    (out segments, in segments), or "cut" (at once: no fade)."""
    if what == "save":
        return "cut"
    if key == "frlg":
        if what == "party":
            return ([_f(17)], [_i(9)]) if way == "open" else ([_f(9)], [_i(17)])
        if what == "bag":   # (the shutter: 160 px at 16 a frame = 10 frames)
            return ([_f(17)], [("shutter_up", 17, {"from": BLACK, "fade": 17, "shut": 10})]) if way == "open" else \
                ([("shutter_down", 10, {"to": BLACK, "fade": 9, "shut": 10})], [_i(17)])
        if what == "dex" and way == "open":   # (the Kanto dex's own screens fade through white)
            return [_f(17)], [_i(17, WHITE)]
        return [_f(17)], [_i(17)]
    if key == "emerald":
        return [_f(17)], [_i(17)]
    if key in ("hgss", "platinum"):
        if key == "hgss" and what in GEAR:
            return [_f(2)], [_i(2)]
        return [_f(6)], [_i(6)]
    if key == "orre":
        return [_f(24)], [_i(24)]
    return None


def decide(game, old, new):
    """What Game.change_state does going from old to new: None (today's crossfade), "cut" (no fade at all) or a plan
    (out, in) for the wipe."""
    if getattr(game, "FADE_FRAMES", 6) == 0 or getattr(game, "area_wipe", None) is not None:
        return None
    a, b = role(old), role(new)
    if (a, b) not in (("map", "menu"), ("menu", "map"), ("menu", "screen"), ("map", "screen"), ("screen", "menu"), ("screen", "map")):
        return None   # (a screen to another (the party's summary...), a battle, a scene: as today)
    key = ac.here_key(game)
    if not key:
        return None
    if {a, b} == {"map", "menu"}:
        return "cut"
    if b == "screen":
        return plan(key, "open", kind(new))
    return plan(key, "close", kind(old))


def start(game, how, snap, old, new):
    """Play the wipe for a plan decide() gave (snap: the last frame shown)."""
    if not isinstance(how, tuple) or snap is None:
        return None
    out, into = how
    w = ac.Wipe(game, snap, out, into, "menu", ac.here_key(game))
    game.area_wipe = ac.ACTIVE = w
    game._fade_left = 0
    game.__dict__.setdefault("menu_wipes_log", []).append((ac.here_key(game), type(old).__name__, type(new).__name__, how))
    return w
