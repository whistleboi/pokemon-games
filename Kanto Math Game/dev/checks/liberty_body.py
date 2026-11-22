# Liberty Garden (batch 3a's close-out, 11-21): Black 2's island walked in the live 3D view by the route walker. The
# Liberty Pier sailor's boat out to Dock 1; the lighthouse and Victini's old room up its stairs; Victini there after the
# Champion (Jordan 11-21: Black and White's spot, Lv 15); with Victini along, Juniper's visit and its dance; the boat home.
#   bash dev/checks/run.sh liberty
import json, time as _time
import numpy as _np
from src.states.overworld import CityState, PlayState as _PS
fails = []
def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c: fails.append(m)
g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.story_flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
story.story_flags["visited_CASTELIA_CITY"] = True
def settle(n=60):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()
OUT = os.environ.get("LIBERTY_SHOTS")   # (set it to a folder to keep the pictures)
def shot(name):
    if OUT:
        g.current_state.draw(); pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, name))
# 1) the pier sailor
story.current_area_key = "CASTELIA_CITY"
g.walk_town_pos = ("CASTELIA_CITY", (21, 12), (0, 1)); g.walk_town_room = ("CASTELIA_CITY", "liberty_pier")
g.change_state(CityState(g)); settle()
t = g.current_state
t._talk((20, 12)); settle(200)
t = g.current_state
check(type(t).__name__ == "DungeonState" and story.current_area_key == "LIBERTY_GARDEN", "the Liberty Pier sailor's boat takes you to Liberty Garden, walked by the route walker")
check(tuple(t.run.player) == (7, 12) and t.run.index == 0, f"...off the boat at Dock 1 ({tuple(t.run.player)})")
check(t._dl_live(), "...in the live 3D view")
shot("lg_dock.png")
# walk to the lighthouse door
t.run.player = t.anim_from = t.partner = t.partner_from = (16, 20); t.anim = 0; settle(5)
shot("lg_door.png")
t.step(0, -1); settle(40); t = g.current_state
check(t.run.index != 0, "the lighthouse door leads in")
shot("lg_light.png")
t.run.player = t.anim_from = t.partner = t.partner_from = (5, 2); t.anim = 0; settle(3)
t.step(0, -1); settle(40); t = g.current_state
check("Room" in t._floor_name(t.run.index), "the lighthouse stairs lead up to Victini's old room")
def victinis():
    return [m for m in g.current_state.run.floor.movers if isinstance(getattr(m, "payload", None), dict) and m.payload.get("text") == "Victini"]
check(not victinis(), "...no Victini there before the Champion")
shot("lg_room.png")
story.story_flags["beat_unova_champion"] = True
story.current_area_key = "LIBERTY_GARDEN"; g.walk_town_pos = g.walk_town_room = None
g.arrive_floor = ("LIBERTY_GARDEN", t.run.index, [3, 9])
g.change_state(_PS(g)); settle(10); t = g.current_state
vic = victinis()
check(len(vic) == 1 and (vic[0].x, vic[0].y) == (5, 6), f"after the Champion, Victini waits in its old room ({[(m.x, m.y) for m in vic]})")
shot("lg_victini.png")
if vic:
    t._use_figure(vic[0]); settle(30)
    st = g.current_state
    for _ in range(40):
        st = g.current_state
        if "Battle" in type(st).__name__: break
        settle(1)
    st = g.current_state
    en = getattr(st, "opponent_pokemon", None)
    check("Battle" in type(st).__name__ and int(getattr(en, "id", 0) or 0) == 494 and getattr(en, "level", 0) == 15, f"...walk up to it and the battle with Victini starts ({type(st).__name__}, {getattr(en, 'name', None)} Lv {getattr(en, 'level', None)})")
# Victini with you: Juniper on the island, the dance in its room
story.player_team.append(mk(494)); story.story_flags.pop("beat_unova_champion", None)
story.current_area_key = "CASTELIA_CITY"
g.walk_town_pos = ("CASTELIA_CITY", (21, 12), (0, 1)); g.walk_town_room = ("CASTELIA_CITY", "liberty_pier")
g.change_state(CityState(g)); settle(); t = g.current_state
t._talk((20, 12))
juni = None
for _ in range(300):
    st = g.current_state; st.update(); st.draw()
    if type(st).__name__ == "DungeonState" and st._scenes().actors and juni is None:
        for k in range(6):
            for _ in range(15): st.update(); st.draw()
            shot("lg_juniper%d.png" % k)
        juni = True
    if getattr(st, "npc_active", False):
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
        st.dialogue_box.advance()
check(story.story_flags.get("b2_liberty_juniper") and juni, "with Victini along, Professor Juniper walks over on the island and talks about it")
t = g.current_state
t.run.player = t.anim_from = t.partner = t.partner_from = (16, 20); t.anim = 0; settle(3)
t.step(0, -1); settle(40); t = g.current_state
t.run.player = t.anim_from = t.partner = t.partner_from = (5, 2); t.anim = 0; settle(3)
t.step(0, -1); settle(20); t = g.current_state
danced = None
for _ in range(300):
    st = g.current_state; st.update(); st.draw()
    if type(st).__name__ == "DungeonState" and st._scenes().actors and danced is None:
        for _ in range(20): st.update(); st.draw()
        shot("lg_dance.png"); danced = True
    if getattr(st, "npc_active", False):
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
        st.dialogue_box.advance()
check(story.story_flags.get("b2_liberty_dance") and danced, "...and in its old room Victini pops out for a dance")
# home again on the boat
story.current_area_key = "LIBERTY_GARDEN"; g.walk_town_pos = g.walk_town_room = None
g.arrive_floor = ("LIBERTY_GARDEN", 0, [7, 12])
g.change_state(_PS(g)); settle(10); t = g.current_state
sail = next(m for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict) and "sailor" in m.payload.get("text", ""))
t._use_figure(sail); settle(200); t = g.current_state
check(story.current_area_key == "CASTELIA_CITY" and getattr(t, "room", None) == "liberty_pier" and tuple(t.player) == (21, 12),
      f"the island's sailor takes you back to Liberty Pier ({story.current_area_key}, {getattr(t, 'room', None)}, {getattr(t, 'player', None)})")
print(f"##### {len(fails)} failures")
