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
        "GOLDENROD_CITY", "RADIO_TOWER", "JOHTO_ROUTE_35", "JOHTO_ROUTE_36",
        "DRAGONS_DEN", "DRAGON_SHRINE", "JOHTO_ROUTE_45", "JOHTO_ROUTE_46",   # (N13, 11-16)
        "TOHJO_FALLS", "MR_POKEMONS_HOUSE", "JOHTO_ROUTE_47", "JOHTO_ROUTE_48", "CLIFF_EDGE_GATE", "JOHTO_CLIFF_CAVE", "SAFARI_ZONE_GATE",   # (N14)
        "JOHTO_EMBEDDED_TOWER", "JOHTO_SS_AQUA", "MT_SILVER_CITY", "FRONTIER_ACCESS", "POKEATHLON_DOME",   # (N15)
        "KANTO_ROUTE_27", "KANTO_ROUTE_26", "MT_SILVER", "KANTO_ROUTE_28", "JOHTO_BATTLE_FRONTIER", "JOHTO_SAFARI_ZONE"]   # (N16, N17, N18, N19)


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
# (11-19, the re-audit: every SoulSilver phone trainer; a gift on a team you skipped by waiting still comes - Vance's Carbos)
_phones = {t["name"] for a in _area.values() for t in (a.get("trainer_pool") or []) if isinstance(t, dict) and t.get("phone")}
check(len(_phones) >= 26 and {"Bird Keeper Vance", "Hiker Parry", "Picnicker Erin", "Fisherman Wilton", "Pokefan Beverly"} <= _phones,
      f"Phone: SoulSilver's phone trainers all have rematch teams ({len(_phones)})")
vance_i, vance = next((i, t) for i, t in enumerate(_area["JOHTO_ROUTE_44"]["trainer_pool"]) if t["name"] == "Bird Keeper Vance")
check(vance["phone"]["tiers"][1].get("gift") == {"CARBOS": 1}, "...Vance's second rematch has his Carbos")
phone.register_after_win(g, "JOHTO_ROUTE_44", vance)
story.mark_trainer_defeated("JOHTO_ROUTE_44", vance_i)
_lvl = __import__("src.world.levels", fromlist=["x"])
_save_cap = _lvl.story_ace
_lvl.story_ace = lambda st: 100
try:
    re = phone.rematch_info(g, "JOHTO_ROUTE_44", vance_i, vance)
finally:
    _lvl.story_ace = _save_cap
check(re.get("_phone_tier") == 2 and (re.get("rewards") or {}).get("CARBOS") == 1 and "phone_gift_JOHTO_ROUTE_44|Bird Keeper Vance|1" in str(re.get("_phone_gift")),
      f"...met only at his strongest team, he still hands over the Carbos ({re.get('_phone_tier')}, {re.get('rewards')})")

# ---- givers in the data
li = next(t for t in _area["SPROUT_TOWER"]["trainer_pool"] if t["name"] == "Elder Li")
check(li["rewards"].get("HM_FLASH") and li["team"] == [69, 69, 163], "Elder Li: SoulSilver's team, and Flash for beating him (the Zephyr Badge lets you use it)")
from src.world.hms import hm_for_badge
check(hm_for_badge("JOHTO", "ZEPHYR") is None and hm_for_badge("JOHTO", "HIVE") is None, "...Flash and Cut come from the story now (Elder Li, the charcoal maker), not the badges")
kyle = [o for o in _area["VIOLET_CITY"]["explore_options"] if o.get("text") == "Kyle"]
check(any((o.get("event") or {}).get("trade") == {"want": 69, "give": 95, "item": "PERSIM_BERRY", "nickname": "Rocky"} for o in kyle), "Violet: Kyle trades his Onix (Rocky) for a Bellsprout")

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
check(story.story_flags.get("kurt_examined_gs_ball") and story.inventory.get("GS_BALL") == 1 and not story.story_flags.get("kurt_has_gs_ball"),
      "Kurt studies the GS Ball and gives it straight back: take it to Ilex's shrine")
story.inventory.pop("GS_BALL", None); story.story_flags.pop("kurt_examined_gs_ball", None)
story.story_flags.update({"kurt_has_gs_ball": True, "kurt_gs_ball_day": "2000-01-01"})   # (an older save that left it with him overnight)
az.visit_kurt()
check(story.story_flags.get("kurt_examined_gs_ball") and story.inventory.get("GS_BALL") == 1 and not story.story_flags.get("kurt_has_gs_ball"),
      "...and a save that left it with him gets it back on the next visit")
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
check(r31man and r31man[0]["event"].get("requires") == ["got_kenya"] and r31man[0]["event"]["gift_item"].get("TM085"), "...the man on Route 31 reads it and gives you Rest")
rs = [p for p in _tm["JOHTO_ROUTE_36"].get("people", []) if isinstance(p, dict) and p.get("text") == "Rock Smash man"]
check(rs and rs[0]["event"]["gift_item"].get("HM_ROCK_SMASH") and rs[0]["event"]["requires"] == ["defeated_sudowoodo"], "Route 36: Rock Smash from the man by the odd tree, once it's gone")
dept5 = _tm["GOLDENROD_CITY"]["rooms"]["dept_5"].get("people", [])
check(any("Trader" in str(p) for p in dept5) and any("TM lady" in str(p) for p in dept5), "Dept. Store 5F: the Machop trader and the Sunday TM lady")
stock = {e["item"] for e in gr.get("extra_stock", [])}
check({"TM068", "TM067", "TM069", "TM166", "TM143", "TM163", "TM158"} <= stock, f"...and the 5F TM Corner's TMs on the shelf ({sorted(stock)})")

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
check((_wife.get("event") or {}).get("gift_item", {}).get("TM303") and _wife["event"].get("requires") == ["moomoo_healed"],
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
_elx = story.inventory.get("ELIXIR", 0)
_save_fp = story.story_flags.pop("magikarp_first_prize", None)
_run_story_event(g.current_state, {"lines": [], "size_record": True, "first_prize": "ELIXIR"}, lambda c: True, lambda ls: _said.extend(ls))
check(story.story_flags.get("magikarp_record") == 162 and story.inventory.get("ETHER", 0) == _eth + 1 and not any("IV" in x for x in _said),
      f"Lake of Rage: the Fishing Guru measures your Magikarp; a new record wins an Ether ({_said[1:2]})")
check(story.inventory.get("ELIXIR", 0) == _elx + 1 and story.story_flags.get("magikarp_first_prize"),
      "...and the first record also wins Crystal's Elixir")
story.inventory["ELIXIR"] = _elx
if _save_fp is None:
    story.story_flags.pop("magikarp_first_prize", None)
else:
    story.story_flags["magikarp_first_prize"] = _save_fp
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
# ---- move tutors (Jordan 11-15): Ilex Forest's Headbutt, Grandma Wilma's Draco Meteor, the ultimate moves, Crystal's Goldenrod tutor;
#      the Move Deleter and Reminder are out of work (our Pokemon keep every move)
from src.pokemon.data import Pokemon as _Pk
from src.states.overworld.common import _tutor_teach
def _mon(pid, friend=70):
    m = _Pk(g.loader.fetch_specific(pid), g.assets); m.level = 40; m.friendship = friend; return m
_keep_team = list(story.player_team)
_ilex = next((q for p in _tm["ILEX_FOREST"].get("people", []) if isinstance(p, dict) for q in (p.get("any") or [p]) if q.get("text") == "Tree shaker"), {})
story.player_team = [_mon(25)]
_o = _tutor_teach(g, _ilex["event"]["tutor"], _ilex["event"]) if _ilex.get("event", {}).get("tutor") else ["\x00fail"]
check(_o[0] != "\x00fail" and "HEADBUTT" in __import__("src.pokemon.moves", fromlist=["move_pool"]).move_pool(g, story.player_team[0]),
      f"Ilex Forest: the tree shaker teaches Headbutt ({_o[:1]})")
_wil = next(o for o in _area["BLACKTHORN_CITY"]["explore_options"] if o.get("text") == "Grandma Wilma")["event"]
story.player_team = [_mon(147, 100)]
_o1 = _tutor_teach(g, _wil["tutor"], _wil)
story.player_team = [_mon(147, 255)]
_o2 = _tutor_teach(g, _wil["tutor"], _wil)
check(_o1[0] == "\x00fail" and "close" in _o1[1] and _o2[0] != "\x00fail", "Blackthorn: Grandma Wilma teaches Draco Meteor to a Dragon that loves you")
_ult = next(o for o in _area["BLACKTHORN_CITY"]["explore_options"] if o.get("text") == "Old man")["event"]
story.player_team = [_mon(154, 255)]
check(_ult["tutor"].get("choices") == ["FRENZY-PLANT", "BLAST-BURN", "HYDRO-CANNON"] and _tutor_teach(g, dict(_ult["tutor"], move="FRENZY-PLANT", like="FRENZY-PLANT"), _ult)[0] != "\x00fail",
      "...and the master teaches Meganium Frenzy Plant (the starters' ultimate moves)")
_del = next(o for o in _area["BLACKTHORN_CITY"]["explore_options"] if o.get("text") == "Move Deleter")["event"]
check("every move" in " ".join(_del["lines"]) and not _del.get("tutor"), "...the Move Deleter's out of work: Pokemon keep every move now")
_gt = next((q for p in _tm["GOLDENROD_CITY"].get("people", []) if isinstance(p, dict) for q in (p.get("any") or [p]) if q.get("text") == "Move Tutor"), {})
check(_gt.get("flag_condition") == "beat_johto_champion" and not _gt.get("condition") and _gt["event"]["tutor"]["choices"] == ["FLAMETHROWER", "THUNDERBOLT", "ICE-BEAM"],
      "Goldenrod (Crystal): the Move Tutor, every day after the title (Jordan 11-15)")
from src.states import game_corner as _gc
story.player_team = [_mon(149)]
_gc.add_coins(story, -_gc.coins(story)); _gc.add_coins(story, 3000)
_c1 = _tutor_teach(g, dict(_gt["event"]["tutor"], move="ICE-BEAM", like="ICE-BEAM"), _gt["event"])
_gc.add_coins(story, 2000)
_c2 = _tutor_teach(g, dict(_gt["event"]["tutor"], move="ICE-BEAM", like="ICE-BEAM"), _gt["event"])
check(_c1[0] == "\x00fail" and "coins" in _c1[1] and _c2[0] != "\x00fail" and _gc.coins(story) == 1000,
      f"...for 4000 Game Corner coins a move, as in Crystal ({_c1[-1][:40]} / {_gc.coins(story)} left)")
story.player_team = _keep_team
# ---- Mega on the map in towns too, and it carries between areas (Jordan 11-15)
from src.pokemon import mega_clock as _mc, forms as _fm
_keep = list(story.player_team); _inv = dict(story.inventory)
_v = _mon(3, 70); story.player_team = [_v]
story.inventory["MEGA_BRACELET"] = 1; story.inventory["VENUSAURITE"] = 1
g.rt_mega = None
_town = open_map("CHERRYGROVE_CITY", "JOHTO_ROUTE_29")
_mb = [b for b in (_town._buttons() if hasattr(_town, "_buttons") else []) if str(b[1]).startswith("MEGA")]
if _mb:
    _mb[0][3]()
_was_mega = _mc.active(g) and _fm.is_changed(_v)
_left = _mc.state(g).get("left", 0)
_route = open_map("JOHTO_ROUTE_30", "CHERRYGROVE_CITY"); frames(30)
check(_mb and _was_mega and _mc.active(g) and _fm.is_changed(_v) and 0 < _mc.state(g).get("left", 0) <= _left,   # (the checks' frames don't run Game.run, which ticks the clock)
      f"MEGA in a town: Venusaur Mega Evolves in Cherrygrove and is still Mega on Route 30, its clock running ({bool(_mb)}, {_was_mega}, active {_mc.active(g)}, changed {_fm.is_changed(_v)}, left {_left}->{_mc.state(g).get('left')}, team same {story.player_team[0] is _v})")
g.rt_mega = None
if _fm.is_changed(_v): _fm.revert_form(_v)
story.player_team = _keep; story.inventory.clear(); story.inventory.update(_inv)
# ---- N13 (11-16): HGSS's Dragon's Den. Clair keeps the Rising Badge after her Gym; the Elder's quiz at the Dragon Shrine gives it;
# a Dratini after (Extreme Speed when every answer was right the first time); Clair's TM138 Dragon Pulse by the bridge
_lead = _area["BLACKTHORN_CITY"]["gym"]["leader"]
check(_lead.get("badge_later") == "johto_beat_clair" and _lead.get("badge_reward") == "RISING", "Blackthorn Gym: Clair keeps the Rising Badge when beaten (HGSS)")
_keepN, _flN, _bN = list(story.player_team), dict(story.story_flags), {k: list(v) for k, v in story.badges.items()}
story.badges.setdefault("JOHTO", []); story.badges["JOHTO"] = [b for b in story.badges["JOHTO"] if b != "RISING"]
for f in ("johto_beat_clair", "dragon_quiz_done", "dragon_quiz_done_perfect", "dragon_shrine_dratini", "clair_tm_dragon_pulse"):
    story.story_flags.pop(f, None)
_sh = open_map("DRAGON_SHRINE", "DRAGONS_DEN")
_eld = next((p for p in (_tm["DRAGON_SHRINE"].get("people") or []) if isinstance(p, dict) and p.get("text") == "Elder"), None)
from src.states.overworld.common import _run_story_event as _rseN
_saidN = []
def _talkN(ev):
    _rseN(_sh, ev, lambda c: _sh._check_menu_condition(c) if hasattr(_sh, "_check_menu_condition") else True,
          lambda l, **k: _saidN.extend(l))
    play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 300)
_talkN(_eld["event"])
check(not story.has_badge("RISING") and not story.story_flags.get("dragon_quiz_done"), f"Dragon Shrine: before Clair's battle the Elder only explains ({_saidN[-1:]})")
story.story_flags["johto_beat_clair"] = True
_talkN(_eld["event"])
_picksN = 0
for _ans in (2, 1, 2, 0, 1):
    play(lambda: type(g.current_state).__name__ == "PickListState", 400)
    if type(g.current_state).__name__ == "PickListState":
        g.current_state.pick(_ans); _picksN += 1
play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 400)
check(_picksN == 5 and story.has_badge("RISING") and story.story_flags.get("dragon_quiz_done_perfect"),
      f"...beaten, the Elder's five questions; answered, the Rising Badge, all right the first time ({_picksN}, {story.has_badge('RISING')})")
story.player_team = story.player_team[:5]
_n0 = len(story.player_team)
_talkN(_eld["event"])
_dr = story.player_team[-1] if len(story.player_team) > _n0 else None
check(_dr is not None and _dr.id == 147 and _dr.level == 15 and "EXTREME-SPEED" in _dr.moves, f"...then a Lv 15 Dratini that knows Extreme Speed ({_dr and (_dr.id, _dr.level, _dr.moves)})")
_cl = next((p for p in (_tm["DRAGONS_DEN"]["floors"][1].get("people") or []) if isinstance(p, dict) and p.get("text") == "Clair"), None)
story.inventory.pop("TM115", None)
_rseN(_sh, _cl["event"], lambda c: True, lambda l, **k: None) if _cl else None
check(_cl is not None and _cl.get("condition") == "dragon_quiz_done" and story.inventory.get("TM115") == 1, "...and Clair gives TM138 Dragon Pulse in the Den")
story.player_team = _keepN; story.story_flags.clear(); story.story_flags.update(_flN); story.badges.clear(); story.badges.update(_bN)

# ---- N15 (11-16): the S.S. Aqua's HGSS story - the crewman's sleeping buddy (Sailor Stanly), the granddaughter's hide-and-seek and
# her grandfather's Metal Coat, the captain's Plates (one a day after all 16 Badges, then Nuggets); Mt. Silver's TM Flamethrower;
# the Pokeathlon Dome's plaza from the game file
_flA, _bA, _invA = dict(story.story_flags), {k: list(v) for k, v in story.badges.items()}, dict(story.inventory)
for _f in [f for f in story.story_flags if f.startswith("ss_aqua_")]:
    story.story_flags.pop(_f)
_aq = open_map("JOHTO_SS_AQUA", "OLIVINE_CITY")
_aqP = {p["text"].strip() + (f"@{i}" if p["text"].strip() == "Little girl" else ""): p for i, f in enumerate(_tm["JOHTO_SS_AQUA"]["floors"])
        for p in (f.get("people") or []) if isinstance(p, dict) and p.get("text")}
_saidA = []
def _talkA(who):
    _saidA.clear()
    _rseN(_aq, _aqP[who]["event"], lambda c: _aq._check_route_condition(c, False),
          lambda l, **k: _saidA.extend(l))
    play(lambda: not getattr(g.current_state, "dialogue_box", None) or not g.current_state.dialogue_box.visible, 300)
_need = ["Crewman", "Sailor Stanly", "Captain", "Gentleman", "Little girl@6", "Little girl@5", "Little girl@3"]
check(all(w in _aqP for w in _need), f"S.S. Aqua: the crewman, Stanly, the captain, the gentleman and the girl in her three places {[w for w in _need if w not in _aqP]}")
if all(w in _aqP for w in _need):
    _talkA("Sailor Stanly")
    check(type(g.current_state).__name__ not in ("TrainerIntroState", "TrainerBattleState") and any("Zzz" in l for l in _saidA),
          f"...Sailor Stanly sleeps until his buddy has asked for him ({_saidA[:1]})")
    _talkA("Crewman")
    check(story.story_flags.get("ss_aqua_find_buddy"), "...the crewman on the lower deck asks you to find him")
    _aq = g.current_state
    _rseN(_aq, _aqP["Sailor Stanly"]["event"], lambda c: _aq._check_route_condition(c, False), lambda l, **k: None)
    check(type(g.current_state).__name__ in ("TrainerIntroState", "TrainerBattleState"), f"...then Stanly wakes up and battles ({type(g.current_state).__name__})")
    _aq = open_map("JOHTO_SS_AQUA", "OLIVINE_CITY")
    story.story_flags["ss_aqua_stanly"] = True
    _talkA("Crewman")
    check(any("Thanks" in l for l in _saidA), f"...beaten, the crewman thanks you ({_saidA[:1]})")
    _cnd = lambda w: _aq._check_route_condition(_aqP[w].get("condition"), False) if _aqP[w].get("condition") is not None else True
    check(_cnd("Little girl@6") and not _cnd("Little girl@5") and not _cnd("Little girl@3"), "...the little girl is first in the captain's cabin, pestering him")
    _talkA("Little girl@6")
    check(story.story_flags.get("ss_aqua_girl_hiding") and _cnd("Little girl@5") and not _cnd("Little girl@6"), "...she runs off to hide on the lower deck")
    story.inventory.pop("METAL_COAT", None)
    _talkA("Gentleman")
    check(not story.inventory.get("METAL_COAT"), "...her grandfather asks you to find her (no gift yet)")
    _talkA("Little girl@5")
    check(story.story_flags.get("ss_aqua_girl_found") and _cnd("Little girl@3"), "...found, she goes back to her grandfather's cabin")
    _talkA("Gentleman")
    check(story.inventory.get("METAL_COAT") == 1, "...and he gives you the Metal Coat")
    story.badges = {"JOHTO": [], "KANTO": []}
    _talkA("Captain")
    check(not any(k.endswith("_PLATE") and v for k, v in story.inventory.items()), "...the captain gives nothing before all 16 Badges")
    story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"],
                    "KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]}
    for _k in [k for k in story.inventory if k.endswith("_PLATE")]:
        story.inventory.pop(_k)
    _talkA("Captain"); _talkA("Captain")
    check(story.inventory.get("FLAME_PLATE") == 1 and not story.inventory.get("SPLASH_PLATE"), "...with 16, a Flame Plate - one a day, not two")
    for _k in [k for k in story.story_flags if k.startswith("ss_aqua_captain_gift@")]:
        story.story_flags.pop(_k)   # (the next day)
    _talkA("Captain")
    check(story.inventory.get("SPLASH_PLATE") == 1, "...the next day the Splash Plate")
    story.story_flags["ss_aqua_captain_gifts"] = 16
    for _k in [k for k in story.story_flags if k.startswith("ss_aqua_captain_gift@")]:
        story.story_flags.pop(_k)
    _ng = story.inventory.get("NUGGET", 0)
    _talkA("Captain")
    check(story.inventory.get("NUGGET", 0) == _ng + 1, "...and after all 16 Plates, a Nugget a day")
    from src.pokemon import items as _itA
    check(all(_itA.HELD_BOOSTS.get(f"{p}_PLATE") for p in ("FLAME", "IRON", "DRACO")), "...each Plate boosts its type when held (Flame: Fire, Iron: Steel, Draco: Dragon)")
story.story_flags.clear(); story.story_flags.update(_flA); story.badges.clear(); story.badges.update(_bA); story.inventory.clear(); story.inventory.update(_invA)
_tm139 = json.load(open("assets/tms.json", encoding="utf-8")).get("TM125") or {}
_silver_balls = [o for o in _area["MT_SILVER_CITY"].get("explore_options", []) + _area["MT_SILVER_CITY"].get("route_menu", []) if o.get("found")]
check(_tm139.get("move") == "FLAMETHROWER" and any("TM125" in json.dumps(o) for o in _silver_balls),
      f"Mt. Silver: TM139 Flamethrower (HGSS TM35) lies outside the Pokemon Center ({[o['text'] for o in _silver_balls]})")
_dome = _tm["POKEATHLON_DOME"]
_rows = _dome["art"]
check(len(_rows) == 64 and len(_rows[0]) == 64 and _dome["buildings"] == {"P": "dome"} and any("D" in r for r in _rows)
      and _dome["exits"] == {"v": "NATIONAL_PARK"},
      "Pokeathlon Dome: the plaza is SoulSilver's zone D49, whole; the Dome's door, the way south to the National Park")
_dfolk = [p for p in (_dome.get("people") or []) if isinstance(p, dict) and p.get("event")]
check(len(_dfolk) == 15 and sum(r.count("N") for r in _rows) == 15, f"...its 15 people from the game stand on the plaza ({len(_dfolk)})")

# ---- Mt. Silver's clearing (11-16, Jordan: "fix the entrance to Mt silver however is needed to make canon"): a walked route now,
# SoulSilver's wild Pokemon roaming its grass, its Pokemon Center a room, a Fly spot still; the game's bystander offers our two trips
_flS, _bS, _invS = dict(story.story_flags), {k: list(v) for k, v in story.badges.items()}, dict(story.inventory)
_aS = _area["MT_SILVER_CITY"]
_poolS = {str(k) for f in ("morning_pool_percentages", "day_pool_percentages", "night_pool_percentages") for k in (_ad.get(_aS.get(f)) or {})}
check(_aS.get("area_type") != "town" and _aS.get("fly_island") and {"114", "77", "217", "78"} <= _poolS,
      f"Mt. Silver's clearing: SoulSilver's wild Pokemon (Tangela, Ponyta, Ursaring, Rapidash...) and still a place to Fly to ({sorted(_poolS)})")
story.story_flags["defeated_rival_victory_road_johto"] = True
_ms = open_map("MT_SILVER_CITY", "KANTO_ROUTE_28")
_wildS = [m for f in getattr(_ms.run, "floors", [_ms.run.floor]) for m in f.movers if m.kind == "wild"] if hasattr(_ms, "run") else []
check(type(_ms).__name__ != "WalkTownState" and len(_wildS) > 0, f"...walked like a route: wild Pokemon about in the clearing ({type(_ms).__name__}, {len(_wildS)})")
_wp = _ms._make_wild(__import__("random").Random(3)) if hasattr(_ms, "_make_wild") else None
check(_wp is not None and str(_wp.id) in _poolS, f"...and they're the clearing's own ({_wp and _wp.id})")
_surfS = _ad.get(_aS.get("surf_pool_percentages")) or {}
check(set(_surfS) == {"60", "61"}, f"...and Poliwag and Poliwhirl in its pond, not land Pokemon ({_surfS})")
_artS = (_ms.recipe.get("art") or {})
_cen = [f for f in (_artS.get("floors") or []) if f.get("indoors")]
check(any("POKEMON CENTER" in (f.get("people") or []) for f in _cen), "...its Pokemon Center a room you walk into, the nurse inside")
_guide = next((p for p in (_tm["MT_SILVER_CITY"].get("people") or []) if isinstance(p, dict) and p.get("text") == "Mountain guide"), None)
check(_guide is not None, "...the game's bystander is a guide")
if _guide:
    story.badges = {"JOHTO": ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]}
    story.story_flags["beat_johto_champion"] = True
    story.inventory["HM_ROCK_CLIMB"] = 1
    _rseN(_ms, _guide["event"], lambda c: _ms._check_route_condition(c, False), lambda l, **k: None)
    play(lambda: type(g.current_state).__name__ == "PickListState", 300)
    _pl = g.current_state
    _opts = [getattr(b, "text", None) for b in getattr(_pl, "rows", [])] if type(_pl).__name__ == "PickListState" else []
    check(len(_opts) == 1, f"...who offers the League plateau (the mountainside is walked from Mt. Silver 1F since N16) ({_opts})")
    if type(_pl).__name__ == "PickListState":
        _pl.pick("SILVER_LEAGUE_PLATEAU")
        frames(3)
    check(type(g.current_state).__name__ == "AreaTransitionState" or story.current_area_key == "SILVER_LEAGUE_PLATEAU",
          f"...and takes you there ({type(g.current_state).__name__}, {story.current_area_key})")
story.story_flags.clear(); story.story_flags.update(_flS); story.badges.clear(); story.badges.update(_bS); story.inventory.clear(); story.inventory.update(_invS)

print("Odd Egg (Jordan 11-16): seven from Route 34's Day-Care Man, the next one the day after the last hatches")
from src.world import odd_egg as _oe
_dc = next(o for o in _area["JOHTO_ROUTE_34"]["route_menu"] if o.get("text") == "Day-Care Man")
_flO = dict(story.story_flags); _teamO = list(story.player_team)
for _k in ("odd_eggs_given", "odd_egg_pending", "odd_egg_hatched_day", "odd_egg_ready"):
    story.story_flags.pop(_k, None)
story.current_area_key = "JOHTO_ROUTE_34"
_pO = PlayState(g, classic=True); g.change_state(_pO)
_got, _waits, _mission = [], 0, []
for _i in range(_oe.COUNT):
    story.player_team = [p for p in story.player_team if p and not getattr(p, "is_egg", False)][:5]
    _mission.append(any(m.get("id") == "johto_s_oddegg" for m in story.get_active_missions()))
    _rseN(_pO, _dc["event"], lambda c: True, lambda l, **k: None)
    _eggs = [p for p in story.player_team if getattr(p, "is_egg", False)]
    _got.append(_eggs[-1].id if _eggs else None)
    _rseN(_pO, _dc["event"], lambda c: True, lambda l, **k: None)       # (talking again before it hatches: no second Egg)
    _waits += len([p for p in story.player_team if getattr(p, "is_egg", False)]) == 1
    _oe.hatched(story, _got[-1])
    _rseN(_pO, _dc["event"], lambda c: True, lambda l, **k: None)       # (the same day it hatched: nothing yet)
    _waits += len([p for p in story.player_team if getattr(p, "is_egg", False)]) == 1
    story.story_flags["odd_egg_hatched_day"] = "2000-01-01"               # (a calendar day later)
check(sorted(_got) == sorted(_oe.SPECIES) and _waits == 2 * _oe.COUNT and all(_mission),
      f"...seven different babies {_got}, one at a time, each a day after the last hatched; the Journal mission each time {_mission}")
check(not _oe.refresh(story) and not any(m.get("id") == "johto_s_oddegg" for m in story.get_active_missions()), "...and no eighth")
story.story_flags.clear(); story.story_flags.update(_flO); story.player_team = _teamO

print("Lance and Dragonite walk with you through the Rocket Hideout (Jordan 11-16)")
_flL = dict(story.story_flags)
story.story_flags["defeated_red_gyarados"] = True; story.story_flags.pop("got_hm_whirlpool_lance", None)
story.current_area_key, story.last_area_key = "ROCKET_HQ", "MAHOGANY_TOWN"
_hq = PlayState(g); g.change_state(_hq)
_left = [m.payload.get("text") for fl in _hq.run.floors for m in fl.movers if m.kind == "figure" and isinstance(m.payload, dict)
         and m.payload.get("text", "").strip() in ("Lance", "Dragonite")]
for _d in [(-1, 0), (-1, 0), (0, -1), (-1, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:   # (until three real steps: someone
    if len(set(list(_hq._ctrail)[:3])) == 3:                                                    # wandering can block one, 11-22)
        break
    if _hq.run.floor.walkable(_hq.run.player[0] + _d[0], _hq.run.player[1] + _d[1]):
        _hq.step(*_d)
    for _ in range(20): _hq.update()
_tr = list(_hq._ctrail)
check(_hq._companions() == ("Lance", "Dragonite") and not _left and len(set(_tr[:3])) == 3 and _hq._companion_at(_tr[1]) == "Lance",
      f"...they follow a step behind your Pokemon {_tr[:3]}; their standing figures step off ({_left})")
story.story_flags["got_hm_whirlpool_lance"] = True
check(_hq._companions() == (), "...and leave once Lance has given you Whirlpool")
story.story_flags.clear(); story.story_flags.update(_flL)

print("N18: the Battle Frontier's five facilities (Jordan 11-16: real streaks per facility)")
from src.world import frontier as _fr
_bf = _tm["JOHTO_BATTLE_FRONTIER"]
check(set((_bf.get("rooms") or {})) == set(_fr.JOHTO_FIVE) | {"jgate"} and all(   # (11-22: and the gate, south, down to Frontier Access)
          any(isinstance(p, str) and "attendant" in p for p in _bf["rooms"][k].get("people", [])) for k in _fr.JOHTO_FIVE),
      f"the plaza's five lobbies, an attendant in each {sorted(_bf.get('rooms') or {})}")
_flF = dict(story.story_flags)
for _k in [k for k in story.story_flags if k.startswith("frontier_j") or k == "johto_battle_frontier_cleared"]:
    story.story_flags.pop(_k, None)
story.story_flags["frontier_jtower_wins"] = 5
_p1 = _fr.next_trainer(g, "jtower")
_fr.after_battle(g, "jtower", True)
story.story_flags["frontier_jtower_wins"] = 10
_p2 = _fr.next_trainer(g, "jtower")
check(_p1["name"] == "Tower Tycoon Palmer" and _p1["team"] == [464, 350, 149] and _p1["movesets"]["464"][0] == "ROCK-WRECKER"
      and _p2["team"] == [485, 488, 486] and story.story_flags.get("frontier_jtower_silver"),
      f"...Palmer after 5 wins with the game's own team and moves, then 10 for his Gold team {_p1['team']} -> {_p2['team']}")
for _f in ["jfactory", "jhall", "jcastle", "jarcade"]:
    story.story_flags[f"frontier_{_f}_wins"] = 5
    _b = _fr.next_trainer(g, _f); _ln = _fr.after_battle(g, _f, True)
check(story.story_flags.get("johto_battle_frontier_cleared") and any("Print" in l for l in _ln),
      "...a Silver Print from all five clears Johto's Frontier (its Journal mission)")
story.story_flags.clear(); story.story_flags.update(_flF)

print("N19: the Safari Zone's Area Setup (Jordan 11-16: all ten default layouts)")
_rc = next(o for o in _area["SAFARI_ZONE_GATE"]["explore_options"] if o.get("text") == "Safari receptionist")
_ch = _rc["event"]["choose"]
check(_ch["flag"] == "safari_layout" and len(_ch["choices"]) == 10 and _ch["choices"][0]["text"].startswith("1: Plains, Swamp, Meadow")
      and "gate" in (_tm["SAFARI_ZONE_GATE"].get("rooms") or {}) and "Safari receptionist" in _tm["SAFARI_ZONE_GATE"]["rooms"]["gate"].get("people", []),
      "the gatehouse receptionist offers HGSS's ten default layouts")
_aS2 = _area["JOHTO_SAFARI_ZONE"]
check(_ad[_aS2["zone_pools"]["desert"]].get("27") and _ad[_aS2["zone_pools"]["peak"]].get("74") and _aS2["safari_game"] == {"balls": 30, "steps": 500},
      "...each area's Pokemon are SoulSilver's own (Desert: Sandshrew; Peak: Geodude)")

print("N16: Routes 26-27's houses")
from src.pokemon import evolution as _evoN

_rest = next(o for o in _area["KANTO_ROUTE_26"]["route_menu"] if o.get("text") == "Resting woman")
_tmman = next(o for o in _area["KANTO_ROUTE_27"]["route_menu"] if o.get("text") == "Thoughtful man")
check("resthouse" in ((_tm["KANTO_ROUTE_26"].get("rooms") or {})) and "tmhouse" in ((_tm["KANTO_ROUTE_27"].get("rooms") or {})),
      "Route 26's rest house and Route 27's house are rooms you walk into")
story.current_area_key, story.last_area_key = "KANTO_ROUTE_26", "KANTO_ROUTE_27"
_pN = PlayState(g, classic=True); g.change_state(_pN)
_lead = story.player_team[0]; _lead.current_hp = 1
_rseN(_pN, _rest["event"], lambda c: _pN._check_route_condition(c, False), lambda l, **k: None)
check(_lead.current_hp == _lead.max_hp, f"...the woman on Route 26 lets your team rest ({_lead.current_hp}/{_lead.max_hp})")
_fr, _af = getattr(_lead, "friendship", 0), getattr(_lead, "affection", 0)
_lead.friendship, _lead.affection = 0, 0
_low = _pN._check_route_condition("lead_trusts_you", False)
_lead.friendship = _evoN.FRIENDSHIP_CATCHES
_high = _pN._check_route_condition("lead_trusts_you", False)
_lead.friendship, _lead.affection = _fr, _af
check(not _low and _high and _tmman["event"]["requires"] == ["lead_trusts_you"] and "TM051" in _tmman["event"]["gift_item"],
      "...the man on Route 27 gives TM Sandstorm only when your lead Pokemon trusts you")

# ---- 11-19, Jordan: "Put unknown only inside of the ruins not outside"; Slugma and Houndour somewhere in Johto's first playthrough
_ad = g.loader.area_data
_ruins = _ad["STORY_PROGRESSION"]["RUINS_OF_ALPH"]
check(_ad[_ruins["grass_pool_percentages"]] == {"177": 90, "235": 10} and set(_ad[_ruins["wild_pool_percentages"]]) == {"201"},
      "Ruins of Alph: the outside grass has SoulSilver's Natu and Smeargle; Unown are the inside's (Explore Ruins) only")
_rs = open_map("RUINS_OF_ALPH", "JOHTO_ROUTE_32")
_grass = [(x, y) for y, r in enumerate(_rs.grid) for x, c in enumerate(r) if c == '"' and _rs.rows[y][x] == "."]
_met, _off = set(), 0
_rate, _rs.GRASS_RATE = _rs.GRASS_RATE, 1.0
import random as _rnd
_rnd.seed(7)
for _ in range(30):
    g.change_state(_rs)
    _rs.anim_from = (_grass[0][0] + 1, _grass[0][1])
    if _rs._grass_wild(_grass[0]):
        _met.add(getattr(getattr(g.current_state, "opponent_pokemon", None), "id", None))
g.change_state(_rs)
_path = next((x, y) for y, r in enumerate(_rs.grid) for x, c in enumerate(r) if c == "=" and _rs.rows[y][x] == ".")
_rs.anim_from = (_path[0], _path[1] - 1)
_off = _rs._grass_wild(_path)
_rs.GRASS_RATE = _rate
check(_grass and _met and _met <= {177, 235} and not _off,
      f"...walking in that grass meets them ({sorted(x for x in _met if x)}), and nothing on the stone paths")
_bt = _ad["STORY_PROGRESSION"]["BURNED_TOWER"]
check(not any({"218", "228"} & set(_ad.get(_bt.get(f)) or {}) for f in ("wild_pool_percentages", "morning_pool_percentages", "day_pool_percentages", "night_pool_percentages")),
      "Burned Tower: no Slugma or Houndour (HG/SS don't have them there)")
from src.states.overworld.common import PRIMO_EGGS
check(218 in PRIMO_EGGS and _ad["JOHTO_SAFARI_SAVANNAH_PERCENTAGES"].get("228"),
      "...Slugma comes from Primo's Egg in Violet, Houndour from the Safari Zone's Savannah (both before the League)")
check(not {"177"} & set(_ad[_ad["STORY_PROGRESSION"]["JOHTO_ROUTE_36"]["wild_pool_percentages"]]), "Route 36: no stand-in Natu (it's in the Ruins' grass)")

# ---- 11-19, the Johto re-audit: SoulSilver's trades (a/1/1/2: nicknames from its text bank 200, held items) and Friday's Lapras
_tr = {}
for _k in ("VIOLET_CITY", "GOLDENROD_CITY", "OLIVINE_CITY", "BLACKTHORN_CITY"):
    for _o in _area[_k].get("explore_options", []):
        if (_o.get("event") or {}).get("trade"):
            _t = _o["event"]["trade"]
            _tr[_t["give"]] = (_t.get("nickname"), _t.get("item"))
check(_tr == {95: ("Rocky", "PERSIM_BERRY"), 66: ("Muscle", "MACHO_BRACE"), 100: ("Billy", "CHERI_BERRY"), 85: ("Doris", "SMOKE_BALL")},
      f"Johto's trades: SoulSilver's nicknames and held items (Rocky, Muscle with his Macho Brace, Billy, Doris) ({_tr})")
_lap = next(o for o in _area["UNION_CAVE"]["route_menu"] if o.get("text") == "CHALLENGE LAPRAS")
check("weekday:fri" in _lap["condition"], "Union Cave's Lapras: Fridays only, as HGSS")

if fails:
    print("FAILS:", len(fails))
