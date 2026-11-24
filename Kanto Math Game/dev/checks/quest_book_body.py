# The Quest Book (11-22): the book's machinery on Kanto's pilot data (screen, Feats, saves), Sevii in Kanto's book, regions without a book. Region parts: quest_book_<region>.
#   bash dev/checks/run.sh quest_book
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())


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


print("SEVII (in Kanto's book): after Blaine, and after the title")
flags = story.story_flags   # (the save/load above made a new flag table)
kmissions = {m["id"]: m for m in g.loader.area_data["GAME_CONFIG"]["JOURNAL_MISSIONS"]}
kmissions.update({k: v for k, v in jmissions.items() if k.startswith("sevii_")})
smain = [m for m in jmissions if m.startswith("sevii_") and jmissions[m]["type"] == "MAIN"]
kb_ids = [c["mission"] for a in book["KANTO"] for c in a["chapters"]]
check(sorted(set(smain) - set(kb_ids)) == [], f"every Sevii story mission is in Kanto's book (missing: {sorted(set(smain) - set(kb_ids))})")
check(sorted(set(kb_ids) - set(kmissions)) == [], "every Kanto chapter's mission exists")
story.starting_region = "KANTO"
story.badges = {r: [] for r in story.badges}
for k in [k for k in story.story_flags if k.startswith(("visited_", "feat_"))] + ["unlocked_national_dex", "beat_champion"]:
    story.story_flags.pop(k, None)
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO"]
arcs_k = book["KANTO"]
si = next(i for i, a in enumerate(arcs_k) if a["title"] == "The Sevii Islands")
for a in arcs_k[:si]:
    for ch in a["chapters"]:
        m = kmissions[ch["mission"]]
        for f in story.mission_flags(m):
            flags[f] = True
        for st_ in m.get("steps") or []:
            if isinstance(st_.get("done"), str):
                done_(st_["done"])
        if m.get("target"):
            flags["visited_" + m["target"]] = True
flags.update({"got_oaks_parcel": True, "received_pokedex_kanto": True, "received_starter_kanto": True, "kanto_oak_led": True,
              "kanto_lab_intro": True, "silph_co_cleared": True})
item("SILPH_SCOPE")
at("CINNABAR_ISLAND")
city = CityState(g); g.change_state(city)


def play(arcs_):
    for arc in arcs_:
        for ch in arc["chapters"]:
            m = kmissions[ch["mission"]]
            want(quest_book._words(story, arc["title"]), quest_book._words(story, ch["title"]), f"[{m['id']}]")
            if ch["title"] == "Into the Berry Forest":
                jn_ = JournalState(g, city); g.change_state(jn_); jn_.draw()
                pygame.image.save(g.screen, os.path.join(S, "quest_book_sevii_story.png"))
                g.change_state(city)
            for i in (ch.get("steps") if ch.get("steps") is not None else range(len(m.get("steps") or []))):
                d = m["steps"][i]["done"]
                done_(d["any"][0] if isinstance(d, dict) else d)
                if m["steps"][i].get("area"):
                    flags["visited_" + m["steps"][i]["area"]] = True
            if not ch.get("steps") or ch["steps"][-1] == len(m.get("steps") or []) - 1:
                for f in story.mission_flags(m):
                    flags[f] = True
                if m.get("target"):
                    at(m["target"])


SEVII_ITEMS = {"sevii_m2b": "RUBY", "sevii_m4": "RAINBOW_PASS"}
_play_one = play


def play(arcs_):
    for arc in arcs_:
        for ch in arc["chapters"]:
            _play_one([{"title": arc["title"], "chapters": [ch]}])
            m = ch["mission"]
            last = not ch.get("steps") or ch["steps"][-1] == len(kmissions[m].get("steps") or []) - 1
            if last and m in SEVII_ITEMS:
                item(SEVII_ITEMS[m])
            if last and m == "sevii_m2c":
                story.inventory.pop("RUBY", None)


play([arcs_k[si]])
story.badges["KANTO"].append("EARTH")
flags["beat_champion"] = True; at("INDIGO_PLATEAU")
want("The Network Machine", "A Bigger Pokedex", "Champion: Sevii again")
check(all(a["state"] == "done" for a in quest_book.arcs(g) if a["title"] in ("The Sevii Islands", "The Indigo Plateau")),
      "the Sevii arc and the League are finished")
play([next(a for a in arcs_k if a["title"] == "The Network Machine")])
check(quest_book.current(g) == (None, None) and all(a["state"] == "done" for a in quest_book.arcs(g)), f"Kanto's whole book is finished, Sevii and all ({quest_book.current(g)[1] and quest_book.current(g)[1]['title']}, {[(a['title'], a['state']) for a in quest_book.arcs(g) if a['state'] != 'done']})")
sev = next(f for f in ft["KANTO"] if f["id"] == "sevii")
check(len(feats._places(story, sev, "KANTO")) == len(sev["places"]) == 34, "Sevii Explorer: all 34 Sevii places are real places")
n = feats.value(story, sev, "KANTO")
check(n >= 10, f"Sevii Explorer counts the Sevii places walked ({n})")
uno = next(f for f in ft["KANTO"] if f["id"] == "unown")
for f_ in story.UNOWN_FORMS[:7]:
    story.catch_counts[f"201_{f_}"] = 1
check(feats.value(story, uno, "KANTO") >= 7 and feats.goal(story, uno, uno["tiers"][-1], "KANTO") == 28, "Tanoby Scholar counts Unown shapes, 28 in all")
paid = feats.pay(story)
check(any("Sevii Explorer" in l for l in paid) and any("Tanoby Scholar" in l for l in paid), f"both Sevii feats pay ({[l for l in paid if 'Feat' in l]})")
check(all(_items.describe(i) for f in ft["KANTO"] for t in f["tiers"] for i in (t[1].get("items") or {})), "every Kanto reward item is real")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
jn.set_tab("FEATS"); jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "sevii"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_sevii_feats.png"))
g.change_state(city)


print("UNOVA: the book's data (11-23: Aspertia to Route 4, the part walkable so far; each batch adds its chapters)")
ub = book["UNOVA"]
uids = [c["mission"] for a in ub for c in a["chapters"]]
check(all(i in jmissions for i in uids), "every Unova chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in ub for c in a["chapters"]), "every Unova chapter has a title and a page")
umain = [m for m in jmissions if m.startswith("b2_") and jmissions[m]["type"] == "MAIN"]
check(sorted(set(umain) - set(uids)) == [], f"every B2W2 story mission is in the book (missing: {sorted(set(umain) - set(uids))})")
said = " ".join(c["say"] for a in ub for c in a["chapters"]).lower()
check(not re.search(r"\b(because|so that|in order to)\b", said), "Unova's pages never spell out why")
uk = [k for k, a in prog.items() if str(a.get("region", "")).upper() == "UNOVA"]
uused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in uk]) + json.dumps([tmaps[k] for k in uk if k in tmaps])))
ugiven = [t[1]["tm"] for f in ft["UNOVA"] for t in f["tiers"] if t[1].get("tm")]
check(all(k in tms for k in ugiven) and len(ugiven) == len(set(ugiven)), "Unova Feat TMs: real, none twice")
check(not (set(ugiven) & uused), f"no Unova Feat TM is also on Unova's maps / people ({sorted(set(ugiven) & uused)})")
check(not (set(ugiven) & set(tutors.tutor_tms(g, "UNOVA"))), "no Unova Feat TM is a Unova tutor's")
check(all(_items.describe(i) for f in ft["UNOVA"] for t in f["tiers"] for i in (t[1].get("items") or {})), "every Unova reward item is real")

print("UNOVA: chapters follow the story, Aspertia to Colress on Route 4 (the order the Journal leads)")
story.starting_region = "UNOVA"
story.badges = {r: [] for r in story.badges}
story.badges["UNOVA"] = []
for m in jmissions.values():
    if m["id"].startswith(("b2_", "unova_")):
        for f in story.mission_flags(m):
            flags.pop(f, None)
for k in [k for k in flags if k.startswith(("visited_", "feat_", "badge_"))] + ["b2_send_off", "b2_castelia_arrived", "b2_mom_talk"]:
    flags.pop(k, None)
flags["unova_version"] = "BLACK_2"
at("ASPERTIA_CITY")
city = CityState(g); g.change_state(city)
UBADGE = {"b2_m7": "BASIC", "b2_m9": "TOXIC", "b2_m17": "INSECT"}
USCENE = {"b2_m1": ["b2_mom_talk"], "b2_m13": ["b2_castelia_arrived"], "b2_m33": ["b2_lentimas_juniper"]}   # (the scenes between: Mom's talk, the arrival; the send-off is b2_m1b's own, 11-23; Juniper at Lentimas, 11-24)
n_u = 0
for arc in ub:
    for ch in arc["chapters"]:
        m = jmissions[ch["mission"]]
        want(quest_book._words(story, arc["title"]), quest_book._words(story, ch["title"]), f"[{m['id']}]")
        if m["id"] == "b2_m10":
            jn_ = JournalState(g, city); g.change_state(jn_); jn_.draw()
            pygame.image.save(g.screen, os.path.join(S, "quest_book_unova_story.png"))
            g.change_state(city)
        for f in story.mission_flags(m):
            flags[f] = True
        if m["id"] in UBADGE:
            story.badges["UNOVA"].append(UBADGE[m["id"]])
        done_(USCENE.get(m["id"], []))
        if m.get("target"):
            at(m["target"])
        n_u += 1
check(n_u == len(uids) and all(a["state"] == "done" for a in quest_book.arcs(g)), "the whole Unova book so far is played through")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("STORY"); jn.draw()
check(not any(str(r.get("title", "")).startswith(("Team Plasma's Speech", "A Stranger Named N")) for r in jn.rows),
      "the menu-era BW story missions stay out of the book")
flags["visited_RELIC_CASTLE"] = True
jn.set_tab("SIDE"); jn.draw()
side = {r["mission"]["id"] for r in jn.rows if r.get("mission")}
check({"b2_s_r4_trade", "b2_s_join", "b2_s_royal"} <= side, f"SIDE: Route 4's swap, Join Avenue, the Royal Unova ({sorted(side)})")
check(not side & {"unova_s1", "unova_s6", "unova_s12", "unova_s13"}, "SIDE: menu-era errands for rebuilt places stay hidden (Relic Castle's, Cheren's and Roxie's)")
pygame.image.save(g.screen, os.path.join(S, "quest_book_unova_side.png"))
from src.world import medals as _medals
story.inventory["MEDAL_BOX"] = 1; flags["medal_box"] = True
before = feats.value(story, next(f for f in ft["UNOVA"] if f["id"] == "medals"), "UNOVA")
got = len(_medals.waiting(story)) if _medals.have_box(story) else 0
_medals.hand_out(story)
check(feats.value(story, next(f for f in ft["UNOVA"] if f["id"] == "medals"), "UNOVA") == before + got and got > 0,
      f"Medals from Mr. Medal count ({got})")
from src.states.pokestar import MovieState, SCRIPTS
mv = MovieState(g, city, SCRIPTS[0]); mv.picks = ["good"] * 3
mv._finish()
check(feats.value(story, next(f for f in ft["UNOVA"] if f["id"] == "films"), "UNOVA") == 1, "a Pokestar film shot counts")
feats.note(story, "phenomena", 5)
feats.pay(story)
for fid in ("films", "phenomena", "medals"):
    f_ = next(f for f in ft["UNOVA"] if f["id"] == fid)
    check(flags.get(feats.tier_flag("UNOVA", f_, 0)), f"Unova: {f_['name']} Bronze paid")
jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["UNOVA"]), "FEATS lists Unova's feats")
pygame.image.save(g.screen, os.path.join(S, "quest_book_unova_feats.png"))
g.change_state(city)

print("Other regions: no book yet, each story mission an arc of its own")
story.current_area_key = next(k for k, a in prog.items() if str(a.get("region", "")).upper() == "KALOS")
a = quest_book.arcs(g)
check(a and all(c.get("title") for x in a for c in x["chapters"]), f"Kalos's missions show as arcs ({len(a)})")
jn = JournalState(g, city); g.change_state(jn); jn.draw()
jn.set_tab("FEATS"); jn.draw()
check(jn.rows == [], "no Feats in a region without its list yet")

print(f"##### {fails} failures")
