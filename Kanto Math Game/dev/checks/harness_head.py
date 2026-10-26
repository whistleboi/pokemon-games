import os, sys
S = sys.argv[1]
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.getcwd())
import pygame
pygame.display.init(); pygame.display.set_mode((1280, 720))
from src.core.data import DataManager
DataManager.save = lambda self, *a, **k: None
DataManager.wipe_data = lambda self, *a, **k: self.data.update({"pokedex": {}, "story": {}})
pygame.display.Info = lambda: type("I", (), {"current_w": 1280, "current_h": 720})()
import src.core.game as gm
from src.pokemon.data import Pokemon
from src.states.menus import RegionSelectionState
from src.states.battle import WildBattleState
from src.states.systems import PokeMartState, BagState

g = gm.Game()
g.start_new_game(); g.player_name, g.player_character = "ASH", "red"
rs = RegionSelectionState(g); rs.selected_idx = 2; rs.confirm_selection()
g.current_state.input_name = "GARY"; g.current_state.confirm_selection(); g.current_state.on_confirm()
st = g.current_state
if not hasattr(st, "load_starters"):  # Hoenn starts at home (Route 101's starter): pick it straight away
    from src.states.menus import StarterSelectionState
    st = StarterSelectionState(g, starter_ids=g.story_manager.get_region_start("HOENN")["starters"], region="HOENN")
st.load_starters(); st.selected_idx = 2; st.complete_selection()
story = g.story_manager
story._migrate_hoenn_start()  # the suites start past the opening (Pokedex in hand), like older saves
for _r in story.RIVAL_CHOICES:  # every region's rival already picked (no rival screen in the suites)
    story.assign_region_rival(_r)["chosen"] = True
mk = lambda pid: Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)


def drive(b, frames=800):
    seen = []
    for _ in range(frames):
        if b.dialogue_box.visible:
            for line in b.dialogue_box.text_lines:
                if not seen or seen[-1] != line:
                    seen.append(line)
            b.dialogue_box.is_finished = True
        if b.phase == "MESSAGE" and b.dialogue_box.callback:
            cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update()
        if b.phase == "MENU" and not b.turn_actions and not b.dialogue_box.visible:
            break
    return seen


def battle(area, player_id, foe_id):
    story.current_area_key = area
    story.player_team = [mk(player_id)]
    b = WildBattleState(g, mk(foe_id), area)
    g.change_state(b)
    return b



# Most suites jump between regions with one test save: give it one shared storage (linked).
_store = story._store()
story.linked_regions = set(g.loader.area_data.get("REGION_START", {}))
story.region_stores[story.LINKED] = _store
