
# OPEN_ITEMS.md section 2 fixes (2026-10-23).
import json
from src.states.overworld import CityState, PlayState, _run_story_event
from src.states.battle import TrainerIntroState
from src.pokemon import evolution
from src.world import levels
fails = 0
SP = g.loader.area_data["STORY_PROGRESSION"]


def check(ok, msg):
    global fails
    print(("ok   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


def route_buttons(area):
    story.current_area_key = area
    p = PlayState(g); g.change_state(p)
    p.show_progression_menu()
    return p, [b.text for b in p.route_buttons]


def city_buttons(area, kind="travel_options"):
    story.current_area_key = area
    c = CityState(g); g.change_state(c)
    c.open_travel_menu() if kind == "travel_options" else c.open_explore_menu()
    return c, [b.text for b in c.hover_buttons]


# U-B2 Unova finale: Alder opens N's Castle; the Sages, N, then Ghetsis give the title.
check(SP["UNOVA_POKEMON_LEAGUE"]["gym"]["leader"]["victory_flag"] == "beat_alder", "Alder's win sets beat_alder")
for f in ("beat_alder", "defeated_n_castle", "beat_unova_champion", "plasma_sages_defeated"):
    story.story_flags.pop(f, None)
check("N's Castle" not in city_buttons("UNOVA_POKEMON_LEAGUE")[1], "N's Castle hidden before Alder")
story.story_flags["beat_alder"] = True
check("N's Castle" in city_buttons("UNOVA_POKEMON_LEAGUE")[1], "N's Castle open after Alder")
for i in range(3):
    story.defeated_trainers.get("NS_CASTLE", set()).discard(i)
p, btns = route_buttons("NS_CASTLE")
check(btns[:2] == ["BATTLE PLASMA SAGE", "CONFRONT N"] and "STOP GHETSIS" in btns, f"castle menu: {btns}")
n_item = next(o for o in SP["NS_CASTLE"]["route_menu"] if o["text"] == "CONFRONT N")
p._get_route_callback(n_item)()
check(not isinstance(g.current_state, TrainerIntroState), "N waits until the Sages are beaten")
for i in range(3):
    story.mark_trainer_defeated("NS_CASTLE", i)
story.story_flags["plasma_sages_defeated"] = True  # the last Sage's victory flag
p, btns = route_buttons("NS_CASTLE")
p._get_route_callback(n_item)()
st = g.current_state
check(isinstance(st, TrainerIntroState) and st.next_state.trainer_name == "N"
      and st.next_state.victory_flag == "defeated_n_castle", "CONFRONT N starts N's battle")
check(any(levels.is_legendary(m.id) for m in st.next_state.opponent_team), "N brings Zekrom to the castle")
g_item = next(o for o in SP["NS_CASTLE"]["route_menu"] if o["text"] == "STOP GHETSIS")
p, btns = route_buttons("NS_CASTLE")
p._get_route_callback(g_item)()
check(not isinstance(g.current_state, TrainerIntroState), "Ghetsis waits until N is beaten")
story.story_flags["defeated_n_castle"] = True
p, btns = route_buttons("NS_CASTLE")
check("CONFRONT N" not in btns and "STOP GHETSIS" in btns, f"after N: {btns}")
p._get_route_callback(g_item)()
st = g.current_state
check(isinstance(st, TrainerIntroState) and st.next_state.victory_flag == "beat_unova_champion"
      and st.next_state.rewards.get("MASTER_BALL") == 1, "Ghetsis's battle grants the title and the Master Ball")

# K-D2 route trainers named {rival_name}: name, rival art.
g.rival_name = "SHAUNA"
story.current_area_key = "VICTORY_ROAD_KALOS"
p = PlayState(g); g.change_state(p)
p.trigger_trainer_battle(specific_index=1)
st = g.current_state
check(isinstance(st, TrainerIntroState) and "{" not in str(st.next_state.trainer_name)
      and st.next_state.trainer_name == g.rival_name, f"route rival name filled in: {st.next_state.trainer_name}")
check(all("{" not in line for line in st.dialogue_box.text_lines), f"route intro filled: {st.dialogue_box.text_lines}")

# A-D2 Alola Team Skull button; villain classes.
malie = next(o for o in SP["MALIE_CITY"]["explore_options"] if o.get("target") == "alola_guzma_intro")
check(malie["condition"] == "has_rockium_z_badge" and malie.get("victory_flag") == "malie_skull_cleared", "Malie Skull button")
dlg = g.loader.area_data["TRAINER_CLASS_DIALOGUE"]
check(all(c in dlg for c in ("PLASMA", "FLARE", "SKULL", "GALACTIC", "ROCKET")), "villain class dialogue")
classes = {t.get("class") for a in SP.values() for t in a.get("trainer_pool", []) if "Plasma" in str(t.get("name"))}
check("GALACTIC" not in classes, f"Plasma trainers aren't Galactic: {classes}")

# U-D3 / U-D4 Unova monkeys and rival stages.
striaton = SP["STRIATON_CITY"]["gym"]["leader"]["team_choice"]
check(striaton == {"495": [506, 513], "498": [506, 515], "501": [506, 511]}, "Striaton leader counters the starter")
from src.world import story_events
check(story_events.get("dreamyard_monkey")["gift_pokemon"] == {"495": 515, "498": 511, "501": 513, "default": 511},
      "Fennel's monkey beats that leader")
acc = SP["ACCUMULA_TOWN"]["on_enter_event"]["trainer"]["team_choice"]
check(acc == {"495": [498, 504], "498": [501, 504], "501": [495, 504]}, "Accumula rival uses base starters")

# U-D2 fishing by region.
for area, want in (("UNOVA_ROUTE_17", "UNOVA"), ("JOHTO_ROUTE_32", "JOHTO"), ("KANTO_ROUTE_12", None)):
    story.current_area_key = area
    p = PlayState(g)
    pool = p._fishing_pool("SUPER_ROD")
    want_pool = g.loader.area_data.get(f"{want}_SUPER_ROD_POOL_PERCENTAGES") if want else None
    if want == "JOHTO":
        want_pool = g.loader.area_data["JOHTO_SUPER_ROD_POOL_PERCENTAGES"]
    if not want:
        want_pool = g.loader.area_data["SUPER_ROD_POOL_PERCENTAGES"]
    # an area with its own rod table from the games (Serebii PokeEarth, 10-26) uses that first
    want_pool = g.loader.area_data.get(f"{area}_SUPER_ROD_PERCENTAGES") or want_pool
    check(pool == want_pool, f"{area} fishes its own pool (the area's, else the region's)")

# J-D1 / J-D2 Johto: National Park catches, headbutt buttons.
p, btns = route_buttons("NATIONAL_PARK")
check("CATCH WILD POKéMON" in btns and "Route 35" in btns, f"National Park is a wild route: {btns}")
for r in ("JOHTO_ROUTE_30", "JOHTO_ROUTE_42"):
    check(any(o.get("action") == "HEADBUTT" for o in SP[r]["route_menu"]), f"{r} has HEADBUTT")

# GZ-2, U-S2, P-4, D-5 data and evolutions.
check(g.loader.area_data["FORM_MAP"]["2019"]["id"] == 52, "Galarian Meowth's base is Meowth")
check("COTTONEE" in g.loader.evolution_map["EVOLUTION_ITEMS"]["SUN_STONE"], "Sun Stone lists Cottonee")
story.current_area_key = "MOTOSTOKE"; story.enter_region("GALAR")
dip = Pokemon(g.loader.fetch_specific(1011), g.assets, size_mult=2.5)
check("DRAGON-CHEER" in evolution.known_moves(g, dip), "Dipplin knows Dragon Cheer")
check(any(e.startswith("HYDRAPPLE") for e in evolution.ready_evolutions(g, dip)), "Dipplin can become Hydrapple")
gslow = Pokemon(g.loader.fetch_specific(2022), g.assets, size_mult=2.5)
check(evolution.item_evolution(g, gslow, "GALARICA_CUFF") == ("SLOWBRO_GALARIAN", 80)
      and evolution.item_evolution(g, gslow, "GALARICA_WREATH") == ("SLOWKING_GALARIAN", 199), "Galarica Cuff / Wreath")

# O-1 / D-1 Pokedex: Shadow forms count as the species; Urshifu counts as #892.
g.data.data["pokedex"] = {}
g.data.add_pokemon(Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5))
g.data.add_pokemon(Pokemon(g.loader.fetch_specific(8004), g.assets, size_mult=2.5))
keys = set(g.data.data["pokedex"])
check("9406-shadow" in keys and "296-normal" not in keys, f"Shadow Makuhita is its own variant entry: {keys}")
check("892-normal" in keys and "8004-single" in keys, "Urshifu registers as #892 too")

# O-4 purified Pokemon evolve when due.
shadow = Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5)
shadow.level = 40
story.player_team = [shadow]
story.current_area_key = "PHENAC_CITY" if "PHENAC_CITY" in SP else story.current_area_key
c = CityState(g); g.change_state(c)
_run_story_event(c, {"purify": True, "lines": ["The Relic Stone glows."]}, lambda cond: True, lambda lines: None)
check(story.player_team[0].id == 297, f"purified Makuhita evolved: {story.player_team[0].name}")

# K-D3 Kalos NPC flags; D-4 Zarude flag; H-F1 KNUCKLE migration.
for target, flag in (("kalos_sycamore_intro", "met_sycamore"), ("kalos_shauna_intro", "met_kalos_friends")):
    opt = next(o for a in SP.values() for o in a.get("explore_options", []) if o.get("target") == target)
    check(opt.get("victory_flag") == flag, f"{target} sets {flag}")
check(SP["GLIMWOOD_TANGLE"]["area_boss"]["victory_flag"] == "GLIMWOOD_TANGLE_boss_defeated", "Zarude's flag")
check(SP["DEWFORD_TOWN"]["gym"]["leader"]["badge_reward"] == "KNUCKLE", "Knuckle Badge spelled KNUCKLE")
old = {"badges": {"HOENN": ["STONE", "KNuckle"]}, "story_flags": {"ISLE_OF_ARMOR_boss_defeated": True}}
mig = story._migrate_area_keys(old)
check(mig["badges"]["HOENN"] == ["STONE", "KNUCKLE"] and "GLIMWOOD_TANGLE_boss_defeated" in mig["story_flags"],
      "old saves migrate KNuckle and Zarude's flag")

# P-7 region welcome text.
story.current_area_key = "SOUTH_PROVINCE_AREA_1" if "SOUTH_PROVINCE_AREA_1" in SP else "MESAGOZA"
p = PlayState(g)
check("Kanto" not in " ".join(p.dialogue_box.text_lines), f"Paldea welcome: {p.dialogue_box.text_lines}")

print(f"##### bugs2: {fails} fails")
