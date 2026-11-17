# Pokemon Yellow's additions to Kanto (Jordan 11-16; kanto_handoff/HANDOFF_KANTO_MAPS.md "Pokemon Yellow additions"),
# met the way a player meets them. Uses kanto_maps_body.py's walking helpers.   bash dev/checks/run.sh yellow_kanto
_src = open("dev/checks/kanto_maps_body.py", encoding="utf-8").read()
exec(_src[:_src.index("# ---- every rebuilt map")])
from src.pokemon import rowdy
SHOTS = S

print("1) Jessie & James: Yellow's four battles, Yellow's teams and levels, each on its map")
JJ = {"MT_MOON": ([23, 52, 109], [14] * 3, 2), "ROCKET_HIDEOUT": ([109, 52, 23], [25] * 3, 3),
      "KANTO_POKEMON_TOWER": ([52, 24, 110], [27] * 3, 6), "SILPH_CITY": ([110, 24, 52], [31] * 3, 10)}
for key, (team, lv, floor) in JJ.items():
    t = [x for x in _area[key].get("trainer_pool", []) if x.get("name") == "Jessie and James"]
    check(len(t) == 1 and t[0].get("team") == team and t[0].get("levels") == lv, f"{key}: Jessie & James {team} Lv {lv[0]} ({[(x.get('team'), x.get('levels')) for x in t]})")
    fl = _tm[key]["floors"][floor]
    check("Jessie and James" in (fl.get("trainer_spots") or []), f"{key}: they stand on the map (floor {floor})")
vg = _area["VIRIDIAN_CITY"]["gym"]["pre_battle_event"]["trainer"]
check(vg.get("levels") == [6, 6], f"Viridian ambush: low levels for a first visit ({vg.get('team')}, {vg.get('levels')})")
import pygame as _pg
_jj = _pg.image.load("assets/sprites/trainers/jessie_james.png")
check(_jj.get_size() == (128, 128), "their battle sprite: the whole pair (Orre 2.1.1's, not cut off)")

print("2) Viridian Forest: Yellow's two extra trainers")
vf = {x.get("spot_name"): x for x in _area["VIRIDIAN_FOREST"]["trainer_pool"] if x.get("spot_name")}
check(vf.get("Lass VF", {}).get("team") == [29, 32] and vf.get("Bug Catcher VF", {}).get("team") == [10, 10], "the Lass (Nidoran pair) and the Bug Catcher (two Caterpie)")
check({"Lass VF", "Bug Catcher VF"} <= set(_tm["VIRIDIAN_FOREST"].get("trainer_spots") or []), "both on the forest's map")

print("3) Viridian: the Journal sends you to the Gym, and Jessie & James jump you there")
story.badges["KANTO"] = []
story.starting_region = "KANTO"
story.story_flags.update({"received_pokedex_kanto": True, "received_starter_kanto": True})
story.story_flags.pop("viridian_rocket_defeated", None)
story.current_area_key = "VIRIDIAN_CITY"
_m = [m.get("id") for m in story.get_active_missions() if m.get("type") == "MAIN"]
check(_m and _m[0] == "m1", f"the Journal's main task: Investigation at Viridian ({_m[:3]})")
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (36, 11); v.anim = 0; v.facing = (0, -1)
walk(v, "u")
st = g.current_state
check(isinstance(st, (TrainerIntroState, TrainerBattleState)), f"walking into the locked Gym starts their battle ({type(st).__name__})")
story.story_flags["viridian_rocket_defeated"] = True
v = open_map("VIRIDIAN_CITY", "KANTO_ROUTE_1")
v.player = (36, 11); v.anim = 0; v.facing = (0, -1)
said.clear()
walk(v, "u")
play(lambda: not g.current_state._busy(), 300)
check(isinstance(g.current_state, _WTS) and tuple(g.current_state.player) == (36, 11), "after that the doors are just locked again")
_m = [m.get("id") for m in story.get_active_missions() if m.get("type") == "MAIN"]
check("m1" not in _m, f"...and the Journal moves on ({_m[:2]})")

print("4) Route 19: Yellow's Summer Beach House, on the sand below the ledges")
r19 = _tm["KANTO_ROUTE_19"]
check(r19.get("inside", {}).get("9,11") == "beach" and "beach" in r19.get("rooms", {}), "its door leads into the house")
check(r19["roofs"]["_picture"]["f"].endswith("k_r19.png"), "drawn on Route 19's picture")
story.story_flags.pop(rowdy.GIVEN, None); story.story_flags.pop(rowdy.LOCKER, None)
for p in [p for p in story.player_team if rowdy.is_rowdy(p)]:
    story.player_team.remove(p)
dude = next(o for o in _area["KANTO_ROUTE_19"]["route_menu"] if o.get("text") == "SURFIN' DUDE")
from src.states.overworld.common import _run_story_event
told = []
_run_story_event(v, dude["event"], lambda c: True, lambda ls: told.extend(ls))
check(any("Bring it by" in l for l in told), "no Pikachu with you: the Surfin' Dude asks for one")
pk = rowdy.make(g); story.player_team.append(pk)
told.clear()
_run_story_event(v, dude["event"], lambda c: True, lambda ls: told.extend(ls))
tap(g.current_state)
from src.minigames.beach import PikachuBeach
check(isinstance(g.current_state, PikachuBeach), f"with the rowdy Pikachu: Pikachu's Beach starts ({type(g.current_state).__name__})")

print("5) Pikachu's Beach plays as Yellow's, with sums")
from src.minigames.beach import radness, AIR, BEST_FLAG
check([radness(x) for x in (["L"], ["L", "L"], ["L", "R"], ["R"] * 3, ["L", "R", "L"])] == [50, 150, 180, 350, 500], "Yellow's Radness table")
mg = g.current_state
mg._play()
story.story_flags.pop(BEST_FLAG, None)
asked = right = 0
for _ in range(6000):
    if mg.phase != "PLAY":
        break
    if mg.question and mg.question[3] is None:
        asked += 1
        mg._answer([str(o) for o in mg.question[2]].index(str(mg.question[1])))
        right += 1
    if mg.air == AIR - 2:
        mg._flip("R")
    mg.update(); mg.draw()
check(mg.phase == "WON" and asked >= 5, f"surfed to the shore, a sum at every wave ({mg.phase}, {asked} sums)")
check(int(story.story_flags.get(BEST_FLAG, 0)) == mg.rad + int(mg.hp) > 0, f"the best score is kept ({story.story_flags.get(BEST_FLAG)})")
pygame.image.save(g.screen, SHOTS + "/yellow_beach_end.png")

print("6) the Celadon Mansion old lady reads Pikachu's mood")
story.story_flags["got_tea"] = True
lady = next(o for o in _area["CELADON_CITY"]["explore_options"] if o.get("text") == "Celadon Mansion")
told.clear(); pk.friendship = 255
_run_story_event(v, lady["event"], lambda c: True, lambda ls: told.extend(ls))
check(any("adores" in l for l in told), f"a happy Pikachu ({told[-1:]})")
told.clear(); pk.friendship = 10
_run_story_event(v, lady["event"], lambda c: True, lambda ls: told.extend(ls))
check(any("trust" in l for l in told), f"a rowdy one ({told[-1:]})")

print("7) into the beach house, and surfing with Pikachu")
story.current_area_key = "KANTO_ROUTE_19"
d = open_map("KANTO_ROUTE_19", "FUCHSIA_CITY")
d.run.player = (9, 12); d.partner = (9, 13); d.anim = 0; d.facing = (0, -1)
walk(d, "u")
d = g.current_state
inside = d.run.floor if hasattr(d, "run") else None
_names = [str(getattr(f, "name", f)) for f in (getattr(d, "_figures", lambda: {})() or {}).values()] if hasattr(d, "_figures") else []
check(hasattr(d, "run") and d.run.index != 0, f"walked through the door into the Summer Beach House (floor {getattr(d.run, 'index', None)})")
pygame.image.save(g.screen, SHOTS + "/yellow_beach_house.png")
d = open_map("KANTO_ROUTE_19", "FUCHSIA_CITY")
story.inventory["HM_SURF"] = 1
sea = next((x, y) for y in range(14, 20) for x in range(6, 18) if d.run.floor.tile(x, y) == __import__("src.dungeon.core", fromlist=["SURF"]).SURF)
d.run.player = sea; d.partner = (sea[0] - 1, sea[1]); d.anim = 0; d.facing = (1, 0)
frames(3)
pygame.image.save(g.screen, SHOTS + "/yellow_surf.png")
check(d._on_surf(), f"out on the sea {sea}")
check(d._surf_draw(d._player_img(), pygame.Rect(0, 0, 48, 48), lambda x, y: pygame.Rect(0, 0, 48, 48), 1)[0][1].get_width() > 0, "you ride Pikachu's surfboard (Jordan's sheet)")

print(f"##### {len(fails)} failures")
