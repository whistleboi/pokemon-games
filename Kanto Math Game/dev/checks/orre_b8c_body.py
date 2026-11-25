# Orre batch 8c played (11-21, kanto_handoff/orre_check/BATCH_8C.md): Colosseum after the title - Nett's tip, the kid behind
# Pyrite's bookcase, Cail, the Snagem raid (missed Shadows, the coloured peons, grunts), Gurks, the Lab's peon, Biden, Agrev,
# Gonzap and the D-Disk, the Deep Colosseum's five rounds, Realgam's rematches (raised, healed), Fein, the Journal.
# bash dev/checks/run_par.sh orre_b8c
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

from src.world import xd_colosseum as XC, col_post, miror_radar
from src.states.overworld.gym_lobby import GymLobbyState

story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "has_under_badge", "has_phenac_badge", "has_orre_badge",
                                        "beat_gonzap", "xd_gorigan_beaten", "col_gonzap_realgam", "beat_orre_champion", "move_offer_orre",
                                        "orre_heard_cail", "orre_beat_cail", "orre_kids_grid", "orre_power_up_part", "met_agate_elder")}
F = story.story_flags
_TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))
for _a in ("THE_UNDER", "SNAGEM_HIDEOUT", "SHADOW_PKMN_LAB", "DEEP_COLOSSEUM", "OUTSKIRT_STAND", "PYRITE_TOWN", "REALGAM_TOWER"):
    _m = _TM.get(_a) or {}
    for _f in [_m] + list(_m.get("floors") or []) + list((_m.get("rooms") or {}).values()):   # (the places' earlier scenes: seen)
        for _sc in _f.get("scenes") or []:
            if _sc.get("flag"):
                F[_sc["flag"]] = True
F["cleared_the_under"] = True
F["orre_part2"] = True   # (story rework 11-24, Q8: Colosseum's after-game opens in Part 2, not after the title)
story.badges = {"ORRE": ["PHENAC", "PYRITE", "AGATE", "SNAGEM"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
SP = g.loader.area_data["STORY_PROGRESSION"]
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))


def team_reset(six=True):
    """The OP test team (Jordan 11-21): six Lv 100 legends, perfect IVs, full EVs, base stats tripled."""
    story.player_team = [mk(i) for i in (150, 249, 250, 384, 383, 382)]
    for p in story.player_team:
        p.level = 100
        p.base_stats = {k: v * 3 for k, v in dict(p.base_stats).items()}
        p.ivs = {k: 31 for k in p.IV_KEYS}
        p.evs = {k: 252 for k in p.IV_KEYS}
        p.heal_full()


team_reset()
# every Colosseum Shadow snagged except the ones this run looks for
for a in SP.values():
    for e in a.get("shadow_pool") or []:
        if (g.loader.area_data["SHADOW_DATA"].get(str(e["id"])) or {}).get("game") == "col":
            F[e["flag"]] = True
for f in ("snagged_shadow_yanma", "snagged_shadow_bayleef", "snagged_shadow_croconaw", "snagged_shadow_smeargle",
          "snagged_shadow_ursaring", "snagged_shadow_skarmory", "snagged_shadow_shuckle", "snagged_shadow_togetic"):
    F.pop(f, None)

print("1) The disc trainers, raised to fit")
check(max(TR["c8c:441"]["levels"]) == 72 and 9351 in TR["c8c:441"]["team"] and 9351 not in TR["c8c:442"]["team"], "Cail ~72, with and without Furret")
check(max(TR["c8c:426"]["levels"]) == 78, "Gonzap 78")
check([max(TR[f"c8c:{i}"]["levels"]) for i in (165, 214, 329, 406, 378)] == [77, 79, 81, 83, 85], "the Deep Colosseum's finals 77..85, the Deep King 85")
check(max(TR["c8c:472"]["levels"]) == 82, "Fein 82")

print("2) Nett's tip, the kid, Cail")
t = route("THE_UNDER", "PYRITE_TOWN")
check(bool(meet(t, "NETT")) and F.get("col_post_nett"), "Nett: a kid in Pyrite saw Cail with a Shadow Pokemon")
t = town("PYRITE_TOWN", "ORRE_DESERT")
check(bool(meet(t, "Kid (behind the bookcase)")) and F.get("col_post_kid"), "the kid behind the bookcase")
t = town("PYRITE_TOWN", "ORRE_DESERT")
s = meet(t, "Rogue Cail")
if not F.get("col_cail_post"):
    s = meet(g.current_state, "Rogue Cail")
check(F.get("col_cail_post") and any("Snagem" in x for x in (s or [])), "Cail (his Furret's snagged: the team without it) points to Snagem")

print("3) The Snagem raid")
t = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
names = {m.payload.get("text") for i in range(t.run.n_floors) for m in t.run.made(i).movers if m.kind == "figure" and isinstance(m.payload, dict)}
check("Cipher Peon Nore" in names, "Nore is back with the Yanma you missed")
check("Cipher Peon Skrub" not in names, "Skrub isn't (his Hitmontop was snagged)")
check("Snagem Head Gonzap" not in names, "Gonzap waits till after Gurks")
s = meet(t, "Cipher Peon Nore")
check(F.get("snagged_shadow_yanma"), "Shadow Yanma snagged from Nore")
s = meet(g.current_state, "Coloured Cipher Peon")
check(F.get("snagged_shadow_bayleef") and any("Verde" in x for x in (s or [])), "the coloured peon: Verde with the Bayleef you missed")
s = meet(g.current_state, "Team Snagem Niver")
check(F.get("col_raid_473"), "a Snagem grunt (optional) battled")

print("4) Nett again, Gurks, the Lab's peon, the late Shadows, Gonzap")
t = route("THE_UNDER", "PYRITE_TOWN")
check(bool(meet(t, "NETT")) and F.get("col_post_nett2"), "Nett: ask Gurks")
s = meet(g.current_state, "Gurks")
check(F.get("col_gurks_post") and any("lab" in x.lower() for x in (s or [])), "Gurks on the Junk Shop balcony: the peon went to the old lab")
t = route("SHADOW_PKMN_LAB", "THE_UNDER")
s = meet(t, "Coloured Cipher Peon")
check(F.get("snagged_shadow_croconaw") and any("Bluno" in x for x in (s or [])), "in the Lab where Ein was: Bluno's Croconaw snagged")
t = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
meet(t, "Snagem's Biden")
check(F.get("snagged_shadow_smeargle"), "Biden's Shadow Smeargle snagged")
meet(g.current_state, "Snagem's Agrev")
check(F.get("snagged_shadow_ursaring"), "Agrev's Shadow Ursaring snagged")
s = meet(g.current_state, "Snagem Head Gonzap")
check(F.get("snagged_shadow_skarmory") and story.inventory.get("D_DISK") == 1, "Gonzap: Shadow Skarmory snagged, the D-Disk")
lib = {e["flag"]: e for e in SP["SNAGEM_HIDEOUT"]["shadow_pool"]}
check(all(lib[f].get("event_only") for f in ("snagged_shadow_smeargle", "snagged_shadow_ursaring", "snagged_shadow_skarmory")),
      "the hideout's generic snag no longer hands out Smeargle, Ursaring or Skarmory")

print("5) Down to the Deep Colosseum")
t = route("THE_UNDER", "PYRITE_TOWN")
meet(t, "FLOATING PLATFORM")
for _ in range(400):
    if story.current_area_key == "DEEP_COLOSSEUM":
        break
    st = g.current_state
    if getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
        st.dialogue_box.advance()
    st.update(); st.draw()
check(story.current_area_key == "DEEP_COLOSSEUM", "the D-Disk sinks the platform to the Deep Colosseum")
t = route("DEEP_COLOSSEUM", "THE_UNDER")
check(not any(m.kind == "trainer" for m in t.run.floor.movers), "no standing trainers: the desk runs the rounds")
F["snagged_shadow_sudowoodo"] = True   # (Miror B.'s Sudowoodo snagged long ago: his team without it)
picked_ok = []
for r in range(1, 6):
    for _try in range(4):
        if XC.cleared(story, {"cleared": "col_deep_cleared"}) >= r:
            break
        team_reset()
        if not isinstance(g.current_state, PlayState):
            t = route("DEEP_COLOSSEUM", "THE_UNDER")
        st = g.current_state
        f = st.run.floor
        desk = next((m for m in f.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Deep Colosseum desk"), None)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (desk.x + dx, desk.y + dy)
            if f.walkable(*b) and f.mover_at(*b) is None:
                st.run.player = b; st.anim = 0
                st.step(-dx, -dy)
                break
        for _ in range(60):
            st = g.current_state
            if type(st).__name__ == "PickListState":
                break
            if getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
                st.dialogue_box.advance()
            st.update(); st.draw()
        offered = [v for _l, v in getattr(st, "choices", [])]
        picked_ok.append(r in offered)
        if r not in offered:
            break
        st.pick(r)
        play(30000)
    print("   deep round", r, "cleared", XC.cleared(story, {"cleared": "col_deep_cleared"}))
check(all(picked_ok), "each round offered once the one before is won")
check(F.get("col_deep_all"), "all five Deep Colosseum rounds won")
check(story.inventory.get("TM098") and story.inventory.get("TM078"), "rounds 2 and 4: TM Skill Swap, TM Dragon Claw")
check(F.get("snagged_shadow_shuckle"), "the Deep King's Shadow Shuckle snagged")

print("6) Realgam: the door down is shut")
room = g.town_maps["REALGAM_TOWER"]["rooms"]["realgam"] if hasattr(g, "town_maps") else _json.load(open("assets/town_maps.json", encoding="utf-8"))["REALGAM_TOWER"]["rooms"]["realgam"]
check(any("no handle" in " ".join(b.get("lines", [])) for b in room.get("barred", [])), "Realgam's door to the Deep Colosseum is shut")
# (the old lobby-screen rematch of Evice's run, healed and raised to fit after the title - retired 11-24: after the title
#  Realgam's Colosseum is the Orre League (story rework S5, gym_swaps), and League rematches don't rise to your level
#  (Jordan 11-21). The League's rematch is on ROADMAP_ORRE R6.)

print("7) Fein")
team_reset()
check(col_post.fein_due(g), "every other Colosseum Shadow snagged: Fein is due")
t = town("OUTSKIRT_STAND", "ORRE_DESERT")
s = meet(t, "Shady man")
check(F.get("snagged_shadow_togetic") and any("Fein" in x for x in (s or [])), "the shady man is Cipher Peon Fein: Shadow Togetic snagged")
lib = next(e for e in SP["ORRE_DESERT"]["shadow_pool"] if e["flag"] == "snagged_shadow_togetic")
check(lib.get("event_only"), "Togetic isn't in the desert's generic snag any more")

print("8) Missed Colosseum Shadows don't go to Miror B.")
story.inventory["MIROR_RADAR"] = 1
F["miror_b_missed"] = []
x = mk(9366); x.level = 40; shadow.make_shadow(g, x)
F.pop("snagged_shadow_yanma", None)
miror_radar.miss(g, x)
check(not miror_radar.missed(g), "a missed Colosseum Shadow stays for the Snagem raid")
F["snagged_shadow_yanma"] = True

print("9) The Journal")
J = {j["id"]: j for j in g.loader.area_data.get("JOURNAL_MISSIONS", [])}
check(all(k in J for k in ("orre_s7", "orre_s7b", "orre_s7c")), "Nett's rumour, the Snagem raid, the Deep Colosseum")

print(f"##### {len(fails)} failures")
for f in fails:
    print("  ", f)
