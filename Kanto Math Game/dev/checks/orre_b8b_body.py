# Orre batch 8b played (11-21, kanto_handoff/orre_check/BATCH_8B.md): XD after Greevil - Eagun at the HQ Lab, the Orre Colosseum's
# seven rounds (four in a row, healed between; a lost round), the Relic Stone's purify fixed, walking opening Shadow hearts, the
# Purify Chamber's nine sets (tempo, steps, XD001's best circle, its screen), Miror B.'s last Shadow Dragonite and the radar,
# Greevil's rematch, the Lucky Egg quest (Voice Cases), the Journal.
# bash dev/checks/run_par.sh orre_b8b
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


exec(open("dev/checks/orre_lib.py", encoding="utf-8").read())   # (meet, _fight, route, step_into_zone, town, _note, frames, check, mine: shared, Checks C5)


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


_MV = _json.load(open("assets/moves.json", encoding="utf-8"))

from src.world import purify_chamber as PC, xd_colosseum as XC, xd_post, miror_radar
from src.states.systems.purify_chamber import PurifyChamberState

story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "has_under_badge", "has_phenac_badge", "has_orre_badge",
                                        "beat_gonzap", "xd_gorigan_beaten", "col_gonzap_realgam", "beat_orre_champion",
                                        "move_offer_orre", "xd_master_ball", "xd_xd001", "xd_greevil_beaten", "orre_beat_skrub",
                                        "orre_beluh_tablet", "met_agate_elder", "xd_lovrina_beaten")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE", "UNDER", "PHENAC", "ORRE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 99}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
SP = g.loader.area_data["STORY_PROGRESSION"]
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))


def shadow_mon(form_id, level=50):
    m = mk(form_id)
    m.level = level
    shadow.make_shadow(g, m)
    return m


def team_reset(six=False):
    """six: an overpowered test team for the Colosseum's no-healing rounds (Jordan 11-21: "give an OP team to blow through
    the battles") - six Lv 100 legends, perfect IVs, full EVs, base stats tripled. The flow is under test, not the balance."""
    story.player_team = [mk(i) for i in ((150, 249, 250, 384, 383, 382) if six else (196, 197, 150))]
    for p in story.player_team:
        p.level = 100
        if six:
            p.base_stats = {k: v * 3 for k, v in dict(p.base_stats).items()}
            p.ivs = {k: 31 for k in p.IV_KEYS}
            p.evs = {k: 252 for k in p.IV_KEYS}
        p.heal_full()


print("1) The disc trainers, raised to fit")
colo = [TR.get(f"xdcolo:{r}:{m}") for r in range(1, 8) for m in range(1, 5)]
check(all(colo), "all 28 Orre Colosseum challengers are in")
check([max(TR[f"xdcolo:{r}:4"]["levels"]) for r in range(1, 8)] == [75, 76, 77, 78, 79, 80, 82], "each round's final 75..80, Eldes 82")
check([max(TR[f"xdcolo:{r}:1"]["levels"]) for r in range(1, 8)] == [74, 75, 76, 77, 78, 79, 80], "round r's challengers at 73+r")
check([TR[f"xdcolo:{r}:4"]["name"] for r in range(1, 8)] == ["Cipher Admin Lovrina", "Cipher Admin Snattle", "Cipher Admin Gorigan",
      "Robo Groudon Chobin", "Snagem Head Gonzap", "Cipher Admin Ardos", "Cipher Admin Eldes"], "the finals are the disc's")
check(max(TR["xd:Story:222"]["levels"]) == 72 and TR["xd:Story:222"]["team"][-1] == 26, "Eagun's six, ace Raichu 72")
check(max(TR["xd:Story:221"]["levels"]) == 78 and 9347 in TR["xd:Story:221"]["team"], "Miror B.'s five Ludicolo and Shadow Dragonite, ~78")
check(TR["xd:Colosseum:41"]["levels"][0] == 60, "the badge round's Greel stays at Lv 60 (its own key)")

print("2) Eagun at the HQ Lab, then the Orre Colosseum's rounds")
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
s = meet(t, "Eagun")
check(s is not None and F.get("xd_eagun_lab"), "Eagun battles you outside the lab")
check(any("Orre Colosseum" in x for x in (s or [])), "and tells you the Colosseum is running again")
t = town("ORRE_COLOSSEUM", "ORRE_DESERT")
picked = []
from src.states.systems import pick_list as _pl
_real_pick = _pl.PickListState.__init__


def _spy(self, game, back, title, choices, done):
    _real_pick(self, game, back, title, choices, done)
    picked.append([c[0] for c in choices])


_pl.PickListState.__init__ = _spy
said.clear()
desk = None


def desk_pick(r):
    st = g.current_state
    for _ in range(50):
        if type(st).__name__ == "PickListState":
            break
        _note(st)
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw(); st = g.current_state
    if type(st).__name__ == "PickListState":
        st.pick(r)


heal_seen = []
st = g.current_state
spot = next((sp for sp, o in st._people().items() if o.get("text") == "Colosseum desk"), None)
if spot is None:
    st._go("gym", ""); frames(2)
    spot = next((sp for sp, o in st._people().items() if o.get("text") == "Colosseum desk"), None)
check(spot is not None, "the Colosseum desk stands in the arena")


def talk_desk():
    st = g.current_state
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        b = (spot[0] + dx, spot[1] + dy)
        if st._open(b) and b not in st.exits:
            st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
            st.step(-dx, -dy)
            return


team_reset(True)
talk_desk()
desk_pick(1)
hp_between = []
_real_begin = XC.begin


def _spy_begin(game, rounds, r, m):
    hp_between.append((r, m, [p.current_hp for p in story.player_team if p]))
    return _real_begin(game, rounds, r, m)


XC.begin = _spy_begin
play(20000)
check(picked and picked[0] == ["ROUND 1"], "only Round 1 is open at first")
check(XC.cleared(story) == 1, "Round 1 won: four battles in a row")
check(story.inventory.get("TM175") == 1, "Round 1's prize: TM Toxic (our TM175)")
check(F.get("xd_beluh_mail"), "Beluh's e-mail comes after Round 1")
check(any("Lovrina Fan Club" in x for x in said), "and the title")
# the round's battles followed one another without healing
seen = [h for h in hp_between if h[0] == 1]
check(len(seen) >= 3, "battles 2-4 started straight after the one before (%d)" % len(seen))
check(seen and all(all(hp == p.get_max_hp() for hp, p in zip(h[2], [q for q in story.player_team if q])) for h in seen),
      "your team is healed before each next battle (Jordan 11-21)")
# losing a round: healed, back to battle 1 next time
team_reset()
for p in story.player_team:
    p.level = 5
    p.heal_full()
picked.clear()
talk_desk(); desk_pick(2)


def lose_all(n=80000):
    """Play on with wrong answers until the round is lost (as a player who keeps missing would)."""
    quiet = 0
    for _ in range(n):
        st = g.current_state
        nm = type(st).__name__
        if nm == "PokemonPartyMenuState" and getattr(st, "on_select", None):
            prev = getattr(getattr(st, "previous_state", None), "player_pokemon", None)
            nxt = next((i for i, p in enumerate(story.player_team) if p and p.current_hp > 0 and p is not prev), None)
            if nxt is None:
                break
            st.on_select(nxt); continue
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            b = st; quiet = 0
            if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
                b.btn_no.callback()
            elif b.phase == "TARGET_SELECT" and getattr(b, "_target_buttons", None):
                b._target_buttons[0].callback()
            elif b.phase in ("MENU", "BATTLE") and not b.dialogue_box.visible and b.math_ui and b.math_ui.visible:
                b.math_ui.on_click(next(i for i, o in enumerate(b.options) if o != b.correct_ans))
            elif b.phase == "MENU" and not b.dialogue_box.visible:
                b.open_move_menu(); b.choose_move([m.text.replace(" ", "-") for m in b.move_buttons if m.text][0])
            elif b.dialogue_box.visible:
                _note(b)
                b.dialogue_box.is_finished = True
                if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                    b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
                elif b.dialogue_box.callback:
                    cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
            b.feedback_timer = 0
            b.update(); b.draw()
            continue
        if getattr(st, "npc_active", False):
            _note(st); st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance(); quiet = 0
        else:
            quiet += 1
            if quiet > 60:
                return
        st.update(); st.draw()


said.clear()
lose_all()
check(any("Round 2 is over" in x for x in said), "the round ends when you lose a battle")
picked.clear()
talk_desk()
st = g.current_state
for _ in range(50):
    if type(st).__name__ == "PickListState":
        break
    if getattr(st, "npc_active", False):
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    st.update(); st.draw(); st = g.current_state
if type(st).__name__ == "PickListState":
    st.pick(None)
play(50)
check(picked and picked[0] == ["ROUND 1 (WON)", "ROUND 2"], "Round 1 marked won, Round 2 open")
check(XC.cleared(story) == 1, "losing Round 2 doesn't count it")
check(all(p.current_hp == p.get_max_hp() for p in story.player_team if p), "after a lost round your Pokemon are healed")
check(type(g.current_state).__name__ in ("CityState", "WalkTownState"), "and you're back in the Colosseum, not blacked out")
team_reset(True)
# rounds 2-7 straight through (the data path: each round's prize and the last flag)
tries = 0
for r in range(2, 8):
    for _try in range(4):   # (a lost round is tried again, healed at the Center first - as a player would)
        if XC.cleared(story) >= r:
            break
        tries += 1
        picked.clear()
        for p in story.player_team:
            p.heal_full(); p.pp = {}
        if not isinstance(g.current_state, _WTS):   # (left on another screen: note it, walk back in)
            print("   (round", r, "ended on", type(g.current_state).__name__, ")")
            town("ORRE_COLOSSEUM", "ORRE_DESERT")
        if not any(o.get("text") == "Colosseum desk" for o in g.current_state._people().values()):
            g.current_state._go("gym", ""); frames(2)
        talk_desk()
        st = g.current_state
        for _ in range(50):
            if type(st).__name__ == "PickListState":
                break
            if getattr(st, "npc_active", False):
                st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            st.update(); st.draw(); st = g.current_state
        offered = [v for _l, v in getattr(st, "choices", [])]
        if r not in offered:
            check(False, f"Round {r} is offered once Round {r - 1} is won ({offered})")
            break
        st.pick(r)
        play(30000)
    print("   round", r, "cleared", XC.cleared(story), [x for x in said if "Round" in x][-2:])
check(XC.cleared(story) == 7 and F.get("xd_colo_all"), "all seven rounds won")
check(all(story.inventory.get(tm) for tm in ("TM274", "TM098", "TM148", "TM085", "TM239", "TM078")),
      "each round's TM: Return, Skill Swap, Sludge Bomb, Rest, Steel Wing, Dragon Claw")
XC.begin = _real_begin
_pl.PickListState.__init__ = _real_pick

print("3) The Relic Stone's purify keeps nothing of the Shadow (fixed 11-21)")
team_reset()
m = shadow_mon(9406, 40)
m.shadow["gauge"] = 0
story.player_team.append(m)
name = story.purify_slot(len(story.player_team) - 1)
p = story.player_team[-1]
check(p.id == 296 and not getattr(p, "shadow", None), "purified Makuhita: its own species, no Heart Gauge left")
check("SHADOW-RUSH" not in (p.moves or []), "and no Shadow Rush")

print("4) Walking opens a Shadow Pokemon's heart (it never did before 11-21)")
team_reset()
m = shadow_mon(9406, 40)
story.player_team.append(m)
g0 = m.shadow["gauge"]
F["_shadow_steps"] = 0
t = town("AGATE_VILLAGE", "ORRE_DESERT")
st = g.current_state
moved = 0
for _ in range(400):
    if moved >= 70:
        break
    x, y = st.player
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b = (x + dx, y + dy)
        if st._open(b) and b not in st.exits and b not in st._people():
            st.anim = 0; st.step(dx, dy); st.anim = 0; moved += 1
            break
    if st is not g.current_state:
        break
check(m.shadow["gauge"] < g0, f"after {moved} steps its gauge opened ({g0} -> {m.shadow['gauge']})")

print("5) The Purify Chamber's rules")
F[PC.KEY] = None
sets = PC.sets(story)
check(len(sets) == 9, "nine sets")
r = lambda i: story._pokemon_record(mk(i))
check(PC.link(g, r(19), r(19)) == 1, "Normal counts as super effective on Normal")
check(PC.link(g, r(7), r(4)) == 1 and PC.link(g, r(4), r(7)) == -1, "Water on Fire +1, Fire on Water -1")
check(PC.link(g, r(25), r(50)) == -1, "an immunity (Electric on Diglett) counts as resisted")
ring = [r(7), r(4), r(361), r(1)]   # (Water -> Fire -> Ice -> Grass -> Water)
s0 = {"shadow": None, "ring": ring}
check(PC.flow(g, s0) == 4 and PC.tempo_max(g, s0), "Squirtle, Charmander, Snorunt, Bulbasaur round the ring: Max Tempo")
check(not PC.tempo_max(g, {"ring": ring[:3]}), "three in the ring is never Max Tempo")
sm = shadow_mon(9406, 40)
F[PC.KEY] = None
sets = PC.sets(story)
sets[0]["ring"] = [r(7), r(4), r(361), r(1)]
check(PC.put_shadow(g, 0, sm) is None, "a Shadow Pokemon goes in a set's middle")
before = sets[0]["shadow"]["shadow"]["gauge"]
F["_chamber_steps"] = 0
PC.walked(g, 161)
after = sets[0]["shadow"]["shadow"]["gauge"]
check(before - after == 192, f"161 steps: its heart opens by 96 x 2 at Max Tempo ({before - after})")
sets[0]["shadow"]["shadow"]["gauge"] = 50
said_c = PC.walked(g, 161)
check(PC.is_open(sets[0]["shadow"]) and said_c, "its heart opens, and the Lab tells you")
team_reset()
new = PC.purify(g, 0)
check(new is not None and new.id == 296 and not getattr(new, "shadow", None), "purified in the chamber: Makuhita, no gauge")

print("6) XD001: only when all nine sets are at Max Tempo")
lug = shadow_mon(9400, 78)
F[PC.KEY] = None
sets = PC.sets(story)
said_l = PC.put_shadow(g, 0, lug)
check(said_l and "Max Tempo" in " ".join(said_l), "refused before a best circle")
for s in sets:
    s["ring"] = [r(7), r(4), r(361), r(1)]
check(PC.best_circle(g), "all nine sets at Max Tempo")
check(PC.put_shadow(g, 0, lug) is None and PC.is_open(sets[0]["shadow"]), "XD001 goes in - its heart opens at once")
new = PC.purify(g, 0)
check(new is not None and new.id == 249 and not getattr(new, "shadow", None), "purified: Lugia")
check({"FEATHER-DANCE", "PSYCHO-BOOST"} <= set(getattr(new, "move_pool", []) or []), "it can learn Feather Dance and Psycho Boost")
check(F.get("xd_lugia_purified") and F.get("purified_line_249"), "the Journal's XD001 task closes; the line counts for Ho-Oh")

print("7) The chamber's screen at the Lab")
team_reset()
F[PC.KEY] = None
F["snagged_shadow_lugia"] = True
story.player_team.append(shadow_mon(9406, 40))
t = town("POKEMON_HQ_LAB", "GATEON_PORT")
s = meet(t, "Purify Chamber")
st = g.current_state
check(isinstance(st, PurifyChamberState), "Lily's Purify Chamber opens the chamber's screen")
if isinstance(st, PurifyChamberState):
    frames(5)
    st._open(2); frames(5)
    check(st.view == 2, "a set opens")
    st._pick(lambda i, mon: None)
    party = g.current_state
    check(type(party).__name__ == "PokemonPartyMenuState", "picking goes to your party")
    party.on_cancel()
    st = g.current_state
    st._pick = lambda then, want=None: then(("party", len(story.player_team) - 1), story.player_team[-1])
    st._shadow_in()
    check(PC.sets(story)[2]["shadow"] is not None and len(story.player_team) == 3, "the Shadow Pokemon went into set 3's middle")
    st._pick = lambda then, want=None: then(("party", 0), story.player_team[0])
    st._ring_in()
    check(len(PC.sets(story)[2]["ring"]) == 1 and len(story.player_team) == 2, "a party Pokemon joined its ring")
    for _ in range(60):
        st.update(); st.draw()
    check(st.angle > 30, "the ring turns round the middle")
    st._take_out()
    check(len(PC.sets(story)[2]["ring"]) == 0 and len(story.player_team) == 3, "taken back out to the party")
    del st._pick   # (the real picker: from the PC, Jordan 11-21)
    story.pc_pokemon[5] = mk(7)
    st._ring_in()
    where = g.current_state
    check(type(where).__name__ == "PickListState" and [v for _l, v in where.choices] == ["party", "pc"], "RING IN asks: your party or the PC")
    where.pick("pc")
    page = g.current_state
    check(type(page).__name__ == "PickListState" and 5 in [v for _l, v in page.choices], "the PC's page lists its Pokemon")
    page.pick(5)
    check(len(PC.sets(story)[2]["ring"]) == 1 and story.pc_pokemon[5] is None, "a PC Pokemon joins the ring and leaves its box")
    st._back(); st._back()
    check(not isinstance(g.current_state, PurifyChamberState), "BACK leaves the chamber")

print("8) Miror B.'s last Shadow Pokemon")
team_reset()
story.inventory["MIROR_RADAR"] = 1
for e in xd_post._xd_pool(g):
    if e["flag"] != xd_post.LAST_FLAG:
        F[e["flag"]] = True
check(not story.story_flags.get("snagged_shadow_dragonite") and xd_post.last_due(g), "every other XD Shadow snagged: Miror B. waits")
lib = next(e for e in SP["SS_LIBRA"]["shadow_pool"] if e["id"] == 9347)
check(lib.get("event_only"), "Shadow Dragonite isn't in the S.S. Libra's snag list any more")
t = town("GATEON_PORT", "ORRE_DESERT")
s = meet(t, "Wanderer Miror B.")
check(s is not None and F.get("snagged_shadow_dragonite"), "Miror B. on the harbour wall: Shadow Dragonite snagged")
check(9347 in mine(), "Dragonite is yours")
check(not miror_radar.has(story), "the radar's bug is crushed: the Miror B. Radar goes quiet")
check(any("bug" in x.lower() or "gadget" in x.lower() for x in (s or [])), "his hair gadget scene")

print("9) Greevil's rematch")
team_reset()
for f in xd_post.GREEVIL_FLAGS:
    F.pop(f, None)
F["snagged_shadow_moltres"] = True
F["snagged_shadow_lugia"] = True
gr = next(o for o in SP["XD_CITADARK_ISLE"]["route_menu"] if o["text"] == "GRAND MASTER GREEVIL")["event"]["then"]["greevil_rematch"]
b = xd_post.greevil_battle(g, gr)
check(b["team"][1] == 277 and b["team"][0] == 9331, "Moltres snagged: Swellow stands in; Rhydon still a Shadow")
F.pop("snagged_shadow_lugia")
story.badges.setdefault("ORRE", []).append("CITADARK")   # (Greevil stands once Drake's Citadark Badge is won: S3 11-24)
t = route("XD_CITADARK_ISLE", "GATEON_PORT")
s = meet(t, "GRAND MASTER GREEVIL")
check(s is not None and F.get("snagged_shadow_lugia"), "XD001 got away? Greevil brings it back first - snagged")
s = meet(g.current_state, "GRAND MASTER GREEVIL")
check(F.get("snagged_shadow_rhydon") and F.get("snagged_shadow_zapdos"), "then his team: the Shadows you missed, snagged")
F["miror_b_missed"] = []
story.inventory["MIROR_RADAR"] = 1
F.pop("snagged_shadow_dragonite", None)
x = shadow_mon(9344, 70)
F.pop("snagged_shadow_articuno", None)
miror_radar.miss(g, x)
check(not miror_radar.missed(g), "a missed Greevil Shadow doesn't go to Miror B.")
F["snagged_shadow_articuno"] = True
F["snagged_shadow_dragonite"] = True

print("10) The Lucky Egg quest")
team_reset()
F["xd_beluh_mail"] = True
t = town("AGATE_VILLAGE", "ORRE_DESERT")
check(bool(meet(t, "Beluh")) and F.get("xd_le_asked"), "Beluh asks you to look into the silent Pokemon")
check(bool(meet(g.current_state, "Senilor")) and F.get("xd_le_senilor"), "Senilor: his Wobbuffet went silent after the translator")
check(bool(meet(g.current_state, "Old man")) and F.get("xd_le_oldman"), "the old man at the Center got them from Kaminko")
t = route("KAMINKO_HOUSE", "ORRE_DESERT")
check(bool(meet(t, "Dr. Kaminko")) and story.inventory.get("VOICE_CASE") == 1, "Kaminko: Voice Case 1")
t = town("AGATE_VILLAGE", "ORRE_DESERT")
check(bool(meet(t, "Combusken")) and F.get("xd_le_c1") and not story.inventory.get("VOICE_CASE"), "Combusken freed in the far-west house")
for n, who in ((2, "Poochyena"), (3, "Taillow")):
    t = route("KAMINKO_HOUSE", "ORRE_DESERT"); meet(t, "Dr. Kaminko")
    t = town("AGATE_VILLAGE", "ORRE_DESERT")
    check(bool(meet(t, who)) and F.get(f"xd_le_c{n}"), f"{who} freed")
t = route("KAMINKO_HOUSE", "ORRE_DESERT"); meet(t, "Dr. Kaminko")
t = town("AGATE_VILLAGE", "ORRE_DESERT")
s = meet(t, "Wobbuffet")
check(F.get("xd_le_c4") and any("didn't work" in x for x in (s or [])), "the Voice Case fails on Wobbuffet")
t = route("KAMINKO_HOUSE", "ORRE_DESERT")
s = meet(t, "Dr. Kaminko")
check(F.get("xd_le_vc5") and any("Megg" in x for x in (s or [])), "Kaminko bins it; Megg's e-mail about her Shroomish")
t = route("XD_ONBS", "PYRITE_TOWN")
check(bool(meet(t, "Shroomish")) and F.get("xd_le_c5"), "Shroomish freed at ONBS's front desk")
t = route("KAMINKO_HOUSE", "ORRE_DESERT")
check(bool(meet(t, "Dr. Kaminko")) and F.get("xd_le_kaminko_done"), "Kaminko: only its own trainer's voice will do")
t = town("AGATE_VILLAGE", "ORRE_DESERT")
s = meet(t, "Senilor")
check(F.get("xd_le_spoken") and any("WOBBUFFET!" in x for x in (s or [])), "Senilor speaks to Wobbuffet himself: it talks")
t = town("AGATE_VILLAGE", "ORRE_DESERT")
check(bool(meet(t, "Lotad")) and F.get("xd_le_lotad"), "the Lotad was only ever quiet")
check(bool(meet(g.current_state, "Beluh")) and story.inventory.get("LUCKY_EGG") == 1, "Beluh's Lucky Egg")

print("11) The Journal")
J = {j["id"]: j for j in g.loader.area_data.get("JOURNAL_MISSIONS", [])}
check(all(k in J for k in ("orre_s6", "orre_s6b", "orre_s6c", "orre_s6d")), "Eagun, the Colosseum, XD001's heart, silent Pokemon")
check(J["orre_s6c"]["completed_flag"] == "xd_lugia_purified", "XD001's task closes when Lugia is purified")

print(f"##### {len(fails)} failures")
for f in fails:
    print("  ", f)
