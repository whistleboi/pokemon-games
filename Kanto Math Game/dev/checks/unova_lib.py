# Helpers that grottoes, royal_unova, unovab3b, unovab4a, unovab4b, unovab4c, unovab5a, unovab5b, unovab6a, unovab6b, unovab7a, unovab7b, unovab8a, unovab8b, unovab9a, unovab9b, unovab9c shared word for word (Checks C5, 11-24;
# made by dev/checks/share_helpers.py). Each suite runs: exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())
# They use the suite's own globals (g, story, fails, check...). Change one here and every suite gets it.

def settle(n=60):
    for _ in range(n):
        st = g.current_state
        box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
        if box is not None and getattr(box, "visible", True):
            for line in getattr(box, "text_lines", []) or []:
                if not said or said[-1] != line:
                    said.append(line)
        db = getattr(st, "dialogue_box", None)
        if db is not None and getattr(db, "visible", False):
            db.advance()
        elif getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()


def heard():
    return " ".join(said)


def town(area, at, room=None, face=(0, 1)):
    story.current_area_key = area
    g.walk_town_pos = (area, tuple(at), face)
    g.walk_town_room = (area, room) if room else None
    said.clear()
    g.change_state(CityState(g)); settle(30)
    return g.current_state


def until(names, n=600):
    for _ in range(n):
        if type(g.current_state).__name__ in names:
            return g.current_state
        settle(1)
    return g.current_state


def _opts(o):
    return o.get("any") if isinstance(o, dict) and "any" in o else o if isinstance(o, list) else [o]


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label.rstrip() and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(80)
    return True


def walked(area, at, floor=0):
    story.current_area_key = area; g.walk_town_pos = g.walk_town_room = None
    g.arrive_floor = (area, floor, list(at))
    said.clear()
    g.change_state(PlayState(g)); settle(30)
    return g.current_state


def team_of(b):
    b = getattr(b, "next_state", None) or b
    return [(int(getattr(p, "id", 0)), int(getattr(p, "level", 0))) for p in (getattr(b, "opponent_team", None) or [])]


def win(cur):
    from src.states.battle import TrainerIntroState
    b = cur
    for _ in range(3):
        if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
            b = b.next_state; g.change_state(b); settle(1)
    b.player_won = True
    if hasattr(b, "exit_battle"):
        b.exit_battle()
    settle(400)


def battle_talk(area, at, room, label, want_id, flag, frozen=None):
    st = town(area, at, room)
    ok = talk(st, label)
    cur = until(BATTLES, 800)
    t = team_of(cur)
    check(ok and type(cur).__name__ in BATTLES and want_id in [s for s, _ in t], f"{label}: Black 2's team ({t})")
    if type(cur).__name__ in BATTLES:
        win(cur)
    if flag:
        check(flags.get(flag), f"{label} beaten ({flag})")


def go(dx, dy, times=1, n=40):
    for _ in range(times):
        g.current_state.step(dx, dy)
        settle(n)
    return g.current_state
