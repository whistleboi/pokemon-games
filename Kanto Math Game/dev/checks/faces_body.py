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
        tried += 1
        imgs = {pygame.image.tobytes(st._figure_img(opt, f, 0), "RGBA") for f in ((0, 1), (-1, 0), (1, 0), (0, -1))}
        if len(imgs) == 4:
            turned.append(opt.get("text"))
    check(tried and len(turned) == tried, f"{area}: all {tried} drawn four ways ({turned})")
print("FAILURES:", fails)
