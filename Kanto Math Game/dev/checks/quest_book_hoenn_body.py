# The Quest Book: Hoenn's book, Littleroot to the Other Orb, its Feats (split from quest_book 11-23).
#   bash dev/checks/run.sh quest_book_hoenn
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())

print("HOENN: the book's data")
hb = book["HOENN"]
hids = [c["mission"] for a in hb for c in a["chapters"]]
check(all(i in jmissions for i in hids), "every Hoenn chapter's mission exists")
hmain = [m for m in jmissions if m.startswith("hoenn_") and jmissions[m]["type"] == "MAIN"]
check(sorted(set(hmain) - set(hids)) == [], f"every Hoenn story mission is in the book (missing: {sorted(set(hmain) - set(hids))})")
hk = [k for k, a in prog.items() if str(a.get("region", "")).upper() == "HOENN"]
hused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in hk]) + json.dumps([tmaps[k] for k in hk if k in tmaps])))
hgiven = [t[1]["tm"] for f in ft["HOENN"] for t in f["tiers"] if t[1].get("tm")]
check(all(k in tms for k in hgiven) and len(hgiven) == len(set(hgiven)), "Hoenn Feat TMs: real, none twice")
check(not (set(hgiven) & hused), f"no Hoenn Feat TM is also on Hoenn's maps / people ({sorted(set(hgiven) & hused)})")
check(not (set(hgiven) & set(tutors.tutor_tms(g, "HOENN"))), "no Hoenn Feat TM is a Hoenn tutor's")
check(all(_items.describe(i) for f in ft["HOENN"] for t in f["tiers"] for i in (t[1].get("items") or {})), "every Hoenn reward item is real")

print("HOENN: chapters follow the story, Littleroot to the Other Orb (the order the Journal leads, 11-23)")
from src.world import hoenn as _hoenn
story.starting_region = "HOENN"
story.badges = {r: [] for r in story.badges}
story.badges["HOENN"] = []
for m in jmissions.values():
    if m["id"].startswith("hoenn_"):
        for f in story.mission_flags(m):
            flags.pop(f, None)
for k in [k for k in flags if k.startswith(("visited_", "feat_", "badge_"))] + ["received_pokedex_hoenn", "heard_devon_parts_stolen"]:
    flags.pop(k, None)
at("LITTLEROOT_TOWN")
flags["hoenn_version"] = "OMEGA_RUBY"   # (picked on arrival: Team Magma, Maxie, Groudon)
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (11-24: the Journal opened from the walked town's map)
city = walk_town(story.current_area_key, None, play=False)
HBADGE = {"hoenn_m3": "STONE", "hoenn_m5": "KNUCKLE", "hoenn_m7": "DYNAMO", "hoenn_m9": "HEAT", "hoenn_m10": "BALANCE",
          "hoenn_m13": "FEATHER", "hoenn_m17": "MIND", "hoenn_m21": "RAIN"}
HSCENE = {"hoenn_m3": ["heard_devon_parts_stolen"], "hoenn_m5": ["visited_SLATEPORT_CITY"]}   # (Rustboro's thief, the boat to Slateport)
n_h = 0
for arc in hb:
    for ch in arc["chapters"]:
        m = jmissions[ch["mission"]]
        want(quest_book._words(story, arc["title"]), quest_book._words(story, ch["title"]), f"[{m['id']}]")
        if m["id"] == "hoenn_m8":
            check("Maxie is waiting" in quest_book.current(g)[1]["say"], f"Omega Ruby's words filled in ({quest_book.current(g)[1]['say'][:70]})")
            jn_ = JournalState(g, city); g.change_state(jn_); jn_.draw()
            pygame.image.save(g.screen, os.path.join(S, "quest_book_hoenn_story.png"))
            g.change_state(city)
        for f in story.mission_flags(m):
            flags[f] = True
        for st_ in m.get("steps") or []:
            if isinstance(st_.get("done"), str):
                done_(st_["done"])
        if m["id"] in HBADGE:
            story.badges["HOENN"].append(HBADGE[m["id"]])
        done_(HSCENE.get(m["id"], []))
        if m.get("target"):
            at(m["target"])
        n_h += 1
check(n_h == len(hids) and all(a["state"] == "done" for a in quest_book.arcs(g)), "the whole Hoenn book is played through")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
check(not any(r["mission"]["id"].startswith("hoenn_dex") for r in jn.rows), "Hoenn's old Catch missions are its Pokedex Feat now")
check(any(r["mission"]["id"] == "hoenn_s_trades" for r in jn.rows), "SIDE: Hoenn's trades")
flags["hoenn_catch_30"] = True
before = story.money
for kind, n in (("contests", 1), ("contest_wins", 1), ("berries", 5), ("smash", 3), ("safari", 5)):
    feats.note(story, kind, n)
paid = feats.pay(story)
for name in ("Contest Star", "Ribbon Winner", "Berry Farmer", "Rock Breaker", "Safari Explorer"):
    check(any(name in l for l in paid), f"Hoenn: {name} Bronze paid")
check(not any("Pokedex" in l for l in paid), "a Hoenn catch milestone paid before isn't paid again")
jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["HOENN"]), "FEATS lists Hoenn's feats")
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "contests"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_hoenn_feats.png"))
g.change_state(city)


print(f"##### {fails} failures")
