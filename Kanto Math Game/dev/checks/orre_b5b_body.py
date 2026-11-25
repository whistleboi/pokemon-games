# Orre batch 5b played (11-20, kanto_handoff/orre_check/BATCH_5B.md): Krane's data to Nett, ONBS before and during the raid,
# Duking's Poke Spots and trades, Miror B. and his radar (XD's way), Exol, Bonsly's family, Kaminko's crane and the scooter,
# the S.S. Libra, Pyrite's XD duel square. bash dev/checks/run_par.sh orre_b5b
# Fateen, Agate Village, the Relic Cave and Skrub, purifying at the Relic Stone. bash dev/checks/run_par.sh orre_b2
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


exec(open("dev/checks/orre_lib.py", encoding="utf-8").read())   # (meet, _fight, route, step_into_zone, town, _note, frames, check, mine, scenes_done: shared, Checks C5)


def play(n=3000):
    quiet = 0
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "on_select", None):   # (one fainted: send in the next able)
            nxt = next((i for i, p in enumerate(story.player_team) if p and p.current_hp > 0 and p is not getattr(getattr(st, "previous_state", None), "player_pokemon", None)), 0)
            st.on_select(nxt)
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
story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "orre_miror_cave", "met_agate_elder", "orre_beat_skrub",
                                        "orre_dakim_mt_battle", "orre_time_flute", "cleared_the_under", "orre_maingate_key", "orre_ein_lab",
                                        "xd_kidnap_seen", "xd_krane_taken", "xd_lily_asked", "xd_machine_part_given", "xd_krane_rescued",
                                        "xd_lovrina_beaten", "xd_perr_asked", "kaminko_chobin", "xd_makan_back")}   # (5a done: Perr, Chobin, Makan)
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SP = g.loader.area_data["STORY_PROGRESSION"]
from src.world import miror_radar


print("1) XD's trainers in our data")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
ex = next(o for o in SP["XD_ONBS"]["route_menu"] if o["text"] == "BATTLE CIPHER CMDR EXOL")["event"]["battle"]
check(max(ex["levels"]) == 42 and len(SP["XD_ONBS"]["trainer_pool"]) == 10, f"Exol's ace 42 (Part 2's stage, L1 11-24); the raid's ten peons ({ex['levels']})")
check(max(TR["xd:Story:72"]["levels"]) == 50 and max(TR["xd:Story:128"]["levels"]) == 52, "Miror B. at the Cave 50, Smarton on the Libra 52")

print("2) Krane's data to Nett; ONBS before the raid")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Lily")
check(story.inventory.get("XD_DATA_ROM") == 1, "home again, Krane hands over his data for Nett")
p = route("XD_ONBS", "PYRITE_TOWN")
on = {m.payload[1].get("name") for f in range(4) for m in p.run.made(f).movers if m.kind == "trainer"}
check(not on, f"no Cipher in ONBS yet ({on})")
for who in ("SECC", "KANDEE", "KANDEE'S MOTHER"):
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, who)
check(F.get("xd_kandee_home") and story.inventory.get("SOOTHE_BELL"), "lost Kandee back to her mother: a Soothe Bell")
route("XD_ONBS", "PYRITE_TOWN")
meet(g.current_state, "NETT")
check(F.get("xd_nett_rom") and not story.inventory.get("XD_DATA_ROM"), "Nett takes the data, sends you to Duking")

print("3) The Poke Spots and Miror B.")
pt = SP["PYRITE_TOWN"]["travel_options"]
oasis = next(o for o in pt if o.get("target_area") == "OASIS_POKE_SPOT")["condition"]
check(not F.get(oasis), "the Oasis isn't on the map yet")
route("ORRE_POKE_SPOTS", "ORRE_DESERT")
meet(g.current_state, "DUKING AT THE ROCK")
check(F.get("xd_spot_oasis"), "Duking at the Rock: Pofty's interview, the Oasis revealed")
route("OASIS_POKE_SPOT", "PYRITE_TOWN")
meet(g.current_state, "DUKING AT THE OASIS")
check(F.get("xd_spot_cave"), "at the Oasis: the Cave revealed")
story.player_team.append(mk(194))
route("OASIS_POKE_SPOT", "PYRITE_TOWN")
meet(g.current_state, "DUKING AT THE OASIS")
lar = next((p for p in story.player_team if p and p.id == 246), None)
check(lar is not None and "DRAGON-DANCE" in lar.moves and F.get("xd_duking_larvitar"), "a Wooper traded: Duking's Larvitar, with Dragon Dance")
story.player_team = [p for p in story.player_team if p and p.id != 246]
p = route("CAVE_POKE_SPOT", "AGATE_VILLAGE")
scenes_done()
check(F.get("xd_cave_folly"), "the Cave: Folly and Trudly with their radar")
meet(g.current_state, "MIROR B. AT THE CAVE")
check(F.get("xd_miror_cave") and story.inventory.get("MIROR_RADAR") and F.get("snagged_shadow_voltorb"),
      "Miror B. beaten (Shadow Voltorb snagged); he drops the Miror B. Radar")

print("4) The radar, XD's way")
vul = next(s for s in SP["XD_ONBS"]["shadow_pool"] if "Vulpix" in s["name"])
fake = mk(vul["id"]); fake.level = 46
miror_radar.miss(g, fake)
check(miror_radar.missed(g) and miror_radar.missed(g)[0][0] == vul["flag"], "a Shadow beaten unsnagged goes to Miror B.")
spot = miror_radar.where(g)
check(spot in miror_radar.SPOTS and any("beeping" in ln for ln in miror_radar.radar_lines(g)), f"the radar says where he is today ({spot})")
p = route("XD_ONBS", "PYRITE_TOWN")
check(p._next_shadow() is None or p._next_shadow()["flag"] != vul["flag"], "it's no longer in ONBS's Snag list")
route(spot, "PYRITE_TOWN")
meet(g.current_state, "WANDERER MIROR B.")
check(F.get(vul["flag"]) and not miror_radar.missed(g), "battled at the Poke Spot: snagged back, the radar goes quiet")

print("5) The ONBS raid")
p = route("XD_ONBS", "PYRITE_TOWN")
names = [t["name"] for t in SP["XD_ONBS"]["trainer_pool"]]
for who in names:
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("duskull", "ralts", "makuhita")), "the raid's Shadows snagged (Duskull, Ralts, Makuhita)")
route("XD_ONBS", "PYRITE_TOWN")
meet(g.current_state, "BATTLE CIPHER CMDR EXOL")
check(F.get("xd_exol_beaten") and F.get("snagged_shadow_mawile"), "Exol beaten, his Shadow Mawile snagged")
for it in ("ETHER", "HP UP", "REVIVE", "BATTLE CD 21", "BATTLE CD 24", "NETT", "BONSLY'S GRANDFATHER"):
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, it)
check(story.inventory.get("HP_UP") and story.inventory.get("BATTLE_CD_21") and story.inventory.get("BATTLE_CD_24"), "ONBS's items, Battle CDs 21 and 24")
check(F.get("xd_nett_libra") and F.get("xd_bonsly_asked"), "Nett: the Libra was Cipher's; Bonsly's grandfather asks for help")

print("6) Perr's grandfather and the scooter")
gt = SP["GATEON_PORT"]["travel_options"]
libc = next(o for o in gt if o.get("target_area") == "SS_LIBRA")["condition"]
check(not F.get(libc), "the Libra's out of reach in the deep sand")
t = town("GATEON_PORT", "PYRITE_TOWN")
meet(t, "Perr")
check(F.get("xd_perr_grandpa"), "Perr: Grandpa's on Kaminko's crane floor")
route("KAMINKO_HOUSE", "GATEON_PORT")
meet(g.current_state, "CHOBIN AGAIN")
check(F.get("xd_chobin3") and story.inventory.get("SUN_STONE"), "Chobin's third battle: a Sun Stone")
for it in ("PERR'S GRANDFATHER", "BATTLE CD 05", "BATTLE CD 11", "BATTLE CD 29"):
    route("KAMINKO_HOUSE", "GATEON_PORT")
    meet(g.current_state, it)
check(F.get("xd_scooter_sand") and all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("05", "11", "29")),
      "the scooter rebuilt for deep sand; Battle CDs 05, 11 and 29 on the hook platforms")

print("7) The S.S. Libra")
route("SS_LIBRA", "GATEON_PORT", floor=2)
scenes_done()
check(F.get("xd_libra_gorigan"), "Gorigan scolds Snidle and Smarton on the bridge")
meet(g.current_state, "Cipher Peon Smarton")
check(story.is_trainer_defeated("SS_LIBRA", 0), "Smarton beaten")
for it in ("BATTLE CD 18", "IRON", "PP UPS", "MAX ETHER", "BONSLY"):
    route("SS_LIBRA", "GATEON_PORT")
    meet(g.current_state, it)
check(F.get("xd_bonsly_found") and story.inventory.get("BATTLE_CD_18") and story.inventory.get("MAX_ETHER"), "Bonsly found; the Libra's items, Battle CD 18")

print("8) Pyrite's duel square in XD's time")
for text in ("Rogue Cail", "Worker Dobit", "Chaser Finol", "Rider Dert", "Hunter Raling", "Chaser Labet", "Bodybuilder Doby"):
    t = town("PYRITE_TOWN", "XD_ONBS")
    meet(t, text)
check(all(F.get(f"xd_sq_{i}") for i in (62, 63, 64, 65, 66, 67, 68)), "the seven XD duel-square trainers")

print("9) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m11") < jm.index("orre_m11b") < jm.index("orre_m11c") < jm.index("orre_m12") < jm.index("orre_m12b") < jm.index("orre_m13"),
      "Lovrina, Nett's data, the Poke Spots, ONBS, the Libra, then Phenac")

print("10) R1 (11-23): ONBS's front door in Pyrite (Q21, Jordan's pick: the small building left of the stairs)")
_had = F.pop("xd_lovrina_beaten", None)
t = town("PYRITE_TOWN", "PHENAC_CITY")
door = [xy for xy, v in t.exits.items() if v == "XD_ONBS"]
check(len(door) == 1, f"one ONBS door in Pyrite {door}")
_msgs = []
t.flash = lambda s_, *a, **k: _msgs.append(s_)
t.player = list(door[0]); t._leave("XD_ONBS"); frames(3)
check(story.current_area_key == "PYRITE_TOWN" and any("ONBS" in m_ for m_ in _msgs), f"shut before Lovrina ({_msgs[:1]})")
F["xd_lovrina_beaten"] = True
t = town("PYRITE_TOWN", "PHENAC_CITY")
t.player = list(door[0]); t._leave("XD_ONBS")
check(getattr(g.current_state, "ride", None) is None, "walked in: no bike ride on the way")
for _ in range(300):
    st = g.current_state
    if getattr(st, "area_key", None) == "XD_ONBS" and hasattr(st, "run"):
        break
    st.update(); st.draw()
check(getattr(g.current_state, "area_key", None) == "XD_ONBS", "through the door: the ONBS lobby")
t = town("PYRITE_TOWN", "XD_ONBS")
check(abs(t.player[0] - door[0][0]) + abs(t.player[1] - door[0][1]) <= 1, f"back out at that door ({t.player})")
if _had is None:
    F.pop("xd_lovrina_beaten", None)
else:
    F["xd_lovrina_beaten"] = _had

print(f"##### {len(fails)} failures")
for f_ in fails:
    print("  ", f_)
