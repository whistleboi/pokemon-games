# The Orange story gates, both sides (11-17; SWEEP_RULES Part 3 item 12): each gate of
# kanto_handoff/orange_rom_tools/orange_gates.json (read from Orange Islands Beta 5.7's own scripts by orange_gates_make.py)
# that is built on our maps is tried the way a player meets it: BEFORE (the state that must stop you) and AFTER (the state
# that lets you by). Gates in areas not built yet are listed, not tested.
#   bash dev/checks/run.sh orange_gates
import json
from src.states.overworld import CityState, PlayState, AreaTransitionState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states import overworld as ow

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
_tools = os.environ.get("ORANGE_TOOLS") or next((os.path.join(_d, "kanto_handoff", "orange_rom_tools") for _d in
          [os.path.abspath(os.path.join(os.getcwd(), *[".."] * _n)) for _n in range(1, 8)]
          if os.path.isdir(os.path.join(_d, "kanto_handoff", "orange_rom_tools"))), "")   # (the first kanto_handoff above the game folder: main folder or a worktree, 11-23)
G = json.load(open(os.path.join(_tools, "orange_gates.json"), encoding="utf-8"))
TM = json.load(open("assets/town_maps.json", encoding="utf-8"))
AREAS = g.loader.area_data["STORY_PROGRESSION"]
story.enter_region("ORANGE")
BASE = {"received_starter_orange": True}


def setup(state):
    story.story_flags = {k: True for k in state.get("flags", [])}
    for it in ("HM_SURF", "LIFT_KEY", "WHIRLPULLER"):
        story.inventory.pop(it, None)
    for it in state.get("items", []):
        story.inventory[it] = 1
    if "money" in state:   # (a fee: the Moro Museum's ticket stops you only when you can't pay it)
        story.money = state["money"]
    story.badges["ORANGE"] = list(state.get("badges", []))   # (a badge the gate needs: Trovita's Whirlpuller, 11-17)


def town(key, room=None, at=None):
    story.current_area_key, story.last_area_key = key, key
    g.walk_town_pos = (key, tuple(at), (0, 1)) if at else None
    g.walk_town_room = (key, room) if room else None
    st = CityState(g)
    g.change_state(st)
    for _ in range(3):
        st.update(); st.draw()
    return st


def tap(st, n=400):
    for _ in range(n):
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            st.dialogue_box.advance()
        else:
            return
        st.update(); st.draw()


def opt(key, text):
    a = AREAS[key]
    return next(o for o in a.get("explore_options", []) + a.get("route_menu", []) if o.get("text") == text)


print("== 5.7's story steps read from its scripts:", len(G["steps"]), "| stopping triggers:", len(G["stops"]),
      "| item checks:", len(G["item_checks"]), "| gifts:", len(G["gifts"]))
for gate in G["gates"]:
    key = gate["area"]
    if key not in TM:
        print(f"   --  {gate['id']}: {key} not built yet (batch {gate['batch']})")
        continue
    sides = {}
    for side in ("before", "after"):
        setup(gate[side])
        k = gate["kind"]
        if k == "exit":
            st = town(key)
            o = st._travel_option(gate["to"])
            sides[side] = bool(o and st._shown(o))
        elif k == "option":
            o = opt(key, gate["text"])
            if AREAS[key].get("area_type") == "town":
                st = town(key)
                sides[side] = st._check_menu_condition(o.get("condition")) if hasattr(st, "_check_menu_condition") else st._shown(o)
            else:
                story.current_area_key = key
                ps = PlayState(g)
                sides[side] = ps._check_route_condition(o.get("condition"), False)
        elif k == "event_travel":
            st = town(key)
            o = opt(key, gate["text"])
            moved = []
            g.change_state = (lambda real: (lambda s, *a, **kw: (moved.append(s), real(s, *a, **kw))[1]))(type(g).change_state.__get__(g))
            try:
                ow._run_story_event(st, o["event"], st._check_menu_condition, lambda l: None)
            finally:
                del g.change_state
            sides[side] = any(isinstance(s, AreaTransitionState) and getattr(s, "target_area", getattr(s, "area_key", None)) == gate["to"] for s in moved) \
                or any(isinstance(s, AreaTransitionState) for s in moved)
        elif k in ("barred", "barred_item"):   # (the map's own blocker: shut before, open after, as the game tests it)
            m = TM[key]
            part = m["floors"][gate.get("floor", 0)] if m.get("floors") else m
            bar = next(b for b in part.get("barred", []) if gate["tile"] in b.get("tiles", []))
            u = bar.get("until") or {}
            if u.get("flag_condition"):
                sides[side] = bool(story.story_flags.get(u["flag_condition"]))
            elif u.get("item_condition"):
                sides[side] = story.inventory.get(u["item_condition"], 0) > 0
            if side == "before":
                story.inventory.pop(gate.get("item", ""), None)
        elif k == "floor_gate":   # (11-18, batch 27: a switch puzzle's rocks or barrier, on the floor as the game builds it with
            #  these flags: walkable or not. Fire / Lightning Island's secret switches, New Island's lab statues)
            g.arrive_floor = (key, gate["floor"], list(gate["at"]))
            story.current_area_key, story.last_area_key = key, gate["came"]
            g.walk_town_pos = None
            st = PlayState(g); g.states["play"] = st
            g.change_state(st)
            for _ in range(3):
                g.current_state.update(); g.current_state.draw()
            tap(g.current_state)
            cur = g.current_state
            sides[side] = cur.run.index == gate["floor"] and cur.run.floor.walkable(*gate["tile"])
        elif k == "gym_challenge":   # (before: the Gym's lobby offers its challenge, not the Leader; after: the Leader)
            story.badges["ORANGE"] = []
            story.current_area_key = key
            lobby = ow.GymLobbyState(g, None)
            sides[side] = lobby.challenge is None
        elif k == "event_gift":
            st = town(key)
            o = opt(key, gate["text"])
            story.inventory.pop(gate["item"], None)
            _team = list(story.player_team)
            ow._run_story_event(st, o["event"], st._check_menu_condition, lambda l: None)
            sides[side] = story.inventory.get(gate["item"], 0) > 0
            story.player_team[:] = _team
        elif k == "walk":   # (someone stands in the way: from "from", one "step"; before you don't get by, after you do. Murcott's Bug Catchers)
            st = town(key, gate.get("room"), gate["from"])
            tap(st)
            st.player = tuple(gate["from"]); st.anim = 0
            st.step(*gate["step"])
            for _ in range(60):
                st.update(); st.draw()
                tap(st)
            cur = g.current_state
            sides[side] = not (isinstance(cur, _WTS) and tuple(cur.player) == tuple(gate["from"]))
        elif k == "whirl":   # (11-17, batch 15: a flowing whirlpool; from "from", one "step" onto it: before, its current throws
            #  you back out; after (the Whirlpuller), you're carried through to "lands")
            story.current_area_key, story.last_area_key = key, key
            g.walk_town_pos = None
            st = PlayState(g); g.states["play"] = st
            g.change_state(st)
            for _ in range(3):
                g.current_state.update(); g.current_state.draw()
            tap(g.current_state)
            cur = g.current_state
            cur.run.player = tuple(gate["from"]); cur.anim = 0; cur.sliding = None
            cur.step(*gate["step"])
            for _ in range(240):
                cur.update(); cur.draw()
                tap(cur)
                if not getattr(cur, "sliding", None) and not getattr(cur, "anim", 0):
                    break
            sides[side] = tuple(g.current_state.run.player) == tuple(gate["lands"])
        elif k == "room_push":
            st = town(key, gate["room"], gate["from"])
            tap(st)
            st.player = tuple(gate["from"]); st.anim = 0
            st.step(*gate["step"])
            for _ in range(240):
                st.update(); st.draw()
                tap(st)
            cur = g.current_state
            sides[side] = not (isinstance(cur, _WTS) and cur.room == gate["room"] and tuple(cur.player) == tuple(gate["from"]))
    check(sides["before"] is False, f"{gate['id']}: BEFORE ({gate['before']}) it stops you   [5.7: {gate['57'][:80]}]")
    check(sides["after"] is True, f"{gate['id']}: AFTER ({gate['after']}) it lets you by   [ours: {gate['ours']}]")
print(f"##### {len(fails)} failures")
