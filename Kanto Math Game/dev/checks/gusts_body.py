# Timed gusts in a walked room (src/world/gusts.py): Black 2's Mistralton Gym is a wind tunnel - the turbines spin up, then
# anyone in the open is blown back toward the door; a wall upwind shelters you. Main cleanup clean-main-unova-gym-wind, 11-24.
#   bash dev/checks/run.sh gusts
from src.states.overworld import CityState
from src.world import gusts

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
g.data.save = lambda *a, **k: None
story.enter_region("UNOVA")
story.current_area_key, story.last_area_key = "MISTRALTON_CITY", None
story.story_flags["visited_MISTRALTON_CITY"] = True
g.walk_town_pos = g.walk_town_room = None
t = CityState(g)
if not hasattr(t, "town_map") or "gym" not in (t.town_map.get("rooms") or {}):
    print("   (Mistralton Gym isn't walked on this branch)")
else:
    cfg = {"every": 60, "warn": 10, "blow": 8, "from": "n", "lanes": [[9, 42, 13, 49]], "to": [11, 48]}
    t.town_map["rooms"]["gym"]["gusts"] = cfg
    t._go("gym", "ROOM:MAIN")
    check(t.room == "gym" and t.gusts == cfg and t._gust_t == 0, f"into the Gym: its wind, the clock at 0 ({t.room})")

    def frames(n):
        for _ in range(n):
            t.update()

    t.npc_active = False
    t.player, t.anim, t.mode = (11, 43), 0, "MAP"
    t._gust_t = 60 - 8 - 10 - 1   # (just before the warning)
    frames(2)
    check(gusts.phase(t) == "warn", f"the turbines spin up first ({gusts.phase(t)})")
    check(t.player == (11, 43), "...the warning moves no one")
    frames(12)
    for _ in range(80):
        if not t._gust_slide and t.player != (11, 43):
            break
        t.update()
    check(t.player == (11, 48), f"out in the open: blown back down the hall to the door ({t.player})")

    t.player, t.anim, t._gust_slide = (9, 46), 0, False   # (right under a post: the wall upwind)
    check(gusts.sheltered(t, cfg, (9, 46)) and not gusts.sheltered(t, cfg, (11, 44)), "a post upwind shelters you; open floor doesn't")
    t._gust_t = 60 - 8 - 1
    frames(10)
    check(t.player == (9, 46) and not t._gust_slide, f"sheltered: the gust passes you by ({t.player})")

    t.player, t.anim, t._gust_slide = (3, 10), 0, False   # (out of the wind's lanes)
    check(not gusts.in_lane(cfg, (3, 10)), "a tile outside the lanes")
    t._gust_t = 60 - 8 - 1
    frames(10)
    check(t.player == (3, 10), "...isn't blown")

    t._go(None, "ROOM:gym")
    t._go("gym", "ROOM:MAIN")
    check(t._gust_t == 0, "back in the room: the clock starts again")
    t._gust_t = 60 - 4
    t.draw()
    check(True, "drawn while it blows")
print(f"##### {fails} failures")
