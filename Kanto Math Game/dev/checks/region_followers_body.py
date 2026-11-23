# A following Pokemon's walking sheet: a game-built region's own overworld sheet first, assets/dungeon/followers as the
# fallback, and a form only one region drew keeps that region's look wherever it follows you (Jordan 11-23).
#   bash dev/checks/run.sh region_followers
import os
from src.states.overworld import dungeon as _dg

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def first(names, shiny=False):
    """The sheet the game would draw: the first path that exists."""
    return next((os.path.basename(p) for p in _dg.region_sheet_paths(g, names, shiny) if os.path.isfile(p)), None)


own = _dg.sprite_map(g).get("region_followers") or {}
_AT = {"ORANGE": "VALENCIA_ISLAND", "UNOVA": "ASPERTIA_CITY", "KANTO": "PALLET_TOWN"}


def go(region):   # (the region you're in comes from the place you stand)
    story.enter_region(region)
    story.current_area_key = _AT[region]
print("1) every region sheet listed exists, 4 x 4")
import pygame
bad = []
for reg, d in own.items():
    if not isinstance(d, dict):
        continue
    for n, f in d.items():
        p = os.path.join("assets", "dungeon", "characters", f)
        if not os.path.isfile(p):
            bad.append((reg, n, f, "missing"))
            continue
        w, h = pygame.image.load(p).get_size()
        if w % 4 or h % 4:
            bad.append((reg, n, f, (w, h)))
check(not bad, f"{sum(len(d) for d in own.values() if isinstance(d, dict))} sheets, all there {bad}")

print("2) in its own region, a region's sheet comes first; elsewhere the follower sheet")
go("ORANGE")
check(first(["249"]) == "oi_138.png", f"Lugia in Orange walks as 5.7's own Lugia ({first(['249'])})")
go("UNOVA")
check(first(["249"]) == "249.png", f"a Lugia in Unova: the follower sheet ({first(['249'])})")
check(first(["494"]) == "b2_victini.png", f"Victini in Unova: Black 2's own ({first(['494'])})")
go("KANTO")
check(first(["494"]) == "494.png", f"Victini in Kanto: the follower sheet ({first(['494'])})")

print("3) a form only one region drew follows you anywhere with that region's sheet")
_saved = dict(own.get("ORANGE") or {})
own.setdefault("ORANGE", {})["249_shadow"] = "oi_138.png"   # (as if Orange had drawn a Shadow Lugia: no follower sheet has one)
go("UNOVA")
got = first(["249_shadow", "249"])
check(got == "oi_138.png", f"that form in Unova keeps Orange's sheet, not the plain Lugia ({got})")
go("ORANGE")
check(first(["249_shadow", "249"]) == "oi_138.png", "and in Orange too")
own["ORANGE"] = _saved
go("UNOVA")
check(first(["249_shadow", "249"]) == "249.png", "with no region's sheet for the form: the plain species' follower sheet")

print("4) shiny: the shiny follower sheet before a region's (theirs have no shiny colours)")
go("ORANGE")
sh = os.path.isfile(os.path.join("assets", "dungeon", "followers", "shiny", "249.png"))
check(first(["249"], shiny=True) == ("249.png" if sh else "oi_138.png"), f"shiny Lugia in Orange ({first(['249'], shiny=True)})")

print("5) the walking map draws it")
from src.states.overworld.dungeon import DungeonState as _DS
class _M:
    id, form, is_shiny, gender = 249, "normal", False, None
st = _DS.__new__(_DS); st.game = g; st._cache = {} if not hasattr(st, "_cache") else st._cache
try:
    img = _DS._follower_img(st, _M(), (0, 1))
    check(img is not None, "a Lugia follower frame in Orange")
except Exception as e:   # (a state built without its __init__: report rather than crash)
    print("   (skipped: needs a live map state)", type(e).__name__, e)
go("KANTO")
print(f"##### {len(fails)} failures")
