"""Headless test bootstrap: run `python tests/test_kanto_fixes.py` from the game folder."""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
import pygame  # noqa
from src.core.game import Game
from src.world.story import StoryManager
from src.pokemon.data import Pokemon

def make_game():
    g = Game()
    import tempfile  # never write the real game_data.json from tests
    g.data.save_file = os.path.join(tempfile.gettempdir(), "kanto_tests_game_data.json")
    g.story_manager = StoryManager(); g.story_manager.game = g
    g.story_manager.initialize_new_game(g.loader.area_data.get("GAME_CONFIG", {}))
    return g

def mk(g, pid, lv):
    m = Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5); m.level = lv
    m.current_hp = m.get_max_hp(); return m
