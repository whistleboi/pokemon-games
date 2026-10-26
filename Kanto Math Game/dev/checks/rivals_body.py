import pygame
from src.states.menus import RivalSelectionState
from src.states.overworld import CityState, _trainer_sprite, _fill_names
from src.states.systems import FlyState
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
g.player_character = "brendan"
for region, want in [("KANTO", ["BLUE"]), ("JOHTO", ["SILVER"]), ("HOENN", ["MAY", "BRENDAN"]), ("SINNOH", ["BARRY"]),
                     ("UNOVA", ["CHEREN", "BIANCA"]), ("KALOS", ["SERENA", "CALEM"]), ("ALOLA", ["HAU"]),
                     ("GALAR", ["HOP"]), ("PALDEA", ["NEMONA"])]:
    done = []
    st = RivalSelectionState(g, region=region, on_done=lambda: done.append(1))
    check([n for n, _ in st.options] == want, f"{region}: {[n for n, _ in st.options]}")
    st.input_name = "ZED" if region == "KALOS" else ""
    st.confirm_selection()
    if st.step == "friend":
        st.confirm_selection()
    r = story.region_rivals[region]
    print("     ", region, r["name"], r["character"], r.get("friend_name"), r.get("chosen"))
check(story.region_rivals["KALOS"]["name"] == "ZED" and story.region_rivals["KALOS"]["friend_name"] == "SHAUNA", "Kalos: typed name, Shauna default")
check(story.region_rivals["UNOVA"]["friend_name"] == "BIANCA", "Unova: Cheren picked -> Bianca is the friend")
# Arriving in a region with no pick yet asks first.
story.region_rivals.pop("ALOLA", None)
story.current_area_key = "IKI_TOWN"
c = CityState(g); g.change_state(c)
check(isinstance(g.current_state, RivalSelectionState) and g.current_state.region == "ALOLA", "arriving in Alola opens the rival screen")
g.current_state.input_name = "KEO"; g.current_state.confirm_selection(); g.current_state.input_name = "SILVY"; g.current_state.confirm_selection()
check(isinstance(g.current_state, CityState) and g.rival_name == "KEO" and g.friend_name == "SILVY", "then the town, with the names set")
check(_fill_names(g, "{rival_name} and {friend_name}") == "KEO and SILVY", "names filled into text")
check(_trainer_sprite(g, "{rival_character}") is not None and _trainer_sprite(g, "{friend_character}") is not None, "rival and friend sprites")

print("Fly: three columns, scrolls like the PC")
for k, a in g.loader.area_data["STORY_PROGRESSION"].items():
    if a.get("area_type") == "town":
        story.story_flags[f"visited_{k}"] = True
f = FlyState(g, c)
g.change_state(f)
f.draw()
xs = sorted({b.rect.x for b in f.cell_buttons})
check(len(xs) == 3 and len(f.rows) > f.visible_rows, f"{len(xs)} columns, {len(f.rows)} rows ({f.visible_rows} in view)")
first = f.cell_buttons[0].text
f.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=5, pos=(600, 400))])
check(f.first_row == 1 and f.cell_buttons[0].text != first or f.rows[1][0] == "towns", "the wheel scrolls the list")
print("FAILURES:", fails)
