# Wild Pokemon that don't always chase you, and ambush spots (Jordan 11-24): src/dungeon/core.py (temper),
# src/world/ambush.py (shaking grass, cave dust, ripples while you surf; each region in its own generation's art).
#   bash dev/checks/run.sh ambush
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
import os as _os
import pygame as _pg
from src.world import ambush
g.dungeon_routes = True
SHOTS = _os.path.join(S, "ambush")
_os.makedirs(SHOTS, exist_ok=True)

print("1) not every wild Pokemon chases: about 4 in 10 chase, 4 wander, 2 keep away; level tilts it")
p = kanto("KANTO_ROUTE_1")
frames(p, 3)
run = p.run


class _P:
    def __init__(self, lv):
        self.level = lv


run.lead_level = 10
got = [run._temper(_P(10)) for _ in range(3000)]
share = {k: got.count(k) / len(got) for k in ("chase", "wander", "shy")}
check(0.34 < share["chase"] < 0.46 and 0.34 < share["wander"] < 0.46 and 0.15 < share["shy"] < 0.25, f"same level: {share}")
hi = [run._temper(_P(20)) for _ in range(2000)].count("chase") / 2000
lo = [run._temper(_P(2)) for _ in range(2000)]
check(hi > 0.65, f"ten levels above your lead: most chase ({hi:.2f})")
check(lo.count("shy") / 2000 > 0.4 and lo.count("chase") / 2000 < 0.2, f"well below: shyer ({lo.count('shy') / 2000:.2f} shy)")
check(all(getattr(m, "temper", None) in ("chase", "wander", "shy") for m in run.floor.movers if m.kind == "wild"),
      "the map's wild Pokemon each have one")

print("2) how each moves when you're near")
f = run.floor
f.movers = [m for m in f.movers if m.kind != "wild"]
px, py = run.player
opens = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y) and not f.occupied(x, y) and (x, y) not in f.exits]
px, py = run.player = next(t for t in opens if sum(1 for u in opens if abs(u[0] - t[0]) + abs(u[1] - t[1]) <= 4) > 30)
spot = next(t for t in opens if abs(t[0] - px) + abs(t[1] - py) == 3)
f.seen.update((x, y) for y in range(f.h) for x in range(f.w))   # (all in view)
wild = core.Mover("wild", spot[0], spot[1], p._make_wild(_rnd.Random(1)))
f.movers.append(wild)


def near_after(temper, turns=6):
    wild.x, wild.y, wild.alert, wild.temper = spot[0], spot[1], False, temper
    d0 = abs(wild.x - px) + abs(wild.y - py)
    ev = []
    for _ in range(turns):
        ev += run.others_act()
    return d0, abs(wild.x - px) + abs(wild.y - py), ev


d0, d1, ev = near_after("chase")
check(d1 < d0 or any(e[0] == "ambush" for e in ev), f"a chaser comes for you ({d0} -> {d1} tiles)")
d0, d1, ev = near_after("shy")
check(d1 >= d0 and not any(e[0] == "ambush" for e in ev), f"a shy one keeps away ({d0} -> {d1} tiles), never jumps in")
wild.x, wild.y, wild.temper = px + (1 if f.walkable(px + 1, py) else -1), py, "wander"
ev = run.others_act()
check(not any(e[0] == "ambush" for e in ev) and not wild.alert, "a wanderer beside you doesn't jump in")
f.movers.remove(wild)

print("3) shaking grass: one spot at a time, a few tiles away, gone after a few seconds; walk in and meet its Pokemon")
p = kanto("KANTO_ROUTE_1")
frames(p, 3)
p.run.floor.movers = [m for m in p.run.floor.movers if m.kind != "wild"]
grass = [(x, y) for y in range(p.run.floor.h) for x in range(p.run.floor.w) if p.run.floor.tile(x, y) == core.GRASS]
check(len(grass) > 10, f"Route 1 has tall grass ({len(grass)} tiles)")
# stand among the grass
start = next(t for t in grass if sum(1 for u in grass if 3 <= abs(u[0] - t[0]) + abs(u[1] - t[1]) <= 8) > 8 and p.run.floor.walkable(*t))
p.run.player = start
st = ambush._state(p)
st.update(next=_pg.time.get_ticks() - 1, floor=p.run.index, seen=_pg.time.get_ticks())
ambush.tick(p, _rnd.Random(3))
check(len(st["spots"]) == 1 and st["spots"][0]["kind"] == "grass", f"a patch of grass shakes ({st['spots']})")
s0 = st["spots"][0]
d = abs(s0["at"][0] - start[0]) + abs(s0["at"][1] - start[1])
check(ambush.NEAR <= d <= ambush.FAR and p.run.floor.tile(*s0["at"]) == core.GRASS, f"...in tall grass, {d} tiles from you")
check(3000 <= s0["until"] - s0["born"] <= 5000, f"...for {(s0['until'] - s0['born']) / 1000:.1f} s")
check(5000 <= st["next"] - _pg.time.get_ticks() <= 10000, f"the next one waits {(st['next'] - _pg.time.get_ticks()) / 1000:.1f} s")
ambush.tick(p)
check(len(st["spots"]) == 1, "no second one meanwhile (one at a time on a map this size)")
check(not any(m.kind == "wild" and (m.x, m.y) == tuple(s0["at"]) for m in p.run.floor.movers), "nothing shows on the spot itself")
p.draw()
_pg.image.save(g.screen, _os.path.join(SHOTS, "kanto_grass.png"))
# paused while away from the map
until0 = s0["until"]
st["seen"] -= 2000
ambush.tick(p)
check(s0["until"] >= until0 + 1900, "time away from the map (a battle, a menu) doesn't count")
# expire
s0["until"] = _pg.time.get_ticks() - 1
ambush.tick(p)
check(not st["spots"], "it fades away")
# walk into one
st.update(next=_pg.time.get_ticks() - 1)
ambush.tick(p, _rnd.Random(5))
s1 = st["spots"][0]["at"]
nb = next((s1[0] + dx, s1[1] + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)) if p.run.floor.walkable(s1[0] + dx, s1[1] + dy))
p.run.player = nb
p.mode = "MAP"
p.walk_goal = None
p.step(s1[0] - nb[0], s1[1] - nb[1])
frames(p, 40)
st2 = g.current_state
met = getattr(st2, "encounter", None) is not None or type(st2).__name__ in ("WildBattleState",) or getattr(st2, "mode", "") in ("CHOICE", "MATH", "OWWALK", "OWBATTLE")
check(met, f"stepping in: a wild Pokemon jumps out and you meet it (mode {getattr(st2, 'mode', type(st2).__name__)})")
_pg.image.save(g.screen, _os.path.join(SHOTS, "kanto_met.png"))

print("4) a cave puffs dust; each region's own generation's frames")
for area, want_gen in (("MT_MOON", 3), ("DARK_CAVE", 4)):
    if area not in g.loader.area_data["STORY_PROGRESSION"]:
        continue
    try:
        story.enter_region("KANTO" if want_gen == 3 else "JOHTO")
    except Exception:
        pass
    q = kanto(area)
    frames(q, 3)
    if not hasattr(q, "run"):
        continue
    check(ambush._kind_for(q) == "dust", f"{area}: a cave: dust puffs")
    check(ambush.gen_of(q) == want_gen, f"{area}: Gen {ambush.gen_of(q)} frames")
    stq = ambush._state(q)
    stq.update(next=_pg.time.get_ticks() - 1, floor=q.run.index, seen=_pg.time.get_ticks())
    ambush.tick(q, _rnd.Random(7))
    if stq["spots"]:
        q.draw()
        _pg.image.save(g.screen, _os.path.join(SHOTS, f"{area.lower()}_dust.png"))
    check(bool(stq["spots"]) and stq["spots"][0]["kind"] == "dust", f"{area}: a puff of dust on the cave floor")
check(all(ambush._frames(k, gen, (32, 32)) for k in ("grass", "dust", "ripple") for gen in (3, 4)), "every kind's frames load, both generations")

print("5) ripples only while you surf")
q = kanto("KANTO_ROUTE_1")
frames(q, 2)
check(ambush._kind_for(q) == "grass", "on land: grass")
fl = q.run.floor
sea = next(((x, y) for y in range(fl.h) for x in range(fl.w) if fl.tile(x, y) in (core.SURF,)), None)
if sea is None:
    q = kanto("KANTO_ROUTE_21")
    frames(q, 2)
    fl = q.run.floor
    sea = next(((x, y) for y in range(fl.h) for x in range(fl.w) if fl.tile(x, y) in (core.SURF,)), None)
if sea:
    q.run.player = sea
    check(ambush._kind_for(q) == "ripple", f"surfing: ripples ({q.area_key})")
print(f"##### {fails} failures")
