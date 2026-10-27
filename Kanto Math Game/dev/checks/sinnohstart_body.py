
# Sinnoh follows Brilliant Diamond / Shining Pearl (Jordan, 10-26; teams from Serebii PokéEarth's area
# pages): the Lake Verity opening, Barry's battles, the lakes after Byron, the Galactic Key, the
# Spear Pillar, and Platinum's Distortion World on top.
from src.states.overworld import CityState, PlayState, AreaTransitionState, _run_story_event
from src.states.menus import StarterSelectionState, region_opening_state
from src.states.battle import WildBattleState, TrainerIntroState, TrainerBattleState
from src.world import story_events
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
said = []


def _show(self, lines, callback=None, **k):
    said.extend(lines if isinstance(lines, list) else [lines])
    if callback:
        callback()


CityState.show_message = _show
PlayState.show_dialogue = _show
prog = g.loader.area_data["STORY_PROGRESSION"]
flags = story.story_flags


def city(area):
    story.current_area_key = area
    said.clear()
    s = CityState(g)
    g.states["city"] = s
    g.change_state(s)
    return s


def route(area):
    story.current_area_key = area
    said.clear()
    s = PlayState(g)
    g.states["play"] = s
    g.change_state(s)
    return s


def battle_team(state):
    b = state.next_state if isinstance(state, TrainerIntroState) else state
    return [(p.id, p.level) for p in b.opponent_team] if isinstance(b, TrainerBattleState) else None


def opt(area, text):
    return next(o for o in prog[area].get("route_menu") or prog[area].get("explore_options") or [] if o.get("text") == text)


# A brand-new Sinnoh game.
for f in list(flags):
    if "sinnoh" in f or f.startswith(("defeated_rival_", "galactic_", "canalave_", "spear_pillar")):
        flags.pop(f)
story.starting_region = "SINNOH"
story.badges["SINNOH"] = []
story.player_team = []
story.balls_left = 0

print("1) a new game starts in Twinleaf; only Lake Verity is open")
st = region_opening_state(g, "SINNOH")
check(isinstance(st, AreaTransitionState) and st.next_area_key == "TWINLEAF_TOWN", "the opening goes to Twinleaf Town")
c = city("TWINLEAF_TOWN")
check(g.current_state is c and not story.player_team, "Twinleaf: no starter screen")
check(not c._check_menu_condition("received_starter_sinnoh"), "Route 201 is closed until the starter")

print("2) Lake Verity: Rowan's briefcase, then the wild Starly")
route("LAKE_VERITY")
sel = g.current_state
check(isinstance(sel, StarterSelectionState) and sel.on_route, f"the starter screen opens at the lake ({type(sel).__name__})")
check(any("briefcase" in l for l in said), "Rowan's briefcase")
sel.load_starters()
sel.selected_idx = 0
sel.complete_selection()
check(story.player_team and story.player_team[0].id == 387, "Turtwig chosen")
sel.start_rival_battle()
route("LAKE_VERITY")
b = g.current_state
check(isinstance(b, WildBattleState) and b.opponent_pokemon.id == 396 and b.opponent_pokemon.level == 2
      and b.no_catch, "a Lv 2 Starly that can't be caught")
b.trigger_outro(win=True)
check(flags.get("sinnoh_starly_driven_off"), "beating it ends the scene")
r = route("LAKE_VERITY")
check(isinstance(g.current_state, AreaTransitionState) and g.current_state.next_area_key == "TWINLEAF_TOWN",
      "then straight home to Twinleaf")
c = city("TWINLEAF_TOWN")
check(battle_team(g.current_state) == [(390, 5)], "Barry's first battle: Chimchar Lv 5 against Turtwig")
flags["defeated_rival_sinnoh_starter"] = True
check(not story.catch_unlocked("SINNOH"), "no catching before Rowan's Pokedex")
c = city("SANDGEM_TOWN")
c.story_event("professor_rowan")
check(flags.get("received_pokedex_sinnoh") and story.catch_unlocked("SINNOH"), "Rowan's Pokedex: catching opens")

print("3) Barry's battles (Serebii)")
r = route("SINNOH_ROUTE_203")
check(battle_team(g.current_state) == [(396, 7), (390, 9)], f"Route 203: Starly 7, Chimchar 9 {battle_team(g.current_state)}")
for area in ("ETERNA_CITY", "VEILSTONE_CITY"):  # (Veilstone has Dawn's battle instead)
    ev = prog[area].get("on_enter_event") or {}
    check((ev.get("trainer") or {}).get("name") != "{rival_name}", f"{area}: no Barry battle (not in BDSP)")
check(len(prog["TWINLEAF_TOWN"]["on_enter_event"]) == 1, "Twinleaf: only the starter battle")
story.badges["SINNOH"] = ["COAL", "FOREST"]
c = city("HEARTHOME_CITY")
check(battle_team(g.current_state) == [(396, 19), (418, 20), (315, 20), (391, 21)],
      f"Hearthome: Starly, Buizel, Roselia, Monferno {battle_team(g.current_state)}")
c = city("VEILSTONE_CITY")
check(battle_team(g.current_state) == [(35, 25), (64, 25), (394, 28)], f"Veilstone: Dawn with Prinplup {battle_team(g.current_state)}")
flags["defeated_dawn_veilstone"] = True
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE"]
vs = city("VEILSTONE_CITY")
grunt = opt("VEILSTONE_CITY", "Talk to the Galactic Grunt")
check(vs._check_menu_condition(grunt["condition"]), "a grunt outside the Galactic building")
_run_story_event(vs, grunt["event"], vs._check_menu_condition, lambda lines: None)
wh = next(o for o in prog["VEILSTONE_CITY"]["travel_options"] if o.get("target_area") == "GALACTIC_WAREHOUSE")
check(story.inventory.get("STORAGE_KEY") == 1 and wh.get("item_condition") == "STORAGE_KEY", "his Storage Key opens the warehouse")
lea = prog["SINNOH_POKEMON_LEAGUE"]["on_enter_event"]["trainer"]
check(len(lea["team_choice"]["387"]) == 6 and lea["levels"][-1] == 55 and lea["class"] == "RIVAL",
      "the League: six Pokemon, Infernape Lv 55")
check(not any(o.get("target") == "barry_victory_road" for o in prog["VICTORY_ROAD_SINNOH"]["route_menu"]),
      "no rival battle in Victory Road")

print("4) Cynthia in Eterna; Byron doesn't need Iron Island")
check(any(o.get("target") == "cynthia_hm" for o in prog["ETERNA_CITY"]["explore_options"])
      and not any(o.get("target") == "cynthia_hm" for o in prog["HEARTHOME_CITY"]["explore_options"]), "HM Cut from Cynthia in Eterna")
check(prog["CANALAVE_CITY"]["gym"]["requirements"].get("badges") == 5, "Byron: 5 badges, no Iron Island lock")

print("5) the lakes after Byron, the Galactic Key, the Spear Pillar")
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC"]
lv = route("LAKE_VALOR")
check(not lv._check_route_condition(opt("LAKE_VALOR", "Confront Saturn at the Lake")["condition"], False),
      "Lake Valor waits for the Canalave Library")
story.badges["SINNOH"].append("MINE")
c = city("CANALAVE_CITY")
said.clear()
c.story_event("canalave_library")
check(flags.get("canalave_library_meeting") and any("Lake Valor" in l for l in said), "the library: an explosion at Lake Valor")
lv = route("LAKE_VALOR")
lv.story_event("saturn_lake_valor")
check(battle_team(g.current_state) == [(64, 35), (436, 35), (454, 37)], f"Saturn in Valor Cavern {battle_team(g.current_state)}")
flags["galactic_lake_valor_cleared"] = True
ve = route("LAKE_VERITY")
ve.story_event("galactic_lake_verity")
check(battle_team(g.current_state) == [(42, 37), (436, 37), (432, 39)], f"Mars at Lake Verity {battle_team(g.current_state)}")
flags["galactic_lake_verity_cleared"] = True
ac = route("LAKE_ACUITY")
check(not ac._check_route_condition(opt("LAKE_ACUITY", "Confront Jupiter at the Lake")["condition"], False),
      "Lake Acuity waits for the Icicle Badge")
story.badges["SINNOH"].append("ICICLE")
said.clear()
ac.story_event("jupiter_lake_acuity")
check(flags.get("galactic_lake_acuity_cleared") and not isinstance(g.current_state, TrainerIntroState)
      and not story.inventory.get("GALACTIC_KEY"), "Jupiter has beaten Barry and gone: no battle, no key")
vs = city("VEILSTONE_CITY")
under = opt("VEILSTONE_CITY", "Warehouse Underpass")
check(vs._check_menu_condition(under["condition"]), "the warehouse underpass opens")
check((under["event"]["battle"].get("rewards") or {}).get("GALACTIC_KEY") == 1, "its grunt has the Galactic Key")
for lake in ("LAKE_VERITY", "LAKE_VALOR", "LAKE_ACUITY"):
    boss = next(o for o in prog[lake]["route_menu"] if o.get("action") == "BOSS")
    check("spear_pillar_resolved" in boss["condition"], f"{lake}: its guardian comes home after Dialga/Palkia")
flags["galactic_hq_cleared"] = True
sp_ = route("SPEAR_PILLAR")
sp_.story_event("cyrus_spear_pillar")
check(not flags.get("spear_pillar_resolved") and not isinstance(g.current_state, TrainerIntroState),
      "Cyrus waits until Mars and Jupiter are beaten")
sp_ = route("SPEAR_PILLAR")
sp_.story_event("spear_pillar_commanders")
check(battle_team(g.current_state) == [(436, 41), (42, 42), (432, 45), (435, 46)], "Mars and Jupiter")
flags["spear_pillar_commanders"] = True
sp_ = route("SPEAR_PILLAR")
sp_.story_event("cyrus_spear_pillar")
check(battle_team(g.current_state) == [(430, 45), (169, 46), (130, 45), (461, 48)], f"Cyrus {battle_team(g.current_state)}")

print("6) Platinum's Distortion World")
dw = prog["DISTORTION_WORLD"]
gir = next(o for o in dw["route_menu"] if o.get("text") == "FACE GIRATINA")
check(gir["boss"]["id"] == 4001 and g.loader.fetch_specific(4001), "Giratina in its Origin Forme")
check(any((o.get("event") or {}).get("gift_item", {}).get("GRISEOUS_ORB") for o in dw["route_menu"]), "the Griseous Orb")
check(dw["trainer_pool"][0].get("levels") == [45, 47, 46, 46, 48], "Cyrus's Platinum team")

print("7) older saves")
for f in ("sinnoh_starly_driven_off", "received_pokedex_sinnoh"):
    flags.pop(f, None)
story._migrate_sinnoh_start()
check(flags.get("received_pokedex_sinnoh"), "a save with a Sinnoh starter keeps catching")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
