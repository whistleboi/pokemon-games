"""Headless smoke test: new game in every region, start sequence, then visit every area/gym in that region."""
import os
import sys
import traceback

GAME_DIR = sys.argv[1]
ONLY = sys.argv[2:] or None
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.chdir(GAME_DIR)
sys.path.insert(0, GAME_DIR)

import pygame  # noqa: E402
pygame.display.init()
pygame.display.set_mode((1280, 720))

from src.core.data import DataManager  # noqa: E402
DataManager.save = lambda self, *a, **k: None
DataManager.wipe_data = lambda self, *a, **k: self.data.update({"pokedex": {}, "story": {}})

import src.core.game as game_mod  # noqa: E402
pygame.display.Info = lambda: type("I", (), {"current_w": 1280, "current_h": 720})()
from src.states.menus import RegionSelectionState  # noqa: E402
from src.states.overworld import CityState, PlayState, GymLobbyState, AreaTransitionState  # noqa: E402
from src.states.systems import BadgeCaseState, PokedexState  # noqa: E402

game = game_mod.Game()
failures = []


def step_until_changed(max_steps=400):
    start = game.current_state
    for _ in range(max_steps):
        if game.current_state is not start:
            return game.current_state
        if hasattr(start, "dialogue_box"):
            start.dialogue_box.is_finished = True
        start.update()
    return game.current_state


def attempt(label, fn):
    try:
        return fn()
    except Exception:
        failures.append((label, traceback.format_exc()))
        return None


for idx, (region, cfg) in enumerate(game.story_manager.get_region_starts()):
    if (ONLY and region not in ONLY) or cfg.get("travel_only"):
        continue
    print(f"\n===== {region}")
    game.start_new_game()
    game.player_name, game.player_character = "ASH", "red"
    rs = RegionSelectionState(game)
    rs.selected_idx = rs.regions.index(region)
    rs.confirm_selection()
    game.current_state.input_name = "GARY"
    game.current_state.confirm_selection()
    if hasattr(game.current_state, "friend"):  # Kalos / Alola: then the second friend's name
        game.current_state.confirm_selection()
    game.current_state.on_confirm()
    st = game.current_state
    if not hasattr(st, "load_starters"):  # Hoenn: the story choice, home, then the starter on Route 101
        from src.states.overworld import PlayState
        if hasattr(st, "choose"):
            st.choose("OMEGA_RUBY")
            st.finish()
        if isinstance(game.current_state, AreaTransitionState):
            step_until_changed()
        print("  opening ->", type(game.current_state).__name__, "| area:", game.story_manager.current_area_key)
        route = game.story_manager.starter_on_route(region)
        if route:  # Hoenn / Sinnoh: the starter is picked on a route or at a lake
            game.story_manager.current_area_key = route
            ps = PlayState(game)
            game.states["play"] = ps
            game.change_state(ps)
            print("  on the route:", ps.dialogue_box.text_lines[:2])
            ps.dialogue_box.callback()  # the professor's call for help -> his bag of starters
        else:  # Kanto: Oak stops you at Route 1 and takes you to his lab (FRLG)
            from src.states.overworld import CityState
            town = CityState(game)
            game.states["city"] = town
            game.change_state(town)
            town.visit_prof_oak()
            print("  in town:", town.npc_dialogue.text_lines[:1])
            town.npc_dialogue.callback()
            for _ in range(300):
                if hasattr(game.current_state, "load_starters"):
                    break
                game.current_state.update()
        st = game.current_state
    st.load_starters()
    print("  starter screen lines:", st.dialogue_box.text_lines[:2],
          "| starters:", [p.name for p in st.starters])
    st.selected_idx = 1
    st.complete_selection()
    story = game.story_manager
    print("  flags:", {k: v for k, v in story.story_flags.items() if region.lower() in k})
    st.start_rival_battle()
    state = game.current_state
    if isinstance(state, AreaTransitionState):
        state = step_until_changed()
    print("  after starter ->", type(state).__name__, "| area:", story.current_area_key)
    nxt = getattr(state, "next_state", None)
    if nxt is not None:
        print("  rival:", nxt.trainer_name, [p.name for p in nxt.opponent_team],
              "| flag:", nxt.victory_flag, "| sprite:", nxt.trainer_sprite is not None if hasattr(nxt, "trainer_sprite") else "?")
        if nxt.victory_flag:
            story.story_flags[nxt.victory_flag] = True

    story.current_area_key = cfg["start_area"]
    city = CityState(game)
    game.change_state(city)
    print("  re-enter start town ->", type(game.current_state).__name__)
    for opt in city.area_data.get("explore_options", []):
        cb = city._get_callback_for_option(opt)
        if opt.get("action") in ("NPC", "RANDOM_NPC"):
            if cb:
                attempt(f"{region} npc {opt.get('text')}", cb)
                lines = getattr(city.npc_dialogue, "text_lines", None)
                print(f"  NPC '{opt.get('text')}': {str(lines)[:110]}")
                city.npc_active = False
            else:
                print(f"  NPC '{opt.get('text')}': (hidden, no handler/text)")

    areas = [k for k, a in game.loader.area_data["STORY_PROGRESSION"].items()
             if str(a.get("region") or "KANTO").upper() == region]
    gyms = 0
    for k in areas:
        story.current_area_key = k
        a = game.loader.area_data["STORY_PROGRESSION"][k]
        cls = CityState if a.get("area_type") == "town" else PlayState
        s = attempt(f"{region} construct {k}", lambda: cls(game))
        if s is not None:
            attempt(f"{region} start {k}", lambda: game.change_state(s))
        if a.get("gym"):
            gyms += 1
            for prog in range(len(a["gym"].get("trainers", [])) + 1):
                story.story_flags[f"gym_progress_{k}"] = prog
                game.transitioning = False
                lobby = attempt(f"{region} gym {k}#{prog}", lambda: GymLobbyState(game))
                if lobby:
                    attempt(f"{region} challenge {k}#{prog}", lobby.challenge_gym)
            story.story_flags[f"gym_progress_{k}"] = 0
    story.badges[region] = story.get_region_gym_badges(region)[:3]
    attempt(f"{region} badge case", lambda: BadgeCaseState(game, None).draw())
    dex = attempt(f"{region} pokedex", lambda: PokedexState(game, None))
    if dex:
        dex.refresh_dex()
        print(f"  dex entries: {len(dex.full_dex)}")
    print(f"  visited {len(areas)} areas, {gyms} gyms; failures so far: {len(failures)}")

print(f"\n##### {len(failures)} failures")
seen = set()
for label, tb in failures:
    sig = tb.strip().splitlines()[-1]
    if sig in seen:
        print(f"- {label}: (same as above) {sig}")
        continue
    seen.add(sig)
    print(f"- {label}\n{tb}")
