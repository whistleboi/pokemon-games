
# The 10-27 Serebii PokéEarth recheck of Orre (Colosseum + XD): Shadow Pokemon, bosses, Poké Spots.
import os
from src.states.overworld import PlayState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
data = g.loader.area_data
prog = data["STORY_PROGRESSION"]
orre = {k: a for k, a in prog.items() if isinstance(a, dict) and str(a.get("region")).upper() == "ORRE"}

print("1) all 131 Shadow Pokemon, once each")
fm = data.get("FORM_MAP", {})
ids = [fm.get(str(s["id"]), {}).get("id", s["id"]) for a in orre.values() for s in a.get("shadow_pool") or []]
check(len(ids) == 131 and len(set(ids)) == 131, f"{len(ids)} shadows, {len(set(ids))} species")


def find(name):
    out = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("name") == name and o.get("team"):
                out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(orre)
    return out


print("2) the bosses' teams from the games")
for name, team in (("Cipher Admin Dakim", [229, 330, 205, 340, 344]), ("Cipher Admin Ein", [310, 121, 112, 279, 169]),
                   ("Cipher Admin Venus", [350, 182, 26, 40, 200]), ("Cipher Head Evice", [306, 373, 68, 212, 289, 199]),
                   ("Cipher Admin Lovrina", [282, 368, 315, 83, 334]), ("Cipher Admin Gorigan", [199, 217, 306, 365, 62, 122]),
                   ("Grand Master Greevil", [310, 277, 121, 210, 334, 142]), ("Pree Champion Justy", [27, 331, 207, 192, 184, 299]),
                   ("Cipher Admin Miror B.", [348, 272, 272, 55, 294]), ("Cipher Nascour", [65, 282, 178, 356, 365, 257]),
                   ("Cipher Admin Snattle", [375, 195, 212, 338, 351, 121]), ("Cipher Admin Ardos", [277, 65, 230, 214, 125, 286]),
                   ("Cipher Admin Eldes", [291, 310, 373, 330, 105, 131]), ("Snagem Head Gonzap", [227, 342, 348, 68, 286, 210])):
    t = [x for x in find(name) if x["team"] == team]  # (Dakim, Ein and Snattle also have earlier story battles)
    check(t and len(t[0]["levels"]) == len(team), f"{name}")
gv = next(o for o in orre["XD_CITADARK_ISLE"]["route_menu"] if "GREEVIL" in o["text"])
check({"xd_snattle_beaten", "xd_ardos_beaten", "xd_eldes_beaten"} <= set(gv["condition"]), "Greevil after Snattle, Ardos and Eldes")

print("3) the Poké Spots")
pool = {p for k in ("ORRE_POKE_SPOTS", "OASIS_POKE_SPOT", "CAVE_POKE_SPOT") for p in data[orre[k]["wild_pool_percentages"]]}
check({"27", "207", "328", "187", "231", "283", "41", "304", "194"} <= pool, "Rock, Oasis and Cave species")
check(any(o.get("target_area") == "ORRE_POKE_SPOTS" for o in orre["ORRE_DESERT"]["route_menu"]), "the Rock Poke Spot is off the Desert Trail")
story.current_area_key = "ORRE_POKE_SPOTS"
try:
    st = PlayState(g)
    g.change_state(st)
    st.draw()
    ok = True
except Exception as e:
    ok = False
    print("     ", type(e).__name__, e)
check(ok, "Poké Spots opens")

print("4) the walkthroughs' story beats (Bulbapedia: Colosseum, XD)")


def opts(area):
    a = orre[area]
    return [o.get("text") for o in (a.get("route_menu") or []) + (a.get("explore_options") or [])]


for area, text in (("OUTSKIRT_STAND", "OUTSKIRT STAND: WILLIE"), ("GATEON_PORT", "Professor Krane's Lab"),
                   ("MT_BATTLE", "DAKIM ATTACKS MT. BATTLE"), ("SHADOW_PKMN_LAB", "SHADOW POKEMON LAB: EIN"),
                   ("PHENAC_CITY", "PHENAC STADIUM: SNATTLE"), ("RELIC_FOREST", "HO-OH AT THE RELIC STONE"),
                   ("PYRITE_CAVE", "PYRITE CAVE: MIROR B."), ("SNAGEM_HIDEOUT", "SNAGEM HIDEOUT: GONZAP")):
    check(text in opts(area), f"{area}: {text}")
pool = [s for a in orre.values() for s in a.get("shadow_pool") or []]
for s_ in pool:
    story.story_flags[s_["flag"]] = True
check(not story.special_condition("orre_all_purified"), "all snagged but none purified: no Ho-Oh yet")
for s_ in pool:
    story.story_flags[f"purified_line_{fm[str(s_['id'])]['id']}"] = True
story.player_team = [Pokemon(g.loader.fetch_specific(9348), g.assets, size_mult=2.5)]  # a kept Shadow Bayleef
check(story.special_condition("orre_all_purified"), "every line purified once: Ho-Oh comes, even with a Shadow Pokemon kept")
story.story_flags[pool[0]["flag"]] = False
check(not story.special_condition("orre_all_purified"), "one not snagged: no Ho-Oh yet")
story.story_flags[pool[0]["flag"]] = True

print("5) Shadow evolution and keeping Shadow Pokemon (Jordan, 10-27; not in the games)")
from src.pokemon import evolution
new_forms = {k: v for k, v in fm.items() if v.get("form") == "shadow" and int(k) >= 9601}
check(len(new_forms) >= 30 and all(v["id"] <= 386 for v in new_forms.values()), f"{len(new_forms)} Shadow evolutions, Gen 3 or earlier")
check(all(os.path.exists(f"assets/sprites/pokemon/{k}.png") for k in new_forms), "each has a Shadow sprite")
bay = Pokemon(g.loader.fetch_specific(9348), g.assets, size_mult=2.5)
bay.level = 40
check("MEGANIUM_SHADOW" in evolution.ready_evolutions(g, bay), f"Shadow Bayleef -> Shadow Meganium {evolution.ready_evolutions(g, bay)}")
mega = g.loader.fetch_specific(154, form="shadow")
check("SHADOW" in mega["name"].upper() and mega["img"], f"Shadow Meganium loads with its art ({mega['name']})")
mega_id = int(next(k for k, v in new_forms.items() if v["id"] == 154))
story.player_team = [Pokemon(g.loader.fetch_specific(mega_id), g.assets, size_mult=2.5)]
story.purify_slot(0)
check(story.story_flags.get("purified_line_153") and story.player_team[0].id == 154,
      "purifying a Shadow Meganium counts for the Bayleef line")
story.inventory["SNAG_MACHINE"] = 1
story.current_area_key = "ORRE_DESERT"
for s_ in orre["ORRE_DESERT"]["shadow_pool"]:
    story.story_flags[s_["flag"]] = True
st = PlayState(g)
g.change_state(st)
st.show_progression_menu()
btns = [b.text for b in st.route_buttons]
check("SNAG AGAIN" in btns and "SNAG SHADOW POKEMON" not in btns, f"area cleared: SNAG AGAIN for another copy {btns}")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
