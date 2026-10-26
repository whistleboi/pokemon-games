
from src.states import overworld as ow
from src.states.overworld import CityState, PlayState, AreaTransitionState
from src.states.menus import StarterSelectionState, region_opening_state
from src.states.battle import WildBattleState, TrainerIntroState, TrainerBattleState
from src.states.hoenn import WallyCatchState
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

# A brand-new Hoenn game: no starter, nothing done.
for f in list(story.story_flags):
    if "hoenn" in f or f in ("helped_wally", "defeated_wally_mauville", "pending_starter"):
        story.story_flags.pop(f)
story.story_flags["hoenn_version"] = "ALPHA_SAPPHIRE"
story.player_team = []
story.balls_left = 0
story.current_area_key = "LITTLEROOT_TOWN"


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


print("1) a new game starts at home, with no starter")
st = region_opening_state(g, "HOENN")
check(isinstance(st, AreaTransitionState) and st.next_area_key == "LITTLEROOT_TOWN", "the opening goes to Littleroot")
c = city("LITTLEROOT_TOWN")
check(g.current_state is c and not story.player_team, "Littleroot: no starter screen, no rival battle")
c.story_event("hoenn_birch_lab")
check(any("Route 101" in l for l in said) and not story.story_flags.get("hoenn_birch_thanked"), "the lab: Birch is out on Route 101")

print("2) Route 101: Birch calls for help, the starter comes from his bag")
r = route("HOENN_ROUTE_101")
sel = g.current_state
check(isinstance(sel, StarterSelectionState) and sel.on_route, f"the starter screen opens on the route ({type(sel).__name__})")
check(any("POOCHYENA" in l for l in said), "Birch is chased by a Poochyena")
sel.load_starters()
sel.selected_idx = 0
sel.complete_selection()
check(story.player_team and story.player_team[0].id == 252 and story.balls_left == 0, "Treecko chosen, no Poke Balls yet")
sel.start_rival_battle()
r = route("HOENN_ROUTE_101")
b = g.current_state
check(isinstance(b, WildBattleState) and b.opponent_pokemon.id == 261 and b.opponent_pokemon.level == 2
      and b.no_catch, "back on the route: a Lv 2 Poochyena that can't be caught")
b.trigger_outro(win=True)
check(story.story_flags.get("hoenn_birch_rescued"), "beating it saves Birch")

print("3) the lab, the rival on Route 103, the Pokedex")
c = city("LITTLEROOT_TOWN")
c.story_event("hoenn_birch_lab")
check(story.story_flags.get("hoenn_birch_thanked") and any("Route 103" in l for l in said), "Birch: go meet my kid on Route 103")
check(not story.catch_unlocked(), "still no catching")
r = route("HOENN_ROUTE_103")
intro = g.current_state
battle = intro.next_state if isinstance(intro, TrainerIntroState) else intro
check(isinstance(battle, TrainerBattleState) and [p.id for p in battle.opponent_team] == [255]
      and battle.opponent_team[0].level == 5, "the rival: Torchic Lv 5 against Treecko")
story.story_flags["hoenn_rival_103"] = True
c = city("LITTLEROOT_TOWN")
c.story_event("hoenn_birch_lab")
check(story.story_flags.get("received_pokedex_hoenn") and story.balls_left == 10 and story.catch_unlocked(),
      "the Pokedex and 10 Poke Balls: catching is open")
oldale = city("OLDALE_TOWN")
check(oldale._check_menu_condition("received_pokedex_hoenn"), "Oldale: the way to Route 102 is open")

print("4) Petalburg: Norman, and Wally catches his Ralts")
p = city("PETALBURG_CITY")
scene = g.current_state
check(isinstance(scene, WallyCatchState), f"arriving starts the scene ({type(scene).__name__})")
for _ in range(3000):
    if g.current_state is not scene:
        break
    scene.update()
    scene.draw()
check(g.current_state is p and story.story_flags.get("helped_wally"), "the scene plays itself and returns to town")
check(any("Rustboro" in l for l in said), "Norman sends you to Rustboro")
p2 = city("PETALBURG_CITY")
check(g.current_state is p2, "it doesn't play twice")

print("5) Mauville: Wally at the Gym door")
story.badges["HOENN"] = ["STONE_BADGE", "KNUCKLE_BADGE"]
m = city("MAUVILLE_CITY")
intro = g.current_state
battle = intro.next_state if isinstance(intro, TrainerIntroState) else intro
check(isinstance(battle, TrainerBattleState) and [(x.id, x.level) for x in battle.opponent_team] == [(280, 17)],
      "Wally's Ralts Lv 17")
check(battle.rewards.get("HM_ROCK_SMASH"), "his uncle's HM Rock Smash")

print("6) rivals follow the starter, and the over-levelled team")
r = route("HOENN_ROUTE_110")
pool = r.area_data["trainer_pool"]
idx = next(i for i, t in enumerate(pool) if t.get("victory_flag") == "defeated_rival_110")
r.trigger_trainer_battle(specific_index=idx)
intro = g.current_state
battle = intro.next_state if isinstance(intro, TrainerIntroState) else intro
check([(x.id, x.level) for x in battle.opponent_team] == [(320, 18), (285, 18), (256, 20)],
      f"Route 110 against Treecko: Wailmer, Shroomish, Combusken ({[(x.id, x.level) for x in battle.opponent_team]})")
story.player_team[0].level = 30
r = route("HOENN_ROUTE_110")
r.trigger_trainer_battle(specific_index=idx)
intro = g.current_state
battle = intro.next_state if isinstance(intro, TrainerIntroState) else intro
check([x.level for x in battle.opponent_team] == [28, 28, 30], "a Lv 30 lead: the rival's ace is lifted to 30")

print("7) older saves skip the new opening")
from src.world.story import StoryManager
s2 = StoryManager()
s2.game = g
s2.story_flags = {"received_starter_hoenn": True}
s2._migrate_hoenn_start()
check(all(s2.story_flags.get(f) for f in StoryManager.HOENN_START_FLAGS), "Pokedex, rival and Birch count as done")
print("FAILURES:", fails)
