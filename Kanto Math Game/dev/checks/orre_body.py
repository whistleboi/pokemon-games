
from src.states.menus import RegionSelectionState
from src.states.systems import BadgeCaseState
from src.world import levels
ORRE = [k for k, a in prog.items() if a.get("region") == "ORRE"]


def menu(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if st._check_route_condition(o.get("condition"), False)
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


print("1) A full region (Colosseum + XD, 10-27)")
story.badges = {}
story.story_flags, story.inventory = {}, {}
pick = RegionSelectionState(g, mode="new")
check("ORRE" in pick.regions, f"a new-game region: {pick.regions}")
cfg = story.get_region_start("ORRE")
check(cfg.get("starters") == [196, 197] and cfg.get("start_area") == "OUTSKIRT_STAND" and not cfg.get("travel_only"),
      "start at the Outskirt Stand with Espeon or Umbreon")
check(all(p <= 386 for p in cfg["dex_list"]), "Gen 3 or earlier")
check(25 <= len(ORRE) <= 35, f"{len(ORRE)} Orre areas")
bad = [(k, o.get("target_area")) for k in ORRE for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(sorted(k for k in ORRE if prog[k].get("wild_pool_percentages")) == ["CAVE_POKE_SPOT", "OASIS_POKE_SPOT", "ORRE_POKE_SPOTS"],
      "wild Pokemon only at the three Poke Spots (XD)")
check(sum(len(prog[k].get("shadow_pool") or []) for k in ORRE) == 131, "all 131 Shadow Pokemon")
no_traps(ORRE)
check("Air Transit to Orre" not in travel("LILYCOVE_CITY"), "no plane from Hoenn: Orre is reached like any region")
story.enter_region("ORRE")
check("ORRE" in BadgeCaseState(g, ow.CityState(g)).unlocked_regions, "a badge page for Orre's tournaments")
check(story.get_region_gym_badges("ORRE") == ["PYRITE", "UNDER", "PHENAC", "ORRE"] or
      set(story.get_region_gym_badges("ORRE")) == {"PYRITE", "UNDER", "PHENAC", "ORRE"}, "four tournament badges")
story.current_area_key = "PHENAC_CITY"
story.level_cap_mode = "OBEDIENCE"
check(levels.obey_level(story) == 20, "obedience follows Orre's badges")
story.current_area_key = "VALENCIA_ISLAND"
story.badges["ORANGE"] = []
check(levels.obey_level(story) == 20, "the Orange Islands are a full region now (10-27): obedience follows its badges")
story.level_cap_mode = "NONE"

print("2) The Snag Machine")
story.story_flags["received_starter_orre"] = True
check("Pyrite Town" not in travel("PHENAC_CITY"), "Pyrite waits for the Snag Machine")
run("PHENAC_CITY", "Trouble at the Fountain")
check(lineup(battle_of(g.current_state))[-1][1] <= 15, f"Cipher Peons at the fountain, early levels {lineup(battle_of(g.current_state))}")
story.story_flags["phenac_cipher_beaten"] = True
run("PHENAC_CITY", "Meet Rui")
check(story.inventory.get("SNAG_MACHINE") == 1 and "Pyrite Town" in travel("PHENAC_CITY"), "Rui: Snag Machine")
m = menu("ORRE_DESERT")
check(m.count("SNAG SHADOW POKEMON") == 1, f"desert: one SNAG button for its Shadow pool: {m}")
raw = g.loader.fetch_specific(9406)
check(raw["name"] == "SHADOW MAKUHITA" and raw["img"], f"Shadow form: {raw['name']}")

print("3) Purifying at the Relic Stone")
sh = Pokemon(g.loader.fetch_specific(9399), g.assets, size_mult=2.5)
sh.level, sh.moves, sh.ivs = 70, ["CRUNCH", "EARTHQUAKE"], {k: 31 for k in sh.IV_KEYS}
story.player_team = [mk(25), sh]
story.pc_pokemon = [Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5), None]
said = run("AGATE_VILLAGE", "Purify at the Relic Stone")
pm = g.current_state
check(type(pm).__name__ == "PokemonPartyMenuState", "Relic Stone: choose which Pokemon (purifying is optional)")
pm.on_select(1)
ty = story.player_team[1]
check(ty.id == 248 and ty.level == 70 and ty.moves == ["CRUNCH", "EARTHQUAKE"] and set(ty.ivs.values()) == {31},
      f"Shadow Tyranitar -> Tyranitar, same level, moves and IVs ({ty.id} Lv {ty.level})")
check(story.pc_pokemon[0].id == 9406, "a Shadow Pokemon you didn't choose stays Shadow")
said = run("AGATE_VILLAGE", "Purify at the Relic Stone")
check(type(g.current_state).__name__ != "PokemonPartyMenuState" and "None of the Pokemon" in said[-1][-1],
      "nothing in the party to purify")

print("4) Tournaments, story gates, the League and Jirachi")
for town, gate in (("PYRITE_TOWN", "got_snag_machine"), ("UNDER_COLOSSEUM", "orre_dakim_mt_battle"),
                   ("PHENAC_CITY", "orre_snattle_phenac"), ("ORRE_COLOSSEUM", "beat_gonzap")):
    req = prog[town]["gym"]["requirements"]
    check(req.get("flag") == gate, f"{town}: its tournament opens after {gate}")
story.badges["ORRE"] = ["PYRITE", "UNDER", "PHENAC"]
story.current_area_key = "REALGAM_TOWER"
c = ow.CityState(g)
g.change_state(c)
said = []
c.show_message = lambda lines, callback=None: said.append(lines)
c.start_gym_battle()
check(said and "four" in str(said[-1]), "Realgam sealed until all four tournaments")
story.badges["ORRE"].append("ORRE")
story.story_flags["xd_gorigan_beaten"] = True
story.story_flags["gym_progress_REALGAM_TOWER"] = len(prog["REALGAM_TOWER"]["gym"]["trainers"])
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check([p for p, _ in lineup(battle_of(g.current_state))] == [306, 373, 68, 212, 289, 199], "Champion Evice")
check(prog["REALGAM_TOWER"]["gym"]["leader"]["victory_flag"] == "beat_orre_champion", "Evice's defeat makes you Orre's Champion")
check("THE WISHING STAR" in menu("RELIC_FOREST") and "MEET JIRACHI" not in menu("RELIC_FOREST"), "no Jirachi yet")
story.story_flags["beat_orre_champion"] = True
run("RELIC_FOREST", "THE WISHING STAR")
check("MEET JIRACHI" in menu("RELIC_FOREST"), "after the title: Jirachi")

print("5) Visiting every Orre area")
for k in ORRE:
    try:
        state_for(k)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("FAILURES:", fails)
