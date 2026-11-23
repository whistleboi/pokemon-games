# Battle Points (Jordan 11-22: "add battle points ... implement them for all walkable regions"): won in the battle facilities,
# spent at their Exchange Service Corners (src/world/battle_points.py), and the held items the prize lists needed.
#   bash dev/checks/run.sh battle_points
from src.states.overworld import PlayState as _PS
from src.world import battle_points as bpl, frontier

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.story_flags.pop(bpl.BP_FLAG, None)

print("1) earning: a streak win, a Frontier Brain")
story.story_flags["frontier_jtower_wins"] = 0
said = frontier.after_battle(g, "jtower", True)
check(bpl.bp(story) == bpl.WIN_BP and any("BP" in l for l in said), f"a Battle Tower win: {bpl.WIN_BP} BP, and you're told ({bpl.bp(story)}, {said})")
story.story_flags["frontier_jtower_wins"] = frontier.goal(g, "jtower")
said = frontier.after_battle(g, "jtower", True)
check(bpl.bp(story) == bpl.WIN_BP + bpl.BRAIN_BP and story.story_flags.get("frontier_jtower_silver"),
      f"beating Palmer: the Silver Print and {bpl.BRAIN_BP} BP more ({bpl.bp(story)})")
before = bpl.bp(story)
frontier.after_battle(g, "jtower", False)
check(bpl.bp(story) == before, "a loss ends the streak and keeps what you'd won")

print("2) spending")
for shop in bpl.SHOPS:
    st = bpl.stock(g, shop)
    check(len(st) == len(bpl.SHOPS[shop][1]) and all(k in story.inventory or True for k, _ in st), f"{shop}: every prize found ({len(st)})")
story.story_flags[bpl.BP_FLAG] = 5
story.inventory.pop("PROTEIN", None)
line = bpl.buy(g, "PROTEIN", 1)
check(story.inventory.get("PROTEIN") == 1 and bpl.bp(story) == 4, f"a Protein for 1 BP ({line})")
line = bpl.buy(g, "CHOICE_BAND", 48)
check("need" in line and bpl.bp(story) == 4 and not story.inventory.get("CHOICE_BAND"), f"not enough BP: nothing changes hands ({line})")
tm = bpl.stock(g, "hgss_tms")[0][0]
story.story_flags[bpl.BP_FLAG] = 200
story.inventory.pop(tm, None)
bpl.buy(g, tm, 40)
line = bpl.buy(g, tm, 40)
check(story.inventory.get(tm) == 1 and bpl.bp(story) == 160 and "already" in line, f"a TM once only ({tm}: {line})")

print("3) the counters, where the games have them")
from src.states.game_corner import BPShopState


def figure_shops(key):
    story.current_area_key = key; story.story_flags["visited_" + key] = True
    g.walk_town_pos = g.walk_town_room = None
    t = _PS(g); g.change_state(t)
    found = {}
    for i in range(t.run.n_floors):   # (a place's rooms are built as you go in: step into each)
        if t.run.index != i:
            t._warp(i, 1, 1)
        for m in list(t.run.floor.movers):
            p = m.payload if isinstance(m.payload, dict) else {}
            if p.get("action") == "BP_SHOP":
                t._use_figure(m)
                st = g.current_state
                found[p.get("shop")] = type(st).__name__ == "BPShopState" and len(st.list) > 0
                g.change_state(t)
    return found


story.starting_region = "JOHTO"
j = figure_shops("JOHTO_BATTLE_FRONTIER")
check(j == {"hgss_items": True, "hgss_tms": True}, f"Johto's Frontier: the two stalls in the plaza open their prizes {j}")
story.starting_region = "HOENN"
h = figure_shops("HOENN_BATTLE_FRONTIER")
check(h == {"emerald": True}, f"Hoenn's Frontier: the Exchange Service Corner's clerk {h}")
sub = [o for o in g.loader.area_data["STORY_PROGRESSION"]["BATTLE_SUBWAY"]["route_menu"] if o.get("action") == "BP_SHOP"]
check(sorted(o["shop"] for o in sub) == ["b2w2_items", "b2w2_tms"], f"the Battle Subway's two counters {[o['shop'] for o in sub]}")
st = BPShopState(g, g.current_state, "hgss_items")
pages = st.btn_next.visible
st._turn(1)
check(pages and st.page == 1 and st.cards, f"a long list in pages of {BPShopState.PER_PAGE} ({len(st.list)} prizes)")
st.draw()

print("4) the held items the prize lists needed")
from src.pokemon import items as itemlib
from src.pokemon.data import Pokemon
mon = Pokemon(g.loader.fetch_specific(25), g.assets)
mon.evs = {}
mon.held_item = "POWER_BRACER"
got = itemlib.gain_battle_evs(g, mon, 1)   # (Bulbasaur: 1 Sp. Atk)
check(got.get("ATTACK") == 8 and got.get("SPATK") == 1, f"a Power Bracer: 8 more Attack effort points a knockout {got}")
for k in ("FOCUS_SASH", "MUSCLE_BAND", "WISE_GLASSES", "ZOOM_LENS", "LIFE_ORB", "POWER_ANKLET"):
    check(k in itemlib.HELD, f"{k} has its Bag words")
print("5) the Battle Resort's tutors at Hoenn's Frontier: Battle Points, at its prices")
from src.states.overworld.common import _tutor_teach
area = g.loader.area_data["STORY_PROGRESSION"]["HOENN_BATTLE_FRONTIER"]
tutors_ = {o["text"]: o["event"] for o in (area.get("explore_options") or []) + (area.get("route_menu") or []) if (o.get("event") or {}).get("tutor")}
check({k: v["tutor"].get("bp") for k, v in tutors_.items()} == {"Tutor Thunder Punch": 8, "Tutor Fire Punch": 8, "Tutor Ice Punch": 8, "Tutor Superpower": 16},
      f"Thunder, Fire and Ice Punch 8 BP, Superpower 16 BP {[(k, v['tutor'].get('bp')) for k, v in tutors_.items()]}")
ev = tutors_["Tutor Thunder Punch"]
pika = Pokemon(g.loader.fetch_specific(25), g.assets)
story.player_team = [pika]
from src.pokemon import tms as _tms
_tp = _tms.key_for_move(g, "THUNDER-PUNCH")
story.inventory.pop(_tp, None); story.story_flags.pop("bp_tutor_THUNDER-PUNCH", None)
story.story_flags[bpl.BP_FLAG] = 5
out = _tutor_teach(g, ev["tutor"], ev, who=pika)
check(out[0] == "\x00fail" and bpl.bp(story) == 5 and "THUNDER-PUNCH" not in pika.moves, f"5 BP: not enough, nothing taught ({out[-1]})")
story.story_flags[bpl.BP_FLAG] = 20
out = _tutor_teach(g, ev["tutor"], ev, who=pika)
from src.pokemon import moves as _mv
check(bpl.bp(story) == 12 and "THUNDER-PUNCH" in _mv.move_pool(g, pika), f"20 BP: Pikachu learns Thunder Punch, 12 BP left ({out})")
check(story.inventory.get(_tp) == 1 and story.story_flags.get("bp_tutor_THUNDER-PUNCH"), f"one payment unlocks it, like the TM: {_tp} in the Bag ({out[-1]})")
char = Pokemon(g.loader.fetch_specific(4), g.assets)   # (Charmander: Thunder Punch is a TM move for it, not a level-up one)
story.player_team = [pika, char]
check("THUNDER-PUNCH" in _mv.move_pool(g, char), "unlocked like a TM: every Pokemon that can learn it has it, no second payment")
out = _tutor_teach(g, ev["tutor"], ev, who=char)
check(bpl.bp(story) == 12 and "unlocked" in out[-1], f"the tutor again: no BP taken, it says the move is unlocked ({out[-1]})")
from src.pokemon import tutors as _tut
tm_ = _tut.tutor_event_tms(g, ev)
st = BPShopState(g, g.current_state, items=[(t, 8) for t in tm_], title="Move Tutor")
check(tm_ and st.list and st.list[0][2] == 8, f"its TM costs the same 8 BP, not money {tm_}")

print("6) Johto's Frontier trainers: Platinum / HeartGold / SoulSilver's own (Jordan 11-22)")
import os as _os
g4 = frontier.data4(g)["trainers"]
g3 = {(t["class"].rstrip("♂♀"), t["name"]) for t in frontier.data(g)["trainers"]}
check(len(g4) == 300 and not [t for t in g4 if (t["class"], t["name"]) in g3], f"300 of them, none repeating Emerald's ({len(g4)})")
check(all(_os.path.exists(_os.path.join(g.assets.assets_dir, "sprites", "trainers", t["sprite"])) for t in g4), "each with its own Platinum portrait")
names4 = {f"{t['class']} {t['name']}" for t in g4}
seen = set()
for w in (0, 10, 30, 60):
    story.story_flags["frontier_jhall_wins"] = w
    story.story_flags.pop("frontier_jhall_silver", None) if w < 5 else story.story_flags.__setitem__("frontier_jhall_silver", True)
    for _ in range(6):
        info = frontier.next_trainer(g, "jhall")
        if info.get("class") != "FRONTIER_BRAIN":
            seen.add(info["name"])
check(seen and seen <= names4, f"the Battle Hall draws only from them ({sorted(seen)[:4]})")
story.story_flags["frontier_tower_wins"] = 0
info = frontier.next_trainer(g, "tower")
check(info["name"] not in names4 or info["name"] in {f"{c} {n}" for c, n in g3}, f"Hoenn's Battle Tower keeps Emerald's ({info['name']})")

print("7) Sinnoh's Battle Frontier (Platinum's: Johto's same map, Sinnoh's own streaks; Jordan 11-22)")
story.starting_region = "SINNOH"
g.live3d_headless = True
story.current_area_key = "SINNOH_BATTLE_FRONTIER"; story.last_area_key = "FIGHT_AREA"
g.walk_town_pos = g.walk_town_room = None
t = _PS(g); g.change_state(t)
check(type(t).__name__ == "DungeonState" and "FIGHT_AREA" in {str(v) for v in t.run.floor.exits.values()},
      f"in from the Fight Area: the gate, its stairs back down ({t._floor_name(t.run.index)})")
facs, shops, live = set(), set(), []
for i in range(t.run.n_floors):
    if t.run.index != i:
        t._warp(i, 1, 1)
    for _ in range(3):   # (drawn once: the floor's look, its scene, is picked as it's drawn)
        t.update(); t.draw()
    live.append(bool(t._dl_live()))
    for m in t.run.floor.movers:
        p = m.payload if isinstance(m.payload, dict) else {}
        if p.get("action") == "FRONTIER":
            facs.add(p.get("facility"))
        if p.get("action") == "BP_SHOP":
            shops.add(p.get("shop"))
check(facs == set(frontier.SINNOH_FIVE) and shops == {"plat_items", "plat_tms"}, f"the five attendants and Platinum's two stalls {sorted(facs)} {sorted(shops)}")
check(all(live), f"every part drawn in SoulSilver's 3D (the same Frontier) {live}")
check(not [t_ for t_, _c in bpl.SHOPS["plat_tms"][1] if t_ == "TM:U-TURN"] and len(bpl.SHOPS["plat_tms"][1]) == 15, "Platinum's TMs: HGSS's without U-turn")
fl = story.story_flags
for f in frontier.SINNOH_FIVE:
    fl.pop(f"frontier_{f}_silver", None)
fl.pop("sinnoh_battle_frontier_cleared", None)
for f in frontier.SINNOH_FIVE:
    fl[f"frontier_{f}_wins"] = frontier.goal(g, f)
    said = frontier.after_battle(g, f, True)
check(fl.get("sinnoh_battle_frontier_cleared") and any("every facility" in l for l in said) and not fl.get("frontier_jtower_gold"),
      "a Silver Print from all five: the Sinnoh Frontier cleared (Johto's Prints untouched)")

print("8) the Brains' held items, the Scratch-Off, the plaza (Jordan 11-22: \"work on those still open items\")")
from src.pokemon import forms as _forms
for f in ("jtower", "stower"):
    fl.pop(f"frontier_{f}_silver", None); fl[f"frontier_{f}_wins"] = frontier.goal(g, f)
    info = frontier.next_trainer(g, f)
    team = [Pokemon(g.loader.fetch_specific(i), g.assets) for i in info["team"]]
    _forms.mark_trainer_team(team, info)
    check([p.held_item for p in team] == ["FOCUS_BAND", "SHELL_BELL", "LUM_BERRY"], f"{f}: Palmer's Silver team holds Platinum's items {[p.held_item for p in team]}")
import random as _rnd
from src.states.game_corner import ScratchOffState, scratch_result, SCRATCH_DITTO
check(scratch_result([25, 25, SCRATCH_DITTO]) == 25 and scratch_result([25, 175, 25]) is None, "a Ditto stands in for one; two kinds don't win")
story.story_flags[bpl.BP_FLAG] = 1
so = ScratchOffState(g, g.current_state, rng=_rnd.Random(1))
check(bpl.bp(story) == 0 and so.cards_left == 2 and so.card, "1 BP: three cards (the first one out)")
for _c in range(3):
    sq = so.card["squares"]
    lucky = max(set(sq), key=sq.count)
    for i in [i for i, m in enumerate(sq) if m == lucky][:3]:
        so.scratch(i)
    so.next_card()
check(len(so.won) == 3 and all(story.inventory.get(it, 0) >= n for it, n in so.won), f"three of a kind each time: its prize in the Bag {so.won}")
so2 = ScratchOffState(g, g.current_state)
check(so2.card is None and "1 BP" in so2.message, "no BP: no cards")
story.current_area_key = "JOHTO_BATTLE_FRONTIER"; story.last_area_key = "FRONTIER_ACCESS"; story.starting_region = "JOHTO"
g.walk_town_pos = g.walk_town_room = None
t = _PS(g); g.change_state(t)
fl0 = t.run.floors[0]
acts = [m.payload for m in fl0.movers if isinstance(m.payload, dict)]
check(sum(1 for a in acts if a.get("action") == "EVENT") >= 20 and any(a.get("action") == "SCRATCH_OFF" for a in acts),
      f"the plaza: its folk and the Scratch-Off clerk ({len(acts)} people)")
check(t._floor_name(t.run.index) == "Gate", f"in from Frontier Access: the gate, south ({t._floor_name(t.run.index)})")
print(f"##### {len(fails)} failures")
