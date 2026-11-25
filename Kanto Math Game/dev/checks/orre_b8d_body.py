# Orre batch 8d played (11-21, kanto_handoff/orre_check/BATCH_8D.md): the Desert Trail walked (its five ways out, arriving
# from the Outskirt Stand and Phenac, its trainers), XD's Poke Snacks (Duking's first ten, the tray, the visitor after the
# steps, the Spot Monitor, battling it, eating till empty, Munchlax and the herbalist, a trainer's snack, Bonsly), the P*DA's
# four tabs (Journal, Mail, Snag List, Spot Monitor), the Journal. Screens: dev/checks/out/b8d_*.png.
# bash dev/checks/run_par.sh orre_b8d
import json as _json
from src.states.overworld import CityState as _CS, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import catching
from src.world import shadow

fails = []
g.dungeon_routes = True
g.walk_towns = True
said = []


exec(open("dev/checks/orre_lib.py", encoding="utf-8").read())   # (meet, _fight, route, step_into_zone, town, _note, frames, check, mine: shared, Checks C5)


def play(n=3000):
    quiet = 0
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "on_select", None):   # (one fainted: send in the next able)
            nxt = next((i for i, p in enumerate(story.player_team) if p and p.current_hp > 0 and p is not getattr(getattr(st, "previous_state", None), "player_pokemon", None)), 0)
            st.on_select(nxt)
            continue
        if type(st).__name__ == "EvolutionState":   # (a snagged one grew up after the battle: not now)
            st.evolve_no(); quiet = 0
            continue
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st); quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance(); quiet = 0
        elif getattr(getattr(st, "scenes", None), "playing", None):
            quiet = 0
        else:
            quiet += 1
            if quiet > 40:
                return
        st.update(); st.draw()


_MV = _json.load(open("assets/moves.json", encoding="utf-8"))

import random as _random
from src.world import poke_snacks as PS
from src.states.systems.journal import JournalState
from src.states.systems import pda as PDA

story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "move_offer_orre", "xd_nett_rom", "xd_spot_oasis",
                                        "orre_kids_grid", "xd_beluh_mail")}
F = story.story_flags
_TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))
for _a in ("ORRE_DESERT", "ORRE_POKE_SPOTS", "OASIS_POKE_SPOT", "CAVE_POKE_SPOT", "GATEON_PORT"):
    _m = _TM.get(_a) or {}
    for _f in [_m] + list(_m.get("floors") or []) + list((_m.get("rooms") or {}).values()):
        for _sc in _f.get("scenes") or []:
            if _sc.get("flag"):
                F[_sc["flag"]] = True
story.badges = {"ORRE": ["PYRITE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197)]
for p in story.player_team:
    p.level = 60
    p.heal_full()
SP = g.loader.area_data["STORY_PROGRESSION"]
shots = []


def snap(name):
    g.current_state.draw()
    g.ui_manager.draw(g.screen)
    pygame.image.save(g.screen, f"dev/checks/out/b8d_{name}.png")
    shots.append(name)


class _R:
    def __init__(self, seq): self.seq = list(seq)
    def random(self): return self.seq.pop(0) if self.seq else 0.99


print("1) The Desert Trail, walked")
t = route("ORRE_DESERT", "OUTSKIRT_STAND")
check(isinstance(t, PlayState) and hasattr(t, "run"), "the Desert Trail is a walked map now")
targets = set(t.run.floor.exits.values())
check({"OUTSKIRT_STAND", "PHENAC_CITY", "ORRE_POKE_SPOTS", "SNAGEM_HIDEOUT", "ORRE_COLOSSEUM"} <= targets, f"its five ways out ({sorted(map(str, targets))})")
px, py = t.run.player
check(px <= 3 and 10 <= py <= 15, f"from the Outskirt Stand you arrive at the west end ({t.run.player})")
snap("desert")
t = route("ORRE_DESERT", "PHENAC_CITY")
check(g.current_state.run.player[1] <= 3, f"from Phenac you arrive at the north end ({g.current_state.run.player})")
st = g.current_state
names = {m.payload.get("text") for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
trs = [m for m in st.run.floor.movers if m.kind == "trainer"]
check(len(trs) == 0, f"no trainers on the desert: neither game has any (Jordan 11-21; {len(trs)})")
# the barred ways
print("   people:", sorted(n for n in names if n))

print("2) Poke Snacks")
story.current_area_key = "ORRE_POKE_SPOTS"
t = route("ORRE_POKE_SPOTS", "ORRE_DESERT")
check(not any(m.kind == "wild" for m in t.run.floor.movers), "no snacks, no wild Pokemon at the spot")
picked = []
from src.states.systems import pick_list as _pl
_real = _pl.PickListState.__init__


def _spy(self, game, back, title, choices, done):
    _real(self, game, back, title, choices, done)
    picked.append([c[1] for c in choices])


_pl.PickListState.__init__ = _spy
said.clear()
st = g.current_state
f = st.run.floor
tray = next(m for m in f.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Snack tray")
for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    b = (tray.x + dx, tray.y + dy)
    if f.walkable(*b) and f.mover_at(*b) is None:
        st.run.player = b; st.anim = 0
        st.step(-dx, -dy)
        break
for _ in range(80):
    s_ = g.current_state
    if type(s_).__name__ == "PickListState":
        break
    _note(s_)
    if getattr(s_, "dialogue_box", None) is not None and getattr(s_.dialogue_box, "visible", False):
        s_.dialogue_box.advance()
    s_.update(); s_.draw()
check(any("Duking" in x for x in said) and story.inventory.get("POKE_SNACK", 0) == 10, "Duking's note on the first tray: 10 Poke Snacks")
check(picked and "put" in picked[0], "the tray offers PUT IN SNACKS")
g.current_state.pick("put")
play(50)
check(PS.trays(story)["ORRE_POKE_SPOTS"]["tray"] == 10 and story.inventory.get("POKE_SNACK", 0) == 0, "10 snacks on the tray")
_pl.PickListState.__init__ = _real
story.current_area_key = "ORRE_DESERT"
rng = _random.Random(3)
said_m = PS.walked(g, PS.ARRIVE - 1, rng)
check(not PS.trays(story)["ORRE_POKE_SPOTS"]["visitor"], "nothing yet before the steps are up")
for _ in range(10):
    said_m = PS.walked(g, 1, rng)
    if said_m:
        break
v = PS.trays(story)["ORRE_POKE_SPOTS"]["visitor"]
check(v and said_m and "Spot Monitor" in said_m[0], f"walking elsewhere: the Spot Monitor beeps ({said_m[:1]})")
if v and v["kind"] != "wild":
    PS.trays(story)["ORRE_POKE_SPOTS"]["visitor"] = {"id": 27, "kind": "wild", "rare": False}
t = route("ORRE_POKE_SPOTS", "ORRE_DESERT")
wild = [m for m in t.run.floor.movers if m.kind == "wild"]
check(len(wild) == 1 and int(wild[0].payload.id) in (27, 207, 328, 446), "back at the spot: the visitor is there, the only wild Pokemon")
snap("spot_visitor")
if wild:
    t._meet_wild(wild[0])   # (walked into: the map's own meeting - wild Pokemon wander, so a scripted step can miss)
    t._pick(1)   # (BATTLE)
    play(8000)
check(not PS.trays(story)["ORRE_POKE_SPOTS"]["visitor"], "battled: the visitor is gone")
check(PS.trays(story)["ORRE_POKE_SPOTS"]["tray"] > 0, "the snacks it didn't eat stay on the tray")
# eating till empty
PS.trays(story)["ORRE_POKE_SPOTS"].update(tray=3, visitor={"id": 207, "kind": "wild", "rare": True}, steps=0)
story.current_area_key = "ORRE_DESERT"
out = PS.walked(g, PS.EAT * 3, rng)
check(PS.trays(story)["ORRE_POKE_SPOTS"]["tray"] == 0 and not PS.trays(story)["ORRE_POKE_SPOTS"]["visitor"] and out,
      "it eats a snack every few steps, and leaves when they're gone")
check(PS.beeps({"rare": True}) != PS.beeps({"rare": False}), "a rare visitor beeps faster")
# Munchlax
PS.trays(story)["ORRE_POKE_SPOTS"].update(tray=6, visitor={"id": 446, "kind": "munchlax", "rare": True}, steps=0)
t = route("ORRE_POKE_SPOTS", "ORRE_DESERT")
check(not any(m.kind == "wild" for m in t.run.floor.movers), "the herbalist's Munchlax isn't a wild battle")
s = meet(t, "Snack tray")
check(F.get("munchlax_ate") and PS.trays(story)["ORRE_POKE_SPOTS"]["tray"] == 0 and any("Munchlax" in x for x in (s or [])),
      "a Munchlax gobbles the whole tray (its tag: the Gateon herb shop)")
t = town("GATEON_PORT", "ORRE_DESERT")
s = meet(t, "Herbalist")
check(story.inventory.get("POKE_SNACK", 0) == 10 and not F.get("munchlax_ate"), "the herbalist: 10 snacks back and a herb")
check(any(story.inventory.get(h) for h in ("ENERGY_POWDER", "ENERGY_ROOT", "HEAL_POWDER", "REVIVAL_HERB")), "and a herb")
n0 = story.inventory.get("POKE_SNACK", 0)
PS.trainer_reward(g, _R([0.1]))
check(story.inventory.get("POKE_SNACK", 0) == n0 + 1, "an Orre trainer beaten can leave a Poke Snack")
# Bonsly after the Libra
F["xd_bonsly_home"] = True
v = PS._choose(g, "ORRE_POKE_SPOTS", _R([0.5, 0.1]))
check(v and v["kind"] == "bonsly", "after the S.S. Libra, Bonsly can come")

print("3) The P*DA")
story.current_area_key = "PYRITE_TOWN"
F["snagged_shadow_makuhita"] = True
PS.trays(story)["OASIS_POKE_SPOT"].update(tray=4, visitor={"id": 187, "kind": "wild", "rare": False})
j = JournalState(g, g.current_state)
g.change_state(j)
frames(3)
check(j.pda and list(j.tab_buttons) == ["STORY", "SIDE", "FEATS", "mail", "snag", "monitor"], "in Orre the Quest Book is the P*DA: the book's tabs and its own three")
snap("pda_journal")
j.set_tab("mail"); frames(2)
rows = PDA.rows(g, "mail")
check(any("Beluh" in r[0] for r in rows) and any("Megg" in r[0] for r in rows), "MAIL: Megg's and Beluh's e-mails")
snap("pda_mail")
j.set_tab("snag"); frames(2)
rows = PDA.rows(g, "snag")
check(rows[0][0].startswith("Snagged 1 of") and any("Makuhita" in r[0] and "SNAGGED" in r[0] for r in rows), "SNAG LIST: every Shadow, Makuhita snagged")
snap("pda_snag")
j.set_tab("monitor"); frames(2)
rows = PDA.rows(g, "monitor")
check(len(rows) == 3 and any("4 snacks" in r[0] and "eating" in r[1] for r in rows), "SPOT MONITOR: the Oasis tray's 4 snacks and its visitor")
snap("pda_monitor")
j.set_tab("STORY"); frames(2)
check(j.tab == "STORY" and not j._pda_tab(), "back to the story")
story.current_area_key = "PALLET_TOWN"

print("3b) Fly in Orre (Jordan 11-21: after the first badge; HM Fly before it, in Pyrite)")
story.current_area_key = "PYRITE_TOWN"
t = town("PYRITE_TOWN", "ORRE_DESERT")
s = meet(t, "HM Fly")
check(story.inventory.get("HM_FLY") == 1, "HM Fly by the Pyrite Colosseum's steps")
story.badges = {"ORRE": []}
check(not story.can_fly(), "no flying before the Pyrite Badge")
story.badges = {"ORRE": ["PYRITE"]}
check(story.can_fly(), "with the Pyrite Badge, Fly works")
_dt = _TM["ORRE_DESERT"]["floors"][0]
check(not any(p == "Togepi" or p == "Shady Guy" for p in _dt.get("trainer_spots", [])), "the desert's old placeholder trainers are gone")

print("4) The Journal")
J = {x["id"]: x for x in g.loader.area_data.get("JOURNAL_MISSIONS", [])}
check("orre_s8" in J, "Poke Snacks")
print("   shots:", shots)

print(f"##### {len(fails)} failures")
for f_ in fails:
    print("  ", f_)
