
# Orre batch 2 played (11-20, kanto_handoff/orre_check/BATCH_2.md): Pyrite Cave and Miror B., Plusle back to Duking,
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
        p.run.enter_floor(floor); frames(2)
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
                                        "orre_power_on", "has_pyrite_badge", "orre_beat_nore", "orre_plusle_taken", "orre_beat_doken")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 60}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
_known = _MV

print("1) The disc's trainers in our data")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _known})
check(not bad, f"every move one the game knows ({bad})")
pc = [t["name"] for t in g.loader.area_data["STORY_PROGRESSION"]["PYRITE_CAVE"]["trainer_pool"]]
check(len(pc) == 13 and "Rider Sosh" in pc and "Hunter Zalo" in pc and "Cipher Peon Sema" in pc, f"Pyrite Cave's 13 ({pc})")
rc = [t["name"] for t in g.loader.area_data["STORY_PROGRESSION"]["RELIC_CAVE"]["trainer_pool"]]
check(rc == ["Cipher Peon Doven", "Cipher Peon Silton", "Cipher Peon Kass"], f"the Relic Cave's three peons ({rc})")

print("2) Pyrite Cave: its trainers' Shadows, Miror B., the items")
p = route("PYRITE_CAVE", "PYRITE_TOWN")
for who in ("Rider Twan", "Rider Sosh", "Hunter Zalo"):
    route("PYRITE_CAVE", "PYRITE_TOWN")
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("meditite", "dunsparce", "swablu")), "Shadow Meditite, Dunsparce and Swablu snagged")
route("PYRITE_CAVE", "PYRITE_TOWN")
said_s = meet(g.current_state, "Snatch box") or []
check(not F.get("orre_miror_tm_snatch") and any("locked" in ln for ln in said_s), "Miror B.'s box stays shut while he's there")
route("PYRITE_CAVE", "PYRITE_TOWN")
meet(g.current_state, "PYRITE CAVE: MIROR B.")
check(F.get("orre_miror_cave") and F.get("snagged_shadow_sudowoodo"), "Miror B. beaten, his Shadow Sudowoodo snagged")
for it, inv, n in (("Snatch box", "TM299", 1), ("Macho Brace", "MACHO_BRACE", 1), ("Ein File P", "EIN_FILE_P", 1),
                   ("Hyper Potions", "HYPER_POTION", 2), ("Ethers", "ETHER", 3), ("Ultra Balls", "ULTRA_BALL", 3),
                   ("Full Heal", "FULL_HEAL", 1), ("Max Potion", "MAX_POTION", 1), ("Carbos", "CARBOS", 1), ("Zinc", "ZINC", 1),
                   ("Protein", "PROTEIN", 1), ("Iron", "IRON", 1)):
    before = story.inventory.get(inv, 0)
    route("PYRITE_CAVE", "PYRITE_TOWN")
    meet(g.current_state, it)
    check(story.inventory.get(inv, 0) == before + n, f"{it} picked up")

route("PYRITE_CAVE", "PYRITE_TOWN")
meet(g.current_state, "Cipher Peon Mirakle B.")
check(F.get("orre_mirakle_b"), "Mirakle B., Miror B.'s would-be successor, waits in his room afterwards")


def _here(area, came, names):
    p = route(area, came)
    found = set()
    for i in range(p.run.n_floors):
        for m in p.run.made(i).movers:
            pl = m.payload
            n = pl[1].get("name") if isinstance(pl, tuple) and len(pl) > 1 and isinstance(pl[1], dict) else (pl.get("text") if isinstance(pl, dict) else None)
            if n in names:
                found.add(n)
    return found


F["orre_part2"] = True   # (story rework 11-24: Evice beaten ends Part 1; Reath and Ferma come back in Part 2)
F.pop("orre_mirakle_b", None)
seen = _here("PYRITE_CAVE", "PYRITE_TOWN", {"Cipher Peon Mirakle B.", "Miror B. Peon Reath", "Miror B. Peon Ferma"})
check(seen == {"Miror B. Peon Reath", "Miror B. Peon Ferma"}, f"after Evice: Reath and Ferma in his place, not Mirakle B. ({sorted(seen)})")
for who, flag in (("Miror B. Peon Reath", "orre_cave_reath"), ("Miror B. Peon Ferma", "orre_cave_ferma")):
    route("PYRITE_CAVE", "PYRITE_TOWN")
    meet(g.current_state, who)
    check(F.get(flag), f"{who}'s rematch")
F.pop("orre_part2", None)

print("3) Back in Pyrite: Plusle, Fateen, the ride north")
t = town("PYRITE_TOWN", "PYRITE_CAVE")
meet(t, "Duking")
check(F.get("orre_duking_plusle") and 311 in mine(), "Duking gives you Plusle (his own gift, kept)")
t = town("PYRITE_TOWN", "PYRITE_CAVE")
step_into_zone(t, (30, 85))
check(F.get("orre_fateen"), "Fateen sees trouble in the north as you go to leave")
cond = next(o for o in g.loader.area_data["STORY_PROGRESSION"]["PYRITE_TOWN"]["travel_options"] if o["target_area"] == "AGATE_VILLAGE")["condition"]
check(t._check_menu_condition(cond), "the bike rides on to Agate")

print("4) Agate: Eagun, the Relic Cave, Skrub, the Relic Stone")
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
check((36, 27) in t.barred, "a man keeps you out of the Relic Cave")
ac = g.loader.area_data["STORY_PROGRESSION"]["AGATE_VILLAGE"]
rel = next(o for o in ac["travel_options"] if o["target_area"] == "RELIC_CAVE")["condition"]
check(not t._check_menu_condition(rel), "...and its way in is shut")
meet(t, "Village Elder")
check(F.get("met_agate_elder"), "Eagun and Beluh; Cipher pushed into the cave")
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
check((36, 27) not in t.barred and t._check_menu_condition(rel), "the cave is open now")
pur = next(o for o in ac["explore_options"] if o["text"] == "Purify at the Relic Stone")["condition"]
check(not t._check_menu_condition(pur), "no purifying before Skrub")
for who in ("Cipher Peon Doven", "Cipher Peon Skrub"):
    route("RELIC_CAVE", "AGATE_VILLAGE")
    meet(g.current_state, who)
check(F.get("orre_beat_skrub") and F.get("snagged_shadow_hitmontop"), "Skrub beaten, his Shadow Hitmontop snagged")
for it, inv, n in (("Silk Scarf", "SILK_SCARF", 1), ("Ultra Balls", "ULTRA_BALL", 2)):
    before = story.inventory.get(inv, 0)
    route("RELIC_CAVE", "AGATE_VILLAGE")
    meet(g.current_state, it)
    check(story.inventory.get(inv, 0) == before + n, f"{it} picked up")
t = town("AGATE_VILLAGE", "RELIC_CAVE")
check(t._check_menu_condition(pur), "the Relic Stone purifies now")
meet(t, "Beluh")
check(F.get("orre_beluh_tablet"), "Beluh: the Relic Stone, and the e-mail about Mt. Battle")
mtb = next(o for o in ac["travel_options"] if o["target_area"] == "MT_BATTLE")["condition"]
check(t._check_menu_condition(mtb), "Mt. Battle opens")
for who, flag in (("Fun Old Man Skof", "orre_agate_skof"), ("Cooltrainer Dury", "orre_agate_dury")):
    t = town("AGATE_VILLAGE", "RELIC_CAVE")
    meet(t, who)
    check(F.get(flag), f"{who} beaten")
for it, inv in (("Quick Claw", "QUICK_CLAW"), ("Ein File C", "EIN_FILE_C")):
    t = town("AGATE_VILLAGE", "RELIC_CAVE")
    meet(t, it)
    check(story.inventory.get(inv), f"{it} picked up")

print("5) An older save already past Agate")
story.story_flags = {"got_snag_machine": True, "has_pyrite_badge": True, "orre_miror_cave": True, "met_agate_elder": True,
                     "orre_dakim_mt_battle": True}
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
check(t._check_menu_condition(pur) and t._check_menu_condition(mtb) and t._check_menu_condition(rel), "purifying, Mt. Battle and the cave all open")

print("##### orre_b2:", len(fails), "failures")
for f in fails:
    print("  -", f)
