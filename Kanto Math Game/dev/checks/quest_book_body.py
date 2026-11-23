
# The Quest Book (Jordan, 11-22; kanto_handoff/QUEST_BOOK_DESIGN.md): the Journal's STORY tab as arcs and chapters
# (assets/quest_book.json), SIDE errands, FEATS with tiers (assets/quest_feats.json). Kanto is the pilot.
import json, re
import pygame
from src.states.overworld import CityState
from src.states.systems import JournalState
from src.world import quest_book, feats, guide
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def tap(st, pos):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
missions = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}
book = quest_book.table(g)
ft = feats.table(g)

print("The book's data: every chapter names a real mission, has a title and a page")
kb = book["KANTO"]
ids = [c["mission"] for a in kb for c in a["chapters"]]
check(all(i in missions for i in ids), "every chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in kb for c in a["chapters"]), "every chapter has a title and a page")
kanto_main = [m["id"] for m in g.loader.area_data["GAME_CONFIG"]["JOURNAL_MISSIONS"] if m["type"] == "MAIN"]
check(sorted(set(kanto_main) - set(ids)) == [], f"every Kanto story mission is in the book (missing: {sorted(set(kanto_main) - set(ids))})")
said = " ".join(c["say"] for a in kb for c in a["chapters"]).lower()
check(not re.search(r"\b(because|so that|in order to)\b", said), "the pages never spell out why")

print("Feats: real rewards, Kanto's own TMs not given anywhere else in Kanto")
tms = json.load(open("assets/tms.json", encoding="utf-8"))
kanto = [k for k, a in prog.items() if str(a.get("region", "KANTO")).upper() == "KANTO"]
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
used = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in kanto]) + json.dumps([tmaps[k] for k in kanto if k in tmaps])))
given = []
for f in ft["KANTO"]:
    for t in f["tiers"]:
        r = t[1]
        given += [r["tm"]] if isinstance(r.get("tm"), str) else list(r.get("tm") or [])
check(all(k in tms for k in given), "every Feat TM is a real TM")
check(not (set(given) & used), f"no Feat TM is also on Kanto's maps / people ({sorted(set(given) & used)})")
check(len(given) == len(set(given)), "no TM is given by two Feats")
from src.pokemon import tutors
try:
    tut = set(tutors.tutor_tms(g, "KANTO"))
except Exception:
    tut = set()
check(not (set(given) & tut), "no Feat TM is a Kanto tutor's")
check(all(t[0] == "all" or (isinstance(t[0], int) and t[0] > 0) for f in ft["KANTO"] for t in f["tiers"]), "every tier has a goal")
check(all([t[0] for t in f["tiers"] if t[0] != "all"] == sorted(t[0] for t in f["tiers"] if t[0] != "all") for f in ft["KANTO"]),
      "tiers go up")

# A Kanto game, part way.
story.starting_region = "KANTO"
story.badges["KANTO"] = []
story.current_area_key = "PALLET_TOWN"
for k in [k for k in story.story_flags if k.startswith(("visited_", "kanto_catch_", "feat_"))]:
    story.story_flags.pop(k)
flags = story.story_flags
flags.update({"kanto_oak_led": True, "kanto_lab_intro": True, "received_starter_kanto": True, "got_oaks_parcel": True,
              "received_pokedex_kanto": True})
story.player_team = [mk(6)]
city = CityState(g); g.change_state(city)


def now():
    a, c = quest_book.current(g)
    return (a or {}).get("title"), (c or {}).get("title")


print("Chapters follow the story")
check(now()[0] == "The Boulder Badge", f"after the Pokedex: the Boulder Badge arc ({now()})")
story.badges["KANTO"] = ["BOULDER"]; flags["visited_PEWTER_CITY"] = True; flags["viridian_rocket_defeated"] = True
story.current_area_key = "KANTO_ROUTE_3"; flags["visited_KANTO_ROUTE_3"] = True
check(now() == ("The Cascade Badge", "East to the Mountain"), f"after Brock: east to Mt. Moon ({now()})")
arcs = quest_book.arcs(g)
cas = next(a for a in arcs if a["title"] == "The Cascade Badge")
titles = [(c["title"], c["state"]) for c in cas["chapters"]]
check(all(t != "Shadows in Mt. Moon" for t, s in titles), "Mt. Moon's Rockets aren't in the book before you've been there")
check(any(s == "later" for t, s in titles), "the arc's later chapters are still to come")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
check(any(r["kind"] == "chapter" and r["title"] == "???" for r in jn.rows), "chapters still to come show as ???")
q = next(i for i, r in enumerate(jn.rows) if r["title"] == "???")
jn.selected = q; jn._guide_layout(); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_hidden.png"))
check(not jn.btn_guide.visible, "no GUIDE ME on a chapter still to come")
g.change_state(city)
boulder = next(a for a in arcs if a["title"] == "The Boulder Badge")
check(boulder["state"] == "done", "the Boulder Badge arc is finished")
flags["visited_MT_MOON"] = True; story.current_area_key = "MT_MOON"
check(now()[1] == "Shadows in Mt. Moon", f"inside Mt. Moon: a Rocket chapter turns up ({now()})")
story.defeated_trainers.setdefault("MT_MOON", set()).add(11)
check(now()[1] == "Light at the End", f"Jessie and James beaten: on to the way out ({now()})")
flags["visited_CERULEAN_CITY"] = True; story.current_area_key = "CERULEAN_CITY"
check(now()[1] == "The Man in the Cottage", f"in Cerulean: Bill's cottage first, as the Journal leads ({now()})")
cas = next(a for a in quest_book.arcs(g) if a["title"] == "The Cascade Badge")
st = {c["title"]: c["state"] for c in cas["chapters"]}
check(st["East to the Mountain"] == st["Shadows in Mt. Moon"] == st["Light at the End"] == "done", f"the mountain's chapters are done ({st})")
check(st["The Tomboyish Mermaid"] in ("open", "later"), "Misty's chapter is still to come")
m = guide.tracked_mission(g)
check(m and m["id"] == "k_bill", "the marker follows the chapter being played (Bill)")

print("The Quest Book screen")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_story.png"))
row = jn._row()
check(jn.tab == "STORY" and row and row["kind"] == "chapter" and row["title"] == "The Man in the Cottage",
      "it opens on the chapter being played")
check(any(r["kind"] == "arc" and r["done"] for r in jn.rows), "finished arcs are listed")
check(jn.btn_guide.visible, "GUIDE ME on the current chapter")
jn.toggle_guide(); jn.toggle_guide()
check((guide.tracked_mission(g) or {}).get("id") == "k_bill", "GUIDE ME guides its mission")
jn.set_tab("SIDE"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_side.png"))
check(jn.rows and all(r["kind"] == "side" for r in jn.rows), "SIDE lists errands")
check(not any("Catch 30" in r["title"] for r in jn.rows), "the old catch missions are Feats now")
check(any(r["mission"]["id"] == "s_magikarp" for r in jn.rows), "new errands: the Magikarp salesman")

print("Feats pay once, per tier")
money = story.money
feats.note(story, "steps", 5000)
paid = feats.pay(story)
check(any("Walker" in l for l in paid) and story.inventory.get("SUPER_POTION", 0) >= 5, f"5,000 steps: Walker Bronze ({paid[:3]})")
check(feats.pay(story) == [], "and only once")
check(story.story_flags.get("feat_kanto_steps_1"), "its flag is set")
flags["kanto_catch_30"] = True
check(not any("Pokedex" in l for l in feats.pay(story)), "a catch milestone paid before isn't paid again")
for _ in range(12):
    story.note_answer("2 + 2", True)
paid = feats.pay(story)
check(any("Math Whiz" in l for l in paid), "10 right answers in a row: Math Whiz Bronze")
jn.set_tab("FEATS"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_feats.png"))
check(len(jn.rows) == len(ft["KANTO"]), "FEATS lists Kanto's feats")
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "steps"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_feat_page.png"))

print("Saves: feat counts kept, older saves load")
import copy
data = story.serialize()
check(data.get("feat_counts", {}).get("KANTO", {}).get("steps") == 5000, "the counts are saved")
keep = copy.deepcopy(data)
data.pop("feat_counts")
story.deserialize(data, g.loader)
check(getattr(story, "feat_counts", None) == {}, "a save without them loads (counting from now on)")
story.deserialize(keep, g.loader)
check(story.feat_counts.get("KANTO", {}).get("steps") == 5000, "and a save with them gets them back")

print("Other regions: no book yet, each story mission an arc of its own")
story.current_area_key = "NEW_BARK_TOWN"
a = quest_book.arcs(g)
check(a and all(c.get("title") for x in a for c in x["chapters"]), f"Johto's missions show as arcs ({len(a)})")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
jn.set_tab("FEATS"); jn.draw()
check(jn.rows == [], "no Feats in a region without its list yet")
print(f"{fails} fails")
