# Doors, area changes and the name sign as each walked region's own game does them (Jordan 11-24, region/systems;
# src/vfx/area_changes.py): per region (Kanto FireRed, Hoenn Emerald, Johto HGSS, Sinnoh Platinum, Unova Platinum's,
# Orre Essentials) a door in and out, a floor change, a walk over from a town to a route and back, a cave entry: no
# in-between screen, the game's fade (colour, length), the sign's style and timing (none inside buildings), story text
# still said. Played through Game._frame as the game runs; pictures and a GIF per region in out/area_changes.
#   bash dev/checks/run.sh area_changes
import json
import math
import os as _os
from PIL import Image
from src.config import FPS
from src.states.overworld import PlayState, CityState, AreaTransitionState
from src.states.overworld.dungeon import DungeonState, map_view
from src.states.overworld.walk_town import WalkTownState
from src.vfx import area_changes as ac
from src.vfx import canon_intros as ci

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


OUT = _os.path.join(S, "area_changes")
_os.makedirs(OUT, exist_ok=True)
g.dungeon_routes = True; g.walk_towns = True
story.story_flags["hoenn_version"] = "OMEGA_RUBY"; story.story_flags["unova_version"] = "BLACK_2"
for _k in ("kanto", "johto", "hoenn", "sinnoh", "unova", "orre"):
    story.story_flags[f"received_starter_{_k}"] = story.story_flags[f"move_offer_{_k}"] = True
SP = g.loader.area_data["STORY_PROGRESSION"]
MAPS = json.load(open("assets/town_maps.json", encoding="utf-8"))
GIF = []


def grab():
    s = pygame.transform.smoothscale(g.screen, (640, 360))
    GIF.append(Image.frombytes("RGB", s.get_size(), pygame.image.tobytes(s, "RGB")))


def play(n=200, until=None):
    """Frames as the game runs them (Game._frame: the wipe over the top); each one kept for the GIF. Returns the frames
    the wipe took and a list of (holding, centre colour, corner colour) per wipe frame."""
    seen, took = [], 0
    for _ in range(n):
        w = g.area_wipe
        hold = w.holding() if w is not None else False
        g._frame()
        grab()
        if w is not None:
            took += 1
            v = map_view(g)
            seen.append((hold, tuple(g.screen.get_at(v.center))[:3],
                         tuple(g.screen.get_at((v.x + 4, v.y + 4)))[:3], w.log[-1] if w.log else None))
        if until and until() and g.area_wipe is None:
            break
    return took, seen


def shot(name):
    pygame.image.save(g.screen, _os.path.join(OUT, name))


def near(c, want, tol=40):
    return all(abs(a - b) <= tol for a, b in zip(c, want))


def wipe_frames(key, kind):
    p = ac.plan(key, kind)
    return int(math.ceil(ac.length60(p) * FPS / 60.0)) + 1 if p else 0


def town(area):
    story.current_area_key, story.last_area_key = area, None
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = g.walk_town_room = None
    g._sign_area = None
    st = CityState(g)
    g.change_state(st)
    g.screen.fill((0, 0, 0))
    for _ in range(30):   # (tap through anything said first)
        if not st.npc_active:
            break
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update()
    g.area_wipe = ac.ACTIVE = None
    return st


def route(area, came=None):
    story.current_area_key, story.last_area_key = area, came
    g._sign_area = None
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    g.screen.fill((0, 0, 0))
    g.area_wipe = ac.ACTIVE = None
    return p


def talk_off(st):
    for _ in range(40):
        if isinstance(st, DungeonState) and st.dialogue_box.visible:
            st.dialogue_box.advance(); st.update()
        elif isinstance(st, WalkTownState) and st.npc_active:
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); st.update()
        else:
            return


def sign_life(st, n=400, name=None):
    """Frames the state's sign is on screen (from first showing to gone), played on the map; its phases seen."""
    s = getattr(st, "sign", None)
    if s is None:
        return 0, None
    on, phases = 0, []
    for _ in range(n):
        if g.current_state is not st:
            break
        g._frame()
        if len(GIF) < 2000 and on % 3 == 0:
            grab()
        if s.shown() > 0 or s.phase()[0] == "wait":
            on += 1
            if not phases or phases[-1] != s.phase()[0]:
                phases.append(s.phase()[0])
                if name and phases[-1] == "hold":
                    shot(name)
        if s.gone:
            break
    return on, phases


def expect_sign(key):
    w, a, h, o = ac.SIGN_TIMES[key]
    return int(math.ceil((w + a + h + o) * FPS / 60.0))


# (game, town, route-to-cave, cave, stairs place)
PLACES = {
    "KANTO": ("frlg", "PEWTER_CITY", "KANTO_ROUTE_2", "DIGGLETT_CAVE", "DIGGLETT_CAVE"),
    "HOENN": ("emerald", "OLDALE_TOWN", "HOENN_ROUTE_111", "HOENN_DESERT_RUINS", "HOENN_GRANITE_CAVE"),
    "JOHTO": ("hgss", "VIOLET_CITY", "JOHTO_ROUTE_47", "JOHTO_CLIFF_CAVE", "SPROUT_TOWER"),
    "SINNOH": ("platinum", "JUBILIFE_CITY", "SINNOH_ROUTE_203", "OREBURGH_GATE", "OREBURGH_GATE"),
    "UNOVA": ("platinum", "FLOCCESY_TOWN", "UNOVA_ROUTE_9", "CHALLENGERS_CAVE", "SEASIDE_CAVE"),
    "ORRE": ("orre", "PHENAC_CITY", "PYRITE_TOWN", "PYRITE_CAVE", "SNAGEM_HIDEOUT"),
}

print("0) each region's game (Unova copies Platinum: Jordan 11-24)")
check([ci.game_for(r) for r in PLACES] == [v[0] for v in PLACES.values()], "Kanto FireRed, Hoenn Emerald, Johto HGSS, Sinnoh and Unova Platinum, Orre Essentials")
check(ac.game_key("KALOS") is None and ac.plan(None, "door_in") is None, "Kalos (a menu region): no profile")
check(ac.SIGN_TIMES["frlg"] == (0, 12, 120, 12) and ac.SIGN_TIMES["emerald"] == (30, 20, 120, 20)
      and ac.SIGN_TIMES["hgss"] == ac.SIGN_TIMES["platinum"] == (0, 10, 60, 10) and ac.SIGN_TIMES["orre"] == (0, 24, 96, 24),
      "the signs' timings: FireRed 12/120/12, Emerald wait 30 + 20/120/20, HGSS/Platinum 10/60/10 (4 px a frame), Orre 0.4/1.6/0.4 s")


def first_in(seen):
    """The first frame after the old picture is gone (the new place under its cover)."""
    return next((s for s in seen if not s[0]), None)


def last_out(seen):
    outs = [s for s in seen if s[0]]
    return outs[-1] if outs else None


def stairs_place(region, given):
    if given:
        return given
    for k, v in SP.items():
        if isinstance(v, dict) and str(v.get("region") or "KANTO").upper() == region and v.get("area_type") == "dungeon":
            try:
                p = route(k)
            except Exception:
                continue
            if isinstance(p, DungeonState) and p.run.n_floors > 1:
                return k
    return None


COLOUR = {"black": (0, 0, 0), "white": (255, 255, 255)}
for region, (key, town_key, cave_from, cave_key, stairs_key) in PLACES.items():
    GIF.clear()
    print(f"\n{region} ({key})")
    # --- the town: its sign, a door in and back out
    t = town(town_key)
    check(isinstance(t, WalkTownState) and t.sign and t.sign.key == key and t.banner == 0,
          f"{town_key}: walked; the sign in {key}'s look ({t.sign.theme if t.sign else None}), not the old big banner")
    on, phases = sign_life(t, name=f"{region.lower()}_sign.png")
    want = expect_sign(key)
    check(abs(on - want) <= 2 and phases and phases[-1] in ("out", "hold"), f"...on screen {on} frames ({want} wanted: {phases})")
    if key == "emerald":
        check(phases[0] == "wait", "...Emerald's 30-frame wait first")
    door = next((tuple(int(v) for v in d.split(",")) for d, r in (t.town_map.get("inside") or {}).items()
                 if tuple(int(v) for v in d.split(",")) in t.doors and r in (t.town_map.get("rooms") or {})), None)
    check(door is not None, f"...a door with a room behind it ({door})")
    if door:
        play(3)
        t._enter(door)
        w = g.area_wipe
        check(t.room and w is not None and w.kind == "door_in" and w.length == wipe_frames(key, "door_in"),
              f"in by the door: {t.room}, the {key} door fade ({w.length if w else None} frames, {wipe_frames(key, 'door_in')} wanted)")
        took, seen = play(60, until=lambda: True)
        fi = first_in(seen)
        if key != "orre":
            check(fi is not None and fi[3][0] == "fade_in" and sum(fi[1]) < 160, f"...through black ({fi[1] if fi else None}, {fi[3] if fi else None})")
        else:
            check(all(s[3] and s[3][0] == "cross" for s in seen), "...Essentials' 0.4 s crossfade (no black)")
        check(getattr(t, "sign", None) is None or t.sign.gone, "...no sign inside the building")
        out_to = next(v for v in t.exits.values() if str(v).startswith("OUT:")) if any(str(v).startswith("OUT:") for v in t.exits.values()) else "OUT:%d,%d" % door
        t._leave(out_to)
        w = g.area_wipe
        styles = {"frlg": "barn", "emerald": "fade_in", "hgss": "shutter", "platinum": "shutter", "orre": "cross"}[key]
        check(not t.room and w is not None and w.kind == "door_out" and any(s[0] == styles for s in w.into),
              f"out of the door: outside, the {key} way ({styles})")
        half = w.out_len * FPS / 60.0 + (w.length - w.out_len * FPS / 60.0) / 2
        took = 0
        while g.area_wipe is w and took < 80:
            g._frame(); grab(); took += 1
            if took == int(half):
                shot(f"{region.lower()}_door_out_mid.png")
        check(t.sign is not None and t.sign.key == key, f"...and back outdoors the town's sign again ({t.sign.text if t.sign else None})")
    # --- over the edge: town -> route, and back
    t = town(town_key)
    play(2)
    edge = [(at, v) for at, v in t.exits.items() if not str(v).startswith(("OUT", "ROOM")) and ac.place_class(g, v) == "outside"
            and (at[0] <= 0 or at[1] <= 0 or at[0] >= t.w - 1 or at[1] >= t.h - 1) and ac.walked(g, v)
            and t._travel_option(v) is not None and t._shown(t._travel_option(v))]
    if region == "ORRE":
        check(True, "Orre: towns are reached by motorbike (the ride scene stays); the edge walk is played from the map below")
    if edge:
        at, target = edge[0]
        t.player = t.anim_from = at
        t.anim = 0
        t._leave(target)
        st = g.current_state
        q = getattr(st, "quick", None)
        if isinstance(st, AreaTransitionState) and q is None:
            check(region == "ORRE", f"{town_key} -> {target}: the in-between screen kept ({'a ride' if st.ride or st.scene else 'why?'})")
        else:
            check(isinstance(st, AreaTransitionState) and q and q[0] == "walk" and not st.dialogue_box.visible and not st.dialogue_box.text_lines,
                  f"{town_key} -> {target} over the edge: no in-between screen (no words, no picture)")
            took, seen = play(40, until=lambda: not isinstance(g.current_state, AreaTransitionState))
            r = g.current_state
            check(isinstance(r, DungeonState) and story.current_area_key == target, f"...on {target}'s map after {took} wipe frames")
            if key == "orre":
                check(took == wipe_frames(key, "walk"), f"...Essentials' 0.4 s crossfade ({took} frames)")
            else:
                check(took == 0 and getattr(g, "_fade_left", 0) >= 0, "...no fade but the quick crossfade between screens (the games walk straight over)")
            if isinstance(r, DungeonState):
                play(2)
                check(r.sign is not None and r.sign.key == key and r.banner == 0, f"...{target}'s sign ({r.sign.text if r.sign else None})")
                back = [(tl, v) for tl, v in r.run.floor.exits.items() if v == town_key]
                if back:
                    r.run.player = back[0][0]
                    r._leave(town_key)
                    st = g.current_state
                    q = getattr(st, "quick", None)
                    check(isinstance(st, AreaTransitionState) and q and q[0] == "walk", f"...and back over its edge to {town_key}: no in-between screen ({q})")
                    play(30, until=lambda: not isinstance(g.current_state, AreaTransitionState))
                    check(isinstance(g.current_state, WalkTownState) and story.current_area_key == town_key, "...in the town again")
    elif region != "ORRE":
        check(False, f"{town_key}: an edge way out to a walked route")
    # --- a floor change (stairs)
    sk = stairs_place(region, stairs_key)
    if sk:
        p = route(sk)
        play(2)
        talk_off(p)
        from src.dungeon import core as _core
        down = next(((tl, v) for tl, v in p.run.floor.exits.items() if v == _core.STAIRS
                     or (str(v).startswith("WARP:") and int(str(v).split(":")[1]) != p.run.index and not p._indoors(int(str(v).split(":")[1]))
                         and not str(v).endswith(":fall"))), None)
        check(down is not None, f"{sk}: stairs (or a ladder) to another floor on its first floor ({down})")
        if down:
            p.run.player = p.anim_from = down[0]
            _to = 1 if down[1] == _core.STAIRS else int(str(down[1]).split(":")[1])
            p._handle([("stairs",)] if down[1] == _core.STAIRS else [("warp", down[1])])
            w = g.area_wipe
            check(p.run.index == _to and not p.dialogue_box.visible and w is not None and w.kind == "stairs",
                  f"{sk}: down the stairs at once, no words, the {key} fade ({w.length if w else None} frames)")
            took, seen = play(60, until=lambda: True)
            check(took == wipe_frames(key, "stairs"), f"...{took} frames ({wipe_frames(key, 'stairs')} wanted)")
            fl = p._floor_name(_to)
            if p._indoors(_to):
                check(p.sign is None, "...a room: no sign")
            elif key in ("hgss", "platinum") and ac.place_class(g, sk) == "inside" and "tower" not in sk.lower():
                check(p.sign is None, "...a building: no sign (Gen 4)")
            else:
                check(p.sign is not None and ((fl in p.sign.text) == (key in ("frlg", "orre"))),
                      f"...the sign: '{p.sign.text if p.sign else None}' ({'with' if key in ('frlg', 'orre') else 'without'} the floor)")
    else:
        check(True, f"{region}: no multi-floor place to try stairs in")
    # --- story text still said (Johto: Sprout Tower's warning; every region: words a trip carries, on arrival)
    if region == "JOHTO":
        t = town("VIOLET_CITY")
        play(2)
        t._enter(next(d for d, k in t.doors.items() if k == "sprout"))
        st = g.current_state
        check(isinstance(st, AreaTransitionState) and st.quick and st.quick[0] == "door_in", f"Violet City -> Sprout Tower's door: no in-between screen ({getattr(st, 'quick', None)})")
        play(40, until=lambda: isinstance(g.current_state, DungeonState) and g.current_state.dialogue_box.visible)
        p = g.current_state
        lines = list(getattr(getattr(p, "dialogue_box", None), "text_lines", []) or [])
        check(isinstance(p, DungeonState) and p.dialogue_box.visible and any("pillar" in l for l in lines),
              f"...its warning said on the tower's own text box ({lines[:2]})")
        shot("johto_story_text.png")
    p = route(cave_from) if region != "ORRE" else town(cave_from)
    play(2)
    talk_off(p)
    g.change_state(p)
    # --- a cave entry
    if isinstance(p, DungeonState):
        mouth = next((tl for tl, v in p.run.floor.exits.items() if v == cave_key), None)
        if mouth:
            p.run.player = mouth
        p._leave(cave_key)
    else:
        g.change_state(AreaTransitionState(g, cave_key))   # (Orre's caves are reached from the town's own options)
    st = g.current_state
    q = getattr(st, "quick", None)
    check(isinstance(st, AreaTransitionState) and q and q[0] == "cave_in", f"{cave_from} -> {cave_key}: a cave entry, no in-between screen ({q})")
    w = g.area_wipe
    took = 0
    seen = []
    mid = None
    while g.area_wipe is w and w is not None and took < 120:
        hold = w.holding()
        g._frame(); grab(); took += 1
        v = map_view(g)
        seen.append((hold, tuple(g.screen.get_at(v.center))[:3], tuple(g.screen.get_at((v.x + 4, v.y + 4)))[:3], w.log[-1]))
        if took == max(1, int(w.out_len * FPS / 60.0 / 2)):
            shot(f"{region.lower()}_cave_in_mid.png")
    lo, fi = last_out(seen), first_in(seen)
    if key in ("frlg", "emerald"):
        check(lo and near(lo[1], (255, 255, 255)) and fi and fi[3][0] == "ramp" and fi[1][0] > 128,
              f"...the old map fades to WHITE, the cave's ramp down to black, in from black ({lo[1] if lo else None}, {fi[1] if fi else None})")
    elif key in ("hgss", "platinum"):
        check(any(s[3] and s[3][0] == "iris" for s in seen) and lo and near(lo[2], (0, 0, 0)), "...the iris closing on the middle (black)")
    else:
        check(any(s[3] and s[3][0] == "bands" for s in seen) and any(s[3] and s[3][0] == "cross" for s in seen),
              "...Essentials' 15 bands from the edges in, to black, then the crossfade")
    check(took == wipe_frames(key, "cave_in"), f"...{took} frames ({wipe_frames(key, 'cave_in')} wanted)")
    play(10)
    check(story.current_area_key == cave_key and isinstance(g.current_state, DungeonState), f"...in {cave_key}")
    # --- words the trip carries, said on the map on arrival (a lift's, an event's)
    p = g.current_state
    talk_off(p)
    g.change_state(AreaTransitionState(g, cave_from if region != "ORRE" else "ORRE_DESERT", initial_message=["The ground rumbles..."]))
    st = g.current_state
    check(getattr(st, "quick", None) is not None and not st.dialogue_box.text_lines, f"out again with words: no in-between screen ({getattr(st, 'quick', None)})")
    play(40, until=lambda: getattr(g.current_state, "npc_active", False) or getattr(getattr(g.current_state, "dialogue_box", None), "visible", False) and not isinstance(g.current_state, AreaTransitionState))
    m = g.current_state
    said = list(getattr(m, "dialogue_box", None).text_lines) if isinstance(m, DungeonState) else \
        list(getattr(getattr(m, "npc_dialogue", None), "text_lines", None) or getattr(getattr(m, "npc_dialogue", None), "lines", None) or [])
    check(any("rumbles" in l for l in said), f"...said by the map you arrive on ({said[:1]})")
    if GIF:
        GIF[0].save(_os.path.join(OUT, f"{region.lower()}.gif"), save_all=True, append_images=GIF[1::2][:900], duration=40, loop=0)

print("\nKalos (a menu region): the in-between screen stays")
story.current_area_key = "KALOS_ROUTE_2" if "KALOS_ROUTE_2" in SP else next(k for k, v in SP.items() if isinstance(v, dict) and v.get("region") == "KALOS")
_k = AreaTransitionState(g, story.current_area_key)
check(getattr(_k, "quick", None) is None and _k.timer == 75 and _k.dialogue_box.text_lines, "Kalos: its old screen (75 frames, its words)")
print(f"\n##### {len(fails)} failures")
for f in fails:
    print("FAIL " + f)
