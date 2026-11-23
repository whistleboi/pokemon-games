# The Orange Islands and Orre are full regions with a Pokedex of their own (main step M4, 11-23; Orange D1: "everything
# Orange gives", in National order): their REGION_START dex_list is what the Pokedex screen lists and what the dex count,
# catch missions and Feats use. The generation regions are unchanged.
#   bash dev/checks/run.sh region_dex
from src.states.systems import pokedex as _px

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


_saved = (dict(story.story_flags), story.starting_region, set(story.visited_region_set), story.current_area_key)


def reset(start, area):
    story.story_flags = {k: v for k, v in _saved[0].items() if not k.startswith(("received_starter_", "unlocked_national_dex"))}
    story.starting_region = start
    story.visited_region_set = set()
    story.current_area_key = area


def screen():
    st = _px.PokedexState.__new__(_px.PokedexState)
    st.game = g
    return st


for reg, area in (("ORANGE", "VALENCIA_ISLAND"), ("ORRE", "OUTSKIRT_STAND")):
    cfg = story.get_region_start(reg)
    want = list(cfg.get("dex_list") or [])
    print(f"{reg}:")
    check(bool(want), f"has a dex_list ({len(want)} species)")
    reset(reg, area)
    check(reg in _px.dex_regions(story), "starting there: it's one of your Pokedexes")
    st = screen()
    st.dex_view = reg
    got = st.normal_dex_ids({}, [])
    check(got == want, f"the Pokedex screen lists its dex_list ({len(got)} rows, first {got[:4]})")
    check(story.region_caught_count(reg) <= len(want), "the dex count reads the same list")
    check(not _px.has_national_dex(story), "one Pokedex alone: no National Dex yet")

print("from Kanto: Orange's Pokedex arrives with its starter, as any region's")
reset("KANTO", "PALLET_TOWN")
check("ORANGE" not in _px.dex_regions(story), "not before")
story.story_flags["received_starter_orange"] = True
check("ORANGE" in _px.dex_regions(story), "after Prof. Ivy's starter")
st = screen()
check("ORANGE" in st.dex_views() and "NATIONAL" in st.dex_views(), f"its view, and the National view ({st.dex_views()})")

print("the generation regions are unchanged")
reset("KANTO", "PALLET_TOWN")
st = screen(); st.dex_view = "KANTO"
check(st.normal_dex_ids({}, []) == list(range(1, 152)), "Kanto: #1-151")
check(_px.region_dex(story.get_region_start("KALOS")) == list(story.get_region_start("KALOS")["dex_list"]), "Kalos: its X/Y dex list")

print("a place with neither a list nor a range still gets the what-lives-here list")
_cfg = story.get_region_start("ORRE")
_keep = _cfg.pop("dex_list")
try:
    reset("KANTO", "PALLET_TOWN")
    check("ORRE" not in _px.dex_regions(story), "no Pokedex of its own")
    st = screen(); st.dex_view = "ORRE"
    check(st.normal_dex_ids({}, []) == _px.travel_dex(g, "ORRE"), "its view lists what lives there")
finally:
    _cfg["dex_list"] = _keep

story.story_flags, story.starting_region, story.visited_region_set, story.current_area_key = _saved[0], _saved[1], _saved[2], _saved[3]
print(f"##### {len(fails)} failures")
