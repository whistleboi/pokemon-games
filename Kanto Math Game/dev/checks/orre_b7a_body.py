# Orre batch 7a played (11-21, kanto_handoff/orre_check/BATCH_7A.md): the Orre Colosseum's tournament (XD's challengers, Justy
# the final), XD's Cipher Key Lair - Zook and Snagem's Biden at the door, the maze, the Box Rooms' crates pushed (to the stairs
# and onto the moon door's switch, then the reset panel), the System Lever and the voltage panel, Smarton, Gorigan, Greevil's
# screen, the Journal. bash dev/checks/run_par.sh orre_b7a
import json as _json
from src.states.overworld import CityState as _CS, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import catching
from src.world import shadow

fails = []
g.dungeon_routes = True
g.walk_towns = True
said = []


def check(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def _fight(b, n=8000):
    """Win with right answers; snag each Shadow Pokemon as soon as it's out (the ball always holds)."""
    tried = set()
    for _k in range(n):
        if g.current_state is not b:
            return
        foe = b._snag_target() if hasattr(b, "_snag_target") else None
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible and foe is not None and id(foe) not in tried \
                and story.inventory.get("POKE_BALL", 0) > 0:
            tried.add(id(foe))
            story.selected_ball = "POKE_BALL"
            real = catching.throw
            catching.throw = lambda *a, **k: (True, 3, False)
            b.throw_from_bag()
            catching.throw = real
        elif b.phase == "TARGET_SELECT" and getattr(b, "_target_buttons", None):
            b._target_buttons[0].callback()
        elif b.phase in ("MENU", "BATTLE") and not b.dialogue_box.visible and b.math_ui and b.math_ui.visible:
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            names = [m.text.replace(" ", "-") for m in b.move_buttons if m.text]
            odd = ("FUTURE-SIGHT", "DOOM-DESIRE", "LAST-RESORT", "SOLAR-BEAM", "HYPER-BEAM", "GIGA-IMPACT", "FOCUS-PUNCH", "SKY-ATTACK",
                   "DREAM-EATER", "SNORE", "BELCH", "FLING", "NATURAL-GIFT", "SYNCHRONOISE", "EXPLOSION", "SELF-DESTRUCT")
            best = max(names, key=lambda n: 0 if n in odd else ((_MV.get(n) or {}).get("power") or 0))   # (its strongest plain attack)
            b.choose_move(best)
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def play(n=3000):
    quiet = 0
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "on_select", None):   # (one fainted: send in the next able)
            nxt = next((i for i, p in enumerate(story.player_team) if p and p.current_hp > 0 and p is not getattr(getattr(st, "previous_state", None), "player_pokemon", None)), 0)
            st.on_select(nxt)
            continue
        if type(st).__name__ == "EvolutionState":   # (a snagged one grew up after the battle: not now)
            st.evolve_no(); quiet = 0
            continue
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st); quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance(); quiet = 0
        elif getattr(getattr(st, "scenes", None), "playing", None):
            quiet = 0
        else:
            quiet += 1
            if quiet > 40:
                return
        st.update(); st.draw()


def town(area, came):
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    t = _CS(g); g.change_state(t); frames(2); play()
    return g.current_state


def route(area, came, floor=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = 0, 0
    story.current_area_key, story.last_area_key = area, came
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3); play()
    p = g.current_state
    if floor:
        p.run.made(floor); p.run.enter_floor(floor); frames(2)
    return p


def meet(st, text):
    """Walk into whoever is called text (town, its rooms, or a route/dungeon's floors) and play out what follows."""
    said.clear()
    for p in story.player_team:   # (healed between encounters, PP too, as at a Center: the flow is under test)
        if p:
            p.heal_full()
            p.pp = {}
    st = g.current_state
    if isinstance(st, _WTS):
        spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
        if spot is None:
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
        def _who(m):   # (a figure's payload is its option; a trainer's is (index, its data))
            pl = m.payload
            if isinstance(pl, tuple) and len(pl) > 1 and isinstance(pl[1], dict):
                return pl[1].get("name")
            return pl.get("text") if isinstance(pl, dict) else None
        hit = lambda fl: next((m for m in fl.movers if m.kind in ("figure", "trainer") and _who(m) == text), None)
        if hit(st.run.floor) is None:
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
    play()
    return list(said)


def step_into_zone(t, tile):
    """Stand next to tile and step onto it (a zone scene starts as you arrive)."""
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        b = (tile[0] + dx, tile[1] + dy)
        if t._open(b) and b not in t.exits:
            t.player = t.anim_from = b; t.anim = 0; t.walk_goal = None
            t.step(-dx, -dy)
            break
    play()


def mine():
    return {p.id for p in list(story.player_team) + list(story.pc_pokemon or []) if p}


_MV = _json.load(open("assets/moves.json", encoding="utf-8"))

story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "has_under_badge", "has_phenac_badge", "beat_gonzap",
                                        "xd_hordel", "xd_pregym_freed", "orre_snattle_phenac")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER", "PHENAC"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
SP = g.loader.area_data["STORY_PROGRESSION"]
KL = "XD_CIPHER_KEY_LAIR"

print("1) The Orre Colosseum: XD's own challengers, Justy the final")
gym = SP["ORRE_COLOSSEUM"]["gym"]
check([t["name"] for t in gym["trainers"]] == ["Hunter Greel", "Rider Herlam", "Navigator Lestor"]
      and all(t["levels"] == [60] * 6 and t.get("double") for t in gym["trainers"]),
      "Greel, Herlam and Lestor, six Pokemon each at Lv 60, double battles, as XD's disc has them")
ld = gym["leader"]
check(ld["name"] == "Pre Gym Leader Justy" and max(ld["levels"]) == 62 and ld["sprite"] == "orre_justy.png" and ld.get("badge_reward") == "ORRE",
      f"Justy the final, raised (ace {max(ld['levels'])}), his own picture, the Orre Badge")
check(gym["requirements"].get("flag") == "beat_gonzap", "open once Gonzap's beaten")
t = town("ORRE_COLOSSEUM", "ORRE_DESERT")
check(isinstance(t, _WTS), "the Orre Colosseum's town loads")

print("2) The Key Lair's door: Zook, then Snagem's Biden")
gate = next(o for o in SP["GATEON_PORT"]["travel_options"] if o.get("target_area") == KL)
check(gate.get("condition") == "has_orre_badge", "Gateon's way to the Key Lair: after the Orre Badge")
story.badges["ORRE"].append("ORRE")
F["has_orre_badge"] = True
p = route(KL, "GATEON_PORT")
bars0 = p.run.recipe["art"]["floors"][0]["barred"]
door = next(b for b in bars0 if "guards" in " ".join(b["lines"]))
check(not p._until_met(door["until"]), "the guards block the door at first")
meet(p, "THUG ZOOK")
check(F.get("xd_zook_lair") and F.get("snagged_shadow_zangoose"), "Zook beaten, his Shadow Zangoose snagged")
meet(g.current_state, "TEAM SNAGEM BIDEN")
p = g.current_state
check(F.get("xd_lair_guards") and p._until_met(door["until"]), "Biden's battle; Snagem takes out the guards, the door's open")

print("3) The maze")
maze = ["Cipher Peon Grezle", "Cipher Peon Humah", "Cipher Peon Ibsol", "Cipher Peon Kollo", "Cipher Peon Gorog", "Cipher Peon Jelstin", "Cipher Peon Lok"]
pool = [t_["name"] for t_ in SP[KL]["trainer_pool"]]
check(pool[:7] == maze and len(pool) == 15, f"the lair's fifteen peons and R&D men ({len(pool)})")
for who in maze:
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("paras", "growlithe", "shellder", "beedrill", "pidgeotto")),
      "Shadow Paras, Growlithe, Shellder, Beedrill, Pidgeotto snagged")
for it in ("HYPER POTIONS", "REVIVES", "ULTRA BALLS", "RARE CANDY", "TM THUNDERBOLT", "PP UP"):
    meet(g.current_state, it)
check(story.inventory.get("TM126") and story.inventory.get("PP_UP") and story.inventory.get("RARE_CANDY"), "the maze's boxes (TM126 Thunderbolt among them)")


def solve_crates(st, goal_test, limit=200000):
    """Pushes [(crate, (dx, dy))] that reach goal_test(reachable, crates) on this floor, by the engine's own tiles."""
    from collections import deque
    f = st.run.floor
    art = st._here_art()
    links = {tuple(int(v) for v in k.split(",")) for k in (art.get("links") or {})}
    start = frozenset(st._box_spots())

    def solid(t):
        if not (0 <= t[0] < f.w and 0 <= t[1] < f.h):
            return True
        d = str(f.decor.get(t, ""))
        if d.startswith("box:"):
            return False
        return f.tile(*t) != core.FLOOR or f.mover_at(*t) is not None or t in f.decor
    D = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def reach(p, bx):
        seen = {p}
        todo = [p]
        while todo:
            c = todo.pop()
            for dx, dy in D:
                n = (c[0] + dx, c[1] + dy)
                if n not in seen and n not in bx and (n in links or not solid(n)):
                    seen.add(n)
                    if n not in links:
                        todo.append(n)
        return seen
    q = deque([(tuple(st.run.player), start, [])])
    seen = set()
    while q and len(seen) < limit:
        p, bx, path = q.popleft()
        r = reach(p, bx)
        k = (min(r), bx)
        if k in seen:
            continue
        seen.add(k)
        if goal_test(r, bx):
            return path
        for b in bx:
            for d in D:
                if (b[0] - d[0], b[1] - d[1]) in r:
                    b2 = (b[0] + d[0], b[1] + d[1])
                    if not solid(b2) and b2 not in bx and b2 not in links and b2 not in f.exits:
                        q.append((b, frozenset((bx - {b}) | {b2}), path + [(b, d)]))
    return None


def push_all(st, path):
    ok = True
    for b, (dx, dy) in path:
        st.run.player = (b[0] - dx, b[1] - dy)
        st.anim = 0
        st.walk_goal = None
        st.step(dx, dy)
        frames(2)
        play()
        ok = ok and tuple(st.run.player) == tuple(b) and (b[0] + dx, b[1] + dy) in st._box_spots()
    return ok


print("4) The Box Rooms: crates to push, the moon door, the System Lever")
p = g.current_state
p.run.made(2)
p.run.enter_floor(2)
frames(3)
f = p.run.floor
art = p._here_art()
check(len(art.get("boxes") or []) == 4 and len(art.get("box_switches") or []) == 1, "four crates and one floor switch on the Box Rooms")
up = [tuple(int(v) for v in k.split(",")) for k, to in art["links"].items() if to[0] == 3][0]
down = [tuple(int(v) for v in k.split(",")) for k, to in art["links"].items() if to[0] == 1][0]
p.run.player = next((down[0] + dx, down[1] + dy) for dx, dy in ((0, -1), (1, 0), (-1, 0), (0, 1)) if f.walkable(down[0] + dx, down[1] + dy))
frames(1)
start = list(p._box_spots())
check(all(str(f.decor.get(t, "")).startswith("box:") for t in start), "the crates stand where the map puts them")
walled = solve_crates(p, lambda r, bx: up in r, limit=1)
check(walled is None, "the stairs up can't be reached without pushing a crate")
path = solve_crates(p, lambda r, bx: up in r)
check(path is not None and len(path) >= 3, f"pushing crates opens the way to the stairs ({len(path or [])} pushes)")
check(push_all(p, path or []), "each push slides its crate one tile on, and you step after it")
check(solve_crates(p, lambda r, bx: up in r, limit=1) == [], "the stairs up can be walked to now")
saved = F.get(f"boxes_{KL}_2")
check(isinstance(saved, list) and len(saved) == 4, "where the crates stand is kept")
sw = tuple(art["box_switches"][0]["on"])
moon = next(b for b in art["barred"] if "moon" in " ".join(b["lines"]))
check(not p._until_met(moon["until"]), "the moon door is shut")
path2 = solve_crates(p, lambda r, bx: sw in bx)
check(path2 is not None and push_all(p, path2), f"a crate pushed onto the floor switch ({len(path2 or [])} pushes)")
check(F.get("xd_lair_moon_door") and p._until_met(moon["until"]), "the switch is down: the moon door opens for good")
before = sorted(p._box_spots())
blocked = None
for b in p._box_spots():   # (a crate shoved against a wall stays put)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        to = (b[0] + dx, b[1] + dy)
        stand = (b[0] - dx, b[1] - dy)
        if f.tile(*to) == core.WALL and to not in f.decor and f.walkable(*stand) and f.mover_at(*stand) is None and stand not in p._box_spots():
            blocked = (b, (dx, dy), stand)
            break
    if blocked:
        break
if blocked:
    b, (dx, dy), stand = blocked
    p.run.player = stand
    p.step(dx, dy)
    frames(2)
    play()
    check(sorted(p._box_spots()) == before and tuple(p.run.player) == stand, "a crate against a wall won't move, and you stay put")
said.clear()
meet(g.current_state, "CRATE RESET PANEL")
frames(3)
p = g.current_state
check(F.get(f"boxes_{KL}_2") is None and sorted(p._box_spots()) == sorted(start)
      and all(str(p.run.floor.decor.get(t, "")).startswith("box:") for t in start),
      "the reset panel puts the crates back where they started")
check(F.get("xd_lair_moon_door"), "the moon door stays open after a reset")
p.run.player = next((up[0] + dx, up[1] + dy) for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)) if p.run.floor.walkable(up[0] + dx, up[1] + dy))
frames(1)
check(solve_crates(p, lambda r, bx: down in r, limit=1) is None, "from the stairs-up side, crates at the start shut the way down")
meet(g.current_state, "CRATE PANEL")
frames(3)
p = g.current_state
p.run.player = next((up[0] + dx, up[1] + dy) for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)) if p.run.floor.walkable(up[0] + dx, up[1] + dy))
frames(1)
check(solve_crates(p, lambda r, bx: down in r, limit=1) == [], "the crate panel by the stairs lays the crates out clear: the way down is open")
for who in ("Cipher Peon Kleto", "Cipher Peon Flipis", "Cipher Peon Targ", "Cipher R&D Hospel", "Cipher Peon Snidle"):
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("tangela", "butterfree", "magneton")), "the Box Rooms' peons: Shadow Tangela, Butterfree, Magneton")
for it in ("FULL RESTORE", "ELIXIR", "FULL HEALS", "HP UP", "MAX REVIVE", "SYSTEM LEVER"):
    meet(g.current_state, it)
check(story.inventory.get("MAX_REVIVE") and story.inventory.get("SYSTEM_LEVER") and story.inventory.get("HP_UP"),
      "the Box Rooms' items, the Max Revive behind the moon door, the System Lever")

print("5) The Control Room: the voltage, Smarton")
for who in ("Cipher Peon Fudler", "Cipher Peon Angic", "Cipher R&D Acrod"):
    meet(g.current_state, who)
check(F.get("snagged_shadow_venomoth") and F.get("snagged_shadow_weepinbell"), "Angic's Shadow Venomoth and Weepinbell")
p = g.current_state
p.run.made(3)
p.run.enter_floor(3)
frames(2)
ubar = p._here_art()["barred"][0]
check(not p._until_met(ubar["until"]), "the stairs to Gorigan are shut")
said.clear()
meet(g.current_state, "CONTROL PANEL")
check(F.get("xd_lair_voltage") and not story.inventory.get("SYSTEM_LEVER") and any("shakes" in ln for ln in said),
      "the System Lever in the panel: the voltage up, the building shakes")
meet(g.current_state, "CIPHER PEON SMARTON")
p = g.current_state
check(F.get("xd_smarton_lair") and F.get("snagged_shadow_arbok"), "Smarton bursts out of his door: beaten, his Shadow Arbok snagged")
check(p._until_met(ubar["until"]), "the stairs up open")

print("6) Gorigan's hall")
said.clear()
meet(g.current_state, "BATTLE CIPHER ADMIN GORIGAN")
check(F.get("xd_gorigan_beaten") and F.get("snagged_shadow_primeape") and F.get("snagged_shadow_hypno"),
      "Gorigan beaten (ace 61): Shadow Primeape and Hypno snagged")
said.clear()
meet(g.current_state, "GREEVIL'S SCREEN")
check(F.get("xd_greevil_screen") and any("Citadark" in ln for ln in said), "Greevil on the screen: Citadark Isle and XD001")
meet(g.current_state, "GORIGAN'S DESK")
check(F.get("xd_shadow_list"), "Cipher's Shadow list from Gorigan's desk")
p = route(KL, "GATEON_PORT")
back = next(b for b in p.run.recipe["art"]["floors"][0]["barred"] if "inside" in " ".join(b["lines"]))
check(p._until_met(back["until"]), "the yard's back door from Gorigan's hall opens once he's beaten")
gate = next(o for o in SP["PHENAC_CITY"]["travel_options"] if o.get("target_area") == "REALGAM_TOWER")
check("xd_gorigan_beaten" in str(gate.get("condition")), "Realgam Tower on the map after Gorigan")

print("7) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m16") < jm.index("orre_m17") < jm.index("orre_m17b") < jm.index("orre_m17c") < jm.index("orre_m18"),
      "the Orre Colosseum, the Key Lair's door, the System Lever, Gorigan, then Realgam")


# ---- R2 (11-23): the tournaments on their walked arenas (src/world/orre_tournament.py; orre_story.py _tournament) ----
from src.pokemon.data import Pokemon as _TP
from src.world import levels as _tlv, orre_tournament as _ot


def _team(lv, ids=(248, 6, 9)):
    out = []
    for pid in ids:
        p = _TP(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)
        _tlv.set_team([p], [lv], exact=True)
        p.heal_full()
        out.append(p)
    story.player_team = out


def _drive(n=10, mg=None):
    """Play on; a minigame is won or lost as mg says (a list, first to last; then won)."""
    for _ in range(n):
        play(4000)
        st = g.current_state
        if hasattr(st, "on_done") and not hasattr(st, "math_ui"):
            st.on_done(mg.pop(0) if mg else True)


def _lobby(area):
    lob, desk, arena = _TOURS[area][:3]
    t = town(area, "OUTSKIRT_STAND")
    if lob:
        door = next(tuple(int(v) for v in k.split(",")) for k, r in (story_map_of(area).get("inside") or {}).items() if r == lob)
        t._go(lob, "OUT:%d,%d" % door)
    else:
        pass
    frames(2)
    return g.current_state


def story_map_of(area):
    return _json.load(open("assets/town_maps.json", encoding="utf-8"))[area]


_TOURS = {"PYRITE_TOWN": ("gym", (7, 5), "arena"), "UNDER_COLOSSEUM": (None, (10, 4), "gym"),
          "PHENAC_CITY": ("gym", (7, 5), "arena"), "ORRE_COLOSSEUM": ("gym", (7, 5), "arena")}

print("R2) Every tournament walked: the desk takes you in, round 1 walks in; a loss heals you and starts it over")
_keep = (list(story.player_team), dict(F), {k_: list(v_) for k_, v_ in story.badges.items()})
for area in ("PYRITE_TOWN", "UNDER_COLOSSEUM", "PHENAC_CITY", "ORRE_COLOSSEUM"):
    gym = SP[area]["gym"]
    F.update({gym["requirements"]["flag"]: True})
    story.badges["ORRE"] = ["PYRITE", "UNDER", "PHENAC", "ORRE"][:int(gym["requirements"].get("badges", 0))]
    for k_ in [k_ for k_ in F if k_.startswith((f"gym_progress_{area}", "orre_tourney"))]:
        F.pop(k_, None)
    w = _TP(g.loader.fetch_specific(129), g.assets, size_mult=2.5)
    _tlv.set_team([w], [2], exact=True); w.heal_full(); w.moves = ["SPLASH"]
    story.player_team = [w]
    t = _lobby(area)
    said.clear()
    meet(t, "Receptionist")
    _drive(3)
    st = g.current_state
    lob = _TOURS[area][0]
    check(any("Round 1!" in s_ for s_ in said) and any("Bad luck!" in s_ for s_ in said),
          f"{area}: signed up, round 1 walked in; lost, the receptionist sends you back ({[s_ for s_ in said if 'Round' in s_ or 'Bad luck' in s_][:2]})")
    check(not F.get(f"orre_tourney_{area}") and F.get(f"gym_progress_{area}", 0) == 0 and story.player_team[0].current_hp > 0,
          f"{area}: healed, and the tournament starts over")
    if lob:
        check(getattr(st, "room", None) == lob, f"{area}: back in the lobby ({getattr(st, 'room', None)})")
story.player_team, _f, story.badges = _keep[0], _keep[1], _keep[2]
F.clear(); F.update(_f)
_tm = story_map_of("ORRE_COLOSSEUM")
check(_tm["rooms"]["gym"]["roofs"]["_picture"]["f"].endswith("103_sand.png") and story_map_of("PHENAC_CITY")["rooms"]["gym"]["roofs"]["_picture"]["f"].endswith("103_blue.png"),
      "the Orre Colosseum's lobby in sand, Phenac Stadium's in blue (Jordan's OK)")
_rg = story_map_of("REALGAM_TOWER")["rooms"]["colosseum"]
_ppl = [p_ for p_ in _rg["people"] if isinstance(p_, dict)]
check(any(p_.get("text") == "Realgam Colosseum desk" and "xd_colosseum" in p_["event"] for p_ in _ppl)
      and any((p_.get("event") or {}).get("referee") and (p_.get("event") or {}).get("signup") for p_ in _ppl),
      "Realgam's tower top: XD's Realgam Colosseum desk (its own flag) and the host who starts Evice's run")
_rr = _rg["people"]
_xd = next(p_ for p_ in _ppl if p_.get("text") == "Realgam Colosseum desk")["event"]["xd_colosseum"]
check(len(_xd["rounds"]) == 4 and all(len(r_) == 4 for r_ in _xd["rounds"]) and max(max(b_["levels"]) for r_ in _xd["rounds"] for b_ in r_) == 40,
      "XD's Realgam Colosseum: four rounds of four, Lv 40 as the disc")
import os as _os
check(_os.path.isfile("assets/battle_bg/ORRE/index.json") and _os.path.isfile("assets/battle_bg/ORRE/pyritecol.png"),
      "Orre's battle backgrounds from its source game (assets/battle_bg/ORRE)")
from src.world import battle_bg as _bb
story.current_area_key = "PYRITE_TOWN"
check(str(_bb.pick(g, "PYRITE_TOWN", trainer=True, gym=True) or "").endswith("pyritecol.png")
      and str(_bb.pick(g, "OUTSKIRT_STAND", trainer=True) or "").replace("_eve", "").replace("_night", "").endswith("sand.png"),
      "a tournament battle in Pyrite: the Colosseum's own background; out in the desert: the sand")

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
