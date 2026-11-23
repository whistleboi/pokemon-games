
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

print("JOHTO: the book's data")
jb = book["JOHTO"]
jmissions = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}
jids = [c["mission"] for a in jb for c in a["chapters"]]
check(all(i in jmissions for i in jids), "every Johto chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in jb for c in a["chapters"]), "every Johto chapter has a title and a page")
jmain = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["type"] == "MAIN" and m["id"].startswith("johto_")]
check(sorted(set(jmain) - set(jids)) == [], f"every Johto story mission is in the book (missing: {sorted(set(jmain) - set(jids))})")
said = " ".join(c["say"] for a in jb for c in a["chapters"]).lower()
check(not re.search(r"\b(because|so that|in order to)\b", said), "Johto's pages never spell out why")
jk = [k for k, a in prog.items() if str(a.get("region", "KANTO")).upper() == "JOHTO"]
jused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in jk]) + json.dumps([tmaps[k] for k in jk if k in tmaps])))
jgiven = []
from src.pokemon import items as _items
for f in ft["JOHTO"]:
    for t in f["tiers"]:
        r = t[1]
        jgiven += [r["tm"]] if isinstance(r.get("tm"), str) else list(r.get("tm") or [])
        check(all(_items.describe(i) for i in (r.get("items") or {})), f"{f['id']}: every reward item is real ({r.get('items')})")
check(all(k in tms for k in jgiven), "every Johto Feat TM is a real TM")
check(not (set(jgiven) & jused), f"no Johto Feat TM is also on Johto's maps / people ({sorted(set(jgiven) & jused)})")
check(len(jgiven) == len(set(jgiven)), "no TM is given by two Johto Feats")
check(not (set(jgiven) & set(tutors.tutor_tms(g, "JOHTO"))), "no Johto Feat TM is a Johto tutor's")
check(all([t[0] for t in f["tiers"] if t[0] != "all"] == sorted(t[0] for t in f["tiers"] if t[0] != "all") for f in ft["JOHTO"]),
      "Johto's tiers go up")

print("JOHTO: chapters follow the story, New Bark to Mt. Silver")
story.starting_region = "JOHTO"
story.badges = {r: [] for r in story.badges}
story.badges["JOHTO"] = []
for k in [k for k in story.story_flags if k.startswith(("visited_", "feat_"))]:
    story.story_flags.pop(k)
flags = story.story_flags
flags.update({"received_starter_johto": True, "has_johto_starter": True, "received_pokedex_johto": True})
story.current_area_key = "NEW_BARK_TOWN"; flags["visited_NEW_BARK_TOWN"] = True
city = CityState(g); g.change_state(city)


def at(area):
    story.current_area_key = area
    flags["visited_" + area] = True


def badge(name, flag=None):
    story.badges["JOHTO"].append(name)
    if flag:
        flags[flag] = True


def item(k, n=1):
    story.inventory[k] = n


def want(arc, chapter, why):
    check(now() == (arc, chapter), f"{why}: {chapter} ({now()})")


want("Winds of a New Beginning", "The Professor's Errand", "a new Johto game")
a0 = quest_book.arcs(g)[0]
check([c["title"] for c in a0["chapters"]] == ["The Professor's Errand"], "Mr. Pokemon and the stranger aren't in the book yet")
at("JOHTO_ROUTE_29"); at("CHERRYGROVE_CITY")
want("Winds of a New Beginning", "Mr. Pokemon's Discovery", "in Cherrygrove")
flags["met_mr_pokemon"] = True; item("MYSTERY_EGG"); at("MR_POKEMONS_HOUSE")
want("Winds of a New Beginning", "A Stranger in Cherrygrove", "the Egg in hand")
flags["defeated_rival_cherrygrove"] = True; at("CHERRYGROVE_CITY")
want("Winds of a New Beginning", "Trouble at the Lab", "the stranger beaten")
flags["elm_received_egg"] = True; story.inventory.pop("MYSTERY_EGG", None); at("VIOLET_CITY")
want("The Zephyr Badge", "The Swaying Tower", "the Egg shown to Elm")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
check(any(r["kind"] == "chapter" and r["title"] == "???" for r in jn.rows), "Johto: the Gym's chapter, still to come, shows as ???")
g.change_state(city)
check(quest_book.arcs(g)[0]["state"] == "done", "the first arc is finished")
flags["defeated_elder_li"] = True
want("The Zephyr Badge", "Wings Over Violet", "the Sages beaten")
badge("ZEPHYR", "badge_zephyr_earned")
want("The Hive Badge", "Under the Ground", "the Zephyr Badge")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
check(any(r["mission"]["id"] == "johto_s_togepi" for r in jn.rows), "SIDE: Elm's aide's Egg in Violet")
check(any(r["mission"]["id"] == "johto_s_trades" for r in jn.rows), "SIDE: Johto's trades")
g.change_state(city)
at("UNION_CAVE"); at("AZALEA_TOWN")
want("The Hive Badge", "The Well of Tails", "in Azalea")
check((guide.tracked_mission(g) or {}).get("id") == "johto_m5", "the marker follows the Well")
flags["slowpoke_well_cleared"] = True
want("The Hive Badge", "The Bug Master", "the Well cleared")
badge("HIVE")
want("The Plain Badge", "The Runaway Bird", "the Hive Badge")
flags["got_hm_cut_johto"] = True; at("ILEX_FOREST")
want("The Plain Badge", "The Big City", "Cut")
at("GOLDENROD_CITY")
want("The Plain Badge", "Rumours on Route 36", "in Goldenrod")
flags["saw_odd_tree"] = True
want("The Plain Badge", "The Unstoppable Miltank", "the odd tree seen")
badge("PLAIN")
want("The Fog Badge", "The Tree That Wiggled", "the Plain Badge")
flags["defeated_sudowoodo"] = True; at("ECRUTEAK_CITY")
want("The Fog Badge", "Ashes of the Burned Tower", "the tree out of the way")
flags["defeated_rival_burned_tower"] = True
want("The Fog Badge", "Three Beasts Awaken", "the rival beaten in the tower")
flags["johto_beasts_fled"] = True
want("The Fog Badge", "The Mystic Seer", "the beasts fled")
badge("FOG")
want("The Storm Badge", "The Dancers' Trouble", "the Fog Badge")
item("HM_SURF")
want("The Storm Badge", "Across the Whirling Sea", "Surf")
at("CIANWOOD_CITY")
want("The Storm Badge", "The Secret Potion", "in Cianwood: the pharmacy first, the Gym can wait")
item("SECRET_POTION")
want("The Storm Badge", "The Waterfall Fighter", "the Secret Potion")
badge("STORM"); at("OLIVINE_CITY")
want("The Mineral Badge", "A Light for the Sea", "the Storm Badge")
check((guide.tracked_mission(g) or {}).get("id") == "johto_m13", "the marker leads to the lighthouse, potion in hand")
flags["ampharos_cured"] = True; story.inventory.pop("SECRET_POTION", None)
want("The Mineral Badge", "The Steel-Clad Defense", "Amphy cured")
story.badges["JOHTO"].remove("STORM"); story.inventory["SECRET_POTION"] = 0; flags.pop("ampharos_cured")
at("CIANWOOD_CITY"); story.badges["JOHTO"].append("STORM")
check((guide.tracked_mission(g) or {}).get("id") == "johto_m11", "Chuck beaten first: the Journal sends you back for the potion, not to the lighthouse")
item("SECRET_POTION"); flags["ampharos_cured"] = True; story.inventory.pop("SECRET_POTION", None)
st = {c["title"]: c["state"] for a in quest_book.arcs(g) if a["title"] == "The Storm Badge" for c in a["chapters"]}
check(set(st.values()) == {"done"}, f"the Storm arc is finished, the potion and all ({st})")
badge("MINERAL")
want("The Glacier Badge", "The Red Gyarados", "the Mineral Badge")
flags["defeated_red_gyarados"] = True
want("The Glacier Badge", "The Shop with No Customers", "the red Gyarados")
flags["rocket_hq_cleared"] = True
want("The Glacier Badge", "Ice on the Floor", "the hideout cleared")
badge("GLACIER")
want("Voices on the Radio", "The Tower Taken", "the Glacier Badge")
item("BASEMENT_KEY")
want("Voices on the Radio", "Under Goldenrod", "the Basement Key")
item("CARD_KEY")
want("Voices on the Radio", "The Top of the Tower", "the Card Key")
flags["radio_tower_cleared"] = True; story.inventory.pop("CARD_KEY", None); story.inventory.pop("BASEMENT_KEY", None)
want("The Rising Badge", "The Ice Path", "the Radio Tower freed")
st = {c["title"]: c["state"] for a in quest_book.arcs(g) if a["title"] == "Voices on the Radio" for c in a["chapters"]}
check(len(st) == 3 and set(st.values()) == {"done"}, f"the keys used up, the Radio Tower's chapters stay done ({st})")
at("BLACKTHORN_CITY")
want("The Rising Badge", "The Dragon Tamer", "in Blackthorn")
flags["johto_beat_clair"] = True
want("The Rising Badge", "The Elder's Questions", "Clair beaten")
badge("RISING")
want("Bells of Ecruteak", "Three Wise Sages", "eight badges")
flags["wise_trio_beaten"] = True
want("Bells of Ecruteak", "A Wing of Many Colours", "the Wise Trio beaten")
flags["got_rainbow_wing"] = True; item("RAINBOW_WING")
want("The Silver League", "Victory Road", "the Rainbow Wing")
at("SILVER_LEAGUE_PLATEAU")
want("The Silver League", "The Elite Four", "at the League")
flags["beat_johto_champion"] = True; flags["unlocked_national_dex"] = True
want("The Silent Summit", "The Trainer in the Snow", "Champion")
check(all(a["state"] == "done" for a in quest_book.arcs(g)[:-1]), "every arc before the summit is finished")

print("JOHTO: Feats and their counters")
at("JOHTO_ROUTE_29")


def _apricorn(o):
    if isinstance(o, dict):
        if o.get("daily") and any(k.endswith("_APRICORN") for k in (o.get("gift_item") or {})):
            return o
        o = list(o.values())
    if isinstance(o, list):
        for v in o:
            r = _apricorn(v)
            if r:
                return r


ev = _apricorn(tmaps["JOHTO_ROUTE_29"])
for k in [k for k in story.story_flags if k.startswith("apricorn_")]:
    story.story_flags.pop(k)
item("APRICORN_BOX")
from src.states.overworld import _run_story_event
before = feats.value(story, {"count": "apricorns"}, "JOHTO")
_run_story_event(city, ev, lambda c: True, lambda lines: None)
check(feats.value(story, {"count": "apricorns"}, "JOHTO") == before + 1, "an Apricorn picked off a tree counts for Apricorn Picker")
for kind, n in (("contests", 1), ("contest_wins", 1), ("headbutt", 5), ("smash", 3)):
    feats.note(story, kind, n)
paid = feats.pay(story)
for name in ("Bug Catcher", "Contest Champion", "Tree Shaker", "Rock Breaker"):
    check(any(name in l for l in paid), f"{name} Bronze paid ({[l for l in paid if name in l][:1]})")
check(feats.value(story, {"count": "headbutt"}, "KANTO") == 0, "Johto's counts are Johto's")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["JOHTO"]), "FEATS lists Johto's feats")
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "contests"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_johto_feats.png"))
jn.set_tab("STORY"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_johto_story.png"))
g.change_state(city)

print("ORANGE: the book's data")
ob = book["ORANGE"]
oids = [c["mission"] for a in ob for c in a["chapters"]]
check(all(i in jmissions for i in oids), "every Orange chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in ob for c in a["chapters"]), "every Orange chapter has a title and a page")
UMBRELLA = {"orange_m2", "orange_m3"}   # (the old all-four-badges / League missions: always behind a more exact one)
omain = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["type"] == "MAIN" and m["id"].startswith("orange_")]
check(sorted(set(omain) - set(oids) - UMBRELLA) == [], f"every Orange story mission is in the book (missing: {sorted(set(omain) - set(oids) - UMBRELLA)})")
said = " ".join(c["say"] for a in ob for c in a["chapters"]).lower()
check(not re.search(r"\b(because|so that|in order to)\b", said), "Orange's pages never spell out why")
ok_ = [k for k, a in prog.items() if str(a.get("region", "")).upper() == "ORANGE"]
oused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in ok_]) + json.dumps([tmaps[k] for k in ok_ if k in tmaps])))
ogiven = []
for f in ft["ORANGE"]:
    for t in f["tiers"]:
        r = t[1]
        ogiven += [r["tm"]] if isinstance(r.get("tm"), str) else list(r.get("tm") or [])
        check(all(_items.describe(i) for i in (r.get("items") or {})), f"{f['id']}: every reward item is real ({r.get('items')})")
check(all(k in tms for k in ogiven), "every Orange Feat TM is a real TM")
check(not (set(ogiven) & oused), f"no Orange Feat TM is also on Orange's maps / people ({sorted(set(ogiven) & oused)})")
check(len(ogiven) == len(set(ogiven)), "no TM is given by two Orange Feats")
check(not (set(ogiven) & set(tutors.tutor_tms(g, "ORANGE"))), "no Orange Feat TM is an Orange tutor's")

print("ORANGE: chapters follow the story, Valencia to the Ice Sphere")
story.starting_region = "ORANGE"
story.badges = {r: [] for r in story.badges}
story.badges["ORANGE"] = []
for k in [k for k in story.story_flags if k.startswith(("visited_", "feat_"))]:
    story.story_flags.pop(k)
at("VALENCIA_ISLAND")
city = CityState(g); g.change_state(city)


def done_(cond):
    if isinstance(cond, list):
        for c in cond:
            done_(c)
    elif cond.startswith("has_item:"):
        item(cond[9:])
    else:
        flags[cond] = True


SCENES = {"orange_m0f": ["orange_met_misty", "orange_park_tourists"]}   # (Pokemon Park's scenes, met on the way to town)
steps_done = 0
for arc in ob:
    for ch in arc["chapters"]:
        m = jmissions[ch["mission"]]
        want(quest_book._words(story, arc["title"]), quest_book._words(story, ch["title"]), f"[{m['id']}]")
        if ch["mission"] == "orange_m2a":
            jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
            check(any(r["mission"]["id"] == "orange_s_tyrogue" for r in jn.rows), "SIDE: Mikan's Tyrogue")
            jn.set_tab("STORY"); jn.draw()
            check(any(r["kind"] == "chapter" and r["title"] == "???" for r in jn.rows) or arc["chapters"][-1] is ch,
                  "Orange: chapters still to come show as ???")
            g.change_state(city)
        for i in ch.get("steps") or []:
            done_(m["steps"][i]["done"])
        if not ch.get("steps") or ch["steps"][-1] == len(m.get("steps") or []) - 1:
            for f in story.mission_flags(m):
                flags[f] = True
            if m.get("completed_badge"):
                story.badges["ORANGE"].append(m["completed_badge"])
            done_(SCENES.get(m["id"], []))
            if m.get("target"):
                at(m["target"])
        steps_done += 1
check(steps_done == len(oids), "every Orange chapter was played")
check(all(a["state"] == "done" for a in quest_book.arcs(g)), "the whole Orange book is finished")
isl = next(f for f in ft["ORANGE"] if f["id"] == "islands")
n = feats.value(story, isl, "ORANGE")
check(10 <= n < feats.goal(story, isl, isl["tiers"][-1], "ORANGE"), f"Island Hopper counts the islands you set foot on ({n})")
orig = next(f for f in ft["ORANGE"] if f["id"] == "variants")
ids = feats._form_ids(story, orig)
pools = {int(x) for k, v in g.loader.area_data.items() if k.startswith("ORANGE_") and k.endswith("_PERCENTAGES") and isinstance(v, dict)
         for x in v if str(x).isdigit()}
bosses = {int(a["area_boss"]["id"]) for k, a in prog.items() if k in ok_ and (a.get("area_boss") or {}).get("catchable")}
check(len(ids) >= 50 and ids <= pools | bosses, f"Orange Variants: every form it counts can be caught in Orange ({sorted(ids - pools - bosses)})")
check(feats.goal(story, orig, orig["tiers"][-1], "ORANGE") == len(ids), f"Orange Variants' last tier is all of them ({len(ids)})")
dex = g.data.data.setdefault("pokedex", {})
before = feats.value(story, orig, "ORANGE")
for n, sid in enumerate(sorted(ids)[:10]):
    dex[f"orig_{sid}"] = {"id": sid, "name": "x"}
check(feats.value(story, orig, "ORANGE") == before + 10, "ten Pinkan Pokemon caught count ten")
paid = feats.pay(story)
check(any("Island Hopper" in l for l in paid), f"Island Hopper Bronze paid ({[l for l in paid if 'Island' in l][:1]})")
check(any("Orange Variants" in l for l in paid), f"Orange Variants Bronze paid ({[l for l in paid if 'Variants' in l][:1]})")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["ORANGE"]), "FEATS lists Orange's feats")
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "islands"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_orange_feats.png"))
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "variants"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_orange_variants.png"))
jn.set_tab("STORY"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_orange_story.png"))
g.change_state(city)

print("Other regions: no book yet, each story mission an arc of its own")
story.current_area_key = next(k for k, a in prog.items() if str(a.get("region", "")).upper() == "HOENN")
a = quest_book.arcs(g)
check(a and all(c.get("title") for x in a for c in x["chapters"]), f"Hoenn's missions show as arcs ({len(a)})")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
jn.set_tab("FEATS"); jn.draw()
check(jn.rows == [], "no Feats in a region without its list yet")
print(f"{fails} fails")
