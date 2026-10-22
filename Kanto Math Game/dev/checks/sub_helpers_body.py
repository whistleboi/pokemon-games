
from src.states import overworld as ow
from src.states import gym_puzzles as gp
from src.states.battle import TrainerIntroState
from src.world import regional_forms
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
SEVII = [k for k, a in prog.items() if a.get("subregion") == "SEVII"]


def battle_of(st):
    return st.next_state if isinstance(st, TrainerIntroState) else st


def lineup(b):
    return [(p.id, p.level) for p in b.opponent_team]


def state_for(area):
    story.current_area_key = area
    st = ow.CityState(g) if prog[area]["area_type"] == "town" else ow.PlayState(g)
    g.change_state(st)
    return st


def chk(st):
    return st._check_menu_condition if isinstance(st, ow.CityState) else (lambda c: st._check_route_condition(c, False))


def opt(area, text):
    a = prog[area]
    return next(o for o in (a.get("route_menu") or []) + (a.get("explore_options") or []) + (a.get("travel_options") or [])
                if o.get("text") == text)


def run(area, text, solve=True):
    st = state_for(area)
    said = []
    st.show_message = lambda lines, callback=None: said.append(lines)
    ow._run_story_event(st, opt(area, text)["event"], chk(st), lambda l: said.append(l))
    pz = g.current_state
    if isinstance(pz, gp.GymPuzzleState):
        if not solve:
            pz.answer(next(i for i, o in enumerate(pz.options) if not o[1]))
            pz.leave()
            return said
        while not pz.finished:
            pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
        pz.on_done(pz.solved)
    return said


def travel(area):
    st = state_for(area)
    return [o["text"] for o in prog[area].get("travel_options", []) if st._check_menu_condition(o.get("condition"))]




def no_traps(keys):
    """Areas without wild Pokemon must let you leave right away."""
    trapped = []
    for k in keys:
        a = prog[k]
        if a["area_type"] == "town" or a.get("wild_pool_percentages"):
            continue
        st = state_for(k)
        if not any(o["action"] == "EXIT" and st._check_route_condition(o.get("condition"), False) for o in a["route_menu"]):
            trapped.append(k)
    check(not trapped, f"no area traps you {trapped}")
