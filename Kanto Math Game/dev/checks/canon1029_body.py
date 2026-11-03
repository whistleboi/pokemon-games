
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
check(levels.area_level(g, "JOHTO_ROUTE_44") == 23, f"Route 44 at HGSS's 22-26: {levels.area_level(g, 'JOHTO_ROUTE_44')}")
story.player_team = [mk(6)]
story.player_team[0].level = 80
check(levels.area_level(g, "JOHTO_ROUTE_29") == 3, "a Lv 80 team doesn't raise Route 29")

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
check(_lv.area_level(g, "ORRE_DESERT") >= 14 and _lv.area_level(g, "PYRITE_CAVE") < _lv.area_level(g, "THE_UNDER")
      < _lv.area_level(g, "SNAGEM_HIDEOUT") < _lv.area_level(g, "REALGAM_TOWER"), "they rise through the story")
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
check([_mg.pick(g, k, []).key for k in ("VERMILLION_CITY", "FUCHSIA_CITY", "SAFFRON_CITY", "CINNABAR_ISLAND")]
      == ["surge", "koga", "sabrina", "quiz"], "Kanto's puzzle Gyms keep their own challenges, drawn as games")
check(all(not _mg.GAMES[k].in_pool for k in ("surge", "koga", "sabrina", "quiz")) and _mg.GAMES["chase"].in_pool,
      "and only there; the chase is in the pool")
_titles = {}
for _area in ("PEWTER_CITY", "RUSTBORO_CITY", "STRIATON_CITY"):
    story.current_area_key = _area
    _titles[_area] = (_mg.GAMES["flight"].title_for(g), _mg.GAMES["chase"].title_for(g))
check(_titles["PEWTER_CITY"] == ("Pidgey Flight", "Magikarp Escape") and _titles["RUSTBORO_CITY"] == ("Taillow Flight", "Feebas Escape")
      and _titles["STRIATON_CITY"][0] == "Pidove Flight", f"each region's own Pokemon {_titles}")
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
check("CONFRONT GHOST" in _floor(4)[1], "the ghost, at the top once Team Rocket is beaten")
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
for _area, _n in (("SAFARI_ZONE", 4), ("JOHTO_SAFARI_ZONE", 12), ("HOENN_SAFARI_ZONE", 4), ("GREAT_MARSH", 6)):
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
check(isinstance(_pg, _PD35) and _pg.dex and "STATS" not in _pg.tab_buttons and _pg.pokemon.id == 52
      and {m.form for m in _pg.forms} == {"normal", "alolan", "galarian"},
      "its page: the base form first, its forms cycle, no STATS")
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

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
