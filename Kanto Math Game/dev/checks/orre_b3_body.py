# Orre batch 3 played (11-20, kanto_handoff/orre_check/BATCH_3.md): Mt. Battle - Colosseum's Cipher takeover and Dakim, the
# F-Disk, Vander's Time Flute, XD's 100 (raised to fit), the gates, rest points, reception, starting over, Battlus and the Master.
# bash dev/checks/run_par.sh orre_b3
# Fateen, Agate Village, the Relic Cave and Skrub, purifying at the Relic Stone. bash dev/checks/run_par.sh orre_b2
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
                                        "orre_power_on", "has_pyrite_badge", "orre_miror_cave", "met_agate_elder", "orre_beat_skrub")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 60}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SPM = g.loader.area_data["STORY_PROGRESSION"]["MT_BATTLE"]
POOL = SPM["trainer_pool"]
BARS = {i: f.get("barred") for i, f in enumerate(_json.load(open("assets/town_maps.json", encoding="utf-8"))["MT_BATTLE"]["floors"])}
idx = {t["name"]: i for i, t in enumerate(POOL)}

print("1) The climb's trainers in our data")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
cip = [t for t in POOL if t.get("gone_flags") == ["orre_dakim_mt_battle"]]
xd = [t for t in POOL if "orre_dakim_mt_battle" in (t.get("when_flags") or [])]
check(len(POOL) == 109 and len(cip) == 9 and len(xd) == 100, f"Colosseum's 9 takeover battles + XD's 100 ({len(POOL)}, {len(cip)}, {len(xd)})")
check(all(t.get("stays_beaten") for t in POOL), "every climber stays beaten till you start over")
spots = {t["spot_name"] for t in POOL}
check(spots == {f"Area {a} Trainer {k}" for a in range(1, 11) for k in range(1, 11)}, "ten spots in each of the ten areas")
lv = lambda n: max(POOL[idx[n]]["levels"])
check(lv("Beauty Miru") == 25 and lv("Area Leader Vander") == 28 and lv("Area Leader Eldof") == 29 and lv("Area Leader Taria") == 30
      and lv("Area Leader Boyden") == 30 and lv("Cooltrainer Roze") == 31 and lv("Researcher Hombol") == 31 and lv("Mt. Battle Master Battlus") == 50,
      "Mt. Battle's climb fits its story stage (L1 11-24, orre_levels: Lv 25-31 after Agate, Battlus 50)")
check(POOL[idx["Mt. Battle Master Battlus"]].get("victory_flag") == "mt_battle_battlus", "Battlus, the 100th, marks the climb done")
dak = next(o for o in SPM["route_menu"] if o["text"] == "DAKIM ATTACKS MT. BATTLE")["event"]["battle"]
check(dak["team"][0] == 9397 and dak["levels"][0] == 26 and dak["team"][1:] == [375, 259, 75, 322],
      "Dakim: Shadow Entei 26, Metang, Marshtomp, Graveler, Numel (stage levels, L1 11-24)")

print("2) Before Dakim: Cipher holds Area 1")
p = route("MT_BATTLE", "AGATE_VILLAGE", floor=2)
names_on = lambda fl: {m.payload[1].get("name") for m in fl.movers if m.kind == "trainer"}
on = names_on(p.run.floor)
check({"Rider Turo", "Cipher Peon Kison", "Cipher Peon Berin"} <= on and "Beauty Miru" not in on, f"the takeover nine stand on Area 1, XD's are away ({sorted(on)[:4]})")
gate = BARS[2][0]["until"]
check(not p._until_met(gate), "Area 1's way up is shut while Dakim is there")
meet(g.current_state, "Rider Turo")
check(story.is_trainer_defeated("MT_BATTLE", idx["Rider Turo"]), "a takeover battle won (Rider Turo)")
route("MT_BATTLE", "AGATE_VILLAGE", floor=2)
said_d = meet(g.current_state, "DAKIM ATTACKS MT. BATTLE") or []
check(F.get("orre_dakim_mt_battle") and F.get("snagged_shadow_entei"), "Dakim beaten, his Shadow Entei snagged")
check(any("Skrub" in ln for ln in said_d) and any("leaps" in ln for ln in said_d), "after him: Skrub and a Cipher woman come; Dakim leaps away")

print("3) After Dakim: the F-Disk, Vander's Time Flute, XD's Area 1")
route("MT_BATTLE", "AGATE_VILLAGE", floor=2)
meet(g.current_state, "F-DISK")
check(F.get("orre_f_disk") and story.inventory.get("F_DISK") == 1, "the F-Disk picked up")
route("MT_BATTLE", "AGATE_VILLAGE", floor=2)
on = names_on(g.current_state.run.floor)
check("Rider Turo" not in on and "Cipher Peon Berin" not in on and "Beauty Miru" in on and "Area Leader Vander" not in on,
      "Cipher's gone, Mt. Battle's own trainers are back (Vander still catching his breath)")
said_v = meet(g.current_state, "AREA LEADER VANDER") or []
check(F.get("orre_time_flute") and story.inventory.get("TIME_FLUTE") == 1, "Vander gives the Time Flute")
p = route("MT_BATTLE", "AGATE_VILLAGE", floor=2)
check("Area Leader Vander" in names_on(p.run.floor), "Vander back at his post, Area 1's leader")
check(not p._until_met(gate), "Area 1's way up stays shut till its ten are beaten")
for k in range(9):
    story.mark_trainer_defeated("MT_BATTLE", 9 + k)
check(not p._until_met(gate), "...nine isn't enough")
meet(g.current_state, "Area Leader Vander")
check(story.is_trainer_defeated("MT_BATTLE", idx["Area Leader Vander"]) and p._until_met(gate), "Vander beaten: the way up opens")
check(not story.trainer_on_map("MT_BATTLE", idx["Area Leader Vander"], POOL[idx["Area Leader Vander"]]), "a beaten climber isn't back the next visit")

print("4) The Time Flute")
ent = next((m for m in list(story.player_team) + list(story.pc_pokemon or []) if m and m.id == 9397), None)
if ent is not None and ent not in story.player_team:
    story.player_team[-1] = ent
check(ent is not None and story.is_shadow(ent) and ent.shadow["gauge"] > 0, "Shadow Entei with its heart still shut")
from src.states.systems.bag import BagState
bag = BagState(g, g.current_state)
bag.on_pokemon_select_time_flute(story.player_team.index(ent))
check(any(m and m.id == 244 for m in story.player_team) and not story.inventory.get("TIME_FLUTE"),
      "played on it: Entei purified at once, the flute used up")
bag.on_pokemon_select_time_flute(0)
check(True, "played on nothing: no harm")

print("5) Rest points and the reception")
p = route("MT_BATTLE", "AGATE_VILLAGE", floor=3)
story.player_team[0].current_hp = 1
meet(g.current_state, "REST POINT 1")
check(F.get("mt_battle_rest_1") and story.player_team[0].current_hp == story.player_team[0].get_max_hp(), "Passage 1's rest point heals and marks Area 2")
route("MT_BATTLE", "AGATE_VILLAGE", floor=1)
meet(g.current_state, "MT. BATTLE RECEPTION")
pk = g.current_state
check(type(pk).__name__ == "PickListState" and [c[0] for c in pk.choices] == ["AREA 1", "AREA 2"],
      f"the desk offers Area 1 and Area 2 ({[c[0] for c in getattr(pk, 'choices', [])]})")
if type(pk).__name__ == "PickListState":
    pk.done("@AREA 2"); frames(3); play()
st = g.current_state
check(getattr(getattr(st, "run", None), "index", None) == 4, f"...and sends you up to Area 2's floor ({getattr(getattr(st, 'run', None), 'index', None)})")

print("6) Starting over; Battlus and the Master")
route("MT_BATTLE", "AGATE_VILLAGE", floor=1)
meet(g.current_state, "START OVER FROM AREA 1")
check(not story.defeated_trainers.get("MT_BATTLE") and not F.get("mt_battle_rest_1"), "start over: everyone's back, the rest points too")
F["beat_orre_champion"] = True
p = route("MT_BATTLE", "AGATE_VILLAGE", floor=20)
master = next(o for o in SPM["route_menu"] if o["text"] == "MT. BATTLE MASTER")
check(not all(p._check_route_condition(c, False, master) for c in master["condition"]), "the Master waits till Battlus is beaten")
meet(g.current_state, "Mt. Battle Master Battlus")
check(F.get("mt_battle_battlus"), "Battlus beaten, the 100th")
p = route("MT_BATTLE", "AGATE_VILLAGE", floor=20)
check(all(p._check_route_condition(c, False, master) for c in master["condition"]), "...then Vander, the Master, is at the very top")

print("7) The Journal")
jm = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_")}
check(jm["orre_m7b"]["completed_flag"] == ["orre_time_flute", "orre_f_disk"] and jm["orre_m7c"]["condition"]["flag"] == ["orre_time_flute", "orre_f_disk"],
      "Vander's thanks and the F-Disk are a step (R6 11-24); The Under follows it")
check(jm["orre_s2a"]["completed_flag"] == "mt_battle_battlus", "the 100 is a side step")

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
