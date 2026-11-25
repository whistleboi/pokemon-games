# The VS Seeker and trainer rematches (11-18, Jordan's answers: kanto_handoff/VS_SEEKER.md).
#   cat dev/checks/harness_head.py dev/checks/vsseeker_body.py > dev/checks/out/check_vsseeker.py
from src.world import vs_seeker
from src.pokemon import items as itemlib
from src.states.overworld import PlayState
fails = 0
g.dungeon_routes = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


print("1) getting it: Vermilion City in Kanto; after the 2nd badge elsewhere")
story.enter_region("KANTO")
story.inventory.pop("VS_SEEKER", None)
check(vs_seeker.gift(g, "CERULEAN_CITY") == [], "not in Cerulean")
lines = vs_seeker.gift(g, "VERMILLION_CITY")
check(story.inventory.get("VS_SEEKER") == 1 and any("VS SEEKER" in l for l in lines), f"Vermilion: given ({lines[-1:]})")
check(vs_seeker.gift(g, "VERMILLION_CITY") == [], "...once")
check("VS_SEEKER" in itemlib.FIELD and itemlib.FIELD["VS_SEEKER"].get("keep"), "a Bag item, kept when used")
story.inventory.pop("VS_SEEKER", None)
story.enter_region("JOHTO")
story.badges["JOHTO"] = ["ZEPHYR"]
check(vs_seeker.gift(g, "AZALEA_TOWN") == [], "Johto with one badge: not yet")
story.badges["JOHTO"] = ["ZEPHYR", "HIVE"]
check(vs_seeker.gift(g, "AZALEA_TOWN") != [] and story.inventory.get("VS_SEEKER") == 1, "Johto after the 2nd badge: given on arrival")

print("2) used on a route: trainers beaten today in view come back with a '!'")
story.enter_region("KANTO")
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
area = "KANTO_ROUTE_3"
pool = g.loader.area_data["STORY_PROGRESSION"][area]["trainer_pool"]
idxs = [i for i, t in enumerate(pool) if isinstance(t, dict) and vs_seeker._route_trainer(story, t)]
for i in idxs:
    story.mark_trainer_defeated(area, i)
    story.story_flags.setdefault("trainers_beaten_on", {}).setdefault(area, {})[str(i)] = story._today()
story.current_area_key, story.last_area_key = area, "PEWTER_CITY"
p = PlayState(g)
g.states["play"] = p
g.change_state(p)
for _ in range(3):
    p.update()
f = p.run.floor
check(not any(m.kind == "trainer" for m in f.movers), f"Route 3: all {len(idxs)} trainers beaten today, none out")
spot = next(f.spots[f"trainer:{pool[i]['name']}"] for i in idxs if f.spots.get(f"trainer:{pool[i]['name']}"))
p.run.player = next((spot[0] + dx, spot[1] + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1), (0, 2), (2, 0)) if f.walkable(spot[0] + dx, spot[1] + dy))
story.inventory["VS_SEEKER"] = 1
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
vs_seeker.READY_CHANCE = 1.0
lines = vs_seeker.use(p)
back = [m for m in f.movers if m.kind == "trainer"]
check(back and all(vs_seeker.is_ready(story, area, m.payload[0]) for m in back) and "wants a rematch" in lines[-1],
      f"used: {len(back)} came back ({lines[:3]})")
check(all(story.trainer_on_map(area, m.payload[0], pool[m.payload[0]]) for m in back), "...and they stay out if you come back today")
check("charging" in vs_seeker.use(p)[0], "used again at once: the battery needs charging")
for _ in range(vs_seeker.CHARGE):
    vs_seeker.step(story)
check(vs_seeker.charge(story) == vs_seeker.CHARGE, "100 steps: charged again")

print("3) FireRed's own rematch stages: the next one you haven't beaten, held back till its story point")
ben_i = next(k for k, t in enumerate(pool) if isinstance(t, dict) and t.get("name") == "Ben")
ben = pool[ben_i]
check((ben.get("rematch") or {}).get("source") == "FireRed", f"Youngster Ben carries FireRed's stages ({[None if t is None else t['levels'] for t in ben['rematch']['tiers']]})")
for k in ("visited_CELADON_CITY", "visited_FUCHSIA_CITY", "beat_champion", "vs_stage"):
    story.story_flags.pop(k, None)
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()
re1 = vs_seeker.rematch(g, area, ben_i, dict(ben))
check(re1["levels"] == [17, 17], f"first rematch: FireRed's Lv 17 team ({re1['levels']})")
check(re1["rewards"].get("balls", 0) > (ben.get("rewards") or {}).get("balls", 0), f"...a bigger reward ({ben.get('rewards')} -> {re1['rewards']})")
vs_seeker.won(story, area, ben_i, re1["_vs_stage"])
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [17, 17], "next stage still locked: the Lv 17 team again")
story.story_flags["visited_CELADON_CITY"] = True
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [17, 17], "Celadon reached: still Lv 17 (Ben's Lv 28 team is FireRed's 3rd stage, held till Fuchsia)")
story.story_flags["visited_FUCHSIA_CITY"] = True
re2 = vs_seeker.rematch(g, area, ben_i, dict(ben))
check(re2["levels"] == [28, 28], f"Fuchsia reached: the Lv 28 team ({re2['levels']})")
vs_seeker.won(story, area, ben_i, re2["_vs_stage"])
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()   # (called back again)
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [28, 28], "the Lv 48 team waits for the Champion: Lv 28 again")
story.story_flags["beat_champion"] = True
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [48, 48], "after the Champion: the Lv 48 team")
vs_seeker.won(story, area, ben_i, 3)
check(not vs_seeker.is_ready(story, area, ben_i), "won: gone till the next use or tomorrow")
plain = {"name": "Nobody", "class": "YOUNGSTER", "team": [19], "levels": [5]}
check(not vs_seeker._has_rematch(story, area, plain), "a Kanto trainer FireRed gives no rematch never wants one (FireRed's X)")
print("4) in a town, just Seven Island's Psychics Dario and Rodette (FireRed's one rematch each, after the Sevii quest)")
from src.states.overworld import CityState as _CS
from src.states.overworld import common as _common
from src.states.battle import TrainerIntroState as _TIS
g.walk_towns = True
story.enter_region("KANTO")
story.story_flags.update({"beat_dario_seven": True, "sevii_warehouse_cleared": True})
for _k in [k for k in (story.story_flags.get("vs_ready") or {}).get("SEVEN_ISLAND", {})]:
    story.story_flags["vs_ready"]["SEVEN_ISLAND"].pop(_k)
story.current_area_key, story.last_area_key = "SEVEN_ISLAND", None
g.walk_town_pos = None; g.walk_town_room = None
t = _CS(g); g.change_state(t)
for _ in range(3):
    g.current_state.update()
t = g.current_state
_d = next(((tile, ev) for tile, ev in vs_seeker._town_battles(t) if ev["battle"]["name"] == "Psychic Dario"), None)
check(_d is not None, f"Dario stands in Seven Island, beaten, with FireRed's rematch stage ({_d[0] if _d else None})")
t.player = (_d[0][0], _d[0][1] + 1)
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
lines = vs_seeker.use_town(t)
check(any("Psychic Dario wants a rematch" in l for l in lines) and vs_seeker.is_ready(story, "SEVEN_ISLAND", vs_seeker.town_key(_d[1])), f"used beside him: {lines}")
_common._run_story_event(t, _d[1], lambda c: True, lambda ls: None)
intro = g.current_state
b = getattr(intro, "next_state", None)
check(isinstance(intro, _TIS) and [p_.id for p_ in b.opponent_team] == [203] and b.opponent_team[0].level == 56,
      f"talk to him: FireRed's rematch, Girafarig Lv 56 ({type(intro).__name__}, {[(p_.id, p_.level) for p_ in getattr(b, 'opponent_team', [])]})")
story.story_flags[f"vs_won|SEVEN_ISLAND|{vs_seeker.town_key(_d[1])}"] = True   # (the battle won)
vs_seeker.settle_town(story, "SEVEN_ISLAND")
check(not vs_seeker.is_ready(story, "SEVEN_ISLAND", vs_seeker.town_key(_d[1])), "won: he waits for the VS Seeker again")
g.change_state(t)
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
t.player = (3, 3)
_far = vs_seeker.use_town(t); check(not any(l.endswith("wants a rematch!") for l in _far), f"far from them: nobody answers ({_far}, at {t.player})")
print("5) Hoenn: Emerald's rematch stages, from 5 badges on (its Match Call), the next one each win")
story.enter_region("HOENN")
_hp = g.loader.area_data["STORY_PROGRESSION"]
_em = next((a_, i_, t_) for a_, a in _hp.items() if isinstance(a, dict) and story.area_region(a_) == "HOENN"
           for i_, t_ in enumerate(a.get("trainer_pool") or []) if isinstance(t_, dict) and (t_.get("rematch") or {}).get("source") == "Emerald"
           and sum(1 for x in t_["rematch"]["tiers"] if x) >= 2)
_ea, _ei, _et = _em
_n_em = sum(1 for a_, a in _hp.items() if isinstance(a, dict) for t_ in (a.get("trainer_pool") or []) if isinstance(t_, dict) and (t_.get("rematch") or {}).get("source") == "Emerald")
check(_n_em >= 50, f"{_n_em} Hoenn trainers carry Emerald's stages")
story.badges["HOENN"] = ["STONE", "KNUCKLE", "DYNAMO", "HEAT"]
check(not vs_seeker._has_rematch(story, _ea, _et), f"{_et['name']}: no rematch with 4 badges")
story.badges["HOENN"].append("BALANCE")
check(vs_seeker._has_rematch(story, _ea, _et), "...with 5, yes")
story.story_flags.get("vs_stage", {}).pop(f"{_ea}|{_ei}", None)
vs_seeker._ready(story).setdefault(_ea, {})[str(_ei)] = story._today()
_r1 = vs_seeker.rematch(g, _ea, _ei, dict(_et))
_t = [x for x in _et["rematch"]["tiers"] if x]
check(_r1["levels"] == _t[0]["levels"], f"first rematch: Emerald's first stage ({_r1['levels']})")
vs_seeker.won(story, _ea, _ei, _r1["_vs_stage"])
vs_seeker._ready(story).setdefault(_ea, {})[str(_ei)] = story._today()
_r2 = vs_seeker.rematch(g, _ea, _ei, dict(_et))
check(_r2["levels"] == _t[1]["levels"], f"won: the next stage at once, nothing holds it back ({_r2['levels']})")
print("6) Sinnoh: Platinum's rematch levels, unlocked at its milestones (Jordan: Fantina or Celestic, Giratina, Hall of Fame, Heatran)")
story.enter_region("SINNOH")
_sp = g.loader.area_data["STORY_PROGRESSION"]
_ta, _ti, _tt = next((a_, i_, t_) for a_, a in _sp.items() if isinstance(a, dict) for i_, t_ in enumerate(a.get("trainer_pool") or [])
                     if isinstance(t_, dict) and t_.get("name") == "Youngster Tristan")
check((_tt.get("rematch") or {}).get("source") == "Platinum", f"Youngster Tristan carries Platinum's levels ({[None if x is None else x['levels'] for x in _tt['rematch']['tiers']]})")
check(vs_seeker.CHANCE.get("SINNOH") == 0.5, "Platinum's 50% chance a trainer wants a rematch")
for k in ("visited_CELESTIC_TOWN", "TURNBACK_CAVE_boss_defeated", "beat_sinnoh_champion", "STARK_MOUNTAIN_boss_defeated"):
    story.story_flags.pop(k, None)
story.badges["SINNOH"] = []
story.story_flags.get("vs_stage", {}).pop(f"{_ta}|{_ti}", None)


def _tri():
    vs_seeker._ready(story).setdefault(_ta, {})[str(_ti)] = story._today()
    return vs_seeker.rematch(g, _ta, _ti, dict(_tt))


_r = _tri()
check(_r["team"] == [397] and _r["levels"] == [24], f"level 1: Staravia Lv 24 ({_r['team']}, {_r['levels']})")
vs_seeker.won(story, _ta, _ti, _r["_vs_stage"])
check(_tri()["levels"] == [24], "level 2 waits: Fantina not beaten, Celestic not reached")
story.story_flags["visited_CELESTIC_TOWN"] = True
_r = _tri()
check(_r["team"] == [398] and _r["levels"] == [35], f"Celestic Town reached: level 2, Staraptor Lv 35 ({_r['levels']})")
vs_seeker.won(story, _ta, _ti, _r["_vs_stage"])
check(_tri()["levels"] == [35], "level 3 waits for Giratina")
story.story_flags["TURNBACK_CAVE_boss_defeated"] = True
check(_tri()["levels"] == [45], "Giratina caught or beaten: level 3, Staraptor Lv 45")
story.story_flags.pop("visited_CELESTIC_TOWN", None)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC"]
check(vs_seeker._unlocked(story, ["badge:RELIC", "visited_CELESTIC_TOWN"]), "...level 2 also opens with Fantina's Relic Badge")
print("7) Orange: 5.7's table, its first team again (5.7 filled every rematch slot with it)")
story.enter_region("ORANGE")
_op = g.loader.area_data["STORY_PROGRESSION"]
_oa, _oi, _ot = next((a_, i_, t_) for a_, a in _op.items() if isinstance(a, dict) and story.area_region(a_) == "ORANGE"
                     for i_, t_ in enumerate(a.get("trainer_pool") or []) if isinstance(t_, dict) and (t_.get("rematch") or {}).get("source") == "Orange 5.7")
_n_oi = sum(1 for a_, a in _op.items() if isinstance(a, dict) for t_ in (a.get("trainer_pool") or []) if isinstance(t_, dict) and (t_.get("rematch") or {}).get("source") == "Orange 5.7")
check(_n_oi >= 170, f"{_n_oi} Orange trainers carry 5.7's rematch")
vs_seeker._ready(story).setdefault(_oa, {})[str(_oi)] = story._today()
_r = vs_seeker.rematch(g, _oa, _oi, dict(_ot))
check(_r["team"] == _ot["team"] and _r.get("levels") == _ot.get("levels") and _r["rewards"].get("balls", 0) > (_ot.get("rewards") or {}).get("balls", 0),
      f"{_ot['name']}: the same team ({_r['team']}), a bigger reward ({_ot.get('rewards')} -> {_r['rewards']})")
check(not vs_seeker._has_rematch(story, _oa, {"name": "Nobody", "class": "YOUNGSTER", "team": [19], "levels": [5]}), "an Orange trainer 5.7 gives no rematch never wants one")
print("8) made-up stronger teams (Jordan: Orange, and the regions whose games have none): 5 stages, by badges and the Champion")
story.enter_region("ORANGE")
story.badges["ORANGE"] = []
for _k in [k for k in (story.story_flags.get("vs_stage") or {}) if k.startswith(f"{_oa}|")]:
    story.story_flags["vs_stage"].pop(_k)
_ot2 = dict(_ot)
vs_seeker._ready(story).setdefault(_oa, {})[str(_oi)] = story._today()
_r0 = vs_seeker.rematch(g, _oa, _oi, dict(_ot2))
check(_r0["_vs_stage"] == -1 and _r0["team"] == _ot2["team"], f"{_ot2['name']}, no badges: its own team ({_r0['team']})")
_n_or = len(story.get_region_gym_badges("ORANGE") or []) or 4
story.badges["ORANGE"] = ["B%d" % i for i in range(_n_or)]
_seen = []
for _k in range(4):
    _r = vs_seeker.rematch(g, _oa, _oi, dict(_ot2))
    _seen.append((_r["_vs_stage"], len(_r["team"]), max(_r["levels"])))
    vs_seeker.won(story, _oa, _oi, _r["_vs_stage"])
    vs_seeker._ready(story).setdefault(_oa, {})[str(_oi)] = story._today()
check([x[0] for x in _seen] == [0, 1, 2, 3] and _seen[-1][2] > _seen[0][2] and _seen[-1][1] >= _seen[0][1],
      f"all badges: stages 1-4 one win at a time, stronger each time ((stage, size, top level): {_seen})")
check(vs_seeker.rematch(g, _oa, _oi, dict(_ot2))["_vs_stage"] == 3, "stage 5 waits for the Champion")
story.story_flags["beat_orange_champion"] = True
_old_champ = story.is_region_champion
story.is_region_champion = lambda r: True
_r5 = vs_seeker.rematch(g, _oa, _oi, dict(_ot2))
story.is_region_champion = _old_champ
check(_r5["_vs_stage"] == 4 and max(_r5["levels"]) >= 52, f"after the Champion: stage 5 ({_r5['team']}, {_r5['levels']})")
check(vs_seeker.made_team(g, _oa, _oi, _ot2, 2) == vs_seeker.made_team(g, _oa, _oi, _ot2, 2), "the same team every time")
from src.world import levels as _lvm
_lb = _lvm.canon_league_boost(g)   # (Jordan 11-23: HGSS, ORAS, Platinum, B2W2's League rematch jumps, averaged)
check(15 <= _lb <= 20, f"League rematch jump where the games have none: +{_lb} (ORAS +20, HGSS ~+20, Platinum +12, B2W2 ~+16)")
check(_lvm.orange_postgame_levels({}, [20, 22], _lb) == [20 + _lb, 22 + _lb], f"Orange's Gyms after the title: +{_lb} (Cissy's 22 -> {22 + _lb})")
_cb = vs_seeker.canon_boosts(g)   # (Jordan 11-23, M5: the canon rematch tables' average boost at each stage)
check(len(_cb) == vs_seeker.MADE_STAGES and all(x < y for x, y in zip(_cb, _cb[1:])) and 6 <= _cb[0] <= 12,
      f"the canon tables' average boost a stage, rising (about +9 a stage): {_cb}")
for _k in range(vs_seeker.MADE_STAGES):
    _tm, _lv = vs_seeker.made_team(g, _oa, _oi, _ot2, _k)
    _own = [int(x) for x in _ot2["levels"]]
    _want = [min(100, (_own[i] if i < len(_own) else max(_own)) + _cb[_k]) for i in range(len(_tm))]
    check(_lv == _want, f"stage {_k + 1}: its own levels + {_cb[_k]} ({_own} -> {_lv})")
story.enter_region("UNOVA")
_ua, _ui, _ut = next((a_, i_, t_) for a_, a in g.loader.area_data["STORY_PROGRESSION"].items()
                     if isinstance(a, dict) and story.area_region(a_) == "UNOVA" and a.get("wild_pool_percentages")
                     for i_, t_ in enumerate(a.get("trainer_pool") or []) if isinstance(t_, dict) and vs_seeker._route_trainer(story, t_)
                     and isinstance((t_.get("team") or [None])[0], int))
check(vs_seeker._has_rematch(story, _ua, _ut), f"Unova: every route trainer rematches ({_ut['name']})")
story.badges["UNOVA"] = ["B%d" % i for i in range(8)]
vs_seeker._ready(story).setdefault(_ua, {})[str(_ui)] = story._today()
_ru = vs_seeker.rematch(g, _ua, _ui, dict(_ut))
check(_ru["_vs_stage"] >= 0 and len(_ru["team"]) >= len(_ut["team"]), f"{_ut['name']}: a stronger team ({_ut['team']} -> {_ru['team']} {_ru['levels']})")

print("9) on a route played from its menu (Unova...): the VS Seeker calls beaten trainers back; the next trainer battle is one")
_ma = _ua
_mp = g.loader.area_data["STORY_PROGRESSION"][_ma]["trainer_pool"]
for _i in range(len(_mp)):
    story.mark_trainer_defeated(_ma, _i)
story.current_area_key = _ma
_ms = PlayState(g, classic=True) if "classic" in PlayState.__new__.__code__.co_varnames else None
class _Fake:
    def __init__(self):
        self.game = g
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
_vs_ready_before = dict((story.story_flags.get("vs_ready") or {}).get(_ma, {}))
story.story_flags.setdefault("vs_ready", {})[_ma] = {}
_lines = vs_seeker.use_menu(_Fake())
_ready_n = len(story.story_flags["vs_ready"][_ma])
check(_ready_n >= 1 and any(l.endswith("wants a rematch!") for l in _lines), f"used: {_ready_n} want a rematch ({_lines[:2]})")
_first_ready = int(next(iter(story.story_flags["vs_ready"][_ma])))
story.mark_trainer_defeated(_ma, _first_ready)
check(not vs_seeker.is_ready(story, _ma, _first_ready) and (story.story_flags.get("vs_stage") or {}).get(f"{_ma}|{_first_ready}") is not None,
      "beating one (on the map or from the menu) counts the rematch: its stage is recorded, it waits again")
print(f"##### {fails} failures")
