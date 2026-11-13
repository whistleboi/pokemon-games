
# Jordan's 10-29 changes: canon levels, EXP SHARE and XP for every battler, the town menu on routes,
# Hoenn's catching before the Pokedex and Galarian Zigzagoon.
from collections import Counter
from src.world import levels, regional_forms
from src.states.overworld import PlayState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]

print("1) canon levels: each region's own game")
check(levels.CHAMPION_ACE["JOHTO"] == 50 and levels.CHAMPION_ACE["SINNOH"] == 66, "Lance 50 (HGSS), Cynthia 66 (BDSP)")
check(levels.GYM_ACE["ORANGE"] == [levels.GYM_ACE["JOHTO"][i] for i in (1, 3, 5, 7)], "Orange Gyms = Johto Gyms 2/4/6/8")
check(prog["PUMMELO_ISLAND"]["gym"]["leader"]["levels"][-1] == levels.CHAMPION_ACE["JOHTO"], "Drake's ace = Lance's")
check(levels.canon_area_level(g, "JOHTO_ROUTE_44") == 23, f"Route 44 at HGSS's 22-26: {levels.canon_area_level(g, 'JOHTO_ROUTE_44')}")
story.player_team = [mk(6), mk(9), mk(3)]
for _p, _l in zip(story.player_team, (40, 30, 5)):
    _p.level = _l
check(levels.area_level(g, "JOHTO_ROUTE_29") == 35, "areas keep up with the team: its average, the lowest left out (Jordan, 11-07)")
story.player_team[0].level = story.player_team[1].level = 2
check(levels.area_level(g, "JOHTO_ROUTE_44") == 23, "...never below the area's own level")

print("2) XP: every battler that hasn't fainted; EXP SHARE gives the rest half")
story.current_area_key = "HOENN_ROUTE_101"
story.level_cap_mode = "NONE"
a, b, c = mk(258), mk(261), mk(263)
for p in (a, b, c):
    p.level, p.xp = 10, 0
    p.current_hp = p.get_max_hp()
story.player_team = [a, b, c]
story.inventory.pop("EXP_SHARE", None)
story.exp_share = False
bt = battle(story.current_area_key, 258, 263)
story.player_team = [a, b, c]
bt.player_pokemon = a
bt._note_participant()
bt.player_pokemon = b
bt._note_participant()
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(a): 0.5, id(b): 0.5}, "EXP SHARE off: the two battlers split it")
a.current_hp = 0
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(b): 1.0}, "a fainted battler gets none")
a.current_hp = a.get_max_hp()
story.exp_share = True
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(a): 1.0, id(b): 1.0, id(c): 0.5}, "EXP SHARE on: battlers all of it, the rest half")
check(getattr(type(story)(), "exp_share", None) is True, "EXP SHARE is on by default")

print("3) Hoenn: battle before the Pokedex, catch only after")
story.story_flags.pop("received_pokedex_hoenn", None)
check(not story.catch_unlocked("HOENN"), "no catching before Birch's Pokedex")
story.story_flags["received_pokedex_hoenn"] = True

print("4) Galarian Zigzagoon: not in Hoenn until Galar; wild battles follow the pool's odds")
pool = g.loader.area_data["HOENN_ROUTE_101_PERCENTAGES"]
story.visited_region_set = {"HOENN"}
story.current_area_key = "HOENN_ROUTE_101"
check("2032" not in regional_forms.extend_pool(g, pool), "Galarian Zigzagoon filtered out")
ps = PlayState(g)
picks = Counter()
orig = levels.set_wild
levels.set_wild = lambda game, poke, area: picks.update([poke.id]) or orig(game, poke, area)
for _ in range(120):
    g.change_state(ps)
    ps.action_battle_wild()
levels.set_wild = orig
check(picks[263] > picks[2032] * 5 and picks[263] > 20, f"Zigzagoon common, no Galarian: {dict(picks)}")

print("5) routes: the town menu (EXPLORE / PKDEX / POKeMON / TRAVEL) with pop-ups")
story.current_area_key = "HOENN_ROUTE_104"
ps = PlayState(g)
g.change_state(ps)
ps.rounds_completed = 99  # the route's opening rounds done: its ways out are open
ps.show_progression_menu()
check([b.text for b in ps.route_action_menu.buttons] == ["EXPLORE", "PKDEX", "POKéMON", "TRAVEL"], "four commands")
ps.toggle_route_popup("explore")
shown = [b for b in ps.route_buttons if b in g.ui_manager.elements]
check(shown and all(b.route_group == "explore" for b in shown), f"EXPLORE: {[b.text for b in shown]}")
ps.toggle_route_popup("travel")
shown = [b for b in ps.route_buttons if b in g.ui_manager.elements]
check(shown and all(b.route_group == "travel" for b in shown), f"TRAVEL: {[b.text for b in shown]}")
print("6) leaving a route early: an ambush or a reason (Jordan, 10-29)")

import random as _rnd

said = []

PlayState.show_dialogue = lambda self, lines, callback=None: said.append((list(lines), callback))

story.current_area_key = "HOENN_ROUTE_104"

ps = PlayState(g)

g.change_state(ps)

ps.rounds_completed = 0

ps.show_progression_menu()

early = [b for b in ps.route_buttons if b.route_group == "travel"]

check(early, f"TRAVEL still lists the ways out before the route is done: {[b.text for b in early]}")

_rnd.seed(1)

kinds = Counter()

for _ in range(200):

    said.clear()

    ps._exit_ambush({"condition": "can_exit"})

    line = said[-1][0][0]

    kinds["trainer" if "trainer" in line else "wild" if "wild" in line else "blocked"] += 1

check(55 <= kinds["blocked"] <= 145 and kinds["trainer"] and kinds["wild"],

      f"about 40% ambush, split trainer/wild: {dict(kinds)}")

for i in range(len(ps.area_data.get("trainer_pool", []))):

    story.mark_trainer_defeated("HOENN_ROUTE_104", i)

kinds = Counter()

for _ in range(100):

    said.clear()

    ps._exit_ambush({"condition": "can_exit"})

    kinds["trainer" if "trainer" in said[-1][0][0] else "other"] += 1

check(kinds["trainer"] == 0, "no trainers left: the ambush is always wild")

story.current_area_key = "KANTO_ROUTE_22"

story.badges = {"KANTO": []}

ps = PlayState(g)

g.change_state(ps)

ps.rounds_completed = 99

ps.show_progression_menu()

r23 = next((b for b in ps.route_buttons if "23" in b.text), None)

said.clear()

if r23:

    r23.callback()

check(r23 is not None and said and "eight badges" in said[-1][0][0], f"Route 23 says why: {said[-1][0] if said else None}")

print("7) get through the exit ambush and you leave that way")

from src.states.overworld import AreaTransitionState

story.current_area_key = "UNOVA_ROUTE_2"

story.player_team = [mk(495)]

ps = PlayState(g)

g.change_state(ps)

exit_opt = {"text": "Striaton City", "action": "EXIT", "target_area": "STRIATON_CITY", "condition": "can_exit"}

story.ambush_exit = {"area": "UNOVA_ROUTE_2", "exit": exit_opt}

ps.show_progression_menu()

check(isinstance(g.current_state, AreaTransitionState) and story.ambush_exit is None, "won the ambush: off to Striaton City")

ps = PlayState(g)

g.change_state(ps)

story.player_team[0].current_hp = 0

story.ambush_exit = {"area": "UNOVA_ROUTE_2", "exit": exit_opt}

ps.show_progression_menu()

left = isinstance(g.current_state, AreaTransitionState) and getattr(g.current_state, "next_area_key", "") == "STRIATON_CITY"
check(not left and story.ambush_exit is None, f"lost it: not sent on to Striaton ({type(g.current_state).__name__})")

story.player_team[0].current_hp = story.player_team[0].get_max_hp()

print("8) the trainer battle intro, as in a fan game (Jordan, 10-30)")
import pygame as _pg
from src.states.battle import TrainerBattleState
from src.vfx import animations as _an
from src.utils import Utils as _U
PlayState.show_dialogue = PlayState.__dict__.get("_orig_show", PlayState.show_dialogue)
story.current_area_key = "KANTO_ROUTE_24"
story.player_team = [mk(4), mk(25)]
for p in story.player_team:
    p.current_hp = p.get_max_hp()
ps = PlayState(g)
g.change_state(ps)
ps.trigger_trainer_battle(specific_index=0)
seen, texts = [], []
for i in range(600):
    st = g.current_state
    ph = (type(st).__name__, getattr(st, "phase", ""))
    if not seen or seen[-1] != ph:
        seen.append(ph)
    box = getattr(st, "dialogue_box", None)
    if box is not None and box.visible and box.text_lines and box.text_lines[0] not in texts:
        texts.append(box.text_lines[0])
    st.draw()
    if isinstance(st, TrainerBattleState) and st.phase == "MENU":
        break
    if box is not None and box.visible and getattr(box, "is_waiting_for_click", False) and ph[1] == "CHALLENGE":
        box.advance()
    st.update()
order = [p for n, p in seen if n == "TrainerIntroState"]
check(order == ["SLIDE_IN", "CHALLENGE", "FOE_OUT", "PLAYER_OUT"], f"intro steps {order}")
check(seen[-1] == ("TrainerBattleState", "MENU"), f"then the battle menu {seen[-1]}")
check(any(t.startswith("You are challenged by") for t in texts) and any(" sent out " in t for t in texts)
      and any(t.startswith("Go! ") for t in texts), f"lines {texts}")
img = _an.battle_sprite(story.player_team[0], "player")
r = _an.sprite_rect(g, img, "player")
feet = r.bottom - (img.get_height() - img.get_bounding_rect().bottom)
check(feet == _U.get_full_dialogue_rect(g).top + _an.PLAYER_FEET_UNDER_BOX, f"your Pokemon stands on the text box ({feet})")
big = _an.battle_sprite(mk(143), "opponent")
check(big.get_bounding_rect().height <= 720 * _an.MAX_HEIGHT["opponent"] + 1, "Snorlax stays on screen")
print("9) Journeys region maps for the Town Map and Fly (Jordan, 10-30)")
import os as _os
from src.states import region_map as _rmod
_rm = _rmod.map_data(g).get("region_maps", {})
check(set(_rm) == set(_rmod.map_data(g)["views"]) - {"PALDEA"}, f"a map for every region but Paldea {sorted(_rm)}")
for _v, _e in _rm.items():
    _img = _pg.image.load(_os.path.join(g.assets.assets_dir, _e["file"]))
    _w, _h = _img.get_size()
    _want = {k for k in _rmod.map_data(g)["points"] if _rmod.view_of(g, k) == _v}
    check(_want <= set(_e["points"]), f"{_v}: every Fly town placed {sorted(_want - set(_e['points']))}")
    check(all(0 <= x < _w and 0 <= y < _h for x, y in _e["points"].values()), f"{_v}: points on the map")
story.current_area_key = "AQUACORDE_TOWN"
story.story_flags["visited_AQUACORDE_TOWN"] = True
story.story_flags["visited_LUMIOSE_CITY"] = True
_st = _rmod.RegionMapState(g, ps, fly=True)
g.change_state(_st)
check(_st.view == "KALOS" and _st.map_img is not None and _st.map_img.get_width() > 480 * 1.5, f"Kalos on its own map {_st.view}")
_tw = dict(_st.towns())
check("AQUACORDE_TOWN" in _tw and _st.map_rect.collidepoint(_tw["AQUACORDE_TOWN"]), "Aquacorde is on the map")
check(_st._hit(_tw["LUMIOSE_CITY"]) == "LUMIOSE_CITY", "tapping Lumiose finds it")
_st.update(); _st.draw()
_pg.image.save(g.screen, _os.path.join(S, "fly_kalos.png"))
print("10) Journeys graphics: battle intros, battle backgrounds, Ash's throw, title scenes, ribbons (Jordan, 10-30)")
import datetime as _dt
from src.vfx import transitions as _tr
from src.states.battle import TrainerIntroState as _TIS
story.current_area_key = "KANTO_ROUTE_24"
_ps = PlayState(g); g.change_state(_ps); g.current_state = _ps; _ps.draw()
check(not g.battle_transitions, "no intros headless (checks step straight into battles)")
g.battle_transitions = True
_ps.trigger_trainer_battle(specific_index=0)
check(isinstance(g.current_state, _tr.BattleTransitionState), f"a trainer battle opens with an intro {type(g.current_state).__name__}")
for _i in range(80):
    g.current_state.draw(); g.current_state.update()
    if isinstance(g.current_state, _TIS):
        break
check(isinstance(g.current_state, _TIS), "then the trainer's intro")
_intro = g.current_state
for _style in ("rule", "hexa", "ball", "water", "wedges", "vs", "rocket"):
    g.current_state = _ps
    _t = _tr.BattleTransitionState(g, _intro, _style)
    for _i in range(_t.length):
        _t.draw(); _t.t += 1
check(_tr.style_for(_intro) in ("wedges", "hexa", "rule"), "a plain trainer gets a plain wipe")
_intro.next_state.trainer_class = "GYM_LEADER"
check(_tr.style_for(_intro) == "vs", "a gym leader gets the VS screen")
_intro.next_state.trainer_class = "ROCKET_GRUNT"
check(_tr.style_for(_intro) == "rocket", "Team Rocket gets their R")
g.battle_transitions = False
g.player_character = "ash"
_frames = g.assets.get_player_image("ash", back=True, frames=True)
check(len(_frames) == 5 and g.assets.get_player_image("ash", back=True).get_size() == (128, 128), "Ash's back is a 5-picture throw")
check(len(g.assets.get_player_image("red", back=True, frames=True)) == 1, "a plain back sprite is one picture")
_it = _TIS(g, _intro.trainer_sprite, ["Hi"], _intro.next_state)
check(len(_it.throw_frames) == 5, "the intro plays Ash's throw")
g.player_character = "red"
_a = g.assets
_files = ["battle_field1.png", "journeys/battle_field_j.png", "journeys/battle_field_j_eve.png", "journeys/battle_field_j_night.png"]
check(_a._for_time_of_day(_files, _dt.datetime(2026, 1, 1, 12)) == _files[:2], "day: the daytime backgrounds")
check(_a._for_time_of_day(_files, _dt.datetime(2026, 1, 1, 18)) == [_files[2]], "evening: the evening one")
check(_a._for_time_of_day(_files, _dt.datetime(2026, 1, 1, 23)) == [_files[3]], "night: the night one")
check(_a._for_time_of_day(["battle_cave1.png", "journeys/battle_cave_j1.png"], _dt.datetime(2026, 1, 1, 23)) == ["battle_cave1.png", "journeys/battle_cave_j1.png"], "no night version: the daytime ones")
check(sum(1 for n in _a.battle_bg_map if "_j" in n) >= 40, "the Journeys battle backgrounds are found")
check(_a.get_league_background("battle_elite_lorelei.png") is not None, "an Elite Four room without art gets a league arena")
from src.states.menus import MainMenuState as _MM
_mm = _MM(g)
check(len(_mm.scenes) == 5, f"title scenes {len(_mm.scenes)}")
_mm.draw(); _pg.image.save(g.screen, _os.path.join(S, "title.png"))
from src.states.contest import RibbonCaseState as _RC
from src.pokemon.contest import ribbon_id as _rid
story.player_team[0].ribbons = [_rid("COOL", "NORMAL"), _rid("COOL", "SUPER"), _rid("CUTE", "NORMAL")]
_rc = _RC(g, _ps)
check(len(_rc.icons) == 20, "the 20 contest ribbon icons")
_rc.draw(); _pg.image.save(g.screen, _os.path.join(S, "ribbons.png"))
print("11) from Unova on: the Pokemon Center with its shop inside; Kalos's one Center (Jordan, 10-30)")
from src.states import overworld as _ow
story.current_area_key = "SANTALUNE_CITY"
_town = _ow.CityState(g); g.change_state(_town)
_opts = _ow.center_entrance(_town.area_data["explore_options"]) if _ow.combined_center(g) else []
_acts = [o.get("action") for o in _opts]
check("CENTER" in _acts and "HEAL" not in _acts and "SHOP" not in _acts, f"Santalune: one way into the Center {_acts}")
_town._get_callback_for_option(next(o for o in _opts if o["action"] == "CENTER"))()
_in = g.current_state
check(isinstance(_in, _ow.CenterInsideState), f"inside the Center {type(_in).__name__}")
check([o["action"] for o in _in.area_data["explore_options"]] == ["HEAL", "SHOP"], "EXPLORE: heal and shop")
check(_in.background is not None and getattr(_in, "generic_bg", False), "Kalos's one Center picture (Nurse Joy in it)")
_in.draw(); _pg.image.save(g.screen, _os.path.join(S, "center_inside.png"))
story.player_team[0].current_hp = 1
_in._get_callback_for_option({"action": "HEAL"})()
check(isinstance(g.current_state, _ow.PokeCenterState) and story.player_team[0].current_hp == story.player_team[0].get_max_hp(),
      "HEAL heals")
check(g.current_state.nurse_sprite is None, "no second Nurse Joy over the picture")
g.current_state.finish_heal()
check(g.current_state is _in, "back inside after healing")
from src.states.systems import PokeMartState as _PM
_in._get_callback_for_option(_in.area_data["explore_options"][1])()
check(isinstance(g.current_state, _PM), "SHOP opens the shop")
g.change_state(_in)
_in._get_callback_for_option(_in.area_data["travel_options"][0])()
check(g.current_state is _town, "TRAVEL takes you back out to the town")
story.current_area_key = "VERMILLION_CITY"
_k = _ow.CityState(g)
check(not _ow.combined_center(g), "Kanto keeps its Center and Mart apart")
story.current_area_key = "SANTALUNE_CITY"
print("12) Fake Out: goes first and always flinches, but only on the user's first turn out (Jordan, 10-30)")
from src.states.battle import WildBattleState as _WB


def _settle(b, frames=600):
    log = []
    for _ in range(frames):
        if b.phase == "MENU" and not b.dialogue_box.visible and not b.turn_actions:
            break
        if b.dialogue_box.visible:
            for line in b.dialogue_box.text_lines:
                if line not in log:
                    log.append(line)
            b.dialogue_box.is_finished = True
            cb = b.dialogue_box.callback
            if cb:
                b.dialogue_box.callback = None
                cb()
        b.feedback_timer = 0
        b.update()
    return log


def _turn(b):
    b.open_move_menu()
    b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
    b._question_at -= 5000
    b.math_ui.on_click(b.options.index(b.correct_ans))
    return _settle(b)


def _mon(pid, level, moves):
    p = mk(pid)
    p.level, p.moves = level, list(moves)
    p.current_hp = p.get_max_hp()
    return p


story.level_cap_mode = "NONE"
story.current_area_key = "KANTO_ROUTE_1"
_me = _mon(52, 30, ["FAKE-OUT"])
story.player_team = [_me, _mon(52, 30, ["FAKE-OUT"])]
_b = _WB(g, _mon(135, 60, ["TACKLE"]), "KANTO_ROUTE_1"); g.change_state(_b); _settle(_b)
_log = _turn(_b)
check(_log[:1] == ["MEOWTH USED FAKE OUT!"] and any("flinched" in l for l in _log),
      f"turn 1: before a faster foe, and it flinches {_log}")
_log = _turn(_b)
check("But it failed!" in _log and not any("flinched" in l for l in _log), f"turn 2: it fails {_log}")
_b.player_pokemon = story.player_team[1]   # a new Pokemon comes out
_log = _turn(_b)
check(any("flinched" in l for l in _log), f"a Pokemon just sent out can use it {_log}")
story.player_team = [_mon(135, 60, ["TACKLE"])]
_foe = _mon(52, 30, ["FAKE-OUT", "SCRATCH"])
_b = _WB(g, _foe, "KANTO_ROUTE_1"); g.change_state(_b); _settle(_b)
_log = _turn(_b)
check(any("Foe MEOWTH USED FAKE OUT" in l for l in _log) and any("flinched" in l for l in _log),
      f"the foe uses it on its first turn {_log}")
_log = _turn(_b)
check(not any("FAKE OUT" in l for l in _log), f"and not after {_log}")
print("13) Unova's Journal: the Black/White story in order, then its side quests (Jordan, 10-30)")
from src.world import guide as _guide
_saved = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key)
story.current_area_key = "NUVEMA_TOWN"
story.badges["UNOVA"] = []
for _k in list(story.story_flags):
    if not _k.startswith("visited_") or _k[8:] in g.loader.area_data["STORY_PROGRESSION"]:
        story.story_flags.pop(_k)
_steps = [  # (what happens, the main mission shown after it)
    (None, "unova_m1"), ("defeated_rival_nuvema", "unova_m2"), ("heard_n_accumula", "unova_m3"),
    ("defeated_n_route2", "unova_m4"), ("got_elemental_monkey", "unova_m5"),
    ("TRIO", "unova_m6"), ("BASIC", "unova_m7"), ("plasma_nacrene_cleared", "unova_m8"),
    ("plasma_pinwheel_cleared", "unova_m9"), ("plasma_castelia_cleared", "unova_m10"), ("INSECT", "unova_m11"),
    ("met_n_nimbasa", "unova_m12"), ("BOLT", "unova_m13"), ("QUAKE", "unova_m14"), ("defeated_n_chargestone", "unova_m15"),
    ("JET", "unova_m16"), ("FREEZE", "unova_m17"), ("plasma_dragonspiral_cleared", "unova_m18"),
    ("heard_dragon_stones", "unova_m19"), ("LEGEND", "unova_m20"), ("beat_alder", "unova_m21"), ("defeated_n_castle", "unova_m22"),
    ("beat_unova_champion", None)]
_got = []
for _what, _want in _steps:
    if _what and _what.isupper():
        story.badges["UNOVA"].append(_what)
    elif _what:
        story.story_flags[_what] = True
    _main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
    _got.append((_main[0] if _main else None) == _want)
    if not _got[-1]:
        print("      after", _what, "shows", _main, "wanted", _want)
check(all(_got), "each story step shows the next mission")
_done = {m["id"] for m in story.get_all_journal_entries() if m["status"] == "COMPLETED"}
check({f"unova_m{i}" for i in range(1, 23)} <= _done, f"all 22 story missions marked done {sorted(_done)[:5]}")
_side = [m["id"] for m in story.get_active_missions() if m["type"] == "SIDE"]
check(len(_side) >= 12, f"after the story, side quests open {_side}")
_ms = g.loader.area_data["JOURNAL_MISSIONS"]
_areas = g.loader.area_data["STORY_PROGRESSION"]
check(all(m.get("target") in _areas for m in _ms if m["id"].startswith("unova_")), "every Unova mission points somewhere real")
check(all((m.get("condition") or {}).get("required_region") == "UNOVA" for m in _ms if m["id"].startswith("unova_")),
      "Unova's missions stay in Unova")
story.current_area_key = "VERMILLION_CITY"
check(not any(m["id"].startswith("unova_") for m in story.get_active_missions()), "and don't show in Kanto")
story.story_flags, _b, story.current_area_key = _saved
story.badges = _b
import json
print("14) Orre's levels follow its badge curve, from Espeon/Umbreon at 15/16 (Jordan, 11-01)")
from src.world import levels as _lv
_orre = [k for k, a in g.loader.area_data["STORY_PROGRESSION"].items() if (a or {}).get("region") == "ORRE"]
_missing = [k for k in _orre if k not in _lv._area_levels(g) and not g.loader.area_data["STORY_PROGRESSION"][k].get("level")]
check(not _missing, f"every Orre area has its own level {_missing}")
check(_lv.canon_area_level(g, "ORRE_DESERT") >= 14 and _lv.canon_area_level(g, "PYRITE_CAVE") < _lv.canon_area_level(g, "THE_UNDER")
      < _lv.canon_area_level(g, "SNAGEM_HIDEOUT") < _lv.canon_area_level(g, "REALGAM_TOWER"), "they rise through the story")
_willie = json.dumps(g.loader.area_data["STORY_PROGRESSION"]["OUTSKIRT_STAND"]).replace(" ", "")
check('"levels":[14]' in _willie, "Willie's first battle is near the starters' level")
print("15) Orre's Journal: the Colosseum + XD story in order (Jordan, 11-01)")
_saved = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key)
story.current_area_key = "OUTSKIRT_STAND"
story.badges["ORRE"] = []
for _k in list(story.story_flags):
    if not _k.startswith("visited_"):
        story.story_flags.pop(_k)
_steps = [(None, 1), ("orre_beat_willie", 2), ("phenac_cipher_beaten", 3), ("got_snag_machine", 4), ("PYRITE", 5),
          ("orre_miror_cave", 6), ("met_agate_elder", 7), ("orre_dakim_mt_battle", 8), ("cleared_the_under", 9),
          ("UNDER", 10), ("orre_ein_lab", 11), ("xd_lovrina_beaten", 12), ("xd_exol_beaten", 13),
          ("orre_snattle_phenac", 14), ("PHENAC", 15), ("beat_gonzap", 16), ("ORRE", 17), ("xd_gorigan_beaten", 18),
          ("beat_orre_champion", None)]
_ok = True
for _what, _n in _steps:
    if _what and _what.isupper():
        story.badges["ORRE"].append(_what)
    elif _what:
        story.story_flags[_what] = True
    _main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
    _want = f"orre_m{_n}" if _n else None
    if (_main[0] if _main else None) != _want:
        _ok = False
        print("      after", _what, "shows", _main, "wanted", _want)
check(_ok, "each story step shows the next mission")
_done = {m["id"] for m in story.get_all_journal_entries() if m["status"] == "COMPLETED"}
check({f"orre_m{i}" for i in range(1, 19)} <= _done, "all 18 story missions marked done")
_side = [m["id"] for m in story.get_active_missions() if m["type"] == "SIDE"]
check({"orre_s2", "orre_s3", "orre_s5"} <= set(_side), f"after the title: Mt. Battle, Jirachi, Citadark Isle {_side}")
_ms = [m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_")]
check(all(m.get("target") in g.loader.area_data["STORY_PROGRESSION"] for m in _ms), "every Orre mission points somewhere real")
story.story_flags, _b, story.current_area_key = _saved
story.badges = _b
print("16) Orre's Pokemon Center and Mart from Pokemon Orre, for all its towns (Jordan, 11-01)")
from src.states import overworld as _ow2
from src.states.systems import PokeMartState as _PM2
_shots = []
for _area in ("PHENAC_CITY", "AGATE_VILLAGE"):
    story.current_area_key = _area
    _town = _ow2.CityState(g); g.change_state(_town)
    _c = _ow2.PokeCenterState(g, _town)
    _m = _PM2(g, _town)
    _shots.append((_c.bg, _m.bg))
    check(getattr(_c, "generic_bg", False) and _c.nurse_sprite is None, f"{_area}: Nurse Joy is in the picture")
_want_c = _pg.transform.scale(g.assets.get_background("orre_center.png"), _shots[0][0].get_size())
_want_m = _pg.transform.scale(g.assets.get_background("orre_mart.png"), _shots[0][1].get_size())
_same = lambda a, b: _pg.image.tobytes(a, "RGB") == _pg.image.tobytes(b, "RGB")
check(all(_same(c, _want_c) and _same(m, _want_m) for c, m in _shots), "every Orre town: the same Center and Mart")
story.current_area_key = "SANTALUNE_CITY"
check(g.assets.get_region_building("KALOS", "mart") is not None, "Kalos keeps its one Center (shop inside)")
check(g.assets.get_region_building("KANTO", "center") is None, "Kanto keeps each town's own")
print("17) Orre starts with Espeon and Umbreon: pick a lead, the other comes along (Jordan, 11-01)")
from src.states.menus import StarterSelectionState as _SS
_saved_team = list(story.player_team)
story.current_area_key = "OUTSKIRT_STAND"
story.player_team = []
for _f in ("received_starter_orre", "has_orre_starter"):
    story.story_flags.pop(_f, None)
_ss = _SS(g, starter_ids=story.get_region_start("ORRE")["starters"], region="ORRE")
g.change_state(_ss)
_ss.load_starters()
_intro = list(_ss.dialogue_box.text_lines)
check(any("Cipher" in l for l in _intro) and any("Espeon and Umbreon" in l for l in _intro), f"the story set-up first ({len(_intro)} lines)")
_ss.selected_idx = [p.id for p in _ss.starters].index(197)
_ss.complete_selection()
_team = [p.id for p in story.player_team]
check(_team[:2] == [197, 196], f"Umbreon leads, Espeon comes along {_team}")
_lines = " ".join(str(l) for l in g.current_state.dialogue_box.text_lines) if getattr(g.current_state, "dialogue_box", None) else ""
check("ESPEON doesn't want to be left behind" in _lines, f"and says so: {_lines[:160]}")
story.player_team = _saved_team
print("18) Hoenn's journal: Professor Cozmo and Meteor Falls before Mt. Chimney (Jordan, 11-01)")
from src.world import guide as _g18
_saved18 = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key)
story.current_area_key = "HOENN_FIERY_PATH"
story.badges["HOENN"] = ["STONE", "KNUCKLE", "DYNAMO"]
for _f in ("heard_cozmo", "meteor_falls_cleared", "mt_chimney_boss_defeated"):
    story.story_flags.pop(_f, None)
for _f in ("badge_stone_earned", "badge_knuckle_earned", "badge_dynamo_earned", "oceanic_museum_cleared", "helped_wally"):
    story.story_flags[_f] = True
_main = lambda: next((m for m in story.get_active_missions() if m["type"] == "MAIN"), {})
_steps = []
for _flag, _want, _goal in ((None, "hoenn_m7b", "FALLARBOR_TOWN"), ("heard_cozmo", "hoenn_m7c", "HOENN_METEOR_FALLS"),
                            ("meteor_falls_cleared", "hoenn_m8", "HOENN_MT_CHIMNEY"), ("mt_chimney_boss_defeated", "hoenn_m9", None)):
    if _flag:
        story.story_flags[_flag] = True
    _m = _main()
    _steps.append((_m.get("id"), _g18.goal_area(g)))
    check(_m.get("id") == _want and (_goal is None or _g18.goal_area(g) == _goal),
          f"after {_flag or 'the Dynamo Badge'}: {_m.get('id')} -> {_g18.goal_area(g)}")
story.story_flags.pop("heard_cozmo"); story.story_flags.pop("meteor_falls_cleared"); story.story_flags.pop("mt_chimney_boss_defeated")
check(_g18.next_hop(g, "HOENN_FIERY_PATH") == "HOENN_ROUTE_112", f"from the Fiery Path the marker points back to Route 112 ({_g18.next_hop(g, 'HOENN_FIERY_PATH')})")
story.story_flags, _b18, story.current_area_key = _saved18
story.badges = _b18
print("19) the battle or event a Journal mission needs is gold (Jordan, 11-01)")
from src.world import guide as _g19
from src.states.overworld import CityState as _CS19
_saved19 = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key,
            {k: set(v) for k, v in story.defeated_trainers.items()})
story.badges["HOENN"] = ["STONE", "KNUCKLE", "DYNAMO"]
for _f in ("heard_cozmo", "meteor_falls_cleared", "mt_chimney_boss_defeated"):
    story.story_flags.pop(_f, None)
for _f in ("badge_stone_earned", "badge_knuckle_earned", "badge_dynamo_earned", "oceanic_museum_cleared", "helped_wally"):
    story.story_flags[_f] = True
story.defeated_trainers.pop("HOENN_METEOR_FALLS", None)
_g19._CACHE.clear()


def _labels(area, explore=True):
    story.current_area_key = area
    if g.loader.area_data["STORY_PROGRESSION"][area].get("area_type") == "town":
        c = _CS19(g); g.change_state(c); c.open_explore_menu()
        return [b.text for b in c.hover_buttons]
    p = PlayState(g); g.change_state(p); p.show_progression_menu()
    return [b.text for b in p.route_buttons if getattr(b, "route_group", "") == "explore"]


story.current_area_key = "FALLARBOR_TOWN"
_t = _labels("FALLARBOR_TOWN")
check(any(l.startswith("> ") and "Cozmo" in l for l in _t), f"Fallarbor: Talk to Cozmo is gold {_t}")
story.story_flags["heard_cozmo"] = True
_t = _labels("HOENN_METEOR_FALLS")
check(any(l.startswith("> ") and "TRAINER" in l for l in _t) and not any(l.startswith("> ") and "CATCH" in l for l in _t),
      f"Meteor Falls: BATTLE TRAINER is gold, catching isn't {_t}")
story.story_flags["meteor_falls_cleared"] = True
story.story_flags["mt_chimney_boss_defeated"] = True
_t = _labels("LAVARIDGE_TOWN")
check(any(l.startswith("> ") and "Gym" in l for l in _t), f"Lavaridge: the Gym is gold for the Heat Badge {_t}")
story.story_flags, _b19, story.current_area_key, story.defeated_trainers = _saved19
story.badges = _b19
print("20) Kalos's Journal: the X/Y story in order, and each step's place is open by then (Jordan, 11-01)")
from src.world import guide as _g20, hms as _hms20
_saved20 = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key, dict(story.inventory))
story.current_area_key = "VANIVILLE_TOWN"
story.badges["KALOS"] = []
for _k in list(story.story_flags):
    story.story_flags.pop(_k)
for _k in [k for k in story.inventory if k.startswith("HM_")]:
    story.inventory.pop(_k)
_steps = [(None, "kalos_m1"), ("defeated_rival_vaniville", "kalos_m2"), ("defeated_shauna_aquacorde", "kalos_m3"),
          ("BUG", "kalos_m4"), ("met_sycamore", "kalos_m5"), ("visited_PARFUM_PALACE", "kalos_m6"),
          ("glittering_cave_cleared", "kalos_m7"), ("CLIFF", "kalos_m8"), ("defeated_rival_mastery", "kalos_m9"),
          ("RUMBLE", "kalos_m10"), ("PLANT", "kalos_m11"), ("kalos_power_plant_cleared", "kalos_m12"),
          ("VOLTAGE", "kalos_m13"), ("FAIRY", "kalos_m14"), ("pokeball_factory_cleared", "kalos_m15"),
          ("frost_cavern_cleared", "kalos_m16"), ("PSYCHIC", "kalos_m17"), ("lysandre_labs_cleared", "kalos_m18"),
          ("geosenge_flare_cleared", "kalos_m19"), ("ICEBERG", "kalos_m20"), ("beat_kalos_champion", None)]
_order, _reach, _prev = [], [], "VANIVILLE_TOWN"
for _what, _want in _steps:
    if _what and _what.isupper():
        story.badges["KALOS"].append(_what)
        _hms20.give_for_badges(story)
    elif _what:
        story.story_flags[_what] = True
    _main = [m for m in story.get_active_missions() if m["type"] == "MAIN"]
    _order.append((_main[0]["id"] if _main else None) == _want)
    if not _order[-1]:
        print("      after", _what, "shows", [m["id"] for m in _main], "wanted", _want)
    if _main:
        _goal = _g20.goal_area(g)
        _open = _g20.path_to(g, _prev, _goal)
        _ok20 = bool(_open) and all(b in _g20.neighbours(g, a) for a, b in zip(_open, _open[1:]))
        _reach.append(_ok20)
        if not _ok20:
            print("      ", _main[0]["id"], "can't reach", _goal, "from", _prev, _open)
        _prev = _goal
check(all(_order), "each story step shows the next mission")
check(all(_reach), "and the way to it is open")
_done = {m["id"] for m in story.get_all_journal_entries() if m["status"] == "COMPLETED"}
check({f"kalos_m{i}" for i in range(1, 21)} <= _done, "all 20 story missions marked done")
_ms = [m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("kalos_")]
check(all(m.get("target") in g.loader.area_data["STORY_PROGRESSION"] for m in _ms), "every Kalos mission points somewhere real")
check(all((m.get("condition") or {}).get("required_region") == "KALOS" for m in _ms), "Kalos's missions stay in Kalos")
# the gates: Team Flare's steps can't be skipped
story.badges["KALOS"] = ["BUG", "CLIFF", "RUMBLE", "PLANT", "VOLTAGE", "FAIRY", "PSYCHIC"]
for _f in ("lysandre_labs_cleared", "geosenge_flare_cleared", "frost_cavern_cleared", "pokeball_factory_cleared"):
    story.story_flags.pop(_f, None)
check("GEOSENGE_FLARE_HQ" not in _g20.neighbours(g, "GEOSENGE_TOWN"), "Flare HQ waits on Lysandre Labs")
check("KALOS_ROUTE_17" not in _g20.neighbours(g, "DENDEMILLE_TOWN"), "Route 17 waits on Frost Cavern")
check("KALOS_ROUTE_15" not in _g20.neighbours(g, "LAVERRE_CITY") and "KALOS_ROUTE_16" not in _g20.neighbours(g, "LUMIOSE_CITY"),
      "Routes 15 and 16 wait on the Poké Ball Factory")
check("KALOS_ROUTE_18" not in _g20.neighbours(g, "ANISTAR_CITY"), "Route 18 waits on the Flare HQ")
_reqs = lambda a: g.loader.area_data["STORY_PROGRESSION"][a]["gym"]["requirements"]
check("glittering_cave_cleared" in _reqs("CYLLAGE_CITY").get("flags", []) and
      "kalos_power_plant_cleared" in _reqs("LUMIOSE_CITY").get("flags", []), "Grant and Clemont wait on Team Flare")
_km = [o for o in g.loader.area_data["STORY_PROGRESSION"]["TOWER_OF_MASTERY"]["route_menu"] if o.get("action") == "NPC"]
check(all(o.get("victory_flag") == "got_mega_ring" for o in _km), "the Mega Ring talk marks itself done")
story.current_area_key = "VERMILLION_CITY"
check(not any(m["id"].startswith("kalos_") for m in story.get_active_missions()), "and Kalos's missions don't show in Kanto")
story.story_flags, _b20, story.current_area_key, story.inventory = _saved20
story.badges = _b20
print("21) League Redo: after a second title, the first region's Leaders with six, Lv 80+ (Jordan, 11-01/02)")
from src.world import league_redo as _lr
from src.states.overworld import GymLobbyState as _GL21, CityState as _CS21, is_league as _isl21
from src.states.systems import BadgeCaseState as _BC21
_saved21 = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key,
            story.starting_region, story.player_team)
story.starting_region = "KANTO"
story.story_flags = {k: v for k, v in story.story_flags.items() if not k.startswith(("redo_", "league_redo_"))}
story.story_flags.pop("beat_johto_champion", None)
story.story_flags["beat_champion"] = True
_prog = g.loader.area_data["STORY_PROGRESSION"]
_kgyms = _lr.gyms(story, "KANTO")[0]
story.badges["KANTO"] = [b for _k, b in _kgyms]
check(len(_kgyms) == 8, f"Kanto has 8 Gyms {[k for k, _b in _kgyms]}")
check(_lr.redo_region(story) is None, "one title: no League Redo yet")
story.story_flags["beat_johto_champion"] = True
check(_lr.redo_region(story) == "KANTO", "a second title opens Kanto's")
story.current_area_key = "VIRIDIAN_CITY"
_city = _CS21(g); g.change_state(_city)
_said = " ".join(str(l) for l in (getattr(_city.dialogue_box, "text_lines", None) or [])) if getattr(_city, "dialogue_box", None) else ""
check(story.story_flags.get("league_redo_told_KANTO") and "Professor Oak" in " ".join(_lr.call_lines(story, "KANTO")),
      "back in Kanto, Professor Oak calls")
check(not _lr.take_call(story, "KANTO"), "only once")
_m = next((m for m in story.get_active_missions() if m["type"] == "MAIN"), {})
check(_m.get("id") == "league_redo_kanto" and _m.get("target") == _kgyms[0][0], f"the Journal tracks it {_m.get('id')} -> {_m.get('target')}")
# a Gym (the last one first: any order)
_gk, _gb = _kgyms[-1]
story.current_area_key = _gk
_lob = _GL21(g); g.change_state(_lob)
check(_lob.redo and _lob.next_opponent is _lob.leader, f"{_gk}: the Leader waits, League Redo ({_lob.status_text})")
story.player_team = [_mon(150, 100, ["PSYCHIC"])]
_lob.challenge_gym()
_bs = g.current_state
_bs = getattr(_bs, "battle_state", None) or getattr(_bs, "next_state", None) or _bs
_team = getattr(_bs, "enemy_team", None) or getattr(_bs, "opponent_team", None) or []
check(len(_team) == 6 and all(p.level == 100 for p in _team), f"six at level 100 {[(p.name, p.level) for p in _team]}")
check(getattr(_bs, "victory_flag", None) == _lr.badge_flag("KANTO", _gb) and not getattr(_bs, "badge_reward", None),
      f"a win stars the badge ({getattr(_bs, 'victory_flag', None)})")
check(not any(_lr.is_legendary(p.id) for p in _team) and all(p.id <= 151 for p in _team),
      "no legendaries, and Kanto's own Pokemon (Gen 1)")
g.transitioning = False
story.story_flags[_lr.badge_flag("KANTO", _gb)] = True
check(not _GL21(g).redo, "won again: that Gym is done")
_bc = _BC21(g, _city); _bc.current_page_idx = _bc.unlocked_regions.index("KANTO")
_pocket = _bc.region_maps["KANTO"][_gb]
check(_bc._starred("KANTO", _pocket) and not any(_bc._starred("KANTO", i) for i in range(1, 9) if i != _pocket),
      f"the Badge Case stars it (pocket {_pocket})")
_bc.draw()
# all eight: the League at full strength
for _k, _b in _kgyms:
    story.story_flags[_lr.badge_flag("KANTO", _b)] = True
check(_lr.league_open(story, "KANTO"), "all 8 won again: the League is next")
_lk = _lr.gyms(story, "KANTO")[1]
story.current_area_key = _lk
story.story_flags[f"gym_progress_{_lk}"] = 0
_lob = _GL21(g); g.change_state(_lob)
check(_lob.redo and "League Redo" in _lob.status_text, f"{_lk}: {_lob.status_text}")
_lob.challenge_gym()
_bs = g.current_state
_bs = getattr(_bs, "battle_state", None) or getattr(_bs, "next_state", None) or _bs
_team = getattr(_bs, "enemy_team", None) or getattr(_bs, "opponent_team", None) or []
check(len(_team) == 6 and all(p.level == 100 for p in _team), f"the Elite Four too {[(p.name, p.level) for p in _team]}")
g.transitioning = False
_m = next((m for m in story.get_active_missions() if m["type"] == "MAIN"), {})
check(_m.get("target") == _lk, f"the Journal points at the League now ({_m.get('target')})")
story.story_flags[_lr.champion_flag("KANTO")] = True
check(not _lr.league_open(story, "KANTO") and not _GL21(g).redo, "the Champion beaten again: back to normal rematches")
check(not any(m["id"] == "league_redo_kanto" for m in story.get_active_missions()), "and the mission is done")
story.story_flags, _b21, story.current_area_key, story.starting_region, story.player_team = _saved21
story.badges = _b21
print("22) Zones: the Wild Areas, Isle of Armor, Crown Tundra and Area Zero in parts, each its own picture (Jordan, 11-01)")
from src.states.overworld import PlayState as _PS22
_saved22 = (dict(story.story_flags), story.current_area_key)


def _zone_buttons(area):
    story.current_area_key = area
    p = _PS22(g); g.change_state(p)
    p.show_progression_menu()
    return p, [b for b in p.route_buttons if b.text.replace("> ", "").startswith("TO ")]


for _a, _n in (("WILD_AREA", 2), ("WILD_AREA_NORTH", 2), ("ISLE_OF_ARMOR", 5), ("CROWN_TUNDRA", 4), ("AREA_ZERO", 4)):
    story.story_flags.pop(f"zone_{_a}", None)
    _p, _btns = _zone_buttons(_a)
    check(len(_btns) == _n - 1 and all(b.route_group == "travel" for b in _btns),
          f"{_a}: a TO button for each other zone, under TRAVEL {[b.text for b in _btns]}")
_p, _btns = _zone_buttons("WILD_AREA")
check(_p._zone()["key"] == "rolling_fields" and "Rolling Fields" in " ".join(_p._route_prompt()),
      f"the Wild Area starts in Rolling Fields ({_p._route_prompt()[0]})")
_before = _p.route_bg.copy() if _p.route_bg else None
_p.action_switch_zone("lake_miloch")
check(story.story_flags.get("zone_WILD_AREA") == "lake_miloch", "TO LAKE MILOCH moves there")
check(_p.route_bg is not None and _before is not None and _p.route_bg.get_at((640, 200)) != _before.get_at((640, 200)),
      "and the picture changes with it")
_p, _btns = _zone_buttons("WILD_AREA")
check([b.text.replace("> ", "") for b in _btns] == ["TO ROLLING FIELDS"], f"and it stays there {[b.text for b in _btns]}")
for _a in ("WILD_AREA", "WILD_AREA_NORTH", "ISLE_OF_ARMOR", "CROWN_TUNDRA"):
    _zs = g.loader.area_data["STORY_PROGRESSION"][_a]["zones"]
    _miss = [z["key"] for z in _zs if not g.assets.get_journeys_background("routes", f"{_a}_{z['key']}")]
    check(not _miss, f"{_a}: every zone has its picture {_miss}")
story.story_flags, story.current_area_key = _saved22
print("23) Gym challenges: a minigame in place of the trainers, the same one until it's won (Jordan, 11-01)")
from src import minigames as _mg
from src.minigames.base import Minigame as _MG
from src.states.overworld import GymLobbyState as _GL23
_saved23 = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, story.current_area_key,
            story.player_team, story.balls_left)
check(len(_mg.GAMES) >= 10, f"a stable of games {sorted(_mg.GAMES)}")
# Greater than / less than (Jordan, 11-06): "8 ? 4" (<, = or >), "8 > ?" (one number makes it true), and
# sums on both sides at the higher levels; always right, always the buttons asked for.
import re as _re1106
_val = lambda t: eval(t.replace("x", "*").replace("÷", "/"))
_bad, _seen1106 = 0, {"compare": set(), "fill": 0, "eq": 0}
for _lvl in range(1, 9):
    for _i in range(600):
        _n = 3 if _i % 2 else 4
        _p, _a, _o = g.math.generate(_lvl, _n)
        if _o == ["<", "=", ">"]:
            _l, _r = _p.split(" ? ")
            _want = "<" if _val(_l) < _val(_r) else ">" if _val(_l) > _val(_r) else "="
            _bad += _want != _a
            _seen1106["eq"] += _a == "="
            _seen1106["compare"].add((_lvl, "+" in _l or "-" in _l or "x" in _l, "+" in _r or "-" in _r or "x" in _r))
        elif _re1106.search(r"[<>]", _p):
            _true = [x for x in _o if _val(_p.replace("?", str(x)))]
            _bad += _true != [_a] or len(_o) != 3 or not (_o[0] < _o[1] < _o[2])  # lower, the same, higher
            _seen1106["fill"] += 1
        else:
            _bad += len(_o) != _n
check(_bad == 0 and _seen1106["fill"] and _seen1106["eq"], f"comparisons: always right ({_bad} wrong), = sometimes, 8 > ? too (lower, 8, higher)")
check((1, False, False) in _seen1106["compare"] and (8, True, True) in _seen1106["compare"]
      and not any(l and r for lv, l, r in _seen1106["compare"] if lv == 1), "plain numbers at first, a sum on each side later")
from src.minigames.kanto import KogaWalls as _KW
_kw = _KW(g, lambda w: None, level=2, seed=5)
_n1106 = next(c for c, (_t, ok) in zip(_kw.counts, _kw.options) if ok)
_sum = _re1106.search(r"with (.+) footprints", _kw.prompt).group(1)
check(_re1106.search(r"\d+ [-+x] \d+", _sum) and _val(_sum) == _n1106, f"Koga's paths: a sum to work out ({_kw.prompt})")

import src.minigames.base as _MGB
for _k, _cls in _mg.GAMES.items():  # each one starts, plays a while, and can lose and try again
    _m = _cls(g, lambda won: None, level=3, leader={"name": "Brock", "team": [74, 95]}, partner=25, seed=4)
    g.change_state(_m)
    _m.buttons[0][3]()
    for _f in range(120):
        if _f % 7 == 0:
            _m.on_tap((100 + (_f * 37) % 1080, 140 + (_f * 53) % 540))
        _m.update()
        _m.draw()
        if _m.phase != "PLAY":
            break
    _ok = _m.phase in ("PLAY", "WON", "LOST")
    if _m.phase == "LOST":
        _m.buttons[0][3]()
        _ok = _m.phase == "PLAY" and _m.progress()[0] == 0
    check(_ok, f"{_k}: plays and tries again ({_m.phase})")
    if _k in _MGB.SCENES:  # its pixel-art scene: drawn, alive (it changes from frame to frame)
        _shot = g.screen.copy()
        for _f in range(30):
            _m.update()
        _m.draw()
        check(_m.backdrop is not None and g.screen.get_at((g.width // 2, g.height - 4)) != (0, 0, 0)
              and pygame.image.tostring(_shot, "RGB") != pygame.image.tostring(g.screen, "RGB"),
              f"{_k}: its scene ({_MGB.SCENES[_k]}) behind it, alive")
story.current_area_key = "PEWTER_CITY"
story.badges["KANTO"] = []
for _f in [f for f in story.story_flags if f.startswith(("gym_challenge", "gym_progress_PEWTER"))]:
    story.story_flags.pop(_f)
_lob = _GL23(g, None); g.change_state(_lob)
check(_lob.challenge is not None and "Gym Challenge" in _lob.status_text, f"Pewter: {_lob.status_text}")
_first = story.story_flags.get(_mg.picked_flag("PEWTER_CITY"))
_lob.challenge_gym()
check(isinstance(g.current_state, _MG) and g.current_state.key == _first, f"CHALLENGE plays it ({g.current_state.key})")
g.current_state.buttons[0][3]()
g.current_state.lose("test")
g.current_state.buttons[1][3]()  # LEAVE
_lob = g.current_state
check(isinstance(_lob, _GL23) and _lob.challenge and _lob.challenge.key == _first, "lost: back in the lobby, the same game")
_balls = story.balls_left
_lob.challenge_gym()
g.current_state.buttons[0][3]()
g.current_state.win()
g.current_state.buttons[0][3]()  # CONTINUE
_lob = g.current_state
check(story.story_flags.get(_mg.done_flag("PEWTER_CITY")) and not _lob.challenge and _lob.next_opponent is _lob.leader,
      f"won: the Leader is next ({_lob.status_text})")
check(story.balls_left > _balls, "and the trainers' Poke Balls come with it")
story.badges["KANTO"] = ["BOULDER"]
story.story_flags.pop(_mg.done_flag("PEWTER_CITY"))
check(not _GL23(g, None).challenge, "a Gym already beaten has no challenge")
from src.states.game_corner import GymGamesState as _GGS, coins as _coins1106
story.story_flags[_mg.done_flag("PEWTER_CITY")] = True
story.story_flags[_mg.picked_flag("PEWTER_CITY")] = "flight"
_ggs = _GGS(g, g.current_state)
check(("flight", "PEWTER_CITY") in _mg.beaten(g) and any("PIKAFLY" in b.text.upper() for b in _ggs.buttons),
      "the Game Corner's GYM GAMES: a game won at a Gym is there to play again")
_c0 = _coins1106(story)
_ggs.play("flight", "PEWTER_CITY")
_m = g.current_state
_m.buttons[0][3]()
_m.win()
_m.buttons[0][3]()
check(isinstance(g.current_state, _GGS) and _coins1106(story) == _c0 + 50, "won again: 50 coins, back to the list")
story.story_flags.pop(_mg.done_flag("PEWTER_CITY"))

check([_mg.pick(g, k, []).key for k in ("VERMILLION_CITY", "FUCHSIA_CITY", "SAFFRON_CITY", "CINNABAR_ISLAND")]
      == ["surge", "koga", "sabrina", "quiz"], "Kanto's puzzle Gyms keep their own challenges, drawn as games")
check(all(not _mg.GAMES[k].in_pool for k in ("surge", "koga", "sabrina", "quiz")) and _mg.GAMES["chase"].in_pool,
      "and only there; the chase is in the pool")
_titles = {}
for _area in ("PEWTER_CITY", "RUSTBORO_CITY", "STRIATON_CITY"):
    story.current_area_key = _area
    _titles[_area] = (_mg.GAMES["flight"].title_for(g), _mg.GAMES["chase"].title_for(g))
check(_titles["PEWTER_CITY"] == ("Pikafly", "Magikarp Escape") and _titles["RUSTBORO_CITY"] == ("Pikafly", "Feebas Escape")
      and _titles["STRIATON_CITY"][1] != _titles["PEWTER_CITY"][1], f"each region's own Pokemon {_titles}")
story.current_area_key = "RUSTBORO_CITY"
_tc = _mg.GAMES["typeclash"](g, lambda w: None, leader={"name": "Roxanne", "team": [74]})
check(_tc.species == {"GRASS": 252, "FIRE": 255, "WATER": 258}, f"Type Clash in Hoenn: Treecko, Torchic, Mudkip {_tc.species}")
check(all(_mg.GAMES[k].controls for k in _mg.GAMES), "every game shows its controls")
_tc.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(5, 5), button=1)])
check(_tc.phase == "INTRO", "the controls card waits for GOT IT!")
_tc.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="")])
check(_tc.phase == "PLAY", "(or Enter)")
story.story_flags, _b23, story.current_area_key, story.player_team, story.balls_left = _saved23
story.badges = _b23
print("24) Game Corner: coins, Slots and Voltorb Flip from the fan games' set, the Prize Counter (Jordan, 11-01)")
import random as _r24
from src.states import game_corner as _gc
_saved24 = (dict(story.story_flags), story.money, story.current_area_key, list(story.player_team))
story.current_area_key = "CELADON_CITY"
story.story_flags.pop(_gc.COINS_FLAG, None)
story.money = 5000
_line = _gc.buy_coins(story)
check(_gc.coins(story) == 50 and story.money == 4000, f"50 coins for $1,000 ({_line})")
story.money = 30000
_m = _gc.buy_coins(story, 500)
check(_gc.coins(story) == 550 and story.money == 20000, f"500 coins for $10,000 ({_m})")
_m = _gc.buy_coins(story, 1000)
check(_gc.coins(story) == 1550 and story.money == 0, f"1,000 coins for $20,000 ({_m})")
check("You need $1,000" in _gc.buy_coins(story, 50) and _gc.coins(story) == 1550, "no money: no coins")
from src.states.systems import GameCornerState as _GCS
story.inventory["COIN_CASE"] = 1
story.money = 1500
_gcs = _GCS(g, None); g.change_state(_gcs); _gcs.show_main_menu()
_packs = {b.text: (b.sub, b.callback is not None) for b in _gcs.menu_buttons if "COINS" in b.text}
check(_packs == {"50 COINS": ("$1,000", True), "100 COINS": ("$2,000", False), "500 COINS": ("$10,000", False),
                 "1,000 COINS": ("$20,000", False)}, f"the counter: 50 / 100 / 500 / 1,000 with prices, too dear greyed ({_packs})")
story.money = 4000
story.story_flags[_gc.COINS_FLAG] = 50
check(_gc.line_pay("RED7", "RED7", "RED7") == 300 and _gc.line_pay("RED7", "BLUE7", "RED7") == 90
      and _gc.line_pay("PIKACHU", "PIKACHU", "PIKACHU") == 15 and _gc.line_pay("CHERRY", "PSYDUCK", "RED7") == 2
      and _gc.line_pay("CHERRY", "CHERRY", "RED7") == 4 and _gc.line_pay("REPLAY", "REPLAY", "REPLAY") == "REPLAY"
      and _gc.line_pay("PSYDUCK", "RED7", "CHERRY") == 0, "the machine's payout table")
_sl = _gc.SlotsState(g, g.current_state, rng=_r24.Random(3))
g.change_state(_sl)
_sl.place_bet(3)
check(_gc.coins(story) == 47 and _sl.bet == 3, "a 3-coin bet lights 3 lines' worth")
_sl.spin()
for _i in range(3):
    _sl.update(); _sl.stop_reel(_i)
for _f in range(60):
    _sl.update()
_sl.draw()
check(not any(_sl.spinning) and _gc.coins(story) == 47 + _sl.payout, f"STOP, STOP, STOP: paid {_sl.payout}")
story.story_flags[_gc.LEVEL_FLAG] = 1
_vf = _gc.VoltorbFlipState(g, g.current_state, rng=_r24.Random(5))
g.change_state(_vf)
_rows, _cols = _vf._sums()
check(sum(p for p, _ in _rows) == sum(sum(r) for r in _vf.board) and sum(b for _, b in _cols) == sum(r.count(0) for r in _vf.board),
      "the hints add up (points and Voltorb per row and column)")
_before = _gc.coins(story)
for _rr in range(5):
    for _cc in range(5):
        if _vf.board[_rr][_cc] > 0:
            _vf.flip(_cc, _rr)
for _f in range(12):
    _vf.update()
check(_vf.over == "WIN" and _gc.coins(story) > _before and _vf.level == 2, f"every 2 and 3 found: level cleared ({_vf.message})")
_vf.new_round()
_bomb = next((c, r) for r in range(5) for c in range(5) if _vf.board[r][c] == 0)
_vf.flip(*_bomb)
for _f in range(12):
    _vf.update()
_vf.draw()
check(_vf.over == "BOOM" and _vf.round_coins == 0 and _vf.level == 1, f"a Voltorb: the round's coins are lost ({_vf.message})")
_gc.add_coins(story, 200)
_pc = _gc.PrizeCounterState(g, g.current_state)
_n = len(story.player_team) + len([p for p in story.pc_pokemon if p])
_pc.buy(("POKEMON", 63, 180))
check(len(story.player_team) + len([p for p in story.pc_pokemon if p]) == _n + 1, f"a prize Pokemon ({_pc.message})")
story.story_flags, story.money, story.current_area_key, story.player_team = _saved24
print("25) Tile puzzles (Gyms and the Ruins of Alph) and Blackjack (Jordan, 11-01)")
import random as _r25
from src import minigames as _mg25
from src.minigames.tiles import TilePuzzle as _TP, AlphPuzzle as _AP, flag as _alph_flag
from src.states import game_corner as _gc25
_saved25 = (dict(story.story_flags), story.current_area_key)
check("tiles" in _mg25.GAMES and _mg25.GAMES["tiles"].in_pool, "the Tile Puzzle is in the Gym rotation")
_t = _TP(g, lambda w: None, level=5, leader={"name": "Brock", "team": [74, 95]}, seed=1)
check(_t.title == "Onix Puzzle" and _t.n == 4, f"the Leader's ace is the picture ({_t.title}, {_t.n} x {_t.n})")
_t3 = _TP(g, lambda w: None, level=0, leader={"name": "Falkner", "team": [16, 17]}, seed=1)
check(_t3.n == 3 and _t3.title == "Pidgeotto Puzzle", "early Gyms: 3 x 3")
_t.buttons[0][3]()
for _i in range(16):
    _t._use(next(k for k, v in _t.spots.items() if v == _i))
    _t._use(("B", _i))
check(_t.phase == "WON", "every piece in place: won")
_a = _AP(g, lambda w: None, panel="hooh", seed=2)
check(_a.title == "Ho-Oh Panel" and _a.WALL == "bg_hooh.png" and _a.n == 4, f"the Ho-Oh chamber's own panel ({_a.title})")
story.current_area_key = "RUINS_OF_ALPH"
story.story_flags.pop(_alph_flag("kabuto"), None)
_alph = [o for o in g.loader.area_data["STORY_PROGRESSION"]["RUINS_OF_ALPH"]["explore_options"] if o.get("action") == "TILE_PUZZLE"]
check([o["panel"] for o in _alph] == ["kabuto", "omanyte", "aerodactyl", "hooh"], "the Ruins of Alph's four chambers")
from src.states.overworld import CityState as _CS25
_city = _CS25(g)
g.change_state(_city)
_city.solve_alph_panel("kabuto")
_ap = g.current_state
check(isinstance(_ap, _AP), "a chamber opens its puzzle")
_ap.buttons[0][3]()
_ap.win()
_ap.buttons[0][3]()
check(story.story_flags.get(_alph_flag("kabuto")) and g.current_state is _city, "solved: it stays solved")
check(_gc25.hand_total([("A", "spade"), ("K", "heart")]) == (21, True) and _gc25.blackjack([("A", "spade"), ("10", "club")])
      and _gc25.hand_total([("A", "spade"), ("9", "heart"), ("5", "club")]) == (15, False), "Blackjack hand totals (an Ace is 1 or 11)")
story.story_flags[_gc25.COINS_FLAG] = 100
_bj = _gc25.BlackjackState(g, g.current_state, rng=_r25.Random(7))
g.change_state(_bj)
_bj.add_bet(10)
_bj.deal()
for _f in range(200):
    _bj.update()
    if _bj.phase == "PLAY":
        _bj.stand()
    if _bj.phase == "DONE":
        break
_bj.draw()
check(_bj.phase == "DONE" and _gc25.coins(story) in (90, 100, 110, 115), f"a hand plays out and pays ({_bj.message}, {_gc25.coins(story)} coins)")
story.story_flags, story.current_area_key = _saved25
print("26) The Pokemon Tower in four floors; the Black Fog ambushes on the stairs (Jordan, 11-02)")
from src.states.overworld import PlayState as _PS26
_saved26 = (dict(story.story_flags), story.current_area_key, {k: set(v) for k, v in story.defeated_trainers.items()},
            dict(story.inventory))
story.current_area_key = "KANTO_POKEMON_TOWER"
story.inventory["SILPH_SCOPE"] = 1
for _f in ("tower_ghost_defeated", "black_fog_banished_kanto_pokemon_tower"):
    story.story_flags.pop(_f, None)
story.story_flags["defeated_rival_tower"] = True  # (the rival met at the door: done)
story.defeated_trainers.pop("KANTO_POKEMON_TOWER", None)


def _floor(n):
    story.story_flags["zone_KANTO_POKEMON_TOWER"] = f"floor_{n}"
    p = _PS26(g); g.change_state(p); p.show_progression_menu()
    return p, [b.text.replace("> ", "") for b in p.route_buttons]


_p, _f1 = _floor(1)
_p4, _f4 = _floor(4)
check("UP TO 2F" in _f1 and "Lavender Town" in _f1 and not any("DOWN" in t for t in _f1), f"1F: up the stairs or out {_f1}")
check("DOWN TO 3F" in _f4 and "Lavender Town" not in _f4 and not any("UP TO" in t for t in _f4), f"4F: the top {_f4}")
check(not any("BLACK FOG" in t for n in (1, 2, 3, 4) for t in _floor(n)[1]), "no Black Fog option on any floor")
check(all(g.assets.get_journeys_background("routes", f"KANTO_POKEMON_TOWER_floor_{n}") for n in range(1, 5)),
      "each floor has its own picture")
_pool = g.loader.area_data["STORY_PROGRESSION"]["KANTO_POKEMON_TOWER"]["trainer_pool"]
for _i, _t in enumerate(_pool):
    if _t.get("zone") == "floor_4":
        story.defeated_trainers.setdefault("KANTO_POKEMON_TOWER", set()).add(_i)
check("CONFRONT GHOST" in _floor(3)[1] and "CONFRONT GHOST" not in _floor(4)[1],
      "the ghost on the stairs at 3F, before Team Rocket's floor (Jordan, 11-07: as in the games)")
_tower = g.loader.area_data["STORY_PROGRESSION"]["KANTO_POKEMON_TOWER"]
_chance = _tower["zone_ambush"]["chance"]
_tower["zone_ambush"]["chance"] = 1.0
_p, _ = _floor(1)
_p.dialogue_box.visible = False  # (the arrival message, read)
said.clear()
_p.action_switch_zone("floor_2")
_said = " ".join(map(str, said[-1][0])) if said else ""
check("lights go out" in _said and said and said[-1][1] is not None, f"changing floors can bring the Black Fog ({_said[:60]})")
story.story_flags["black_fog_banished_kanto_pokemon_tower"] = True
_p, _ = _floor(1)
_p.dialogue_box.visible = False  # (the arrival message, read)
said.clear()
_p.action_switch_zone("floor_2")
_said = " ".join(map(str, said[-1][0])) if said else ""
check("lights go out" not in _said and "2F" in _said, f"not once it's banished ({_said[:70]})")
_tower["zone_ambush"]["chance"] = _chance
story.story_flags, story.current_area_key, story.defeated_trainers, story.inventory = _saved26
print("27) Regional forms: plain names; only the region's own forms count for Area Complete (Jordan, 11-02)")
from src.world import regional_forms as _rf27
from src.pokemon.loader import PokemonLoader as _PL27
from src.states.overworld import PlayState as _PS27
_saved27 = (dict(story.story_flags), story.current_area_key)
check(g.loader.fetch_specific(2001)["display_name"].upper() == "RATTATA", f"Alolan Rattata is just RATTATA ({g.loader.fetch_specific(2001)['display_name']})")
check(_PL27.plain_name("ALOLAN RATTATA") == "RATTATA" and _PL27.plain_name("Galarian Zigzagoon") == "Zigzagoon"
      and _PL27.plain_name("Mr. Mime") == "Mr. Mime", "older saves' Pokedex names lose the prefix too")
_fm = g.loader.area_data["FORM_MAP"]
_alolan = next(int(k) for k, m in _fm.items() if m.get("form") == "alolan")
_galarian = next(int(k) for k, m in _fm.items() if m.get("form") == "galarian")
story.current_area_key = "HAUOLI_CITY"
_in_alola = (_rf27.counts_for_area(g, _alolan), _rf27.counts_for_area(g, _galarian), _rf27.counts_for_area(g, 19))
story.current_area_key = "HOENN_ROUTE_101"
_in_hoenn = (_rf27.counts_for_area(g, _alolan), _rf27.counts_for_area(g, _galarian), _rf27.counts_for_area(g, 263))
check(_in_alola == (True, False, True) and _in_hoenn == (False, False, True),
      f"own forms count, other regions' don't (Alola {_in_alola}, Hoenn {_in_hoenn})")
story.current_area_key = "KANTO_POKEMON_TOWER"
story.story_flags["defeated_rival_tower"] = True
story.story_flags["zone_KANTO_POKEMON_TOWER"] = "floor_2"
_pt = _PS27(g); g.change_state(_pt); _pt.show_progression_menu()
_stairs = [b for b in _pt.route_buttons if "UP TO" in b.text or "DOWN TO" in b.text]
check(_stairs and all(b.route_group == "explore" for b in _stairs), f"the tower's stairs are under EXPLORE {[b.text for b in _stairs]}")
story.story_flags, story.current_area_key = _saved27
print("28) The Black Fog returns and scales; League rematches Lv 70+; the League Redo Lv 80+ (Jordan, 11-02)")
import datetime as _dt28
import random as _r28
from src.world import black_fog as _bf
from src.world import league_redo as _lr28
from src.states import overworld as _ow28
_saved28 = (dict(story.story_flags), story.player_team)
_tower = g.loader.area_data["STORY_PROGRESSION"]["KANTO_POKEMON_TOWER"]
_flag = _bf.fog_flag(_tower)
check(_flag == "black_fog_banished_kanto_pokemon_tower", f"the tower's Black Fog is found ({_flag})")


class _Always:
    def random(self):
        return 0.0


story.story_flags[_flag] = True
story.story_flags.pop("black_fog_back_KANTO_POKEMON_TOWER", None)
_day = _dt28.date(2026, 11, 2)
_back = _bf.maybe_return(story, "KANTO_POKEMON_TOWER", _tower, rng=_Always(), today=_day)
check(_back and not story.story_flags.get(_flag), "banished, it can gather again on entry")
story.story_flags[_flag] = True
check(not _bf.maybe_return(story, "KANTO_POKEMON_TOWER", _tower, rng=_Always(), today=_day), "but not twice in one day")
check(_bf.maybe_return(story, "KANTO_POKEMON_TOWER", _tower, rng=_Always(), today=_day + _dt28.timedelta(days=1)),
      "and again the next day")
_n = 0
for _i in range(400):
    story.story_flags[_flag] = True
    _n += bool(_bf.maybe_return(story, f"T{_i}", _tower, rng=_r28.Random(_i), today=_day))
check(20 <= _n <= 60, f"about 10% of entries ({_n} of 400)")
story.player_team = [_mon(25, 47, ["TACKLE"]), _mon(150, 61, ["TACKLE"])]
check(_bf.level(story) == 63, f"it's as strong as your ace: Lv {_bf.level(story)}")
check(_ow28.league_rematch_levels(story, [55, 58, 60]) == [70, 70, 70], "rematches: everyone at least Lv 70")
story.player_team = [_mon(150, 88, ["TACKLE"])]
check(_ow28.league_rematch_levels(story, [72, 75, 78]) == [82, 85, 88], "and up to your ace once it's above 80")
story.player_team = [_mon(150, 60, ["TACKLE"])]
check(_lr28.redo_level(story) == 80, "the League Redo: at least Lv 80")
story.player_team = [_mon(150, 93, ["TACKLE"])]
check(_lr28.redo_level(story) == 93, "or your ace's level above that")
check(any("at least level 80" in l for l in _lr28.call_lines(story, "KANTO")), "and the professor says so")
story.story_flags, story.player_team = _saved28
print("29) Kanto's catch missions count Kanto species owned, paid once each (Jordan, 11-02)")
_saved29 = (dict(story.story_flags), story.money, dict(g.data.data.get("pokedex", {})))
for _k in [k for k in story.story_flags if k.startswith("kanto_catch_")]:
    story.story_flags.pop(_k)
g.data.data["pokedex"] = {str(_i): {"id": _i} for _i in range(1, 65)}
g.data.data["pokedex"].update({str(_i): {"id": _i} for _i in range(152, 182)})  # other regions don't count
_m0 = story.money
_lines = story.catch_milestones()
check(story.story_flags.get("kanto_catch_30") and story.story_flags.get("kanto_catch_60")
      and not story.story_flags.get("kanto_catch_90") and story.money - _m0 == 100000,
      f"64 Kanto species: the 30 and 60 bonuses ({_lines})")
check(story.catch_milestones() == [] and story.money - _m0 == 100000, "and only once")
_cm = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"] if str(m.get("id", "")).startswith("cm")}
if _cm:
    _ui = story._prepare_mission_for_ui(_cm["cm90"])
    check("(64/90)" in _ui["text"], f"the next one shows progress ({_ui['text']})")
story.story_flags, story.money = _saved29[0], _saved29[1]
g.data.data["pokedex"] = _saved29[2]

print("30) IVs: at least 2 at 31, legendaries 4, gifts all 6; every form goes by its plain name (Jordan, 11-02)")
from src.world import story_events as _se30
_saved30 = (list(story.player_team), list(story.pc_pokemon))
_p31 = lambda m: sum(1 for v in m.ivs.values() if v == 31)
_wild = [Pokemon(g.loader.fetch_specific(19), g.assets) for _ in range(30)]
_leg = [Pokemon(g.loader.fetch_specific(150), g.assets) for _ in range(30)]
check(min(map(_p31, _wild)) >= 2, f"every Pokemon has at least 2 perfect IVs (fewest {min(map(_p31, _wild))})")
check(min(map(_p31, _leg)) >= 4, f"a legendary at least 4 (fewest {min(map(_p31, _leg))})")
story.player_team = story.player_team[:1]
_se30.gift_pokemon(g, 133)
check(_p31(story.player_team[-1]) == 6, "a gift Pokemon has all six at 31")
_ow30 = PlayState(g); _l30 = []; _ow30._gift_pokemon(25, _l30)
check(_p31(story.player_team[-1]) == 6, "from the town gift helper too")
_old = {"HP": 3, "ATTACK": 9, "DEFENSE": 20, "SPATK": 1, "SPDEF": 2, "SPEED": 4}
_m30 = Pokemon(g.loader.fetch_specific(19), g.assets); _m30.ivs = dict(_old); _m30.floor_ivs()
check(_p31(_m30) == 2 and _m30.ivs["DEFENSE"] == 31 and _m30.ivs["ATTACK"] == 31 and _m30.ivs["HP"] == 3,
      f"an older save's Pokemon: its two best raised ({_m30.ivs})")
import re as _re30
_pre = _re30.compile(r"\b(ALOLAN|GALARIAN|HISUIAN|PALDEAN|PINKAN|VALENCIA)\b", _re30.I)
_named = [(k, g.loader.fetch_specific(int(k))) for k in g.loader.area_data["FORM_MAP"]]
_bad30 = [(k, r["name"]) for k, r in _named if _pre.search(str(r.get("name"))) or _pre.search(str(r.get("display_name")))]
check(not _bad30, f"no form keeps a region prefix ({len(_named)} forms; {_bad30[:3]})")
story.player_team, story.pc_pokemon = _saved30

print("31) Safari Zones in areas: own pictures, own Pokemon, area buttons under EXPLORE (Jordan, 11-02)")
_saved31 = (dict(story.story_flags), story.current_area_key)
for _area, _n in (("SAFARI_ZONE", 4), ("JOHTO_SAFARI_ZONE", 12), ("HOENN_SAFARI_ZONE", 6), ("GREAT_MARSH", 6)):
    _ad = g.loader.area_data["STORY_PROGRESSION"][_area]
    _zs = _ad.get("zones") or []
    _pics = [z["key"] for z in _zs if g.assets.get_journeys_background("routes", f"{_area}_{z['key']}") is not None]
    _union = set(g.loader.area_data[_ad["wild_pool_percentages"]])
    _parts = set().union(*(g.loader.area_data[_ad["zone_pools"][z["key"]]] for z in _zs))
    check(len(_zs) == _n and len(_pics) == _n and _union == _parts,
          f"{_area}: {len(_zs)} areas, {len(_pics)} pictures, the whole pool is the areas' together")
story.current_area_key = "JOHTO_SAFARI_ZONE"
story.story_flags["zone_JOHTO_SAFARI_ZONE"] = "desert"
_ps31 = PlayState(g); g.change_state(_ps31); _ps31.show_progression_menu()
_pool31 = _ps31._base_wild_pool(_ps31.area_data)
check("27" in _pool31 and "74" not in _pool31, f"the Desert has Sandshrew, not the Peak's Geodude ({sorted(_pool31)[:6]})")
_to = [b for b in _ps31.route_buttons if b.text.startswith("TO ") or b.text.startswith("> TO ")]
check(len(_to) == 11 and all(b.route_group == "explore" for b in _to), f"11 other areas, under EXPLORE ({len(_to)})")
story.story_flags, story.current_area_key = _saved31

print("32) PC search and filter; Summary pages through the party / Box; shiny badge (Jordan, 11-02)")
from src.states.systems import PCState as _PC32, PokemonDetailState as _PD32
_saved32 = (list(story.player_team), list(story.pc_pokemon))
_mk32 = lambda pid, shiny=False: Pokemon(g.loader.fetch_specific(pid, is_shiny=shiny), g.assets, size_mult=2.5)
story.player_team = [_mk32(25), _mk32(6), _mk32(9)]
story.pc_pokemon = [_mk32(i, i == 37) for i in (4, 37, 58, 7, 150, 1)] + [None] * 24
_pc = _PC32(g, None); g.change_state(_pc); _pc.start()
_names = lambda: [story.pc_pokemon[i].display_name.upper() for i in _pc.results()]
_pc.search = "char"
check(_names() == ["CHARMANDER"], f"search by name ({_names()})")
_pc.search = "#150"
check(_names() == ["MEWTWO"], f"search by number ({_names()})")
_pc.search = ""
_pc.set_filter("FIRE")
check(_names() == ["CHARMANDER", "VULPIX", "GROWLITHE"], f"filter by type ({_names()})")
_pc.set_filter("SHINY")
check(_names() == ["VULPIX"] and not _pc.filter_open, f"filter shinies ({_names()})")
_pc.set_filter("LEGENDARY")
check(_names() == ["MEWTWO"], f"filter legendaries ({_names()})")
_pc.set_filter("FIRE")
_pc.popup = ("pc", _pc.results()[0]); _pc.popup_summary()
_d = g.current_state
check(isinstance(_d, _PD32) and [m.display_name.upper() for m in _d.roster] == ["CHARMANDER", "VULPIX", "GROWLITHE"],
      "the Summary pages through what the Box shows")
_d.show_mon(1)
check(_d.own.display_name.upper() == "VULPIX" and _d.own.is_shiny, "RIGHT: the next one (the shiny Vulpix)")
_d.show_mon(-1); _d.show_mon(-1)
check(_d.own.display_name.upper() == "GROWLITHE", "LEFT wraps round")
_d.draw()
_d2 = _PD32(g, story.player_team[1], None, roster=list(story.player_team))
check(len(_d2.roster) == 3 and _d2._roster_index() == 1, "from the party menu: the party")
story.player_team, story.pc_pokemon = _saved32

print("33) Regional forms evolve at home or where you're Champion; never into another region's form (Jordan, 11-02)")
from src.pokemon import evolution as _ev33
_saved33 = (dict(story.story_flags), story.current_area_key)
for _r in ("KANTO", "JOHTO", "HOENN", "SINNOH", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA"):
    story.story_flags.pop(story.champion_flag(_r), None)
_m33 = lambda pid: Pokemon(g.loader.fetch_specific(pid), g.assets)
_ag = _m33(2013)  # Alolan Graveler
_cord = lambda mon: _ev33.item_evolution(g, mon, "LINKING_CORD")
_opts = lambda mon: [o[0] for o in _ev33.evolution_options(g, mon)]
story.current_area_key = "HAUOLI_CITY"
check(_cord(_ag) == ("GOLEM_ALOLAN", 76), f"Alolan Graveler + Linking Cord in Alola: Alolan Golem ({_cord(_ag)})")
story.current_area_key = "VIRIDIAN_CITY"
check(_cord(_ag) is None, "not in Kanto before you're a Champion there or in Alola")
story.story_flags[story.champion_flag("KANTO")] = True
check(_cord(_ag) == ("GOLEM_ALOLAN", 76), "in Kanto once you're Kanto's Champion")
story.story_flags.pop(story.champion_flag("KANTO"))
story.story_flags[story.champion_flag("ALOLA")] = True
story.current_area_key = "MOTOSTOKE"
check(_cord(_ag) == ("GOLEM_ALOLAN", 76), "anywhere once you're Alola's Champion")
_gv = _m33(75)
for _area in ("HAUOLI_CITY", "VIRIDIAN_CITY", "MOTOSTOKE"):
    story.current_area_key = _area
    check(_cord(_gv) == ("GOLEM", 76), f"Graveler never becomes Alolan Golem ({_area}: {_cord(_gv)})")
story.current_area_key = "VIRIDIAN_CITY"
check(_opts(_m33(25)) == ["RAICHU"], f"Pikachu outside Alola: Raichu ({_opts(_m33(25))})")
story.current_area_key = "HAUOLI_CITY"
check(_opts(_m33(25)) == ["RAICHU_ALOLAN"], f"in Alola: Alolan Raichu ({_opts(_m33(25))})")
story.story_flags.pop(story.champion_flag("ALOLA"))
_gm = _m33(2019)  # Galarian Meowth
story.current_area_key = "VIRIDIAN_CITY"
check("PERRSERKER" not in _opts(_gm), f"Galarian Meowth: no Perrserker in Kanto yet ({_opts(_gm)})")
story.current_area_key = "MOTOSTOKE"
story.enter_region("GALAR")  # (Galar Pokemon need Galar visited)
check("PERRSERKER" in _opts(_gm), f"but in Galar ({_opts(_gm)})")
story.current_area_key = "OBSIDIAN_FIELDLANDS"
check("TYPHLOSION_HISUIAN" in _opts(_m33(156)), f"Quilava in Hisui: Hisuian Typhlosion ({_opts(_m33(156))})")
story.story_flags, story.current_area_key = _saved33

print("34) Evolutions wait for a level-up; Bag items show ABLE / NO EFFECT (Jordan, 11-02)")
from src.pokemon import evolution as _ev34
from src.states.overworld import evolve_ready_party as _erp34
from src.states.systems import BagState as _Bag34, EvolutionState as _ES34
_saved34 = (list(story.player_team), story.current_area_key, dict(story.inventory))
story.current_area_key = "VIRIDIAN_CITY"
_lick = Pokemon(g.loader.fetch_specific(108), g.assets); _lick.level = 40
_lick.moves = ["ROLLOUT", "LICK"]; _lick.move_pool = list(_lick.moves)
_mach = Pokemon(g.loader.fetch_specific(67), g.assets); _mach.level = 30
story.player_team = [_mach, _lick]
check(not _ev34.ready_evolutions(g, _lick), "Lickitung knowing Rollout doesn't evolve without a level-up")
check(not _erp34(g, g.current_state), "so evolving the Machoke doesn't take the Lickitung along")
_lick.gain_xp(_lick.xp_to_next)
_r34 = _ev34.ready_evolutions(g, _lick)
check(_r34 == ["LICKILICKY"] or "LICKILICKY" in _r34 or not _ev34.evolution_allowed(g, 463),
      f"at its next level-up it does ({_r34})")
_lick.evo_due = False
_bag = _Bag34(g, g.current_state)
_hurt = Pokemon(g.loader.fetch_specific(25), g.assets); _hurt.current_hp = 3
_full = Pokemon(g.loader.fetch_specific(25), g.assets)
_out = Pokemon(g.loader.fetch_specific(25), g.assets); _out.current_hp = 0
check(_bag.item_works("POTION", _hurt) and not _bag.item_works("POTION", _full) and not _bag.item_works("POTION", _out),
      "Potion: ABLE when hurt, NO EFFECT at full HP or fainted")
check(_bag.item_works("REVIVE", _out) and not _bag.item_works("REVIVE", _hurt), "Revive: only the fainted")
check(_hurt.current_hp == 3, "(trying it doesn't use it)")
check(_bag.item_works("LINKING_CORD", _mach) and not _bag.item_works("LINKING_CORD", _lick),
      "Linking Cord: ABLE on Machoke, NO EFFECT on Lickitung")
check(_bag.item_works("THUNDER_STONE", _full) and not _bag.item_works("FIRE_STONE", _full), "stones: the right one")
story.player_team, story.current_area_key = _saved34[0], _saved34[1]
story.inventory.clear(); story.inventory.update(_saved34[2])

print("35) Pokedex: regional forms by species number; the region's own form in its dex; species pages without stats (Jordan, 11-02)")
from src.states.systems import PokedexState as _PX35, PokemonDetailState as _PD35
_saved35 = dict(g.data.data.get("pokedex", {}))
g.data.data["pokedex"] = {"52-normal": {"id": 52, "form": "normal", "name": "MEOWTH"},
                          "2010-alolan": {"id": 2010, "form": "alolan", "name": "MEOWTH"},
                          "2019-galarian": {"id": 2019, "form": "galarian", "name": "MEOWTH"}}
_px = _PX35(g, g.current_state)
_px.dex_view = "ALOLA"; _px.refresh_dex()
_al = next((e for e in _px.full_dex if e["id"] == 2010), None)
check(_al and _al["name"] == "MEOWTH" and _al["status"] == 2 and _px._species(2010) == 52,
      f"Alola's dex: Alolan Meowth, named Meowth, No.052 ({_al})")
_px.dex_view = "NATIONAL"; _px.refresh_dex()
_ids = [e["id"] for e in _px.full_dex]
check(52 in _ids and 2010 not in _ids and 2019 not in _ids, "the National Dex: each species once, the base form")
_px.selected_pkmn_id = 52; _px.show_selected_info()
_pg = g.current_state
check(type(_pg).__name__ == "DexEntryState" and _pg.pid == 52 and _pg.forms[0][1] == "normal"
      and {f[1] for f in _pg.forms} >= {"normal", "alolan", "galarian"},
      "its entry: the base form first, its forms on the FORMS page")
_pg.draw()
g.data.data["pokedex"] = _saved35

print("36) The Seafoam Islands by floor: 1F-B4F, Articuno at the bottom, out from 1F (Jordan, 11-02)")
from src.states.overworld import PlayState as _PS36
_saved36 = (dict(story.story_flags), story.current_area_key)
story.current_area_key = "SEAFOAM_ISLANDS"
for _z in ("1f", "b4f"):
    story.story_flags["zone_SEAFOAM_ISLANDS"] = _z
    _sf = _PS36(g); g.change_state(_sf); _sf.show_progression_menu()
    _t = [b.text.replace("> ", "") for b in _sf.route_buttons]
    _pool = _sf._base_wild_pool(_sf.area_data)
    if _z == "1f":
        check("UP TO B1F" not in _t and "DOWN TO B1F" in _t and any("EXIT" in x or "ROUTE 20" in x.upper() for x in _t)
              and not any("ARTICUNO" in x for x in _t) and "7" in _pool and "87" not in _pool,
              f"1F: down to B1F, the way out, no Articuno; Squirtle, no Dewgong ({_t})")
    else:
        _art = next(m for m in _sf.area_data["route_menu"] if "ARTICUNO" in m["text"])  # (after its trainers)
        check("UP TO B3F" in _t and _sf._in_zone(_art) and not any("ROUTE 20" in x.upper() for x in _t)
              and "87" in _pool and "131" in _pool, f"B4F: Articuno, no way out; Dewgong and Lapras ({_t})")
_pic = g.assets.get_journeys_background("routes", "SEAFOAM_ISLANDS_b3f")
check(_pic is not None, "each floor has its picture")
story.story_flags, story.current_area_key = _saved36

print("37) Norman's ORAS team: Slaking 28, Vigoroth 28, Slaking 30, each with its own moves (Jordan, 11-03)")
from src.pokemon import forms as _fm37, moves as _mv37
_norm = g.loader.area_data["STORY_PROGRESSION"]["PETALBURG_CITY"]["gym"]["leader"]
check(_norm["team"] == [289, 288, 289] and _norm["levels"] == [28, 28, 30], f"the team and levels ({_norm['team']}, {_norm['levels']})")
_t37 = [Pokemon(g.loader.fetch_specific(i), g.assets) for i in _norm["team"]]
_fm37.mark_trainer_team(_t37, _norm)
_sets = [_mv37.ensure_moves(g, m) for m in _t37]
check("YAWN" in _sets[0] and "FURY-SWIPES" in _sets[1] and "SWAGGER" in _sets[2] and "CHIP-AWAY" in _sets[2]
      and _sets[0] != _sets[2], f"each Slaking has its own moves ({_sets})")

print("38) TMs (100, reusable) in Marts by badges, from Leaders and trainers; Mart tabs; HM discs (Jordan, 11-03)")
from src.pokemon import tms as _tm
from src.states.systems import PokeMartState as _Mart38, BagState as _Bag38
_saved38 = (dict(story.inventory), story.current_area_key, dict(story.badges), list(story.player_team), story.money)
_t = {k: d for k, d in _tm.table(g).items() if not d.get("gift") and not d.get("shop_only")}   # (TM100 on: story gifts, 11-12; shop-only TMs, 11-13)
check(len(_t) == 100 and _t["TM24"]["move"] == "SNORE" and all(0 <= d["tier"] <= 8 for d in _t.values()),
      f"Sword/Shield's TM00-TM99 ({len(_t)})")
check(_tm.label(g, "TM05") == "TM05 Thunder Punch", f"named by their move ({_tm.label(g, 'TM05')})")
story.current_area_key = "VIRIDIAN_CITY"
for _k in [k for k in story.inventory if _tm.is_tm(k)]:
    story.inventory.pop(_k)
story.badges["KANTO"] = []
_low = _tm.mart_stock(g, 0)
story.badges["KANTO"] = ["B"] * 8
_all = _tm.mart_stock(g, 8)
check(0 < len(_low) < 20 and len(_all) == 100, f"the Mart: {len(_low)} TMs at 0 badges, all 100 at 8")
_mart = _Mart38(g, g.current_state); _mart.phase = "SHOP"; g.change_state(_mart)
_cats = _mart._categories()
check(_cats[:2] == ["BALLS", "MEDICINE"] and "TMs" in _cats, f"the Mart's tabs: {_cats}")
_mart.set_category("TMs")
check(all(_tm.is_tm(i) for i in _mart._list()) and _mart._price("TM24") <= 3000, "the TMs tab: TMs only, cheap")
story.money = 50000
_mart.init_purchase("TM05"); _mart.max_qty()
check(_mart.qty == 1, "one of each TM")
_mart.confirm_purchase()
check(story.inventory.get("TM05") == 1 and "TM05" not in _mart._list(), "bought: off the shelf")
_pk38 = Pokemon(g.loader.fetch_specific(25), g.assets); _pk38.level = 20
_ch38 = Pokemon(g.loader.fetch_specific(129), g.assets)
story.player_team = [_pk38, _ch38]
_bag = _Bag38(g, g.current_state)
check(_bag.item_works("TM05", _pk38) and not _bag.item_works("TM05", _ch38),
      "ABLE on Pikachu, NO EFFECT on Magikarp")
_bag.selected_item = "TM05"; _bag.on_pokemon_select_tm(0)
check("THUNDER-PUNCH" in (_pk38.move_pool or []) and story.inventory.get("TM05") == 1, "taught; the TM stays")
check(_bag.item_works("TM05", _pk38) == ("THUNDER-PUNCH" not in _pk38.moves),
      "then ABLE only while it isn't one of its four (the TM unlocks it for the pool: Jordan, 11-04)")
import random as _r38
_rew = [_tm.reward(g, 3, "GYM_LEADER", ["ROCK"], rng=_r38.Random(i)) for i in range(5)]
check(all(_rew) and len(set(_rew)) == 1 and _tm.info(g, _rew[0])["type"] == "ROCK",
      f"a Rock Leader gives a Rock TM ({_rew[0]} {_tm.move_of(g, _rew[0])})")
_tr = sum(1 for i in range(200) if _tm.reward(g, 3, "YOUNGSTER", rng=_r38.Random(i)))
check(40 < _tr < 110, f"route trainers often give one ({_tr}/200)")
check(_tm.reward(g, 3, "WILD") is None, "wild Pokemon don't")
_img_hm = g.assets.get_item_image("HM_WATERFALL")
_img_tm = g.assets.get_item_image("TM05")
check(_img_hm is not None and _img_tm is not None, "every HM shows the HM disc; TMs their type's disc")
story.inventory.clear(); story.inventory.update(_saved38[0])
story.current_area_key, story.player_team, story.money = _saved38[1], _saved38[3], _saved38[4]
story.badges.clear(); story.badges.update(_saved38[2])

print("39) Genders, the Day Care and Eggs (Jordan, 11-03)")
from src.pokemon import breeding as _br
from src.states.daycare import DaycareState as _DC
import random as _r39
_saved39 = (list(story.player_team), story.current_area_key, dict(story._store().get("daycare") or {}))
story.current_area_key = "JOHTO_ROUTE_34"
_mk = lambda pid: Pokemon(g.loader.fetch_specific(pid), g.assets)
_rng = _r39.Random(4)
_g = [_br.roll_gender(g, 25, _rng) for _ in range(400)]
check(150 < _g.count("F") < 250 and _br.roll_gender(g, 132) is None and _br.roll_gender(g, 29) == "F"
      and _br.roll_gender(g, 32) == "M", f"genders by the species' ratio (Pikachu {_g.count('F')}/400 female; Ditto none)")
_pm, _pf = _mk(25), _mk(25)
_pm.gender, _pf.gender = "M", "F"
check(_br.compatible(g, _pm, _pf)[0], "a male and a female Pikachu: compatible")
_pf.gender = "M"
check(not _br.compatible(g, _pm, _pf)[0], "two males: not")
_pf.gender = "F"
check(not _br.compatible(g, _pm, _mk(144))[0] and _br.compatible(g, _mk(132), _mk(81))[0]
      and not _br.compatible(g, _mk(132), _mk(132))[0], "a legendary never; Ditto with Magnemite yes; two Ditto no")
check(_br.egg_species(g, _mk(26)) == 172, "Raichu's Egg: Pichu")
_am = _mk(2010); _am.gender = "F"
check(int(_br.egg_species(g, _am)) == 2010, "Alolan Meowth's Egg: Alolan Meowth")
_pf.ability_slot = 2
_hid = sum(1 for i in range(100) if _br.make_egg(g, _pm, _pf, rng=_r39.Random(i)).ability_slot == 2)
check(40 < _hid < 80, f"a mother's hidden ability passes on about 60% of the time ({_hid}/100)")
_egg = _br.make_egg(g, _pm, _pf)
check(_egg.is_egg and _egg.current_hp == 0 and _egg.display_name == "Egg", "an Egg: 0 HP, named Egg")
_egg.heal_full() if hasattr(_egg, "heal_full") else None
check(_egg.current_hp == 0, "healing doesn't wake it")
# the Day Care counts trips; the Egg hatches after 30 in the party
_lead = _mk(4); _lead.ability_slot = 0
story.player_team = [_lead]
_dc = _br.daycare(story); _dc.update({"mons": [_pm, _pf], "steps": 0, "egg": False})
for _ in range(_br.EGG_TRAVELS):
    _br.on_travel(g)
check(_dc["egg"], f"after {_br.EGG_TRAVELS} trips the Day Care has an Egg")
_scr = _DC(g, g.current_state); g.change_state(_scr)
_scr.collect_egg()
check(len(story.player_team) == 2 and story.player_team[1].is_egg and not _dc["egg"], "collected into the party")
_ready = None
for _n in range(1, _br.HATCH_TRAVELS + 1):
    _ready, _ = _br.on_travel(g)
    if _ready is not None:
        break
check(_ready == 1 and _n == _br.HATCH_TRAVELS, f"it hatches after {_n} trips")
story.player_team[1].egg_steps = 0
_lead.ability_slot = 0
g._ability_data = None if False else g.__dict__.get("_ability_data")
_fb = _mk(126); _fb.vol = None
_mag = _mk(219); _mag.ability_slot = 0  # Magcargo: Flame Body / Magma Armor (not its hidden Weak Armor)
story.player_team = [_mag, story.player_team[1]]
for _n in range(1, 31):
    if _br.on_travel(g)[0] is not None:
        break
check(_n == 15, f"Flame Body / Magma Armor in the party: twice as fast ({_n} trips)")
check(_br.hatch_hint(type("E", (), {"egg_steps": 0})()).startswith("It looks like")
      and "soon" in _br.hatch_hint(type("E", (), {"egg_steps": 28})()), "the Summary's hints, by how close it is")
# the party menu's tags once one is left
_dc.update({"mons": [_pm], "steps": 0, "egg": False})
check(_scr.party_tag(_pf) == ("COMPATIBLE", True) and _scr.party_tag(_mk(144))[1] is False,
      "COMPATIBLE / NOT COMPATIBLE on the party cards")
# saved and loaded
_dc.update({"mons": [_pm, _pf], "steps": 7, "egg": False})
story.player_team = [_lead, _br.make_egg(g, _pm, _pf)]
story.player_team[1].egg_steps = 12
_data = story.serialize()
_st2 = type(story)(); _st2.game = g
_st2.deserialize(_data, g.loader)
_team2 = _st2.player_team
_dc2 = _br.daycare(_st2)
check(_team2[1].is_egg and _team2[1].egg_steps == 12 and _team2[1].current_hp == 0
      and len(_dc2["mons"]) == 2 and _dc2["steps"] == 7 and _team2[0].gender == _lead.gender,
      "Eggs, genders and the Day Care are saved")
_bt = TrainerBattleState(g, [_mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name="JOHTO_ROUTE_34")
_pm.gender, _x = "M", _mk(25)
_x.gender = "M"
check(_bt.ailment_effect("infatuation", "ATTRACT", _pm, _x, "A", "B") == ["But it failed!"], "Attract: not on the same gender")
story.player_team, story.current_area_key = _saved39[0], _saved39[1]
story._store()["daycare"] = _saved39[2] or {"mons": [], "steps": 0, "egg": False}

print("40) Alolan Diglett's sprite; Z-Moves and Terastal (Jordan, 11-03)")
from src.pokemon import zpower as _zp
from src.states.battle_gimmicks import end_battle as _endb
_saved40 = (dict(story.inventory), story.current_area_key, dict(story.badges), list(story.player_team))
check(g.assets.get_pokemon_image(50, "alolan", False, placeholder=False) is not None,
      "Alolan Diglett by species and form: its own sprite (not the grey ball)")
check(_zp.z_power(40) == 100 and _zp.z_power(90) == 175 and _zp.z_power(120) == 190 and _zp.z_power(150) == 200,
      "Z-Move power from the move's (the games' table)")
story.current_area_key = "HAUOLI_CITY"
story.inventory.pop("Z_RING", None); story.badges["ALOLA"] = []
check(not _zp.give_key_items(story), "no Z-Ring before a trial")
story.badges["ALOLA"] = ["NORMALIUM_Z"]
_ln = _zp.give_key_items(story)
check(story.inventory.get("Z_RING") == 1 and "Z-RING" in _ln[0] and "NORMALIUM_Z" in _zp.crystals(story),
      "the first trial: the Z-Ring (its prize crystal counts)")
check("WATERIUM_Z" in _zp.mart_stock(story) and "NORMALIUM_Z" not in _zp.mart_stock(story), "Alola's Marts sell more crystals")
_pk40 = Pokemon(g.loader.fetch_specific(25), g.assets); _pk40.level = 30
_pk40.moves = ["THUNDERBOLT", "QUICK-ATTACK"]
story.player_team = [_pk40]
story.inventory["ELECTRIUM_Z"] = 1
_bag39 = __import__("src.states.systems", fromlist=["BagState"]).BagState(g, g.current_state)
_bag39.selected_item = "ELECTRIUM_Z"
_pk40.held_item = None
_nb = TrainerBattleState(g, [Pokemon(g.loader.fetch_specific(19), g.assets)], trainer_class="YOUNGSTER",
                         trainer_name="Joey", area_name="HAUOLI_CITY")
_nb.player_pokemon = _pk40
check(not _nb.z_option(), "no Z-MOVE unless the Pokemon holds a Z-Crystal")
_bag39.on_pokemon_select_crystal(0)
check(_pk40.held_item == "ELECTRIUM_Z" and story.inventory.get("ELECTRIUM_Z") == 1,
      "given from the Bag: it holds the Electrium Z (the Bag keeps it, as in Sun / Moon)")
_b40 = TrainerBattleState(g, [Pokemon(g.loader.fetch_specific(19), g.assets)], trainer_class="YOUNGSTER",
                          trainer_name="Joey", area_name="HAUOLI_CITY")
g.change_state(_b40); _b40.phase = "MENU"
_b40.setup_action_menu()
_labels = [b.text for b in _b40.action_menu.special_buttons]
check(_b40.z_option() and "Z-MOVE" in _labels, f"the Z-MOVE button shows ({_labels})")
_b40.activate_z(); _b40.phase = "MENU"
_dmg, _lines, _ = _b40._use_move(_pk40, _b40.opponent_pokemon, "THUNDERBOLT", "PIKACHU", "FOE", 999, 999)
check(any("GIGAVOLT HAVOC" in l.upper() for l in _lines) and _dmg > 0 and not _b40.z_option(),
      f"Thunderbolt becomes Gigavolt Havoc, once a battle ({_lines[2] if len(_lines) > 2 else _lines})")
story.current_area_key = "MESAGOZA"
story.inventory.pop("TERA_ORB", None)
_zp.give_key_items(story)
check(story.inventory.get("TERA_ORB") == 1, "Paldea: the Tera Orb")
_ch = Pokemon(g.loader.fetch_specific(6), g.assets); _ch.tera_type = "FIRE"
_b41 = TrainerBattleState(g, [Pokemon(g.loader.fetch_specific(19), g.assets)], trainer_class="YOUNGSTER",
                          trainer_name="Joey", area_name="MESAGOZA")
story.player_team = [_ch]; _b41.player_pokemon = _ch
check(_b41.tera_option(), "the TERA button (in Paldea)")
story.current_area_key = "VIRIDIAN_CITY"
check(not _b41.tera_option(), "no Terastal outside Paldea (for now)")
story.current_area_key = "MESAGOZA"
_b41.terastallize(_ch)
check(_ch.types == ["FIRE"] and _b41.stab_mult(_ch, "FIRE") == 2.0 and _b41.stab_mult(_ch, "FLYING") == 1.5
      and not _b41.tera_option(), "Terastallized Fire: Fire moves 2x, its old Flying moves still 1.5x, once a battle")
_endb(_ch)
check(_ch.types == ["FIRE", "FLYING"], "after the battle: its own types again")
story.inventory["WATER_TERA_SHARD"] = 10
_bag40 = __import__("src.states.systems", fromlist=["BagState"]).BagState(g, g.current_state)
_bag40.selected_item = "WATER_TERA_SHARD"
check(_bag40.item_works("WATER_TERA_SHARD", _ch), "10 Water Tera Shards: ABLE")
_bag40.on_pokemon_select_shards(0)
check(_ch.tera_type == "WATER" and not story.inventory.get("WATER_TERA_SHARD"), "they change its Tera Type")
_ace = [Pokemon(g.loader.fetch_specific(i), g.assets) for i in (590, 591)]
_b42 = TrainerBattleState(g, _ace, trainer_class="GYM_LEADER", trainer_name="Katy", area_name="MESAGOZA")
check(_b42.foe_tera_on_entry(_ace[0]) == [] and _b42.foe_tera_on_entry(_ace[1]) and _ace[1].types == ["GRASS"],
      f"a Paldea Leader's last Pokemon Terastallizes into the team's type ({_ace[1].types})")
story.inventory.clear(); story.inventory.update(_saved40[0])
story.current_area_key, story.player_team = _saved40[1], _saved40[3]
story.badges.clear(); story.badges.update(_saved40[2])

print("41) Nugget Bridge is a story step: no way off it until every trainer is beaten; Abra on Routes 24-25 (Jordan, 11-03)")
from src.states.overworld import PlayState as _PS41
_saved41 = (dict(story.story_flags), story.current_area_key, {k: set(v) for k, v in story.defeated_trainers.items()})
story.current_area_key = "KANTO_ROUTE_24"
story.story_flags.pop("nugget_bridge_cleared", None)
story.story_flags["defeated_rival_nugget_bridge"] = True
story.defeated_trainers.pop("KANTO_ROUTE_24", None)
_ps41 = _PS41(g); g.change_state(_ps41); _ps41.rounds_completed = 9; _ps41.show_progression_menu()
_exits = [m for m in _ps41.area_data["route_menu"] if m.get("action") == "EXIT"]
_blocks = [_ps41._exit_block(m, True) for m in _exits]
check(_blocks == ["story", "story"], f"fresh on the bridge: both ways off it are locked ({_blocks})")
_ps41._exit_locked(_exits[0])
check(any("no turning back" in l for l in _ps41.npc_dialogue.text_lines if isinstance(l, str))
      if hasattr(_ps41, "npc_dialogue") else True, "it says why")
for _i in range(6):
    story.mark_trainer_defeated("KANTO_ROUTE_24", _i)
_ps41.show_progression_menu()
check(not story.story_flags.get("nugget_bridge_cleared"), "six of seven beaten: still on the bridge")
story.mark_trainer_defeated("KANTO_ROUTE_24", 6)
_ps41.show_progression_menu()
_blocks = [_ps41._exit_block(m, False) for m in _exits]
check(story.story_flags.get("nugget_bridge_cleared") and _blocks == [None, None],
      f"all seven: the story flag, and both ways open ({_blocks})")
_f = story.story_flags
_f.pop("nugget_bridge_cleared"); _f["visited_BILLS_HOUSE"] = True
story._migrate_flags() if hasattr(story, "_migrate_flags") else None
_d41 = story.serialize(); _st41 = type(story)(); _st41.game = g; _st41.deserialize(_d41, g.loader)
check(_st41.story_flags.get("nugget_bridge_cleared"), "an older save already past Bill's has it done")
_p24 = g.loader.area_data["KANTO_ROUTE_24_PERCENTAGES"]; _p25 = g.loader.area_data["KANTO_ROUTE_25_PERCENTAGES"]
check(_p24.get("63") == 15 and _p25.get("63") == 15 and sum(_p24.values()) == 100 and sum(_p25.values()) == 100,
      "Abra on Routes 24 and 25 at 15%, as in FireRed / LeafGreen")
story.story_flags.clear(); story.story_flags.update(_saved41[0])
story.current_area_key = _saved41[1]
story.defeated_trainers.clear(); story.defeated_trainers.update(_saved41[2])

print("42) Porygon at the Celadon Prize Counter; no leftover pool lists (Jordan, 11-03)")
from src.states import game_corner as _gc42
check(("POKEMON", 137, 6500) in _gc42.PRIZES["CELADON_CITY"], "Porygon: a Celadon Game Corner prize, as in FireRed / LeafGreen")
import glob as _glob42, json as _json42
_left = []
for _f42 in _glob42.glob("assets/*_area_data.json"):
    _d42 = _json42.load(open(_f42, encoding="utf-8"))
    _left += [k for k, v in _d42.items() if isinstance(v, list) and (k + "_PERCENTAGES") in _d42]
check(not _left, f"no old pool lists beside the _PERCENTAGES pools ({_left[:3]})")

print("43) Moltres on Mt. Ember (the Cinnabar volcano is a wild area); the Seagallop from Cinnabar (Jordan, 11-03)")
_ms = next(m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m.get("id") == "s_moltres")
check("Mt. Ember" in _ms["desc"] and _ms["condition"].get("flag_not") == "MT_EMBER_boss_defeated", "the Journal points to Mt. Ember")
_em = next(m for m in g.loader.area_data["STORY_PROGRESSION"]["MT_EMBER"]["route_menu"] if m.get("action") == "BOSS")
check(_em["condition"] == "boss_not_defeated", "Mt. Ember's Moltres: no leftover volcano condition")
_ci = g.loader.area_data["STORY_PROGRESSION"]["CINNABAR_ISLAND"]["travel_options"]
check(any(o.get("target_area") == "ONE_ISLAND" and o.get("condition") == "has_item:TRI_PASS" for o in _ci),
      "Cinnabar: the Seagallop to One Island, with the Tri-Pass")
_f43 = dict(story.story_flags)
story.story_flags["CINNABAR_VOLCANO_boss_defeated"] = True
story.story_flags.pop("MT_EMBER_boss_defeated", None)
_d43 = story.serialize(); _st43 = type(story)(); _st43.game = g; _st43.deserialize(_d43, g.loader)
check(_st43.story_flags.get("MT_EMBER_boss_defeated"), "an old save's volcano Moltres counts for Mt. Ember")
story.story_flags.clear(); story.story_flags.update(_f43)

print("44) Move buttons show accuracy; a TM in the Bag unlocks its move for every Pokemon that can learn it (Jordan, 11-04)")
from src.pokemon import tms as _tms44, moves as _mv44
_c44 = Pokemon(g.loader.fetch_specific(6), g.assets); _c44.level = 50
_c44.moves = ["FLAMETHROWER", "THUNDER-WAVE", "SWORDS-DANCE"]
_t44 = list(story.player_team); story.player_team = [_c44]
_b44 = TrainerBattleState(g, [Pokemon(g.loader.fetch_specific(130), g.assets)], trainer_class="YOUNGSTER",
                          trainer_name="Joey", area_name="VIRIDIAN_CITY")
g.change_state(_b44); _b44.phase = "MENU"; _b44.open_move_menu()
_det44 = {b.text: b.detail for b in _b44.move_buttons if hasattr(b, "detail")}
check(_det44.get("FLAMETHROWER") == "Pow 90  Acc 100%", "Flamethrower: power and accuracy")
check(_det44.get("THUNDER WAVE", "").endswith("Acc 90%"), "Thunder Wave: its accuracy")
check("Acc" not in _det44.get("SWORDS DANCE", "Acc"), "Swords Dance (on itself): no accuracy")
_inv44 = dict(story.inventory)
_tm44 = next(k for k, d in _tms44.table(g).items() if _tms44.can_learn(g, _c44, k)
             and d.get("move") not in _mv44.move_pool(g, _c44))
_mv = _tms44.move_of(g, _tm44)
story.inventory[_tm44] = 1
check(_mv in _mv44.move_pool(g, _c44), f"{_tm44} in the Bag: {_mv} is in Charizard's move pool")
check(_tms44.works_on(g, _c44, _tm44), "the Bag still marks it ABLE (it isn't one of its four)")
_tms44.teach(g, _c44, _tm44)
check(_mv in _c44.moves, "using it fills a free slot")
_mg44 = Pokemon(g.loader.fetch_specific(129), g.assets)
_tmx = next((k for k in _tms44.table(g) if not _tms44.can_learn(g, _mg44, k)), None)
story.inventory[_tmx] = 1
check(_tms44.move_of(g, _tmx) not in _mv44.move_pool(g, _mg44), "a Pokemon that can't learn it doesn't get it")
story.inventory.clear(); story.inventory.update(_inv44); story.player_team = _t44

print("45) Celio's Rainbow Pass: two regional Pokedexes count as the National Dex (Jordan, 11-04)")
from src.states.systems import has_national_dex as _hnd
from src.states import overworld as _ow45
_f45, _i45 = dict(story.story_flags), dict(story.inventory)
story.story_flags.pop("unlocked_national_dex", None); story.story_flags.pop("got_rainbow_pass", None)
story.inventory.pop("RAINBOW_PASS", None)
story.story_flags.update({"beat_champion": True, "received_starter_kanto": True, "received_starter_johto": True})
story.current_area_key = "ONE_ISLAND"
_a45 = g.loader.area_data["STORY_PROGRESSION"]["ONE_ISLAND"]
_o45 = next(o for o in (_a45.get("route_menu") or []) + (_a45.get("explore_options") or [])
            if o.get("text") == "Celio's Rainbow Pass")
_cs45 = _ow45.CityState(g)
_ow45._run_story_event(_cs45, _o45["event"], _cs45._check_menu_condition, lambda l: None)
check(story.inventory.get("RAINBOW_PASS") == 1, "a Champion with two regional dexes gets the Rainbow Pass")
check(_hnd(story), "and the National Dex flag is set")
story.story_flags.clear(); story.story_flags.update(_f45); story.inventory.clear(); story.inventory.update(_i45)

print("46) Sevii's buttons as in Kanto; Four Island's Contest Hall; no Three Isle Path (Jordan, 11-04)")
_sp46 = g.loader.area_data["STORY_PROGRESSION"]
_sev46 = [k for k, a in _sp46.items() if isinstance(a, dict) and a.get("subregion") == "SEVII"]
_ex46 = [o for k in _sev46 for o in _sp46[k].get("explore_options") or []]
check(not any(o.get("text") in ("Pokemon Center", "Poke Mart") for o in _ex46)
      and sum(o.get("action") == "HEAL" and o.get("text") == "Heal" for o in _ex46) == 7, "Sevii towns: Heal and Shop")
check(not any(o.get("condition") == "can_battle" for k in _sev46 for o in _sp46[k].get("route_menu") or []),
      "Sevii wild battles need Poke Balls, as on Kanto's routes")
_four = [o.get("action") for o in _sp46["FOUR_ISLAND"]["explore_options"]]
check(_four.count("DAYCARE") == 1 and not any(o.get("target") == "day_care" for o in _sp46["FOUR_ISLAND"]["explore_options"]),
      "Four Island: one Day Care")
_ch46 = next(o for o in _sp46["FOUR_ISLAND"]["explore_options"] if o.get("text") == "Contest Hall")
from src.states import overworld as _ow46
story.current_area_key = "FOUR_ISLAND"
_cs46 = _ow46.CityState(g); g.change_state(_cs46)
_cs46._get_callback_for_option(_ch46)()
check(type(g.current_state).__name__ == "ContestHallState", f"its Contest Hall opens ({type(g.current_state).__name__})")
for _a46, _t46, _f46 in (("THREE_ISLAND", "Stop the Biker Gang", "beat_three_island_bikers"),
                         ("FOUR_ISLAND", "Battle Lorelei", "defeated_lorelei_sevii"),
                         ("RESORT_GORGEOUS", "SELPHY'S VILLA", "visited_resort_gorgeous")):  # (Selphy's event is at her villa's door on Resort Gorgeous now, with the maps, 11-11)
    _o46 = next(o for o in _sp46[_a46].get("explore_options", []) + _sp46[_a46].get("route_menu", []) if o.get("text") == _t46)
    check(_o46.get("flag_condition") == f"not {_f46}", f"{_t46}: gone once done")
check("THREE_ISLE_PATH" not in _sp46 and any(o.get("target_area") == "THREE_ISLE_PORT"
                                             for o in _sp46["THREE_ISLAND"]["travel_options"])
      and any(o.get("target_area") == "THREE_ISLAND" for o in _sp46["THREE_ISLE_PORT"]["route_menu"]),
      "Three Island <-> Three Isle Port (the empty path is gone)")
_d46 = story.serialize(); _d46["current_area_key"] = "THREE_ISLE_PATH"
_st46 = type(story)(); _st46.game = g; _st46.deserialize(_d46, g.loader)
check(_st46.current_area_key == "THREE_ISLE_PORT", "a save on the old path loads at the port")

print("47) Android (Pydroid 3): the phone keyboard, the Back button, leaving the app (Jordan, 11-04)")
import os as _os47
import pygame as _pg47
from src.core import android as _and47
from src.states.menus import CharacterSelectionState as _CS47
_os47.environ["POKEMATH_ANDROID"] = "1"
check(_and47.is_android(), "Android mode (POKEMATH_ANDROID=1 for tests)")
_c47 = _CS47(g); g.change_state(_c47); _c47.draw()
_a47 = g.android
_a47.filter([])  # (a new screen)
_box = _c47.text_input_rect()
check(_box is not None and not _a47.typing, "the name screen has a name box; no keyboard yet")
_tap = _pg47.event.Event(_pg47.MOUSEBUTTONDOWN, button=1, pos=_box.center)
_a47.filter([_tap])
check(_a47.typing, "tapping the name box opens the keyboard")
_ev = _a47.filter([_pg47.event.Event(_pg47.TEXTINPUT, text="ash"),
                   _pg47.event.Event(_pg47.KEYDOWN, key=_pg47.K_k, unicode="k", mod=0, scancode=0)])
_c47.handle_events(_ev)
check(_c47.input_name == "ASH", f"the keyboard's letters are typed once each ({_c47.input_name!r})")
_c47.handle_events(_a47.filter([_pg47.event.Event(_pg47.KEYDOWN, key=_pg47.K_BACKSPACE, unicode="\b", mod=0, scancode=0)]))
check(_c47.input_name == "AS", "backspace still deletes")
_a47.filter([_pg47.event.Event(_pg47.MOUSEBUTTONDOWN, button=1, pos=(5, 5))])
check(not _a47.typing, "tapping elsewhere closes the keyboard")
if _and47.BACK_KEYS:
    _b47 = _a47.filter([_pg47.event.Event(_pg47.KEYDOWN, key=_and47.BACK_KEYS[0], unicode="", mod=0, scancode=0)])
    check(_b47 and _b47[0].key == _pg47.K_ESCAPE, "the Back button works as Esc")
from src.states import overworld as _ow47
story.current_area_key = "PALLET_TOWN"
_t47 = _ow47.CityState(g); g.change_state(_t47)
_saved = []
_orig = g.data.save
g.data.save = lambda *a, **k: _saved.append(1)
story.autosave = True
if _and47.BACKGROUND:
    _a47.filter([_pg47.event.Event(_and47.BACKGROUND[0])])
    check(_a47.away and _saved, "leaving the app pauses the sound and saves (in a town, with AUTOSAVE on)")
    _a47.filter([_pg47.event.Event(_and47.FOREGROUND[0])])
    check(not _a47.away, "coming back plays it again")
g.data.save = _orig
from src.states.systems import PCState as _PC47
check(_PC47.text_input_rect is not None, "the PC's search box takes typing too")
del _os47.environ["POKEMATH_ANDROID"]
check(_a47.filter([_pg47.event.Event(_pg47.TEXTINPUT, text="z")])[0].type == _pg47.TEXTINPUT,
      "on a PC nothing changes")

print("48) Tanoby Unown letters, Camden and Sina without legends (Jordan, 11-04)")
import random as _r48
from collections import Counter as _C48
from src.pokemon.balance import is_legendary as _leg48
_tan = g.loader.area_data["STORY_PROGRESSION"]["TANOBY_RUINS"]
_w48 = _tan["alt_forms"]["weights"]
check(len(_w48) == 28 and abs(sum(_w48.values()) - 1) < 0.002, f"Tanoby lists all 28 Unown forms ({len(_w48)})")
_r48.seed(48)
_got = _C48(g.loader._resolve_form_context(201, "normal", "UNOWN", _tan)[0] for _ in range(3000))
check(len(_got) >= 20 and "a" not in _got, f"Tanoby Unown come in many letters, the A as the plain form ({len(_got)} seen)")
_alph48 = next(a for a in g.loader.area_data["STORY_PROGRESSION"].values() if isinstance(a, dict) and a.get("route_name") == "Ruins of Alph" and a.get("alt_forms"))
check(_alph48["alt_forms"]["weights"] == _w48, "the Ruins of Alph use the same Unown odds as Tanoby")
from src.pokemon.loader import PokemonLoader as _PL48
check([_PL48.unown_name(f) for f in ("normal", "n", "exclamation", "question")] == ["A UNOWN", "N UNOWN", "! UNOWN", "? UNOWN"],
      "Unown names: A UNOWN, N UNOWN, ! UNOWN, ? UNOWN")
_n48 = g.loader.fetch_specific(201, form="n")
_a48 = g.loader.fetch_specific(201, form="a", is_shiny=True)
check(_n48["display_name"] == "N UNOWN" and _a48["form"] == "normal" and _a48["display_name"] == "A UNOWN",
      f"a saved N and a saved 'a' load as {_n48['display_name']} and {_a48['display_name']} ({_a48['form']})")
from src.states.systems import PokedexState as _PD48
_pd48 = _PD48(g, g.current_state); _pd48.current_tab = "unown"; _pd48.refresh_dex()
check([e["form"] for e in _pd48.full_dex][:2] == ["normal", "b"] and [e["form"] for e in _pd48.full_dex][-2:] == ["exclamation", "question"]
      and len(_pd48.full_dex) == 28, "Unown's letters (its FORMS page now): A to Z, then ! and ?")
_one = _C48(g.loader._resolve_form_context(201, "normal", "UNOWN", {"alt_forms": {"enabled": True, "weights": {"201_b": 0.5}}})[0] for _ in range(2000))
check(800 < _one["b"] < 1200, f"a single listed form keeps its chance ({_one['b']}/2000 at 50%)")
for _f48, _a48, _n48 in (("HOENN", "HOENN_ROUTE_127", "Cooltrainer Camden"), ("ALOLA", "ALOLA_ROUTE_16", "Veteran Sina")):
    _t48 = next(t for t in g.loader.area_data["STORY_PROGRESSION"][_a48]["trainer_pool"] if t["name"] == _n48)
    check(not any(_leg48(p) for p in _t48["team"]), f"{_n48} has no legendary ({_t48['team']})")

print("49) Six Island: an Unown Report lies next to the Ruin Maniac's notes (Jordan, 11-04)")
from src.states import overworld as _ow49
story.current_area_key = "SIX_ISLAND"
_had49 = story.inventory.pop("UNOWN_REPORT", None)
story.story_flags.pop("got_unown_report_sevii", None)
_t49 = _ow49.CityState(g); g.change_state(_t49)
_m49 = next(o for o in story.get_current_area_data()["explore_options"] if o["text"] == "Ruin Maniac's Notes")
_shown49 = []
_show49 = lambda lines: _shown49.append(list(lines))
from src.states.overworld.common import _run_story_event as _rse49
_rse49(_t49, _m49["event"], _t49._check_menu_condition, _show49)
check(story.inventory.get("UNOWN_REPORT", 0) == 1, "no Report yet: one lies next to the notes")
check(any("UNOWN REPORT" in l.upper() for l in _shown49[-1]), "and says so")
_shown49.clear(); _rse49(_t49, _m49["event"], _t49._check_menu_condition, _show49)
check(story.inventory.get("UNOWN_REPORT") == 1 and not any("REPORT" in l.upper() for l in _shown49[-1]), "only once; then just his hint")
story.story_flags.pop("got_unown_report_sevii", None)
_shown49.clear(); _rse49(_t49, _m49["event"], _t49._check_menu_condition, _show49)
check(story.inventory.get("UNOWN_REPORT") == 1, "a Bag that already has one (from Johto) gets no second Report")
if _had49 is None:
    story.inventory.pop("UNOWN_REPORT", None)
else:
    story.inventory["UNOWN_REPORT"] = _had49

print("50) Sevii side mission: fill the Unown Report; Johto's Unown join at the link (Jordan, 11-04)")
import copy as _cp50
_save50 = (_cp50.copy(story.linked_regions), dict(story.region_stores), story.active_store, dict(story.story_flags),
           story.current_area_key)
def _unown50(form):
    u = mk(201); u.form = form; return u
story.current_area_key = "SIX_ISLAND"
story.linked_regions = set()
story.region_stores = {"KANTO": {"team": [_unown50("a"), _unown50("b")], "pc": [_unown50("normal"), None], "bag": {"UNOWN_REPORT": 1}},
                       "JOHTO": {"team": [_unown50(f) for f in "cdefg"], "pc": [], "bag": {"UNOWN_REPORT": 1}}}
story.use_region_store("KANTO")
story.story_flags["met_celio"] = True
for _f50 in ("beat_champion", "beat_johto_champion", story.champion_flag("KANTO"), story.champion_flag("JOHTO")):
    story.story_flags.pop(_f50, None)
_m50 = next((m for m in story.get_active_missions() if m["id"] == "sevii_m7"), None)
check(_m50 is not None and "(2/28)" in _m50["text"], f"in Sevii with the Report: Unown of Tanoby, A and B ({_m50 and _m50['text']})")
from src.states.systems.town_services import UnownReportState as _UR50
check(_UR50(g, g.current_state).caught_forms == {"normal", "b"}, "the Report shows a caught 'a' on the A card")
story.story_flags[story.champion_flag("KANTO")] = True
story.story_flags[story.champion_flag("JOHTO")] = True
story.link_champion_regions()
story.use_region_store("KANTO")
_m50 = next((m for m in story.get_active_missions() if m["id"] == "sevii_m7"), None)
check(_m50 is not None and "(7/28)" in _m50["text"], f"Kanto and Johto titles: Johto's Unown count too ({_m50 and _m50['text']})")
story.player_team = [_unown50(f) for f in story.UNOWN_FORMS]
_e50 = next(e for e in story.get_all_journal_entries() if e["id"] == "sevii_m7")
check(_e50["status"] == "COMPLETED", "all 28: the mission is done")
story.linked_regions, story.region_stores, story.active_store, _fl50, story.current_area_key = _save50
story.story_flags.clear(); story.story_flags.update(_fl50)

print("51) Hoenn's Jirachi: the Millennium Comet over Meteor Falls (Jordan, 11-04)")
from src.states import overworld as _ow51
from src.states.overworld.common import _run_story_event as _rse51
from src.world import story_events as _se51
_fl51 = dict(story.story_flags)
for _f in ("delta_episode_cleared", "millennium_comet_told", "hoenn_jirachi_met", "legend_rematch_hoenn_jirachi_met"):
    story.story_flags.pop(_f, None)
story.story_flags.update({"heard_cozmo": True, "meteor_falls_cleared": True, "cozmo_thanked": True})
story.current_area_key = "FALLARBOR_TOWN"
_t51 = _ow51.CityState(g); g.change_state(_t51)
_said51 = []
_rse51(_t51, _se51.get("professor_cozmo"), _t51._check_menu_condition, _said51.append)
check(not story.story_flags.get("millennium_comet_told") and not any("Comet" in l for l in _said51[-1]),
      "before the Delta Episode, Cozmo doesn't mention the comet")
story.story_flags["delta_episode_cleared"] = True
_rse51(_t51, _se51.get("professor_cozmo"), _t51._check_menu_condition, _said51.append)
check(story.story_flags.get("millennium_comet_told") and any("Meteor Falls" in l for l in _said51[-1]),
      "after it, Cozmo sends you to Meteor Falls")
story.current_area_key = "HOENN_METEOR_FALLS"
_p51 = _ow51.PlayState(g); g.change_state(_p51)
_btn51 = next(o for o in story.get_current_area_data()["route_menu"] if o["text"] == "THE MILLENNIUM COMET")
check(_btn51["boss"]["id"] == 385 and _p51._check_route_condition(_btn51["condition"], False, _btn51),
      "Meteor Falls: THE MILLENNIUM COMET (Jirachi)")
_j51 = next((m for m in story.get_active_missions() if m["id"] == "hoenn_s9"), None) if story.get_current_region() == "HOENN" else True
check(_j51, "the journal's Millennium Comet mission is open")
story.story_flags["hoenn_jirachi_met"] = True
check(not _p51._check_route_condition(_btn51["condition"], False, _btn51), "once met, the button goes (a rematch keeps it if Jirachi got away)")
_orre51 = g.loader.area_data["STORY_PROGRESSION"]["RELIC_FOREST"]
check(any(o.get("text") == "MEET JIRACHI" for o in _orre51["route_menu"]), "Orre keeps its own Jirachi at the Relic Forest")
story.story_flags.clear(); story.story_flags.update(_fl51)

print("52) The Unown Report's reward: all 28 forms merge into Nown (Jordan, 11-04)")
from src.states.systems.town_services import UnownReportState as _UR52
_nown52 = g.loader.get_special_id("NOWN", 3025)
_save52 = (set(story.linked_regions), dict(story.region_stores), story.active_store, dict(story.story_flags), story.current_area_key)
story.current_area_key = "SEVEN_ISLAND"  # (Sevii: the Kanto Bag)
def _u52(form, lv):
    u = mk(201); u.form = form; u.level = lv; return u
story.linked_regions = set()
_party52 = [mk(25), _u52("b", 30)]
_pc52 = [_u52(f, 20) for f in story.UNOWN_FORMS if f != "b"] + [_u52("c", 41), mk(1), None]
story.region_stores = {"KANTO": {"team": _party52, "pc": _pc52, "bag": {"UNOWN_REPORT": 1}}}
story.use_region_store("KANTO")
story.story_flags.pop("unown_merged", None)
_r52 = _UR52(g, g.current_state); g.change_state(_r52)
check(_r52.ready and _r52.btn_merge.callback is not None, "all 28 with you: MERGE THE UNOWN is on")
_r52.ask_merge()
check(_r52.confirming and _r52.btn_yes.visible, "it asks first")
_r52.close_confirm()
check(sum(1 for p in story.pc_pokemon if p and p.id == 201) == 28, "NOT YET: nothing changes")
_r52.ask_merge(); _r52.merge()
from src.states.systems.evolution_scene import EvolutionState as _ES52
_evo52 = g.current_state
check(isinstance(_evo52, _ES52) and _evo52.evolution_id == _nown52 and _evo52.context == "party",
      "MERGE: the party's Unown evolves into Nown")
_left52 = [p for p in story.player_team + story.pc_pokemon if p and p.id == 201]
check(len(_left52) == 2 and {(p.form, p.level) for p in _left52} == {("b", 30), ("c", 41)},
      f"one of each form merged (the Lv 20 C, not the Lv 41 one); left: {sorted((p.form, p.level) for p in _left52)}")
check(any(p and p.id == 1 for p in story.pc_pokemon) and story.player_team[0].id == 25, "other Pokemon stay")
for _ in range(600):
    if g.current_state is not _evo52:
        break
    _evo52.update()
check(any(p and p.id == _nown52 for p in story.player_team), "the party now has NOWN")
_m52 = next((e for e in story.get_all_journal_entries() if e["id"] == "sevii_m7"), None)
_m52 = next((e for e in story.get_all_journal_entries() if e["id"] == "sevii_m7"), None)
check(_m52 is not None and _m52["status"] == "COMPLETED", "the Unown mission stays done after the merge")
story.region_stores = {"KANTO": {"team": [_u52(f, 10) for f in "abcdef"], "pc": [_u52(f, 15) for f in story.UNOWN_FORMS[6:]], "bag": {}}}
story.use_region_store("KANTO")
_k52 = story.merge_unown()
check(_k52 and _k52[2] == "party" and len(story.player_team) == 1 and story.player_team[0].level == 15,
      "a party of only Unown keeps one, so it's never empty")
story.linked_regions, story.region_stores, story.active_store, _fl52, story.current_area_key = _save52
story.story_flags.clear(); story.story_flags.update(_fl52)

print("53) Pokedex: Nown (No. ???) right after Unown, only once caught (Jordan, 11-04)")
from src.states.systems import PokedexState as _PD53
_dex53 = g.data.data.setdefault("pokedex", {})
_had53 = {k: v for k, v in _dex53.items() if isinstance(v, dict) and v.get("id") in (201, _nown52)}
for _k in _had53:
    _dex53.pop(_k)
_dex53["201-normal"] = {"id": 201, "name": "A UNOWN", "form": "normal", "shiny": False, "gmax": False}
def _ids53():
    d = _PD53(g, g.current_state); d.current_tab = "normal"; d.sort_mode = "NUMBER"; d.dex_view = "NATIONAL"; d.refresh_dex()
    return [e["id"] for e in d.full_dex]
check(_nown52 not in _ids53(), "no Nown yet: it isn't listed")
_dex53[f"{_nown52}-normal"] = {"id": _nown52, "name": "NOWN", "form": "normal", "shiny": False, "gmax": False}
_i53 = _ids53()
check(_i53.count(_nown52) == 1 and _i53[_i53.index(_nown52) - 1] == 201, f"caught: Nown comes right after Unown ({_i53.count(_nown52)}x, after {_i53[max(0, _i53.index(_nown52) - 2):_i53.index(_nown52) + 1] if _nown52 in _i53 else None}, 201 in list: {201 in _i53})")
_dex53.pop(f"{_nown52}-normal"); _dex53.pop("201-normal")
_dex53.update(_had53)

print("54) Sevii: a side mission for every legendary there (Jordan, 11-04)")
from src.pokemon.balance import is_legendary as _leg54
_sp54 = g.loader.area_data["STORY_PROGRESSION"]
_ms54 = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m.get("region") == "KANTO"}
_wins54 = {}  # victory flag -> legendary, from Sevii's boss buttons and area bosses
for _k54, _a54 in _sp54.items():
    if isinstance(_a54, dict) and _a54.get("subregion") == "SEVII" or _k54 in ("NAVEL_ROCK", "BIRTH_ISLAND", "FARAWAY_ISLAND"):
        _bs54 = [o.get("boss") or {} for o in _a54.get("route_menu", [])] + [_a54.get("area_boss") or {}]
        for _b54 in _bs54:
            if _b54.get("id") and _leg54(_b54["id"]):
                _wins54[_b54.get("victory_flag") or f"{_k54}_boss_defeated"] = (_b54["name"], _k54)
_done54 = {m.get("completed_flag") for m in _ms54.values()}
check(set(_wins54) <= _done54, f"each Sevii legendary has a mission ({sorted(n for n, _ in _wins54.values())})")
_fl54 = dict(story.story_flags); _area54 = story.current_area_key
story.current_area_key = "SEVEN_ISLAND"
for _f in list(_wins54) + ["beat_champion", "met_celio"]:
    story.story_flags.pop(_f, None)
_act54 = {m["id"] for m in story.get_active_missions()}
check(not ({"sevii_m8", "sevii_m9", "sevii_m10", "sevii_m11"} & _act54), "before Celio, none of them show")
story.story_flags["met_celio"] = True
_act54 = {m["id"] for m in story.get_active_missions()}
check("sevii_m8" in _act54 and "sevii_m9" not in _act54, "after Celio: Moltres; Navel Rock and Birth Island wait for the title")
story.story_flags["beat_champion"] = True
_act54 = {m["id"] for m in story.get_active_missions()}
check({"sevii_m8", "sevii_m9", "sevii_m10", "sevii_m11"} <= _act54, "after the Kanto title: Lugia, Ho-Oh and Deoxys too")
story.story_flags["navel_rock_lugia"] = True
_e54 = {e["id"]: e["status"] for e in story.get_all_journal_entries()}
check(_e54.get("sevii_m9") == "COMPLETED" and _e54.get("sevii_m10") == "ACTIVE", "beating Lugia completes its mission only")
story.story_flags.clear(); story.story_flags.update(_fl54); story.current_area_key = _area54

print("55) Nown: a Sp. Atk glass cannon whose one move is Found Power (Jordan, 11-04)")
from src.pokemon import moves as _mv55
_st55 = g.loader.fetch_specific(_nown52)["stats"]
check(_st55 == {"HP": 70, "ATTACK": 40, "DEFENSE": 60, "SPECIAL-ATTACK": 180, "SPECIAL-DEFENSE": 90, "SPEED": 140},
      f"Nown's own stats: 70/40/60/180/90/140 ({_st55})")
check(g.loader.fetch_specific(201)["stats"]["SPECIAL-ATTACK"] == 72, "Unown keeps its own")
_fp55 = _mv55.info(g, "FOUND-POWER")
check((_fp55["power"], _fp55["category"], _fp55["type"]) == (120, "SPECIAL", "???"), "Found Power: 120, special, typeless")
_n55 = mk(_nown52); _n55.level = 50; _n55.moves = ["HIDDEN-POWER"]; _n55.move_pool = ["HIDDEN-POWER"]
check(_mv55.ensure_moves(g, _n55) == ["FOUND-POWER"] and _mv55.move_pool(g, _n55) == ["FOUND-POWER"],
      "its only move, even after an Unown that knew Hidden Power")
_eff55 = []
for _foe55 in (197, 94, 68):  # Umbreon (Dark: no Psychic move touches it), Gengar, Machamp
    _b55 = battle("PALLET_TOWN", 25, _foe55); _b55.player_pokemon = _n55
    _dmg55, _l55, _ = _b55._use_move(_n55, _b55.opponent_pokemon, "FOUND-POWER", "NOWN", "FOE",
                                     _b55.opponent_pokemon.get_max_hp(), _b55.opponent_pokemon.current_hp)
    _eff55.append(_dmg55 > 0 and not any("effective" in l.lower() or "affect" in l.lower() for l in _l55))
check(all(_eff55), "always a normal hit: Dark, Ghost and Fighting alike")

print("56) No Lv 100 XP warning; the Rocket Warehouse's trainers before the Admin; the Trainer Card (Jordan, 11-04)")
from src.world import levels as _lv56
_b56 = battle("PALLET_TOWN", 25, 19)
_cap56 = _lv56.xp_cap(story)
_b56.player_pokemon.level = 100
_m56 = _b56._award_battle_xp()
check(not any("can't grow" in m for m in _m56), f"Lv 100: no 'can't grow' message ({_m56})")
if _cap56 < 100:
    _b56 = battle("PALLET_TOWN", 25, 19); _b56.player_pokemon.level = _cap56
    check(any("can't grow" in m for m in _b56._award_battle_xp()), f"at the cap (Lv {_cap56}) it still says so")
_wh56 = g.loader.area_data["STORY_PROGRESSION"]["ROCKET_WAREHOUSE"]
_adm56 = next(o for o in _wh56["route_menu"] if o["text"] == "CONFRONT THE ADMIN")
from src.states import overworld as _ow56
_area56 = story.current_area_key; story.current_area_key = "ROCKET_WAREHOUSE"
_p56 = _ow56.PlayState(g); g.change_state(_p56)
story.story_flags["warehouse_doors_open"] = True
check(not _p56._check_route_condition(_adm56["condition"], True, _adm56), "doors open, Rockets left: no Admin yet")
check(_p56._check_route_condition(_adm56["condition"], False, _adm56), "every Rocket beaten: CONFRONT THE ADMIN")
story.story_flags.pop("warehouse_doors_open", None); story.current_area_key = _area56
from src.ui.trainer_card import facts_live as _fl56, facts_from_save as _fs56
story.play_seconds = 2 * 3600 + 5 * 60 + 9
_live56 = _fl56(g)
g.update_save_data()
_saved56 = _fs56(g, g.data.data)
check(_live56["seconds"] == 7509 and _saved56["seconds"] == 7509 and _saved56["trainer_id"] == story.trainer_id,
      "play time and ID No. are saved and read back for the card")
check(_saved56["name"] == _live56["name"] and _saved56["money"] == _live56["money"] and len(_saved56["party"]) == len(_live56["party"]),
      "the load screen's card matches the game's")
from src.states.menus import SaveState as _SS56
_home56 = g.current_state
_s56 = _SS56(g, _home56); g.change_state(_s56)
_wrote56 = []
_s56.save_to_slot = lambda *a, **k: _wrote56.append(a)
_s56.confirm_save()
check(_s56.phase == "SAVING" and not _wrote56, "YES: 'Saving...' first")
for _ in range(_s56.SAVING_FRAMES):
    _s56.update()
check(_s56.phase == "DONE" and len(_wrote56) == 1, "then the file is written and it says so")
for _ in range(_s56.DONE_FRAMES):
    _s56.update()
check(g.current_state is _home56, "then back to the game")

print("57) Building interiors from the fan games; a Gym's rooms follow your progress; move animations (Jordan, 11-04)")
from src.states.overworld.gym_lobby import GymLobbyState as _GL57
from src.minigames import done_flag as _df57
_area57 = story.current_area_key
story.current_area_key = "PETALBURG_CITY"
_rooms57 = story.get_current_area_data()["backgrounds"]["gym"]
_asked57 = []
_gb57 = g.assets.get_background
g.assets.get_background = lambda n, *a, **k: (_asked57.append(n), _gb57(n, *a, **k))[1]
story.story_flags[_df57("PETALBURG_CITY")] = True
story.story_flags["gym_progress_PETALBURG_CITY"] = 2
_GL57(g)
check(_asked57 and _asked57[0] == _rooms57[-1], "Petalburg Gym: the Leader's room once the trainers are beaten")
_asked57.clear()
story.current_area_key = "EVER_GRANDE_CITY"
story.story_flags["gym_progress_EVER_GRANDE_CITY"] = 1
_GL57(g)
check(_asked57 and _asked57[0] == "hoenn_elite_phoebe.png", "Hoenn League: the second member's room for the second match")
g.assets.get_background = _gb57
for _k57 in ("gym_progress_PETALBURG_CITY", "gym_progress_EVER_GRANDE_CITY", _df57("PETALBURG_CITY")):
    story.story_flags.pop(_k57, None)
story.current_area_key = _area57
check(all(g.assets.get_background(n) for n in ("kanto_center.png", "kanto_mart.png", "hoenn_center.png",
                                               "hoenn_mart.png", "sycamore_lab.png", "cyllage_gym_leader.png")),
      "the fan games' rooms are there")
check(g.assets.get_region_default_building({"region": "KANTO", "subregion": "SEVII"}, "center") is not None
      and g.assets.get_region_default_building({"region": "ALOLA"}, "center") is None,
      "towns without their own Center: their region's (Sevii's too); none where there isn't one")
from src.vfx import move_anim as _ma57
_t57, _sw57 = _ma57.find(g.assets.assets_dir, "TACKLE", "player")
_w57, _sw57b = _ma57.find(g.assets.assets_dir, "WATER-GUN", "opponent")
check(_t57 and not _sw57 and _w57 and _sw57b, "Pokemon Orre's animations: Tackle; a foe's Water Gun uses its foe-side version")
check(_ma57.move_key("DOUBLE-EDGE") == "DOUBLEEDGE" and _ma57.find(g.assets.assets_dir, "DOUBLE-EDGE", "player")[0],
      "our move names find Essentials' (DOUBLE-EDGE -> DOUBLEEDGE)")
_fp57 = _ma57.find(g.assets.assets_dir, "FOUND-POWER", "player")[0]
check(_fp57 and len(_fp57.get("graphics", [])) == 2 and any(len(c) > 16 and c[16] == 1 for f in _fp57["frames"] for c in f[2:] if c),
      "Found Power: Hidden Power's orbs, then a violet Hyper Beam (two sheets)")
_b57 = battle("HOENN_ROUTE_101", 258, 263)
for _ in range(400):
    _b57.update()
    if _b57.phase == "MENU":
        break
_b57.chosen_move = "TACKLE"
_b57.player_attack()
check(_b57.move_anim is not None and _b57.dialogue_box.visible and _b57.dialogue_box.text_lines == ["MUDKIP USED TACKLE!"],
      "'MUDKIP USED TACKLE!' shows first, the box up")
_typing57 = []
for _ in range(60):
    _b57.update()
    if _b57._move_seq and _b57._move_seq["stage"] == "text":
        _typing57.append(_b57.move_anim.frame)
    else:
        break
check(_typing57 and set(_typing57) == {-1}, "the animation waits for the text to be typed out")
check(_b57.move_anim is not None and _b57.move_anim.frame >= 0 and _b57.dialogue_box.visible,
      "then the animation plays, the text box still up")
_rest57 = list(_b57._move_seq["rest"]) if _b57._move_seq else []
for _ in range(300):
    if _b57._move_seq is None:
        break
    _b57.update()
check(_b57.move_anim is None and _b57._move_seq is None
      and (_b57.opponent_hp < _b57.opp_max_hp or any("miss" in str(l).lower() for l in _rest57))
      and (not _rest57 or (_b57.dialogue_box.visible and _b57.dialogue_box.text_lines == _rest57)),
      f"then the HP drop and the rest (its text after: {_rest57 or 'none for a plain hit'})")
_b57 = battle("HOENN_ROUTE_101", 258, 263)
for _ in range(400):
    _b57.update()
    if _b57.phase == "MENU":
        break
story.balls_left = max(5, getattr(story, "balls_left", 0))
_b57.opponent_hp = _b57.opponent_pokemon.current_hp = 1
_b57.chosen_move = "TACKLE"
if _b57.catch_offer_ready():
    _b57.player_attack()
    check(_b57.phase != "CATCH_PROMPT" and _b57.dialogue_box.visible, "a knockout: no catch window yet, the text first")
    for _ in range(400):
        if _b57.phase == "CATCH_PROMPT":
            break
        _b57.dialogue_box.is_finished = True
        if _b57.dialogue_box.callback and _b57._move_seq is None:
            _cb57, _b57.dialogue_box.callback = _b57.dialogue_box.callback, None
            _cb57()
        _b57.update()
    check(_b57.phase == "CATCH_PROMPT" and not _b57.renderer.hp_animating(), "the catch window once the HP bar is empty")
else:
    check(False, "a test wild battle should offer the catch window")
check(not _b57._start_move_anim(_b57.player_pokemon, "TACKLE", "player", ["MUDKIP USED TACKLE!", "MUDKIP's attack missed!"]),
      "a missed move shows no animation")

print("58) Hoenn: the Devon Parts journal entry starts when Devon Corp tells you they were stolen (Jordan, 11-05)")
from src.states import overworld as _ow58
_m58 = next(m for m in story.region_missions() if m["id"] == "hoenn_m4")
_live58 = lambda: (story.check_requirements(_m58["condition"], region=_m58.get("region"))
                   and not story.story_flags.get(_m58["completed_flag"]))
_area58 = story.current_area_key
_keep58 = {k: story.story_flags.get(k) for k in ("heard_devon_parts_stolen", "rusturf_rescued", "met_mr_stone")}
for _k58 in _keep58:
    story.story_flags.pop(_k58, None)
story.story_flags["badge_stone_earned"] = True
check(not _live58(), "the Stone Badge alone doesn't add it")
story.current_area_key = "RUSTBORO_CITY"
_c58 = _ow58.CityState(g)
_said58 = []
_ow58._run_story_event(_c58, "devon_president", _c58._check_menu_condition, _said58.append)
check(_live58() and any("stole" in l for l in _said58[-1]), "talking to Devon Corp: the parts were stolen, and the entry is in the journal")
story.story_flags["rusturf_rescued"] = True
check(_live58(), "it stays until the parts are back at Devon")
_ow58._run_story_event(_c58, "devon_president", _c58._check_menu_condition, _said58.append)
check(story.story_flags.get("met_mr_stone") and not _live58(), "returned to Mr. Stone: done")
for _k58, _v58 in _keep58.items():
    if _v58 is None:
        story.story_flags.pop(_k58, None)
    else:
        story.story_flags[_k58] = _v58
story.current_area_key = _area58

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
