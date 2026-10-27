
# The 10-27 Serebii PokéEarth recheck of Unova (BW + B2W2 merged) and Kalos (X/Y), high to low
# (kanto_handoff/SEREBII_RECHECK_UNOVA_KALOS_2026-10-26.md).
from src.states.overworld import CityState, PlayState, _cast_trainer, _story_team
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
data = g.loader.area_data
prog = data["STORY_PROGRESSION"]
flags = story.story_flags


def enter_events(area):
    ev = prog[area].get("on_enter_event")
    return ev if isinstance(ev, list) else [ev] if ev else []


def links(area):
    a = prog[area]
    return {o.get("target_area") or o.get("target") for o in (a.get("travel_options") or []) + (a.get("route_menu") or [])
            + (a.get("explore_options") or []) if o.get("action") in (None, "EXIT", "TRAVEL")}


print("1) Unova: Cheren and Bianca, whoever is the rival")
cheren4 = next(e["trainer"] for e in enter_events("UNOVA_ROUTE_4") if e["trainer"].get("who") == "cheren")
story.current_area_key = "UNOVA_ROUTE_4"
flags["starter_unova"] = 495
for rival, friend in (("cheren", "bianca"), ("bianca", "cheren")):
    g.rival_character, g.friend_character = rival, friend
    t = _cast_trainer(g, cheren4)
    role = "{rival_name}" if rival == "cheren" else "{friend_name}"
    check(t["name"] == role and [p.id for p in _story_team(g, "UNOVA_ROUTE_4", t)] == [519, 510, 511, 499],
          f"Route 4 Cheren as {'rival' if rival == 'cheren' else 'friend'}: his own team (Pignite vs Snivy)")
for area in ("STRIATON_CITY", "UNOVA_ROUTE_2", "UNOVA_ROUTE_3", "UNOVA_ROUTE_5", "DRIFTVEIL_CITY", "TWIST_MOUNTAIN",
             "UNOVA_ROUTE_8", "UNOVA_ROUTE_10"):
    check(any(e["trainer"].get("who") in ("cheren", "bianca") for e in enter_events(area)), f"{area}: Cheren or Bianca battles here")
check(not enter_events("ACCUMULA_TOWN") and not any(e["trainer"].get("name") == "{rival_name}" for e in enter_events("NIMBASA_CITY")),
      "the non-canon Accumula and Nimbasa rival battles are gone")
nv = next(e["trainer"] for e in enter_events("NUVEMA_TOWN") if e["trainer"].get("name") == "{rival_name}")
check(nv["by_character"]["bianca"]["team_choice"]["495"] == [501], "Bianca's starter is the one weak to yours")
check(any(e["trainer"]["name"] == "N" and e["trainer"]["team"] == [519, 535, 532] for e in enter_events("NACRENE_CITY")), "N at Nacrene")
for area, text in (("ASPERTIA_CITY", "Battle Leader Cheren"), ("VIRBANK_CITY", "Battle Leader Roxie"),
                   ("HUMILAU_CITY", "Battle Leader Marlon"), ("UNOVA_POKEMON_LEAGUE", "Challenge Iris")):
    check(any(o.get("text") == text for o in prog[area]["explore_options"]), f"post-game: {text}")
check(any(x["name"] == "Boss Trainer Janna" for x in prog["BLACK_TOWER_UPPER"]["trainer_pool"])
      and any(x["name"] == "Boss Trainer Jariel" for x in prog["WHITE_TREEHOLLOW"]["trainer_pool"]), "Janna and Jariel")

print("2) Kalos: Serena or Calem, Shauna, Tierno, Trevor, Team Flare, Korrina")
flags["starter_kalos"] = 650
story.current_area_key = "ANISTAR_CITY"
an = next(e["trainer"] for e in enter_events("ANISTAR_CITY") if e["trainer"].get("name") == "{rival_name}")
for who, want in (("serena", [135, 359, 655]), ("calem", [678, 135, 359, 655])):
    g.rival_character = who
    check([p.id for p in _story_team(g, "ANISTAR_CITY", _cast_trainer(g, an))] == want, f"Anistar {who}: {want}")
for area in ("TOWER_OF_MASTERY", "COUMARINE_CITY", "KALOS_ROUTE_14", "KILOUDE_CITY"):
    check(any(e["trainer"].get("name") == "{rival_name}" for e in enter_events(area)), f"{area}: rival battle")
check(not any((e.get("trainer") or {}).get("name") == "{rival_name}" for e in enter_events("COURIWAY_TOWN")), "no Couriway rival battle")
names = {e["trainer"]["name"] for a in ("KALOS_ROUTE_5", "KALOS_ROUTE_7", "KALOS_ROUTE_19", "AQUACORDE_TOWN") for e in enter_events(a)}
check({"Tierno", "Trevor", "{friend_name}"} <= names, "Shauna, Tierno and Trevor")
labs = [x["name"] for x in prog["LYSANDRE_LABS"]["trainer_pool"]]
check(all(any(n in x for x in labs) for n in ("Aliana", "Celosia", "Bryony", "Mable", "Xerosic")), "Lysandre Labs: all five Scientists")
lys = next(x for x in prog["GEOSENGE_FLARE_HQ"]["trainer_pool"] if x["name"] == "Lysandre")
check(lys["team"] == [620, 668, 430, 130], "Lysandre: Mienshao, Pyroar, Honchkrow, Gyarados")
check(any("Korrina" in o.get("text", "") for o in prog["GEOSENGE_TOWN"]["explore_options"]), "Korrina's Lucario battle")

print("3) medium / low")
for area, text in (("LOSTLORN_FOREST", "SEEK ENTEI"), ("DREAMYARD", "SEEK LATIOS"), ("REVERSAL_MOUNTAIN", "SEEK HEATRAN"),
                   ("TWIST_MOUNTAIN", "SEEK REGIGIGAS"), ("MARVELOUS_BRIDGE", "SEEK CRESSELIA"), ("CAVE_OF_BEING", "SEEK UXIE"),
                   ("UNDERGROUND_RUINS", "AWAKEN REGICE")):
    check(any(o.get("text") == text for o in prog[area]["route_menu"]), f"{area}: {text}")
for a, b in (("GIANT_CHASM", "UNOVA_ROUTE_13"), ("UNOVA_ROUTE_21", "UNDELLA_BAY"), ("CYLLAGE_CITY", "KALOS_ROUTE_8"),
             ("KALOS_ROUTE_16", "LUMIOSE_CITY")):
    check(b in links(a), f"{a} -> {b}")
for area in ("SKYARROW_BRIDGE", "DRIFTVEIL_DRAWBRIDGE", "UNDERGROUND_RUINS", "PWT", "PLEDGE_GROVE", "ABYSSAL_RUINS", "CAVE_OF_BEING",
             "MARINE_TUBE", "POKESTAR_STUDIOS", "JOIN_AVENUE", "ANVILLE_TOWN", "ENTRALINK", "KALOS_FLARE_CAFE", "CHAMBER_OF_EMPTINESS"):
    linked = any(area in links(k) for k in prog if isinstance(prog[k], dict))
    try:
        story.current_area_key = area
        st = CityState(g) if prog[area].get("area_type") == "town" else PlayState(g)
        g.change_state(st)
        st.draw()
        ok = True
    except Exception as e:
        ok = False
        print("     ", type(e).__name__, e)
    check(linked and ok, f"{area}: reachable and opens")
k7 = data[prog["KALOS_ROUTE_7"]["wild_pool_percentages"]]
check(all(p in k7 for p in ("165", "412", "415", "665")), "Route 7: Ledyba, Burmy, Combee, Spewpa")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
