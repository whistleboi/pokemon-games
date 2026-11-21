
# Orre batch 1 played (11-20, kanto_handoff/orre_check/BATCH_1.md): Pyrite in Colosseum's order - the duel square's
# Shadow Pokemon, Cail, the Gear from the Construction Lot, the windmill, the jail, the Colosseum's gate and teams, the
# bridge, Cipher's hideout to Pyrite Cave. bash dev/checks/run_par.sh orre_b1
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
F = story.story_flags
story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_phenac_folly", "orre_rui_joined",
                                        "orre_met_mayor", "orre_wakin", "orre_got_balls", "orre_raid_told", "orre_raid_mirorb",
                                        "orre_raid_folly", "orre_raid_trudly", "got_snag_machine", "received_starter_orre")}
F = story.story_flags
story.badges = {}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 40}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))

print("1) The disc's trainers, as our data holds them")
_known = _json.load(open("assets/moves.json", encoding="utf-8"))
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _known})
check(not bad, f"every move one the game knows ({bad})")
check(TR["col:57"]["team"][0] == 9352 and TR["col:57"]["levels"] == [30, 27, 27], "Rider Nover: Shadow Noctowl Lv 30, Ledyba and Wingull Lv 27 (the disc)")
gym = g.loader.area_data["STORY_PROGRESSION"]["PYRITE_TOWN"]["gym"]
names = [t["name"] for t in gym["trainers"]] + [gym["leader"]["name"]]
check(names == ["Hunter Hoks", "Chaser Tisler", "Bandana Guy Vilch", "Bodybuilder Mirez"], f"Pyrite Colosseum's four rounds ({names})")
check(all(t.get("double") for t in gym["trainers"] + [gym["leader"]]) and gym["requirements"]["flag"] == "orre_power_on",
      "all doubles, and the Colosseum needs its power back")
bp = [t["name"] for t in g.loader.area_data["STORY_PROGRESSION"]["PYRITE_BUILDING"]["trainer_pool"]]
check(len(bp) == 10 and "Hunter Toti" in bp and "Bodybuilder Elidi" in bp, f"the hideout's ten trainers ({bp})")

print("2) Arriving in Pyrite; the duel square")
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(F.get("orre_pyrite_cop"), "the officer lets the thief walk off")
for who, flag, sh in (("Chaser Calda", "orre_sq_calda", None), ("Chaser Emok", "orre_sq_emok", None),
                      ("Rider Nover", "orre_sq_nover", 9352), ("St.Performer Diogo", "orre_sq_diogo", None),
                      ("Rider Leba", "orre_sq_leba", None), ("Bandana Guy Divel", "orre_sq_divel", None),
                      ("Rider Vant", "orre_sq_vant", None), ("Roller Boy Lon", "orre_sq_lon", None)):
    meet(t, who)
    check(F.get(flag), f"{who} beaten")
    t = g.current_state
check(F.get("snagged_shadow_noctowl") and 9352 in mine(), "Nover's Shadow Noctowl snagged")
snags = [n for n in ("noctowl", "flaaffy", "skiploom", "quagsire", "misdreavus", "slugma") if F.get(f"snagged_shadow_{n}")]
check(len(snags) == 6, f"all six of the square's Shadow Pokemon snagged ({snags})")

print("3) Cail, the power, the Gear, the windmill, the jail")
t = town("PYRITE_TOWN", "PHENAC_CITY")
said_c = meet(t, "Rogue Cail") or []
check(not F.get("orre_beat_cail") and any("nobodies" in ln for ln in said_c), "Cail won't battle a nobody yet")
t = town("PYRITE_TOWN", "PHENAC_CITY")
meet(t, "Thug")
check(F.get("orre_heard_cail"), "the thug by the Colosseum names Cail")
t = town("PYRITE_TOWN", "PHENAC_CITY")
meet(t, "Rogue Cail")
check(F.get("orre_beat_cail") and F.get("snagged_shadow_furret"), "Cail beaten, his Shadow Furret snagged")
t = town("PYRITE_TOWN", "PHENAC_CITY")
step_into_zone(t, (13, 67))
check(F.get("orre_power_out"), "the scientist falls out of Duking's door: no power")
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(t._check_menu_condition("orre_power_out"), "the bike rides to the Construction Lot now")
p = route("CONSTRUCTION_LOT", "PYRITE_TOWN")
meet(p, "The Gear")
check(F.get("orre_got_gear") and story.inventory.get("GEAR"), "the Gear found at the Construction Lot")
t = town("PYRITE_TOWN", "CONSTRUCTION_LOT")
meet(t, "Duking")
check(F.get("orre_power_on"), "Duking: the Gear back in the windmill, the Colosseum has power")
t = town("PYRITE_TOWN", "PHENAC_CITY")
meet(t, "Jail Key")
t = town("PYRITE_TOWN", "PHENAC_CITY")
meet(t, "Prisoner")
check(F.get("orre_jail_prisoner") and story.inventory.get("TM018"), "the Jail Key frees the prisoner: TM18 Thief")

print("4) The Colosseum won; the bridge; Cipher's hideout")
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(any((tuple(tl) in t.barred) for tl in ((32, 40), (33, 40))), "the hideout's door is guarded before the badge")
story.badges.setdefault("ORRE", []).append("PYRITE") if isinstance(story.badges, dict) else None
story.story_flags["has_pyrite_badge"] = True
check(t._check_menu_condition("has_pyrite_badge"), "the Pyrite Badge counts")
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(not any((tuple(tl) in t.barred) for tl in ((32, 40), (33, 40))), "...and the guards step aside once you have it")
step_into_zone(t, (26, 34))
check(F.get("orre_beat_nore") and F.get("snagged_shadow_yanma"), "the bridge: Peon Nore beaten, his Shadow Yanma snagged")
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(F.get("orre_plusle_taken") and any("Plusle" in ln for ln in said), "back in town, Duking: Plusle has been taken")
p = route("PYRITE_BUILDING", "PYRITE_TOWN")
said_d = meet(p, "Hunter Doken") or []
check(not F.get("orre_beat_doken") and any("Miror B." in ln for ln in said_d), "Doken won't step aside before the roof")
for who, flag in (("Miror B. Peon Reath", "orre_roof_reath"), ("Miror B. Peon Ferma", "orre_roof_ferma"), ("Hunter Doken", "orre_beat_doken")):
    route("PYRITE_BUILDING", "PYRITE_TOWN")
    meet(g.current_state, who)
    check(F.get(flag), f"{who} beaten")
check(F.get("snagged_shadow_remoraid") and F.get("snagged_shadow_mantine") and F.get("snagged_shadow_qwilfish"),
      "the roof's Shadow Remoraid and Mantine, and Doken's Shadow Qwilfish, snagged")
for it, inv, n in (("Ein File H", "EIN_FILE_H", 1), ("Great Balls", "GREAT_BALL", 5), ("Revive", "REVIVE", 1),
                   ("Ein File S", "EIN_FILE_S", 1), ("Hyper Potions", "HYPER_POTION", 3)):
    before = story.inventory.get(inv, 0)
    route("PYRITE_BUILDING", "PYRITE_TOWN")
    meet(g.current_state, it)
    check(story.inventory.get(inv, 0) == before + n, f"{it} picked up")
t = town("PYRITE_TOWN", "PYRITE_BUILDING")
cave = next(o for o in g.loader.area_data["STORY_PROGRESSION"]["PYRITE_TOWN"]["travel_options"] if o["target_area"] == "PYRITE_CAVE")
check(t._check_menu_condition(cave["condition"]), "Pyrite Cave opens once Doken is beaten")

print("5) An older save already past Pyrite")
story.story_flags = {"got_snag_machine": True, "has_pyrite_badge": True, "orre_miror_cave": True}
t = town("PYRITE_TOWN", "PHENAC_CITY")
check(t._check_menu_condition(cave["condition"]), "Pyrite Cave still open")
check(not any((tuple(tl) in t.barred) for tl in ((32, 40), (33, 40))), "the hideout's door open")

print("##### orre_b1:", len(fails), "failures")
for f in fails:
    print("  -", f)
