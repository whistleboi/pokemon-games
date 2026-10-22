
from src.states.menus import RegionSelectionState
from src.states.systems import BadgeCaseState
from src.world import levels
ORRE = [k for k, a in prog.items() if a.get("region") == "ORRE"]


def menu(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if st._check_route_condition(o.get("condition"), False)
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


print("1) Getting there")
story.badges = {"HOENN": ["x"] * 8}
story.story_flags, story.inventory = {}, {}
check("Air Transit to Orre" not in travel("LILYCOVE_CITY"), "before the Hoenn title: no flight")
story.story_flags["beat_hoenn_champion"] = True
check("Air Transit to Orre" in travel("LILYCOVE_CITY"), "Hoenn Champion: fly from Lilycove")
check(len(ORRE) == 8, f"{len(ORRE)} Orre areas")
bad = [(k, o.get("target_area")) for k in ORRE for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(not any(prog[k].get("wild_pool_percentages") for k in ORRE), "no wild Pokemon anywhere in Orre")
no_traps(ORRE)
check("ORRE" not in RegionSelectionState(g, mode="new").regions, "not a new-game region")
story.enter_region("ORRE")
check("ORRE" not in BadgeCaseState(g, ow.CityState(g)).unlocked_regions, "no empty badge page for Orre")
story.current_area_key = "PHENAC_CITY"
story.level_cap_mode = "STORY"
check(levels.story_level_cap(story) == 100, "no level cap in Orre")
story.level_cap_mode = "OBEDIENCE"
check(levels.obey_level(story) == 100, "your team obeys you in Orre")
story.current_area_key = "VALENCIA_ISLAND"
check(levels.obey_level(story) == 100, "and in the Orange Islands")
story.level_cap_mode = "NONE"

print("2) The Snag Machine")
check("Pyrite Town" not in travel("PHENAC_CITY"), "Pyrite waits for the Snag Machine")
run("PHENAC_CITY", "Trouble at the Fountain")
check(lineup(battle_of(g.current_state))[-1] == (296, 60), "Cipher Peons at the fountain")
story.story_flags["phenac_cipher_beaten"] = True
run("PHENAC_CITY", "Meet Rui")
check(story.inventory.get("SNAG_MACHINE") == 1 and "Pyrite Town" in travel("PHENAC_CITY"), "Rui: Snag Machine")
m = menu("ORRE_DESERT")
check("SNAG SHADOW MAKUHITA" in m and "SNAG SHADOW TEDDIURSA" in m, f"desert snags: {m}")
raw = g.loader.fetch_specific(9301)
check(raw["name"] == "SHADOW MAKUHITA" and raw["img"], f"Shadow form: {raw['name']}")

print("3) Purifying at the Relic Stone")
sh = Pokemon(g.loader.fetch_specific(9312), g.assets, size_mult=2.5)
sh.level, sh.moves, sh.ivs = 70, ["CRUNCH", "EARTHQUAKE"], {k: 31 for k in sh.IV_KEYS}
story.player_team = [mk(25), sh]
story.pc_pokemon = [Pokemon(g.loader.fetch_specific(9301), g.assets, size_mult=2.5), None]
said = run("AGATE_VILLAGE", "Purify at the Relic Stone")
ty = story.player_team[1]
check(ty.id == 248 and ty.level == 70 and ty.moves == ["CRUNCH", "EARTHQUAKE"] and set(ty.ivs.values()) == {31},
      f"Shadow Tyranitar -> Tyranitar, same level, moves and IVs ({ty.id} Lv {ty.level})")
check(story.pc_pokemon[0].id == 296, "PC Shadow Pokemon purified too")
check(any("heart opened" in l for l in said[-1]), f"{said[-1][-1]}")
said = run("AGATE_VILLAGE", "Purify at the Relic Stone")
check("None of your Pokemon" in said[-1][-1], "nothing left to purify")

print("4) Cipher and Jirachi")
story.story_flags["cleared_the_under"] = True
check("Agate Village" in travel("PHENAC_CITY"), "The Under cleared: Agate open")
story.current_area_key = "REALGAM_TOWER"
c = ow.CityState(g)
g.change_state(c)
said = []
c.show_message = lambda lines, callback=None: said.append(lines)
c.start_gym_battle()
check(said and "Agate" in str(said[-1]), "Realgam sealed until the elder")
story.story_flags["met_agate_elder"] = True
story.story_flags["gym_progress_REALGAM_TOWER"] = 2
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check(lineup(battle_of(g.current_state))[-1] == (289, 72), "Cipher Head Evice")
check("THE WISHING STAR" in menu("RELIC_FOREST") and "MEET JIRACHI" not in menu("RELIC_FOREST"), "no Jirachi yet")
story.story_flags["cipher_defeated"] = True
run("RELIC_FOREST", "THE WISHING STAR")
check("MEET JIRACHI" in menu("RELIC_FOREST"), "after Cipher: Jirachi")
check("385" not in g.loader.area_data["HOENN_SKY_PILLAR_PERCENTAGES"], "Jirachi gone from Sky Pillar")

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
