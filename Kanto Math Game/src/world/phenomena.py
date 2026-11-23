"""Black 2 / White 2's phenomena (11-20, Jordan: "Add phenomena"): rustling grass and rippling water.

Now and then as you walk a place whose "wild_tables" have them (src/world/wild_tables.py), a patch of tall grass near you
rustles, or a spot of water ripples. Step into the rustling grass (or surf onto the ripple) and its own Pokemon jumps out:
the "rustle" / "ripple" slots (Audino, Dunsparce, Emolga...). Fish into the ripple and the "fish_ripple" slots bite. Walk
well away, or change floor, and it stops. The grass shakes in Platinum's own frames (the Poke Radar's), the water rings.
Dust clouds (caves) and flying shadows (bridges) come with their places, from the same tables."""
import random

import pygame

START_AFTER = 20      # steps on the map before the first one can start (and after one ends)
CHANCE = 1 / 18       # each step after that
NEAR, FAR = 3, 7      # how far from you it starts (tiles), and stops beyond FAR + 4


def _state(ds):
    st = getattr(ds, "_phenom", None)
    if st is None:
        st = ds._phenom = {"spot": None, "kind": None, "floor": None, "quiet": 0, "burst": None}
    return st


def _kinds(ds):
    from src.world import wild_tables as wt
    return [k for k in ("rustle", "ripple") if wt.has(ds.area_data, k)]


def active(ds):
    st = getattr(ds, "_phenom", None)
    return (st["spot"], st["kind"]) if st and st.get("spot") and st.get("floor") == ds.run.index else (None, None)


def is_ripple(ds, tile):
    spot, kind = active(ds)
    return kind == "ripple" and tile is not None and tuple(tile) == spot


def _start(ds, rng):
    from src.dungeon import core
    f = ds.run.floor
    px, py = ds.run.player
    kinds = _kinds(ds)
    rng.shuffle(kinds)
    dark = ds._dark_tiles() if hasattr(ds, "_dark_tiles") else set()
    for kind in kinds:
        want = (core.GRASS,) if kind == "rustle" else (core.WATER, core.SURF)
        spots = [(x, y) for y in range(py - FAR, py + FAR + 1) for x in range(px - FAR, px + FAR + 1)
                 if NEAR <= abs(x - px) + abs(y - py) <= FAR and f.inside(x, y) and f.tile(x, y) in want
                 and (x, y) not in dark and not f.occupied(x, y)]
        if spots:
            return rng.choice(spots), kind
    return None, None


def on_step(ds, rng=None):
    """After you step: into the rustling grass or onto the ripple, its Pokemon jumps out (True). Else it may start or stop."""
    if getattr(ds, "mode", "") != "MAP" or not _kinds(ds):
        return False
    rng = rng or random
    st = _state(ds)
    t = tuple(ds.run.player)
    if st["spot"] and st["floor"] == ds.run.index and t == st["spot"]:
        kind = st["kind"]
        st.update(spot=None, kind=None, quiet=0, burst=(t, pygame.time.get_ticks()))
        return _jump_out(ds, t, kind)
    if st["spot"] and (st["floor"] != ds.run.index or abs(st["spot"][0] - t[0]) + abs(st["spot"][1] - t[1]) > FAR + 4):
        st.update(spot=None, kind=None, quiet=0)
    if st["spot"] is None:
        st["quiet"] += 1
        if st["quiet"] >= START_AFTER and rng.random() < CHANCE:
            spot, kind = _start(ds, rng)
            if spot:
                st.update(spot=spot, kind=kind, floor=ds.run.index)
    return False


def _jump_out(ds, t, kind):
    from src.dungeon.core import Mover
    ds._phenom_kind = kind
    try:
        p = ds._from_wild_tables(random.Random())
    finally:
        ds._phenom_kind = None
    if p is None:
        return False
    m = Mover("wild", t[0], t[1], p)
    ds.run.floor.movers.append(m)
    from src.world import feats as _feats
    _feats.note(ds.game.story_manager, "phenomena")   # (a Feat: Pokemon met in rustling grass, rippling water, dust; Unova)
    ds._meet_wild(m)
    return True


def leave(ds):
    if hasattr(ds, "_phenom"):
        ds._phenom = None


def draw(ds, screen, at):
    """The rustling patch (Platinum's own shaking-grass frames) or the rings on the water; the leaves bursting up."""
    st = getattr(ds, "_phenom", None)
    if not st:
        return
    ms = pygame.time.get_ticks()
    spot, kind = active(ds)
    if spot:
        r = at(*spot)
        if kind == "rustle":
            from src.world import poke_radar
            fr = poke_radar._frames("shake", (r.w, r.h))
            if fr:
                screen.blit(fr[(ms // 110) % len(fr)], r)
        else:
            for k in range(2):   # (two white rings, growing outward and fading, one after the other)
                ph = ((ms / 900.0) + k * 0.5) % 1.0
                w, h = int(r.w * (0.35 + 0.65 * ph)), int(r.h * (0.18 + 0.32 * ph))
                ring = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (255, 255, 255, int(220 * (1 - ph))), ring.get_rect(), 2)
                screen.blit(ring, ring.get_rect(center=r.center))
    burst = st.get("burst")
    if burst and ms - burst[1] < 560:
        from src.world import poke_radar
        r = at(*burst[0])
        fr = poke_radar._frames("burst", (r.w * 2, r.h * 2))
        if fr:
            img = fr[min(len(fr) - 1, (ms - burst[1]) // 140)]
            screen.blit(img, img.get_rect(center=r.center))
