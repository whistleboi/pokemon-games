
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
check(25 <= len(ORRE) <= 35, f"{len(ORRE)} Orre areas")
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
check("Pyrite Town" not in bike("PHENAC_CITY"), "Pyrite waits for the Snag Machine (Phenac's bike)")
# (11-23: the old menu steps "Trouble at the Fountain" / "Meet Rui" are gone; Phenac's walked story - Folly, Rui, the
#  Mystery Troop guards - is played by orre_pilot. The Snag Machine comes with the new game; a guard's win sets the flag.)
check(not any(o.get("text") in ("Trouble at the Fountain", "Meet Rui") for o in g.loader.area_data["STORY_PROGRESSION"]["PHENAC_CITY"]["explore_options"]),
      "Phenac's old menu steps are gone")
story.inventory["SNAG_MACHINE"] = 1
story.story_flags["got_snag_machine"] = True
check("Pyrite Town" in bike("PHENAC_CITY"), "the Snag Machine opens the bike ride to Pyrite")
m = figures("ORRE_DESERT")
check(m.count("SNAG SHADOW POKEMON") == 1, f"desert: one snag figure for its Shadow pool, on the walked map: {m}")
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
check(said and "lift" in str(said[-1]), "Realgam's rooftop sealed until the way up through the tower (batch 7b: Gonzap, then the roof lift)")
story.badges["ORRE"].append("ORRE")
story.story_flags["xd_gorigan_beaten"] = True
story.story_flags["col_gonzap_realgam"] = True
story.story_flags["gym_progress_REALGAM_TOWER"] = len(prog["REALGAM_TOWER"]["gym"]["trainers"])
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check([p for p, _ in lineup(battle_of(g.current_state))] == [9399, 373, 68, 212, 289, 199], "Champion Evice (Colosseum's team, his Shadow Tyranitar first: batch 7b)")
check(prog["REALGAM_TOWER"]["gym"]["leader"]["victory_flag"] == "beat_orre_champion", "Evice's defeat makes you Orre's Champion")
f = figures("RELIC_FOREST")
check("THE WISHING STAR" in f and "MEET JIRACHI" not in f, f"no Jirachi yet, on the walked forest ({f})")
story.story_flags["beat_orre_champion"] = True
run("RELIC_FOREST", "THE WISHING STAR")
f = figures("RELIC_FOREST")
check("MEET JIRACHI" in f, f"after the title: Jirachi stands in the forest ({f})")

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
