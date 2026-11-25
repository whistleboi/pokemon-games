# Helpers that kanto_events, orange_events, orange_postgame shared word for word (Checks C5, 11-24;
# made by dev/checks/share_helpers.py). Each suite runs: exec(open("dev/checks/events_lib.py", encoding="utf-8").read())
# They use the suite's own globals (g, story, fails, check...). Change one here and every suite gets it.

def meet(st, text, picks=(), n=3000):
    """Walk into whoever is called text on this map (from an open tile beside them) and play out what follows."""
    said.clear()
    if isinstance(st, _WTS):
        spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
        if spot is None:   # (in one of the town's rooms: go in)
            for room in (st.town_map.get("rooms") or {}):
                st._go(room, ""); frames(2)
                spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
                if spot is not None:
                    break
        if spot is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (spot[0] + dx, spot[1] + dy)
            if st._open(b) and b not in st.exits:
                st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
                st.step(-dx, -dy)
                break
        else:
            return None
    else:
        hit = lambda fl: next((m for m in fl.movers if m.kind in ("figure", "trainer") and isinstance(m.payload, dict) and m.payload.get("text") == text), None)
        if hit(st.run.floor) is None:   # (on another floor, or in a room of the route: rooms are floors after the map's own)
            for i in range(st.run.n_floors):
                if hit(st.run.made(i)) is not None:
                    st.run.enter_floor(i); frames(2)
                    break
        f = st.run.floor
        f.movers = [m for m in f.movers if m.kind != "wild"]
        m = hit(f)
        if m is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (m.x + dx, m.y + dy)
            if f.walkable(*b) and f.mover_at(*b) is None and b not in f.exits:
                st.run.player = b; st.anim = 0
                st.step(-dx, -dy)
                break
        else:
            return None
    play(picks, n)
    return list(said)


def play(picks=(), n=3000, until=None):
    """Run the game as a player: tap through what's said, answer each pick list with the next of picks (by value, or
    True for the first), fight battles with the right answers. Stops when nothing is left to do (or until() is true)."""
    picks = list(picks)
    quiet = 0
    for _ in range(n):
        if until and until():
            return True
        st = g.current_state
        name = type(st).__name__
        if name == "PickListState":
            v = picks.pop(0) if picks else None
            if v is None:
                st.done(None) if hasattr(st, "done") else None
            elif v is True:   # (the first choice on the list)
                c0 = (getattr(st, "choices", None) or [None])[0]
                st.pick(c0[1] if isinstance(c0, (tuple, list)) else c0)
            else:
                st.pick(v) if hasattr(st, "pick") else st.done(v)
            quiet = 0
        elif hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st)
            quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
            quiet = 0
        else:
            quiet += 1
            if quiet > 40 and until is None:
                return True
        st.update(); st.draw()
    return until() if until else True


def _fight(b, n=8000):
    for _k in range(n):
        if g.current_state is not b:
            return
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def route(area, came, floor=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = 0, 0
    story.current_area_key, story.last_area_key = area, came
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3); play()
    p = g.current_state
    if floor:
        p.run.enter_floor(floor); frames(2)
    return p
