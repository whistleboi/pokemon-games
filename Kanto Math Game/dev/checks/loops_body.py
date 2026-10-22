
import importlib
from src.ui.dialogue import ClassicDialogueBox
from src.states import overworld as ow
from src.states.overworld import CityState, PlayState, PokeCenterState, AreaTransitionState
from src.states.battle import TrainerBattleState
from src.states.menus import DifficultySelectionState, open_difficulty_options
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


prog = g.loader.area_data["STORY_PROGRESSION"]

print("1) whiteout -> last Pokemon Center")
story.last_center = None
story.current_area_key = "ROUTE_1"
check(story.whiteout_destination() == ("PALLET_TOWN", False), f"no center yet -> home: {story.whiteout_destination()}")
story.current_area_key = "VIRIDIAN_CITY"
g.change_state(CityState(g))
g.change_state(PokeCenterState(g, g.current_state))
check(story.last_center == "VIRIDIAN_CITY", "using a center records it")
story.current_area_key = "ROUTE_2"
story.player_team = [mk(25)]
story.player_team[0].current_hp = 0
b = TrainerBattleState(g, [mk(19)], "YOUNGSTER", "Joey", "ROUTE_2")
g.change_state(b)
b.perform_battle_black_out()
cs = g.current_state
check(isinstance(cs, PokeCenterState) and story.current_area_key == "VIRIDIAN_CITY",
      f"battle whiteout lands in Viridian's center ({type(cs).__name__}, {story.current_area_key})")
check(any("tough battle" in l for l in cs.dialogue_box.text_lines), f"nurse line: {cs.dialogue_box.text_lines}")
check(story.player_team[0].current_hp == story.player_team[0].get_max_hp(), "team healed")
cs.finish_heal()
check(isinstance(g.current_state, CityState), "after the nurse you're in the town")

# a center from another region doesn't count
story.last_center = "VIRIDIAN_CITY"
jkey = next(k for k, a in prog.items() if str(a.get("region", "")).upper() == "JOHTO" and a.get("area_type") != "town")
story.current_area_key = jkey
dest = story.whiteout_destination()
check(story.area_region(dest[0]) == "JOHTO", f"in Johto, a Kanto center is skipped -> {dest}")

# overworld whiteout with no center -> home with Mom
story.last_center = None
story.current_area_key = "ROUTE_1"
g.change_state(PlayState(g))
g.current_state.perform_black_out()
boxes = [e for e in g.ui_manager.elements if isinstance(e, ClassicDialogueBox) and e.visible]
check(story.current_area_key == "PALLET_TOWN" and boxes and any("Mom" in l for l in boxes[-1].text_lines),
      "no center used yet -> home, Mom heals")
check(story.serialize()["last_center"] is None and "autosave" in story.serialize(), "saved fields present")

print("2) journal")
story.current_area_key = "PALLET_TOWN"
ms = story.region_missions()
regions = {m.get("region") for m in ms}
check(ms and regions == {"KANTO"}, f"Kanto shows only Kanto missions ({len(ms)}, {regions})")
story.current_area_key = next(k for k, a in prog.items() if str(a.get("region", "")).upper() == "SINNOH")
sm = story.region_missions()
check(sm and {m.get("region") for m in sm} == {"SINNOH"}, f"Sinnoh shows only Sinnoh missions ({len(sm)})")
hisui = next(m for m in sm if m["id"] == "sinnoh_hisui")
story.story_flags["visited_JUBILIFE_CITY"] = True
story.badges["SINNOH"] = []
check(not story.check_requirements(hisui["condition"], region="SINNOH"), "Hisui waits for the Coal Badge")
story.badges["SINNOH"] = ["COAL"]
check(story.check_requirements(hisui["condition"], region="SINNOH"), "Hisui opens with the Coal Badge")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]
check(len(story.badges["SINNOH"]) == 1 and story.check_requirements({"badges_less": 2}, region="SINNOH"),
      "a region's missions count that region's badges only")
story.get_active_missions(); story.get_all_journal_entries()

print("3) options")
story.current_area_key = "VIRIDIAN_CITY"
city = CityState(g); g.change_state(city)
open_difficulty_options(g, city)
op = g.current_state
check(isinstance(op, DifficultySelectionState) and op.in_game, "in-game Options has QUIT/AUTOSAVE")
was = story.autosave
op.toggle_autosave()
check(story.autosave != was and op.btn_autosave.text.endswith("OFF" if was else "ON"), op.btn_autosave.text)
op.open_quit_prompt(); op.draw()
check(op.quit_prompt, "quit prompt opens and draws")
op.close_quit_prompt(); check(not op.quit_prompt, "cancel closes it")
newgame = DifficultySelectionState(g, lambda: None, lambda: None)
newgame.draw()
check(not newgame.in_game, "new-game difficulty screen has no quit button")

print("4) autosave on travel")
saves = []
g.data.save = lambda: saves.append(story.current_area_key)
story.autosave = True
t = AreaTransitionState(g, "ROUTE_2"); g.change_state(t)
for _ in range(400):
    if g.current_state is not t:
        break
    t.dialogue_box.is_finished = True
    t.update()
check(saves == ["ROUTE_2"], f"saved once on arrival: {saves}")
story.autosave = False
t = AreaTransitionState(g, "VIRIDIAN_CITY"); g.change_state(t)
for _ in range(400):
    if g.current_state is not t:
        break
    t.update()
check(saves == ["ROUTE_2"], "autosave off -> no save")

print("FAILURES:", fails)
