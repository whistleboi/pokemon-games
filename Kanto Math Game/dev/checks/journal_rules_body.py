# The Journal's rules, every region's Quest Book (Journal branch, J1, 11-24; kanto_handoff/ROADMAP_JOURNAL.md).
#   bash dev/checks/run.sh journal_rules
# Jordan's rules (11-14, 11-22, 11-23): every MAIN mission is a chapter; every chapter has a title and a page; pages are
# suspenseful and never say why; rivals by {rival_name}; Feats tiered, a Variants Feat where a region has its own forms,
# a Safari Feat where it has a Safari Game; a region on the walked marker (guide.WALKED_REGIONS) has a book.
# Data only: no playing (each region's quest_book_<region> suite walks its chapters).
import json, re
from src.world import quest_book, feats, guide
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


book = quest_book.table(g)
ft = feats.table(g)
prog = g.loader.area_data["STORY_PROGRESSION"]
missions = {m["id"]: m for m in g.loader.area_data["JOURNAL_MISSIONS"]}
tms = json.load(open("assets/tms.json", encoding="utf-8"))
regions = [r for r in book if not r.startswith("_")]

# MAIN missions left out of a book on purpose (with why); anything else missing fails.
LEFT_OUT = {
    "ORANGE": {"orange_m2", "orange_m3"},   # (the old all-badges / League missions: exact missions cover them, 11-23)
    "JOHTO": {"kanto_johto_travel"},   # (a Kanto Champion's way in, before Johto's own story starts at New Bark)
    "UNOVA": {f"unova_m{i}" for i in range(2, 23)},   # (menu-era BW-order missions: replaced with batch 12, J4)
}
# Open items already on the Journal plan (ROADMAP_JOURNAL): listed so the check stays green until they're done; a NEW
# one fails. Remove an entry when it is fixed.
KNOWN = set()   # (Unova's b2_m23 / b2_m29 "Hugh" fixed on region/unova 4392cd97, 11-24)
NOT_YET = set()   # (walked regions with no book yet; Orre's came 11-24, J5)
OWN_FORMS = {"ORANGE", "SINNOH", "ALOLA", "GALAR", "PALDEA", "HISUI"}
RIVALS = {"KANTO": ["Blue", "Gary"], "JOHTO": ["Silver"], "HOENN": ["Brendan", "May"], "SINNOH": ["Barry"],
          "UNOVA": ["Hugh"]}


def region_of(m):
    return str(m.get("region") or (m.get("condition") or {}).get("required_region") or "").upper()


print("Every walked region has a book")
check(not (guide.WALKED_REGIONS - set(regions)), f"every region on the walked marker has a book ({sorted(guide.WALKED_REGIONS - set(regions))})")
for r in sorted(NOT_YET):
    print(f"   open  {r}: no Quest Book yet (ROADMAP_JOURNAL J5)")

for r in regions:
    print(f"{r}: the story")
    arcs = book[r]
    chs = [c for a in arcs for c in a.get("chapters") or []]
    ids = [c.get("mission") for c in chs]
    check(all(a.get("title") for a in arcs), f"{r}: every arc has a title")
    check(all(i in missions for i in ids), f"{r}: every chapter's mission exists ({sorted({i for i in ids if i not in missions})})")
    check(all(c.get("title") and c.get("say") for c in chs), f"{r}: every chapter has a title and a page")
    main = {i for i, m in missions.items() if region_of(m) == r and str(m.get("type", "")).upper() == "MAIN"}
    miss = sorted(main - set(ids) - LEFT_OUT.get(r, set()))
    check(not miss, f"{r}: every MAIN mission is a chapter (missing: {miss})")
    stale = sorted(LEFT_OUT.get(r, set()) - main)
    check(not stale, f"{r}: the left-out list names only real MAIN missions ({stale})")
    why = [c["title"] for c in chs if re.search(r"\b(because|so that|in order to)\b", str(c.get("say", "")), re.I)]
    check(not why, f"{r}: no page spells out why ({why})")
    names = RIVALS.get(r, [])
    if names:
        pat = re.compile(r"(?<!Mt\. )\b(" + "|".join(names) + r")\b(?! (League|Wing|Cave|Trophy))")   # (not Mt. Silver)
        bad = [c["title"] for c in chs if pat.search(str(c.get("title", "")) + " " + str(c.get("say", "")))]
        check(not bad, f"{r}: the rival is {{rival_name}} on every page ({bad})")
        mbad = sorted(i for i in main if pat.search(str(missions[i].get("title", "")) + " " + str(missions[i].get("description", "")))
                      and (r, i) not in KNOWN)
        check(not mbad, f"{r}: the rival is {{rival_name}} in every MAIN mission's words ({mbad})")
        for k in sorted(x for x in KNOWN if x[0] == r):
            print(f"   open  {k[1]}: rival named in its words (ROADMAP_JOURNAL J2)")

    print(f"{r}: the Feats")
    fl = ft.get(r) or []
    check(bool(fl), f"{r}: has Feats")
    fid = [f.get("id") for f in fl]
    check(len(fid) == len(set(fid)), f"{r}: Feat ids are unique")
    short = [f["id"] for f in fl if len(f.get("tiers") or []) < 3]
    check(not short, f"{r}: every Feat has at least three tiers ({short})")
    flat = [f["id"] for f in fl if any(not isinstance(t[0], str) and not isinstance(p[0], str) and t[0] <= p[0]
                                        for p, t in zip(f["tiers"], f["tiers"][1:]))]
    check(not flat, f"{r}: every Feat's goals rise tier by tier ({flat})")
    empty = [f["id"] for f in fl if any(not (t[1].get("tm") or t[1].get("items") or t[1].get("money")) for t in f["tiers"])]
    check(not empty, f"{r}: every tier pays something ({empty})")
    given = [t[1]["tm"] for f in fl for t in f["tiers"] if t[1].get("tm")]
    given = [x for t in given for x in (t if isinstance(t, list) else [t])]
    check(all(k in tms for k in given) and len(given) == len(set(given)), f"{r}: Feat TMs are real and none is given twice")
    if r in OWN_FORMS:
        check("variants" in fid, f"{r}: has a '{r.title()} Variants' Feat (its own forms)")
    safari = sorted(k for k, a in prog.items() if isinstance(a, dict) and str(a.get("region", "KANTO")).upper() == r
                    and a.get("safari_game"))
    if safari:
        check(any(f.get("count") == "safari" for f in fl), f"{r}: has a Safari Feat (Safari Game at {safari})")

print(f"##### {fails} failures")
