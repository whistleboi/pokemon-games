
# The 10-26 Serebii PokéEarth recheck of Kanto, Sevii, Johto and Hoenn
# (kanto_handoff/SEREBII_RECHECK_2026-10-26.md): every fix, critical to low.
from src.states.overworld import CityState, PlayState
from src.world import hoenn, levels
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
data = g.loader.area_data
prog = data["STORY_PROGRESSION"]
flags = story.story_flags


def links(area):
    a = prog[area]
    return {o.get("target_area") or o.get("target") for o in (a.get("travel_options") or []) + (a.get("route_menu") or [])
            + (a.get("explore_options") or []) if o.get("action") in (None, "EXIT", "TRAVEL")}


def pool(area):
    return {int(k.split("_")[0]) for k in data.get(prog[area].get("wild_pool_percentages"), {}) if int(k.split("_")[0]) < 1000}


print("1) critical / high")
check("JOHTO_ROUTE_38" in links("ECRUTEAK_CITY") and "JOHTO_ROUTE_36" not in links("ECRUTEAK_CITY"), "Ecruteak: Route 38, not Route 36")
rt = prog["RADIO_TOWER"]["trainer_pool"]
check([t["name"] for t in rt][-4:] == ["Executive Petrel", "Executive Proton", "Executive Ariana", "Executive Archer"]
      and rt[-1].get("victory_flag") == "radio_tower_cleared" and rt[-4]["team"] == [109, 109, 109, 110, 109, 109],
      "Radio Tower: Petrel (6 Pokemon), Proton, Ariana, Archer last")
hq = prog["ROCKET_HQ"]["trainer_pool"]
check(hq[-1]["name"] == "Executive Ariana" and hq[-1]["team"] == [24, 44, 198] and hq[-2]["name"] == "Executive Petrel",
      "Rocket HQ: Petrel, then Ariana (Arbok, Gloom, Murkrow)")
kim = prog["ECRUTEAK_DANCE_THEATER"]["trainer_pool"]
check([t["team"][0] for t in kim] == [196, 135, 197, 134, 136] and all(t.get("levels") == [38] for t in kim),
      "Kimono Girls: the five Eeveelutions at Lv 38")
r24 = prog["KANTO_ROUTE_24"]["on_enter_event"]["trainer"]["team_choice"]
r22 = next(e for e in prog["KANTO_ROUTE_22"]["on_enter_event"] if e["flag_check"] == "defeated_rival_route22_late")
check(r24 == {"1": [17, 63, 19, 4], "4": [17, 63, 19, 7], "7": [17, 63, 19, 1]} and r22["trainer"]["levels"] == [47, 45, 45, 45, 47, 53],
      "Kanto rival: unevolved starter on Route 24; FRLG's late Route 22 team")
for ver, chimney, seafloor in (("OMEGA_RUBY", [109, 322], [262, 110, 169, 323]), ("ALPHA_SAPPHIRE", [88, 318], [262, 89, 169, 319])):
    flags["hoenn_version"] = ver
    hoenn.apply_version(g)
    p = data["STORY_PROGRESSION"]
    adm = next(t for t in p["HOENN_MT_CHIMNEY"]["trainer_pool"] if t.get("villain") == "admin_a")
    lead = next(t for t in p["HOENN_SEAFLOOR_CAVERN"]["trainer_pool"] if t.get("villain") == "leader")
    hide = next(t for t in p["HOENN_TEAM_HIDEOUT"]["trainer_pool"] if t.get("villain") == "admin_b")
    check(adm["team"] == chimney and lead["team"] == seafloor and len(hide["team"]) == 1
          and adm["name"].endswith("Tabitha" if ver == "OMEGA_RUBY" else "Shelly")
          and hide["name"].endswith("Courtney" if ver == "OMEGA_RUBY" else "Matt"),
          f"{ver}: ORAS admins and leader ({adm['name']}, {hide['name']})")
prog = data["STORY_PROGRESSION"]
e4 = {t["name"]: t for t in prog["EVER_GRANDE_CITY"]["gym"]["trainers"]}
check(e4["Phoebe"]["team"] == [356, 354, 302, 354, 477] and e4["Glacia"]["team"] == [362, 478, 362, 478, 365]
      and e4["Drake"]["team"] == [334, 330, 230, 330, 373] and e4["Phoebe"].get("rematch"), "Hoenn Elite Four: ORAS teams and rematches")
check(381 not in pool("HOENN_ROUTE_121") and 380 not in pool("HOENN_ROUTE_123"), "no wild Latios / Latias")

print("2) medium")
check(prog["LAVARIDGE_TOWN"]["gym"]["leader"]["team"] == [218, 322, 324] and levels.gym_aces("HOENN")[-1] == 46,
      "Hoenn Gyms: ORAS teams and levels (Flannery's Numel, Wallace 46)")
check(prog["KANTO_ROUTE_12"]["area_boss"]["victory_flag"] == "KANTO_ROUTE_12_boss_defeated"
      and prog["KANTO_ROUTE_16"]["area_boss"]["victory_flag"] == "KANTO_ROUTE_16_boss_defeated"
      and not prog["KANTO_ROUTE_11"].get("area_boss"), "Kanto: two Snorlax, Routes 12 and 16")
flags.update({"KANTO_ROUTE_11_boss_defeated": True})
flags.pop("KANTO_ROUTE_12_boss_defeated", None)
story._migrate_kanto_start()
check(flags.get("KANTO_ROUTE_12_boss_defeated") and flags.get("KANTO_ROUTE_16_boss_defeated"), "old saves: both woken")
az = prog["AZALEA_TOWN"]["on_enter_event"]["trainer"]
check(az["levels"] == [14, 16, 18] and prog["GOLDENROD_UNDERGROUND"]["on_enter_event"]["trainer"]["team_choice"]["152"][-1] == 156,
      "Johto rival: HGSS levels (Azalea 14/16/18), Quilava in the Underground")
for a, b in (("KANTO_ROUTE_19", "FUCHSIA_CITY"), ("CERULEAN_CITY", "CERULEAN_CAVE"), ("HOENN_ROUTE_120", "FORTREE_CITY"),
             ("HOENN_ROUTE_123", "HOENN_ROUTE_118"), ("JOHTO_ROUTE_46", "JOHTO_ROUTE_45"), ("SEVAULT_CANYON", "TANOBY_RUINS")):
    check(b in links(a), f"{a} -> {b}")
check("MAUVILLE_CITY" not in links("HOENN_ROUTE_120"), "Route 120 no longer reaches Mauville")
vr = prog["MT_SILVER_CITY"]["on_enter_event"]
vr = (vr if isinstance(vr, list) else [vr])[0]["trainer"]
check(vr["levels"] == [36, 38, 37, 37, 37, 40] and vr["team_choice"]["158"] == [215, 42, 82, 93, 64, 154],
      "Silver at Victory Road: HGSS team and levels (Serebii kanto/4th/victoryroad)")
check(pool("KANTO_ROUTE_11") == {21, 23, 27, 96} and 122 in pool("KANTO_ROUTE_2"), "FRLG Route 11 pool; Mr. Mime on Route 2")
check(prog["KANTO_ROUTE_24"]["route_name"] == "Nugget Bridge" and prog["KANTO_ROUTE_25"]["route_name"] == "Route 25"
      and prog["KANTO_ROUTE_24"]["trainer_pool"][5]["name"] == "Team Rocket Grunt", "Nugget Bridge is Route 24")

print("3) low")
for area in ("BELLCHIME_TRAIL", "SAFARI_ZONE_GATE", "FRONTIER_ACCESS", "POKEATHLON_DOME",
             "THREE_ISLE_PATH", "THREE_ISLE_PORT", "NAVEL_ROCK", "BIRTH_ISLAND", "HOENN_SOUTHERN_ISLAND", "HOENN_MARINE_CAVE",
             "HOENN_TERRA_CAVE", "HOENN_CRESCENT_ISLE", "HOENN_FABLED_CAVE", "HOENN_GNARLED_DEN", "HOENN_NAMELESS_CAVERN",
             "HOENN_PATHLESS_PLAIN", "HOENN_TRACKLESS_FOREST", "HOENN_SECRET_ISLET", "HOENN_SECRET_MEADOW", "HOENN_SECRET_SHORE"):
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
flags["hoenn_version"] = "OMEGA_RUBY"
check(story.special_condition("hoenn_version:OMEGA_RUBY") and not story.special_condition("hoenn_version:ALPHA_SAPPHIRE"),
      "Marine Cave in Omega Ruby, Terra Cave in Alpha Sapphire")
check(any(o.get("text") == "SEEK HEATRAN" for o in prog["HOENN_SCORCHED_SLAB"]["route_menu"])
      and any(o.get("text") == "CALL RAYQUAZA" for o in prog["JOHTO_EMBEDDED_TOWER"]["route_menu"]), "Heatran; Rayquaza at the Embedded Tower")
check(697 in next(t for t in prog["HOENN_SKY_PILLAR"]["trainer_pool"] if t["name"] == "Lorekeeper Zinnia")["team"], "Zinnia's Tyrantrum")
check(any(o.get("text") == "BATTLE LANCE" for o in prog["DRAGONS_DEN"]["route_menu"]), "Dragon's Den: Clair and Lance post-game")
story.current_area_key = "KANTO_ROUTE_21"
check(PlayState(g)._fishing_pool("GOOD_ROD") == data["KANTO_ROUTE_21_GOOD_ROD_PERCENTAGES"], "Route 21 fishes its own FRLG table")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
