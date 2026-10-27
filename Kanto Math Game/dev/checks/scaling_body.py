
from src.world import levels
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
story.current_area_key = "ROUTE_1"
story.badges = {}

print("1) a fresh starter: Route 1 keeps its own levels")
lead = mk(4)
lead.level = 5
story.player_team = [lead]
base = levels._area_levels(g).get("ROUTE_1", 5)
check(levels.area_level(g, "ROUTE_1") == max(base, 2), f"area level {levels.area_level(g, 'ROUTE_1')} (data {base})")

print("2) an over-levelled team: wild Pokemon and trainers follow its best member")
weak = mk(1)
weak.level = 6
lead.level = 14
story.player_team = [weak, lead]
wl = [levels.wild_level(g, "ROUTE_1") for _ in range(200)]
check(min(wl) >= 9 and max(wl) <= 12, f"wild Lv {min(wl)}-{max(wl)} for a Lv 14 lead (cap-5..cap-2)")
tl = [levels.trainer_level(g, "ROUTE_1") for _ in range(200)]
check(min(tl) >= 12 and max(tl) <= 14, f"route trainers Lv {min(tl)}-{max(tl)}")

print("3) canon story teams are lifted, keeping their spread")
got = levels.follow_team(g, [9, 11, 12])
check(got == [11, 13, 14], f"{got}: ace at the team's best")
check(levels.follow_team(g, [30, 32]) == [30, 32], "a team already above stays as it is")

print("4) an area's own level is the floor, the team is the ceiling (Jordan, 10-26)")
vr = levels._area_levels(g).get("VICTORY_ROAD", 0)
check(vr > 14 and levels.area_level(g, "VICTORY_ROAD") == 14,
      f"Victory Road (own Lv {vr}) is held to the Lv 14 lead: {levels.area_level(g, 'VICTORY_ROAD')}")
lead.level = vr + 10
check(levels.area_level(g, "VICTORY_ROAD") == vr + 10 - levels.POSTGAME_UNDER,
      "a team well above it pulls it up (3 under the lead)")
lead.level = vr + 2
check(levels.area_level(g, "VICTORY_ROAD") == vr, "in between, the area keeps its own level")
lead.level = 14

print("5) Gyms keep their canon levels")
check(levels.gym_team_levels("KANTO", "PEWTER_CITY", 2, "leader") == [12, 14], "Brock 12/14")
print("FAILURES:", fails)
