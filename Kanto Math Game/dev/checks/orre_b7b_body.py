# Orre batch 7b played (11-21, kanto_handoff/orre_check/BATCH_7B.md): Colosseum's Realgam Tower - the lobby's trainers and its shut
# door to the roof, the old man in the tower yard, the Dome Halls' Admins and their keys (a missed Shadow's second chance), the
# giant door, the healing machine, the Tower Halls (the Johto-starter peons, Silva, the lifts, Gonzap), the roof lift, the rooftop
# run with no healing between (Nascour, Evice), the Hall of Fame in Realgam's look, the Journal. bash dev/checks/run_par.sh orre_b7b
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
                                        "beat_gonzap", "xd_gorigan_beaten", "xd_lair_voltage")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER", "PHENAC", "ORRE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
SP = g.loader.area_data["STORY_PROGRESSION"]
CC = "CIPHER_COMMAND"
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))

print("1) The rooftop run's line-up")
gym = SP["REALGAM_TOWER"]["gym"]
check([t["name"] for t in gym["trainers"]] == ["Bodybuilder Jomas", "Rider Delan", "Cipher Peon Nella", "Cipher Peon Ston", "Cipher Nascour"],
      "four matches (Jomas, Delan, Nella, Ston), then Nascour")
ld = gym["leader"]
check(ld["name"] == "Cipher Head Evice" and max(ld["levels"]) == 37 and ld["team"][0] == TR["col:439"]["team"][0] and ld.get("victory_flag") == "orre_evice_beaten",
      f"Evice last (ace {max(ld['levels'])}, Part 1's end - story rework 11-24), his Shadow Tyranitar leading")
check(gym["requirements"].get("flag") == "col_gonzap_realgam", "the rooftop opens once Gonzap's beaten inside")
check(max(gym["trainers"][-1]["levels"]) == 36 and min(min(t["levels"]) for t in gym["trainers"][:4]) >= 34, "the matches at Lv 34-35, Nascour 36 (Part 1's stage, L1 11-24)")

print("2) The lobby")
t = town("REALGAM_TOWER", "PHENAC_CITY")
t._go("realgam", "")
frames(2)
t = g.current_state
up = next(tuple(k) for k, v in t.exits.items() if v == "ROOM:colosseum")
check(up in t.barred, "the lobby's door up to the roof is shut")
for who in ("Hunter Aline", "St.Performer Luper", "Bandana Guy Klest"):
    meet(g.current_state, who)
check(all(F.get(f"col_{n}_realgam") for n in ("aline", "luper", "klest")), "the lobby's three trainers")

print("3) The tower yard: the old man")
p = route(CC, "REALGAM_TOWER")
said.clear()
meet(p, "OLD MAN")
check(F.get("col_oldman_realgam") and F.get("snagged_shadow_sunflora") and any("disguise" in ln for ln in said),
      "the old man's a peon in disguise: Baila, Shadow Sunflora snagged")

print("4) The Dome Halls: the Admins and their keys")
p = g.current_state
p.run.made(2)
p.run.enter_floor(2)
frames(2)
gate = p._here_art()["barred"][0]
check(not p._until_met(gate["until"]), "the giant door is shut")
for who in ("Cipher Peon Arton", "Cipher Peon Dioge"):
    meet(g.current_state, who)
check(F.get("snagged_shadow_delibird") and F.get("snagged_shadow_heracross"), "Arton and Dioge: Shadow Delibird and Heracross")
F["snagged_shadow_suicune"] = True   # (caught in The Under: Venus has her usual team)
said.clear()
meet(g.current_state, "CIPHER ADMIN VENUS")
check(F.get("col_venus_realgam") and story.inventory.get("BLUE_KEY"), "Venus beaten: the Blue Key")
meet(g.current_state, "CIPHER ADMIN EIN")
check(F.get("col_ein_realgam") and story.inventory.get("YELLOW_KEY") and F.get("snagged_shadow_raikou"),
      "Ein brings the Raikou missed in his lab: a second chance, snagged; the Yellow Key")
F["snagged_shadow_sudowoodo"] = F["snagged_shadow_entei"] = True
meet(g.current_state, "CIPHER ADMIN MIROR B.")
meet(g.current_state, "CIPHER ADMIN DAKIM")
check(story.inventory.get("RED_KEY") and story.inventory.get("GREEN_KEY"), "Miror B. and Dakim: the Red and Green Keys")
p = g.current_state
p.run.made(2)
p.run.enter_floor(2)
frames(2)
check(p._until_met(gate["until"]), "the four keys open the giant door")
for q in story.player_team:
    q.current_hp = 1
said.clear()
st = g.current_state
m = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "HEALING MACHINE")
for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    b_ = (m.x + dx, m.y + dy)
    if st.run.floor.walkable(*b_) and st.run.floor.mover_at(*b_) is None:
        st.run.player = b_
        st.step(-dx, -dy)
        break
play()
check(all(q.current_hp == q.get_max_hp() for q in story.player_team), "the Dome Halls' healing machine heals the team")
jm = [mm for mm in g.loader.area_data["JOURNAL_MISSIONS"] if mm["id"] == "orre_m18"][0]
check(story.mission_flag_done(jm), "the Journal's first Realgam step is done with all four Admins")

print("5) The Tower Halls: the peons, Silva, the lifts, Gonzap")
for who in ("Chaser Trus", "Rider Kevel", "Rider Elose", "Chaser Rugen", "Cipher Peon Bopen", "Bodybuilder Givern"):
    meet(g.current_state, who)
check(len(story.defeated_trainers.get(CC, set())) >= 8, f"the halls' trainers beaten ({len(story.defeated_trainers.get(CC, set()))})")
F["snagged_shadow_quilava"] = F["snagged_shadow_croconaw"] = True
for who in ("CIPHER PEON VERDE", "CIPHER PEON ROSSO", "CIPHER PEON BLUNO"):
    meet(g.current_state, who)
check(F.get("col_verde_realgam") and F.get("snagged_shadow_bayleef") and F.get("col_rosso_realgam") and F.get("col_bluno_realgam"),
      "the Johto-starter peons: Verde brings the missed Bayleef (snagged); Rosso and Bluno their usual teams")
said.clear()
meet(g.current_state, "BLACK-SUITED MAN")
check(F.get("col_silva_realgam") and any("Silva" in ln for ln in said), "the man in the black suit is Silva, undercover")
said.clear()
meet(g.current_state, "LIFT (LEFT)")
check(any("won't open" in ln for ln in said) and not F.get("col_gonzap_realgam"), "the left lift's dead")
said.clear()
meet(g.current_state, "LIFT TO THE ROOF")
check(any("won't come" in ln for ln in said), "the roof lift won't come before Gonzap")
meet(g.current_state, "LIFT (RIGHT)")
check(F.get("col_gonzap_realgam") and F.get("snagged_shadow_skarmory"), "Gonzap steps out of the right lift: beaten, his Shadow Skarmory snagged")
said.clear()
st = g.current_state
m = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "LIFT TO THE ROOF")
for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    b_ = (m.x + dx, m.y + dy)
    if st.run.floor.walkable(*b_) and st.run.floor.mover_at(*b_) is None:
        st.run.player = b_
        st.step(-dx, -dy)
        break
for _ in range(60):
    s_ = g.current_state
    if type(s_).__name__ == "PickListState":
        s_.pick("colosseum")
    elif getattr(s_, "npc_active", False) or (getattr(s_, "dialogue_box", None) is not None and getattr(s_.dialogue_box, "visible", False)):
        play(5)
    s_.update(); s_.draw()
    if isinstance(g.current_state, _WTS) and getattr(g.current_state, "room", None) == "colosseum":
        break
check(isinstance(g.current_state, _WTS) and getattr(g.current_state, "room", None) == "colosseum",
      f"the roof lift rides up to Cipher's Colosseum ({type(g.current_state).__name__}, {getattr(g.current_state, 'room', None)})")
t = town("REALGAM_TOWER", "PHENAC_CITY")
t._go("realgam", "")
frames(2)
t = g.current_state
check(up not in t.barred, "the lobby's door to the roof opens too")

# (6, the old Gym lobby screen's run - Evice as Champion, the Hall of Fame - retired 11-24: Orre's tournaments are walked
#  (R2 below plays Evice's run, which ends Part 1), and the League's Hall of Fame and title are the end of the Orre
#  playthrough's story: dev/checks/orre_playthrough_body.py, goal beat_orre_champion)
from src.world import gym_swaps as _gsw

print("7) The Journal")
jm = [m_["id"] for m_ in g.loader.area_data["JOURNAL_MISSIONS"] if m_["id"].startswith("orre_m")]
check(jm.index("orre_m17c") < jm.index("orre_m18") < jm.index("orre_m18b") < jm.index("orre_m18c"),
      "Gorigan, the four keys, inside the tower, Cipher's Colosseum")


print("R2) Cipher's Colosseum walked (11-23): the host starts the run, the six walk in one by one, Evice - Part 1's end")
from src.pokemon.data import Pokemon as _TP
from src.world import levels as _tlv
F = story.story_flags
_keep = (list(story.player_team), dict(F), {k_: list(v_) for k_, v_ in story.badges.items()})
_t = []
for pid in (248, 6, 9, 3, 65, 149):
    p_ = _TP(g.loader.fetch_specific(pid), g.assets, size_mult=2.5); _tlv.set_team([p_], [100], exact=True); p_.heal_full(); _t.append(p_)
story.player_team = _t
F.update({"col_gonzap_realgam": True})
for k_ in ("beat_orre_champion", "orre_evice_beaten", "orre_part2"):
    F.pop(k_, None)
_gsw.apply(g)
for k_ in [k_ for k_ in F if k_.startswith(("gym_progress_REALGAM", "orre_tourney"))]:
    F.pop(k_, None)
story.badges["ORRE"] = ["PHENAC", "PYRITE", "AGATE", "SNAGEM"]
t = town("REALGAM_TOWER", "PHENAC_CITY"); t._go("realgam", "OUT:31,7"); frames(2)
t._go("colosseum", "ROOM:realgam"); frames(3)
_heard = []
for _try in range(4):   # (a lost run starts over: sign up again, as a player would)
    if type(g.current_state).__name__ != "WalkTownState" or getattr(g.current_state, "room", None) != "colosseum":
        t = town("REALGAM_TOWER", "PHENAC_CITY"); t._go("realgam", "OUT:31,7"); frames(2)
        t._go("colosseum", "ROOM:realgam"); frames(2)
    for p_ in story.player_team:
        p_.heal_full()
    said.clear()
    meet(g.current_state, "Realgam Tower: Cipher's Colosseum")
    _heard += said
    for _ in range(12):
        play(4000)
        _heard += said
        if story.story_flags.get("orre_evice_beaten") or not story.story_flags.get("orre_tourney_REALGAM_TOWER"):
            break
    if story.story_flags.get("orre_evice_beaten"):
        break
_calls = list(dict.fromkeys(h_ for h_ in _heard if "takes the field" in h_))
check(len(_calls) == 6 and "Evice" in _calls[-1], f"six walk in, Evice last ({len(_calls)})")
check(story.story_flags.get("orre_evice_beaten") and not story.story_flags.get("beat_orre_champion"),
      f"Evice beaten: Part 1's end, not the title ({type(g.current_state).__name__})")
from src.world import orre_tournament as _ot
_was = story.current_area_key
story.current_area_key = "REALGAM_TOWER"
check(not _ot.condition(story, "on") and not _ot.condition(story, "lost"),
      f"back on the tower top later, the run is closed (the five-year skip ends it), not lost (count {story.story_flags.get('gym_progress_REALGAM_TOWER')}, "
      f"battle {story.story_flags.get('orre_tourney_fight_REALGAM_TOWER')})")
story.current_area_key = _was
story.player_team, _f, story.badges = _keep[0], _keep[1], _keep[2]
F.clear(); F.update(_f)
_gsw.apply(g)

print("FAILURES:", len(fails))
for f_ in fails:
    print("  ", f_)
