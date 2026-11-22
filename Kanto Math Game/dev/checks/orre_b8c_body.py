# Orre batch 8c played (11-21, kanto_handoff/orre_check/BATCH_8C.md): Colosseum after the title - Nett's tip, the kid behind
# Pyrite's bookcase, Cail, the Snagem raid (missed Shadows, the coloured peons, grunts), Gurks, the Lab's peon, Biden, Agrev,
# Gonzap and the D-Disk, the Deep Colosseum's five rounds, Realgam's rematches (raised, healed), Fein, the Journal.
# bash dev/checks/run_par.sh orre_b8c
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

from src.world import xd_colosseum as XC, col_post, miror_radar
from src.states.overworld.gym_lobby import GymLobbyState

story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "has_under_badge", "has_phenac_badge", "has_orre_badge",
                                        "beat_gonzap", "xd_gorigan_beaten", "col_gonzap_realgam", "beat_orre_champion", "move_offer_orre",
                                        "orre_heard_cail", "orre_beat_cail", "orre_kids_grid", "orre_power_up_part", "met_agate_elder")}
F = story.story_flags
_TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))
for _a in ("THE_UNDER", "SNAGEM_HIDEOUT", "SHADOW_PKMN_LAB", "DEEP_COLOSSEUM", "OUTSKIRT_STAND", "PYRITE_TOWN", "REALGAM_TOWER"):
    _m = _TM.get(_a) or {}
    for _f in [_m] + list(_m.get("floors") or []) + list((_m.get("rooms") or {}).values()):   # (the places' earlier scenes: seen)
        for _sc in _f.get("scenes") or []:
            if _sc.get("flag"):
                F[_sc["flag"]] = True
F["cleared_the_under"] = True
story.badges = {"ORRE": ["PYRITE", "UNDER", "PHENAC", "ORRE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
SP = g.loader.area_data["STORY_PROGRESSION"]
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))


def team_reset(six=True):
    """The OP test team (Jordan 11-21): six Lv 100 legends, perfect IVs, full EVs, base stats tripled."""
    story.player_team = [mk(i) for i in (150, 249, 250, 384, 383, 382)]
    for p in story.player_team:
        p.level = 100
        p.base_stats = {k: v * 3 for k, v in dict(p.base_stats).items()}
        p.ivs = {k: 31 for k in p.IV_KEYS}
        p.evs = {k: 252 for k in p.IV_KEYS}
        p.heal_full()


team_reset()
# every Colosseum Shadow snagged except the ones this run looks for
for a in SP.values():
    for e in a.get("shadow_pool") or []:
        if (g.loader.area_data["SHADOW_DATA"].get(str(e["id"])) or {}).get("game") == "col":
            F[e["flag"]] = True
for f in ("snagged_shadow_yanma", "snagged_shadow_bayleef", "snagged_shadow_croconaw", "snagged_shadow_smeargle",
          "snagged_shadow_ursaring", "snagged_shadow_skarmory", "snagged_shadow_shuckle", "snagged_shadow_togetic"):
    F.pop(f, None)

print("1) The disc trainers, raised to fit")
check(max(TR["c8c:441"]["levels"]) == 72 and 9351 in TR["c8c:441"]["team"] and 9351 not in TR["c8c:442"]["team"], "Cail ~72, with and without Furret")
check(max(TR["c8c:426"]["levels"]) == 78, "Gonzap 78")
check([max(TR[f"c8c:{i}"]["levels"]) for i in (165, 214, 329, 406, 378)] == [77, 79, 81, 83, 85], "the Deep Colosseum's finals 77..85, the Deep King 85")
check(max(TR["c8c:472"]["levels"]) == 82, "Fein 82")

print("2) Nett's tip, the kid, Cail")
t = route("THE_UNDER", "PYRITE_TOWN")
check(bool(meet(t, "NETT")) and F.get("col_post_nett"), "Nett: a kid in Pyrite saw Cail with a Shadow Pokemon")
t = town("PYRITE_TOWN", "ORRE_DESERT")
check(bool(meet(t, "Kid (behind the bookcase)")) and F.get("col_post_kid"), "the kid behind the bookcase")
t = town("PYRITE_TOWN", "ORRE_DESERT")
s = meet(t, "Rogue Cail")
if not F.get("col_cail_post"):
    s = meet(g.current_state, "Rogue Cail")
check(F.get("col_cail_post") and any("Snagem" in x for x in (s or [])), "Cail (his Furret's snagged: the team without it) points to Snagem")

print("3) The Snagem raid")
t = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
names = {m.payload.get("text") for i in range(t.run.n_floors) for m in t.run.made(i).movers if m.kind == "figure" and isinstance(m.payload, dict)}
check("Cipher Peon Nore" in names, "Nore is back with the Yanma you missed")
check("Cipher Peon Skrub" not in names, "Skrub isn't (his Hitmontop was snagged)")
check("Snagem Head Gonzap" not in names, "Gonzap waits till after Gurks")
s = meet(t, "Cipher Peon Nore")
check(F.get("snagged_shadow_yanma"), "Shadow Yanma snagged from Nore")
s = meet(g.current_state, "Coloured Cipher Peon")
check(F.get("snagged_shadow_bayleef") and any("Verde" in x for x in (s or [])), "the coloured peon: Verde with the Bayleef you missed")
s = meet(g.current_state, "Team Snagem Niver")
check(F.get("col_raid_473"), "a Snagem grunt (optional) battled")

print("4) Nett again, Gurks, the Lab's peon, the late Shadows, Gonzap")
t = route("THE_UNDER", "PYRITE_TOWN")
check(bool(meet(t, "NETT")) and F.get("col_post_nett2"), "Nett: ask Gurks")
s = meet(g.current_state, "Gurks")
check(F.get("col_gurks_post") and any("lab" in x.lower() for x in (s or [])), "Gurks on the Junk Shop balcony: the peon went to the old lab")
t = route("SHADOW_PKMN_LAB", "THE_UNDER")
s = meet(t, "Coloured Cipher Peon")
check(F.get("snagged_shadow_croconaw") and any("Bluno" in x for x in (s or [])), "in the Lab where Ein was: Bluno's Croconaw snagged")
t = route("SNAGEM_HIDEOUT", "ORRE_DESERT")
meet(t, "Snagem's Biden")
check(F.get("snagged_shadow_smeargle"), "Biden's Shadow Smeargle snagged")
meet(g.current_state, "Snagem's Agrev")
check(F.get("snagged_shadow_ursaring"), "Agrev's Shadow Ursaring snagged")
s = meet(g.current_state, "Snagem Head Gonzap")
check(F.get("snagged_shadow_skarmory") and story.inventory.get("D_DISK") == 1, "Gonzap: Shadow Skarmory snagged, the D-Disk")
lib = {e["flag"]: e for e in SP["SNAGEM_HIDEOUT"]["shadow_pool"]}
check(all(lib[f].get("event_only") for f in ("snagged_shadow_smeargle", "snagged_shadow_ursaring", "snagged_shadow_skarmory")),
      "the hideout's generic snag no longer hands out Smeargle, Ursaring or Skarmory")

print("5) Down to the Deep Colosseum")
t = route("THE_UNDER", "PYRITE_TOWN")
meet(t, "FLOATING PLATFORM")
for _ in range(400):
    if story.current_area_key == "DEEP_COLOSSEUM":
        break
    st = g.current_state
    if getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
        st.dialogue_box.advance()
    st.update(); st.draw()
check(story.current_area_key == "DEEP_COLOSSEUM", "the D-Disk sinks the platform to the Deep Colosseum")
t = route("DEEP_COLOSSEUM", "THE_UNDER")
check(not any(m.kind == "trainer" for m in t.run.floor.movers), "no standing trainers: the desk runs the rounds")
F["snagged_shadow_sudowoodo"] = True   # (Miror B.'s Sudowoodo snagged long ago: his team without it)
picked_ok = []
for r in range(1, 6):
    for _try in range(4):
        if XC.cleared(story, {"cleared": "col_deep_cleared"}) >= r:
            break
        team_reset()
        if not isinstance(g.current_state, PlayState):
            t = route("DEEP_COLOSSEUM", "THE_UNDER")
        st = g.current_state
        f = st.run.floor
        desk = next((m for m in f.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Deep Colosseum desk"), None)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b = (desk.x + dx, desk.y + dy)
            if f.walkable(*b) and f.mover_at(*b) is None:
                st.run.player = b; st.anim = 0
                st.step(-dx, -dy)
                break
        for _ in range(60):
            st = g.current_state
            if type(st).__name__ == "PickListState":
                break
            if getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
                st.dialogue_box.advance()
            st.update(); st.draw()
        offered = [v for _l, v in getattr(st, "choices", [])]
        picked_ok.append(r in offered)
        if r not in offered:
            break
        st.pick(r)
        play(30000)
    print("   deep round", r, "cleared", XC.cleared(story, {"cleared": "col_deep_cleared"}))
check(all(picked_ok), "each round offered once the one before is won")
check(F.get("col_deep_all"), "all five Deep Colosseum rounds won")
check(story.inventory.get("TM098") and story.inventory.get("TM078"), "rounds 2 and 4: TM Skill Swap, TM Dragon Claw")
check(F.get("snagged_shadow_shuckle"), "the Deep King's Shadow Shuckle snagged")

print("6) Realgam: the door down is shut; rematches raised and healed")
room = g.town_maps["REALGAM_TOWER"]["rooms"]["realgam"] if hasattr(g, "town_maps") else _json.load(open("assets/town_maps.json", encoding="utf-8"))["REALGAM_TOWER"]["rooms"]["realgam"]
check(any("no handle" in " ".join(b.get("lines", [])) for b in room.get("barred", [])), "Realgam's door to the Deep Colosseum is shut")
team_reset()
for p in story.player_team:   # (a Lv 75 team: above Lv 80 the League rematch rule lifts foes to your ace)
    p.level = 75
    p.heal_full()
story.current_area_key = "REALGAM_TOWER"
F["gym_progress_REALGAM_TOWER"] = 1
story.player_team[0].current_hp = 1
lobby = GymLobbyState(g, None)
check(story.player_team[0].current_hp == story.player_team[0].get_max_hp(), "between rematch battles your team is healed")
F["gym_progress_REALGAM_TOWER"] = 0
lobby = GymLobbyState(g, None)
seen_levels = []
from src.states.battle import TrainerBattleState as _TBS
_orig = _TBS.__init__


def _spy(self, game, team, *a, **k):
    seen_levels.append(max(p.level for p in team if p))
    return _orig(self, game, team, *a, **k)


_TBS.__init__ = _spy
lobby.challenge_gym()
_TBS.__init__ = _orig
check(seen_levels and seen_levels[0] == 78, f"the first rematch raised to fit (ace {seen_levels[:1]})")

print("7) Fein")
team_reset()
check(col_post.fein_due(g), "every other Colosseum Shadow snagged: Fein is due")
t = town("OUTSKIRT_STAND", "ORRE_DESERT")
s = meet(t, "Shady man")
check(F.get("snagged_shadow_togetic") and any("Fein" in x for x in (s or [])), "the shady man is Cipher Peon Fein: Shadow Togetic snagged")
lib = next(e for e in SP["ORRE_DESERT"]["shadow_pool"] if e["flag"] == "snagged_shadow_togetic")
check(lib.get("event_only"), "Togetic isn't in the desert's generic snag any more")

print("8) Missed Colosseum Shadows don't go to Miror B.")
story.inventory["MIROR_RADAR"] = 1
F["miror_b_missed"] = []
x = mk(9366); x.level = 40; shadow.make_shadow(g, x)
F.pop("snagged_shadow_yanma", None)
miror_radar.miss(g, x)
check(not miror_radar.missed(g), "a missed Colosseum Shadow stays for the Snagem raid")
F["snagged_shadow_yanma"] = True

print("9) The Journal")
J = {j["id"]: j for j in g.loader.area_data.get("JOURNAL_MISSIONS", [])}
check(all(k in J for k in ("orre_s7", "orre_s7b", "orre_s7c")), "Nett's rumour, the Snagem raid, the Deep Colosseum")

print("FAILURES:", len(fails))
for f in fails:
    print("  ", f)
