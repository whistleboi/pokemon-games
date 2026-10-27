
# The 10-27 Serebii PokéEarth recheck of Orre (Colosseum + XD): Shadow Pokemon, bosses, Poké Spots.
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
                   ("Miror B.", [348, 272, 272, 55, 294]), ("Cipher Nascour", [65, 282, 178, 356, 365, 257]),
                   ("Cipher Admin Snattle", [375, 195, 212, 338, 351, 121]), ("Cipher Admin Ardos", [277, 65, 230, 214, 125, 286]),
                   ("Cipher Admin Eldes", [291, 310, 373, 330, 105, 131]), ("Snagem Head Gonzap", [227, 342, 348, 68, 286, 210])):
    t = find(name)
    check(t and t[0]["team"] == team and len(t[0]["levels"]) == len(team), f"{name}")
gv = next(o for o in orre["XD_CITADARK_ISLE"]["route_menu"] if "GREEVIL" in o["text"])
check({"xd_snattle_beaten", "xd_ardos_beaten", "xd_eldes_beaten"} <= set(gv["condition"]), "Greevil after Snattle, Ardos and Eldes")

print("3) the Poké Spots")
pool = data[orre["ORRE_POKE_SPOTS"]["wild_pool_percentages"]]
check({"27", "207", "328", "187", "231", "283", "41", "304", "194"} <= set(pool), "Rock, Oasis and Cave species")
check(any(o.get("target_area") == "ORRE_POKE_SPOTS" for o in orre["ORRE_DESERT"]["route_menu"]), "reached from the Desert Trail")
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

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
