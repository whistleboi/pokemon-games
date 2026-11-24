# The Quest Book: Johto's book, chapters New Bark to Mt. Silver, its Feats (split from quest_book 11-23).
#   bash dev/checks/run.sh quest_book_johto
exec(open("dev/checks/quest_book_lib.py", encoding="utf-8").read())

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
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (11-24: the Journal opened from the walked town's map)
city = walk_town(story.current_area_key, None, play=False)


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
want("The Hive Badge", "Something Warm", "the Zephyr Badge: Elm's aide's Egg first (HGSS + Crystal stop you on Route 32 without it; 11-23)")
flags["got_togepi_egg"] = True
want("The Hive Badge", "Under the Ground", "the Egg in hand")
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
check(not any(r["mission"]["id"] == "johto_s_togepi" for r in jn.rows), "SIDE: the Egg is a story step now, not a side mission")
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
want("The Storm Badge", "The Dark Tower", "Surf: up the Lighthouse to Jasmine first (HGSS + Crystal; 11-23)")
flags["jasmine_explained"] = True
want("The Storm Badge", "Across the Whirling Sea", "Jasmine has explained")
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


print(f"##### {fails} failures")
