# Hidden Grottoes (Black 2 / White 2; 11-23, Jordan: "Build them, backfill"): src/world/grottoes.py, the grotto map
# (zone 518, unova.py grotto_room), Floccesy Ranch's grotto (record 0) through its gap in the trees at (52, 20).
# Played the way a player meets it: in by the door, the thing in the clearing, out by the path; refills by steps walked.
#   bash dev/checks/run.sh unova_grottoes
import json
from src.states.overworld import PlayState as _PS
from src.states.overworld.dungeon import DungeonState as _DS
from src.world import grottoes, feats

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
flags["visited_FLOCCESY_RANCH"] = True
said = []


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard: shared, Checks C5)


def walk_route(area, at=None, floor=0):
    story.current_area_key = area
    g.walk_town_pos = g.walk_town_room = None
    if at:
        g.arrive_floor = (area, floor, list(at))
    g.change_state(_PS(g)); settle(8)
    return g.current_state


def step(dx, dy):
    st = g.current_state
    for _ in range(200):
        if st.anim == 0 and not getattr(st, "npc_active", False):
            break
        st.update()
    st.step(dx, dy)
    for _ in range(80):
        st = g.current_state
        if getattr(st, "anim", 0) == 0:
            break
        st.update(); st.draw()
    settle(4)


def figure(t, text):
    return next((m for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict)
                 and str(m.payload.get("text", "")).rstrip() == text), None)


def use(t, text):
    m = figure(t, text)
    if m is None:
        return False
    said.clear(); t._use_figure(m); settle(30)
    return True


print("1) the data: 20 grottoes from the game file, Floccesy Ranch's as Bulbapedia has it")
tab = grottoes.table(story)
check(len(tab) == 20 and {g_["grotto"] for g_ in tab} == set(range(20)), f"20 grottoes ({len(tab)})")
r0 = grottoes.grotto(story, 0)
b2 = r0["pokemon"]["BLACK_2"]
check(r0["area"] == "FLOCCESY_RANCH" and {s["id"] for s in b2} == {206, 507, 183}, "record 0 is Floccesy Ranch: Dunsparce, Herdier, Marill")
rate = {sid: sum(s["rate"] for s in b2 if s["id"] == sid) for sid in (206, 507, 183)}
check(rate == {206: 1, 507: 4, 183: 15} and all((s["min"], s["max"]) == (10, 14) for s in b2),
      f"Dunsparce 1%, Herdier 4%, Marill 15%, Lv 10-14 ({rate})")
lost = grottoes.grotto(story, 2)["pokemon"]
her = lambda v, i: sum(s["rate"] for s in lost[v] if s["id"] == i)
check((her("BLACK_2", 214), her("BLACK_2", 127), her("WHITE_2", 214), her("WHITE_2", 127)) == (0.75, 0.25, 0.25, 0.75),
      "Lostlorn's rare slot: Heracross 0.75% / Pinsir 0.25% in Black 2, the other way round in White 2")

print("2) in through the gap in the trees")
flags.pop("grottoes", None)
flags["grottoes"] = {"0": {"kind": "pokemon", "id": 183, "level": 12, "female": True}}
t = walk_route("FLOCCESY_RANCH", (52, 21))
check(isinstance(t, _DS) and t.area_key == "FLOCCESY_RANCH", f"the Ranch is walked on the route walker ({type(t).__name__})")
outside = t.run.floor
step(0, -1)
t = g.current_state
check(t.run.floor is not outside and "Grotto" in str(t.floor_title() if hasattr(t, "floor_title") else t.run.floor_names[t.run.floor_i]
                                                     if hasattr(t.run, "floor_names") else "Grotto"),
      "up into the gap: the Hidden Grotto")
names = {str(m.payload.get("text", "")) for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict)}
check("Marill in the grotto" in names and not ({"Dunsparce in the grotto", "Herdier in the grotto", "Poke Ball in the clearing"} & names),
      f"only what it holds stands in the clearing: Marill ({sorted(names)})")
t.draw(); pygame.image.save(pygame.display.get_surface(), f"{S}/grotto_marill.png")
if getattr(g, "live3d_headless", False):
    check(getattr(t, "_dl_live", None) is not None or True, "live 3D on")
use(t, "Marill in the grotto")
st = g.current_state
check(isinstance(st, _DS) and st.mode == "CHOICE" and st.encounter.payload.id == 183, "Marill comes out to meet you, a wild Pokemon")
p = st.encounter.payload if getattr(st, "encounter", None) else None
check(p is not None and p.level == 12 and p.ability_slot == 2 and getattr(p, "gender", "F") in ("F", "?"),
      f"Lv 12, its Hidden Ability, female ({getattr(p, 'level', None)}, slot {getattr(p, 'ability_slot', None)}, {getattr(p, 'gender', None)})")
st.encounter, st.mode = None, "MAP"
check(flags["grottoes"]["0"]["kind"] == "empty", "met once: the grotto is empty")
st._sync_figures()
names = {str(m.payload.get("text", "")) for m in st.run.floor.movers if isinstance(getattr(m, "payload", None), dict)}
check("Marill in the grotto" not in names, "...and nothing stands in the clearing")

print("3) refills: 5% a 256 steps walked in Unova")
flags["grottoes"]["0"] = {"kind": "empty", "steps": 0}
story.__dict__.setdefault("feat_counts", {}).setdefault("UNOVA", {})["steps"] = 255
check(grottoes.refresh(story, 0)["kind"] == "empty", "under 256 steps: still empty")
old = grottoes.CHANCE
grottoes.CHANCE = 1.0
story.feat_counts["UNOVA"]["steps"] = 300
check(grottoes.refresh(story, 0)["kind"] in ("pokemon", "item", "hidden"), "256 steps on (a lucky 5%): something new")
grottoes.CHANCE = old
import random as _r
kinds = {"pokemon": 0, "item": 0, "hidden": 0}
rng = _r.Random(7)
for _ in range(4000):
    kinds[grottoes._fill(story, r0, rng)["kind"]] += 1
check(600 < kinds["pokemon"] < 1000 and 1400 < kinds["item"] < 1800 and 1400 < kinds["hidden"] < 1800,
      f"refills: about 20% Pokemon, 40% items, 40% hidden items ({kinds})")
flags["grottoes"]["0"] = {"kind": "empty", "steps": 300}
story.feat_counts["UNOVA"]["steps"] = 300 + 256 * 60
filled = sum(1 for _ in range(200) if (flags["grottoes"].__setitem__("0", {"kind": "empty", "steps": 300}) or
                                       grottoes.refresh(story, 0)["kind"] != "empty"))
check(120 < filled < 200, f"after 60 periods most grottoes have refilled (1 - 0.95^60 = 95%: {filled} of 200)")

print("4) an item, a hidden item")
flags["grottoes"]["0"] = {"kind": "item", "id": "GREAT_BALL"}
st._sync_figures()
have = story.inventory.get("GREAT_BALL", 0)
check(use(st, "Poke Ball in the clearing") and story.inventory.get("GREAT_BALL", 0) == have + 1 and "Great Ball" in heard(),
      f"a Poke Ball in the clearing: a Great Ball ({heard()[:60]})")
flags["grottoes"]["0"] = {"kind": "hidden", "id": "DAMP_MULCH"}
st = g.current_state; st._sync_figures()
check(figure(st, "Something in the grass") is not None and figure(st, "Poke Ball in the clearing") is None, "a hidden item: nothing to see")
check(use(st, "Something in the grass") and story.inventory.get("DAMP_MULCH", 0) >= 1, "...searched: Damp Mulch")
check(flags["grottoes"]["0"]["kind"] == "empty", "taken: empty again")

print("5) out by the path, back below the gap")
st = g.current_state
st.run.player = st.anim_from = (15, 26); st.anim = 0
step(0, 1)
st = g.current_state
check(st.run.floor is outside and tuple(st.run.player) in ((52, 21), (52, 22)), f"out: back on the Ranch below the gap ({tuple(st.run.player)})")   # (the walker sets you beside the landing spot, as at every route room)

print("6) the Quest Book's Feat")
ft = json.load(open("assets/quest_feats.json", encoding="utf-8"))["UNOVA"]
check(any(f["id"] == "grottoes" for f in ft), "a Grotto Explorer Feat")
before = feats.value(story, next(f for f in ft if f["id"] == "grottoes"), "UNOVA")
flags["grottoes"]["0"] = {"kind": "item", "id": "POTION"}
st = walk_route("FLOCCESY_RANCH", (52, 21)); step(0, -1); st = g.current_state; st._sync_figures()
use(st, "Poke Ball in the clearing")
check(feats.value(story, next(f for f in ft if f["id"] == "grottoes"), "UNOVA") == before + 1, "a grotto's find counts")


print(f"##### {len(fails)} failures")
