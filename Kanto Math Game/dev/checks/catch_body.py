from src.states.overworld import PlayState
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
story.current_area_key = "HOENN_ROUTE_101"
story.player_team = [mk(258)]
p = PlayState(g); g.states["play"] = p; g.change_state(p)
for _ in range(5): p.update()
p.action_search_pokemon()
for _ in range(60): p.update()
names = lambda: [getattr(x, "name", None) if x is not None else None for x in p.p_data]
before = (names(), p.pending_wild_encounters, p.catch_selection_active)
print("   before:", before)
for label in ("BAG", "BADGES", "JOURNAL", "OPTIONS", "PC"):
    btn = next((b for b in getattr(p, "menu_entries", p.hud_buttons) if b.text == label), None)
    if not btn: continue
    btn.callback()
    menu = g.current_state
    back = getattr(menu, "go_back", None) or getattr(menu, "on_back", None) or getattr(menu, "close", None)
    if back: back()
    else: g.change_state(p)
    for _ in range(30): p.update()
    after = (names(), p.pending_wild_encounters, p.catch_selection_active)
    check(after == before and g.current_state is p, f"{label} ({type(menu).__name__}) -> same choices {after[0]}")
print(f"##### {fails} failures")
