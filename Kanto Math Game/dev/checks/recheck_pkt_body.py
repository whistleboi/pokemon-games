
# The 10-27 Serebii PokéEarth recheck of Paldea, Kitakami and the Terarium / Blueberry Academy,
# critical to low (kanto_handoff/SEREBII_RECHECK_PALDEA_KITAKAMI_TERARIUM_2026-10-27.md).
import os
from src.states.overworld import CityState, PlayState
from src.pokemon import balance
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
data = g.loader.area_data
prog = data["STORY_PROGRESSION"]


def enter_events(area):
    ev = prog[area].get("on_enter_event")
    return ev if isinstance(ev, list) else [ev] if ev else []


def opts(area):
    a = prog[area]
    return (a.get("route_menu") or []) + (a.get("explore_options") or []) + (a.get("travel_options") or [])


def pool(area):
    return data.get(prog[area].get("wild_pool_percentages") or "", {})


print("1) critical: full wild pools")
for area, n in (("SOUTH_PROVINCE_AREA_1", 50), ("SOUTH_PROVINCE_AREA_5", 50), ("WEST_PROVINCE_AREA_3", 50), ("GLASEADO_MOUNTAIN", 50),
                ("AREA_ZERO", 60), ("KITAKAMI", 80), ("ONI_MOUNTAIN", 80), ("POLAR_BIOME", 40), ("SAVANNA_BIOME", 40)):
    check(len(pool(area)) >= n, f"{area}: {len(pool(area))} species")
check(any(k in pool("SOUTH_PROVINCE_AREA_2") or k in pool("EAST_PROVINCE_AREA_1") or k in pool("WEST_PROVINCE_AREA_2")
          for k in ("2058",)) or any("2058" in pool(a) for a in prog if isinstance(prog[a], dict) and str(prog[a].get("region")).upper() == "PALDEA"),
      "Paldean Wooper (2058) is wild somewhere in Paldea")
leg = [(a, p) for a in prog if isinstance(prog[a], dict) and str(prog[a].get("region")).upper() == "PALDEA"
       for p in pool(a) if p.isdigit() and balance.is_legendary(int(p))]
check(not leg, f"no legendaries in Paldea's wild pools {leg[:4]}")

print("2) high: story battles")
t = next(e["trainer"] for e in enter_events("SOUTH_PROVINCE_AREA_1") if e["trainer"]["name"] == "{rival_name}")
check(set(t["team_choice"]) == {"906", "909", "912"} and any(p in (909, 910, 911) for p in t["team_choice"]["906"]),
      "Nemona on South Province Area 1, the starter strong against yours")
check(any(e["trainer"]["name"] == "Arven" for e in enter_events("PALDEA_ROUTE_1")) and prog["PALDEA_ROUTE_1"]["route_name"] == "Poco Path",
      "Arven on Poco Path")
for area, text in (("MESAGOZA", "Champion Battle: {rival_name}"), ("MESAGOZA", "Director Clavell"), ("MOSSUI_TOWN", "Photographer Perrin"),
                   ("APPLE_HILLS", "Glitterati O'Nare"), ("BLUEBERRY_ACADEMY", "Director Cyrano"), ("SAVANNA_BIOME", "BB Elite Four Crispin"),
                   ("CANYON_BIOME", "BB Elite Four Amarys"), ("COASTAL_BIOME", "BB Elite Four Lacey"), ("POLAR_BIOME", "BB Elite Four Drayton")):
    check(any(o.get("text") == text for o in opts(area)), f"{area}: {text}")
ace = prog["ACADEMY_ACE_TOURNAMENT"]
check(len(ace["trainer_pool"]) == 13 and ace["trainer_pool"][-1]["name"] == "Champion {rival_name}"
      and any(o.get("target_area") == "ACADEMY_ACE_TOURNAMENT" for o in opts("NARANJA_ACADEMY")), "the Academy Ace Tournament")
kit = [(a, e["trainer"]["name"]) for a in ("MOSSUI_TOWN", "ONI_MOUNTAIN", "KITAKAMI_PARADISE_BARRENS", "KITAKAMI_LOYALTY_PLAZA", "DREADED_DEN")
       for e in enter_events(a) if e["trainer"]["name"] in ("Carmine", "Kieran")]
check(sum(1 for _, n in kit if n == "Carmine") == 3 and sum(1 for _, n in kit if n == "Kieran") == 4, f"Kitakami: Carmine x3, Kieran x4 {kit}")
check(any(e["trainer"]["name"] == "Carmine" for e in enter_events("TERARIUM_CENTRAL_PLAZA"))
      and any(e["trainer"]["name"] == "Lacey" for e in enter_events("BLUEBERRY_ACADEMY")), "Blueberry: Carmine and Lacey")

print("3) medium / low: legendaries, places, trainers, sprites")
zero = {(o.get("boss") or {}).get("id") for o in opts("AREA_ZERO")}
check({1009, 1010, 1020, 1021, 1022, 1023} <= zero, "Walking Wake, Iron Leaves and the Paradox legends")
snack = {(o.get("boss") or {}).get("id") for o in opts("TERARIUM")}
check(len(snack & {144, 145, 146, 243, 244, 245, 249, 250, 380, 381, 382, 383, 384, 638, 639, 640, 643, 644, 646, 791, 792, 800,
                   891, 896, 897}) == 25, "Snacksworth's 25 legendaries")
for area in ("LOS_PLATOS", "ZAPAPICO", "ACADEMY_ACE_TOURNAMENT", "SOUTH_PROVINCE_AREA_1", "TERARIUM"):
    try:
        story.current_area_key = area
        st = CityState(g) if prog[area].get("area_type") == "town" else PlayState(g)
        g.change_state(st)
        st.draw()
        ok = True
    except Exception as e:
        ok = False
        print("     ", type(e).__name__, e)
    check(ok, f"{area} opens")
check(len(prog["SOUTH_PROVINCE_AREA_1"]["trainer_pool"]) >= 5
      and any(o.get("action") == "TRAINER" for o in prog["SOUTH_PROVINCE_AREA_1"]["route_menu"]), "province trainers")
sprites = os.path.join(g.assets.assets_dir, "sprites", "trainers")
for s in ("clavell", "perrin", "cyrano", "lacey", "carmine", "kieran", "drayton", "amarys", "crispin", "dendra", "miriam", "raifort",
          "saguaro", "salvatore", "tyme", "jacq"):
    check(os.path.isfile(os.path.join(sprites, s + ".png")), f"sprite {s}.png")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
