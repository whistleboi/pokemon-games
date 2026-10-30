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

print("2) canon levels (Jordan, 10-29): an over-levelled team doesn't pull wild Pokemon or trainers up")
weak = mk(1)
weak.level = 6
lead.level = 14
story.player_team = [weak, lead]
area = levels.area_level(g, "ROUTE_1")
wl = [levels.wild_level(g, "ROUTE_1") for _ in range(200)]
check(min(wl) >= max(2, area - 2) and max(wl) <= area + 1, f"wild Lv {min(wl)}-{max(wl)} around Route 1's own {area}")
tl = [levels.trainer_level(g, "ROUTE_1") for _ in range(200)]
check(max(tl) <= area + 3, f"route trainers Lv {min(tl)}-{max(tl)}")

print("3) canon story teams keep the games' levels")
check(levels.follow_team(g, [9, 11, 12]) == [9, 11, 12], "not lifted to the team's best")

print("4) a late area keeps its own level, whatever the team")
vr = levels._area_levels(g).get("VICTORY_ROAD", 0)
check(vr > 14 and levels.area_level(g, "VICTORY_ROAD") == vr,
      f"Victory Road stays Lv {vr} for a Lv 14 lead: {levels.area_level(g, 'VICTORY_ROAD')}")
lead.level = vr + 10
check(levels.area_level(g, "VICTORY_ROAD") == vr, "and for a team well above it")
lead.level = 14

print("5) Gyms keep their canon levels; the cap after the last badge is the Champion's ace")
check(levels.gym_team_levels("KANTO", "PEWTER_CITY", 2, "leader") == [12, 14], "Brock 12/14")
story.badges = {"KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]}
story.current_area_key = "VICTORY_ROAD"
check(levels.story_level_cap(story) == levels.CHAMPION_ACE["KANTO"], f"cap {levels.story_level_cap(story)}")
story.badges = {}
print("FAILURES:", fails)
