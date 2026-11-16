# Johto's content from SoulSilver (11-15, Jordan: "Each map should have its HG/SS content"): item balls lying where the game has
# them, hidden items found by stepping on them, the game's trainers on their tiles, HGSS morning / day / night wild tables.
# Built by kanto_handoff/johto_map_tools/jcontent.py + jwild.py; jcanon.py lists what is still missing. Glue after harness_head.py:
#   bash dev/checks/run.sh johto_canon
import json
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "red"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8")); _tm = _tm.get("maps", _tm)
_ad = json.load(open("assets/johto_area_data.json", encoding="utf-8")); _area = _ad["STORY_PROGRESSION"]
story.badges = {"JOHTO": ["ZEPHYR"]}
story.story_flags.update({"received_starter_johto": True, "visited_NEW_BARK_TOWN": True})
story.balls_left = max(getattr(story, "balls_left", 0), 5)

DONE = ["NEW_BARK_TOWN", "JOHTO_ROUTE_29", "CHERRYGROVE_CITY", "JOHTO_ROUTE_30", "JOHTO_ROUTE_31", "VIOLET_CITY", "SPROUT_TOWER", "DARK_CAVE",
        "JOHTO_ROUTE_32", "RUINS_OF_ALPH", "UNION_CAVE", "JOHTO_ROUTE_33", "AZALEA_TOWN", "SLOWPOKE_WELL", "ILEX_FOREST", "JOHTO_ROUTE_34",
        "GOLDENROD_CITY", "RADIO_TOWER", "JOHTO_ROUTE_35", "JOHTO_ROUTE_36"]


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def play(until, n=3000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def open_map(key, came):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 300)
    return g.current_state


# ---- the data: every item ball an option with a spot, every trainer spot a trainer of the area's, the HGSS time-of-day pools
for key in DONE:
    m = _tm[key]; a = _area[key]
    parts = m.get("floors") or [m]
    opts = {o["text"]: o for o in a.get("explore_options", []) + a.get("route_menu", [])}
    balls = [o for o in opts.values() if o.get("found")]
    on_map = [p if isinstance(p, str) else (p.get("text") if isinstance(p, dict) else None) for f in parts for p in (f.get("people") or [])]
    check(all(o["text"] in on_map for o in balls), f"{key}: its {len(balls)} item ball(s) lie on the map {[o['text'] for o in balls if o['text'] not in on_map]}")
    names = {t["name"] for t in a.get("trainer_pool", [])} | {t.get("spot_name") for t in a.get("trainer_pool", []) if t.get("spot_name")}
    spots = [n for f in parts for n in (f.get("trainer_spots") or [])]
    check(set(spots) <= names and all(sum(r.count("X") for r in f["art"]) == len(f.get("trainer_spots") or []) for f in parts),
          f"{key}: {len(spots)} trainers on the game's tiles, all of them the area's {sorted(set(spots) - names)}")
    if a.get("morning_pool_percentages"):   # (an area the games give wild Pokemon: HGSS's three times of day)
        pools = [a.get(f) for f in ("morning_pool_percentages", "day_pool_percentages", "night_pool_percentages")]
        check(all(p and sum(_ad.get(p, {}).values()) == 100 for p in pools), f"{key}: morning / day / night wild tables, each 100% {pools}")
hid = sum(len(f.get("hidden") or {}) for k in DONE for f in (_tm[k].get("floors") or [_tm[k]]))
check(hid >= 40, f"N1-N4: the game's hidden items are on the maps ({hid})")

# ---- as a player meets it: Route 30
r30 = open_map("JOHTO_ROUTE_30", "CHERRYGROVE_CITY")
fig = {m.payload.get("text"): (m.x, m.y) for m in r30.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
check(fig.get("POTION") == (10, 54) and fig.get("ANTIDOTE") == (20, 81), f"Route 30: the Potion and Antidote lie on SoulSilver's tiles ({fig.get('POTION')}, {fig.get('ANTIDOTE')})")
tr = {getattr(m, "payload", {}).get("name") if isinstance(getattr(m, "payload", None), dict) else None: (m.x, m.y) for m in r30.run.floor.movers if m.kind == "trainer"}
check(any(v == (9, 44) for v in tr.values()), f"Route 30: Youngster Joey's tile has a trainer ({tr})")
flag = next(o["event"]["flag"] for o in _area["JOHTO_ROUTE_30"]["route_menu"] if o["text"] == "POTION")
story.story_flags.pop(flag, None)
_had = story.inventory.get("POTION", 0)
r30.run.floor.movers = [m for m in r30.run.floor.movers if m.kind not in ("wild", "trainer")]
r30.run.player = (10, 55); r30.anim = 0
r30.step(0, -1)
play(lambda: not r30.dialogue_box.visible, 300)
check(story.inventory.get("POTION", 0) == _had + 1 and story.story_flags.get(flag), "...walk up to the Potion and you pick it up")
for k in [k for k in story.story_flags if k.startswith("hidden_JOHTO_ROUTE_30")]:
    story.story_flags.pop(k)
_had = story.inventory.get("POTION", 0)
r30.run.player = (11, 32); r30.anim = 0
r30.step(0, -1)
play(lambda: False, 40)
play(lambda: not r30.dialogue_box.visible, 200)
check(story.inventory.get("POTION", 0) == _had + 1, "...the hidden Potion in the flower bed by the sign is found by stepping on it")

# ---- the Apricorn tree (Jordan 11-15, simplified: with the Apricorn Box, one Apricorn a day)
r30 = open_map("JOHTO_ROUTE_30", "CHERRYGROVE_CITY")
fig = {m.payload.get("text"): (m.x, m.y) for m in r30.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
tree = next((t for n, t in fig.items() if n and n.startswith("GREEN APRICORN TREE")), None)
check(tree == (9, 67), f"Route 30: the Green Apricorn tree on SoulSilver's spot ({tree})")
story.inventory.pop("APRICORN_BOX", None); story.inventory.pop("GRN_APRICORN", None)
for k in [k for k in story.story_flags if k.startswith("apricorn_johto_route_30")]:
    story.story_flags.pop(k)
r30.run.floor.movers = [m for m in r30.run.floor.movers if m.kind not in ("wild", "trainer")]
def _pick():
    r30.run.player = (9, 68); r30.anim = 0
    r30.step(0, -1)
    play(lambda: not r30.dialogue_box.visible, 300)
_pick()
check(not story.inventory.get("GRN_APRICORN"), "...without the Apricorn Box there's nothing to carry one in")
story.inventory["APRICORN_BOX"] = 1
_pick()
check(story.inventory.get("GRN_APRICORN") == 1, f"...with the Box: a Green Apricorn ({story.inventory.get('GRN_APRICORN')})")
_pick()
check(story.inventory.get("GRN_APRICORN") == 1, "...and no more till tomorrow")

# ---- Kurt makes his balls on the spot (simplified), after his Fast Ball for the Well
from src.states.overworld import CityState as _CS
story.current_area_key = "AZALEA_TOWN"
az = _CS(g)
story.story_flags["slowpoke_well_cleared"] = True; story.story_flags.pop("got_fast_ball_kurt", None)
_fb = story.inventory.get("FAST_BALL", 0)
az.visit_kurt()
check(story.inventory.get("FAST_BALL", 0) == _fb + 1 and story.story_flags.get("got_fast_ball_kurt"), "Kurt: after the Well, his Fast Ball")
_fr = story.inventory.get("FRIEND_BALL", 0)
az.visit_kurt()
check(story.inventory.get("FRIEND_BALL", 0) == _fr + 1 and not story.inventory.get("GRN_APRICORN"), "...then a Green Apricorn into a Friend Ball, on the spot")

# ---- the phone (Jordan 11-15: built, HGSS's Pokegear)
from src.world import phone
story.current_area_key = "JOHTO_ROUTE_30"
joey_i, joey = next((i, t) for i, t in enumerate(_area["JOHTO_ROUTE_30"]["trainer_pool"]) if t["name"] == "Youngster Joey")
story.story_flags.pop("phone_contacts", None)
story.inventory.pop("POKEGEAR", None)
check(phone.register_after_win(g, "JOHTO_ROUTE_30", joey) == [], "Phone: no Pokegear, no numbers")
story.inventory["POKEGEAR"] = 1
lines = phone.register_after_win(g, "JOHTO_ROUTE_30", joey)
check(lines and "JOHTO_ROUTE_30|Youngster Joey" in phone.contacts(story), f"...with the Pokegear, Joey asks for your number ({lines[:1]})")
story.mark_trainer_defeated("JOHTO_ROUTE_30", joey_i)
story.badges["JOHTO"] = ["ZEPHYR"]
check(phone.ring(g, "VIOLET_CITY") == [] and phone.rematch_info(g, "JOHTO_ROUTE_30", joey_i, joey) is joey, "...with one Badge his next team isn't ready: no call, his old team")
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL"]
call = phone.ring(g, "VIOLET_CITY")
re = phone.rematch_info(g, "JOHTO_ROUTE_30", joey_i, joey)
check(call and "Joey" in " ".join(call) and re.get("team") == [20] and re.get("levels") == [34],
      f"...later his Raticate (lv 34, SoulSilver's rematch) is ready: he calls, and you meet that team ({re.get('team')}, {re.get('levels')})")
check(phone.ring(g, "VIOLET_CITY") == [], "...one call a team")

# ---- givers in the data
li = next(t for t in _area["SPROUT_TOWER"]["trainer_pool"] if t["name"] == "Elder Li")
check(li["rewards"].get("HM_FLASH") and li["team"] == [69, 69, 163], "Elder Li: SoulSilver's team, and Flash for beating him (the Zephyr Badge lets you use it)")
from src.world.hms import hm_for_badge
check(hm_for_badge("JOHTO", "ZEPHYR") is None and hm_for_badge("JOHTO", "HIVE") is None, "...Flash and Cut come from the story now (Elder Li, the charcoal maker), not the badges")
kyle = [o for o in _area["VIOLET_CITY"]["explore_options"] if o.get("text") == "Kyle"]
check(any((o.get("event") or {}).get("trade") == {"want": 69, "give": 95, "item": "PERSIM_BERRY"} for o in kyle), "Violet: Kyle trades his Onix for a Bellsprout")

# ---- Johto starts as HGSS does (Jordan 11-15: "ensure the johto region starts the same as the games, with the same scenes")
from src.states.menus import StarterSelectionState as _SSS, region_opening_state
said = []


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def play2(until, n=3000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            _note(st); st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif not isinstance(st, _WTS) and getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def walk(st, path):
    for c in path:
        d = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}[c]
        play2(lambda: not g.current_state._busy() and g.current_state.anim == 0, 400)
        g.current_state.step(*d)
        play2(lambda: isinstance(g.current_state, _WTS) and g.current_state.anim == 0, 60)


for f in [k for k in list(story.story_flags) if k.startswith("johto_") or k in ("received_starter_johto", "met_mr_pokemon", "received_pokedex_johto", "got_map_card_johto")]:
    story.story_flags.pop(f, None)
story.player_team = []
story.inventory.pop("POKEGEAR", None); story.inventory.pop("MAP_CARD", None)
story.starting_region = "JOHTO"
story.badges["JOHTO"] = []
story.current_area_key = "NEW_BARK_TOWN"
g.change_state(region_opening_state(g, "JOHTO"))
play2(lambda: isinstance(g.current_state, _WTS), 600)
t = g.current_state
check(isinstance(t, _WTS) and t.area_key == "NEW_BARK_TOWN" and t.room == "home_2" and tuple(t.player) == (5, 7),
      f"a new Johto game: you wake up in your room upstairs ({getattr(t, 'room', None)}, {getattr(t, 'player', None)})")
said.clear()
t.player = (3, 6); t.anim = 0
walk(t, "u")
play2(lambda: story.story_flags.get("johto_mom_morning") and not g.current_state._busy(), 1500)
t = g.current_state
check(t.room == "home" and any("Professor Elm came by" in x for x in said), f"downstairs, Mom says Lyra was round and Elm wants you ({said[-1:]})")
_door = next(xy for xy, v in t.exits.items() if str(v).startswith("OUT:"))
t.player = (_door[0], _door[1] - 1); t.anim = 0
said.clear()
walk(t, "d")
play2(lambda: story.story_flags.get("johto_lyra_morning") and not g.current_state._busy(), 3000)
t = g.current_state
check(t.room is None and any("Marill! There you are" in x for x in said), f"outside, Marill runs up, then Lyra ({said[:2]})")
check(any(isinstance(o, dict) and o.get("text") == "Red-haired boy" for o in t._people().values()), "...and a red-haired boy peers in at the Lab window")
said.clear()
t._enter(next(xy for xy, k in t.doors.items() if k == "lab"))
play2(lambda: isinstance(g.current_state, _SSS), 4000)
st = g.current_state
check(isinstance(st, _SSS) and st.region == "JOHTO" and any("Mr. Pokemon" in x for x in said), f"in the Lab Elm asks the favour and you pick your Pokemon ({type(st).__name__}, room {getattr(st, 'room', None)}, flags {story.story_flags.get('johto_lab_intro')}, said {said[:3]}, npc {getattr(st, 'current_npc', None)})")
if isinstance(st, _SSS):
    st.load_starters(); st.selected_idx = 1; st.complete_selection()
    st.dialogue_box.callback()
play2(lambda: isinstance(g.current_state, _WTS), 1500)
t = g.current_state
check(story.story_flags.get("received_starter_johto") and getattr(t, "room", None) == "lab", f"...your Pokemon is yours, and you're back in the Lab ({getattr(t, 'room', None)})")
if getattr(t, "room", None):
    t._leave("OUT:12,9")
play2(lambda: not g.current_state._busy(), 300)
t = g.current_state
said.clear()
t.player = (12, 10); t.anim = 0
play2(lambda: story.story_flags.get("johto_lyra_after") and not g.current_state._busy(), 3000)
check(any("show your mom" in x for x in said), f"Lyra waits outside: show your mom ({said[:1]})")
story.current_area_key = "NEW_BARK_TOWN"
t.visit_mom()
play2(lambda: not g.current_state.npc_active, 400)
check(story.inventory.get("POKEGEAR") == 1, "Mom gives you the Pokegear")
# Route 29: Lyra's catching lesson
_b = story.balls_left
r29 = open_map("JOHTO_ROUTE_29", "NEW_BARK_TOWN")
said.clear()
play2(lambda: story.story_flags.get("johto_lyra_lesson") and not g.current_state.dialogue_box.visible, 4000)
check(story.story_flags.get("johto_lyra_lesson") and story.balls_left == _b + 5, f"Route 29: Lyra catches you up, shows you how to catch, and gives you 5 Poke Balls ({story.balls_left - _b})")
# Cherrygrove: the Guide Gent's tour and the Map Card
said.clear()
story.current_area_key, story.last_area_key = "CHERRYGROVE_CITY", "JOHTO_ROUTE_29"
g.walk_town_pos = None; g.walk_town_room = None
cg = _CS(g); g.change_state(cg)
play2(lambda: story.story_flags.get("got_map_card_johto") and not g.current_state._busy() and not g.current_state.npc_active, 6000)
check(any("This is the Pokemon Center" in x for x in said) and story.inventory.get("MAP_CARD"), f"Cherrygrove: the Guide Gent's tour, then the Map Card ({len(said)} lines)")
# Mr. Pokemon: the Egg, and Oak's Pokedex; then Elm's call
story.story_flags["met_mr_pokemon"] = True
call = phone.ring(g, "JOHTO_ROUTE_30")
check(call and "terrible" in " ".join(call), f"leaving Mr. Pokemon's, Elm calls in a panic ({call[1:2]})")
lab_sc = [sc for sc in _tm["NEW_BARK_TOWN"]["rooms"]["lab"].get("scenes", []) if sc.get("flag") == "johto_police_scene"]
check(lab_sc and "{rival_name}" in " ".join(lab_sc[0]["cast"][0]["lines"]), "back at the Lab, the officer asks the thief's name")
sp = [sc for f in _tm["SPROUT_TOWER"]["floors"] for sc in f.get("scenes", []) if sc.get("flag") == "johto_silver_sprout"]
check(sp, "Sprout Tower: Silver has just beaten the Elder when you arrive")

# ---- Primo's Eggs, the Togepi Egg, the Farfetch'd, the GS Ball
from src.states.overworld.common import _run_story_event
story.story_flags.pop("primo_eggs", None)
_team = len(story.player_team)
_run_story_event(r29, {"lines": ["Primo: Correct!"], "gift_egg": 179, "primo_next": True}, lambda c: True, lambda ls: None)
check(story.story_flags.get("primo_eggs") == 1 and len(story.player_team) == _team + 1 and story.player_team[-1].id == 179, "Primo: a right answer, his first Egg (Mareep)")
story.player_team = story.player_team[:_team]
aide = [o for o in _area["VIOLET_CITY"]["explore_options"] if o.get("text") == "Elm's aide"]
check(aide and aide[0]["event"].get("gift_egg") == 175 and aide[0]["condition"] == "has_badge:ZEPHYR", "Violet's Center: after the Zephyr Badge, Elm's aide brings the Egg (Togepi)")
maker = [p for p in _tm["ILEX_FOREST"].get("people", []) if isinstance(p, dict) and p.get("text") == "Charcoal maker"]
check(maker and {"ilex_farfetchd_1", "ilex_farfetchd_2"} <= set(maker[0]["event"].get("requires", [])), "Ilex: find both Farfetch'd, then the charcoal maker gives Cut")
story.current_area_key = "AZALEA_TOWN"
az = _CS(g)
story.inventory["GS_BALL"] = 1
for k in ("kurt_has_gs_ball", "kurt_examined_gs_ball", "kurt_gs_ball_day"):
    story.story_flags.pop(k, None)
az.visit_kurt()
check(story.story_flags.get("kurt_has_gs_ball") and not story.inventory.get("GS_BALL"), "Kurt keeps the GS Ball to study it")
story.story_flags["kurt_gs_ball_day"] = "2000-01-01"
az.visit_kurt()
check(story.story_flags.get("kurt_examined_gs_ball") and story.inventory.get("GS_BALL") == 1, "...the next day he gives it back: take it to Ilex's shrine")
cel = [o for o in _area["ILEX_FOREST"]["route_menu"] if o.get("action") == "BOSS"]
check(cel and "kurt_examined_gs_ball" in cel[0]["condition"], "Celebi waits at the shrine for the GS Ball Kurt studied")
gs = [o for o in _area["GOLDENROD_CITY"]["explore_options"] if (o.get("event") or {}).get("gift_item", {}).get("GS_BALL")]
check(gs and gs[0]["flag_condition"] == "beat_johto_champion", "Goldenrod's Center hands you the GS Ball once you're Champion (Crystal)")


# ---- N5: Goldenrod, Routes 35 and 36
gr = _area["GOLDENROD_CITY"]
kenya = [o for o in gr["explore_options"] if o.get("text") == "Gate guard"]
check(any((o.get("event") or {}).get("gift_pokemon") == 21 for o in kenya) and any("kenya_delivered" in (o.get("event") or {}).get("requires", []) for o in kenya),
      "Goldenrod's gate: the guard lends you Kenya (Spearow), and thanks you with an HP Up once the letter's delivered")
r31man = [p for p in _tm["JOHTO_ROUTE_31"].get("people", []) if isinstance(p, dict) and p.get("text") == "Sleepy man"]
check(r31man and r31man[0]["event"].get("requires") == ["got_kenya"] and r31man[0]["event"]["gift_item"].get("TM21"), "...the man on Route 31 reads it and gives you Rest")
rs = [p for p in _tm["JOHTO_ROUTE_36"].get("people", []) if isinstance(p, dict) and p.get("text") == "Rock Smash man"]
check(rs and rs[0]["event"]["gift_item"].get("HM_ROCK_SMASH") and rs[0]["event"]["requires"] == ["defeated_sudowoodo"], "Route 36: Rock Smash from the man by the odd tree, once it's gone")
dept5 = _tm["GOLDENROD_CITY"]["rooms"]["dept_5"].get("people", [])
check(any("Trader" in str(p) for p in dept5) and any("TM lady" in str(p) for p in dept5), "Dept. Store 5F: the Machop trader and the Sunday TM lady")
stock = {e["item"] for e in gr.get("extra_stock", [])}
check({"TM05", "TM03", "TM04", "TM110", "TM111", "TM08", "TM132"} <= stock, f"...and the 5F TM Corner's TMs on the shelf ({sorted(stock)})")

# ---- the Radio Card quiz, the radio, Buena, the Daily Drawing (Jordan 11-15)
from src.states.systems.yes_no_quiz import YesNoQuizState, make_question
from src.world import radio
import random as _r
q, tr = make_question(_r.Random(3), 2)
check(" = " in q and isinstance(tr, bool), f"the quiz asks yes/no equations ({q})")
story.inventory.pop("RADIO_CARD", None)
story.story_flags.pop("radio_takeover_started", None); story.story_flags.pop("radio_tower_cleared", None)
story.badges["JOHTO"] = ["ZEPHYR", "HIVE"]
rt = open_map("RADIO_TOWER", "GOLDENROD_CITY")
figs = {m.payload.get("text"): (m.x, m.y) for m in rt.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
trs = [m for m in rt.run.floor.movers if m.kind == "trainer"]
check("Quiz lady" in figs and not trs, f"Radio Tower 1F, before the takeover: visitors, the quiz lady behind her desk, no Rockets ({sorted(figs)})")
rt.run.floor.movers = [m for m in rt.run.floor.movers if m.kind != "wild"]
qx, qy = figs.get("Quiz lady", (13, 9))
rt.run.player = (qx, qy - 2); rt.anim = 0   # (her desk is the counter above her)
rt.step(0, 1)
play(lambda: isinstance(g.current_state, YesNoQuizState) or not rt.dialogue_box.visible, 400)
qs = g.current_state
check(isinstance(qs, YesNoQuizState), f"...talk to her across the desk and the quiz starts ({type(qs).__name__})")
if isinstance(qs, YesNoQuizState):
    for _ in range(5):
        qs.answer(qs.truth)
play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 300)
check(story.inventory.get("RADIO_CARD") == 1, "...five right in a row: the Radio Card")
story.inventory["POKEGEAR"] = 1
chs = [k for k, n in radio.channels(g)]
check({"talk", "music", "buena", "variety"} <= set(chs) and "unown" not in chs, f"the radio's channels ({chs})")
radio.tune(g, "music")
check(story.story_flags.get("radio_station") in ("march", "lullaby") and radio.encounter_effect(story) in ("more", "fewer"), "Pokemon Music: the March or the Lullaby, by the day")
story.story_flags["radio_station"] = "hoenn"
check(radio.sound_species(story, _area["JOHTO_ROUTE_30"]) == [293, 264], "Hoenn Sound on Route 30: Whismur and Linoone, SoulSilver's own")
story.story_flags.pop("radio_station", None)
lines = radio.tune(g, "buena")
pw = radio.password_today()
check(pw in " ".join(lines), f"Buena's Password gives today's password ({pw})")
_run_story_event(rt, {"lines": [], "buena": True}, lambda c: True, lambda ls: None)
check(story.story_flags.get("buena_points") and story.inventory.get("ULTRA_BALL", 0) >= 1 or story.story_flags.get("buena_points", 0) >= 1, "...tell Buena: a Blue Card point (and a prize)")
story.money = 1000
_run_story_event(rt, {"lines": [], "raffle": True}, lambda c: True, lambda ls: None)
check(story.money == 700 and story.story_flags.get("goldenrod_raffle_day"), "Dept. Store 6F: the Daily Drawing, $300 once a day")
bars = _tm["RADIO_TOWER"]["floors"][1].get("barred", [])
check(bars and bars[0]["tiles"] == [[3, 2]], "Radio Tower 2F: the officer keeps visitors off the stairs till the takeover")
# ---- the Goldenrod Tunnel (Jordan 11-15: option B, simplified): the elevator to B1F, the crates, the warehouse, the keys
from src.states.systems.pick_list import PickListState
_gu = _tm["GOLDENROD_UNDERGROUND"]
check(len(_gu["floors"]) == 5, f"Goldenrod Tunnel: SoulSilver's five maps (Tunnel, booths, warehouse, back room, B1F) ({len(_gu['floors'])})")
_who = {str(p.get("text")) for f in _gu["floors"] for p in f.get("people", []) if isinstance(p, dict)}
check({"Herb shop", "Bargain shop", "Photographer", "Director", "Elevator attendant"} <= _who
      and any(w.startswith("Salon") for w in _who), f"...the herb shop, the salon brothers, the Monday bargain shop, the photo studio, the Director")
_lifts = [o for o in gr["explore_options"] if o.get("text") == "Elevator"]
check(_lifts and _lifts[0].get("door") == "dept", "Dept. Store: an elevator attendant on the floors")
_ev = dict((_lifts[0] if _lifts else {}).get("event") or {})
for k in ("b1f_crate_1", "b1f_crate_2", "b1f_crate_3", "warehouse_switch_1", "warehouse_switch_2", "warehouse_switch_3"):
    story.story_flags.pop(k, None)
_run_story_event(g.current_state, _ev, lambda c: True, lambda ls: None)
pk = g.current_state
check(isinstance(pk, PickListState) and len(pk.rows) == 7, f"...ask for a floor: B1F to 6F ({type(pk).__name__})")
if isinstance(pk, PickListState):
    pk.pick("B1F")
play(lambda: getattr(g.current_state, "run", None) is not None and story.current_area_key == "GOLDENROD_UNDERGROUND", 600)
b1 = g.current_state
g.arrive_floor = None
check(getattr(getattr(b1, "run", None), "index", None) == 4, f"...B1F: the elevator brings you down to the store's basement ({story.current_area_key}, {getattr(getattr(b1, 'run', None), 'index', None)})")
if getattr(b1, "run", None) is not None and b1.run.index == 4:
    frames(120)
    check(not [m for m in b1.run.floor.movers if m.kind == "wild"] and not _area["GOLDENROD_UNDERGROUND"].get("wild_pool_percentages"),
          "...no wild Pokemon down here, as in HGSS (Jordan 11-15)")
    b1.run.player = (3, 8); b1.anim = 0
    b1.step(-1, 0)
    play(lambda: not b1.dialogue_box.visible, 300)
    check(b1.run.player == (3, 8), f"...a crate blocks the side room by the wall ({b1.run.player})")
    b1.run.player = (5, 14); b1.anim = 0      # (the Black Belt by the wall stands below, at (5, 15))
    b1.step(0, 1)
    play(lambda: not b1.dialogue_box.visible, 400)
    check(story.story_flags.get("b1f_crate_1"), "...talk to the Black Belt: his Machoke shifts it")
    b1.run.player = (3, 8); b1.anim = 0
    b1.step(-1, 0)
    play(lambda: not b1.dialogue_box.visible, 300)
    check(b1.run.player == (2, 8), f"...and the way to its item is open ({b1.run.player})")
story.story_flags["warehouse_switch_2"] = True
_wh = _gu["floors"][2].get("barred", [])
check(len(_wh) == 3 and all((b.get("until") or {}).get("condition", "").startswith("warehouse_switch_") for b in _wh),
      "the warehouse: three shutters, each opened by its own switch")
check(any((p.get("event") or {}).get("gift_item", {}).get("CARD_KEY") for p in _gu["floors"][3].get("people", []) if isinstance(p, dict)),
      "...the Director, held in the back room, gives the Card Key")
_rt2 = _tm["RADIO_TOWER"]["floors"][2].get("barred", [])
check(any("CARD_KEY" in str(b.get("until")) for b in _rt2), "Radio Tower 3F: the door that needs the Card Key")
import json as _js
check('"Executive Petrel"' in _js.dumps(_area["RADIO_TOWER"]) and '"BASEMENT_KEY": 1' in _js.dumps(_area["RADIO_TOWER"]), "...Petrel, the fake Director, drops the Basement Key for the Tunnel's locked door")
check(any("BASEMENT_KEY" in str(b.get("until")) for b in _gu["floors"][0].get("barred", [])), "...which opens the Tunnel's NO ENTRY door")
# ---- N6: the National Park, Route 37, Ecruteak
from src.pokemon import items as _it
def _ppl(key, room=None):
    m = _tm[key]["rooms"][room] if room else _tm[key]
    out = []
    for p in m.get("people", []):
        if isinstance(p, dict):
            out += p.get("any") or [p]
    return out
_np = {p.get("text"): p for p in _ppl("NATIONAL_PARK")}
check("Teacher" in _np and (_np["Teacher"].get("event") or {}).get("gift_item", {}).get("QUICK_CLAW") and "Persian" in _np,
      "National Park: the teacher with her Persian gives a Quick Claw")
_gate = [p for p in _area["JOHTO_ROUTE_35"]["route_menu"] if p.get("door") == "gate" and p.get("action") == "BUG_CONTEST"]
check(_gate, "...the contest helper in the Route 35 gate signs you up for the Bug-Catching Contest")
check("ss_ground/D22R0101" in __import__("json").dumps(_tm["BUG_CONTEST"]),
      "...the contest runs in the park itself (SoulSilver's picture of it)")
_r37 = {p.get("text"): p for p in _ppl("JOHTO_ROUTE_37")}
check(_r37.get("Sunny", {}).get("condition") == "weekday:sun" and (_r37["Sunny"].get("event") or {}).get("gift_item", {}).get("MAGNET"),
      "Route 37: Sunny, on Sundays, gives a Magnet")
check(sum("APRICORN TREE" in t for t in _r37) == 3, "...and its three Apricorn trees (Red, Blue, Black)")
_dw = [o for o in _area["ECRUTEAK_CITY"]["explore_options"] if o.get("door") == "dowsing" and (o.get("event") or {}).get("gift_item", {}).get("ITEMFINDER")]
check(_dw and "dowsing" in _tm["ECRUTEAK_CITY"].get("rooms", {}) and "skyhouse" in _tm["ECRUTEAK_CITY"].get("rooms", {}),
      "Ecruteak: the house east of the Gym (the Dowsing Machine) and the old man's house are open")
class _P: pass
_a, _b = _P(), _P(); _a.friendship = _b.friendship = 70; _a.held_item = "SOOTHE_BELL"; _b.held_item = None
_it.friend_gain(_a, 2); _it.friend_gain(_b, 2)
check(_a.friendship > _b.friendship, f"the Soothe Bell: its holder grows friendly faster ({_a.friendship} vs {_b.friendship})")
check(_it.HELD_BOOSTS.get("MAGNET") == "ELECTRIC", "the Magnet powers up Electric-type moves")
# ---- Ecruteak Gym (Jordan 11-15: "As HGSS (dark, falls)"): dark, a light round you; step off the path and you fall back to the entrance
eg = open_map("ECRUTEAK_CITY", "JOHTO_ROUTE_37")
_gd = next((d for d, k in getattr(eg, "doors", {}).items() if k == "gym"), None)
if _gd:
    eg._enter(_gd); frames(5)
check(getattr(eg, "room", None) == "gym" and eg.light_radius() == 2, f"Ecruteak Gym: dark, lit only round you ({getattr(eg, 'room', None)})")
if getattr(eg, "room", None) == "gym":
    eg.player = (15, 50); eg.anim = 0
    eg.step(0, -1)
    frames(20)
    check(tuple(eg.player) == (15, 49), f"...the path carries you ({eg.player})")
    eg.anim = 0
    eg.step(-1, 0)
    frames(5)
    check(tuple(eg.player) == (16, 55), f"...step off it into the dark and you fall, back by the entrance ({eg.player})")
g.walk_town_room = g.walk_town_pos = None
# ---- N7: the Burned Tower, the Dance Theater, the Bell Tower (HGSS)
from src.world import hms as _hms
_kg = [t for t in _area["ECRUTEAK_DANCE_THEATER"]["trainer_pool"] if t["name"].startswith("Kimono Girl")]
_had = list(story.badges.get("JOHTO", []))
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG"]
_early = [story.trainer_on_map("ECRUTEAK_DANCE_THEATER", i, t) for i, t in enumerate(_kg)]
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM", "MINERAL", "GLACIER", "RISING"]
_late = [story.trainer_on_map("ECRUTEAK_DANCE_THEATER", i, t) for i, t in enumerate(_kg)]
story.badges["JOHTO"] = _had
check(len(_kg) == 5 and not any(_early) and all(_late), f"Dance Theater: the five Kimono Girls battle only after the Rising Badge ({_early} / {_late})")
_thm = _tm["ECRUTEAK_DANCE_THEATER"]
_th = {p.get("text"): p for p in ((_thm.get("floors") or [_thm])[0].get("people") or []) if isinstance(p, dict)}
_g = _th.get("Rocket Grunt", {}).get("event", {})
check(_g.get("battle", {}).get("team") == [109] and _g.get("flag") == "beat_theater_grunt", "...a Rocket Grunt pesters a Kimono Girl (Koffing): beat him")
_gm = _th.get("Gentleman", {}).get("event", {})
check(_gm.get("gift_item", {}).get("HM_SURF") and _gm.get("requires") == ["beat_theater_grunt"], "...and the gentleman gives you Surf")
check(_hms.HM_BY_BADGE["JOHTO"].get("FOG") is None and _hms.USE_BADGE["JOHTO"].get("HM_SURF") == "FOG", "...usable with the Fog Badge (it no longer comes with the badge)")
_bt = _tm["BURNED_TOWER"]["floors"][1]
check(any(sc.get("flag") == "johto_beasts_fled" for sc in _bt.get("scenes", [])) and {"Raikou", "Entei", "Suicune"} <= {p.get("text") for p in _bt.get("people", []) if isinstance(p, dict)},
      "Burned Tower B1F: Raikou, Entei and Suicune wake and flee as you come near")
_eb = [b for b in _tm["ECRUTEAK_CITY"].get("barred", []) if b.get("tiles") == [[24, 56]]]
check(_eb and _eb[0]["until"]["condition"] == "johto_beasts_fled", "Ecruteak Gym: shut till you've seen the Burned Tower's Pokemon (Morty went there)")
# ---- N8: Routes 38 and 39, Olivine (HGSS)
_r39 = _area["JOHTO_ROUTE_39"]["route_menu"]
_moo = next((o for o in _r39 if o.get("door") == "barn" and (o.get("event") or {}).get("feed")), None)
check(_moo and "barn" in _tm["JOHTO_ROUTE_39"].get("rooms", {}) and "farmhouse" in _tm["JOHTO_ROUTE_39"]["rooms"],
      "Moomoo Farm: the barn and the farmhouse, SoulSilver's own rooms off Route 39")
if _moo:
    for _k in ("moomoo_healed", "moomoo_berries"):
        story.story_flags.pop(_k, None)
    story.inventory["ORAN_BERRY"] = 7
    _st = g.current_state
    for _ in range(6):
        _run_story_event(_st, _moo["event"], lambda c: True, lambda ls: None)
    _mid = not story.story_flags.get("moomoo_healed") and story.story_flags.get("moomoo_berries") == 6
    _run_story_event(_st, _moo["event"], lambda c: True, lambda ls: None)
    check(_mid and story.story_flags.get("moomoo_healed") and not story.inventory.get("ORAN_BERRY"),
          "...the sick Miltank eats seven Oran Berries, one at a time, and gets well")
_wife = next((o for o in _r39 if o.get("text") == "Farmer's wife"), {})
check((_wife.get("event") or {}).get("gift_item", {}).get("TM136") and _wife["event"].get("requires") == ["moomoo_healed"],
      "...the farmer's wife then gives TM Natural Gift, and the farm sells Moomoo Milk")
_ol = _area["OLIVINE_CITY"]["explore_options"]
_gift = lambda door, item: any(o.get("door") == door and (o.get("event") or {}).get("gift_item", {}).get(item) for o in _ol)
check(_gift("guru", "GOOD_ROD") and not _gift("cafe", "HM_STRENGTH"), "Olivine: the Fishing Guru's Good Rod (Strength isn't the cafe's in HGSS)")
check(_hms.HM_BY_BADGE["JOHTO"].get("PLAIN") is None and _hms.USE_BADGE["JOHTO"].get("HM_STRENGTH") == "PLAIN", "...Strength usable with the Plain Badge (no longer given by it)")
check(any((o.get("event") or {}).get("trade", {}).get("want") == 98 for o in _ol), "...the Krabby-for-Voltorb trade (Billy holds a Cheri Berry)")
# ---- N9: Cianwood, Routes 40 and 41 (HGSS)
_cw = {p.get("text"): p for p in _ppl("CIANWOOD_CITY")}
_wife = (_cw.get("Chuck's wife") or {}).get("event") or {}
check(_wife.get("gift_item", {}).get("HM_FLY") and _wife.get("requires") == ["has_storm_badge"], "Cianwood: Chuck's wife gives Fly once you have the Storm Badge")
check(_hms.HM_BY_BADGE["JOHTO"].get("STORM") is None and _hms.USE_BADGE["JOHTO"].get("HM_FLY") == "STORM", "...usable with the Storm Badge (no longer given by it)")
_ck = next((o for o in _area["CIANWOOD_CITY"]["explore_options"] if o.get("door") == "kirk"), {}).get("event") or {}
check(_ck.get("gift_pokemon") == 213 and _ck.get("gift_held") == "BERRY_JUICE", "...Kirk asks you to look after Shuckie, his Shuckle, holding Berry Juice")
_had_team = list(story.player_team)
from src.world import story_events as _se
_msg = _se.gift_pokemon(g, 213, 15, "BERRY_JUICE")
_sh = next((p for p in list(story.player_team) + [q for q in story.pc_pokemon if q] if getattr(p, "id", None) == 213), None)
check(_sh is not None and getattr(_sh, "held_item", None) == "BERRY_JUICE", "...and Shuckie arrives holding it")
story.player_team = _had_team
check(any(sc.get("flag") == "johto_suicune_cianwood" for sc in _tm["CIANWOOD_CITY"].get("scenes", [])), "...Suicune by the north rocks, then gone across the sea")
_r40 = {p.get("text"): p for p in _ppl("JOHTO_ROUTE_40")}
check(_r40.get("Monica", {}).get("condition") == "weekday:mon" and (_r40["Monica"].get("event") or {}).get("gift_item", {}).get("SHARP_BEAK"),
      "Route 40: Monica, on Mondays, gives a Sharp Beak")
check("Swimmer Kirk" in _tm["JOHTO_ROUTE_41"].get("trainer_spots", []) and len(_tm["JOHTO_ROUTE_41"]["trainer_spots"]) == 11,
      "Route 41: SoulSilver's swimmers, and our own Swimmer Kirk still out on the water")
# ---- Lugia waits for the Tidal Bell (Jordan 11-15: as SoulSilver), Kimono Girl Miki's prize
_lg = next((o for o in _area["WHIRL_ISLANDS"]["route_menu"] if o.get("text") == "CHALLENGE LUGIA"), {})
check({"has_tidal_bell", "has_silver_wing"} <= set(_lg.get("condition") or []), "Whirl Islands: Lugia appears to the holder of the Silver Wing and the Tidal Bell (SoulSilver)")
_ho = next((o for o in _area["BELL_TOWER"]["route_menu"] if o.get("text") == "CHALLENGE HO-OH"), {})
check("has_rainbow_wing" in (_ho.get("condition") or []), "Bell Tower: Ho-Oh, for the holder of the Rainbow Wing")
check(_area["BELL_TOWER"]["area_boss"]["level"] == 60 and _area["WHIRL_ISLANDS"]["area_boss"]["level"] == 60, "...both legends at level 60, as in Crystal")
_inv = story.inventory; _rw = _inv.pop("RAINBOW_WING", None)
from src.states.overworld.route_actions import RouteActions as _RA
class _SL: pass
_sl = _SL(); _sl.game = g; _sl.is_progression_paused = False
for _n in ("hide_menu_buttons", "show_dialogue", "_end_npc_interaction_playstate"):
    setattr(_sl, _n, lambda *a, **k: None)
try:
    _RA.visit_sage_li(_sl)
except Exception as _e:
    print("sage li:", repr(_e)[:80])
check(_inv.get("RAINBOW_WING") == 1, "...Sage Li gives the Rainbow Wing without the three beasts caught")
if _rw is None:
    _inv.pop("RAINBOW_WING", None)
else:
    _inv["RAINBOW_WING"] = _rw
check(any((t.get("rewards") or {}).get("TIDAL_BELL") for t in _area["ECRUTEAK_DANCE_THEATER"]["trainer_pool"]), "...which Kimono Girl Miki gives after the dance")
# ---- N10: Route 42, Mahogany, Mt. Mortar (HGSS)
_r42 = {p.get("text"): p for p in _ppl("JOHTO_ROUTE_42")}
check(((_r42.get("Hiker") or {}).get("event") or {}).get("gift_item", {}).get("HM_STRENGTH")
      and any(sc.get("flag") == "johto_strength_hiker" for sc in _tm["JOHTO_ROUTE_42"].get("scenes", [])),
      "Route 42: a Hiker comes charging out of Mt. Mortar and gives you Strength")
check(sum("APRICORN TREE" in t for t in _r42) == 3, "...and the three Apricorn trees (Pink, Green, Yellow)")
_ky = next((t for t in _area["MT_MORTAR"]["trainer_pool"] if t["name"] == "Karate King Kiyo"), {})
check((_ky.get("rewards") or {}).get("POKEMON_236") and "TYROGUE" not in (_ky.get("rewards") or {}), "Mt. Mortar: Karate King Kiyo gives a Tyrogue (the Pokemon, not a bag item)")
check("radiohouse" in _tm["MAHOGANY_TOWN"].get("rooms", {}), "Mahogany: the house by the Center is open")
# ---- the Bug-Catching Contest (Jordan 11-15): check in across the gate's desk; contestants walk the park, their Pokemon at their heels
_g35 = _tm["JOHTO_ROUTE_35"]["rooms"]["gate"]
check(_g35["art"][8][20] == "N" and _g35["art"][9][20] == "m", "Route 35's park gate: the contest helper behind SoulSilver's desk, checked in across its counter")
_bc = open_map("BUG_CONTEST", "JOHTO_ROUTE_35")
_figs = {m.payload.get("text"): m for m in getattr(getattr(_bc, "run", None), "floor", None).movers if m.kind == "figure" and isinstance(m.payload, dict)} if getattr(_bc, "run", None) else {}
check({"Bug Catcher Don", "Bug Catcher Ed", "Cooltrainer Nick", "Pokefan Beverly", "Youngster Samuel"} <= set(_figs) and "Venonat" in _figs,
      f"the contest: the other contestants out in the park, each with a Pokemon ({sorted(_figs)[:6]})")
if "Bug Catcher Don" in _figs and "Venonat" in _figs:
    _ld, _fo = _bc._motion(_figs["Bug Catcher Don"]), _bc._motion(_figs["Venonat"])
    _was = tuple(_ld.pos)
    _to = next(((_was[0] + dx, _was[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, -1)) if _bc._npc_free((_was[0] + dx, _was[1] + dy), _figs["Bug Catcher Don"])), None)
    if _to:
        _ld.timer = 999; _ld.path = [_to]
        frames(40)
    _lp, _lf = tuple(_ld.pos), tuple(_ld.facing)
    _bad = {(_lp[0] + _lf[0], _lp[1] + _lf[1]), (_lp[0], _lp[1] + 1), _lp}
    check(_to and abs(_fo.pos[0] - _lp[0]) + abs(_fo.pos[1] - _lp[1]) == 1 and tuple(_fo.pos) not in _bad,
          f"...a contestant's Pokemon follows, then rests at their side - never in front ({_was} -> {_to}; Venonat at {_fo.pos}, Don at {_lp} facing {_lf})")
# ---- N11: Lake of Rage, Route 43 (HGSS)
_lr = {p.get("text"): p for p in _ppl("LAKE_OF_RAGE")}
check(_lr.get("Wesley", {}).get("condition") == "weekday:wed" and (_lr["Wesley"].get("event") or {}).get("gift_item", {}).get("BLACK_BELT"),
      "Lake of Rage: Wesley, on Wednesdays, gives a Black Belt")
check({"hiddenpower", "magikarphouse"} <= set(_tm["LAKE_OF_RAGE"].get("rooms", {})), "...the hermit's house (Hidden Power) and the Fishing Guru's are open")
_r43 = {p.get("text"): p for p in _ppl("JOHTO_ROUTE_43")}
_toll = (_r43.get("Rocket Grunt") or {}).get("event") or {}
check(_toll.get("pay") == 1000 and _toll.get("flag") == "paid_route43_toll", "Route 43: Team Rocket's toll at the gate ($1000)")
_gd = (_r43.get("Gate guard") or {})
check(_gd.get("condition") == "rocket_hq_cleared" and (_gd.get("event") or {}).get("gift_item"), "...and the guard's TM Sludge Bomb once the Hideout is cleared")
check(_it.HELD_BOOSTS.get("BLACK_BELT") == "FIGHTING", "the Black Belt powers up Fighting-type moves")
# ---- the Rocket Hideout (Jordan 11-15: the whole hideout; Lance with Dragonite; single battles only)
_hq = _tm["ROCKET_HQ"]["floors"]
_hqp = lambda i: [q for p in _hq[i].get("people", []) if isinstance(p, dict) for q in (p.get("any") or [p])]
check(sum(1 for sc in _hq[0].get("scenes", []) if str(sc.get("flag", "")).startswith("hq_alarm_scene_")) == 5
      and sum(1 for p in _hqp(0) if str(p.get("text", "")).startswith("Persian statue")) == 5,
      "Rocket Hideout B1F: five Persian statues; pass in front of one and a grunt comes running")
_lnc = next((p for p in _hqp(0) if p.get("text") == "Lance"), {})
check((_lnc.get("event") or {}).get("heal"), "...Lance waits on B1F with his Dragonite, and heals your team")
_pool = {t.get("spot_name") or t["name"]: t for t in _area["ROCKET_HQ"]["trainer_pool"]}
check(_pool.get("Team Rocket Grunt", {}).get("victory_flag") == "hq_password_1" and _pool.get("Team Rocket Grunt 2", {}).get("victory_flag") == "hq_password_2",
      "...two grunts give up the office's passwords when beaten")
check(any(b.get("until", {}).get("condition") == ["hq_password_1", "hq_password_2"] for b in _hq[2].get("barred", [])),
      "...the boss's office opens only with both passwords")
check(any((p.get("event") or {}).get("flag") == "hq_murkrow_password" for p in _hqp(2)) and any("hq_murkrow_password" in str(b.get("until")) for b in _hq[1].get("barred", [])),
      "...Petrel's Murkrow repeats the voice password for the Radio Transmitter room")
_el = [p for p in _hqp(1) if p.get("action") == "BOSS" and (p.get("boss") or {}).get("id") == 101]
check(len(_el) == 3, f"...three Electrode power the transmitter ({len(_el)})")
_l2 = next((p for p in _hqp(1) if p.get("text") == "Lance "), {})
check((_l2.get("event") or {}).get("gift_item", {}).get("HM_WHIRLPOOL") and _l2["event"].get("requires") == ["hq_electrode_3"]
      and _hms.HM_BY_BADGE["JOHTO"].get("GLACIER") is None and _hms.USE_BADGE["JOHTO"].get("HM_WHIRLPOOL") == "GLACIER",
      "...then Lance gives Whirlpool (usable with the Glacier Badge)")
_sv = [o for o in _area["MAHOGANY_TOWN"]["explore_options"] if o.get("door") == "souvenir" and o.get("text") in ("Lance", "Dragonite")]
check(len(_sv) == 2, "Mahogany's souvenir shop: Lance and Dragonite uncover the Hideout's stairs")

# ---- the Fishing Guru's Magikarp record (Jordan 11-15: by its hidden strength, record from 130; Ralph's comment on its weakest point)
class _K: pass
_k = _K(); _k.id = 129; _k.is_egg = False; _k.display_name = "MAGIKARP"
_save_team, _save_flag = list(story.player_team), story.story_flags.pop("magikarp_record", None)
story.player_team = [_k]
_k.ivs = {"HP": 31, "ATTACK": 31, "DEFENSE": 30, "SPATK": 30, "SPDEF": 20, "SPEED": 20}   # (162: a record)
_said = []
_eth = story.inventory.get("ETHER", 0)
_run_story_event(g.current_state, {"lines": [], "size_record": True}, lambda c: True, lambda ls: _said.extend(ls))
check(story.story_flags.get("magikarp_record") == 162 and story.inventory.get("ETHER", 0) == _eth + 1 and not any("IV" in x for x in _said),
      f"Lake of Rage: the Fishing Guru measures your Magikarp; a new record wins an Ether ({_said[1:2]})")
_k.ivs = {"HP": 31, "ATTACK": 31, "DEFENSE": 25, "SPATK": 25, "SPDEF": 20, "SPEED": 3}
_said = []
_run_story_event(g.current_state, {"lines": [], "size_record": True}, lambda c: True, lambda ls: _said.extend(ls))
check(story.story_flags.get("magikarp_record") == 162 and any("Ralph" in x and ("fast" in x or "quick" in x) for x in _said),
      f"...a smaller one, and he notes Ralph's was faster ({_said[-1:]})")
story.player_team = _save_team
if _save_flag is None:
    story.story_flags.pop("magikarp_record", None)
else:
    story.story_flags["magikarp_record"] = _save_flag
# ---- followers rest at their trainer's side (Jordan 11-15, global): Lance's Dragonite in the transmitter room
story.story_flags["hq_electrode_1"] = story.story_flags["hq_electrode_2"] = True
_tr = kanto_open = open_map("ROCKET_HQ", "MAHOGANY_TOWN")
if getattr(_tr, "run", None):
    _tr.run.enter_floor(1); frames(30)
    _ff = {m.payload.get("text"): m for m in _tr.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
    if "Lance " in _ff and "Dragonite " in _ff:
        _lm, _dm = _tr._motion(_ff["Lance "]), _tr._motion(_ff["Dragonite "])
        frames(60)
        _lp = tuple(_lm.pos); _bad = {(_lp[0] + _lm.facing[0], _lp[1] + _lm.facing[1]), (_lp[0], _lp[1] + 1)}
        check(abs(_dm.pos[0] - _lp[0]) + abs(_dm.pos[1] - _lp[1]) == 1 and tuple(_dm.pos) not in _bad,
              f"Lance's Dragonite stands at his side, not in front of him (Lance {_lp} facing {_lm.facing}, Dragonite {_dm.pos})")
    else:
        check(False, f"Lance and Dragonite in the transmitter room ({sorted(_ff)})")
for _k in ("hq_electrode_1", "hq_electrode_2"):
    story.story_flags.pop(_k, None)
# ---- N12: Route 44, the Ice Path, Blackthorn (HGSS)
_ip = [q for f in _tm["ICE_PATH"]["floors"] for p in f.get("people", []) if isinstance(p, dict) for q in (p.get("any") or [p])]
_hmw = [o for o in _area["ICE_PATH"]["route_menu"] if (o.get("event") or {}).get("gift_item", {}).get("HM_WATERFALL")]
check(_hmw and _hms.HM_BY_BADGE["JOHTO"].get("RISING") is None and _hms.USE_BADGE["JOHTO"].get("HM_WATERFALL") == "RISING",
      "Ice Path: HM Waterfall lies in an icy corner (usable with the Rising Badge, no longer given by it)")
_bt = {p.get("text"): p for p in _ppl("BLACKTHORN_CITY")}
check(_bt.get("Santos", {}).get("condition") == "weekday:sat" and (_bt["Santos"].get("event") or {}).get("gift_item", {}).get("SOFT_SAND"),
      "Blackthorn: Santos, on Saturdays, gives Soft Sand")
_bo = _area["BLACKTHORN_CITY"]["explore_options"]
check(any((o.get("event") or {}).get("trade", {}).get("give") == 85 for o in _bo) and {"dratinihouse", "dodriotrade", "movehouse"} <= set(_tm["BLACKTHORN_CITY"].get("rooms", {})),
      "...the Dodrio-for-Dragonair trade (Doris holds a Smoke Ball), the Dratini house and the move house are open")
check(_it.HELD_BOOSTS.get("SOFT_SAND") == "GROUND", "Soft Sand powers up Ground-type moves")
if fails:
    print("FAILS:", len(fails))
