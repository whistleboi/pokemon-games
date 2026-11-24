# Shared helpers for the route-walker suites (dungeon, dungeon_kanto, dungeon_johto): split 11-23 so a change runs
# only the part it touches. Each suite reads this with exec(open("dev/checks/dungeon_lib.py").read()).
import random as _rnd
from src.states.overworld import PlayState, AreaTransitionState
from src.states.overworld.dungeon import DungeonState
from src.dungeon import core
from src.pokemon import catching, tms
from src.states.battle import WildBattleState

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def talk(p, n=60):
    """Read the text box to the end."""
    for _ in range(n):
        if not p.dialogue_box.visible:
            return
        p.dialogue_box.advance()


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def kanto(area, came="PALLET_TOWN"):
    story.current_area_key = area
    story.last_area_key = came
    story.player_team = [mk(4)]
    story.player_team[0].level = 12
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    return p


def beside(p, kind):
    """Put a mover of this kind right beside you (east), on a walkable tile."""
    f = p.run.floor
    m = next(x for x in f.movers if x.kind == kind)
    px, py = p.run.player
    for dx, dy in core.DIRS:
        t = (px + dx, py + dy)
        if f.walkable(*t) and not f.occupied(*t):
            m.x, m.y = t
            return m, (dx, dy)
    raise RuntimeError("no room")

from src.states.overworld import dungeon as _dg
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
_prog = g.loader.area_data["STORY_PROGRESSION"]


def _tap_through(st, n=400):
    """Tap through whatever the town says first (a call, a milestone), as a player would."""
    for _ in range(n):
        if not st.npc_active:
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)
