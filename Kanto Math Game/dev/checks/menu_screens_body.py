# The MENU and its screens as each walked region's own game opens and closes them (Jordan 11-24, region/systems step 3;
# src/vfx/menu_screens.py): per region (Kanto FireRed, Hoenn Emerald, Johto HGSS, Sinnoh Platinum, Unova Platinum's,
# Orre Essentials) the MENU opened from a town's map (at once), every screen on it opened by its tile and closed with Esc
# as a player would (the game's fade: colour, length; FireRed's party -2 fade, its Bag's shutter, its Pokedex from
# white; HGSS's Pokegear apps' 2-frame fade; Save at once), the MENU closed (at once); Kalos (a menu region) keeps the
# old crossfade. Played through Game._frame; mid-fade pictures and a GIF per region in out/menu_screens.
#   bash dev/checks/run.sh menu_screens
import math
import os as _os
from PIL import Image
from src.config import FPS
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState
from src.vfx import area_changes as ac
from src.vfx import menu_screens as ms

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


OUT = _os.path.join(S, "menu_screens")
_os.makedirs(OUT, exist_ok=True)
g.dungeon_routes = True; g.walk_towns = True
story.story_flags["hoenn_version"] = "OMEGA_RUBY"; story.story_flags["unova_version"] = "BLACK_2"
for _k in ("kanto", "johto", "hoenn", "sinnoh", "unova", "orre"):
    story.story_flags[f"received_starter_{_k}"] = story.story_flags[f"move_offer_{_k}"] = True
story.inventory["TOWN_MAP"] = 1
story.player_team = [mk(25), mk(1)]
GIF = []


def grab():
    if len(GIF) < 1200:
        s = pygame.transform.smoothscale(g.screen, (640, 360))
        GIF.append(Image.frombytes("RGB", s.get_size(), pygame.image.tobytes(s, "RGB")))


def shot(name):
    pygame.image.save(g.screen, _os.path.join(OUT, name))


def frames_for(p):
    return int(math.ceil(sum(s[1] for s in p[0] + p[1]) * FPS / 60.0)) + 1


def town(area):
    story.current_area_key, story.last_area_key = area, None
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = g.walk_town_room = None
    g._sign_area = None
    st = CityState(g)
    g.change_state(st)
    for _ in range(30):   # (tap through anything said first)
        if not getattr(st, "npc_active", False):
            break
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update()
    g.area_wipe = ac.ACTIVE = None
    g._fade_left = 0
    return st


def run_wipe(name=None, limit=80):
    """Frames until the wipe is over; (frames, centre colour on the last old-screen frame, on the first new one, styles)."""
    w = g.area_wipe
    took, last_out, first_in, styles = 0, None, None, []
    outf = int(w.out_len * FPS / 60.0) if w else 0
    shots = {max(1, (outf + 1) // 2): "going", outf + max(1, (w.length - outf) // 2) if w else 0: "coming"}
    while g.area_wipe is w and w is not None and took < limit:
        hold = w.holding()
        g._frame(); grab(); took += 1
        c = tuple(g.screen.get_at((g.width // 2, g.height // 2)))[:3]
        top = tuple(g.screen.get_at((g.width // 2, 8)))[:3]
        styles.append(w.log[-1][0] if w.log else None)
        if hold:
            last_out = c
        elif first_in is None:
            first_in = (c, top)
        if name and took in shots:   # (one picture as the old screen goes, one as the new one shows)
            shot(name.replace(".png", "_" + shots[took] + ".png"))
    return took, last_out, first_in, styles


def esc():
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="\x1b", scancode=41))
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_ESCAPE, mod=0, unicode="\x1b", scancode=41))


def dark(c, tol=24):
    return c is not None and max(c) <= tol


def light(c, tol=200):
    return c is not None and min(c) >= tol


def open_menu(st):
    menu_btn = next(b for b in st.hud_buttons if getattr(b, "text", "") == "MENU")
    for _ in range(3):
        g._frame(); grab()
    menu_btn.callback()
    return g.current_state


LABELS = ("POKEMON", "BAG", "POKEDEX", "BADGES", "JOURNAL", "MAP", "PC", "PHONE", "RADIO", "STATS", "OPTIONS", "SAVE")
PLACES = {"KANTO": ("frlg", "PEWTER_CITY"), "HOENN": ("emerald", "OLDALE_TOWN"), "JOHTO": ("hgss", "VIOLET_CITY"),
          "SINNOH": ("platinum", "JUBILIFE_CITY"), "UNOVA": ("platinum", "FLOCCESY_TOWN"), "ORRE": ("orre", "PHENAC_CITY")}

print("0) the numbers (60 fps frames, from transitions_research)")
check(ms.plan("frlg", "open", "party") == ([ms._f(17)], [ms._i(9)]) and ms.plan("frlg", "close", "party") == ([ms._f(9)], [ms._i(17)]),
      "FireRed's party: field out 17, party in 9 (delay -2); out 9, the field in 17")
check(ms.plan("frlg", "open", "bag")[1][0][0] == "shutter_up" and ms.plan("frlg", "close", "bag")[0][0][0] == "shutter_down",
      "FireRed's Bag: the black shutter opens upward, closes downward")
check(ms.plan("emerald", "open", "party") == ms.plan("emerald", "close", "bag") == ([ms._f(17)], [ms._i(17)]), "Emerald: delay 0 everywhere")
check(ms.plan("hgss", "open", "bag") == ms.plan("platinum", "close", "dex") == ([ms._f(6)], [ms._i(6)]), "Gen 4: 6-frame fades")
check(ms.plan("hgss", "open", "gear") == ([ms._f(2)], [ms._i(2)]) and ms.plan("platinum", "open", "gear") == ([ms._f(6)], [ms._i(6)]),
      "HGSS's Pokegear apps: the 2-frame swap (Platinum has none)")
check(ms.plan("orre", "open", "bag") == ([ms._f(24)], [ms._i(24)]), "Orre: pbFadeOutIn 0.4 s + 0.4 s")
check(all(ms.plan(k, w, "save") == "cut" for k in ("frlg", "emerald", "hgss", "platinum", "orre") for w in ("open", "close")), "Save: no fade anywhere")

for region, (key, town_key) in PLACES.items():
    GIF.clear()
    print(f"\n{region} ({key})")
    t = town(town_key)
    check(isinstance(t, WalkTownState) and ac.here_key(g) == key, f"{town_key}: walked, {key}'s profile")
    menu = open_menu(t)
    check(type(menu).__name__ == "HomeMenuState" and g.area_wipe is None and g._fade_left == 0,
          "MENU: opens at once (no fade, no crossfade)")
    g._frame(); grab()
    shot(f"{region.lower()}_menu.png")
    labels = [b.label for b in menu.tiles]
    for label in LABELS:
        if label not in labels:
            continue
        if g.current_state is not menu:
            g.change_state(menu); g.area_wipe = ac.ACTIVE = None; g._fade_left = 0
        for _ in range(2):
            g._frame(); grab()
        tile = next(b for b in menu.tiles if b.label == label)
        tile.callback()
        scr = g.current_state
        what = ms.kind(scr)
        want = ms.plan(key, "open", what)
        w = g.area_wipe
        if want == "cut":
            check(scr is not menu and w is None and g._fade_left == 0, f"{label} ({type(scr).__name__}): at once, no fade")
        else:
            check(w is not None and (w.out, w.into) == want and w.length == frames_for(want),
                  f"{label} ({type(scr).__name__}, {what}): in with {key}'s fade ({w.length if w else None} frames, {frames_for(want) if want else None} wanted)")
            took, lo, fi, styles = run_wipe(f"{region.lower()}_{label.lower()}_open.png")
            check(took == frames_for(want) and dark(lo) and fi is not None,
                  f"...{took} frames, the menu gone to black ({lo}), the screen showing through ({fi[0] if fi else None})")
            if key == "frlg" and what == "bag":
                check("shutter_up" in styles and dark(fi[1]) if fi else False, f"...the Bag's black shutter over its top first ({fi[1] if fi else None})")
            if key == "frlg" and what == "dex":
                check(fi and light(fi[0], 150), f"...the Pokedex comes in from white ({fi[0] if fi else None})")
        for _ in range(3):
            g._frame(); grab()
        if g.current_state is not scr:
            check(type(g.current_state).__name__ == "HomeMenuState" or what in ("save",), f"...{label} already went on ({type(g.current_state).__name__})")
            continue
        esc()
        for _ in range(4):
            g._frame()
            if g.current_state is not scr:
                break
        if g.current_state is scr:   # (a screen Esc doesn't close: its own way back)
            back = next((getattr(scr, a) for a in ("previous_state", "back", "return_state") if getattr(scr, a, None) is not None), menu)
            g.change_state(back if not callable(back) else menu)
        back_to = g.current_state
        wantc = ms.plan(key, "close", what)
        w = g.area_wipe
        if back_to is not menu:
            check(what in ("save", "options"), f"...{label} back to {type(back_to).__name__} (the MENU wanted)")
            continue
        if wantc == "cut":
            check(w is None, f"...back to the MENU at once")
            continue
        check(w is not None and (w.out, w.into) == wantc and w.length == frames_for(wantc), f"...back to the MENU with {key}'s fade ({w.length if w else None} frames)")
        lo0 = tuple(g.screen.get_at((g.width // 2, g.height // 2)))[:3]   # (the Esc frame drew the wipe's first frame)
        took, lo, fi, styles = run_wipe(f"{region.lower()}_{label.lower()}_close.png")
        lo = lo if lo is not None else lo0
        check(took + 1 == frames_for(wantc) and dark(lo), f"...{took + 1} frames, through black ({lo})")
        if key == "frlg" and what == "bag":
            check("shutter_down" in styles, "...the Bag's shutter closing downward")
    if g.current_state is not menu:
        g.change_state(menu); g.area_wipe = ac.ACTIVE = None
    g._frame(); grab()
    esc()
    for _ in range(3):
        g._frame(); grab()
        if g.current_state is not menu:
            break
    check(isinstance(g.current_state, WalkTownState) and g.area_wipe is None and g._fade_left == 0, "MENU closed with Esc: back on the map at once")
    for _ in range(6):
        g._frame(); grab()
    # straight from the map: the Bag (the map's own BAG button where there is one) gets the same fade
    m = g.current_state
    from src.states.systems import BagState
    g.change_state(BagState(g, m))
    w = g.area_wipe
    wantb = ms.plan(key, "open", "bag")
    check(w is not None and (w.out, w.into) == wantb, "the Bag straight from the map: the same fade")
    run_wipe()
    g.change_state(m)
    run_wipe()
    check(g.current_state is m, "...and back on the map")
    if GIF:
        GIF[0].save(_os.path.join(OUT, f"{region.lower()}.gif"), save_all=True, append_images=GIF[1:900], duration=40, loop=0)

print("\nKalos (a menu region): today's crossfade stays")
story.current_area_key = next(k for k, v in g.loader.area_data["STORY_PROGRESSION"].items()
                              if isinstance(v, dict) and v.get("region") == "KALOS" and v.get("area_type") == "town")
c = CityState(g)
g.change_state(c)
g.area_wipe = ac.ACTIVE = None
g._frame()
check(ac.here_key(g) is None, f"{story.current_area_key}: no profile")
menu_btn = next((b for b in getattr(c, "hud_buttons", []) if getattr(b, "text", "") == "MENU"), None)
if menu_btn is not None:
    menu_btn.callback()
    check(type(g.current_state).__name__ == "HomeMenuState" and g.area_wipe is None and g._fade_left == g.FADE_FRAMES,
          "MENU: the old 6-frame crossfade")
    mn = g.current_state
    next(b for b in mn.tiles if b.label == "BAG").callback()
    check(g.area_wipe is None and g._fade_left == g.FADE_FRAMES, "Bag: the old crossfade")
else:
    check(False, "Kalos town: a MENU button")
print("\nOptions > Screen fade off: everything at once")
t = town("PEWTER_CITY")
keep = g.FADE_FRAMES
g.FADE_FRAMES = 0
open_menu(t)
mn = g.current_state
next(b for b in mn.tiles if b.label == "BAG").callback()
check(g.area_wipe is None, "no wipe with the fades off")
g.FADE_FRAMES = keep
print(f"\n##### {len(fails)} failures")
for f in fails:
    print("FAIL " + f)
