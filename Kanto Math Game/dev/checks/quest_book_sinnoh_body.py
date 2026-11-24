# The Quest Book: Sinnoh's book, Twinleaf to the Champion, its Feats (split from quest_book 11-23).
#   bash dev/checks/run.sh quest_book_sinnoh
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())

print("SINNOH: the book's data")
sb = book["SINNOH"]
sids = [c["mission"] for a in sb for c in a["chapters"]]
check(all(i in jmissions for i in sids), "every Sinnoh chapter's mission exists")
check(all(c.get("title") and c.get("say") for a in sb for c in a["chapters"]), "every Sinnoh chapter has a title and a page")
smain = [m for m in jmissions if m.startswith("sinnoh_") and jmissions[m]["type"] == "MAIN"]
check(sorted(set(smain) - set(sids)) == [], f"every Sinnoh story mission is in the book (missing: {sorted(set(smain) - set(sids))})")
said = " ".join(c["say"] for a in sb for c in a["chapters"]).lower()
check(not re.search(r"\b(because|so that|in order to)\b", said), "Sinnoh's pages never spell out why")
sk = [k for k, a in prog.items() if str(a.get("region", "")).upper() == "SINNOH"]
sused = set(re.findall(r"TM\d{3}", json.dumps([prog[k] for k in sk]) + json.dumps([tmaps[k] for k in sk if k in tmaps])))
sgiven = [t[1]["tm"] for f in ft["SINNOH"] for t in f["tiers"] if t[1].get("tm")]
check(all(k in tms for k in sgiven) and len(sgiven) == len(set(sgiven)), "Sinnoh Feat TMs: real, none twice")
check(not (set(sgiven) & sused), f"no Sinnoh Feat TM is also on Sinnoh's maps / people ({sorted(set(sgiven) & sused)})")
check(not (set(sgiven) & set(tutors.tutor_tms(g, "SINNOH"))), "no Sinnoh Feat TM is a Sinnoh tutor's")
check(all(_items.describe(i) for f in ft["SINNOH"] for t in f["tiers"] for i in (t[1].get("items") or {})), "every Sinnoh reward item is real")
var = next(f for f in ft["SINNOH"] if f["id"] == "variants")
hforms = feats._form_ids(story, var)
spools = json.load(open("assets/sinnoh_area_data.json", encoding="utf-8"))
caught_at = {int(p) for k, v in spools.items() if k.endswith("PERCENTAGES") and isinstance(v, dict) for p in v if str(p).isdigit()}
check(len(hforms) == 16 and hforms <= caught_at, f"Hisuian Variants: all 16 forms, each wild somewhere in Sinnoh / Hisui ({sorted(hforms - caught_at)})")

print("SINNOH: chapters follow the story, Twinleaf to the Champion (the order the Journal leads)")
story.starting_region = "SINNOH"
story.badges = {r: [] for r in story.badges}
story.badges["SINNOH"] = []
for m in jmissions.values():
    if m["id"].startswith("sinnoh_"):
        for f in story.mission_flags(m):
            flags.pop(f, None)
for k in [k for k in flags if k.startswith(("visited_", "feat_", "badge_"))] + ["received_starter_sinnoh", "defeated_rival_sinnoh_starter", "met_roark"]:
    flags.pop(k, None)
at("TWINLEAF_TOWN")
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (11-24: the Journal opened from the walked town's map)
city = walk_town(story.current_area_key, None, play=False)
SBADGE = {"sinnoh_m2b": "COAL", "sinnoh_m4b": "FOREST", "sinnoh_m5c": "COBBLE", "sinnoh_m6c": "FEN", "sinnoh_m8": "RELIC",
          "sinnoh_m9b": "MINE", "sinnoh_m12b": "ICICLE", "sinnoh_m14b": "BEACON"}
SSCENE = {"sinnoh_m1": ["received_starter_sinnoh"], "sinnoh_m1b": ["defeated_rival_sinnoh_starter"], "sinnoh_m2": ["met_roark"]}
n_s = 0
for arc in sb:
    for ch in arc["chapters"]:
        m = jmissions[ch["mission"]]
        want(quest_book._words(story, arc["title"]), quest_book._words(story, ch["title"]), f"[{m['id']}]")
        if m["id"] == "sinnoh_m10b":
            jn_ = JournalState(g, city); g.change_state(jn_); jn_.draw()
            pygame.image.save(g.screen, os.path.join(S, "quest_book_sinnoh_story.png"))
            g.change_state(city)
        if ch.get("steps") is not None:   # (a chapter over some of a mission's way-points: the Elder's Surf, 11-24)
            for i in ch["steps"]:
                done_(m["steps"][i]["done"])
            n_s += 1
            continue
        for f in story.mission_flags(m):
            flags[f] = True
        if m["id"] in SBADGE:
            story.badges["SINNOH"].append(SBADGE[m["id"]])
        done_(SSCENE.get(m["id"], []))
        if m.get("target"):
            at(m["target"])
        n_s += 1
check(n_s == len(sids) and all(a["state"] == "done" for a in quest_book.arcs(g)), "the whole Sinnoh book is played through")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
check(not any(r["mission"]["id"].startswith("sinnoh_dex") for r in jn.rows), "Sinnoh's old Catch missions are its Pokedex Feat now")
check(any(r["mission"]["id"] == "sinnoh_s_trades" for r in jn.rows), "SIDE: Sinnoh's trades")
from src.states.poffin import PoffinHouseState, PoffinCookState
house = PoffinHouseState(g, city)
ck = PoffinCookState(g, house)   # (a Poffin cooked at the Poffin House, as a player would)
ck.berries, ck.good, ck.quick, ck.mistakes = ["CHERI_BERRY", "PECHA_BERRY"], 4, 3, 0
ck.finish()
check(feats.value(story, next(f for f in ft["SINNOH"] if f["id"] == "poffins"), "SINNOH") == 1, "a Poffin cooked counts")
from src.world import berries as _berries   # (Platinum's Berry patches on the walked routes: soft soil, berry_soil; Sinnoh 75fca7d8)
bk = "FUEGO_IRONWORKS"
_soil = [p for f in (tmaps[bk].get("floors") or [tmaps[bk]]) for p in (f.get("berry_soil") or [])]
check(len(_soil) >= 4, f"Fuego Ironworks has its Berry patches on the walked map ({len(_soil)})")
at(bk); flags["has_berry_pouch"] = True
for _x, _y, _b in _soil[:4]:
    _berries.touch(story, bk, (int(_x), int(_y)), _b)   # (walk up to a ripe patch: pick it)
bp = feats.value(story, next(f for f in ft["SINNOH"] if f["id"] == "berry_picks"), "SINNOH")
check(bp >= 4, f"Berries picked from the walked patches count ({bp} from 4 patches at {bk})")
g.change_state(city)
feats.note(story, "smash", 3)
feats.pay(story)   # (the route screen pays too, on the way)
for fid in ("poffins", "smash", "berry_picks"):
    f_ = next(f for f in ft["SINNOH"] if f["id"] == fid)
    check(flags.get(feats.tier_flag("SINNOH", f_, 0)), f"Sinnoh: {f_['name']} Bronze paid")
jn.set_tab("FEATS"); jn.draw()
check(len(jn.rows) == len(ft["SINNOH"]), "FEATS lists Sinnoh's feats")
jn.selected = next(i for i, r in enumerate(jn.rows) if r["feat"]["id"] == "variants"); jn.draw()
pygame.image.save(g.screen, os.path.join(S, "quest_book_sinnoh_feats.png"))
g.change_state(city)


print(f"##### {fails} failures")
