
from src.states import overworld as ow
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.states.systems import PokeMartState
from src.states.menus import RegionSelectionState
from src.world import levels
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]


def battle_of(st):
    return st.next_state if isinstance(st, TrainerIntroState) else st


def lineup(b):
    return [(p.id, p.level) for p in b.opponent_team]


print("1) Johto Gym Leaders and League")
story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]}
story.story_flags.update({"defeated_elder_li": True, "defeated_rival_burned_tower": True,
                          "ampharos_cured": True, "rocket_hq_cleared": True})
story.player_team = [mk(157)]
expected = {"VIOLET_CITY": [(16, 9), (17, 13)], "OLIVINE_CITY": [(81, 30), (81, 30), (208, 35)],
            "BLACKTHORN_CITY": [(148, 38), (148, 38), (130, 38), (230, 41)]}  # canon HGSS teams and levels
for area, want in expected.items():
    story.current_area_key = area
    story.story_flags[f"gym_progress_{area}"] = len(prog[area]["gym"]["trainers"])
    lobby = ow.GymLobbyState(g, None)
    g.change_state(lobby)
    lobby.challenge_gym()
    got = lineup(battle_of(g.current_state))
    check(got == want, f"{area}: {got}")
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
story.story_flags["gym_progress_SILVER_LEAGUE_PLATEAU"] = 4
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
check(lobby.is_league and "Final Match" in lobby.status_text, lobby.status_text)
lobby.challenge_gym()
got = lineup(battle_of(g.current_state))
check(got == [(130, 57), (149, 62), (149, 62), (142, 61), (6, 61), (149, 63)], f"Lance (canon HGSS +13, ace 63): {got}")

print("2) League loss resets; rematches after the title")
story.story_flags["gym_progress_SILVER_LEAGUE_PLATEAU"] = 3
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
b = TrainerBattleState(g, [mk(197)], trainer_class="ELITE_FOUR", trainer_name="Karen",
                       area_name="SILVER_LEAGUE_PLATEAU", battle_type="gym")
g.change_state(b)
b.perform_battle_black_out()
check(story.story_flags["gym_progress_SILVER_LEAGUE_PLATEAU"] == 0, "a loss starts the League over")
story.story_flags["beat_johto_champion"] = True
story.story_flags["gym_progress_SILVER_LEAGUE_PLATEAU"] = 5  # just won
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
check(lobby.progress == 0 and lobby.rematch and "Rematch" in lobby.status_text, lobby.status_text)
lobby.challenge_gym()
got = lineup(battle_of(g.current_state))
check(got[0] == (437, 58), f"Will's HGSS rematch team: {got}")
story.current_area_key = "EVER_GRANDE_CITY"
story.badges["HOENN"] = ["x"] * 8
story.story_flags["beat_hoenn_champion"] = True
story.story_flags["gym_progress_EVER_GRANDE_CITY"] = 0
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
first = lineup(battle_of((lobby.challenge_gym(), g.current_state)[1]))
story.story_flags.pop("beat_hoenn_champion")
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
plain = lineup(battle_of((lobby.challenge_gym(), g.current_state)[1]))
check([l for _, l in first] == [l + 10 for _, l in plain], f"other regions: rematch +10 levels {plain} -> {first}")

print("3) Silver")
story.story_flags = {"met_mr_pokemon": True, "starter_johto": 152}
story.badges = {"JOHTO": []}
story.current_area_key = "NEW_BARK_TOWN"
g.change_state(ow.CityState(g))
check(isinstance(g.current_state, ow.CityState), "no more New Bark ambush")
for starter, silver in ((152, 155), (155, 158), (158, 152)):
    story.story_flags = {"met_mr_pokemon": True, f"starter_johto": starter}
    story.current_area_key = "CHERRYGROVE_CITY"
    g.change_state(ow.CityState(g))
    got = lineup(battle_of(g.current_state))
    check(got == [(silver, 6)], f"Cherrygrove, you chose #{starter}: Silver has {got}")
story.story_flags = {"starter_johto": 155, "defeated_rival_cherrygrove": True}
story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN"]}
story.current_area_key = "BURNED_TOWER"
story.player_team = [mk(7)]; story.player_team[0].level = 5  # canon levels: a team that hasn't outgrown them
ps = ow.PlayState(g)
g.change_state(ps)
got = lineup(battle_of(g.current_state))
check(got == [(92, 25), (41, 25), (81, 23), (159, 28)], f"Burned Tower: {got}")
story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]}
story.current_area_key = "MT_SILVER_CITY"
g.change_state(ow.CityState(g))
got = lineup(battle_of(g.current_state))
check(got[-1] == (160, 50) and len(got) == 6, f"Victory Road: {got}")

print("4) Red")
red = next(o for o in prog["MT_SILVER"]["route_menu"] if o["text"] == "CHALLENGE RED")
story.current_area_key = "MT_SILVER"
ps = ow.PlayState(g)
g.change_state(ps)
ow._run_story_event(ps, red["event"], lambda c: True, lambda lines: None)
got = lineup(battle_of(g.current_state))
check(got == [(25, 88), (131, 80), (143, 82), (3, 84), (6, 84), (9, 84)], f"Red: {got}")

print("5) Marts")
story.badges = {"JOHTO": []}
story.current_area_key = "CHERRYGROVE_CITY"
check(PokeMartState(g, None)._shop_items()[:3] == ["POKE_BALLS", "POTION", "ANTIDOTE"]
      and "RARE_CANDY" not in PokeMartState(g, None)._shop_items(), "a first-town mart: basics, no Rare Candy")
story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN"]}
story.current_area_key = "ECRUTEAK_CITY"
items = PokeMartState(g, None)._shop_items()
check("EVERSTONE" in items and "REVIVE" in items and "RARE_CANDY" not in items, f"3 badges: {items[:6]}")
story.visited_region_set = {"JOHTO"}
story.starting_region = "JOHTO"
story.current_area_key = "GOLDENROD_CITY"
items = PokeMartState(g, None)._shop_items()
check("METAL_COAT" in items and "DAWN_STONE" not in items and "AUSPICIOUS_ARMOR" not in items,
      f"Goldenrod: Johto items only ({len(items)} items)")
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
check("RARE_CANDY" in PokeMartState(g, None)._shop_items(), "League mart sells Rare Candy")

print("6) Kanto <-> Johto")
story.visited_region_set = {"JOHTO"}
story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]}
story.story_flags = {"beat_johto_champion": True}
story.current_area_key = "NEW_BARK_TOWN"
city = ow.CityState(g)
g.change_state(city)
for _ in range(3):
    city.update()
lines = []
for e in g.ui_manager.elements:
    lines += list(getattr(e, "text_lines", []) or [])
check(story.inventory.get("SS_TICKET") == 1, "the Johto title gives an S.S. Ticket")
pick = RegionSelectionState(g, mode="move", return_state=ow.CityState(g))
check(pick.subtitles.get("KANTO") == "TRAVEL THERE", "Mom's picker: Kanto says TRAVEL THERE")
pick.selected_idx = pick.regions.index("KANTO")
pick.confirm_selection()
check(isinstance(g.current_state, ow.CityState) and story.current_area_key == "NEW_BARK_TOWN",
      "picking Kanto doesn't move house")
story.current_area_key = "OLIVINE_CITY"
st = ow._state = None
from src.states.overworld import CityState
c = CityState(g)
opt = next(o for o in prog["OLIVINE_CITY"]["travel_options"] if "S.S. Aqua" in o["text"])
check(c._check_menu_condition(opt["condition"]), "S.S. Aqua to Vermilion is open with the ticket")
seen = {}
_orig = ow.AreaTransitionState.__init__
owinit = lambda self, game, key, initial_message=None, **k: (seen.update(msg=initial_message), _orig(self, game, key, initial_message, **k))[1]
ow.AreaTransitionState.__init__ = owinit
c._get_callback_for_option(dict(opt, action="TRAVEL"))()
ow.AreaTransitionState.__init__ = _orig
check(isinstance(g.current_state, ow.AreaTransitionState) and g.current_state.next_area_key == "VERMILLION_CITY"
      and "S.S. Aqua" in str(seen.get("msg")), f"boarding message: {seen.get('msg')}")

print("7) Magnet Train quest, Red Scale, GS Ball, Shiny Charm")
story.story_flags.update({"visited_GOLDENROD_CITY": True, "visited_SAFFRON_CITY": True})
said = []
show = lambda lines: said.append(lines)


def run(area, text):
    story.current_area_key = area
    a = prog[area]
    o = next(x for x in (a.get("route_menu") or []) + (a.get("explore_options") or []) if x.get("text") == text)
    st = ow.CityState(g) if a.get("area_type") == "town" else ow.PlayState(g)
    chk = st._check_menu_condition if a.get("area_type") == "town" else (lambda c: st._check_route_condition(c, False))
    ow._run_story_event(st, o["event"], chk, show)


run("POWER_PLANT", "TALK TO THE MANAGER")
run("CERULEAN_CITY", "Search the Gym's Pool")
run("POWER_PLANT", "RETURN THE MACHINE PART")
run("VERMILLION_CITY", "Pokemon Fan Club")
run("SAFFRON_CITY", "Visit Copycat")
check(story.story_flags.get("power_plant_fixed") and story.inventory.get("PASS") == 1
      and not story.inventory.get("MACHINE_PART") and not story.inventory.get("LOST_ITEM"), "Magnet Train Pass")
story.current_area_key = "SAFFRON_CITY"
opt = next(o for o in prog["SAFFRON_CITY"]["travel_options"] if "Magnet" in o["text"])
check(ow.CityState(g)._check_menu_condition(opt["condition"]), "Magnet Train runs")
story.story_flags["defeated_red_gyarados"] = True
story.inventory.pop("EXP_SHARE", None)
run("LAKE_OF_RAGE", "PICK UP THE RED SCALE")
run("MR_POKEMONS_HOUSE", "Show the Red Scale")
check(story.inventory.get("EXP_SHARE") == 1 and not story.inventory.get("RED_SCALE"), "Red Scale -> Exp. Share")
story.current_area_key = "ILEX_FOREST"
ps = ow.PlayState(g)
cel = next(o for o in prog["ILEX_FOREST"]["route_menu"] if "CELEBI" in o["text"])
check(not ps._check_route_condition(cel["condition"], False), "no GS Ball, no Celebi")
story.inventory["GS_BALL"] = 1
check(ps._check_route_condition(cel["condition"], False), "with the GS Ball, Celebi appears")
dex = g.data.data.setdefault("pokedex", {})
dex.clear()
for pid in range(1, 251):
    dex[f"{pid}-normal"] = {"id": pid}
run("PALLET_TOWN", "Show Oak your Pokedex")
check(not story.inventory.get("SHINY_CHARM"), "250 of 251: not yet")
dex["251-normal"] = {"id": 251}
run("PALLET_TOWN", "Show Oak your Pokedex")
check(story.inventory.get("SHINY_CHARM") == 1, "all 251: Shiny Charm")
print("FAILURES:", fails)
