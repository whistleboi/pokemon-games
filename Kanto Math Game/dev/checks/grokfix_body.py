
import random
from src.states.battle import WildBattleState, TrainerBattleState
from src.world import levels

story.badges = {"KANTO": [], "JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL"]}
story.story_flags = {"received_starter_johto": True, "starter_johto": 155}
story.current_area_key = "NEW_BARK_TOWN"
team = [mk(160), mk(166), mk(93)]
for p in team:
    p.level = 50
    p.caught_region = "JOHTO"
team[0].caught_region = None
story.player_team = list(team)

print("1.1) the shiny Red Gyarados")
story.story_flags.update({"rocket_hq_cleared": False, "lance_met": True})
st = state_for("LAKE_OF_RAGE")
try:
    st.action_challenge_boss(dict(prog["LAKE_OF_RAGE"]["area_boss"], lines=None))
    b = g.current_state
    check(isinstance(b, WildBattleState) and b.opponent_pokemon.is_shiny and b.opponent_pokemon.id == 130,
          "Red Gyarados battle starts (no crash), shiny")
except Exception as e:
    check(False, f"Red Gyarados: {type(e).__name__} {e}")

print("1.2) the road to the League keeps the team")
story.current_area_key = "NEW_BARK_TOWN"
for area in ("KANTO_ROUTE_27", "TOHJO_FALLS", "KANTO_ROUTE_26", "POKEMON_LEAGUE_GATE", "MT_SILVER_CITY"):
    t = ow.AreaTransitionState(g, area)
    story.current_area_key = t.next_area_key
    check(t.next_area_key == area and len(story.player_team) == 3 and story.get_current_region() == "JOHTO",
          f"{area}: team of {len(story.player_team)}, region {story.get_current_region()}")
story.current_area_key = "KANTO_ROUTE_27"
b = TrainerBattleState(g, [mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name="KANTO_ROUTE_27")
check(len(story.player_team) == 3 and not any(p for p in story.pc_pokemon), "a battle on Route 27 boxes nobody")

print("1.3) Radio Tower: cleared over two visits, you can still leave")
story.current_area_key = "RADIO_TOWER"
for i in range(len(prog["RADIO_TOWER"]["trainer_pool"])):
    story.mark_trainer_defeated("RADIO_TOWER", i)
st = state_for("RADIO_TOWER")
st.rounds_completed = 0
exit_opt = next(o for o in prog["RADIO_TOWER"]["route_menu"] if o["action"] == "EXIT")
check(st._check_route_condition(exit_opt["condition"], False), "every trainer beaten: the exit is there")
st2 = state_for("JOHTO_ROUTE_29")
st2.rounds_completed = 0
check(not st2._check_route_condition("can_exit", False), "wild routes still ask for their rounds")

print("1.4) Silver League Plateau has exits")
check({o["target_area"] for o in prog["SILVER_LEAGUE_PLATEAU"]["travel_options"]} == {"MT_SILVER_CITY", "POKEMON_LEAGUE_GATE"},
      "back to Mt. Silver City or the Gate")

print("1.5) no balls: no catch screen")
st = state_for("JOHTO_ROUTE_29")
story.balls_left = 0
st.trigger_wild_encounter()
check(not st.catch_selection_active and "no" in " ".join(st.dialogue_box.text_lines).lower(), f"{st.dialogue_box.text_lines}")

print("2.1) bought balls stay bought")
story.balls_left = 0
st = state_for("JOHTO_ROUTE_29")
story.balls_left += 30  # bought in town
again = ow.PlayState(g, restore_data={"balls_left": 0, "current_streak": 0, "rounds_completed": 1})
check(again.balls_left == 30 and story.balls_left == 30, f"a revisited route keeps them ({again.balls_left})")
again.balls_left -= 1
check(story.balls_left == 29, "throwing one uses the one count")

print("2.2) League prizes")
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
e4 = TrainerBattleState(g, [mk(178)], trainer_class="ELITE_FOUR", trainer_name="Will", area_name="SILVER_LEAGUE_PLATEAU",
                        battle_type="gym")
e4.opponent_team[0].level = 53
champ = TrainerBattleState(g, [mk(149)], trainer_class="CHAMPION", trainer_name="Lance", area_name="SILVER_LEAGUE_PLATEAU",
                           battle_type="gym")
champ.opponent_team[0].level = 63
check(e4._calc_money_reward() == 5300 and champ._calc_money_reward() == 12600,
      f"E4 {e4._calc_money_reward()}, Champion {champ._calc_money_reward()} (was 25,000+ and 50,000)")

print("2.3) Johto missions")
ms = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}
check(ms["johto_m17"]["condition"]["flag_not"] == "beat_johto_champion" and "beat_johto_champion" in ms["johto_m18"]["condition"]["flag"],
      "League missions use the Johto title")

print("1.6 / 3.1) roaming beasts")
story.current_area_key = "JOHTO_ROUTE_36" if "JOHTO_ROUTE_36" in prog else "JOHTO_ROUTE_37"
story.story_flags["visited_BURNED_TOWER"] = True
story.balls_left = 10
st = state_for(story.current_area_key)
g.data.data.setdefault("pokedex", {}).clear()
random.seed(1)
_orig = random.random
random.random = lambda: 0.0
try:
    fired = st.check_roaming_encounter()
finally:
    random.random = _orig
b = g.current_state
lv = levels.legendary_encounter_level(g, story.current_area_key)  # Jordan: cap + 3 before the last badge, then 70
check(fired and isinstance(b, WildBattleState) and b.opponent_pokemon.level == lv,
      f"roamer Lv {b.opponent_pokemon.level} = legendary rule {lv} (was 50)")
pid = b.opponent_pokemon.id
b.trigger_outro(True)
check(b.phase == "CATCH_PROMPT", "beating it offers a catch")
b.catch_yes()
for _ in range(200):
    if b.phase == "OUTRO":
        break
    b.update()
check(any(v.get("id") == pid for v in g.data.data["pokedex"].values()), "and YES catches it")

print("3.2 / 3.4 / 3.5) levels")
check(levels.area_level(g, "UNION_CAVE") == 13 and levels.area_level(g, "SLOWPOKE_WELL") == 15, "Union Cave 13, Slowpoke Well 15")
check(levels.area_level(g, "KANTO_ROUTE_26") == 52, "Route 26 trains you for the League (Lv 52, patch 12)")
story.current_area_key = "MAHOGANY_TOWN"
story.level_cap_mode = "STORY"
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE"]
cap5 = levels.story_level_cap(story)
story.badges["JOHTO"].append("MINERAL")
cap6 = levels.story_level_cap(story)
check(cap5 == 35 and cap6 == 35, f"the cap never drops: 5 badges {cap5}, 6 badges {cap6} (HGSS: Jasmine 35, Pryce 34)")
story.level_cap_mode = "NONE"
joey = [levels.trainer_level(g, "JOHTO_ROUTE_29") for _ in range(200)]
check(max(joey) <= 5, f"Route 29 trainers top out at Lv {max(joey)}")

print("4.1 / 4.2 / 4.5) Johto details")
story.inventory.pop("COIN_CASE", None)
said = run("GOLDENROD_CITY", "Coin Case Man")
check(story.inventory.get("COIN_CASE") == 1, "a Coin Case in Goldenrod")
story.current_area_key = "AZALEA_TOWN"
story.defeated_trainers.pop("SLOWPOKE_WELL", None)
c = ow.CityState(g)
g.change_state(c)
shown = []
c.show_message = lambda lines, callback=None: shown.append(lines)
c.start_gym_battle()
check(shown and "Slowpoke" in str(shown[-1]), "Azalea's Gym says why it's closed")
check("battle him again" in str(prog["ECRUTEAK_CITY"]["gym"]["requirements"]["fail_text"]), "Morty's note hints at the rival rematch")

print("4.3) after the Johto title: home, not the rematch lobby")
story.current_area_key = "SILVER_LEAGUE_PLATEAU"
story.story_flags["beat_johto_champion"] = True
lance = TrainerBattleState(g, [mk(149)], trainer_class="CHAMPION", trainer_name="Lance", area_name="SILVER_LEAGUE_PLATEAU",
                           battle_type="gym", victory_flag="beat_johto_champion")
lance.player_won = True
g.change_state(lance)
lance.exit_battle()
check(isinstance(g.current_state, ow.AreaTransitionState) and g.current_state.next_area_key == "NEW_BARK_TOWN",
      f"home to New Bark ({type(g.current_state).__name__})")

print("HANDOFF B-1) a lead with no back sprite can faint")
import os
check(os.path.exists("assets/sprites/pokemon/back/909.png") and os.path.exists("assets/sprites/pokemon/back/shiny/909.png"),
      "Fuecoco has back sprites now")
story.current_area_key = "JOHTO_ROUTE_29"
fu = mk(909); fu.back_image = None
story.player_team = [fu, mk(25)]
tb = TrainerBattleState(g, [mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name="JOHTO_ROUTE_29")
g.change_state(tb)
tb.player_pokemon = fu
tb.fainting_side = "player"
tb._start_faint_animation()
check(tb.faint_anim.active, "the faint animation runs without a back sprite (was a freeze)")

print("HANDOFF G-1) catching a story boss uses the ball; declining keeps it")
story.current_area_key = "CRYSTAL_CAVE"
story.story_flags.pop("crystal_onix_defeated", None)
story.balls_left = 30
st = state_for("CRYSTAL_CAVE")
st.action_challenge_boss(dict(prog["CRYSTAL_CAVE"]["area_boss"], lines=None))
b = g.current_state
b.trigger_outro(True)
check(not story.story_flags.get("crystal_onix_defeated"), "beating the Crystal Onix alone doesn't remove it")
b.catch_no()
check(not story.story_flags.get("crystal_onix_defeated"), "declining the catch: it can be found again")
st = state_for("CRYSTAL_CAVE")
st.action_challenge_boss(dict(prog["CRYSTAL_CAVE"]["area_boss"], lines=None))
b = g.current_state
b.trigger_outro(True)
b.catch_yes()
for _ in range(200):
    if b.phase == "OUTRO":
        break
    b.update()
if b.dialogue_box.callback:
    b.dialogue_box.callback()
check(story.balls_left == 29 and story.story_flags.get("crystal_onix_defeated"), f"caught: one ball used ({story.balls_left})")

print("HANDOFF F-3) a legendary beaten with no balls says so")
story.balls_left = 0
w = WildBattleState(g, mk(244), "JOHTO_ROUTE_36" if "JOHTO_ROUTE_36" in prog else "JOHTO_ROUTE_29")
g.change_state(w)
w.trigger_outro(True)
check("no Poke Balls" in " ".join(w.dialogue_box.text_lines), f"{w.dialogue_box.text_lines}")
story.balls_left = 10

print("HANDOFF S-2) Ho-Oh's Rainbow Wing")
story.current_area_key = "BELL_TOWER" if "BELL_TOWER" in prog else "ECRUTEAK_CITY"
dex = g.data.data.setdefault("pokedex", {})
for pid in (243, 244, 245):
    dex[f"{pid}-normal"] = {"id": pid}
story.inventory.pop("RAINBOW_WING", None)
st = ow.PlayState(g)
st.visit_sage_li()
check(story.inventory.get("RAINBOW_WING") == 1, "all three beasts caught: Sage Li gives the Rainbow Wing")
check(story.is_caught(243, "normal") if hasattr(story, "is_caught") else True, "caught check matches dex keys")

print("HANDOFF Red) Mt. Silver after the Johto title")
story.badges = {"KANTO": [], "JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]}
story.story_flags["beat_johto_champion"] = True
check("Mt. Silver" in travel("MT_SILVER_CITY"), "no Kanto badges needed")

print("HANDOFF R-1 / F-1) moving on: the right rival, and the professor explains")
story.current_area_key = "NEW_BARK_TOWN"
story.region_rivals = {}
nxt = story.move_to_region("SINNOH")
check(g.rival_name.upper() == story.region_rivals["SINNOH"]["name"].upper(), f"Sinnoh rival named: {g.rival_name}")
import time
for _ in range(100):  # the starter screen loads its Pokemon (and text) in the background
    if nxt.starters:
        break
    time.sleep(0.1)
time.sleep(0.2)
ss = nxt
txt = " ".join(ss.dialogue_box.text_lines)
check("safe at home" in txt and "Johto" in txt and txt.index("Choose wisely") < len(txt), f"{ss.dialogue_box.text_lines[:2]}")

print("HANDOFF S-11) Bill's Eevee")
story.current_area_key = "GOLDENROD_CITY"
story.story_flags["met_bill_johto"] = True
story.story_flags.pop("got_bill_eevee", None)
story.player_team = [mk(25)]
c = ow.CityState(g)
c.visit_bill_johto()
check(any(p.id == 133 for p in story.player_team), "Bill gives an Eevee in Goldenrod")

print("HANDOFF S-1) the Fire Treasure can't be lost")
story.current_area_key = "FIRE_ISLAND"
story.story_flags["shamouti_moltres_calmed"] = True
story.inventory.pop("FIRE_TREASURE", None)
st = state_for("FIRE_ISLAND")
sr = opt("FIRE_ISLAND", "SEARCH THE SHRINE")
check(st._check_route_condition(sr["condition"], False), "calmed but no treasure: search the shrine again")
run("FIRE_ISLAND", "SEARCH THE SHRINE")
check(story.inventory.get("FIRE_TREASURE") == 1, "and it's there")

print("Q-1) Mom never offers a region you've already played")
from src.states.menus import RegionSelectionState
story.current_area_key = "NEW_BARK_TOWN"
story.starting_region = "KANTO"
story.visited_region_set = {"KANTO", "JOHTO", "HOENN"}
pick = RegionSelectionState(g, mode="move", return_state=ow.CityState(g))
check(not ({"KANTO", "JOHTO", "HOENN"} & set(pick.regions)) and set(pick.regions) <= {"SINNOH", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA"}
      and pick.regions, f"picker: only unplayed regions {pick.regions}")
story.visited_region_set = {r for r, _ in story.get_region_starts()}
c = ow.CityState(g)
shown = []
c.show_message = lambda lines, callback=None: shown.append(lines)
c._offer_move("JOHTO", phone=False)
check(shown and "nowhere new" in " ".join(shown[-1]), "all nine played: Mom says there's nowhere new")

print("Q-4) sub-region rivals are their own characters")
kt = [o["event"]["battle"]["class"] for o in prog["KITAKAMI"]["route_menu"] if (o.get("event") or {}).get("battle")]
check(kt and "RIVAL" not in kt, f"Carmine and Kieran are Kitakami trainers ({kt})")

print("Q-6) Mew's hint counts Kanto Pokemon only")
story.player_team = [mk(152)]  # (the party is registered in the dex too)
dex = g.data.data.setdefault("pokedex", {})
dex.clear()
for pid in list(range(1, 101)) + list(range(152, 400)):
    dex[f"{pid}-normal"] = {"id": pid}
story.current_area_key = "FARAWAY_ISLAND"
said = run("FARAWAY_ISLAND", "FOLLOW THE PINK SHADOW")
txt = " ".join(said[-1])
check("100 of the 150 Kanto" in txt and "50 still to catch" in txt, f"{said[-1][-1]}")
st = state_for("FARAWAY_ISLAND")
mew = opt("FARAWAY_ISLAND", "CHALLENGE MEW")
check(not st._check_route_condition(mew["condition"], False), "348 species caught but only 100 Kanto: no Mew")
print("FAILURES:", fails)
