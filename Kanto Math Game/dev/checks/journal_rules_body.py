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
moves = json.load(open("assets/moves.json", encoding="utf-8"))


def power(tm):
    x = tms.get(tm)
    name = str((x.get("move") if isinstance(x, dict) else x) or "").upper()
    m = moves.get(name.replace("-", "_")) or moves.get(name) or {}   # (moves.json keys some moves with "_", some with "-")
    return (m.get("power") or 0) * (3 if m.get("min_hits") else 1)

# MAIN missions left out of a book on purpose (with why); anything else missing fails.
LEFT_OUT = {
    "ORANGE": {"orange_m2", "orange_m3"},   # (the old all-badges / League missions: exact missions cover them, 11-23)
    "JOHTO": {"kanto_johto_travel"},   # (a Kanto Champion's way in, before Johto's own story starts at New Bark)
    "UNOVA": {f"unova_m{i}" for i in range(2, 23)},   # (menu-era BW-order missions: replaced with batch 12, J4)
}
# Open items already on the Journal plan (ROADMAP_JOURNAL): listed so the check stays green until they're done; a NEW
# one fails. Remove an entry when it is fixed.
KNOWN = set()   # (Unova's b2_m23 / b2_m29 "Hugh" fixed on region/unova 4392cd97, 11-24)
KNOWN_SIDE = {(r, i) for r, ids in {   # (SIDE lines sent to their regions 11-24; take each out when its region's fix is on main)
    "JOHTO": ["johto_c1", "johto_s_oddegg", "sinjoh_m1"],   # (done on region/johto b3c7c9b4)
    "HOENN": ["hoenn_s3", "hoenn_s4", "hoenn_s5", "hoenn_s7", "hoenn_s11", "hoenn_s14", "hoenn_s22", "hoenn_s25", "hoenn_s28"],
    "UNOVA": ["unova_s9", "unova_s12", "unova_s15", "unova_s16", "unova_s17", "unova_s19", "unova_s21"],
    "ORRE": ["orre_s1", "orre_s2", "orre_s2a"]}.items() for i in ids}
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
    # (J2, 11-24: the Journal's own voice - no orders shouted at the player, no "you need to", no manual-style openers)
    loud = [c["title"] for c in chs if "!" in str(c.get("say", "")) + str(c.get("title", ""))]
    check(not loud, f"{r}: no page or chapter title shouts with '!' ({loud})")
    need = [c["title"] for c in chs if re.search(r"\b(you need|you must|need to|make sure|don't forget)\b", str(c.get("say", "")), re.I)]
    check(not need, f"{r}: no page tells the player what they must do ({need})")
    order = [c["title"] for c in chs if re.match(r"(Defeat|Beat|Go to|Head to|Talk to|Visit|Travel to|Catch|Win|Return to|Bring|Challenge)\b",
                                                   str(c.get("say", "")))]
    check(not order, f"{r}: no page opens with an order ({order})")
    # (J2 11-24: the SIDE tab shows a SIDE mission's own words - no '!' and no order to open with)
    sides = [i for i, m in missions.items() if region_of(m) == r and str(m.get("type", "")).upper() != "MAIN"
             and not (m.get("region_species") or m.get("kanto_species"))]
    loud_side = sorted(i for i in sides if (r, i) not in KNOWN_SIDE and (
        "!" in str(missions[i].get("description") or missions[i].get("desc") or "")
        or re.match(r"(Defeat|Beat|Go to|Head to|Talk to|Visit|Travel to|Catch|Win|Return to|Bring|Challenge|Explore|Battle|Climb)\b",
                    str(missions[i].get("description") or missions[i].get("desc") or ""))))
    check(not loud_side, f"{r}: SIDE missions in the Journal's voice ({loud_side})")
    for k in sorted(x for x in KNOWN_SIDE if x[0] == r):
        print(f"   open  {k[1]}: SIDE line waits on {r.title()}'s card clean-{r.lower()}-journal-side-wording")
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
    weaker = []   # (J8, Jordan 11-24: each tier pays a move at least as strong as the tier before; multi-hit moves x3)
    for f in fl:
        pw = [power(t[1]["tm"]) for t in f["tiers"] if isinstance(t[1].get("tm"), str)]
        if any(b < a for a, b in zip(pw, pw[1:])):
            weaker.append(f["id"])
    check(not weaker, f"{r}: each Feat's TMs get stronger tier by tier ({weaker})")
    if r in OWN_FORMS:
        check("variants" in fid, f"{r}: has a '{r.title()} Variants' Feat (its own forms)")
    safari = sorted(k for k, a in prog.items() if isinstance(a, dict) and str(a.get("region", "KANTO")).upper() == r
                    and a.get("safari_game"))
    if safari:
        check(any(f.get("count") == "safari" for f in fl), f"{r}: has a Safari Feat (Safari Game at {safari})")

# (J7, 11-24: every SIDE mission can be found and finished - its target is a real place, and it ends: a done flag
#  something in the game sets (data or code), a badge, an Unown goal, or a "_not" condition that stops it showing)
print("Every SIDE mission can be found and finished")
import glob as _glob
_blob = json.dumps(g.loader.area_data) + open("assets/town_maps.json", encoding="utf-8").read() + "".join(
    open(_f, encoding="utf-8", errors="ignore").read() for _f in _glob.glob("src/**/*.py", recursive=True))
KNOWN_SIDE_END = {"johto_c1", "johto_s1",   # (card clean-johto-journal-unown-missions)
                  "hoenn_s5", "hoenn_s29"}  # (card clean-hoenn-journal-side-finish)
_bad_t, _bad_f = [], []
for i, m in missions.items():
    if str(m.get("type", "")).upper() == "MAIN" or region_of(m) not in regions or m.get("region_species") or m.get("kanto_species"):
        continue
    if i in KNOWN_SIDE_END:
        print(f"   open  {i}: can't finish yet (its region's card)")
        continue
    if m.get("target") and m["target"] not in prog:
        _bad_t.append(i)
    fl = m.get("completed_flag")
    fl = fl if isinstance(fl, list) else ([fl] if fl else [])
    unset = [x for x in fl if not (x.startswith(("visited_", "beat_", "received_", "feat_", "forms_complete_")) or x.endswith("_boss_defeated"))
             and _blob.count('"%s"' % x) + _blob.count("'%s'" % x) < 2]
    ends = fl or m.get("completed_badge") or m.get("unown_forms") or any(k.endswith("_not") or k == "item" for k in (m.get("condition") or {}))   # (an item asked for is used up: fossils)
    if unset or not ends:
        _bad_f.append(i)
check(not _bad_t, f"every SIDE mission's target is a real place ({_bad_t})")
check(not _bad_f, f"every SIDE mission can finish: its done flag is set somewhere, or it stops showing ({_bad_f})")

print(f"##### {fails} failures")
