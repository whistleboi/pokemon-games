# Live 3D (SoulSilver's scenes): a person standing in front of furniture is drawn over it, not behind it (Johto's J4 look
# review, 11-23: Violet Center 2F's counter covered the player's upper half). The figure keeps its look on screen but is
# depth-tested at its feet; something truly in front of it still covers it.
#   bash dev/checks/run.sh live3d_depth
import pygame
from src.states.overworld import CityState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def settle(n=40):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.enter_region("JOHTO")
story.current_area_key = "VIOLET_CITY"; story.story_flags["visited_VIOLET_CITY"] = True
g.walk_town_pos = None; g.walk_town_room = ("VIOLET_CITY", "center_2")
g.change_state(CityState(g)); settle()
t = g.current_state
if getattr(t, "room", None) != "center_2" and hasattr(t, "_go"):
    t._go("center_2", None); settle()
t = g.current_state
lv = t._live() if hasattr(t, "_live") else None
check(getattr(t, "room", None) == "center_2" and bool(lv), "Violet Center 2F, live")


def shown(spot):
    """How much of a solid test figure stood at spot is drawn at full strength, against the same figure drawn alone."""
    sc = lv[0]
    t.player = t.anim_from = spot
    cam = t._live_cam()
    size = (640, 360)
    fig = pygame.Surface((32, 48), pygame.SRCALPHA)   # (a person's frame: the body in its middle, see-through at the sides)
    fig.fill((255, 0, 255, 255), pygame.Rect(9, 2, 14, 46))
    x, y = spot
    sp = [(fig, (x + 0.5, t._live_height(x, y), sc.wz(x, y) + 0.55), 48 / 32 * 1.5)]

    def count(img):
        n = 0
        for py in range(0, size[1], 2):
            for px in range(0, size[0], 2):
                r, g_, b = img.get_at((px, py))[:3]
                n += r > 235 and g_ < 30 and b > 235
        return n
    full = count(sc.render(size, cam, sp))
    keep = sc.parts
    sc.parts = []
    try:
        alone = count(sc.render(size, cam, sp))
    finally:
        sc.parts = keep
    return full, alone


if lv:
    spot = (8, 7)
    check(t._open(spot), f"{spot} is open (SoulSilver's own collision too)")
    full, alone = shown(spot)
    check(alone > 0 and full >= 0.9 * alone, f"standing in front of the counter: drawn whole ({full} of {alone})")
    behind = (8, 5)   # (two rows up: behind the counter, where the nurse stands - the counter in front still covers part)
    fb, ab = shown(behind)
    check(ab > 0 and fb < 0.97 * ab, f"standing behind the counter: the counter still covers part, as before ({fb} of {ab}; the old drawing 231 of 250)")
    far = next(((x, yy) for yy in range(t.h - 1, 0, -1) for x in range(t.w) if t._open((x, yy))), None)
    if far:
        f2, a2 = shown(far)
        check(a2 > 0 and f2 >= 0.9 * a2, f"on open floor {far}: drawn whole ({f2} of {a2})")
if lv:   # (11-23: people one height in the 3D world too - Johto saw them 1.5x too tall once they were 72 px on the map)
    from src.states.overworld import dungeon as _dn
    from src.states.overworld.walk_town import LIVE_SPRITE as _LS
    me = t._player_img()
    nurse = next((o for o in t.people.values()), None)
    nimg = t._figure_img(nurse, (0, 1), 0) if nurse else None
    hm, hn = _dn.live_height(me, _LS), (_dn.live_height(nimg, _LS) if nimg is not None else None)
    check(me in _dn.PERSON_FRAMES and abs(hm - _dn.LIVE_PERSON) < 0.12, f"the player stands about {_dn.LIVE_PERSON} tiles in 3D ({hm:.2f})")
    check(hn is not None and abs(hn - hm) < 0.3, f"and the nurse about the same ({hn if hn is None else round(hn, 2)} vs {hm:.2f})")
g.walk_town_pos = g.walk_town_room = None
print(f"##### {len(fails)} failures")
