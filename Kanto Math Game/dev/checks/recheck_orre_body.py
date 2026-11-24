
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
check(len(ids) == 134 and len(set(ids)) == 134, f"{len(ids)} shadows (131 + 3 Kanto starters), {len(set(ids))} species")


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


import json as _rj
_PREV = {}
for _pr in _rj.load(open("assets/pokemon_levels.json", encoding="utf-8"))["pairs"]:
    _x, _y = (int(v) for v in _pr.split(">"))
    _PREV.setdefault(_y, _x)


def _line(pid):
    """The first stage of a Pokemon's evolution line (a Shadow id stays itself)."""
    seen = set()
    while pid in _PREV and pid not in seen:
        seen.add(pid)
        pid = _PREV[pid]
    return pid


print("2) the bosses' teams from the games")
for name, team in (("Cipher Admin Dakim", [229, 330, 205, 340, 344]), ("Cipher Admin Ein", [310, 121, 112, 279, 169]),
                   ("Cipher Admin Venus", [350, 182, 26, 40, 200]), ("Cipher Head Evice", [9399, 373, 68, 212, 289, 199]),
                   ("Cipher Admin Lovrina", [370, 267, 315, 9408]), ("Cipher Admin Gorigan", [305, 364, 199, 217, 9313, 9324]),
                   ("Grand Master Greevil", [9331, 9346, 9326, 9341, 9344, 9345]), ("Pre Gym Leader Justy", [27, 331, 207, 192, 184, 299]),
                   ("Cipher Admin Miror B.", [348, 272, 272, 55, 294]), ("Cipher Nascour", [9431, 282, 178, 356, 365, 257]),
                   ("Cipher Admin Snattle", [375, 195, 212, 9422, 351, 9335]), ("Cipher Admin Ardos", [9403, 65, 230, 214, 9338, 9343]),
                   ("Cipher Admin Eldes", [291, 9412, 9430, 330, 9327, 9342]), ("Snagem Head Gonzap", [101, 274, 45, 340, 227])):
    t = [x for x in find(name) if len(x["team"]) == len(team) and all(_line(a_) == _line(b_) for a_, b_ in zip(x["team"], team))]
    # (11-24, L1: each Pokemon at the stage its level fits - Flygon at Lv 34 is a Trapinch - so the game's team is matched
    #  line by line, by evolution family. Dakim, Ein and Snattle also have earlier story battles; Lovrina: her Cipher Lab
    #  battle from the XD disc since batch 5a - her later team comes with Citadark, batch 8)
    check(t and len(t[0]["levels"]) == len(team), f"{name}")
gv = next(o for o in orre["XD_CITADARK_ISLE"]["route_menu"] if "GREEVIL" in o["text"])
_st = gv["event"]["stages"]   # (batch 8a: XD's own order - Snattle, Ardos at the Dome's door, Eldes behind the glass, whose fall opens
check(len(_st) == 2 and "xd_xd001" in _st[1]["requires"], "Greevil: XD001 first, then his six (the way up gated on the map: Ardos, the glass, Eldes)")

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


import json as _json
_willie = _json.dumps(_json.load(open("assets/town_maps.json", encoding="utf-8"))["OUTSKIRT_STAND"])
check("Rider Willie" in _willie, "OUTSKIRT_STAND: Rider Willie (in the diner, on the walked map)")   # (11-23: his old menu button is gone)
for area, text in (("GATEON_PORT", "Professor Krane's Lab"),
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
bay.evo_due = True  # (it just levelled up)
check("MEGANIUM_SHADOW" in evolution.ready_evolutions(g, bay), f"Shadow Bayleef -> Shadow Meganium {evolution.ready_evolutions(g, bay)}")
mega = g.loader.fetch_specific(154, form="shadow")
check("SHADOW" in mega["name"].upper() and mega["img"], f"Shadow Meganium loads with its art ({mega['name']})")
mega_id = int(next(k for k, v in new_forms.items() if v["id"] == 154))
story.player_team = [Pokemon(g.loader.fetch_specific(mega_id), g.assets, size_mult=2.5)]
story.purify_slot(0)
check(story.story_flags.get("purified_line_153") and story.player_team[0].id == 154,
      "purifying a Shadow Meganium counts for the Bayleef line")
story.inventory["SNAG_MACHINE"] = 1
story.story_flags["got_snag_machine"] = True   # (Snag menus open once Phenac's guards are beaten: the pilot, 11-20)
story.current_area_key = "ORRE_DESERT"
for s_ in orre["ORRE_DESERT"]["shadow_pool"]:
    story.story_flags[s_["flag"]] = True
g.dungeon_routes = True   # (R1, 11-23: on the walked desert, as a player meets them - not the old route menu)
story.last_area_key = "OUTSKIRT_STAND"
st = PlayState(g)
g.change_state(st)
for _ in range(3):
    g.current_state.update()
st = g.current_state
btns = [i.get("text") for i in getattr(st, "placed", [])]
check(type(st).__name__ == "DungeonState" and "SNAG AGAIN" in btns and "SNAG SHADOW POKEMON" not in btns,
      f"area cleared: SNAG AGAIN stands on the walked desert for another copy {btns}")

print(f"##### {fails} failures")
