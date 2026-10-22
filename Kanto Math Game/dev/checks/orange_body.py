
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


print("1) Getting there")
story.story_flags = {"beat_champion": True}
story.badges = {"KANTO": ["x"] * 8, "JOHTO": []}
check("Ship to the Orange Islands" not in travel_texts("VERMILLION_CITY"), "Kanto title only: no ferry yet")
story.story_flags["beat_johto_champion"] = True
check("Ship to the Orange Islands" in travel_texts("VERMILLION_CITY"), "both titles: ferry from Vermilion")
check("Ship to the Orange Islands" in travel_texts("OLIVINE_CITY"), "and from Olivine")
check(len(ORANGE) == 21, f"{len(ORANGE)} Orange areas")
bad = [(k, o.get("target_area")) for k in ORANGE for o in (prog[k].get("travel_options", []) + prog[k].get("route_menu", []))
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")

print("2) Ships follow the badges")
story.badges["ORANGE"] = []
t = travel_texts("VALENCIA_ISLAND")
check("Ship to Mikan Island" in t and "Ship to Navel Island" not in t and "Ship to Vermilion City" in t, f"start: {t}")
story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
t = travel_texts("MIKAN_ISLAND")
check(sum(x.startswith("Ship to") for x in t) == 8, f"4 badges: Mikan sails to all 8 other islands")
c = ow.CityState(g)
c.open_travel_menu()
rects = [b.rect for b in c.hover_buttons]
check(all(r.top >= 0 for r in rects) and len(rects) == len(t), f"{len(rects)} buttons fit on screen (top {min(r.top for r in rects)})")

print("3) Gyms: Orange Crew challenges, then the leader")
story.badges["ORANGE"] = []
story.player_team = [mk(6)]
for area, kind, want in (("MIKAN_ISLAND", "cissy", [(117, 60), (9, 62)]),
                         ("KUMQUAT_ISLAND", "luana", [(65, 71), (105, 72)])):
    story.current_area_key = area
    story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"][:0 if area == "MIKAN_ISLAND" else 3]
    story.story_flags[f"gym_progress_{area}"] = 2
    lobby = ow.GymLobbyState(g, None)
    g.change_state(lobby)
    lobby.challenge_gym()
    pz = g.current_state
    check(isinstance(pz, gp.GymPuzzleState) and pz.kind == kind, f"{area}: {kind} challenge first")
    while not pz.finished:
        pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
    check(story.story_flags.get(f"gym_puzzle_{area}"), "challenge solved")
    lobby = ow.GymLobbyState(g, None)
    g.change_state(lobby)
    lobby.challenge_gym()
    got = lineup(battle_of(g.current_state))
    check(got == want, f"leader: {got}")
pz = gp.GymPuzzleState(g, "NAVEL_ISLAND", "danny", lambda s: None)
pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
pz.answer(next(i for i, o in enumerate(pz.options) if not o[1]))
check(pz.step == 0, "Danny: a wrong ledge slides you back down")
story.current_area_key = "NAVEL_ISLAND"
story.badges["ORANGE"] = []
c = ow.CityState(g)
g.change_state(c)
c.open_gym() if hasattr(c, "open_gym") else None

print("4) Drake and the Orange League")
story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
story.current_area_key = "PUMMELO_ISLAND"
story.story_flags["gym_progress_PUMMELO_ISLAND"] = 0
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
check(lobby.is_league, f"Pummelo is a league: {lobby.status_text}")
lobby.challenge_gym()
b = battle_of(g.current_state)
check(lineup(b) == [(132, 72), (95, 72), (94, 73), (3, 74), (125, 73), (149, 76)], f"Drake: {lineup(b)}")
b.player_won = True
b.perform_battle_outcome() if hasattr(b, "perform_battle_outcome") else None
story.story_flags["beat_orange_champion"] = True
story.badges["ORANGE"].append("WINNERS_TROPHY")
check(levels.story_level_cap(story) == 100, "after the trophy: no level cap")
story.story_flags.pop("move_offer_orange", None)
c = ow.CityState(g)
g.change_state(c)
said = []
c.show_message = lambda lines, callback=None: said.append(lines)
offered = []
c._offer_move = lambda *a, **k: offered.append(a)
story.story_flags.pop("move_offer_orange", None)
c.start()
check(said and "Winner's Trophy" in said[0][0] and not offered, f"champion message, no move: {said[:1]}")
story.story_flags["gym_progress_PUMMELO_ISLAND"] = 1
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
check(lineup(battle_of(g.current_state))[-1] == (149, 86), "rematch: Drake +10 levels")

print("5) Region rules")
pick = RegionSelectionState(g, mode="new")
check("ORANGE" not in pick.regions, f"not a new-game region: {pick.regions}")
pick = RegionSelectionState(g, mode="move", return_state=c)
check("ORANGE" not in pick.regions, "Mom never moves there")
story.enter_region("ORANGE")
bc = BadgeCaseState(g, c)
check("ORANGE" in bc.unlocked_regions and len(bc.badge_sprites["ORANGE"]) == 5, "badge case: 5 Orange badges")
story.current_area_key = "MIKAN_ISLAND"
check(not evolution.evolution_allowed(g, 471) or "SINNOH" in story.visited_regions(), "visiting Orange unlocks no later-gen evolutions (Glaceon)")
items = PokeMartState(g, None)._shop_items()
check("RARE_CANDY" not in items, "island mart: no Rare Candy")
story.current_area_key = "PUMMELO_ISLAND"
check("RARE_CANDY" in PokeMartState(g, None)._shop_items(), "Pummelo (League) sells Rare Candy")

print("6) Special islands")
raw = g.loader.fetch_specific(9101)
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
