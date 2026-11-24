import json

from src.states import overworld as ow
from src.states import gym_puzzles as gp
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.states.menus import RegionSelectionState
from src.states.systems import BadgeCaseState, PokeMartState
from src.pokemon import evolution
from src.world import levels
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
ORANGE = [k for k, a in prog.items() if a.get("region") == "ORANGE"]


def battle_of(st):
    return st.next_state if isinstance(st, TrainerIntroState) else st


def lineup(b):
    return [(p.id, p.level) for p in b.opponent_team]


exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (Orange and Kanto are walked: played on their maps, 11-24)


def travel_texts(area):
    """The ways on from the town's walked map that open now (its exits, its harbour's boats and the blimp)."""
    return walk_travel(area)


print("1) A full region (the Pokemon Orange hack, 10-27)")
pick = RegionSelectionState(g, mode="new")
check("ORANGE" in pick.regions and pick.regions.index("ORANGE") == pick.regions.index("KANTO") + 1,
      f"a new-game region, between Kanto and Johto: {pick.regions}")
cfg = story.get_region_start("ORANGE")
check(cfg.get("starters") == [1, 4, 7] and cfg.get("start_area") == "VALENCIA_ISLAND" and not cfg.get("travel_only"),
      "Professor Ivy's Bulbasaur, Charmander or Squirtle on Valencia")
check(len(ORANGE) >= 50, f"{len(ORANGE)} Orange areas")
bad = [(k, o.get("target_area")) for k in ORANGE for o in (prog[k].get("travel_options", []) + prog[k].get("route_menu", []))
       if o.get("target_area") and o["target_area"] not in prog]
check(not bad, f"every link leads somewhere {bad}")
check(sum(len(prog[k].get("trainer_pool") or []) for k in ORANGE) >= 60, "the hack's route trainers")

print("2) From Kanto: the blimp (Jordan 11-17)")
story.story_flags = {"beat_champion": True}
story.badges = {"KANTO": ["x"] * 8, "JOHTO": []}
story.current_area_key = "VERMILLION_CITY"
story.starting_region = "KANTO"
check("Blimp to the Orange Islands" in travel_texts("VERMILLION_CITY"), "Kanto Champion: a Rocket Blimp flies to Orange (Jordan 11-17; was the S.S. Anne)")
pick = RegionSelectionState(g, mode="move", return_state=walk_town("VERMILLION_CITY", "KANTO_ROUTE_6"))
check("ORANGE" in pick.regions and pick._travel_only("ORANGE"), "Mom's picker sends a Kanto player to the blimp")
story.story_flags = {}
check("Blimp to the Orange Islands" not in travel_texts("VERMILLION_CITY"), "no title: no voyage")

print("3) Gyms: the Orange Crew (Kumquat: 5.7's Luana, batch 18)")
story.badges = {"ORANGE": []}
story.player_team = [mk(6)]
story.enter_region("ORANGE")
for area, kind, want in (("MIKAN_ISLAND", "cissy", [(117, 20), (9, 22)]),
                         ("KUMQUAT_ISLAND", "luana", [(105, 46), (65, 46)])):
    story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"][:0 if area == "MIKAN_ISLAND" else 3]
    story.story_flags[f"gym_progress_{area}"] = len(prog[area]["gym"]["trainers"])
    story.story_flags[f"gym_challenge_done_{area}"] = True  # (the Gym challenge minigame: won)
    _ldr = str((prog[area]["gym"].get("leader") or {}).get("name") or "")   # (the Gym's leader: a GYM option, or a walked
    _GYM = lambda o: str(o.get("action") or "").upper() == "GYM" or str(o.get("text") or "").strip() == _ldr   # Gym's own battle)
    t = walk_town(area, None)
    walk_meet(t, _GYM, fight=False)   # (into the Gym, up to the Leader)
    pz = g.current_state
    if isinstance(pz, gp.GymPuzzleState):
        check(pz.kind == kind, f"{area}: {kind} challenge first")
        while not pz.finished:
            pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
        pz.on_done(pz.solved) if hasattr(pz, "on_done") else None
        t = walk_town(area, None)
        walk_meet(t, _GYM, fight=False)
    b = battle_of(g.current_state)
    got = lineup(b) if hasattr(b, "opponent_team") else None
    check(got and [p for p, _ in got] == [p for p, _ in want], f"leader: {got} ({type(g.current_state).__name__})")

print("4) Drake and the Orange League")
story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
story.story_flags["gym_progress_PUMMELO_ISLAND"] = 0
t = walk_town("PUMMELO_ISLAND", None)
check("league" in (t.town_map.get("rooms") or {}), "Pummelo is a league: the stadium's league room")
walk_meet(t, lambda o: o.get("text") == "Drake" and str(o.get("action") or "").upper() != "LEAGUE")   # (5.7: meet him in the Palace first)
walk_meet(t, lambda o: o.get("text") == "Drake" and str(o.get("action") or "").upper() == "LEAGUE", fight=False)   # (up to Drake in the stadium)
b = battle_of(g.current_state)
check(hasattr(b, "opponent_team") and [p for p, _ in lineup(b)] == [132, 95, 94, 3, 125, 149], f"Drake, 5.7's team (batch 20, 11-18): {lineup(b)}")
check(prog["PUMMELO_ISLAND"]["gym"]["leader"]["levels"][-1] == 52 and levels.CHAMPION_ACE["ORANGE"] == 52, "Drake's ace Lv 52 (5.7's, 11-17)")
rival = [e["trainer"] for k in ORANGE for e in (prog[k].get("on_enter_event") or []) if isinstance(e, dict)
         and e["trainer"].get("name") == "{rival_name}"]
check(not any(k in ("TANGELO_JUNGLE",) for k in ORANGE if any(e.get("trainer", {}).get("name") == "{rival_name}" for e in (prog[k].get("on_enter_event") or []) if isinstance(e, dict))),
      f"no rival Cross in the areas rebuilt from 5.7 (DECISIONS 11-17; {len(rival)} menu-era battles left in areas not rebuilt yet)")

print("5) Region rules")
c = walk_town("MIKAN_ISLAND", None)
bc = BadgeCaseState(g, c)
check("ORANGE" in bc.unlocked_regions and len(bc.badge_sprites["ORANGE"]) == 5, "badge case: 5 Orange badges")
walk_meet(walk_town("MIKAN_ISLAND", None), lambda o: str(o.get("action") or "").upper() == "SHOP", play=False)
walk_frames(2)
check(isinstance(g.current_state, PokeMartState), f"Mikan's Mart counter opens the shop ({type(g.current_state).__name__})")
items = g.current_state._shop_items()
check("RARE_CANDY" not in items, "island mart: no Rare Candy")

print("6) Special islands")
raw = g.loader.fetch_specific(9103)
check(raw["name"] == "BUTTERFREE" and raw["form"] == "pinkan" and raw["img"], f"Pinkan form, plain name: {raw['name']}")
raw = g.loader.fetch_specific(9201)
check(raw["name"] == "CRYSTAL ONIX" and raw["types"] == ["ROCK", "ICE"], f"Crystal Onix: {raw['types']}")
# (11-17: Pinkan is 5.7's one wild island now; the old Reserve, its permit and its Rocket battle are gone: DECISIONS)
_pk = g.loader.area_data.get(prog["PINKAN_ISLAND"].get("wild_pool_percentages"), {})
check(prog["PINKAN_ISLAND"]["area_type"] == "wild_route" and "PINKAN_RESERVE" not in prog, "Pinkan: one wild island (5.7's Preserve)")
check(sum(1 for s in _pk if 9101 <= int(s) <= 9135) == 35, "our 35 Pinkan forms live on Pinkan Island")
# (11-18, batch 22: 5.7's spheres story replaces the menu's treasures and shrine: the shrine is Shamouti's own, Lugia sings
#  and is not battled, the three birds are wild bosses on their islands afterwards: orange_maps section 17 plays it)
check("SHAMOUTI_SHRINE" not in prog and all(prog[k]["area_boss"]["level"] == 50 and prog[k]["area_boss"]["catchable"]
                                             for k in ("FIRE_ISLAND", "LIGHTNING_ISLAND", "ICE_ISLAND")),
      "5.7's three islands, each with its legendary bird (Lv 50, catchable) after the story; no menu shrine")
cs = walk_town("VALENCIA_ISLAND", None)
ivy = next(o for o in prog["VALENCIA_ISLAND"]["explore_options"] if o["text"] == "Professor Ivy")   # (11-17, 5.7: Ivy mentions the GS Ball; no item)
check("GS_BALL" not in json.dumps(ivy) and any("GS Ball" in l for st in ivy["event"]["stages"] for l in st.get("lines", [])),
      "Professor Ivy mentions the GS Ball in a line, and gives no GS Ball (DECISIONS 11-17)")

print("6b) Batch O3 (11-23): 5.7's trainer moves, the tutors' TMs")
from src.states.overworld import common as _cm
from src.pokemon import tutors as _tu
_tms_tu = _tu.tutor_tms(g, "ORANGE")
check({"TM077", "TM066", "TM086", "TM088", "TM100", "TM264", "TM103", "TM204", "TM108", "TM231", "TM232", "TM082"} <= set(_tms_tu),
      f"the 12 Orange tutors (5.7's) each sell their TM ({sorted(_tms_tu)})")
_cissy = prog["MIKAN_ISLAND"]["gym"]["leader"] if "leader" in prog["MIKAN_ISLAND"].get("gym", {}) else prog["MIKAN_ISLAND"]["gym"]
_team = _cm._story_team(g, "MIKAN_ISLAND", dict(_cissy))
check(_team and getattr(_team[0], "preset_moves", None) and "WATER-GUN" in [str(m).upper() for m in _team[0].preset_moves] + [str(m).upper() for m in getattr(_team[0], "moves", [])]
      or bool(_cissy.get("team_moves")),
      f"Cissy fights with 5.7's own moves ({_cissy.get('team_moves')})")
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_gul = json.dumps(_tm["BUTWAL_ISLAND"])
check('"oi_trainer": 37' in _gul and "team_moves" in _gul, "Gulzar (a map scene's battle) fights with 5.7's moves too")
check(sum(1 for _ in json.dumps({k: prog[k] for k in ORANGE}).split('"team_moves"')[1:]) >= 58,
      "every Orange trainer whose 5.7 team has set moves carries them (58 in the data, 15 on the maps; oteam.py)")

_shops = [(k, o.get("text"), o.get("stock")) for k in ORANGE for o in (prog[k].get("explore_options") or []) + (prog[k].get("route_menu") or [])
          if o.get("action") == "SHOP"]
check(len(_shops) >= 15 and all(st for _k, _t, st in _shops),
      f"every Orange shop sells 5.7's own list, none the badge counter (Jordan 11-23; ostock.py) ({[(k, t) for k, t, st in _shops if not st]})")
check(prog["TANGELO_ISLAND"]["explore_options"][1].get("stock", [])[:2] == ["POKE_BALLS", "POTION"] and
      not any(str(i).startswith("TM") for k, t, st in _shops if t != "TM clerk" for i in st),
      "Tangelo's Mart: 5.7's Poke Balls, Potions...; no TMs in an Orange Mart but Trovitopolis's TM counter")

print("7) Visiting every Orange area")
for k in ORANGE:
    story.current_area_key = k
    try:
        st = ow.CityState(g) if prog[k]["area_type"] == "town" else ow.PlayState(g)
        g.change_state(st)
        for _ in range(3):
            g.current_state.update()
        g.current_state.draw()
    except Exception as e:
        check(False, f"{k}: {type(e).__name__} {e}")
print("9) Trainer portraits from 5.7's file (11-24, Region Checklist): every Orange trainer's own picture, and its walking sheet")
import json as _json
_ds = _json.load(open("assets/dungeon_sprites.json", encoding="utf-8-sig"))
_own = _ds.get("trainers_ORANGE") or {}
_seen = {}
def _tr(o):
    if isinstance(o, dict):
        if o.get("oi_trainer") is not None and "sprite" in o and not str(o["sprite"]).startswith("{"):
            _seen[o["sprite"]] = _seen.get(o["sprite"], 0) + 1
        for v in o.values():
            _tr(v)
    elif isinstance(o, list):
        for v in o:
            _tr(v)
for _k, _a in g.loader.area_data["STORY_PROGRESSION"].items():
    if _a.get("region") == "ORANGE":
        _tr(_a)
_old = {"swimmer_f.png", "swimmer_m.png", "fisherman.png", "firebreather.png", "jessie_james.png", "butch.png", "cassidy.png",
        "misty.png", "ruinmaniac.png", "acetrainer_m.png", "acetrainer_f.png", "battle_girl.png", "ranger_m.png", "ranger_f.png"}
check(not _old & set(_seen) and all(os.path.isfile("assets/sprites/trainers/" + s) for s in _seen),
      f"...{sum(_seen.values())} trainers, {len(_seen)} pictures, all 5.7's (FireRed's fr_ ones or 5.7's own), none of the old stand-ins ({sorted(_old & set(_seen))})")
_pool = {t.get("sprite") for _a in g.loader.area_data["STORY_PROGRESSION"].values() if _a.get("region") == "ORANGE"
         for t in (_a.get("trainer_pool") or []) if isinstance(t, dict) and not str(t.get("sprite", "{")).startswith("{")}
_walk = [s for s in _pool if not (_own.get(s) or (_ds.get("trainers") or {}).get(s))]
check(not _walk, f"...and each route trainer ({len(_pool)} pictures) walks on the map as 5.7 draws it, not a shrunk battle picture ({_walk})")
print("FAILURES:", fails)
