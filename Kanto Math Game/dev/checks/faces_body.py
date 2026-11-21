# People and Pokemon on the walked maps face the way they're turned (11-18; the old "everyone faces down" note):
# each person, and each Pokemon standing about, is drawn four different ways for down / left / right / up; a boss
# keeps facing out. Orre's Phenac City (its people and its Jigglypuff and Pidgey), Gateon Port and Pallet Town.
from src.states import overworld as ow
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.walk_towns = True
for area, region in (("PHENAC_CITY", "ORRE"), ("GATEON_PORT", "ORRE"), ("PALLET_TOWN", "KANTO")):
    story.enter_region(region)
    story.current_area_key, story.last_area_key = area, None
    g.walk_town_pos = None; g.walk_town_room = None
    g.change_state(ow.CityState(g))
    for _ in range(3):
        g.current_state.update()
    st = g.current_state
    ppl = st._people()
    turned, tried = [], 0
    for mo in list(st.motions.values()):
        opt = ppl.get(mo.pos)
        if not opt:
            continue
        from src.states.overworld.dungeon import sprite_map as _sm
        _spec = (_sm(g).get("figures") or {}).get(f"{area}:{opt.get('text')}") or {}
        if _spec.get("item") or "object" in str(_spec.get("sheet", "")):   # (a thing, not a person: a sack, an item ball - one way only)
            continue
        tried += 1
        imgs = {pygame.image.tobytes(st._figure_img(opt, f, 0), "RGBA") for f in ((0, 1), (-1, 0), (1, 0), (0, -1))}
        if len(imgs) == 4:
            turned.append(opt.get("text"))
    check(tried and len(turned) == tried, f"{area}: all {tried} drawn four ways ({turned})")

print("A roof edge doesn't hide the head of someone standing just south of it (11-18: art.over_uncovered)")
from src.dungeon import art as _art
_scr = pygame.Surface((64, 96), pygame.SRCALPHA)
_roof = pygame.Surface((64, 32), pygame.SRCALPHA); _roof.fill((200, 0, 0, 255))   # (a roof over the top tile row)
_fig = pygame.Surface((20, 40), pygame.SRCALPHA); _fig.fill((0, 0, 255, 255))      # (someone 40 px tall)
_south = _fig.get_rect(midbottom=(32, 62))   # (feet on the open tile below the roof, head up in the roof's row)
_under = _fig.get_rect(midbottom=(32, 30))   # (standing under the roof itself)
_scr.blit(_fig, _south); _scr.blit(_fig, _under); _scr.blit(_roof, (0, 0))
_art.over_uncovered(_scr, [(62, _fig, _south), (30, _fig, _under)], [(_roof, (0, 0))], (0, 0))
check(tuple(_scr.get_at((32, 26)))[:3] == (0, 0, 255), "south of the edge: the head shows over the roof")
check(tuple(_scr.get_at((32, 10)))[:3] == (200, 0, 0), "under the roof: still hidden")
# ---- furniture drawings per region (11-18, roadmap bug: the kinds were shared, a change for one region's rooms showed in all)
print("4) a region's own furniture drawing stays in that region")
_room = ["...", ".m.", "..."]
_roofs = {"_kinds": {"1,1": "crate"}, "_things": {"1,1": [150, 100, 60]}}


def _crate(region):
    img = _art.surface(_room, {}, 48, dict(_roofs, _furniture=region))
    return pygame.image.tobytes(img.subsurface(pygame.Rect(48, 48, 48, 48)), "RGB")


_johto0, _orre0 = _crate("JOHTO"), _crate("ORRE")
check(_johto0 == _orre0, "before: both regions draw a crate the shared way")


@_art.furniture_drawing("ORRE", "crate")
def _test_crate(surf, r, col, same):
    pygame.draw.rect(surf, (0, 255, 0), r)


try:
    _johto1, _orre1 = _crate("JOHTO"), _crate("ORRE")
    check(_orre1 != _orre0, "Orre's own crate drawing is used in Orre")
    check(_johto1 == _johto0, "...and Johto's crates are untouched")
finally:
    _art.FURNITURE_OWN.pop(("ORRE", "crate"), None)
_art.FURNITURE_STYLE = None
print("FAILURES:", fails)
