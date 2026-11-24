"""Ambush spots (Jordan 11-24): the old games' hidden wild Pokemon, on our walked maps. Now and then a patch of tall grass
shakes, a puff of dust rises from a cave floor, or rings spread on the water (only while you surf). Nothing shows on the
spot; walk into it before it fades and a wild Pokemon jumps out: a normal wild meeting (map or classic battle, as the
Options say; the math, the damage, catching), from the area's own grass / cave / water Pokemon.

One spot at a time (two on a very big map), 3-5 seconds each, the next 5-10 seconds later, 3-8 tiles from you and never
beside the last one. The clock stops while you battle, read or use a menu (only the map in MAP mode counts).
Each region in its own generation's art: Gen 3 (Kanto, Sevii, Hoenn, Orange, Orre) FireRed / Emerald's own field effects
(pret pokeemerald: tall_grass, ground_impact_dust, ripple -> gen3_*.png); Gen 4 (Johto, Sinnoh) and Unova Platinum's
(the Poke Radar's shaking grass, ripple and hero_kemu -> radar_rustle_*, gen4_*.png; kanto_handoff/sinnoh_map_tools/
ambush_pics.py). Unova's own Black 2 phenomena keep running beside this (src/world/phenomena.py): only one shows at a time.
State on the map screen: ds._ambush."""
import os
import random

import pygame

LIFE = (3000, 5000)     # ms a spot lasts
GAP = (5000, 10000)     # ms before the next one
FIRST = (3000, 7000)    # ms after arriving before the first
NEAR, FAR = 3, 8        # tiles from you
APART = 5               # tiles from the last spot
BIG = 70 * 70           # a map this big may have two at once
FADE = 500              # ms of fading out at the end
GEN3 = {"KANTO", "SEVII", "HOENN", "ORANGE", "ORRE"}


def _state(ds):
    st = getattr(ds, "_ambush", None)
    if st is None:
        now = pygame.time.get_ticks()
        st = ds._ambush = {"spots": [], "next": now + random.randint(*FIRST), "last": None, "floor": None, "seen": now,
                           "burst": None}
    return st


def _region(ds):
    return ds.game.story_manager.area_region(getattr(ds, "area_key", ""))   # (no region field: Kanto)


def _cave(ds):
    """A cave floor: its walked map's art theme (this floor's own first), else the area's battle type."""
    rec = getattr(ds, "recipe", None) or {}
    lay = rec.get("layout") or []
    i = ds.run.index if hasattr(ds, "run") else 0
    own = lay[i].get("theme") if 0 <= i < len(lay) and isinstance(lay[i], dict) else None
    theme = own or (rec.get("art") or {}).get("theme")
    if theme:
        return theme == "cave"
    return str((ds.area_data or {}).get("battle_type") or "").lower() == "cave"


def _allowed(ds):
    """Wild Pokemon here at all: a walked map's floor with a pool, not a room, not the Bug-Catching Contest."""
    if not hasattr(ds, "run") or getattr(ds, "contest", None):
        return False
    if (getattr(ds, "recipe", None) or {}).get("wild") == [0, 0] or ds._indoors(ds.run.index):
        return False
    a = ds.area_data or {}
    return bool(a.get("wild_pool_percentages") or a.get("zone_pools") or a.get("surf_pool_percentages")
                or getattr(ds, "_floor_tables", lambda: None)())


def _kind_for(ds):
    """What can stir near you now: ripples while you surf, else dust in a cave, else shaking grass."""
    from src.dungeon import core
    f = ds.run.floor
    under = f.tile(*ds.run.player)
    if under in (core.SURF, core.WATER):
        return "ripple" if (ds.area_data or {}).get("surf_pool_percentages") or getattr(ds, "_floor_tables", lambda: None)() else None
    return "dust" if _cave(ds) else "grass"


def _pick_spot(ds, kind, st, rng):
    from src.dungeon import core
    f = ds.run.floor
    px, py = ds.run.player
    want = {"grass": (core.GRASS,), "dust": (core.FLOOR, core.GRASS), "ripple": (core.SURF, core.WATER)}[kind]
    taken = [s["at"] for s in st["spots"]] + ([st["last"]] if st["last"] else [])
    dark = ds._dark_tiles() if hasattr(ds, "_dark_tiles") else set()
    out = [(x, y) for y in range(py - FAR, py + FAR + 1) for x in range(px - FAR, px + FAR + 1)
           if NEAR <= abs(x - px) + abs(y - py) <= FAR and f.inside(x, y) and f.tile(x, y) in want
           and (x, y) not in f.exits and (x, y) not in dark and not f.occupied(x, y)
           and all(abs(x - tx) + abs(y - ty) >= APART for tx, ty in taken)]
    return rng.choice(out) if out else None


def tick(ds, rng=None):
    """Every frame on the map: spots fade, new ones start. Paused (its clock pushed on) while anything else is up."""
    if not hasattr(ds, "run"):
        return
    rng = rng or random
    st = _state(ds)
    now = pygame.time.get_ticks()
    away = now - st["seen"]
    st["seen"] = now
    if getattr(ds, "mode", "") != "MAP" or (getattr(ds, "dialogue_box", None) and ds.dialogue_box.visible):
        return
    if away > 250:   # (a battle, a menu, a talk: none of that time counts)
        st["next"] += away
        for s in st["spots"]:
            s["until"] += away
    if st["floor"] != ds.run.index:
        st.update(spots=[], last=None, floor=ds.run.index)
    st["spots"] = [s for s in st["spots"] if s["until"] > now]
    f = ds.run.floor
    most = 2 if f.w * f.h >= BIG else 1
    if now < st["next"] or len(st["spots"]) >= most or not _allowed(ds):
        return
    from src.world import phenomena as _phen
    if _phen.active(ds)[0]:   # (Black 2's own phenomenon is showing: one at a time)
        st["next"] = now + rng.randint(*GAP)
        return
    kind = _kind_for(ds)
    spot = _pick_spot(ds, kind, st, rng) if kind else None
    st["next"] = now + rng.randint(*GAP)
    if spot:
        st["spots"].append({"at": spot, "kind": kind, "born": now, "until": now + rng.randint(*LIFE)})
        st["last"] = spot


def on_step(ds):
    """After you step: onto a spot, its wild Pokemon jumps out and you meet it (True)."""
    st = getattr(ds, "_ambush", None)
    if not st or not st["spots"] or st["floor"] != ds.run.index:
        return False
    t = tuple(ds.run.player)
    hit = next((s for s in st["spots"] if tuple(s["at"]) == t), None)
    if hit is None:
        return False
    st["spots"].remove(hit)
    now = pygame.time.get_ticks()
    st["next"] = max(st["next"], now + random.randint(*GAP))
    st["burst"] = (t, hit["kind"], now)
    from src.dungeon import core
    from src.dungeon.core import Mover
    core.CURRENT_TILE = ds.run.floor.tile(*t)
    try:
        p = ds._make_wild(random.Random(), t)
    finally:
        core.CURRENT_TILE = None
    if p is None:
        return False
    m = Mover("wild", t[0], t[1], p)
    ds.run.floor.movers.append(m)
    ds._meet_wild(m)
    return True


def leave(ds):
    if hasattr(ds, "_ambush"):
        ds._ambush = None


_FR = {}


def _frames(kind, gen, size):
    key = (kind, gen, size)
    if key not in _FR:
        base = os.path.join(ds_assets(), "dungeon", "effects")
        stem = {("grass", 3): "gen3_grass", ("dust", 3): "gen3_dust", ("ripple", 3): "gen3_ripple",
                ("grass", 4): "radar_rustle", ("dust", 4): "gen4_dust", ("ripple", 4): "gen4_ripple"}[(kind, gen)]
        out, i = [], 1
        while os.path.exists(os.path.join(base, f"{stem}_{i}.png")):
            im = pygame.image.load(os.path.join(base, f"{stem}_{i}.png"))
            w = size[0]
            h = max(1, round(im.get_height() * w / im.get_width()))
            im = pygame.transform.scale(im, (w, h))
            if (kind, gen) == ("grass", 3):   # (FireRed's flying leaves are faint on its own grass: a touch brighter to be seen)
                im.fill((40, 44, 16, 0), special_flags=pygame.BLEND_RGBA_ADD)
            out.append(im)
            i += 1
        _FR[key] = out
    return _FR[key]


def ds_assets():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")


def gen_of(ds):
    return 3 if _region(ds) in GEN3 else 4


def draw(ds, screen, at):
    """The live spots in this region's generation's frames, fading at the end; a burst where one jumped out."""
    st = getattr(ds, "_ambush", None)
    if not st or st.get("floor") != getattr(getattr(ds, "run", None), "index", None):
        return
    now = pygame.time.get_ticks()
    gen = gen_of(ds)
    for s in st["spots"]:
        r = at(*s["at"])
        fr = _frames(s["kind"], gen, (r.w, r.h))
        if not fr:
            continue
        k = (now - s["born"]) // 130
        if s["kind"] == "grass" and gen == 3 and len(fr) > 1:   # (FireRed's first frame is the grass at rest: the leaves-flying ones)
            fr = fr[1:]
        img = fr[k % len(fr)]
        if s["kind"] == "dust":   # (a cave puff: drawn half again as big, rising a little)
            img = pygame.transform.scale(img, (int(img.get_width() * 1.5), int(img.get_height() * 1.5)))
        left = s["until"] - now
        if left < FADE:
            img = img.copy()
            img.set_alpha(max(0, int(255 * left / FADE)))
        jig = (2 if k % 2 else -2) * max(1, r.w // 32) if s["kind"] == "grass" else 0   # (the patch shaking side to side)
        screen.blit(img, img.get_rect(midbottom=(r.centerx + jig, r.bottom - (r.h // 6 if s["kind"] == "dust" else 0))))
    burst = st.get("burst")
    if burst and now - burst[2] < 520:
        r = at(*burst[0])
        fr = _frames(burst[1], gen, (r.w, r.h))
        if fr:
            img = fr[min(len(fr) - 1, (now - burst[2]) // 104)]
            screen.blit(img, img.get_rect(midbottom=r.midbottom))
