
# Kanto follows FireRed/LeafGreen (Jordan, 10-26): the Pallet opening and Oak's Parcel, every rival
# battle, the Rocket arc with Giovanni, the Mt. Moon fossil pick, and real HMs for Surf and Fly.
from src.states.overworld import CityState, PlayState, AreaTransitionState, _run_story_event
from src.states.menus import StarterSelectionState, region_opening_state
from src.states.battle import TrainerIntroState
from src.states.systems import GameCornerState
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


def oak_lines(c):
    c.visit_prof_oak()
    return list(c.npc_dialogue.text_lines)


def event(e):
    _run_story_event(g.current_state, e, lambda cond: True, lambda lines: said.extend(lines))


# A brand-new Kanto game.
for f in ("received_starter_kanto", "received_pokedex_kanto", "got_oaks_parcel", "defeated_rival_kanto",
          "kanto_parcel_era", "pending_starter", "beat_champion"):
    flags.pop(f, None)
story.starting_region = "KANTO"
story.badges["KANTO"] = []
story.player_team = []
story.balls_left = 5

print("1) a new game starts in Pallet Town, not at the starter screen")
st = region_opening_state(g, "KANTO")
check(isinstance(st, AreaTransitionState) and st.next_area_key == "PALLET_TOWN", "the opening goes to Pallet Town")
c = city("PALLET_TOWN")
check(g.current_state is c and not story.player_team, "Pallet: no starter screen yet")
stop = [o for o in prog["PALLET_TOWN"]["travel_options"] if o.get("npc")]
check(stop and stop[0]["text"] == "Route 1" and c._check_menu_condition("not:received_starter_kanto"),
      "Route 1 is the stop where Oak comes running")
check(c._get_callback_for_option(stop[0]) == c.visit_prof_oak, "picking it brings Oak")
check(not story.catch_unlocked("KANTO"), "no catching before the Pokedex")
lines = oak_lines(c)
check(any("Wait" in l for l in lines) and flags.get("kanto_parcel_era"), "Oak: wait, come to my lab")
c.npc_dialogue.callback()  # -> the lab's starter screen once Oak slides out
for _ in range(200):
    if isinstance(g.current_state, StarterSelectionState):
        break
    c.update()
check(isinstance(g.current_state, StarterSelectionState), f"his lab: the starter screen ({type(g.current_state).__name__})")

print("2) Oak's Parcel")
flags["received_starter_kanto"] = flags["defeated_rival_kanto"] = True
story.player_team = [mk(1)]
flags["starter_kanto"] = 1
c = city("PALLET_TOWN")
check(any("Viridian" in l for l in oak_lines(c)), "without the parcel, Oak points to the Viridian Mart")
v = city("VIRIDIAN_CITY")
mart = next(o for o in prog["VIRIDIAN_CITY"]["explore_options"] if o.get("event", {}).get("flag") == "got_oaks_parcel")
check(v._check_menu_condition(mart["condition"]), "the Viridian Mart has a parcel for Oak")
check(not v._check_menu_condition("received_pokedex_kanto"), "the Mart sells nothing yet, and Viridian Forest is closed")
event(mart["event"])
check(story.inventory.get("OAKS_PARCEL") == 1, "you carry Oak's Parcel")
c = city("PALLET_TOWN")
oak_lines(c)
check(flags.get("received_pokedex_kanto") and story.balls_left == 10 and not story.inventory.get("OAKS_PARCEL")
      and story.catch_unlocked("KANTO"), "Oak takes it: the Pokedex and 5 Poke Balls, catching is open")

print("3) rival battles")
r22 = prog["KANTO_ROUTE_22"]["on_enter_event"]
check(isinstance(r22, list) and {e["flag_check"] for e in r22} == {"defeated_rival_route22_early", "defeated_rival_route22_late"},
      "Route 22: the early rival and the one before the League")
for area, flag in (("KANTO_ROUTE_24", "defeated_rival_nugget_bridge"), ("KANTO_POKEMON_TOWER", "defeated_rival_tower")):
    ev = prog[area]["on_enter_event"]
    check(ev["flag_check"] == flag and set(ev["trainer"]["team_choice"]) == {"1", "4", "7"}, f"{area}: the rival, team by starter")
silph = prog["SILPH_CITY"]["trainer_pool"]
names = [t["name"] for t in silph]
check(names.index("{rival_name}") < names.index("Admin Proton") and names[-1] == "Giovanni"
      and silph[-1].get("victory_flag") == "silph_co_cleared", "Silph Co.: the rival on 7F, Giovanni at the top")


def arrive(area):
    story.current_area_key = area
    s = PlayState(g)
    g.states["play"] = s
    g.change_state(s)
    s.update()
    intro = g.current_state  # (only the rival counts: a route's own trainers can also turn up)
    rival = isinstance(intro, TrainerIntroState) and intro.next_state.trainer_class == "RIVAL"
    return [p.id for p in intro.next_state.opponent_team] if rival else None


story.badges["KANTO"] = ["BOULDER"]
check(arrive("KANTO_ROUTE_24") == [17, 63, 19, 4], "Route 24 (Bulbasaur): Pidgeotto, Abra, Rattata, Charmander (still unevolved, FRLG)")
check(arrive("KANTO_POKEMON_TOWER") == [17, 130, 102, 64, 5], "Pokemon Tower: Gyarados and Exeggcute join")
flags["defeated_rival_nugget_bridge"] = flags["defeated_rival_tower"] = True
check(arrive("KANTO_ROUTE_24") is None, "each fights once")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]
flags["defeated_rival_route22_early"] = True
check(arrive("KANTO_ROUTE_22") == [18, 111, 102, 130, 65, 6], "Route 22 with 8 badges: Exeggcute and Gyarados, Charizard last (FRLG)")
story.badges["KANTO"] = []
anne = next(t for t in prog["KANTO_SS_ANNE"]["trainer_pool"] if t["name"] == "{rival_name}")
check(anne.get("team_choice") and anne["sprite"] == "{rival_character}", "S.S. Anne: the player's own rival")

print("4) the Rocket Hideout: Giovanni drops the Silph Scope")
tower = prog["KANTO_POKEMON_TOWER"]["trainer_pool"]
check(not any("SILPH_SCOPE" in (t.get("rewards") or {}) for t in tower), "Jessie and James stay in the Tower, without the Scope")
story.inventory.pop("SILPH_SCOPE", None)
gc = GameCornerState(g, c)
gc.rocket_progress = 4
gc.next_rocket_battle()
intro = g.current_state
check(isinstance(intro, TrainerIntroState) and [p.id for p in intro.next_state.opponent_team] == [95, 111, 115],
      "B4F: Giovanni with Onix, Rhyhorn and Kangaskhan")
gc.rocket_progress = 5
gc.give_porygon()
check(story.inventory.get("SILPH_SCOPE") == 1 and flags.get("game_corner_cleared"), "beating him: the Silph Scope")

print("5) fossils: pick one in Mt. Moon, the other waits at the Cinnabar lab")
menu = prog["MT_MOON"]["route_menu"]
take = {o["text"]: o for o in menu if o.get("text", "").startswith("TAKE ")}
check(set(take) == {"TAKE DOME FOSSIL", "TAKE HELIX FOSSIL"}, "Mt. Moon: Dome or Helix, after Super Nerd Miguel")
for k in ("DOME_FOSSIL", "HELIX_FOSSIL", "OLD_AMBER"):
    story.inventory.pop(k, None)
event(take["TAKE DOME FOSSIL"]["event"])
check(story.inventory.get("DOME_FOSSIL") == 1 and flags.get("took_dome_fossil"), "you took the Dome Fossil")
lab = city("CINNABAR_ISLAND")
lab.visit_stoneman()
check(story.inventory.get("HELIX_FOSSIL") == 1, "the lab hands over the Helix Fossil Miguel kept")
check(not any(o.get("target") == "stoneman" for o in prog["MT_MOON_CITY"]["explore_options"]), "revival is at Cinnabar only")
story.badges["KANTO"] = ["BOULDER"]
p = city("PEWTER_CITY")
p.visit_museum()
check(not story.inventory.get("OLD_AMBER"), "the Old Amber needs Cut")
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
p.visit_museum()
check(story.inventory.get("OLD_AMBER") == 1, "with the Cascade Badge: the Old Amber")

print("6) HM Surf and HM Fly, no Surf Board or Air Balloon")
story.inventory.update({"SURF_BOARD": 1, "AIR_BALLOON": 1})
story.inventory.pop("HM_FLY", None)
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL"]
story.sync_key_items()
inv = story.inventory
check(inv.get("HM_CUT") and inv.get("HM_FLY") and inv.get("HM_SURF") and story.can_fly(), "Kanto's badges give HM Cut, Fly and Surf")
check("SURF_BOARD" not in inv and "AIR_BALLOON" not in inv, "the old stand-ins are gone")
gates = [o for a in ("PALLET_TOWN", "FUCHSIA_CITY") for o in prog[a]["travel_options"] if o.get("item_condition")]
check(gates and all(o["item_condition"] == "HM_SURF" for o in gates), "Surf routes check HM Surf")

print("7) older saves count the opening as done")
for f in ("received_pokedex_kanto", "kanto_parcel_era"):
    flags.pop(f, None)
story._migrate_kanto_start()
check(flags.get("received_pokedex_kanto"), "a save with a Kanto starter keeps catching")

print("8) Grok's Johto walk: the Radio Tower grunt, Goldenrod's shops, early levels")
from src.states.systems import BikeShopState
from src.world import levels
jprog = prog
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER"]
gold = city("GOLDENROD_CITY")
gold.visit_radio_tower_grunt()
gold.npc_dialogue.callback()
intro = g.current_state
grunt = intro.next_state if isinstance(intro, TrainerIntroState) else None
lv = [p.level for p in grunt.opponent_team] if grunt else []
check(grunt and min(lv) >= levels.area_level(g, "RADIO_TOWER"), f"the gate grunt fights at the tower's level {lv}")
grunt.player_won = False
grunt.exit_battle()
check(getattr(g.current_state, "next_area_key", None) != "RADIO_TOWER", "losing doesn't take you into the tower")
texts = [o["text"] for o in jprog["GOLDENROD_CITY"]["explore_options"]]
check("Dept. Store" in texts and "Bike Shop" in texts, "Goldenrod: Dept. Store and Bike Shop")
story.inventory.pop("BICYCLE", None)
story.inventory.pop("BIKE_VOUCHER", None)
gold = city("GOLDENROD_CITY")
BikeShopState(g, gold)
check(story.inventory.get("BICYCLE") == 1, "the Goldenrod Bike Shop lends you a bike, no voucher needed")
az = jprog["AZALEA_TOWN"]["on_enter_event"]["trainer"]
check(max(az["levels"]) <= levels.gym_aces("JOHTO")[2] + 3, f"the Azalea rival's ace is at most the cap + 3 {az['levels']}")
check(levels._area_levels(g)["JOHTO_ROUTE_36"] == 13, "Route 36 at HeartGold/SoulSilver's Lv 12-15 (canon, 10-29)")
story.badges["JOHTO"] = []

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
