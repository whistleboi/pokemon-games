
from src.states import overworld as ow
from src.states import gym_puzzles as gp
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.states.menus import RegionSelectionState
from src.states.systems import BadgeCaseState, PokeMartState
from src.pokemon import evolution
from src.world import levels
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
ORANGE = [k for k, a in prog.items() if a.get("region") == "ORANGE"]


def battle_of(st):
    return st.next_state if isinstance(st, TrainerIntroState) else st


def lineup(b):
    return [(p.id, p.level) for p in b.opponent_team]


def travel_texts(area):
    story.current_area_key = area
    c = ow.CityState(g)
    return [o["text"] for o in prog[area].get("travel_options", []) if c._check_menu_condition(o.get("condition"))]


print("1) A full region (the Pokemon Orange hack, 10-27)")
pick = RegionSelectionState(g, mode="new")
check("ORANGE" in pick.regions and pick.regions.index("ORANGE") == pick.regions.index("KANTO") + 1,
      f"a new-game region, between Kanto and Johto: {pick.regions}")
cfg = story.get_region_start("ORANGE")
check(cfg.get("starters") == [1, 4, 7] and cfg.get("start_area") == "VALENCIA_ISLAND" and not cfg.get("travel_only"),
      "Professor Ivy's Bulbasaur, Charmander or Squirtle on Valencia")
check(len(ORANGE) >= 50, f"{len(ORANGE)} Orange areas")
bad = [(k, o.get("target_area")) for k in ORANGE for o in (prog[k].get("travel_options", []) + prog[k].get("route_menu", []))
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(sum(len(prog[k].get("trainer_pool") or []) for k in ORANGE) >= 60, "the hack's route trainers")

print("2) From Kanto: the S.S. Anne")
story.story_flags = {"beat_champion": True}
story.badges = {"KANTO": ["x"] * 8, "JOHTO": []}
story.current_area_key = "VERMILLION_CITY"
story.starting_region = "KANTO"
check("S.S. Anne to the Orange Islands" in travel_texts("VERMILLION_CITY"), "Kanto Champion: the S.S. Anne sails to Orange")
pick = RegionSelectionState(g, mode="move", return_state=ow.CityState(g))
check("ORANGE" in pick.regions and pick._travel_only("ORANGE"), "Mom's picker sends a Kanto player to the S.S. Anne")
story.story_flags = {}
check("S.S. Anne to the Orange Islands" not in travel_texts("VERMILLION_CITY"), "no title: no voyage")

print("3) Gyms: the hack's Orange Crew")
story.badges = {"ORANGE": []}
story.player_team = [mk(6)]
story.enter_region("ORANGE")
for area, kind, want in (("MIKAN_ISLAND", "cissy", [(116, 15), (8, 18), (72, 13)]),
                         ("KUMQUAT_ISLAND", "luana", [(65, 56), (105, 54), (776, 54), (357, 54)])):
    story.current_area_key = area
    story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"][:0 if area == "MIKAN_ISLAND" else 3]
    story.story_flags[f"gym_progress_{area}"] = len(prog[area]["gym"]["trainers"])
    lobby = ow.GymLobbyState(g, None)
    g.change_state(lobby)
    lobby.challenge_gym()
    pz = g.current_state
    if isinstance(pz, gp.GymPuzzleState):
        check(pz.kind == kind, f"{area}: {kind} challenge first")
        while not pz.finished:
            pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
        lobby = ow.GymLobbyState(g, None)
        g.change_state(lobby)
        lobby.challenge_gym()
    got = lineup(battle_of(g.current_state))
    check([p for p, _ in got] == [p for p, _ in want], f"leader: {got}")

print("4) Drake and the Orange League")
story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
story.current_area_key = "PUMMELO_ISLAND"
story.story_flags["gym_progress_PUMMELO_ISLAND"] = 0
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
check(lobby.is_league, f"Pummelo is a league: {lobby.status_text}")
lobby.challenge_gym()
b = battle_of(g.current_state)
check([p for p, _ in lineup(b)] == [132, 208, 94, 3, 466, 149], f"Drake, the hack's team: {lineup(b)}")
check(prog["PUMMELO_ISLAND"]["gym"]["leader"]["levels"][-1] == 65 and levels.CHAMPION_ACE["ORANGE"] == 65, "Drake's ace Lv 65")
rival = [e["trainer"] for k in ORANGE for e in (prog[k].get("on_enter_event") or []) if isinstance(e, dict)
         and e["trainer"].get("name") == "{rival_name}"]
check(len(rival) == 5 and all(set(t["team_choice"]) == {"1", "4", "7"} for t in rival), "rival Cross: 5 battles, by starter")

print("5) Region rules")
c = ow.CityState(g)
bc = BadgeCaseState(g, c)
check("ORANGE" in bc.unlocked_regions and len(bc.badge_sprites["ORANGE"]) == 5, "badge case: 5 Orange badges")
story.current_area_key = "MIKAN_ISLAND"
items = PokeMartState(g, None)._shop_items()
check("RARE_CANDY" not in items, "island mart: no Rare Candy")

print("6) Special islands")
raw = g.loader.fetch_specific(9103)
check(raw["name"] == "PINKAN BUTTERFREE" and raw["img"], f"Pinkan form: {raw['name']}")
raw = g.loader.fetch_specific(9201)
check(raw["name"] == "CRYSTAL ONIX" and raw["types"] == ["ROCK", "ICE"], f"Crystal Onix: {raw['types']}")
story.current_area_key = "PINKAN_RESERVE"
ps = ow.PlayState(g)
catch = next(o for o in prog["PINKAN_RESERVE"]["route_menu"] if o["action"] == "CATCH")
story.inventory.pop("PINKAN_PERMIT", None)
check(not ps._check_route_condition(catch["condition"], False), "no permit: can't catch Pinkan Pokemon")
story.story_flags["met_pinkan_jenny"] = True
rocket = next(o for o in prog["PINKAN_RESERVE"]["route_menu"] if o["text"] == "STOP TEAM ROCKET")
g.change_state(ps)
ow._run_story_event(ps, rocket["event"], lambda x: ps._check_route_condition(x, False), lambda l: None)
check(lineup(battle_of(g.current_state))[0][0] == 24, "Team Rocket battle")
story.story_flags["defeated_pinkan_rocket"] = True
story.current_area_key = "PINKAN_ISLAND"
cs = ow.CityState(g)
permit = next(o for o in prog["PINKAN_ISLAND"]["explore_options"] if o["text"] == "Get the Research Permit")
ow._run_story_event(cs, permit["event"], cs._check_menu_condition, lambda l: None)
story.current_area_key = "PINKAN_RESERVE"
check(ow.PlayState(g)._check_route_condition(catch["condition"], False), "permit: catching allowed")
story.current_area_key = "SHAMOUTI_SHRINE"
ps = ow.PlayState(g)
lugia = next(o for o in prog["SHAMOUTI_SHRINE"]["route_menu"] if o["text"] == "CHALLENGE LUGIA")
check(not ps._check_route_condition(lugia["condition"], False), "no song yet: no Lugia")
for tr in ("FIRE_TREASURE", "ICE_TREASURE", "LIGHTNING_TREASURE"):
    story.inventory[tr] = 1
place = next(o for o in prog["SHAMOUTI_SHRINE"]["route_menu"] if o["text"] == "PLACE THE TREASURES")
ow._run_story_event(ps, place["event"], lambda x: ps._check_route_condition(x, False), lambda l: None)
check(ps._check_route_condition(lugia["condition"], False), "three treasures, the song: Lugia appears")
story.current_area_key = "VALENCIA_ISLAND"
cs = ow.CityState(g)
story.inventory.pop("GS_BALL", None)
ivy = next(o for o in prog["VALENCIA_ISLAND"]["explore_options"] if o["text"] == "Professor Ivy's Lab")
ow._run_story_event(cs, ivy["event"], cs._check_menu_condition, lambda l: None)
check(story.inventory.get("GS_BALL") == 1, "Professor Ivy gives the GS Ball")

print("7) Visiting every Orange area")
for k in ORANGE:
    story.current_area_key = k
    try:
        st = ow.CityState(g) if prog[k]["area_type"] == "town" else ow.PlayState(g)
        g.change_state(st)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("FAILURES:", fails)
