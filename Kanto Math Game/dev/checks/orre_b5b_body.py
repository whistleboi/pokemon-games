# Orre batch 5b played (11-20, kanto_handoff/orre_check/BATCH_5B.md): Krane's data to Nett, ONBS before and during the raid,
# Duking's Poke Spots and trades, Miror B. and his radar (XD's way), Exol, Bonsly's family, Kaminko's crane and the scooter,
# the S.S. Libra, Pyrite's XD duel square. bash dev/checks/run_par.sh orre_b5b
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
                                        "orre_dakim_mt_battle", "orre_time_flute", "cleared_the_under", "orre_maingate_key", "orre_ein_lab",
                                        "xd_kidnap_seen", "xd_krane_taken", "xd_lily_asked", "xd_machine_part_given", "xd_krane_rescued",
                                        "xd_lovrina_beaten", "xd_perr_asked", "kaminko_chobin", "xd_makan_back")}   # (5a done: Perr, Chobin, Makan)
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SP = g.loader.area_data["STORY_PROGRESSION"]
from src.world import miror_radar



def scenes_done(n=600):
    for _ in range(n):
        st = g.current_state
        run = getattr(st, "_scene_run", None)
        busy = run is not None and (run.playing or run.departing)
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance()
        elif not busy:
            return
        st.update(); st.draw()


print("1) XD's trainers in our data")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
ex = next(o for o in SP["XD_ONBS"]["route_menu"] if o["text"] == "BATTLE CIPHER CMDR EXOL")["event"]["battle"]
check(max(ex["levels"]) == 50 and len(SP["XD_ONBS"]["trainer_pool"]) == 10, f"Exol's ace 50; the raid's ten peons ({ex['levels']})")
check(max(TR["xd:Story:72"]["levels"]) == 50 and max(TR["xd:Story:128"]["levels"]) == 52, "Miror B. at the Cave 50, Smarton on the Libra 52")

print("2) Krane's data to Nett; ONBS before the raid")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
meet(t, "Lily")
check(story.inventory.get("XD_DATA_ROM") == 1, "home again, Krane hands over his data for Nett")
p = route("XD_ONBS", "PYRITE_TOWN")
on = {m.payload[1].get("name") for f in range(4) for m in p.run.made(f).movers if m.kind == "trainer"}
check(not on, f"no Cipher in ONBS yet ({on})")
for who in ("SECC", "KANDEE", "KANDEE'S MOTHER"):
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, who)
check(F.get("xd_kandee_home") and story.inventory.get("SOOTHE_BELL"), "lost Kandee back to her mother: a Soothe Bell")
route("XD_ONBS", "PYRITE_TOWN")
meet(g.current_state, "NETT")
check(F.get("xd_nett_rom") and not story.inventory.get("XD_DATA_ROM"), "Nett takes the data, sends you to Duking")

print("3) The Poke Spots and Miror B.")
pt = SP["PYRITE_TOWN"]["travel_options"]
oasis = next(o for o in pt if o.get("target_area") == "OASIS_POKE_SPOT")["condition"]
check(not F.get(oasis), "the Oasis isn't on the map yet")
route("ORRE_POKE_SPOTS", "ORRE_DESERT")
meet(g.current_state, "DUKING AT THE ROCK")
check(F.get("xd_spot_oasis"), "Duking at the Rock: Pofty's interview, the Oasis revealed")
route("OASIS_POKE_SPOT", "PYRITE_TOWN")
meet(g.current_state, "DUKING AT THE OASIS")
check(F.get("xd_spot_cave"), "at the Oasis: the Cave revealed")
story.player_team.append(mk(194))
route("OASIS_POKE_SPOT", "PYRITE_TOWN")
meet(g.current_state, "DUKING AT THE OASIS")
lar = next((p for p in story.player_team if p and p.id == 246), None)
check(lar is not None and "DRAGON-DANCE" in lar.moves and F.get("xd_duking_larvitar"), "a Wooper traded: Duking's Larvitar, with Dragon Dance")
story.player_team = [p for p in story.player_team if p and p.id != 246]
p = route("CAVE_POKE_SPOT", "AGATE_VILLAGE")
scenes_done()
check(F.get("xd_cave_folly"), "the Cave: Folly and Trudly with their radar")
meet(g.current_state, "MIROR B. AT THE CAVE")
check(F.get("xd_miror_cave") and story.inventory.get("MIROR_RADAR") and F.get("snagged_shadow_voltorb"),
      "Miror B. beaten (Shadow Voltorb snagged); he drops the Miror B. Radar")

print("4) The radar, XD's way")
vul = next(s for s in SP["XD_ONBS"]["shadow_pool"] if "Vulpix" in s["name"])
fake = mk(vul["id"]); fake.level = 46
miror_radar.miss(g, fake)
check(miror_radar.missed(g) and miror_radar.missed(g)[0][0] == vul["flag"], "a Shadow beaten unsnagged goes to Miror B.")
spot = miror_radar.where(g)
check(spot in miror_radar.SPOTS and any("beeping" in ln for ln in miror_radar.radar_lines(g)), f"the radar says where he is today ({spot})")
p = route("XD_ONBS", "PYRITE_TOWN")
check(p._next_shadow() is None or p._next_shadow()["flag"] != vul["flag"], "it's no longer in ONBS's Snag list")
route(spot, "PYRITE_TOWN")
meet(g.current_state, "WANDERER MIROR B.")
check(F.get(vul["flag"]) and not miror_radar.missed(g), "battled at the Poke Spot: snagged back, the radar goes quiet")

print("5) The ONBS raid")
p = route("XD_ONBS", "PYRITE_TOWN")
names = [t["name"] for t in SP["XD_ONBS"]["trainer_pool"]]
for who in names:
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("duskull", "ralts", "makuhita")), "the raid's Shadows snagged (Duskull, Ralts, Makuhita)")
route("XD_ONBS", "PYRITE_TOWN")
meet(g.current_state, "BATTLE CIPHER CMDR EXOL")
check(F.get("xd_exol_beaten") and F.get("snagged_shadow_mawile"), "Exol beaten, his Shadow Mawile snagged")
for it in ("ETHER", "HP UP", "REVIVE", "BATTLE CD 21", "BATTLE CD 24", "NETT", "BONSLY'S GRANDFATHER"):
    route("XD_ONBS", "PYRITE_TOWN")
    meet(g.current_state, it)
check(story.inventory.get("HP_UP") and story.inventory.get("BATTLE_CD_21") and story.inventory.get("BATTLE_CD_24"), "ONBS's items, Battle CDs 21 and 24")
check(F.get("xd_nett_libra") and F.get("xd_bonsly_asked"), "Nett: the Libra was Cipher's; Bonsly's grandfather asks for help")

print("6) Perr's grandfather and the scooter")
gt = SP["GATEON_PORT"]["travel_options"]
libc = next(o for o in gt if o.get("target_area") == "SS_LIBRA")["condition"]
check(not F.get(libc), "the Libra's out of reach in the deep sand")
t = town("GATEON_PORT", "PYRITE_TOWN")
meet(t, "Perr")
check(F.get("xd_perr_grandpa"), "Perr: Grandpa's on Kaminko's crane floor")
route("KAMINKO_HOUSE", "GATEON_PORT")
meet(g.current_state, "CHOBIN AGAIN")
check(F.get("xd_chobin3") and story.inventory.get("SUN_STONE"), "Chobin's third battle: a Sun Stone")
for it in ("PERR'S GRANDFATHER", "BATTLE CD 05", "BATTLE CD 11", "BATTLE CD 29"):
    route("KAMINKO_HOUSE", "GATEON_PORT")
    meet(g.current_state, it)
check(F.get("xd_scooter_sand") and all(story.inventory.get(f"BATTLE_CD_{n}") for n in ("05", "11", "29")),
      "the scooter rebuilt for deep sand; Battle CDs 05, 11 and 29 on the hook platforms")

print("7) The S.S. Libra")
route("SS_LIBRA", "GATEON_PORT", floor=2)
scenes_done()
check(F.get("xd_libra_gorigan"), "Gorigan scolds Snidle and Smarton on the bridge")
meet(g.current_state, "Cipher Peon Smarton")
check(story.is_trainer_defeated("SS_LIBRA", 0), "Smarton beaten")
for it in ("BATTLE CD 18", "IRON", "PP UPS", "MAX ETHER", "BONSLY"):
    route("SS_LIBRA", "GATEON_PORT")
    meet(g.current_state, it)
check(F.get("xd_bonsly_found") and story.inventory.get("BATTLE_CD_18") and story.inventory.get("MAX_ETHER"), "Bonsly found; the Libra's items, Battle CD 18")

print("8) Pyrite's duel square in XD's time")
for text in ("Rogue Cail", "Worker Dobit", "Chaser Finol", "Rider Dert", "Hunter Raling", "Chaser Labet", "Bodybuilder Doby"):
    t = town("PYRITE_TOWN", "XD_ONBS")
    meet(t, text)
check(all(F.get(f"xd_sq_{i}") for i in (62, 63, 64, 65, 66, 67, 68)), "the seven XD duel-square trainers")

print("9) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m11") < jm.index("orre_m11b") < jm.index("orre_m11c") < jm.index("orre_m12") < jm.index("orre_m12b") < jm.index("orre_m13"),
      "Lovrina, Nett's data, the Poke Spots, ONBS, the Libra, then Phenac")

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
