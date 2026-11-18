# The Mart's TM shelf (Jordan, 11-18): SORT (number, power, type, kind), TYPE and KIND filters, tapped like a player.
from src.states import overworld as ow
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def click(btn):
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        ev = pygame.event.Event(kind, button=1, pos=btn.rect.center)
        left = g.ui_manager.unconsumed([ev])
        if left:
            g.current_state.handle_events(left)


def shot(n):
    m.draw()
    pygame.image.save(g.screen, S + "/" + n)


story.current_area_key = "CELADON_CITY"
story.money = 99999
story.badges = {"KANTO": ["B%d" % i for i in range(8)]}
m = PokeMartState(g, ow.CityState(g))
g.change_state(m)
if m.phase == "DIALOGUE":
    m.on_welcome_dialogue_end()
click(m.cat_buttons["TMs"])
check(m.category == "TMs" and m.btn_tm_sort in g.ui_manager.elements, "the TMs tab shows SORT / TYPE / KIND")
shot("tm_1_number.png")
n_all = len(m._list())
click(m.btn_tm_sort)
L = m._list()
pw = [m._tm_move(i)[1] for i in L]
check(m.tm_sort == "POWER" and pw == sorted(pw, reverse=True), f"SORT: POWER, strongest first ({L[:3]} {pw[:3]})")
shot("tm_2_power.png")
click(m.btn_tm_sort)
ty = [m._tm_move(i)[0] for i in m._list()]
check(m.tm_sort == "TYPE" and ty[0] == "NORMAL" and ty[-1] == "FAIRY", "SORT: TYPE (Normal ... Fairy)")
click(m.btn_tm_sort)
kd = [m._tm_move(i)[2] for i in m._list()]
check(m.tm_sort == "KIND" and kd[0] == "PHYSICAL" and kd[-1] == "STATUS", "SORT: KIND (physical, special, status)")
click(m.btn_tm_sort)
check(m.tm_sort == "NUMBER" and m._list()[0] == "TM001", "back to NUMBER")
click(m.btn_tm_type)
check(m.type_open and not m.shop_buttons and m.type_buttons[0] in g.ui_manager.elements, "TYPE opens the type chips")
shot("tm_3_type_menu.png")
click(next(b for b in m.type_buttons if b.text == "FIRE"))
L = m._list()
check(not m.type_open and L and all(m._tm_move(i)[0] == "FIRE" for i in L), f"TYPE: FIRE -> {len(L)} Fire TMs")
shot("tm_4_fire.png")
click(m.btn_tm_kind)
check(m.tm_kind == "DAMAGING" and all(m._tm_move(i)[2] != "STATUS" for i in m._list()), "KIND: DAMAGING")
for _ in range(3):
    click(m.btn_tm_kind)
L = m._list()
check(m.tm_kind == "STATUS" and all(m._tm_move(i)[2] == "STATUS" for i in L), f"KIND: STATUS -> {len(L)} Fire status TMs")
shot("tm_5_fire_status.png")
click(m.btn_tm_type)
click(m.type_buttons[0])
check(m.tm_type == "ALL", "TYPE: ALL again")
click(m.btn_tm_kind)
check(m.tm_kind == "ALL" and len(m._list()) == n_all, f"KIND: ALL: all {n_all} again")
btn = m.shop_buttons[0]
click(btn)
check(m.phase == "QTY" and m.btn_tm_sort not in g.ui_manager.elements, "picking a TM opens the quantity card (bar hidden)")
m.confirm_purchase()
m.cancel_purchase()
click(m.cat_buttons["BALLS"])
check(m.btn_tm_sort not in g.ui_manager.elements and m._shelf_top() == m.panel.y, "other tabs: no bar")
m.tm_sort = "POWER"; m._label_tm_bar()
m2 = PokeMartState(g, ow.CityState(g))
check(m2.tm_sort == "POWER", "the sort is kept for the next Mart visit")
print("FAILURES:", fails)
