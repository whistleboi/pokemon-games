# Wild Pokemon that walk up to you on a walked map (Jordan 11-23, region/systems; src/states/overworld/wild_walkup.py):
# Honey's three pop out nearby and walk up before the catch screen, which is a see-through layer over the live map;
# today's swarm calls its friends over for a three-problem battle on the map. Played through taps and keys like a player.
#   bash dev/checks/run.sh walkup
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
import datetime as _dt
import os as _os
from src.states.overworld import wild_walkup as wu
from src.world import swarms
from src.pokemon import growth
from src.pokemon.evolution import base_id

SHOTS = _os.path.join(S, "walkup")
_os.makedirs(SHOTS, exist_ok=True)
g.dungeon_routes = True
story.level_cap_mode = "NONE"   # (Exp. is shown in full: no Gym-badge cap in the way)


def shot(name):
    g.current_state.draw()
    pygame.image.save(g.screen, _os.path.join(SHOTS, name + ".png"))


def tap(pos):
    g.current_state.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos),
                                   pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)])


def key(k):
    g.current_state.handle_events([pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")])


def until(p, cond, n=900):
    for _ in range(n):
        if cond():
            return True
        frames(p)
    return cond()


def open_floor(p, n=3):
    """Clear wild Pokemon off the floor, and stand you somewhere with room round you and grass not far off."""
    f = p.run.floor
    f.movers[:] = [m for m in f.movers if m.kind not in ("wild",)]
    best = None
    for y in range(2, f.h - 2):
        for x in range(2, f.w - 2):
            if f.tile(x, y) == core.SURF or not f.walkable(x, y) or f.occupied(x, y):
                continue
            ring = [(x + dx, y + dy) for dx, dy in core.DIRS]
            if not all(f.walkable(*t) and f.tile(*t) != core.SURF and not f.occupied(*t) for t in ring):
                continue
            grass = sum(1 for yy in range(y - 6, y + 7) for xx in range(x - 6, x + 7)
                        if 4 <= abs(xx - x) + abs(yy - y) <= 6 and f.tile(xx, yy) == core.GRASS)
            if grass >= n and (best is None or grass > best[0]):
                best = (grass, (x, y))
    p.run.player = p.partner = p.partner_from = p.anim_from = best[1]
    p.anim = 0
    p.run.reveal()
    return best[1]


def walkers(p):
    return [m for m in p.run.floor.movers if m.kind == wu.WALKUP]


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------- 1) Honey: they walk up, then the catch screen
print("1) Honey on Route 1: three walk up, then the catch screen over the map")
p = kanto("KANTO_ROUTE_1")
me = open_floor(p)
story.inventory["HONEY"] = 1
from src.states.systems import BagState as _Bag
_Bag(g, p)._use_field_item("HONEY")   # (from the Bag, as a player does)
check(g.current_state is p, "HONEY from the Bag: back on the map")
talk(p)
ws = walkers(p)
check(p.mode == "WALKUP" and len(ws) == 3, f"three wild Pokemon come out on the map ({p.mode}, {len(ws)})")
check(all(getattr(m.payload, "id", 0) for m in ws), "...each a real Pokemon (its overworld sprite)")
start = {id(m): (m.x, m.y) for m in ws}
check(sum(dist(xy, me) >= 3 for xy in start.values()) >= 2, f"...most pop out a few steps away ({sorted(dist(xy, me) for xy in start.values())})")
check(sum(p.run.floor.tile(*xy) == core.GRASS for xy in start.values()) >= 2, "...out of the tall grass")
for _ in range(wu.HOP + 4):
    frames(p)
shot("1a_honey_walking_up")
key(pygame.K_RIGHT)
check(p.run.player == me, "arrow keys don't walk you off while they walk up")
check(until(p, lambda: p.mode == "CATCH", wu.WALK_LIMIT + 120), f"then the catch screen opens ({p.mode})")
check(all(dist((m.x, m.y), me) == 1 for m in ws), f"...once all three stand round you ({[(m.x, m.y) for m in ws]}, you {me})")
check(len({(m.x, m.y) for m in ws}) == 3, "...each on its own tile")
check([id(x) for x in p.p_data] == [id(m.payload) for m in ws], "the catch screen's three are the very ones that walked up")
check(all(m.motion.facing == ((me[0] > m.x) - (me[0] < m.x), (me[1] > m.y) - (me[1] < m.y)) for m in ws),
      "...and they look at you")
# the see-through layer: the map under it
p.draw()
shot("1b_catch_over_map")
dark = g.screen.copy()
p.mode = "MAP"
p._draw_rest = lambda *a, **k: None   # (just the map, to compare)
p.draw()
del p._draw_rest
plain = g.screen.copy()
p.mode = "CATCH"
spot = (p._view().x + 40, p._view().y + 40)
a, b = dark.get_at(spot), plain.get_at(spot)
check(sum(b[:3]) > 30 and 0 < sum(a[:3]) < sum(b[:3]), f"the map shows through, darker ({tuple(a[:3])} over {tuple(b[:3])})")
check(not any(e.visible for e in p.hud_buttons), "the map's MENU button is hidden while the catch screen is up")
# clicks and keys on it never reach the map
before = (p.run.player, p.walk_goal, p.mode)
for k in (pygame.K_LEFT, pygame.K_UP, pygame.K_h, pygame.K_p, pygame.K_ESCAPE):
    key(k)
tap((p._view().x + 60, p._view().centery))
tap((p._view().right - 60, p._view().bottom - 60))
check((p.run.player, p.walk_goal, p.mode) == before and g.current_state is p,
      f"taps and keys don't reach the map under it ({p.run.player}, {p.walk_goal}, {p.mode})")
# catch the middle one, by the screen's own taps
talk(p)
frames(p, 25)   # (the screen's own short wait before it takes taps)
mid = p.p_data[1]
tap((p.get_cx(1), int(p.sprite_y)))
frames(p, 30)
p.draw()
right = p.options.index(p.correct_ans)
_real_throw = catching.window_throw
catching.window_throw = lambda *a, **k: (True, 3)   # (this ball holds: the catch itself is the catch suite's)
tap(p.answer_btn_rects[right].center)
for _ in range(2000):
    if p.mode == "MAP" and not p.dialogue_box.visible:
        break
    talk(p, 3)
    frames(p)
catching.window_throw = _real_throw
got = any(x is mid for x in story.player_team + [q for q in story.pc_pokemon if q])
check(got, "a right answer catches the one you tapped")
check(p.mode == "MAP", f"after the catch screen: back on the map ({p.mode})")
check(all(m.payload is not mid for m in walkers(p)), "the one you caught is gone from the map")
left = walkers(p)
check(len(left) == 2, f"the other two are still there, running off ({len(left)})")
frames(p, 8)
shot("1c_running_off")
check(until(p, lambda: not walkers(p), wu.LEAVE_FRAMES + 60), "...and then they're gone")
check(all(m.kind != wu.WALKUP for m in p.run.floor.movers), "nothing left behind on the map")
check(sum(1 for m in p.run.floor.movers if m.kind == "wild") == 0, "and no wild ones were made instead (the map's own come back by themselves)")

print("2) Fleeing the catch screen: all three run off")
p = kanto("KANTO_ROUTE_1")
me = open_floor(p)
story.inventory["HONEY"] = 1
p.use_scent("HONEY")
talk(p)
until(p, lambda: p.mode == "CATCH", wu.WALK_LIMIT + 120)
talk(p)
frames(p, 25)
p.action_flee()
until(p, lambda: p.mode == "MAP" and not p.dialogue_box.visible, 400) or talk(p)
for _ in range(400):
    if p.mode == "MAP":
        break
    talk(p, 2)
    frames(p)
check(p.mode == "MAP" and len(walkers(p)) == 3, f"got away: all three run off ({p.mode}, {len(walkers(p))})")
check(until(p, lambda: not walkers(p), wu.LEAVE_FRAMES + 60), "...and are gone")
check(all(e.visible for e in p.hud_buttons), "the map's MENU button is back")
p.step(*next(d for d in core.DIRS if p.run.floor.walkable(me[0] + d[0], me[1] + d[1])))
check(p.run.player != me, "you walk on again")

print("3) Sweet Scent with no room round you: the catch screen still opens")
p = kanto("KANTO_ROUTE_1")
me = open_floor(p)
f = p.run.floor
blockers = []
for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
    t = (me[0] + dx, me[1] + dy)
    if f.walkable(*t) and not f.occupied(*t):
        m = core.Mover("figure", t[0], t[1], {"text": "ROCK"})
        f.movers.append(m)
        blockers.append(m)
story.player_team[0].moves = ["SCRATCH", "SWEET-SCENT"]
p.scent_floor = -1
story.inventory["HONEY"] = 0
p.use_scent()
talk(p)
check(until(p, lambda: p.mode == "CATCH", wu.WALK_LIMIT + 120) and sum(x is not None for x in p.p_data) == 3,
      f"boxed in: no one walks up, the catch screen opens with its three ({p.mode})")
for m in blockers:
    f.movers.remove(m)
p.action_flee()
for _ in range(400):
    if p.mode == "MAP":
        break
    talk(p, 2)
    frames(p)

# ---------------------------------------------------------------- 4) a swarm on the map
print("4) Today's swarm on Route 13 (Chansey, SoulSilver's): it calls its friends, and they battle you on the map")
day = next(_dt.date(2026, 1, 1) + _dt.timedelta(days=i) for i in range(400)
           if swarms.today(story, "KANTO", (_dt.date(2026, 1, 1) + _dt.timedelta(days=i)).isoformat())[0] == "KANTO_ROUTE_13")


class _Date(_dt.date):
    @classmethod
    def today(cls):
        return day


class _DT:
    date = _Date
    datetime = _dt.datetime
    timedelta = _dt.timedelta


swarms.datetime = _DT   # (the calendar on a day Route 13 has its swarm)
check(swarms.today(story, "KANTO") == ("KANTO_ROUTE_13", 113), f"on {day} the swarm is on Route 13 ({swarms.today(story, 'KANTO')})")


def swarm_route():
    p = kanto("KANTO_ROUTE_13", came="KANTO_ROUTE_12")
    story.player_team[0].level = 30
    story.player_team[0].current_hp = story.player_team[0].get_max_hp()
    me = open_floor(p)
    return p, me


def chansey_beside(p, me):
    f = p.run.floor
    d = next(dd for dd in core.DIRS if f.walkable(me[0] + dd[0], me[1] + dd[1]) and not f.occupied(me[0] + dd[0], me[1] + dd[1]))
    mon = p._swarm_mon(113)
    m = core.Mover("wild", me[0] + d[0], me[1] + d[1], mon)
    f.movers.append(m)
    return m, d


p, me = swarm_route()
check(p._swarm_today() == (113, "grass"), "Route 13 knows its swarm today")
pool = p._get_wild_pool(p.area_data)
check(abs(pool.get("113", 0) / sum(pool.values()) - 0.4) < 0.02, "...the grass table is 40% Chansey, as before")
calls = 0
for i in range(200):   # (how often one calls: about 6 in 10, so 1 meeting in 4 there; the text box closed each time)
    m = core.Mover("wild", me[0] + 1, me[1], p._swarm_mon(113))
    if p.swarm_call(m, _rnd.Random(i)):
        calls += 1
    p.dialogue_box.visible = False
    p.dialogue_box.callback = None
check(0.5 < calls / 200 < 0.7, f"a swarm Chansey calls its friends about 6 times in 10 ({calls} of 200)")
pidgey = core.Mover("wild", me[0] + 1, me[1], p._swarm_mon(16))
check(not p.swarm_call(pidgey, _rnd.Random(0)), "a Pidgey there never calls a swarm")
wu.SWARM_CALL = 1.0   # (the next ones always call)
m, d = chansey_beside(p, me)
lead = story.player_team[0]
xp0, lv0 = lead.xp, lead.level
p.step(*d)   # (bumping into it, as a player meets it)
check(p.dialogue_box.visible and any("called its friends" in l for l in p.dialogue_box.text_lines),
      f"bump a swarm Chansey: '{p.dialogue_box.text_lines[:1]}'")
talk(p)
ws = walkers(p)
check(p.mode == "WALKUP" and len(ws) == 3 and m in ws, f"two more walk up, the first one stays ({p.mode}, {len(ws)})")
check(all(x.payload.id == 113 for x in ws), "...all three Chansey")
frames(p, wu.HOP + 6)
shot("4a_swarm_walking_up")
check(until(p, lambda: p.mode == "SWARM", wu.WALK_LIMIT + 120), f"they stand round you, and the battle starts on the map ({p.mode})")
sw = p._sw
check([x.payload.level for x in sw["order"]][-1] == max(x.payload.level for x in ws),
      f"the last one standing is the highest level ({[x.payload.level for x in sw['order']]})")
check(any("swarm of CHANSEY" in l for l in p.dialogue_box.text_lines), "'A swarm of CHANSEY surrounds you!'")
talk(p)
frames(p)
check(sw["phase"] == "ASK" and len(p.options) == 3, "a math problem, three answers along the bottom")
check(not any(e.visible for e in p.hud_buttons), "the map's MENU button is hidden while they battle you")
p.draw()
shot("4b_swarm_question")
px = g.screen.get_at((p._view().x + 40, p._view().y + 40))
check(sum(px[:3]) > 30, "no dark layer: the map is clear behind the battle")
foes = list(sw["order"])
expect_half = []
for n in range(2):
    tgt = sw["order"][sw["k"]]
    right = p.options.index(p.correct_ans)
    r = p._sw_answer_rects()[right]
    tap(r.center)
    check(sw["phase"] == "HIT", f"right answer {n + 1}: your Pokemon attacks")
    frames(p, wu.ORB // 2)
    if n == 0:
        shot("4c_swarm_hit")
    until(p, lambda: p.dialogue_box.visible, 400)
    lines = list(p.dialogue_box.text_lines)
    check(tgt not in p.run.floor.movers and any("fainted" in l for l in lines), f"...and one faints: {lines[:2]}")
    gained = next((int(l.split(" gained ")[1].split()[0]) for l in lines if " gained " in l and "XP" in l), None)
    by = story.player_team[0]
    base_yield = g.assets.movesets.get(str(base_id(tgt.payload)), {}).get("base_xp") or 100
    full = growth.battle_xp(base_yield, tgt.payload.level, by.level if n == 0 else by.level)
    check(gained is not None and gained <= full * 0.5 + 2, f"...for half Exp. ({gained} of a full {full})")
    talk(p)
    frames(p)
check(sw["phase"] == "ASK" and len([x for x in sw["order"][sw["k"]:] if x in p.run.floor.movers]) == 1, "one left standing")
tap(p._sw_answer_rects()[p.options.index(p.correct_ans)].center)
check(until(p, lambda: sw["phase"] == "PICK", 200), "the third right answer: CATCH or FAINT")
last = sw["order"][-1]
check(last in p.run.floor.movers, "...the last one still stands, worn out")
p.draw()
shot("4d_swarm_pick")
balls = catching.total_balls(story)
tap(p._sw_pick_rects()[0].center)   # CATCH
lines = list(p.dialogue_box.text_lines)
check(any(" gained " in l for l in lines), f"CATCH: full Exp. first ({lines[:1]})")
talk(p)
frames(p, wu.THROW // 2)
shot("4e_swarm_throw")
for _ in range(600):
    if p.mode == "MAP" and not p.dialogue_box.visible and not p._sw:
        break
    talk(p, 3)
    frames(p)
caught = any(x is last.payload for x in story.player_team + [q for q in story.pc_pokemon if q])
check(caught and catching.total_balls(story) == balls - 1, "a sure catch: it's yours, one ball used")
check(p.mode == "MAP" and not walkers(p), f"back on the map, the swarm gone ({p.mode}, {len(walkers(p))})")
check(all(e.visible for e in p.hud_buttons), "...and the MENU button is back")

print("5) Wrong answers: the swarm hits your lead; when it faints, the swarm runs off")
p, me = swarm_route()
m, d = chansey_beside(p, me)
story.player_team.append(mk(1))   # (a second Pokemon, so no whiting out)
story.player_team[1].level = 20
story.player_team[1].current_hp = story.player_team[1].get_max_hp()
p.step(*d)
talk(p)
until(p, lambda: p.mode == "SWARM", wu.WALK_LIMIT + 120)
talk(p)
frames(p)
sw = p._sw
lead = p.lead()
hp0 = lead.current_hp
wrong = next(i for i, o in enumerate(p.options) if o != p.correct_ans)
key([pygame.K_1, pygame.K_2, pygame.K_3][wrong])
check(sw["phase"] == "HURT", "wrong answer (key): one of them attacks")
frames(p, wu.ORB // 2)
shot("5a_swarm_hurt")
until(p, lambda: p.dialogue_box.visible, 300)
check(lead.current_hp < hp0 and any("damage" in l for l in p.dialogue_box.text_lines),
      f"...your lead takes damage ({hp0} -> {lead.current_hp}: {p.dialogue_box.text_lines[:1]})")
talk(p)
frames(p)
check(sw["phase"] == "ASK", "...then a new problem")
p.math_timer = 1
frames(p, 2)
check(sw["phase"] == "HURT", "time runs out: it attacks too")
lead.current_hp = 1
sw["hp_from"] = 1
until(p, lambda: p.dialogue_box.visible, 300)
lines = list(p.dialogue_box.text_lines)
check(lead.current_hp == 0 and any("fainted" in l for l in lines) and any("ran off" in l for l in lines),
      f"your lead faints, the swarm runs off: {lines}")
talk(p)
frames(p, 4)
check(p.mode == "MAP" and len(walkers(p)) == 3, "the three run off")
check(until(p, lambda: not walkers(p), wu.LEAVE_FRAMES + 60), "...and are gone")
story.player_team = story.player_team[:1]
story.player_team[0].current_hp = story.player_team[0].get_max_hp()

print("6) FAINT the last one: full Exp., then the map")
p, me = swarm_route()
m, d = chansey_beside(p, me)
p.step(*d)
talk(p)
until(p, lambda: p.mode == "SWARM", wu.WALK_LIMIT + 120)
talk(p)
frames(p)
sw = p._sw
for n in range(3):
    until(p, lambda: sw["phase"] == "ASK", 400)
    tap(p._sw_answer_rects()[p.options.index(p.correct_ans)].center)
    until(p, lambda: p.dialogue_box.visible or sw["phase"] == "PICK", 400)
    if sw["phase"] != "PICK":
        talk(p)
        frames(p)
check(sw["phase"] == "PICK", "three right answers: the choice")
key(pygame.K_RIGHT)
key(pygame.K_RETURN)   # FAINT, by keys
until(p, lambda: p.dialogue_box.visible, 300)
lines = list(p.dialogue_box.text_lines)
check(any("fainted" in l for l in lines) and any(" gained " in l for l in lines), f"FAINT: it faints, full Exp. ({lines[:2]})")
for _ in range(400):
    if p.mode == "MAP" and not p.dialogue_box.visible:
        break
    talk(p, 3)
    frames(p)
check(p.mode == "MAP" and not walkers(p) and not p._sw, "back on the map, nobody left")

print("7) No swarm: a Chansey met there on another day is just one wild Pokemon")
swarms.datetime = _dt
p, me = swarm_route()
m, d = chansey_beside(p, me)
p.step(*d)
check(p.mode == "CHOICE" and not walkers(p), f"the usual catch-or-battle choice ({p.mode})")

print(f"##### {fails} failures")
