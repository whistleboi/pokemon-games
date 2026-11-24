"""Omega Ruby / Alpha Sapphire's small places, on Hoenn's Emerald maps (Jordan, 11-14: "add the 123 go fish shop and
associating npcs, scenes around it"; the Move Reminder "in game with a funny line that he was put out of business once all
pokemon remembered all of their moves").

- Route 123: 123 Go Fish, ORAS's supply shack by the pond (Emerald's own small house front, from its Mauville picture,
  where the open ground north-east of the pond is); nothing for sale, as in ORAS. Its guard dog Chomper (a Poochyena) waits
  by the door, runs up the first time you come near, and digs up the Gyaradosite when you give it a good scratch. The
  Fisherman by the pond who loves Magikarp gives the Eviolite (already the route's).
- Fallarbor: the Move Reminder's house (Emerald's, under its sign) is a door now: he's out of business.
The options are hoenn_area_data.json's (door "gofish", "reminder"; "Chomper").
- Shoal Cave's Ice room: its own wild list with a rare Sneasel (Jordan, 11-23: Weavile in the Hoenn dex needs a Sneasel;
  ORAS has none wild; with the Frontier's Razor Claw it evolves at night). Pool HOENN_SHOAL_CAVE_ICE_ROOM_PERCENTAGES.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TILES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "assets", "tiles")
SHACK = (42, 4)          # (its top-left tile on Route 123: 4 x 4, the door on its bottom row, second from the left)
HOUSE = (18, 11, 4, 4)   # (Emerald's small pink house in Mauville's picture, 0_2.png: x, y, w, h in tiles; door column 1)
CHOMPER = ((38, 10), (45, 8))   # (from the old Gyaradosite spot to the shack's door)


def _stamp(m, at, crop, pic_from="0_2"):
    """Draw a building from an Emerald town picture (ground and top layers, its lawn cut away) onto this map's picture."""
    import pygame as pg
    if not pg.get_init():
        pg.init()
    T = 16
    gfile = m["roofs"]["_picture"]["f"]
    base = os.path.splitext(os.path.basename(gfile))[0]
    ground = pg.image.load(os.path.join(TILES, "em_ground", base + ".png"))
    top_path = os.path.join(TILES, "em_top", base + ".png")
    top = pg.image.load(top_path) if os.path.exists(top_path) else None
    src = pg.image.load(os.path.join(TILES, "em_ground", pic_from + ".png")).copy()
    src.blit(pg.image.load(os.path.join(TILES, "em_top", pic_from + ".png")), (0, 0))
    lawn = {tuple(src.get_at((x, y)))[:3] for x in range(0, 16) for y in range(160, 176)}
    x0, y0, w, h = crop
    img = pg.Surface((w * T, h * T), pg.SRCALPHA)
    img.blit(src, (0, 0), (x0 * T, y0 * T, w * T, h * T))
    for px in range(w * T):
        for py in range(h * T):
            if tuple(img.get_at((px, py)))[:3] in lawn:
                img.set_at((px, py), (0, 0, 0, 0))
    ground.blit(img, (at[0] * T, at[1] * T))
    out_g = f"{base}_oras.png"
    pg.image.save(ground, os.path.join(TILES, "em_ground", out_g))
    m["roofs"] = dict(m["roofs"], _picture=dict(m["roofs"]["_picture"], f=f"em_ground/{out_g}"))
    if top is not None:
        top = top.copy()
        top.fill((0, 0, 0, 0), (at[0] * T, at[1] * T, w * T, h * T))
        pg.image.save(top, os.path.join(TILES, "em_top", out_g))
        m["overheads"] = [dict(o, f=f"em_top/{out_g}") if o.get("f") == f"em_top/{base}.png" else o for o in m.get("overheads") or []]


def _route123(maps):
    m = maps.get("HOENN_ROUTE_123")
    if not m:
        return
    rows = [list(r) for r in m["art"]]
    sx, sy = SHACK
    for y in range(sy, sy + 4):
        for x in range(sx, sx + 4):
            assert rows[y][x] == ".", f"123 Go Fish stands on open ground ({x},{y} is {rows[y][x]!r})"
            rows[y][x] = "c"
    rows[sy + 3][sx + 1] = "D"
    rows[sy + 2][sx + 1] = "G"
    assert rows[sy + 4][sx + 1] == ".", "its door opens onto the path"
    # Chomper: the old Gyaradosite spot's name moves with it to the shack's door (the map's names go by reading order)
    (ox, oy), (nx, ny) = CHOMPER
    names = list(m.get("people") or [])
    spots = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "N"]
    pairs = [(xy, ("Chomper" if n == "GYARADOSITE" else n)) for xy, n in zip(spots, names)]
    pairs = [((nx, ny), n) if xy == (ox, oy) else (xy, n) for xy, n in pairs]
    rows[oy][ox] = "."
    rows[ny][nx] = "N"
    pairs.sort(key=lambda p: (p[0][1], p[0][0]))
    m["people"] = [n for _xy, n in pairs] + names[len(spots):]
    m["art"] = ["".join(r) for r in rows]
    m["buildings"] = dict(m.get("buildings") or {}, G="gofish")
    m["moves"] = dict(m.get("moves") or {}, **{f"{nx},{ny}": {"m": "look", "d": "dlr"}})
    m["scenes"] = list(m.get("scenes") or []) + [
        {"who": "Chomper", "trigger": {"zone": [38, 6, 48, 11]}, "flag": "chomper_ran_up", "approach": True, "after": "home",
         "lines": ["Chomper: Arf! Arf!", "The Poochyena from 123 Go Fish bounded over! It's sniffing your pockets..."]}]
    _stamp(m, SHACK, HOUSE)


def _fallarbor(maps):
    m = maps.get("FALLARBOR_TOWN")
    if not m:
        return
    m["buildings"] = dict(m.get("buildings") or {}, F="reminder")


def _shoal_ice_room(maps):
    m = maps.get("HOENN_SHOAL_CAVE")
    if not m:
        return
    i = m["floor_names"].index("Ice room")
    m["floors"][i]["pool"] = "HOENN_SHOAL_CAVE_ICE_ROOM_PERCENTAGES"


def apply(maps):
    _route123(maps)
    _fallarbor(maps)
    _shoal_ice_room(maps)
