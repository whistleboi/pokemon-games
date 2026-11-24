
from src.states.menus import RegionSelectionState
from src.states.systems import BadgeCaseState
from src.world import levels
ORRE = [k for k, a in prog.items() if a.get("region") == "ORRE"]


def menu(area):
    st = state_for(area)
    return [o["text"] for o in prog[area]["route_menu"] if st._check_route_condition(o.get("condition"), False)
            and not (o.get("flag_condition", "").startswith("not ") and story.story_flags.get(o["flag_condition"][4:]))]


# (R1, 11-23: the parts a player meets in Orre are played on its walked maps - the bike, the Relic Stone's door, the
#  figures on a route - not through the old menus; walked(area) opens a place as its map)
from src.states.overworld.walk_town import WalkTownState as _WTS


def walked(area, came=None):
    g.walk_towns = g.dungeon_routes = True
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    st = ow.CityState(g) if prog[area]["area_type"] == "town" else ow.PlayState(g)
    g.change_state(st)
    for _ in range(3):
        g.current_state.update()
    g.current_state.draw()
    return g.current_state


def bike(area):
    """The rides the parked motorbike offers now (its door's options, as the walked town lists them)."""
    t = walked(area)
    return [o["text"] for o in t._door_options("cycle")]


def figures(area):
    """The route buttons standing on the walked map now."""
    return [i.get("text") for i in walked(area).placed]


print("1) A full region (Colosseum + XD, 10-27)")
story.badges = {}
story.story_flags, story.inventory = {}, {}
pick = RegionSelectionState(g, mode="new")
check("ORRE" in pick.regions, f"a new-game region: {pick.regions}")
cfg = story.get_region_start("ORRE")
check(cfg.get("starters") == [196, 197] and cfg.get("start_area") == "OUTSKIRT_STAND" and not cfg.get("travel_only"),
      "start at the Outskirt Stand with Espeon or Umbreon")
check(all(p <= 386 for p in cfg["dex_list"]), "Gen 3 or earlier")
check(25 <= len(ORRE) <= 45, f"{len(ORRE)} Orre areas")   # (story rework S6, 11-24: Marine Cave, Fuji's legend spots, the Frontier)
bad = [(k, o.get("target_area")) for k in ORRE for o in prog[k].get("travel_options", []) + prog[k].get("route_menu", [])
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(sorted(k for k in ORRE if prog[k].get("wild_pool_percentages")) == ["CAVE_POKE_SPOT", "OASIS_POKE_SPOT", "ORRE_POKE_SPOTS"],
      "wild Pokemon only at the three Poke Spots (XD)")
check(sum(len(prog[k].get("shadow_pool") or []) for k in ORRE) == 134, "all 131 Shadow Pokemon, plus Ein's Kanto starters (Jordan, 10-30)")
no_traps(ORRE)
check("Air Transit to Orre" not in travel("LILYCOVE_CITY"), "no plane from Hoenn: Orre is reached like any region")
story.enter_region("ORRE")
check("ORRE" in BadgeCaseState(g, ow.CityState(g)).unlocked_regions, "a badge page for Orre's tournaments")
EIGHT = ["PHENAC", "PYRITE", "AGATE", "SNAGEM", "GATEON", "KEY_LAIR", "CITADARK", "REALGAM"]   # (story rework, 11-24: eight Gyms)
check(set(story.get_region_gym_badges("ORRE")) == set(EIGHT), f"eight badges {story.get_region_gym_badges('ORRE')}")
story.current_area_key = "PHENAC_CITY"
story.level_cap_mode = "OBEDIENCE"
check(levels.obey_level(story) == 20, "obedience follows Orre's badges")
story.current_area_key = "VALENCIA_ISLAND"
story.badges["ORANGE"] = []
check(levels.obey_level(story) == 20, "the Orange Islands are a full region now (10-27): obedience follows its badges")
story.level_cap_mode = "NONE"

print("2) The Snag Machine")
story.story_flags["received_starter_orre"] = True
check("Pyrite Town" not in bike("PHENAC_CITY"), "Pyrite waits for the Snag Machine (Phenac's bike)")
# (11-23: the old menu steps "Trouble at the Fountain" / "Meet Rui" are gone; Phenac's walked story - Folly, Rui, the
#  Mystery Troop guards - is played by orre_pilot. The Snag Machine comes with the new game; a guard's win sets the flag.)
check(not any(o.get("text") in ("Trouble at the Fountain", "Meet Rui") for o in g.loader.area_data["STORY_PROGRESSION"]["PHENAC_CITY"]["explore_options"]),
      "Phenac's old menu steps are gone")
story.inventory["SNAG_MACHINE"] = 1
story.story_flags["got_snag_machine"] = True
check("Pyrite Town" in bike("PHENAC_CITY"), "the Snag Machine opens the bike ride to Pyrite")
m = figures("ORRE_DESERT")
check(not m.count("SNAG SHADOW POKEMON") and not m.count("SNAG AGAIN"),
      f"desert: no snag figure - its Shadows are their own trainers' (Trudly, the Mystery Troop, Fein, Hordel's gift; 11-24): {m}")
story.story_flags["snagged_shadow_makuhita"] = True
m = figures("ORRE_DESERT")
check("SNAG AGAIN" in m and "SNAG SHADOW POKEMON" not in m, f"desert: once Trudly's Makuhita is snagged, SNAG AGAIN farms it (Jordan 11-24): {m}")
story.story_flags.pop("snagged_shadow_makuhita", None)
raw = g.loader.fetch_specific(9406)
check(raw["name"] == "SHADOW MAKUHITA" and raw["img"], f"Shadow form: {raw['name']}")

print("3) Purifying at the Relic Stone")
sh = Pokemon(g.loader.fetch_specific(9399), g.assets, size_mult=2.5)
sh.level, sh.moves, sh.ivs = 70, ["CRUNCH", "EARTHQUAKE"], {k: 31 for k in sh.IV_KEYS}
story.player_team = [mk(25), sh]
story.pc_pokemon = [Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5), None]
def relic_stone():
    """Walk into the Relic Cave's mouth in Agate and pick "Purify at the Relic Stone" (its door's options)."""
    t = walked("AGATE_VILLAGE")
    said = []
    t.show_message = lambda lines, callback=None: said.append(lines)
    opt = next(o for o in t._door_options("relic") if o.get("text") == "Purify at the Relic Stone")
    t._get_callback_for_option(opt)()
    return said


t = walked("AGATE_VILLAGE")
check(not any(o.get("text") == "Purify at the Relic Stone" for o in t._door_options("relic")), "the Relic Stone waits for Skrub (the cave's mouth)")
story.story_flags["orre_beat_skrub"] = True
said = relic_stone()
pm = g.current_state
check(type(pm).__name__ == "PokemonPartyMenuState", "Relic Stone: choose which Pokemon (purifying is optional)")
sh.shadow = {"gauge": 5, "max": 100, "hidden": [], "seen": True}   # (11-24: a heart still shut - the gauge not empty)
pm.on_select(1)
check(story.player_team[1] is sh and any("still shut" in ln for ln in sum(said, [])), "a heart still shut: the Relic Stone waits (XD's Heart Gauge)")
sh.shadow["gauge"] = 0
said = relic_stone()
pm = g.current_state
pm.on_select(1)
ty = story.player_team[1]
check(ty.id == 248 and ty.level == 70 and ty.moves == ["CRUNCH", "EARTHQUAKE"] and set(ty.ivs.values()) == {31},
      f"Shadow Tyranitar -> Tyranitar, same level, moves and IVs ({ty.id} Lv {ty.level})")
check(story.pc_pokemon[0].id == 9406, "a Shadow Pokemon you didn't choose stays Shadow")
said = relic_stone()
check(type(g.current_state).__name__ != "PokemonPartyMenuState" and "None of the Pokemon" in said[-1][-1],
      "nothing in the party to purify")

print("4) Tournaments, story gates, the League and Jirachi")
for town, gate in (("PYRITE_TOWN", "orre_power_on"), ("UNDER_COLOSSEUM", "orre_dakim_mt_battle"),   # (Pyrite: the windmill's power, batch 1)
                   ("PHENAC_CITY", "got_snag_machine"), ("ORRE_COLOSSEUM", "beat_gonzap")):   # (Phenac first: story rework 11-24)
    req = prog[town]["gym"]["requirements"]
    check(req.get("flag") == gate, f"{town}: its tournament opens after {gate}")
story.badges["ORRE"] = ["PHENAC", "PYRITE", "AGATE"]
story.current_area_key = "REALGAM_TOWER"
c = ow.CityState(g)
g.change_state(c)
said = []
c.show_message = lambda lines, callback=None: said.append(lines)
c.start_gym_battle()
check(said and "lift" in str(said[-1]), "Realgam's Colosseum sealed until the way up through the tower (Gonzap, then the lift)")
gy = prog["REALGAM_TOWER"]["gym"]
check(gy["leader"]["team"][0] == 9399 and gy["leader"]["victory_flag"] == "orre_evice_beaten",
      "Part 1 ends on Evice (Colosseum's team, his Shadow Tyranitar first)")
lg = prog["REALGAM_TOWER"]["gym_league"]
check(lg["requirements"]["badges"] == 8 and [t["name"] for t in lg["trainers"]][:4] ==
      ["Elite Four Justy", "Elite Four Eagun", "Elite Four Miror B.", "Elite Four Vander"] and lg["leader"]["name"] == "Champion Eldes",
      "Part 2: the Orre League in Realgam - Justy, Eagun, Miror B., Vander, then Champion Eldes (S5)")
f = figures("RELIC_FOREST")
check("THE WISHING STAR" in f and "MEET JIRACHI" not in f, f"no Jirachi yet, on the walked forest ({f})")
story.story_flags["orre_part2"] = True   # (Jirachi wakes in Part 2, once Evice is beaten)
run("RELIC_FOREST", "THE WISHING STAR")
f = figures("RELIC_FOREST")
check("MEET JIRACHI" in f, f"in Part 2: Jirachi stands in the forest ({f})")

print("5) Visiting every Orre area, as its walked map")
for k in ORRE:
    try:
        st = walked(k)
        check(type(st).__name__ in ("WalkTownState", "DungeonState"), f"{k} opens as its walked map ({type(st).__name__})")
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("FAILURES:", fails)
