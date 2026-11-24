# The reach checks count a walked map's ride people as links (Unova's cleanup, 11-23): Pop Roxie's ship between Virbank
# and Castelia, the Liberty Garden sailor, Mt. Silver's guide (only with what she asks for) - each when they're shown.
#   bash dev/checks/run.sh reach_rides
exec(open("dev/checks/reach_lib.py", encoding="utf-8").read())
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


_saved = dict(story.story_flags)
for f in ("b2_pop_roxie_back", "b2_sailed_castelia", "b2_castelia_arrived"):
    story.story_flags.pop(f, None)
check("CASTELIA_CITY" not in _rides("VIRBANK_CITY", _state("VIRBANK_CITY")), "Virbank before Pop Roxie is back: no ship")
story.story_flags["b2_pop_roxie_back"] = True
check("CASTELIA_CITY" in _rides("VIRBANK_CITY", _state("VIRBANK_CITY")), "Virbank once she's back: the ship to Castelia")
story.story_flags["b2_castelia_arrived"] = True
_c = _rides("CASTELIA_CITY", _state("CASTELIA_CITY"))
check({"VIRBANK_CITY", "LIBERTY_GARDEN"} <= set(_c), f"Castelia: the ship back to Virbank and the boat to Liberty Garden ({_c})")
check("CASTELIA_CITY" in _rides("LIBERTY_GARDEN", _state("LIBERTY_GARDEN")), "Liberty Garden: the boat back")
check("CASTELIA_CITY" in links("VIRBANK_CITY"), "and links() counts them")
_jb = list(story.badges.get("JOHTO", []))
story.badges["JOHTO"] = []
check("SILVER_LEAGUE_PLATEAU" not in _rides("MT_SILVER_CITY", _state("MT_SILVER_CITY")), "Mt. Silver's guide: not without the eight Johto badges")
story.badges["JOHTO"] = _jb
story.story_flags = _saved
print(f"##### {fails} failures")
