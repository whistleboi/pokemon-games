"""The Poke Radar (Jordan 11-19, the Sinnoh re-audit: built last), Platinum's way on our walked maps:
- Charged by walking (50 steps), used in tall grass (the Bag, or the map's RADAR button): four patches of grass nearby
  shake. Step into one and a wild Pokemon jumps out - from the area's radar pool (its usual grass Pokemon, with
  Platinum's radar-only species in the radar's slots: area "radar_pool_percentages", kanto_handoff s_radar.py).
- After that meeting (caught, beaten or not) the grass shakes again by itself: meet the same species again and the
  chain grows; a longer chain makes the same species likelier in the patches, and shiny patches likelier (Platinum:
  about 1 in 200 at a chain of 40). Step anywhere but a shaking patch, or leave, and the chain breaks.
- In Platinum it works after the National Pokedex: radar-only species only come then (the item is given then too).

State lives on the map screen (ds._radar): {"patches": {(x, y): {"species", "shiny"}}, "chain", "species", "again"};
the charge on the story (story.radar_steps)."""
import math
import random

CHARGE = 50
PATCHES = 4


def _state(ds):
    if not hasattr(ds, "_radar") or ds._radar is None:
        ds._radar = {"patches": {}, "chain": 0, "species": None, "again": False}
    return ds._radar


def owned(story):
    return story.inventory.get("POKE_RADAR", 0) > 0


def charge(story):
    return int(getattr(story, "radar_steps", CHARGE) or 0)


def _grass(ds, t):
    from src.dungeon import core
    f = ds.run.floor
    return f.inside(*t) and f.tile(*t) == core.GRASS


def pool(ds):
    """The radar's pool here: the area's radar pool, else its usual grass pool."""
    data = ds.game.loader.area_data
    key = ds.area_data.get("radar_pool_percentages")
    if key and data.get(key) and ds.game.story_manager.story_flags.get("unlocked_national_dex"):
        return dict(data[key])
    return dict(ds._get_wild_pool(ds.area_data) or {})


def _keep_chance(chain):
    return min(0.9, 0.5 + chain * 0.01)


def _shiny_chance(chain):
    """Platinum's patch odds grow with the chain: about 1 in 200 at 40."""
    c = min(chain, 40)
    return 1.0 / max(200, 8192 - c * 200)


def shake(ds, rng=None, free=False):
    """Four patches of grass shake (free: the chain's own shake, no charge). Returns the lines to say."""
    rng = rng or random.Random()
    st = _state(ds)
    story = ds.game.story_manager
    if not free:
        if not owned(story):
            return ["You don't have a POKE RADAR."]
        if not _grass(ds, tuple(ds.run.player)):
            return ["The POKE RADAR works in tall grass. Stand in the grass first!"]
        if charge(story) < CHARGE:
            return [f"The POKE RADAR is charging... {CHARGE - charge(story)} more steps."]
    pl = pool(ds)
    if not pl:
        return ["The POKE RADAR found nothing here."]
    px, py = ds.run.player
    spots = []
    for ring in range(4, 0, -1):          # (Platinum: one patch on each of the four rings around you, the far ones first)
        ring_tiles = [(px + dx, py + dy) for dx in range(-ring, ring + 1) for dy in range(-ring, ring + 1)
                      if max(abs(dx), abs(dy)) == ring and _grass(ds, (px + dx, py + dy))
                      and ds.run.floor.mover_at(px + dx, py + dy) is None]
        if ring_tiles:
            spots.append(rng.choice(ring_tiles))
    if not spots:
        return ["The grass around here is too sparse for the POKE RADAR."]
    patches = {}
    for t in spots[:PATCHES]:
        if st["species"] and rng.random() < _keep_chance(st["chain"]):
            sp = st["species"]
        else:
            sp = int(rng.choices(list(pl), weights=list(pl.values()))[0])
        shiny = sp == st["species"] and rng.random() < _shiny_chance(st["chain"])
        patches[t] = {"species": int(sp), "shiny": shiny}
    st["patches"] = patches
    st["floor"] = ds.run.index
    if not free:
        story.radar_steps = 0
    return None if free else [f"{ds.game.player_name} used the POKE RADAR!", "The grass is rustling!"]


def on_step(ds):
    """After you step: into a shaking patch, a wild Pokemon jumps out (True); anywhere else the patches stop and the chain
    breaks. Also charges the radar."""
    story = ds.game.story_manager
    if owned(story):
        story.radar_steps = min(CHARGE, charge(story) + 1)
    st = _state(ds)
    if not st["patches"]:
        return False
    if st.get("floor") != ds.run.index:   # (another floor: the patches were left behind)
        st.update(patches={}, chain=0, species=None, again=False)
        return False
    t = tuple(ds.run.player)
    hit = st["patches"].pop(t, None)
    if hit is None:
        lost = st["chain"]
        st.update(patches={}, chain=0, species=None, again=False)
        if lost >= 2:
            ds.flash(f"The POKE RADAR's chain of {lost} broke!")
        return False
    st["patches"] = {}
    sp = hit["species"]
    if sp == st["species"]:
        st["chain"] += 1
    else:
        st["species"], st["chain"] = sp, 1
    from src.pokemon.data import Pokemon
    from src.dungeon.core import Mover
    from src.world import levels
    raw = ds.game.loader._fetch_raw(id_pool=[sp], area_data=ds.area_data)
    if not raw:
        return False
    p = Pokemon(raw, ds.game.assets, size_mult=3.125)
    levels.set_wild(ds.game, p, ds.area_key)
    if hit["shiny"]:
        p.is_shiny = True
    import pygame
    st["burst"] = (t, pygame.time.get_ticks())   # (the leaves fly up: Platinum's kusaeff)
    m = Mover("wild", t[0], t[1], p)
    ds.run.floor.movers.append(m)
    st["again"] = True
    ds._meet_wild(m)
    if st["chain"] >= 2:
        ds.flash(f"POKE RADAR chain: {st['chain']}!")
    return True


def tick(ds):
    """Back on the map after a radar meeting: the grass shakes again by itself (the chain goes on)."""
    st = _state(ds)
    if st["again"] and getattr(ds, "mode", "") == "MAP" and getattr(ds, "encounter", None) is None:
        st["again"] = False
        if _grass(ds, tuple(ds.run.player)):
            shake(ds, free=True)


def leave(ds):
    if hasattr(ds, "_radar"):
        ds._radar = None


_IMGS = {}


def _frames(kind, size):
    """Platinum's own frames (assets/dungeon/effects/radar_<kind>_<n>.png: kanto_handoff radar_pics.py), scaled to a tile."""
    import os
    import pygame
    key = (kind, size)
    if key not in _IMGS:
        out, n = [], 1
        while os.path.exists(f"assets/dungeon/effects/radar_{kind}_{n}.png"):
            im = pygame.image.load(f"assets/dungeon/effects/radar_{kind}_{n}.png").convert_alpha()
            out.append(pygame.transform.scale(im, size))
            n += 1
        _IMGS[key] = out
    return _IMGS[key]


def draw(ds, screen, at):
    """The shaking patches, in Platinum's own field-effect frames: a gentle shake where the chain's kind waits (our hint),
    a hard shake elsewhere, the sparkle on a shiny patch; the leaves bursting up as a Pokemon jumps out."""
    import pygame
    st = getattr(ds, "_radar", None)
    if not st:
        return
    ms = pygame.time.get_ticks()
    for (x, y), patch in (st.get("patches") or {}).items():
        r = at(x, y)
        kind = "shiny" if patch.get("shiny") else "shake" if st.get("species") == patch["species"] else "rustle"
        fr = _frames(kind, (r.w, r.h))
        if fr:
            screen.blit(fr[(ms // 140 + x + y) % len(fr)], r)
    burst = st.get("burst")
    if burst and ms - burst[1] < 560:
        r = at(*burst[0])
        fr = _frames("burst", (r.w * 2, r.h * 2))
        if fr:
            img = fr[min(len(fr) - 1, (ms - burst[1]) // 140)]
            screen.blit(img, img.get_rect(center=r.center))
