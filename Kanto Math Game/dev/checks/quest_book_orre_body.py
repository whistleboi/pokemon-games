# The Quest Book: Orre's book, the Outskirt Stand to the Orre League, its Feats (Journal branch J5, 11-24).
#   bash dev/checks/run.sh quest_book_orre
# Orre's story: kanto_handoff/orre_check/STORY_REWORK.md (Part 1 Colosseum, the five-year skip, Part 2 XD, the League).
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())

print("ORRE: the book's data")
ob = book["ORRE"]
oids = [c["mission"] for a in ob for c in a["chapters"]]
check(all(i in jmissions for i in oids), "every Orre chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in ob for c in a["chapters"]), "every Orre chapter has a title and a page")
omain = [m for m in jmissions if m.startswith("orre_") and jmissions[m]["type"] == "MAIN"]
check(sorted(set(omain) - set(oids)) == [], f"every Orre story mission is in the book (missing: {sorted(set(omain) - set(oids))})")
ok_ = [k for k, a in prog.items() if str(a.get("region", "")).upper() == "ORRE"]
oused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in ok_]) + json.dumps([tmaps[k] for k in ok_ if k in tmaps])
                       + open("assets/orre_battle_cds.json", encoding="utf-8").read()))
ogiven = [t[1]["tm"] for f in ft["ORRE"] for t in f["tiers"] if t[1].get("tm")]
check(all(k in tms for k in ogiven) and len(ogiven) == len(set(ogiven)), "Orre Feat TMs: real, none twice")
check(not (set(ogiven) & oused), f"no Orre Feat TM is also on Orre's maps / people / Battle CDs ({sorted(set(ogiven) & oused)})")
check(not (set(ogiven) & set(tutors.tutor_tms(g, "ORRE"))), "no Orre Feat TM is an Orre tutor's")
check(all(_items.describe(i) for f in ft["ORRE"] for t in f["tiers"] for i in (t[1].get("items") or {})), "every Orre reward item is real")
dexn = len(feats._dex_ids(story, "ORRE"))
dexf = next(f for f in ft["ORRE"] if f["id"] == "dex")
check(all(t[0] == "all" or t[0] < dexn for t in dexf["tiers"]), f"Orre Pokedex tiers fit its dex ({dexn})")
pool = feats._shadow_pool(story, "ORRE")
lines = feats._shadow_lines(story, "ORRE")
check(len(pool) > 80 and len(lines) > 50, f"Snag Master / Open Hearts count Orre's Shadow Pokemon ({len(pool)} to snag, {len(lines)} kinds)")
check(len(feats._battle_cds(story)) == 50, "Battle Disc Solver counts XD's 50 Battle CDs")

print("ORRE: chapters follow the story, the Outskirt Stand to the League (the order the Journal leads)")
story.starting_region = "ORRE"
story.badges = {r: [] for r in story.badges}
story.badges["ORRE"] = []
for m in jmissions.values():
    if m["id"].startswith("orre_"):
        for f in story.mission_flags(m):
            flags.pop(f, None)
for k in [k for k in flags if k.startswith(("visited_", "feat_", "badge_", "orre_", "xd_", "col_"))]:
    flags.pop(k, None)
at("OUTSKIRT_STAND")
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (11-24: the Journal opened from the walked town's map)
city = walk_town(story.current_area_key, None, play=False)
OBADGE = {"orre_m14": "PHENAC", "orre_m4c": "PYRITE", "orre_m6c": "AGATE", "orre_m10y": "SNAGEM", "orre_m10d": "GATEON",
          "orre_m17d": "KEY_LAIR", "orre_m19": "CITADARK", "orre_m20": "REALGAM"}
OSCENE = {"orre_m10c2": ["xd_gateon_bridges"],   # (Makan fixes Gateon's bridges on his way home: Jasmine opens)
          "orre_m10": ["orre_data_rom"],        # (Ein drops his Data ROM)
          "orre_m18c": ["orre_part2"],          # (Evice beaten: "five years later")
          }   # (Makan fixing Gateon's bridges is the first "A Machine Part" chapter's own "done")
n_o = 0
for arc in ob:
    for ch in arc["chapters"]:
        m = jmissions[ch["mission"]]
        want(arc["title"], ch["title"], f"[{m['id']}]")
        if ch["title"] == "Dust and Diesel":
            jn_ = JournalState(g, city); g.change_state(jn_); jn_.draw()
            pygame.image.save(g.screen, os.path.join(S, "quest_book_orre_story.png"))
            g.change_state(city)
        if ch.get("done"):   # (a chapter over part of a mission: the Machine Part up to the bridges, Citadark up to Eldes)
            done_(ch["done"])
        else:
            for f in story.mission_flags(m):
                flags[f] = True
            if m["id"] in OBADGE:
                story.badges["ORRE"].append(OBADGE[m["id"]])
            done_(OSCENE.get(m["id"], []))
        if m.get("target"):
            at(m["target"])
        n_o += 1
check(n_o == len(oids) and all(a["state"] == "done" for a in quest_book.arcs(g)), "the whole Orre book is played through")

print("ORRE: SIDE and FEATS")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
side = {r["mission"]["id"] for r in jn.rows}
check("orre_s9" in side, f"SIDE after the title: Team Rocket in Orre ({sorted(side)})")
flags[next(iter(pool))] = True
for b in list(lines)[:5]:
    flags[f"purified_line_{b}"] = True
for k in feats._battle_cds(story)[:5]:
    flags[f"battle_cd_{k}_cleared"] = True
check(feats.value(story, next(f for f in ft["ORRE"] if f["id"] == "purified"), "ORRE") == 5, "Open Hearts counts purified kinds")
for i in list(pool)[:10]:
    flags[i] = True
paid = feats.pay(story)
for name in ("Snag Master", "Open Hearts", "Battle Disc Solver"):
    check(any(name in l for l in paid), f"Orre: {name} Bronze paid ({[l for l in paid if name in l][:1]})")
jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["ORRE"]), "FEATS lists Orre's feats")
pygame.image.save(g.screen, os.path.join(S, "quest_book_orre_feats.png"))
g.change_state(city)

print(f"##### {fails} failures")
