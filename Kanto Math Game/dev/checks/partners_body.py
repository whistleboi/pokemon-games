# Platinum's walking partners (src/world/walk_partners.py) and wild double battles (src/states/battle_wild_double.py),
# played on the walked Sinnoh maps the way a player meets them (11-18).
#   bash dev/checks/run_par.sh partners
import json as _json
import random as _rnd
from src.states.overworld import PlayState
from src.states.overworld.dungeon import DungeonState
from src.states.battle_double import DoubleBattleState, battle_options
from src.states.battle_wild_double import WildDoubleBattleState
from src.world import walk_partners as WP
from src.world.story_events import EVENTS as _EV
from src.states.overworld import common as _common
from src.pokemon import catching
from src.dungeon import core

fails = 0
g.dungeon_routes = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def talk(p, n=80):
    for _ in range(n):
        if not p.dialogue_box.visible:
            return
        p.dialogue_box.advance()


def click(pos):
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        ev = pygame.event.Event(kind, button=1, pos=pos)
        left = g.ui_manager.unconsumed([ev])
        if left:
            g.current_state.handle_events(left)


def route(area, came):
    story.current_area_key, story.last_area_key = area, came
    story.player_team = [mk(392), mk(25)]
    for _p in story.player_team:
        _p.level = 40
        _p.current_hp = _p.get_max_hp()
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3)
    return p


def figure(p, text):
    for i, f in enumerate(getattr(p.run, "floors", None) or [p.run.floor]):
        for m in f.movers:
            if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == text:
                return i, m
    return None, None


story.story_flags["received_starter_sinnoh"] = True
story.story_flags["starter_sinnoh"] = 390
story.enter_region("SINNOH")
_area_data = g.loader.area_data["STORY_PROGRESSION"]
_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_sp = _json.load(open("assets/dungeon_sprites.json", encoding="utf-8"))["figures"]

print("1) the five, where Platinum stands them")
for key, pt in WP.PARTNERS.items():
    area = pt["area"]
    opt = next((o for o in _area_data[area]["route_menu"] if o.get("text") == pt["figure"]), None)
    m = _tm[area]
    fls = m.get("floors") or [m]
    on = [i for i, f in enumerate(fls) if pt["figure"] in (f.get("people") or [])]
    sheet = (_sp.get(f"{area}:{pt['figure']}") or {}).get("sheet")
    check(opt is not None and opt.get("target") == f"walk_{key}" and on and sheet == pt["sheet"]
          and os.path.exists(os.path.join("assets", "dungeon", "characters", sheet)),
          f"{pt['name']}: a figure in {area} (floor {on}), talk to walk together, drawn from {sheet}")
check([WP.PARTNERS[k]["team"][0] for k in ("cheryl", "mira", "riley", "buck", "marley")] == [113, 64, 448, 344, 59]
      and [WP.PARTNERS[k]["levels"][0] for k in ("cheryl", "mira", "riley", "buck", "marley")] == [20, 26, 41, 63, 59],
      "Platinum's one Pokemon each: Chansey 20, Kadabra 26, Lucario 41, Claydol 63, Arcanine 59")

print("2) Eterna Forest: Cheryl walks with you")
p = route("ETERNA_FOREST", "SINNOH_ROUTE_205")
fi, cm = figure(p, "Cheryl")
check(isinstance(p, DungeonState) and cm is not None and abs(cm.x - p.run.player[0]) + abs(cm.y - p.run.player[1]) <= 8,
      f"Cheryl stands just inside the way in from Route 205 ({(cm.x, cm.y) if cm else None}, you at {p.run.player})")
p._use_figure(cm)
talk(p)
frames(2)
check(WP.active(story) == "cheryl" and story.story_flags.get("walk_cheryl") and p._companions() == ("Cheryl",),
      "talking to her: she walks with you")
check(figure(p, "Cheryl")[1] is None, "her standing figure steps off while she follows")
_start = p.run.player
for _d in ((0, -1), (0, -1), (1, 0), (0, -1)):
    t = (p.run.player[0] + _d[0], p.run.player[1] + _d[1])
    if p.run.floor.walkable(*t) and not p.run.floor.occupied(*t):
        p.run.player = t
        p._ctrail = [t] + p._ctrail[:3]
frames(3)
check(len(p._ctrail) == 4, "she keeps a step behind your Pokemon (the companions' trail)")

print("3) trainers while she's with you")
o_pair = battle_options({"name": "Twins", "double": True})
o_one = battle_options({"name": "Bug Catcher"})
check(o_pair.get("partner", {}).get("name") == "Cheryl" and o_pair.get("heal_after"), f"a pair: you and Cheryl against both, she heals you after ({sorted(o_pair)})")
check(not o_one.get("partner") and o_one.get("heal_after") and not o_one.get("double"), "a lone trainer: one on one, and she still heals you after")

print("4) wild Pokemon come two at a time")
_w = core.Mover("wild", p.run.player[0] + 1, p.run.player[1], mk(265))
p.run.floor.movers.append(_w)
for _q in story.player_team:
    _q.current_hp = max(1, _q.get_max_hp() // 3)
p._battle_wild(_w)
b = g.current_state
check(isinstance(b, WildDoubleBattleState) and b.trainer_class == "WILD" and len(b.opponent_team) == 2
      and [q.id for q in b.partner_team] == [113] and b.p_slots[1] is b.partner_team[0],
      f"a wild double: {[q.display_name for q in b.opponent_team]} against you and Cheryl's Chansey ({type(b).__name__})")
b.start()
frames(2)
_balls = catching.total_balls(story)
b.throw_from_bag()
check(catching.total_balls(story) == _balls and b.dialogue_box.visible and "two" in " ".join(b.dialogue_box.text_lines),
      "a ball can't be aimed while both are standing (none thrown)")
b.dialogue_box.visible = False
_foe1, _foe2 = b.o_slots[0], b.o_slots[1]
b._adjust_hp(_foe1, -99999)
_real = catching.throw
catching.throw = lambda *a, **k: (True, 3, False)
_n = len(story.player_team)
b.throw_from_bag()
catching.throw = _real
for _ in range(900):   # (tap through the lines, as a player would)
    if g.current_state is not b:
        break
    if b.dialogue_box.visible and not b.dialogue_box.is_finished:
        click(b.dialogue_box.rect.center)
    b.update()
check(any(q is _foe2 for q in story.player_team + [x for x in story.pc_pokemon if x]),
      f"one left standing: the ball works, and it's kept ({_foe2.display_name})")
check(all(q.current_hp == q.get_max_hp() for q in story.player_team if q is not _foe2) and g.current_state is not b,
      "after the battle Cheryl heals your team, and you're back on the map")

p = g.current_state if isinstance(g.current_state, DungeonState) else p
_w2 = core.Mover("wild", p.run.player[0] + 1, p.run.player[1], mk(265))
p.run.floor.movers.append(_w2)
for _q in story.player_team:
    _q.current_hp = max(1, _q.get_max_hp() // 2)
p._battle_wild(_w2)
b2 = g.current_state
b2.start()
b2.draw()
pygame.image.save(g.screen, os.path.join(S, "wild_double.png"))
for _m in list(b2.o_slots):
    b2._adjust_hp(_m, -99999)
b2._end_check()
for _ in range(900):
    if g.current_state is not b2:
        break
    if b2.dialogue_box.visible and not b2.dialogue_box.is_finished:
        click(b2.dialogue_box.rect.center)
    b2.update()
check(g.current_state is not b2 and all(q.current_hp == q.get_max_hp() for q in story.player_team),
      "both knocked out: the battle's won, Cheryl heals you, back to the map")
if isinstance(g.current_state, DungeonState):
    _pp = g.current_state
    for _ in range(6):
        _pp.update()
    _pp.draw()
    pygame.image.save(g.screen, os.path.join(S, "cheryl_follows.png"))

print("5) leaving the forest")
story.current_area_key = "ETERNA_FOREST"
said = WP.on_leave(story, "ETERNA_FOREST", "SINNOH_ROUTE_205")
check(not WP.active(story) and not story.story_flags.get("walk_cheryl_done") and said and "wait" in said[0],
      "back out to Route 205: she waits where you met her")
WP.join(story, "cheryl")
check(WP.active(story) == "cheryl", "...and walks with you again")
_bell = story.inventory.get("SOOTHE_BELL", 0)
said = WP.on_leave(story, "ETERNA_FOREST", "ETERNA_CITY")
check(story.story_flags.get("walk_cheryl_done") and story.inventory.get("SOOTHE_BELL", 0) == _bell + 1 and any("Soothe Bell" in l for l in said),
      f"out the far side: she says goodbye and gives you the Soothe Bell ({said[-2:]})")
check(not WP.active(story) and "Cheryl" not in [q.get("text") for q in p._figure_items()], "she's gone from the forest after")

print("6) Iron Island: Riley, then the Galactic pair")
p = route("IRON_ISLAND", "CANALAVE_CITY")
_ev = dict(_EV["riley_iron_island"])
_said = []
_common._run_story_event(p, dict(_ev), lambda c: bool(story.story_flags.get(c)), lambda ls: _said.append(ls))
check(g.current_state is p and story.story_flags.get("riley_iron_island_cleared") is None and _said,
      "the grunts won't battle you before Riley joins you")
_common._run_story_event(p, dict(_EV["walk_riley"]), lambda c: True, lambda ls: _said.append(ls))
check(WP.active(story) == "riley" and p._companions() == ("Team Up with Riley",), "talking to Riley: he walks with you")
bb = _common._start_event_battle(g, "IRON_ISLAND", dict(_ev["battle"]), "riley_iron_island_cleared").next_state
check(isinstance(bb, DoubleBattleState) and [q.id for q in bb.partner_team] == [448] and [q.id for q in bb.foe_teams[0]] == [41, 228, 42]
      and [q.id for q in bb.foe_teams[1]] == [431, 453, 434] and all(q.level == 34 for t in bb.foe_teams for q in t),
      "you and Riley's Lucario against two Grunts, Platinum's teams at Lv 34")
story.story_flags["riley_iron_island_cleared"] = True
check(not WP.active(story), "once the grunts are beaten, Riley's walk is over (the Riolu Egg is the battle's prize)")

print("7) Stark Mountain: Buck stops at Heatran's door")
story.story_flags["walk_buck"] = True
check(WP.on_floor(story, "STARK_MOUNTAIN", 2) == [] and WP.on_floor(story, "IRON_ISLAND", 3) == [], "nothing on other floors")
said = WP.on_floor(story, "STARK_MOUNTAIN", 3)
check(said and story.story_flags.get("walk_buck_done") and not WP.active(story, "STARK_MOUNTAIN"), "at Heatran's chamber Buck waits outside")

print("8) Wayward Cave and Victory Road")
story.story_flags["walk_mira"] = True
check(WP.on_leave(story, "WAYWARD_CAVE", "SINNOH_ROUTE_206") and story.story_flags.get("walk_mira_done"), "Mira says goodbye at the cave's mouth")
story.story_flags["walk_marley"] = True
check(WP.on_leave(story, "VICTORY_ROAD_SINNOH", "SINNOH_POKEMON_LEAGUE") and not story.story_flags.get("walk_marley_done"),
      "Marley waits if you go out to the League")
WP.join(story, "marley")
check(WP.on_leave(story, "VICTORY_ROAD_SINNOH", "SINNOH_ROUTE_224") and story.story_flags.get("walk_marley_done"), "and leaves at the way out to Route 224")
o_none = battle_options({"name": "Ace Trainer", "double": True})
check(not o_none.get("partner") and not o_none.get("heal_after"), "with nobody walking with you, battles are as before")

print(f"##### {fails} failures")
