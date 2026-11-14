# Soaring in the Sky, 3D (11-14): the flight over Omega Ruby's Hoenn, played the way a player meets it. Glue after
# harness_head.py:   bash dev/checks/run.sh soaring3d     (screenshots go to <scratch folder>/soaring3d_*.png)
import time
import pygame
from src.states.overworld import AreaTransitionState
from src.states.overworld.soaring3d import Soaring3DState
from src.states.battle import WildBattleState
from src.world import soaring3d as S3

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def run_transition(frames=400):
    for _ in range(frames):
        st = g.current_state
        if not isinstance(st, AreaTransitionState):
            return st
        st.dialogue_box.is_finished = True
        st.update()
    return g.current_state


def shot(name):
    g.current_state.draw()
    pygame.image.save(g.screen, os.path.join(S, f"soaring3d_{name}.png"))


def key(st, k, down=True):
    st.handle_events([pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k, mod=0, unicode="")])


def tap(st, pos):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)])


def place(st, x, z, heading=0.0, alt=1800.0):
    st.x, st.z, st.heading, st.alt = float(x), float(z), heading, alt
    st.skip.clear()
    st.wilds = []
    st.next_wild = 10 ** 6


g.dungeon_routes = True              # (the walked-routes option on, as in play)
flags = story.story_flags
flags["beat_hoenn_champion"] = True
for k in ("MOSSDEEP_CITY", "SLATEPORT_CITY", "DEWFORD_TOWN", "LILYCOVE_CITY"):
    flags[f"visited_{k}"] = True
story.current_area_key = "MOSSDEEP_CITY"

print("== the Eon Flute")
from src.states.systems import BagState
flags.pop("got_mega_bracelet", None)
story.inventory.pop(S3.FLUTE, None)
check(not S3.give_flute(story), "no flute before Southern Island")
flags["got_mega_bracelet"] = True
check(S3.give_flute(story) and story.inventory.get(S3.FLUTE) == 1, "a save past Southern Island gets the flute")
bag = BagState(g, g.current_state)
check(bag.usable(S3.FLUTE), "the flute can be used from the Bag")
check(bag.pocket_of(S3.FLUTE) == "KEY ITEMS", f"the flute is in Key Items ({bag.pocket_of(S3.FLUTE)})")
from src.pokemon import items as _items
check("fly you high" in _items.describe(S3.FLUTE), "it says what it does")
story.current_area_key = "HOENN_GRANITE_CAVE"
check(S3.flute_block(story) is not None, "no flying from inside a cave")
story.current_area_key = "MOSSDEEP_CITY"
check(S3.flute_block(story) is None, "it plays in Mossdeep")
g.change_state(bag); bag.use_item(S3.FLUTE)
check(isinstance(g.current_state, AreaTransitionState), "playing it starts the trip up")
st = run_transition()
check(isinstance(st, Soaring3DState), f"the trip ends in the 3D flight ({type(st).__name__})")
g.soaring3d_state = None
story.current_area_key = "MOSSDEEP_CITY"

print("== up from Mossdeep")
mossdeep = story.get_current_area_data()
exit_item = next(i for i in mossdeep.get("route_menu", mossdeep.get("town_menu", [])) or [] if
                 i.get("target_area") == S3.AREA) if mossdeep.get("route_menu") else None
g.change_state(AreaTransitionState(g, S3.AREA))
st = run_transition()
check(isinstance(st, Soaring3DState), f"Soaring in the Sky is the 3D flight (got {type(st).__name__})")
check(len(st.levels) == 4, f"the ground's four pictures are loaded ({len(st.levels)})")
check(st._eon_img(2, 1) is not None, "the baked Mega Eon is there (EON_LOOK = \"model\")")
check(S3.EON_LOOK == "sprite" and st._eon_sprite() is not None and st._eon_sprite().get_width() == 31 * 5,
      "Jordan's back sprite carries you, five times its size")
check(len(st.skyspots) == 2, f"after the Champion, the rift and the storm cloud are out ({len(st.skyspots)})")
check(len(st.land) >= 8, f"the Mirage places are out ({len(st.land)})")

print("== flying, and how long a frame takes")
st.update(); st.draw()
t0 = time.perf_counter()
for i in range(40):
    st.heading = (st.heading + 1.5) % 360
    st.update(); st.draw()
ms = (time.perf_counter() - t0) / 40 * 1000
print(f"   {ms:.1f} ms a frame (turning)")
check(ms < 40, f"a frame fits in the game's 25 a second on this PC ({ms:.1f} ms)")
t0 = time.perf_counter()
for i in range(40):
    st.update(); st.draw()
ms2 = (time.perf_counter() - t0) / 40 * 1000
print(f"   {ms2:.1f} ms a frame (straight on)")


def views(st, pre=""):
    """The same views over either ground: placed from the towns on it."""
    def near(town, dx, dz, **kw):
        x, z = S3.TOWNS[town]
        place(st, x + dx, z + dz, **kw)
    near("SLATEPORT_CITY", 0, 5500, heading=0, alt=1600); shot(pre + "slateport")
    near("LITTLEROOT_TOWN", 800, 1400, heading=330, alt=2600); shot(pre + "littleroot")
    near("LAVARIDGE_TOWN", 0, 5000, heading=0, alt=1400); shot(pre + "chimney")
    near("SOOTOPOLIS_CITY", -3200, 4200, heading=40, alt=2200); shot(pre + "sootopolis")
    near("MAUVILLE_CITY", 3800, -2900, heading=270, alt=3800); shot(pre + "high")
    st.bank, st.pitch = -1.0, 0.0; shot(pre + "bank_left")
    st.bank, st.pitch = 0.0, 0.0


check(S3.GROUND == "map" and st.on_map, "the ground is the 2D version's map")
mx, mz = S3.TOWNS["MOSSDEEP_CITY"]
check(abs(mx - (401 * S3.MAP_SCALE + S3.MAP_X0)) < 1 and abs(mz - (129 * S3.MAP_SCALE + S3.MAP_Z0)) < 1,
      "its towns are the map picture's own points")
views(st)

print("== a flock")
place(st, 0, 6000)
st.wilds = [{"pid": 278, "x": 0, "z": 6000 - 2400, "alt": 1800, "dx": 0, "dz": 0, "ph": 0, "n": 3}]
shot("flock")
for _ in range(30):
    if not isinstance(g.current_state, Soaring3DState):
        break
    st.update()
check(isinstance(g.current_state, WildBattleState), f"flying into a flock starts a battle ({type(g.current_state).__name__})")
b = g.current_state
check(b.opponent_pokemon.id == 278, "with one of that flock")

print("== back from the battle")
from src.states.overworld.route import PlayState
back = PlayState(g, restore_data=st._play_data())
check(back is st, "the flight goes on where it was")
g.change_state(back)

print("== the rift south of Dewford")
rift = next(s for s in st.skyspots if s["key"] == "rift")
place(st, rift["at"][0], rift["at"][1] + 4000, heading=0, alt=rift["alt"])
shot("rift_ahead")
for _ in range(40):
    st.update()
    if st.mode == "ASK":
        break
check(st.mode == "ASK" and "gap" in st.ask_line, f"near the rift: fly in? ({st.ask_line if st.mode == 'ASK' else st.mode})")
shot("rift_ask")
key(st, pygame.K_RETURN)
for _ in range(20):                  # (press through the legend's line)
    if g.current_state is st and st.dialogue_box.visible:
        st.dialogue_box.advance()
check(isinstance(g.current_state, WildBattleState) and g.current_state.opponent_pokemon.id == 483,
      f"Dialga comes out first ({getattr(getattr(g.current_state, "opponent_pokemon", None), "id", type(g.current_state).__name__)})")
flags["soaring_dialga"] = flags["soaring_palkia"] = True
g.change_state(PlayState(g, restore_data=st._play_data()))
rift = next((s for s in st.skyspots if s["key"] == "rift"), None)
check(rift is not None and rift["next"]["id"] == 487, "with Dialga and Palkia caught, Giratina is next")
flags["soaring_giratina"] = True
st._refresh_spots()
check(all(s["key"] != "rift" for s in st.skyspots), "all three caught: the rift has closed")

print("== a Mirage place")
spot = next(s for s in st.land if s["area"] == "HOENN_CRESCENT_ISLE")
place(st, spot["at"][0], spot["at"][1] + 3000, heading=0, alt=1500)
shot("crescent_ahead")
for _ in range(40):
    st.update()
    if st.mode == "ASK":
        break
check(st.mode == "ASK" and "Crescent" in st.ask_line, f"over Crescent Isle: land? ({getattr(st, 'ask_line', st.mode)})")
key(st, pygame.K_n)
check(st.mode == "FLY", "FLY ON keeps flying")
place(st, spot["at"][0], spot["at"][1] + 3000, heading=0, alt=1500)
st.skip.clear()
for _ in range(40):
    st.update()
    if st.mode == "ASK":
        break
key(st, pygame.K_RETURN)
nxt = run_transition()
check(story.current_area_key == "HOENN_CRESCENT_ISLE", f"landing puts you on Crescent Isle ({story.current_area_key})")

print("== landing at a town")
g.change_state(AreaTransitionState(g, S3.AREA))
st = run_transition()
check(isinstance(st, Soaring3DState) and st is not None, "up again from Crescent Isle")
place(st, 1600, 8000)
key(st, pygame.K_ESCAPE)
check(st.mode == "ASK" and "Slateport" in st.ask_line, f"LAND offers the nearest town you've been to ({getattr(st, 'ask_line', '')})")
tap(st, st.ask[1][0][0].center)
run_transition()
check(story.current_area_key == "SLATEPORT_CITY", f"and sets you down there ({story.current_area_key})")

print("== Omega Ruby's sky map, the same views (to compare)")
S3.GROUND = "oras"
g.soaring3d_state = None
story.current_area_key = "MOSSDEEP_CITY"
g.change_state(AreaTransitionState(g, S3.AREA))
st = run_transition()
check(isinstance(st, Soaring3DState) and not st.on_map and len(st.levels) == 4, "the sky map still works")
views(st, "oras_")
S3.GROUND = "map"

print(f"##### {len(fails)} fail(s)")
