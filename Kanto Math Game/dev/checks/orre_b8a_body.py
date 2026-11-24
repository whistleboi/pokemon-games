# Orre batch 8a played (11-21, kanto_handoff/orre_check/BATCH_8A.md): Krane's Master Ball, Citadark Isle in seven floors - the dock,
# the Fortress (Lovrina, the crate wing), the Volcano's moving platforms, the Hook Hall's hooks, lift and drops, outside the Dome
# (Snattle, Ardos, Gorigan), Dome 1F's glass wall and Eldes, XD001 and Greevil; XD001 refused at the Relic Stone; the Journal.
# bash dev/checks/run_par.sh orre_b8a
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
                                        "orre_power_on", "has_pyrite_badge", "has_under_badge", "has_phenac_badge", "has_orre_badge",
                                        "beat_gonzap", "xd_gorigan_beaten", "col_gonzap_realgam", "beat_orre_champion",
                                        "move_offer_orre")}   # (Mom's offer to move already answered)
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER", "PHENAC", "ORRE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
SP = g.loader.area_data["STORY_PROGRESSION"]
CI = "XD_CITADARK_ISLE"
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))


def settle(st, n=600):
    for _ in range(n):
        if not getattr(st, "_ride", None) and st.anim == 0:
            return
        st.update(); st.draw()


def on(st, floor):
    st.run.made(floor); st.run.enter_floor(floor); frames(2)
    st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
    return st._here_art()


def nbrs(t):
    return [(t[0] + dx, t[1] + dy, dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]


def walk_into(st, target, avoid=()):
    """Stand beside target (on open ground, not a pad or track) and step onto it."""
    f = st.run.floor
    for x, y, dx, dy in nbrs(target):
        if f.walkable(x, y) and f.mover_at(x, y) is None and (x, y) not in avoid:
            st.run.player = (x, y); st.anim = 0; st.walk_goal = None
            st.step(-dx, -dy)
            settle(st)
            play(20)
            return True
    return False


print("1) Krane's Master Ball")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Professor Krane (the stairs)")
check(F.get("xd_master_ball") and story.inventory.get("MASTER_BALL") == 1, "after the title, Krane's secret staircase: the Master Ball")
gate = next(o for o in SP["GATEON_PORT"]["travel_options"] if o.get("target_area") == CI)
check("xd_master_ball" in str(gate.get("condition")) and "has_key_lair_badge" in str(gate.get("condition")),
      "Citadark on the map after the Master Ball and Norman's Key Lair Badge (S3/S4 11-24)")

story.badges.setdefault("ORRE", []).append("CITADARK")   # (Greevil faces you after Drake's Citadark Badge: S3 11-24)
print("2) The island")
p = route(CI, "GATEON_PORT")
meet(p, "NAVIGATOR AT THE DOCK")
meet(g.current_state, "PP MAX")
for who in ("Navigator Abson", "Cipher Peon Kleef"):
    meet(g.current_state, who)
check(story.inventory.get("BATTLE_CD_31") and story.inventory.get("PP_MAX") and F.get("snagged_shadow_golduck") and F.get("snagged_shadow_sableye"),
      "the dock: Battle CD 31, a PP Max, Abson's Shadow Golduck and Sableye")
pool = [t_["name"] for t_ in SP[CI]["trainer_pool"]]
check(len(pool) == 28 and "Team Magma Grunt Sola" in pool, f"26 trainers in the pool plus the Terra Cave's two Magma grunts (S6a), 6 in the story's own battles ({len(pool)})")
check(max(TR["xd:Story:168"]["levels"]) == 66 and max(TR["xd:Story:200"]["levels"]) == 75 and TR["xd:Story:199"]["levels"] == [78],
      "raised to fit: the dock's ace 66, Greevil's 75, XD001 Lv 78")

print("3) The Fortress")
p = g.current_state
art = on(p, 1)
check(len(art.get("boxes") or []) == 2, "two crates in the 2F wing")
lov = next(m for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "CIPHER ADMIN LOVRINA")
check(lov is not None, "Lovrina stands in the door at the lift")
meet(g.current_state, "CIPHER ADMIN LOVRINA")
check(F.get("xd_lovrina_citadark") and F.get("snagged_shadow_altaria"), "Lovrina beaten (XD001 is complete, she says): her Shadow Altaria snagged")
fort = [n for n in pool[2:16]]
for who in fort:
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("dodrio", "raticate", "kangaskhan", "banette", "magmar", "pinsir", "lickitung", "scyther", "chansey")),
      "the fortress's Shadows: Furgy's, Litnar's, Grupel's, Geftal's, Leden's")
p = g.current_state
on(p, 1)
f = p.run.floor
for crate in list(p._box_spots()):
    p.run.player = (crate[0] + 1, crate[1]); p.anim = 0
    p.step(-1, 0); settle(p); play(10)
check(sorted(p._box_spots()) == [(5, 3), (5, 6)], f"both crates slide into their alcoves ({sorted(p._box_spots())})")
for it in ("REVIVES", "WHITE HERBS", "FULL RESTORES (WING)", "HYPER POTIONS (WING)", "PP UP", "ELIXIR", "MAX ELIXIR", "FULL RESTORES",
           "ULTRA BALLS", "HYPER POTIONS"):
    meet(g.current_state, it)
check(story.inventory.get("WHITE_HERB") == 2 and story.inventory.get("REVIVE", 0) >= 2 and story.inventory.get("ULTRA_BALL", 0) >= 5
      and story.inventory.get("FULL_RESTORE", 0) >= 4 and story.inventory.get("MAX_ELIXIR"),   # (battle prizes add to some)
      "the fortress's boxes, the two behind crates too " + str({k: story.inventory.get(k) for k in ("WHITE_HERB", "REVIVE", "ULTRA_BALL", "FULL_RESTORE", "MAX_ELIXIR", "HYPER_POTION", "PP_UP", "ELIXIR")}))

print("4) The Volcano: moving platforms")
p = g.current_state
art = on(p, 2)
pls = art["platforms"]
check(len(pls) == 4, "four platforms")
f = p.run.floor


def ride_platform(st, pl, forward=True):
    track = [tuple(t) for t in pl["track"]]
    near, far = (track[0], track[-1]) if forward else (track[-1], track[0])
    stand = next((x, y, dx, dy) for x, y, dx, dy in nbrs(near) if st.run.floor.walkable(x, y) and (x, y) not in track)
    st.run.player = stand[:2]; st.anim = 0
    st.step(-stand[2], -stand[3])
    settle(st)
    return any(tuple(st.run.player) == (x, y) for x, y, _a, _b in nbrs(far))


check(ride_platform(p, pls[0]), "the first platform carries you to Kolest's island")
check(ride_platform(p, pls[1]), "the long one to the hidden ledge")
meet(g.current_state, "MAX POTIONS")
p = g.current_state
check(story.inventory.get("MAX_POTION") == 2, "the hidden ledge's 2 Max Potions")
check(ride_platform(p, pls[1], forward=False) and ride_platform(p, pls[2]), "back, and the bent track down to the spiral island")
meet(g.current_state, "RARE CANDY")
p = g.current_state
check(story.inventory.get("RARE_CANDY", 0) >= 3, "3 Rare Candy at the spiral's heart")
check(ride_platform(p, pls[3]), "the last platform to the guards' island")
for who in ("Cipher Peon Kolest", "Cipher Peon Kolin", "Cipher Peon Karbon", "Cipher Peon Petro"):
    meet(g.current_state, who)
check(F.get("snagged_shadow_rapidash") and F.get("snagged_shadow_magcargo") and F.get("snagged_shadow_hitmonchan") and F.get("snagged_shadow_hitmonlee"),
      "Kolest's Rapidash and Magcargo; the two big guards' Hitmonchan and Hitmonlee")

print("5) The Hook Hall: hooks, the lift, the drops")
p = g.current_state
art = on(p, 3)
hk = {h["colour"]: (tuple(h["a"]), tuple(h["b"])) for h in art["hooks"]}
wp = {(w["kind"], tuple(w["at"])): tuple(w["to"]) for w in art["warps"]}
pads = {t for ab in hk.values() for t in ab}


def ride_hook(st, colour, from_a=True):
    a, b = hk[colour]
    src, dst = (a, b) if from_a else (b, a)
    walk_into(st, src, avoid=pads)
    return tuple(st.run.player) == dst


check(ride_hook(p, "yellow"), "the yellow hook lifts you over the pit")
check(ride_hook(p, "pink"), "the pink hook on to the Timer Balls")
meet(g.current_state, "TIMER BALLS")
p = g.current_state
check(ride_hook(p, "red"), "the red hook to the lift side")
lift = next(at for (k, at) in wp if k == "lift" and at[1] > 5)
walk_into(p, lift)
check(p.run.player[1] < 5, "the lift up to the high gallery")
d1 = min(at for (k, at) in wp if k == "drop")
walk_into(p, d1)
check(tuple(p.run.player) == wp[("drop", d1)], "a glowing tile drops you into the first cut-off corner")
meet(g.current_state, "MAX REVIVE")
p = g.current_state
check(story.inventory.get("MAX_REVIVE"), "the corner's Max Revive")
p.run.player = wp[("drop", d1)]
check(ride_hook(p, "orange", False), "the orange hook out of the corner")
for who in ("Cipher Peon Jaymi", "Cipher Peon Gromlet"):
    meet(g.current_state, who)
for it in ("MAX ETHERS", "FULL HEALS", "REVIVES (HOOK HALL)"):
    meet(g.current_state, it)
check(story.inventory.get("MAX_ETHER") == 3 and story.inventory.get("FULL_HEAL") == 4 and story.inventory.get("TIMER_BALL") == 3,
      "the hall's Max Ethers, Full Heals and Timer Balls")

print("6) Outside the Dome")
p = g.current_state
art = on(p, 4)
bars = art["barred"]
door = [b for b in bars if "door" in " ".join(b["lines"])]
liftb = [b for b in bars if "lift" in " ".join(b["lines"])][0]
check(door and not p._until_met(door[0]["until"]) and not p._until_met(liftb["until"]), "the Dome's door and Kolax's lift are shut")
meet(g.current_state, "CIPHER ADMIN SNATTLE")
meet(g.current_state, "CIPHER ADMIN ARDOS")
check(F.get("xd_snattle_citadark") and F.get("xd_ardos_citadark") and F.get("snagged_shadow_snorlax") and F.get("snagged_shadow_solrock"),
      "Snattle (Solrock, Starmie), then Ardos at the door (Swellow, Electabuzz, Snorlax)")
p = g.current_state
check(p._until_met(door[0]["until"]), "the Dome's door opens after Ardos")
meet(g.current_state, "CIPHER ADMIN GORIGAN")
for who in ("Cipher Peon Kolax", "Cipher Peon Kimly"):
    meet(g.current_state, who)
p = g.current_state
check(F.get("xd_gorigan_citadark") and F.get("snagged_shadow_dugtrio") and p._until_met(liftb["until"]),
      "Gorigan runs; the last peon's Shadow Dugtrio; Kolax's lift opens")

print("7) Dome 1F: the glass wall, Eldes")
p = g.current_state
art = on(p, 5)
glass = [b for b in art["barred"] if "thick glass" in " ".join(b["lines"])]
check(len(glass) == 5 and not p._until_met(glass[0]["until"]), "the glass wall is up")
meet(g.current_state, "CIPHER ADMIN ELDES")
for who in ("Cipher R&D Kaller", "Cipher R&D Loket"):
    meet(g.current_state, who)
p = g.current_state
check(F.get("xd_eldes_beaten") and F.get("snagged_shadow_salamence") and p._until_met(glass[0]["until"]),
      "Eldes beaten (his Shadow Salamence among four): the glass comes down")

print("8) Dome 2F: XD001, then Greevil")
said.clear()
story.inventory["POKE_BALL"] = 99
meet(g.current_state, "GRAND MASTER GREEVIL")
check(F.get("xd_xd001") and F.get("snagged_shadow_lugia") and any("XD001" in ln for ln in said), "XD001 descends: Shadow Lugia snagged")
lug = next((q for q in list(story.player_team) + list(story.pc_pokemon or []) if q and q.id == 9400), None)
check(lug is not None and story.is_shadow(lug) and story.chamber_only(lug), "XD001 is yours, still a Shadow, its heart shut")
said.clear()
meet(g.current_state, "GRAND MASTER GREEVIL")
check(F.get("xd_greevil_beaten") and all(F.get(f"snagged_shadow_{n}") for n in ("moltres", "articuno", "zapdos", "rhydon", "exeggutor", "tauros"))
      and any("Eldes" in ln for ln in said), "Greevil's six Shadows snagged; Eldes talks his father into giving up")
meet(g.current_state, "BATTLE CD 46")
check(story.inventory.get("BATTLE_CD_46"), "Battle CD 46 on Greevil's empty seat")

print("9) XD001 won't purify at the Relic Stone")
from src.states.overworld.common import _choose_purify
story.player_team = [q for q in story.player_team if q and q is not lug][:5] + [lug]
t = town("AGATE_VILLAGE", "PYRITE_TOWN")
out = []
_choose_purify(g.current_state, [], lambda ls: out.extend(ls))
menu = g.current_state
if hasattr(menu, "on_select"):
    menu.on_select(len(story.player_team) - 1)
check(any("Purify Chamber" in ln for ln in out) and story.is_shadow(story.player_team[-1]), "the Relic Stone can't reach XD001's heart: only a Purify Chamber")

print("10) The Journal")
jm = [m_["id"] for m_ in g.loader.area_data["JOURNAL_MISSIONS"]]
check(jm.index("orre_s5") + 1 == jm.index("orre_s5b"), "Krane's Master Ball, then Citadark Isle")

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
