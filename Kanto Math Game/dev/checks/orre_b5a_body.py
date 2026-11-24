# Orre batch 5a played (11-20, kanto_handoff/orre_check/BATCH_5A.md): Krane carried off from the HQ Lab, Lily's Machine Part,
# Gateon (Zook, Perr, its five trainers), Kaminko's (Chobin, Makan), the Cipher Lab (Hexagon Brothers, Naps, Krane, Lovrina),
# the Battle CD player. bash dev/checks/run_par.sh orre_b5a
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
                                        "orre_power_on", "has_pyrite_badge", "orre_miror_cave", "met_agate_elder", "orre_beat_skrub",
                                        "orre_dakim_mt_battle", "orre_time_flute", "cleared_the_under", "orre_maingate_key")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SP = g.loader.area_data["STORY_PROGRESSION"]

print("1) XD's trainers in our data, raised to fit")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
lab = [t["name"] for t in SP["XD_CIPHER_LAB"]["trainer_pool"]]
check(len(lab) == 21 and "Cipher Peon Resix" in lab and "Cipher R&D Klots" in lab, f"the Cipher Lab's 21 ({len(lab)})")
lov = next(o for o in SP["XD_CIPHER_LAB"]["route_menu"] if o["text"] == "BATTLE CIPHER ADMIN LOVRINA")["event"]["battle"]
check(max(lov["levels"]) == 41 and lov["levels"][-1] == 41, f"Lovrina's ace (Shadow Delcatty) at Part 2's stage, 41 (L1 11-24) ({lov['levels']})")
check(max(TR["xd:Story:17"]["levels"]) == 47, "Naps's Shadow Teddiursa at 47")

print("2) The HQ Lab: Krane carried off")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
check(not F.get("xd_kidnap_seen"), "before Ein's Lab: nothing happening")
F["orre_ein_lab"] = True
F["orre_part2"] = True   # (Part 2 begins once Evice is beaten: story rework 11-24)
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
check(F.get("xd_kidnap_seen"), "after Ein: Naps drags Krane out, Lily asks for help")
meet(t, "Spy Naps")
check(F.get("xd_krane_taken") and F.get("snagged_shadow_teddiursa"), "Naps beaten, his Shadow Teddiursa snagged; they drive off with Krane")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Lily")
check(F.get("xd_lily_asked"), "Lily asks for the Machine Part")

print("3) Gateon, Perr, Kaminko's House")
t = town("GATEON_PORT", "POKEMON_HQ_LAB")
check(F.get("xd_zook_scene"), "Gateon: Zook, Mr. Verich and Ardos's Alakazam")
check(not t._check_menu_condition(next(o for o in SP["GATEON_PORT"]["travel_options"] if o["target_area"] == "XD_CIPHER_LAB")["condition"]),
      "the Cipher Lab isn't on the map yet")
meet(t, "Perr")
check(F.get("xd_perr_asked"), "Perr: Dad has the stockroom key, at Kaminko's")
route("KAMINKO_HOUSE", "GATEON_PORT")
meet(g.current_state, "KAMINKO'S HOUSE: CHOBIN")
route("KAMINKO_HOUSE", "GATEON_PORT")
meet(g.current_state, "MAKAN")
check(F.get("kaminko_chobin") and F.get("xd_makan_back") and F.get("xd_gateon_bridges"), "Chobin battled; Makan heads home and fixes the bridges")
for n in ("49", "50", "23"):
    route("KAMINKO_HOUSE", "GATEON_PORT")
    meet(g.current_state, f"BATTLE CD {n}")
check(all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("49", "50", "23")), "Battle CDs 49, 50 and 23 at Kaminko's")
t = town("GATEON_PORT", "KAMINKO_HOUSE")
meet(t, "Perr")
check(story.inventory.get("MACHINE_PART") == 1, "the Machine Part")
for who in ("Navigator Berk", "Sailor Bost", "Chaser Laken", "Casual Guy Cyle", "Bodybuilder Kilen"):
    t = town("GATEON_PORT", "KAMINKO_HOUSE")
    meet(t, who)
check(all(F.get(f) for f in ("xd_gateon_berk", "xd_gateon_bost", "xd_gateon_laken", "xd_gateon_cyle", "xd_gateon_kilen"))
      and story.inventory.get("TM240") and F.get("snagged_shadow_ledyba") and F.get("snagged_shadow_poochyena"),
      "Gateon's five; TM240 from Bost; Shadow Ledyba and Poochyena snagged")
t = town("GATEON_PORT", "KAMINKO_HOUSE")
meet(t, "Battle CD 06")
check(story.inventory.get("BATTLE_CD_06"), "Battle CD 06 in the Krabby Club")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Lily")
check(F.get("xd_machine_part_given") and not story.inventory.get("MACHINE_PART"), "the part to Lily; Datan traced the car to the Cipher Lab")
_cl = next(o for o in SP["GATEON_PORT"]["travel_options"] if o["target_area"] == "XD_CIPHER_LAB")["condition"]
t = town("GATEON_PORT", "POKEMON_HQ_LAB")
check(not t._check_menu_condition(_cl), "...but the Cipher Lab waits for Jasmine's Gateon Badge (S3 11-24)")
story.badges.setdefault("ORRE", []).append("GATEON")
t = town("GATEON_PORT", "POKEMON_HQ_LAB")
check(t._check_menu_condition(_cl), "now the Cipher Lab is on the map")

print("4) The Cipher Lab")
p = route("XD_CIPHER_LAB", "GATEON_PORT")
for who in lab:
    route("XD_CIPHER_LAB", "GATEON_PORT")
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("houndour", "spheal", "baltoy", "mareep", "gulpin", "seedot", "spinarak", "numel", "carvanha", "shroomish")),
      "the Hexagon Brothers' six Shadows and the lab's four snagged")
route("XD_CIPHER_LAB", "GATEON_PORT")
said_k = meet(g.current_state, "PROFESSOR KRANE") or []
check(not F.get("xd_krane_rescued"), "Krane can't be freed with Naps on guard")
route("XD_CIPHER_LAB", "GATEON_PORT")
meet(g.current_state, "CIPHER PEON NAPS")
route("XD_CIPHER_LAB", "GATEON_PORT")
meet(g.current_state, "PROFESSOR KRANE")
check(F.get("xd_lab_naps") and F.get("xd_krane_rescued"), "Naps beaten, Krane freed")
route("XD_CIPHER_LAB", "GATEON_PORT")
meet(g.current_state, "BATTLE CIPHER ADMIN LOVRINA")
check(F.get("xd_lovrina_beaten") and F.get("snagged_shadow_delcatty"), "Lovrina beaten, her Shadow Delcatty snagged")
for it in ("ID CARD", "REVIVE", "ETHER", "SUPER POTIONS", "GREAT BALL", "LEAF STONE", "BATTLE CD 42"):
    route("XD_CIPHER_LAB", "GATEON_PORT")
    meet(g.current_state, it)
check(story.inventory.get("ID_CARD") and story.inventory.get("LEAF_STONE") and story.inventory.get("BATTLE_CD_42"), "the lab's items and Battle CD 42")

print("5) The Battle CD player")
mine = [p.id for p in story.player_team]
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Battle CD player")
pk = g.current_state
names = [c[0] for c in getattr(pk, "choices", [])]
check(type(pk).__name__ == "PickListState" and any(n.startswith("CD 06") for n in names), f"it lists the CDs you own ({names})")
if type(pk).__name__ == "PickListState":
    _ice = story.inventory.get("ICE_HEAL", 0)
    pk.pick("06")
    for _ in range(60):
        st = g.current_state
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            break
        if getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            st.dialogue_box.advance()
        elif getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()
    lent = [p.id for p in story.player_team]
    check(lent == [215, 25, 143], f"CD 06 lends its own team: Sneasel, Pikachu, Snorlax ({lent})")
    for p in story.player_team:   # (the test plays to finish, not to solve the puzzle: the lent team made strong)
        p.level = 100
        p.heal_full()
    play(4000)
check(F.get("battle_cd_06_cleared"), "won: Battle CD 06 cleared")
check(story.inventory.get("ICE_HEAL", 0) >= _ice + 1, "its prize, XD's: an Ice Heal (the first clear only)")
check([p.id for p in story.player_team] == mine, "your own team is back afterwards")

print("6) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m10") < jm.index("orre_m10b") < jm.index("orre_m10c") < jm.index("orre_m11"),
      "Ein's Lab, then trouble at the HQ Lab, the Machine Part, the Cipher Lab")

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
