
def menu(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if st._check_route_condition(o.get("condition"), False)
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


print("1) Isle of Armor")
story.badges = {"GALAR": ["x"] * 8}
story.story_flags, story.inventory = {"beat_galar_champion": True}, {}
story.player_team = [mk(812)]
check(not prog["ISLE_OF_ARMOR"].get("area_boss") and "891" not in g.loader.area_data["GALAR_ISLE_OF_ARMOR_PERCENTAGES"],
      "no Zarude, no wild Kubfu on the Isle of Armor")
check(prog["GLIMWOOD_TANGLE"]["area_boss"]["id"] == 893 and "Follow the Jungle Call" in menu("GLIMWOOD_TANGLE"),
      "Zarude in Glimwood Tangle after the title")
run("ISLE_OF_ARMOR", "MASTER DOJO")
run("ISLE_OF_ARMOR", "DOJO TRIAL: KLARA")
from src.world import levels
kl = lineup(battle_of(g.current_state))
check(kl[0][0] == 2023 and kl[-1][1] == levels.postgame_cap(story, story.area_region(story.current_area_key)) + 1, f"Klara's Galarian Slowbro, post-game cap levels {kl}")
story.story_flags.update({"beat_klara_dojo": True, "beat_avery_dojo": True})
run("ISLE_OF_ARMOR", "MUSTARD'S GIFT")
check(any(p.id == 891 for p in story.player_team), "Mustard gives Kubfu")
kub = next(p for p in story.player_team if p.id == 891)
kub.level = 60
said = run("ISLE_OF_ARMOR", "TOWER OF WATERS")
ur = story.player_team[-1]
check(ur.id == 8005 and ur.level == 60, f"Tower of Waters: {said[-1][-1]}")

print("2) Crown Tundra")
check("DYNA TREE HILL" not in menu("CROWN_TUNDRA"), "Dyna Tree Hill after Peony")
run("CROWN_TUNDRA", "PEONY'S EXPEDITION")
check("DYNA TREE HILL" in menu("CROWN_TUNDRA"), "Peony: on to Dyna Tree Hill")
m = menu("DYNA_TREE_HILL")
check(sum(t.startswith("SEE GALARIAN") for t in m) == 3, f"three Galarian birds: {m}")

print("3) Hisui")
std = prog["SPACE_TIME_DISTORTION"]
check(std["region"] == "SINNOH" and std["subregion"] == "HISUI", "Space-Time Distortion is in Hisui")
check(not any(o.get("target_area") == "SPACE_TIME_DISTORTION" for o in prog["SLUMBERING_WEALD"].get("route_menu", [])
              + prog["SLUMBERING_WEALD"].get("travel_options", [])), "no longer reached from Galar")
check(any(o.get("target_area") == "SPACE_TIME_DISTORTION" for o in prog["OBSIDIAN_FIELDLANDS"]["route_menu"]),
      "reached from the Obsidian Fieldlands")

print("4) Teal Mask")
story.badges = {"PALDEA": ["x"] * 8}
story.story_flags = {"beat_paldea_champion": True}
m = menu("KITAKAMI")
check("MEET CARMINE AND KIERAN" in m and "Meet the Masked Ogre" not in m, f"Kitakami start: {m}")
run("KITAKAMI", "MEET CARMINE AND KIERAN")
run("KITAKAMI", "BATTLE CARMINE")
check(isinstance(g.current_state, TrainerIntroState), "Carmine battle")
for f in ("KITAKAMI_REVELERS_ROAD_boss_defeated", "KITAKAMI_PARADISE_BARRENS_boss_defeated",
          "KITAKAMI_TIMELESS_WOODS_boss_defeated"):
    story.story_flags[f] = True
check("Meet the Masked Ogre" in menu("KITAKAMI"), "Ogerpon after the Loyal Three")
run("KITAKAMI", "BATTLE KIERAN")
kb = battle_of(g.current_state)
ace = levels.postgame_cap(story, story.area_region(story.current_area_key)) + 1
check(lineup(kb) == [(1011, ace - 3), (1012, ace - 2), (1015, ace - 1), (1017, ace)], f"Kieran with Ogerpon (post-game cap): {lineup(kb)}")

print("5) Indigo Disk")
check("Exchange to Blueberry Academy" not in travel("MESAGOZA"), "Blueberry after Kitakami")
story.story_flags["KITAKAMI_boss_defeated"] = True
check("Exchange to Blueberry Academy" in travel("MESAGOZA"), "exchange to Blueberry Academy")
check("Awaken Terapagos" not in menu("AREA_ZERO_UNDERDEPTHS"), "no Terapagos before the BB League")
story.current_area_key = "BLUEBERRY_ACADEMY"
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
check(not lobby.is_league, "BB League doesn't trigger Paldea's rematch mode")
lobby.challenge_gym()
check(lineup(battle_of(g.current_state)) == [(324, 70), (1020, 70), (609, 71), (637, 72)], "BB Elite Four: Crispin, Gouging Fire at 70")
story.story_flags["bb_league_champion"] = True
run("BLUEBERRY_ACADEMY", "Briar's Expedition")
check("Awaken Terapagos" in menu("AREA_ZERO_UNDERDEPTHS"), "Briar's expedition: Terapagos")

print("6) Visiting the new areas")
for k in ("DYNA_TREE_HILL", "BLUEBERRY_ACADEMY", "TERARIUM", "SPACE_TIME_DISTORTION", "ISLE_OF_ARMOR", "KITAKAMI"):
    try:
        state_for(k)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
no_traps(["DYNA_TREE_HILL", "TERARIUM", "SPACE_TIME_DISTORTION"])
print("FAILURES:", fails)
