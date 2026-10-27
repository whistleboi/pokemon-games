
from src.states import overworld as ow
from src.states.menu_grid import MenuGridState
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.systems import PokemonPartyMenuState, BagState
fails = 0
out = sys.argv[1] + "/shots5"
os.makedirs(out, exist_ok=True)


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def shot(name):
    g.current_state.draw()
    g.keyboard.draw(g.screen)
    pygame.image.save(g.screen, f"{out}/{name}.png")


g.data.save = lambda *a, **k: None
story.inventory.update({"TOWN_MAP": 1, "HM_FLY": 1})

print("1) MENU grid")
story.current_area_key = "VIRIDIAN_CITY"
city = ow.CityState(g)
g.change_state(city)
shot("city")
check([b.text for b in city.hud_buttons] == ["MENU"], "one MENU button on the town screen")
city.hud_buttons[0].callback()
grid = g.current_state
check(isinstance(grid, MenuGridState) and {"BAG", "PC", "SAVE", "OPTIONS", "MAP", "FLY"} <= {t.label for t in grid.tiles},
      f"grid tiles: {[t.label for t in grid.tiles]}")
shot("menu_grid")
bag_tile = next(t for t in grid.tiles if t.label == "BAG")
bag_tile.callback()
check(isinstance(g.current_state, BagState), "BAG tile opens the Bag")
shot("bag")
g.change_state(grid)
grid.close()
check(g.current_state is city, "CLOSE goes back")
story.current_area_key = "KANTO_ROUTE_1"
ps = ow.PlayState(g)
g.change_state(ps)
check([b.text for b in ps.hud_buttons] == ["MENU"], "and on routes")
shot("route")

print("2) battle")
pk = mk(4)
pk.level = 20
pk.current_hp = pk.get_max_hp()
story.player_team = [pk]
foe = mk(113)  # Chansey: bulky, so a (now still-attacking) wrong answer doesn't end the battle
foe.level = 40
foe.current_hp = foe.get_max_hp()
foe.moves = ["GROWL"]  # it can't hurt us either, so the battle never ends early (was a 1-in-3 flake)
wb = WildBattleState(g, foe, "KANTO_ROUTE_1")
g.change_state(wb)
for _ in range(300):
    if wb.phase == "MENU" and not wb.dialogue_box.visible:
        break
    if wb.dialogue_box.visible:
        wb.dialogue_box.is_finished = True
        cb = wb.dialogue_box.callback
        if cb:
            wb.dialogue_box.callback = None
            cb()
    wb.update()
wb.open_move_menu()
shot("moves")
check(all(hasattr(b, "effect") for b in wb.move_buttons[:-1]), "move buttons carry effectiveness")
wb.choose_move(wb.move_buttons[0].text.replace(" ", "-"))
wrong = next(i for i, o in enumerate(wb.options) if o != wb.correct_ans)
wb.math_ui.on_click(wrong)
for _ in range(6):
    wb.update()
shot("answer_wrong")
check(wb.phase == "ANSWER_FEEDBACK" and "Nice try" in wb.math_ui.feedback["text"], "wrong answer: kind message")
wb.math_ui.on_click(0)  # ignored during the beat
for _ in range(40):
    wb.update()
check(wb.phase != "ANSWER_FEEDBACK", f"then the turn runs ({wb.phase})")
for _ in range(300):
    if wb.phase == "MENU" and not wb.dialogue_box.visible:
        break
    if wb.dialogue_box.visible:
        wb.dialogue_box.is_finished = True
        cb = wb.dialogue_box.callback
        if cb:
            wb.dialogue_box.callback = None
            cb()
    wb.update()
shot("hp_after")
wb.open_move_menu()
wb.choose_move(wb.move_buttons[0].text.replace(" ", "-"))
wb.math_ui.on_click(wb.options.index(wb.correct_ans))
for _ in range(5):
    wb.update()
shot("answer_right")
check(wb.math_ui.feedback and wb.math_ui.feedback["correct"], "right answer: cheer")

print("3) party")
story.player_team = [mk(25), mk(1), mk(130)]
g.change_state(PokemonPartyMenuState(g, city))
shot("party")
cb = g.current_state.cancel_btn
check(cb.rect.right <= g.width - 10 and g.assets.fonts["s_med"].size("CANCEL")[0] < cb.rect.w, "CANCEL fits")
print("FAILURES:", fails)
