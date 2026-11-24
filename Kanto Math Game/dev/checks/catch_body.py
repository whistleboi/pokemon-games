# Opening a menu mid-encounter and coming back keeps the same encounter. Hoenn's Route 101 is walked (legacy menu clear,
# Step 5, 11-24): bump a wild Pokemon (MATH / BATTLE comes up), open BAG / BADGES / JOURNAL / OPTIONS / PC and back.
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
story.enter_region("HOENN")
story.player_team = [mk(258)]
p = walk_route("HOENN_ROUTE_101", "LITTLEROOT_TOWN")
check(walked(p), "Route 101 on its map")
m, d = beside(p, "wild")
p.step(*d)
walk_frames(2)
before = (p.mode, p.encounter is m, getattr(m.payload, "name", None))
print("   before:", before)
check(before[:2] == ("CHOICE", True), "bumping a wild Pokemon brings up MATH / BATTLE")
for label in ("BAG", "BADGES", "JOURNAL", "OPTIONS", "PC"):
    btn = next((b for b in getattr(p, "menu_entries", p.hud_buttons) if b.text == label), None)
    if not btn: continue
    btn.callback()
    menu = g.current_state
    back = getattr(menu, "go_back", None) or getattr(menu, "on_back", None) or getattr(menu, "close", None)
    if back: back()
    else: g.change_state(p)
    for _ in range(30): p.update()
    after = (p.mode, p.encounter is m, getattr(m.payload, "name", None))
    check(after == before and g.current_state is p and m in p.run.floor.movers, f"{label} ({type(menu).__name__}) -> same encounter {after}")
print(f"##### {fails} failures")
