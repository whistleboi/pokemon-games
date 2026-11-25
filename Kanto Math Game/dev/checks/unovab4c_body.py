# Unova batch 4c (11-24): Nimbasa's Pokemon Musical (Black 2's 100 Props and five stages from the file; Dress Up snaps
# each Prop to its spot, a show with three math spotlights, the owner's review, fans with Props) and Big Stadium / Small
# Court (the day's field by the real clock, the ushers in game hours, the athletes by badges, the post-game visitors).
#   bash dev/checks/run.sh unovab4c
import datetime
import json
import os
from src.states.overworld import CityState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
flags["visited_NIMBASA_CITY"] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
from src.world import musical as M, nimbasa_sports as NS


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts: shared, Checks C5)


def people(st):
    out = {}
    for home, o in (getattr(st, "people", None) or {}).items():
        for c in _opts(o):
            if isinstance(c, dict) and st._shown(c):
                out[str(c.get("text", "")).rstrip()] = home
    return out


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(40)
    return True


print("1) the Musical's data: Black 2's Props, stages and songs")
D = M.data(g)
check(len(D["props"]) == 100 and D["props"][0]["name"] == "Pink Barrette" and D["props"][99]["name"] == "Gift Box",
      "100 Props, named by the file (system text 93)")
check(all(os.path.isfile("assets/musical/props/p%02d.png" % i) for i in range(100)), "every Prop's own picture (a/0/4/4)")
check(all(os.path.isfile("assets/musical/" + s["stage"]) for s in D["shows"]) and len(D["shows"]) == 4,
      "four shows, each on Black 2's own stage (a/0/4/6)")
check(all(os.path.isfile("assets/music/" + s["song"] + ".ogg") for s in D["shows"]) and os.path.isfile("assets/music/unova/msl_dressup.ogg"),
      "each show's song and the Dress Up music, rendered from the file")
check({D["props"][p]["name"] for p in M.START_PROPS} == {"Top Hat", "Blue Barrette", "Square Glasses", "Maraca", "Umber Belt", "Tie"},
      "the Prop Case's first Props: the ones zone 606's lines name")
check(M.fan_count(0) == 1 and M.fan_count(2400) == 10 and M.fan_count(1100) == 8, "the fans: Black 2's steps x 0.2 (all ten at 2,400)")

print("2) the theater: the owner's Prop Case, the TM lady")
nim = tmaps["NIMBASA_CITY"]
check("49,17" in (nim.get("inside") or {}) and nim["inside"]["49,17"] == "musical", "the Musical Theater's door leads in")
for k in ("b2_prop_case", "b2_props", "b2_musical_tm49"):
    flags.pop(k, None)
st = town("NIMBASA_CITY", (14, 19), "musical", (0, -1))
settle(200)
check(flags.get("b2_prop_case") and set(M.START_PROPS) <= set(M.props(g)), "first visit: the owner hands over the Prop Case and its Props")
st = town("NIMBASA_CITY", (8, 12), "musical", (0, -1))
ps = people(st)
check({"Musical receptionist", "Theater owner", "Rival stylist", "Woman by the posters"} <= set(ps), f"the theater's people ({len(ps)})")
check(not any(k.startswith("Fan ") for k in ps), "no fans waiting before your first show")
inv0 = story.inventory.get("TM277", 0)
talk(st, "Woman by the posters")
check(story.inventory.get("TM277", 0) == inv0 + 1, "TM49 Echoed Voice (our TM277) from the woman by the posters")

print("3) a Musical: pick, Dress Up (snap to spots), the show with math spotlights, the review")
from src.states.musical import MusicalState
talk(st, "Musical receptionist")
ms = until(("MusicalState",), 300)
check(type(ms).__name__ == "MusicalState", "the receptionist starts a Musical")
if type(ms).__name__ == "MusicalState":
    mon = ms._team()[0]
    ms._click(("mon", mon))
    stardom = next(s for s in D["shows"] if s["key"] == "stardom")
    ms._click(("show", stardom))
    check(ms.stage == "dress", "a Pokemon and a show picked: Dress Up")
    for pid in M.START_PROPS:
        ms._click(("prop", pid))
    w = ms.worn
    check(w.get("head") == 59 and w.get("ear0") == 1 and w.get("face") == 8 and w.get("arm0") == 76 and w.get("waist") == 48
          and w.get("body") == 70, f"each Prop snaps to its spot: Top Hat head, Barrette ear, Glasses face, Maraca arm, Belt waist, Tie body ({w})")
    ms._click(("prop", 76))
    check("arm0" not in ms.worn, "tapping a worn Prop takes it off")
    ms._click(("prop", 76))
    ms.draw()
    ms._click(("done",))
    check(ms.stage == "show" and len(ms.performers) == 4, "on stage: you and three others")
    right = 0
    for _ in range(4000):
        ms.show_t += 50
        ms.update()
        if ms.math_ui is not None:
            ms._answer(ms.options.index(ms.answer)); right += 1
        ms.draw()
        if ms.stage != "show":
            break
    check(right == 3 and ms.performers[0].spot == 3, f"three spotlight questions, each right answer a spotlight ({right})")
    check(ms.stage == "photo" and ms.photo is not None, "the curtain falls: the photo")
    ms._next()
    check(ms.stage == "review" and any("Dress Up was very" in l for l in ms.review), "the owner's review")
    for _ in range(20):
        if g.current_state is not ms:
            break
        ms._next()
    settle(60)
check(flags.get("b2_musical_shows") == 1 and int(flags.get("b2_musical_score", 0)) > 0, "a show counted, its points kept")
nfans = len(flags.get("b2_musical_fans") or [])
check(nfans == M.fan_count(int(flags["b2_musical_score"])) and nfans >= 2, f"fans wait in the lobby ({nfans})")
st = town("NIMBASA_CITY", (8, 12), "musical", (0, -1))
ps = people(st)
check("Fan 1" in ps and "Fan %d" % (nfans + 1) not in ps, "the waiting fans stand in the lobby")
before = set(M.props(g))
talk(st, "Fan 1")
check(len(set(M.props(g)) - before) == 1, "a fan gives you a Prop")
talk(st, "Theater owner")
check(24 in M.props(g) and flags.get("b2_musical_cake"), "the owner's Toy Cake after the first show (Jordan's call)")
talk(st, "Rival stylist")
check("not going to lose" in heard(), "the rival stylist's notes on your show")
flags["b2_musical_wins"] = 5
talk(st, "Theater owner")
check(55 in M.props(g), "the Crown at five wins")

print("4) Big Stadium and Small Court: the day's field, game hours, ushers")
NS.NOW = datetime.datetime(2026, 11, 23, 9, 0)   # (a Monday morning: baseball and tennis, both in practice)
check(NS.sport("stadium") == "baseball" and NS.sport("court") == "tennis" and not NS.game_on("stadium"), "Monday: baseball, tennis; 9 AM practice")
story.badges["UNOVA"] = ["b2_basic", "b2_toxic", "b2_insect"]
st = town("NIMBASA_CITY", (9, 9), "stadium", (0, -1))
ps = people(st)
check("Usher" not in ps and "Kid by the panel" in ps, "practice: no ushers, the kid copying a pitcher")
st.step(0, -1); settle(120)
cur = g.current_state
check(getattr(cur, "room", None) == "field_baseball", f"the warp panel: onto the baseball field ({getattr(cur, 'room', None)})")
ps = people(cur)
check({"Infielder Alex", "Infielder Connor", "Infielder Todd"} <= set(ps), f"the Infielders practise ({sorted(ps)[:6]})")
check(not any("Backers" in k for k in ps), "3 badges: no Backers yet")
check(not any(k.startswith(("Ace Trainer", "Lass", "Waiter")) for k in ps), "no post-game visitors before the League")
talk(cur, "Infielder Alex")
bi = until(("TrainerIntroState", "TrainerBattleState"), 300)
b = getattr(bi, "next_state", bi)
lv = [getattr(p, "level", 0) for p in getattr(b, "opponent_team", []) or []]
check(type(bi).__name__ in ("TrainerIntroState", "TrainerBattleState") and lv[:1] == [24], f"Infielder Alex battles: Black 2's 3-4 badge team, Lv 24 ({lv})")
check((getattr(b, "rewards", {}) or {}).get("POTION") == 1, "his prize: a Potion (Black 2's for that tier)")
st = town("NIMBASA_CITY", (9, 60), "field_baseball", (0, 1))
st.step(0, 1); settle(120)
cur = g.current_state
check(getattr(cur, "room", None) == "stadium" and tuple(cur.player) == (9, 9), f"the field's panel: back to the lobby ({getattr(cur, 'room', None)}, {getattr(cur, 'player', None)})")
story.badges["UNOVA"] += ["b2_bolt", "b2_quake"]
check("Backers Ami & Eira" in people(town("NIMBASA_CITY", (9, 59), "field_baseball", (0, -1))), "5 badges: the Backers join")
NS.NOW = datetime.datetime(2026, 11, 23, 15, 0)   # (Monday 3 PM: a baseball game)
st = town("NIMBASA_CITY", (9, 12), "stadium", (0, -1))
ps = people(st)
check({"Usher"} <= set(ps) and "Kid by the panel" not in ps, "game time: the ushers stand before the panel")
check({"Cheering fan", "Dizzy fan"} <= set(people(town("NIMBASA_CITY", (15, 27), "stadium_stands", (0, -1)))), "and the stands cheer")
NS.NOW = datetime.datetime(2026, 11, 24, 9, 0)   # (Tuesday: soccer, basketball)
check(NS.sport("stadium") == "soccer" and NS.sport("court") == "basketball", "Tuesday: soccer and basketball")
st = town("NIMBASA_CITY", (9, 9), "court", (0, -1))
st.step(0, -1); settle(120)
check(getattr(g.current_state, "room", None) == "court_basketball", "Small Court's panel: onto the basketball court")
story.badges["UNOVA"] = ["x"] * 8
_tier = NS.tier
NS.tier = lambda _s: 4   # (the post-game tier: a real Champion flag would open the next region's pick on arrival)
today = NS.visitors_today()
room = {"stadium": "field_soccer", "court": "court_basketball"}[today["arena"]]
if NS.tier(story) == 4:
    _st = town("NIMBASA_CITY", (10, 27) if room == "field_soccer" else (6, 23), room, (0, -1))
    ps = people(_st)
    names = [v["battle"]["name"] for v in NS.data()["visitors"] if v["id"] in today["slots"]]
    check(all(n in ps for n in names), f"after the League: today's three visitors on {room} ({names}; {sorted(ps)})")
else:
    check(False, "the post-game tier")
NS.tier = _tier
NS.NOW = None

print("5) the data: athletes by tier, visitors, pictures, music")
SD = NS.data()
check(len(SD["athletes"]) == 25 and len(SD["visitors"]) == 52, "25 athletes and Backers pairs, 52 post-game visitors (Black 2's)")
check(sorted(SD["athletes"]["Infielder Alex"]["tiers"]) == ["1", "2", "3", "4"], "an athlete's four tiers")
miss = sorted({e["sprite"] for a in SD["athletes"].values() for e in a["tiers"].values()} | {v["battle"]["sprite"] for v in SD["visitors"]})
miss = [p for p in miss if not os.path.isfile(os.path.join("assets", "sprites", "trainers", p))]
check(not miss, f"every battle picture ({miss})")
blob = json.dumps(json.load(open("assets/music/unova/music.json", encoding="utf-8")))
check("msl_field" in blob, "the theater's own music")

for f in fails:
    print("  -", f)
print(f"##### {len(fails)} failures")
