"""Headless menu screenshots for one exported commit.

usage: python shoot.py <game_dir> <out_dir>
Renders each menu at 1280x720 with SDL's dummy drivers and saves <menu>.png,
plus <menu>.err with the traceback when a menu can't be built.
"""
import os
import sys
import traceback
import importlib

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

game_dir, out_dir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
os.makedirs(out_dir, exist_ok=True)
os.chdir(game_dir)
sys.path.insert(0, game_dir)

import pygame

# Older builds sized the window from the monitor: pin every version to the 1280x720 canvas.
_RealInfo = pygame.display.Info


class _Info:
    def __init__(self):
        real = _RealInfo()
        for k in dir(real):
            if not k.startswith("_"):
                try:
                    setattr(self, k, getattr(real, k))
                except Exception:
                    pass
        self.current_w, self.current_h = 1280, 720


pygame.display.Info = _Info
_real_set_mode = pygame.display.set_mode


def _set_mode(size=(0, 0), flags=0, *a, **k):
    return _real_set_mode((1280, 720))


pygame.display.set_mode = _set_mode

log = open(os.path.join(out_dir, "_log.txt"), "w", encoding="utf-8")


def note(msg):
    log.write(msg + "\n")
    log.flush()
    print(msg)


def find_class(name):
    for mod in ("src.states.menus", "src.states.systems", "src.states.overworld", "src.states.battle"):
        try:
            m = importlib.import_module(mod)
        except Exception:
            continue
        if hasattr(m, name):
            return getattr(m, name)
    raise LookupError(name)


from src.core.game import Game

game = Game()
note(f"screen {game.screen.get_size()}")
story = game.story_manager


def setup_story():
    global story
    story = game.story_manager
    try:
        cfg = game.loader.area_data.get("GAME_CONFIG", {})
        story.initialize_new_game(cfg)
    except Exception as e:
        note(f"initialize_new_game failed: {e!r}")
    game.player_name = "JORDAN"
    for attr, val in (("current_region", "KANTO"), ("region", "KANTO")):
        if hasattr(story, attr):
            try:
                setattr(story, attr, val)
            except Exception:
                pass
    story.current_area_key = "VIRIDIAN_CITY"
    from src.pokemon.data import Pokemon
    team = []
    for pid, lvl in ((6, 36), (25, 22), (9, 34), (143, 30), (130, 28), (65, 33)):
        raw = game.loader.fetch_specific(pid)
        try:
            p = Pokemon(raw, game.assets)
        except TypeError:
            p = Pokemon(raw, game.assets, size_mult=2)
        for fn in ("set_level",):
            if hasattr(p, fn):
                try:
                    getattr(p, fn)(lvl)
                except Exception:
                    pass
        team.append(p)
    team[1].current_hp = max(1, int(getattr(team[1], "max_hp", 40) * 0.4)) if hasattr(team[1], "current_hp") else None
    story.player_team[:] = team
    try:
        story.money = 12345
    except Exception:
        pass
    inv = getattr(story, "inventory", None)
    if isinstance(inv, dict):
        for item, n in (("POTION", 5), ("SUPER_POTION", 3), ("FULL_HEAL", 2), ("REVIVE", 1),
                        ("RARE_CANDY", 2), ("ANTIDOTE", 2), ("GREAT_BALLS", 4)):
            inv[item] = n
    return Pokemon


def step(n):
    for _ in range(n):
        if hasattr(game, "_frame"):
            game._frame()
        else:
            st = game.current_state
            if not game.ui_manager.handle_events([]):
                st.handle_events([])
            st.update()
            st.draw()
        pygame.time.wait(8)


def shoot(name, make, frames=45, after=None):
    if only and name not in only:
        return
    try:
        state = make()
        game.change_state(state)
        step(frames)
        if after:
            after(game.current_state)
            step(20)
        pygame.image.save(game.screen, os.path.join(out_dir, f"{name}.png"))
        note(f"ok {name} ({type(game.current_state).__name__})")
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        with open(os.path.join(out_dir, f"{name}.err"), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        note(f"FAIL {name}: {e!r}")


shoot("main_menu", lambda: find_class("MainMenuState")(game))
shoot("character_select", lambda: find_class("CharacterSelectionState")(game))

Pokemon = setup_story()
prev = find_class("MainMenuState")(game)


def mart():
    cls = find_class("PokeMartState")
    return cls(game, prev)


def open_shop(st):
    # Skip the clerk's greeting so the item list shows.
    for attr in ("dialogue_box",):
        db = getattr(st, attr, None)
        cb = getattr(db, "callback", None)
        if callable(cb):
            try:
                cb()
            except Exception as e:
                note(f"mart callback: {e!r}")


shoot("mart_greeting", mart)
shoot("mart_shop", mart, after=open_shop)
shoot("pokemon_center", lambda: find_class("PokeCenterState")(game, prev), frames=30)
shoot("party", lambda: find_class("PokemonPartyMenuState")(game, prev))
shoot("bag", lambda: find_class("BagState")(game, prev))


def wild():
    raw = game.loader.fetch_specific(16)
    try:
        foe = Pokemon(raw, game.assets)
    except TypeError:
        foe = Pokemon(raw, game.assets, size_mult=2)
    if hasattr(foe, "set_level"):
        try:
            foe.set_level(30)
        except Exception:
            pass
    return find_class("WildBattleState")(game, foe, "ROUTE_1")


shoot("battle", wild, frames=400)
note("done")
