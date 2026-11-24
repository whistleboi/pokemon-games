# The Quest Book: Orange's book, Valencia to the Ice Sphere, its Feats (split from quest_book 11-23).
#   bash dev/checks/run.sh quest_book_orange
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())

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
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (11-24: the Journal opened from the walked town's map)
city = walk_town(story.current_area_key, None, play=False)


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
check(9136 in ids and 9136 in pools, "Pinkan Scyther lives on Pinkan Island and counts (Jordan, 11-23)")
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


print(f"##### {fails} failures")
