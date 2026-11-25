# Orre batch 6 played (11-21, kanto_handoff/orre_check/BATCH_6.md): the Pre Gym's Colosseum era, Cipher's Phenac (gate lady, Music
# Disc, the secretary, Es Cade's note, the fake Justys, the Pre Gym, the stadium, Snattle, the townsfolk freed), the Stadium's
# tournament gate, the Outskirt Stand (Miror B., Hordel's Shadow Togepi, Willie), XD's Snagem Hideout. bash dev/checks/run_par.sh orre_b6
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
                                        "orre_power_on", "has_pyrite_badge", "phenac_cipher_beaten")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SP = g.loader.area_data["STORY_PROGRESSION"]


def pg(floor=0):
    p = route("PRESTIGE_PRECEPT_CENTER", "PHENAC_CITY", floor=floor)
    scenes_done()
    return g.current_state


print("1) The disc's trainers, raised to fit")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
sn = next(o for o in SP["PHENAC_CITY"]["explore_options"] if o["text"] == "PHENAC STADIUM: SNATTLE")["event"]["battle"]
gz = next(o for o in SP["SNAGEM_HIDEOUT"]["route_menu"] if o["text"] == "SNAGEM HIDEOUT: GONZAP")["event"]["battle"]
gym = SP["PHENAC_CITY"]["gym"]
check(max(sn["levels"]) == 43 and max(gz["levels"]) == 44 and max(gym["leader"]["levels"]) == 14,
      f"Snattle 43, Gonzap 44 (Part 2's stage, L1 11-24) and the Stadium's Leader Misty 14 (S2) ({max(sn['levels'])}, {max(gz['levels'])}, {max(gym['leader']['levels'])})")
check([t["name"] for t in gym["trainers"]] == ["Cooltrainer Rewn", "Cooltrainer Buna", "Teacher Holen", "Teacher Glais"] and gym["requirements"].get("flag") == "got_snag_machine",
      "the Stadium: Rewn, Buna, Holen and Glais, then Misty - open once you can snag (Phenac first, S2 11-24)")

print("2) The Pre Gym, Colosseum's era")
for who in ("COOLTRAINER BOTAN", "COOLTRAINER LIQUI", "RICH BOY DUGO", "LADY GWIN"):
    pg()
    meet(g.current_state, who)
check(all(F.get(f"orre_pregym_{n}") for n in ("botan", "liqui", "dugo", "gwin")), "its four students")
F["orre_under_colosseum_won"] = True   # (Justy's Colosseum battle waits for the Under Colosseum now: 11-24)
pg()
meet(g.current_state, "PRE GYM LEADER JUSTY")
check(F.get("orre_justy_col"), "Justy, after the Under Colosseum (Colosseum's)")
p = pg()
on = {m.payload[1].get("name") for m in p.run.floor.movers if m.kind == "trainer"}
check(not on, f"no Cipher in the Pre Gym yet ({on})")

print("3) Cipher's Phenac")
for f in ("orre_dakim_mt_battle", "orre_time_flute", "cleared_the_under", "orre_ein_lab", "xd_lovrina_beaten", "xd_miror_cave",
          "xd_exol_beaten", "xd_bonsly_found", "has_under_badge"):
    F[f] = True
t = town("PHENAC_CITY", "ORRE_DESERT")
meet(t, "Gate lady")
check(all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("01", "07", "20")), "the gate lady's Battle CDs 01, 07, 20")
t = town("PHENAC_CITY", "ORRE_DESERT")
said_s = meet(t, "Mayor's secretary") or []
check(not F.get("xd_secretary"), "the secretary won't let you upstairs")
t = town("PHENAC_CITY", "ORRE_DESERT")
meet(t, "Music lover")
t = town("PHENAC_CITY", "ORRE_DESERT")
meet(t, "Mayor's secretary")
check(F.get("xd_secretary") and any("The mayor is nowhere" in ln for ln in said), "the Music Disc; upstairs, the mayor's note (Part 2's mayor, unnamed) - and the secretary is a peon")
t = town("PHENAC_CITY", "ORRE_DESERT")
meet(t, "Cipher Peon Fenton")
for h in ("Resix", "Blusix", "Browsix", "Yellosix", "Purpsix", "Greesix"):
    t = town("PHENAC_CITY", "ORRE_DESERT")
    meet(t, f"'Justy' ({h})")
check(all(F.get(f"xd_impostor_{h.lower()}") for h in ("resix", "blusix", "browsix", "yellosix", "purpsix", "greesix"))
      and all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("19", "08", "16", "28")),
      "the six fake Justys unmasked; their Battle CDs 19, 08, 16, 28")
for n in ("12", "27", "32", "10"):
    t = town("PHENAC_CITY", "ORRE_DESERT")
    meet(t, f"Battle CD {n}")
check(all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("12", "27", "32", "10")), "Battle CDs 12, 27, 32 (mayor's) and 10")
p = pg()
names = [t_["name"] for t_ in SP["PRESTIGE_PRECEPT_CENTER"]["trainer_pool"]]
for who in names:
    pg()
    meet(g.current_state, who)
pg()
meet(g.current_state, "CIPHER PEON FOSTIN")
check(F.get("xd_fostin") and all(F.get(f"snagged_shadow_{n}") for n in ("swinub", "natu", "roselia", "meowth")),
      "the Pre Gym's peons and Fostin; Shadow Swinub, Natu, Roselia, Meowth snagged")
p = pg()
bar = p.run.recipe["art"]["floors"][0]["barred"][-1]
check(not p._until_met(bar["until"]), "the lift to the basement is locked")
t = town("PHENAC_CITY", "PRESTIGE_PRECEPT_CENTER")
meet(t, "Cipher Peon Ertlig")
for who in ("Cipher Peon Exinn", "Cipher Peon Gonrag", "Cipher Peon Ezin", "Cipher Peon Faltly", "Cipher Peon Egrog"):
    t = town("PHENAC_CITY", "PRESTIGE_PRECEPT_CENTER")
    meet(t, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("snorunt", "pineco", "spearow", "grimer", "seel")), "the stadium's peons; five more Shadows")
t = town("PHENAC_CITY", "PRESTIGE_PRECEPT_CENTER")
meet(t, "PHENAC STADIUM: SNATTLE")
check(F.get("orre_snattle_phenac") and F.get("snagged_shadow_lunatone"), "Snattle beaten (Shadow Lunatone); he drops the Elevator Key")
p = pg()
check(p._until_met(bar["until"]), "the lift goes down now")
pg(1)
said_t = meet(g.current_state, "PHENAC'S TOWNSFOLK") or []
pg(1)
meet(g.current_state, "BATTLE CD 35")
check(F.get("xd_pregym_freed") and story.inventory.get("BATTLE_CD_35") and any("The mayor? He wasn't with us" in ln for ln in said_t), "the townsfolk freed (the mayor's back, unharmed); CD 35")
F["orre_under_colosseum_won"] = True   # (Justy's Colosseum battle waits for the Under Colosseum now: 11-24)
pg()
meet(g.current_state, "PRE GYM LEADER JUSTY")
check(F.get("xd_justy") and story.inventory.get("TM275") and story.inventory.get("LUM_BERRY"), "XD's Justy: TM275 Double Team and a Lum Berry")
for it in ("Battle CD 44", "Runner's Castform", "Fun Old Man Eroll", "Cooltrainer Equin", "Cooltrainer Quelor", "Cooltrainer Teslor",
           "Supertrainer Nopel", "Matron Kalus"):
    t = town("PHENAC_CITY", "PRESTIGE_PRECEPT_CENTER")
    meet(t, it)
check(story.inventory.get("BATTLE_CD_44") and story.inventory.get("BATTLE_CD_15") and all(F.get(f"xd_ph_{i}") for i in (105, 106, 129, 130, 131, 132)),
      "Battle CDs 44 and 15; Phenac's XD trainers, back to normal")

print("4) The Outskirt Stand")
story.badges["ORRE"].append("PHENAC")
for who in ("Wanderer Miror B.", "Researcher Hordel", "Rider Willie (again)"):
    t = town("OUTSKIRT_STAND", "PHENAC_CITY")
    meet(t, who)
tog = next((p for p in list(story.player_team) + list(story.pc_pokemon or []) if p and p.id == 9357), None)
check(F.get("xd_miror_outskirt") and F.get("snagged_shadow_nosepass"), "Miror B. again: Shadow Nosepass snagged")
check(tog is not None and story.is_shadow(tog) and tog.shadow and tog.shadow["gauge"] > 0,
      "Hordel hands over his Shadow Togepi, its heart shut")
check(F.get("xd_hordel") and F.get("xd_willie_again"), "Hordel marks the Snagem Hideout; Willie's rematch")

print("5) The Snagem Hideout (XD's)")
gate = next(o for o in SP["ORRE_DESERT"]["route_menu"] if o.get("target_area") == "SNAGEM_HIDEOUT")["condition"]
check("xd_hordel" in str(gate), "the hideout's on the map once Hordel has pointed it out")
names = [t_["name"] for t_ in SP["SNAGEM_HIDEOUT"]["trainer_pool"]]
check(len(names) == 9 and "Team Snagem Wakin" in names, f"XD's nine Snagem members ({len(names)})")
for who in names:
    route("SNAGEM_HIDEOUT", "ORRE_DESERT")
    meet(g.current_state, who)
F["orre_part2"] = True   # (Part 2: Gonzap in the ruins' hall where Pryce stood in Part 1 - S2/S5 11-24)
route("SNAGEM_HIDEOUT", "ORRE_DESERT")
meet(g.current_state, "SNAGEM HIDEOUT: GONZAP")
check(F.get("beat_gonzap") and story.inventory.get("GONZAPS_KEY"), "Gonzap beaten; his key")
for it in ("LOCKED BOX", "ULTRA BALLS", "HYPER POTIONS", "REVIVES", "RARE CANDY", "PP UP", "TM PSYCHIC", "FULL HEALS"):
    route("SNAGEM_HIDEOUT", "ORRE_DESERT")
    meet(g.current_state, it)
check(story.inventory.get("TM114") and story.inventory.get("TM120"), "the locked box's TM114 Shadow Ball; TM120 Psychic and the hideout's items")

print("6) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m13") < jm.index("orre_m13b") < jm.index("orre_m14") < jm.index("orre_m14b") < jm.index("orre_m15"),
      "Cipher's Phenac, the townsfolk, the Stadium, Hordel, the Snagem Hideout")

print(f"##### {len(fails)} failures")
for f_ in fails:
    print("  ", f_)
