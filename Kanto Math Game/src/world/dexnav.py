"""The DexNav's hidden Pokemon (ORAS; Jordan 11-19: "Add the dex nav, and add 1-3 mons. Add the later gen mons after the
player becomes champion"). With the DexNav (POKE_NAV, from your rival on Route 101), walking a Hoenn route or cave now and
then shows a Pokemon hiding nearby: a tail in the grass (or a cave's floor, or deep sand), or a ripple out on the water
while you surf. Creep onto it and it's yours to battle - one of the area's hidden Pokemon (ORAS's own, from
kanto_handoff/hoenn_rom_tools/hdexnav.py: "dexnav_pool_percentages" / "dexnav_surf_pool_percentages").
It slips away if you take too long. When they turn up:
  Gen 1-3 (#1-386)   after Groudon / Kyogre (cave_of_origin_cleared), as ORAS
  later generations  once you're Hoenn's Champion (beat_hoenn_champion)
State on the map screen (ds._dexnav): {"spot": (x, y) or None, "kind": "land"/"surf", "species", "left": steps, "floor"}."""
import random

CHANCE = 1 / 30      # (each step: about one hidden Pokemon every thirty steps where the area has them)
LIFETIME = 18        # (steps before it slips away)
NEAR = (2, 4)        # (how far from you it appears)
STORY_FLAG = "cave_of_origin_cleared"
LATE_FLAG = "beat_hoenn_champion"


def owned(story):
    return story.inventory.get("POKE_NAV", 0) > 0


def pool(game, area_key, kind="land"):
    """This area's hidden Pokemon you can meet now ({species: weight}), by what you're standing on."""
    data = game.loader.area_data
    area = (data.get("STORY_PROGRESSION", {}) or {}).get(area_key) or {}
    name = area.get("dexnav_surf_pool_percentages" if kind == "surf" else "dexnav_pool_percentages")
    flags = game.story_manager.story_flags
    out = {}
    for sp, w in (data.get(name) or {}).items():
        if not str(sp).isdigit():
            continue
        late = int(sp) > 386
        if (late and flags.get(LATE_FLAG)) or (not late and flags.get(STORY_FLAG)):
            out[str(sp)] = w
    return out


def _state(ds):
    if getattr(ds, "_dexnav", None) is None:
        ds._dexnav = {"spot": None}
    return ds._dexnav


def _kind_here(ds):
    from src.dungeon import core
    t = ds.run.floor.tile(*ds.run.player)
    return "surf" if t in (core.SURF, core.WATER) else "land"


def _hide_tiles(ds, kind):
    from src.dungeon import core
    f = ds.run.floor
    px, py = ds.run.player
    want = (core.SURF, core.WATER) if kind == "surf" else ((core.GRASS,) if f.style not in ("cave", "mountain", "tunnel") else (core.GRASS, core.FLOOR))
    out = []
    for dx in range(-NEAR[1], NEAR[1] + 1):
        for dy in range(-NEAR[1], NEAR[1] + 1):
            if NEAR[0] <= max(abs(dx), abs(dy)) <= NEAR[1]:
                t = (px + dx, py + dy)
                if f.inside(*t) and f.tile(*t) in want and f.walkable(*t) and f.mover_at(*t) is None:
                    out.append(t)
    return out


def on_step(ds, rng=None):
    """After a step: onto the hiding spot, the Pokemon jumps out (True); else it may appear, or slip away."""
    story = ds.game.story_manager
    if not owned(story) or str(story.get_current_region()).upper() != "HOENN" or not hasattr(ds, "run"):
        return False
    rng = rng or random
    st = _state(ds)
    if st.get("spot") and st.get("floor") != ds.run.index:
        st["spot"] = None
    if st.get("spot"):
        if tuple(ds.run.player) == tuple(st["spot"]):
            return _meet(ds, st)
        st["left"] -= 1
        if st["left"] <= 0:
            st["spot"] = None
            ds.flash("The hidden Pokemon slipped away...")
        return False
    if getattr(ds, "encounter", None) is not None or getattr(ds, "contest", None):
        return False
    kind = _kind_here(ds)
    pl = pool(ds.game, ds.area_key, kind)
    if not pl or rng.random() >= CHANCE:
        return False
    tiles = _hide_tiles(ds, kind)
    if not tiles:
        return False
    sp = int(rng.choices(list(pl), weights=list(pl.values()))[0])
    st.update(spot=rng.choice(tiles), kind=kind, species=sp, left=LIFETIME, floor=ds.run.index)
    ds.flash("DexNav: something is hiding nearby! Creep up on it..." if kind == "land" else "DexNav: something is moving in the water!")
    return False


def _meet(ds, st):
    from src.pokemon.data import Pokemon
    from src.dungeon.core import Mover
    from src.world import levels
    sp, t = st["species"], tuple(st["spot"])
    st["spot"] = None
    raw = ds.game.loader._fetch_raw(id_pool=[sp], area_data=ds.area_data)
    if not raw:
        return False
    p = Pokemon(raw, ds.game.assets, size_mult=3.125)
    levels.set_wild(ds.game, p, ds.area_key)
    m = Mover("wild", t[0], t[1], p)
    ds.run.floor.movers.append(m)
    ds._meet_wild(m)
    return True


def leave(ds):
    if getattr(ds, "_dexnav", None):
        ds._dexnav = None


def draw(ds, screen, at):
    """The hiding spot: a tail flicking in the grass (Platinum's rustling grass frames), or rings on the water."""
    import pygame
    st = getattr(ds, "_dexnav", None)
    if not st or not st.get("spot") or st.get("floor") != getattr(ds.run, "index", None):
        return
    r = at(*st["spot"])
    ms = pygame.time.get_ticks()
    if st.get("kind") == "surf":
        k = (ms // 160) % 3
        for i in range(2):
            rad = max(4, r.w // 6 + (k + i * 2) * r.w // 10)
            pygame.draw.circle(screen, (235, 245, 255), r.center, rad, 2)
        return
    from src.world import poke_radar
    fr = poke_radar._frames("rustle", (r.w, r.h))
    if fr:
        screen.blit(fr[(ms // 120) % len(fr)], r)
    else:
        pygame.draw.circle(screen, (250, 230, 120), r.center, r.w // 4)
