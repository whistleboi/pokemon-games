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
_cap = levels.story_ace(story)   # (the lift and the bands follow the ace itself; the Exp. cap is ace + 2: Jordan 11-21)
check(levels.is_postgame(story) or levels.area_level(g, "VICTORY_ROAD") == max(vr, _cap - 3),
      f"a lead at the level cap ({_cap}): the area rises to 3 under the cap, never below its own (Jordan 11-15) {levels.area_level(g, 'VICTORY_ROAD')}")
lead.level = 3
check(levels.is_postgame(story) or levels.area_level(g, "VICTORY_ROAD") == vr, "a lead under the cap: the area keeps its canon level (Jordan 11-15)")
lead.level = 14
_first = weak.level
weak.level = _cap   # (the lead is the team's first Pokemon)
_wl = [levels.wild_level(g, "ROUTE_1") for _ in range(400)]
_tl = [levels.trainer_level(g, "ROUTE_1") for _ in range(400)]
_tt = [lv for _ in range(100) for lv in levels.trainer_team_levels(g, "ROUTE_1", 3)]
_r1 = levels.canon_area_level(g, "ROUTE_1")
check(min(_wl) >= max(2, _r1 - 2) and max(_wl) <= _r1 + 1, f"a lead at the cap ({_cap}): wild Pokemon keep Route 1's own Lv {min(_wl)}-{max(_wl)} (Jordan 11-24: no wild lift)")
check(min(_tl) == _cap - 3 and max(_tl) == _cap + 1, f"...route trainers Lv {min(_tl)}-{max(_tl)} the same")
check(min(_tt) >= _cap - 3 and max(_tt) <= _cap + 1, f"...their whole teams too: Lv {min(_tt)}-{max(_tt)}")
_vw = [levels.wild_level(g, "VICTORY_ROAD") for _ in range(200)]
check(min(_vw) >= vr - 2, f"...an area above the band keeps its own levels: Victory Road Lv {min(_vw)}-{max(_vw)}")
weak.level = _first

print("5) Gyms keep their canon levels; the cap after the last badge is the Champion's ace + 2")
check(levels.gym_team_levels("KANTO", "PEWTER_CITY", 2, "leader") == [12, 14], "Brock 12/14")
story.badges = {"KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]}
story.current_area_key = "VICTORY_ROAD"
check(levels.story_level_cap(story) == levels.CHAMPION_ACE["KANTO"] + 2, f"cap = the Champion's ace + 2: {levels.story_level_cap(story)}")
story.badges = {}

print("6) every region: the cap is the next Leader's ace + 2, the Champion's ace + 2 after the last badge (Jordan 11-21)")
_want = {"KANTO": [16, 23, 26, 31, 45, 45, 49, 52, 65], "JOHTO": [15, 19, 21, 27, 33, 37, 37, 43, 52],
         "HOENN": [16, 18, 23, 30, 32, 37, 47, 48, 61], "SINNOH": [16, 24, 32, 32, 38, 41, 44, 51, 68],
         "UNOVA": [15, 20, 26, 32, 35, 41, 50, 53, 61], "KALOS": [14, 27, 34, 36, 39, 44, 50, 61, 70],
         "ALOLA": [12, 18, 30, 46, 56, 60], "ORANGE": [24, 37, 42, 48, 54], "ORRE": [16, 23, 26, 31, 43, 47, 50, 52, 65]}   # (Orre 11-24: the eight Gyms, then Eldes 63)
_area0, _mode0 = story.current_area_key, story.level_cap_mode
story.level_cap_mode = "STORY"
for _r, _caps in _want.items():
    story.current_area_key = levels.GYM_ORDER[_r][0]
    _got = []
    for _n in range(len(_caps)):
        story.badges = {_r: ["B%d" % i for i in range(_n)]}
        _got.append(levels.story_level_cap(story) if story.get_current_region() == _r and not levels.is_postgame(story) else None)
    check(_got == _caps, f"{_r}: caps by badge count {_got}")
    story.badges = {_r: []}
    check(levels.xp_cap(story) == _caps[0] and levels.story_ace(story) == _caps[0] - 2,
          f"...Exp. stops at {levels.xp_cap(story)}; the wild lift, legends and rematches still follow the ace {levels.story_ace(story)}")
story.badges = {}
story.current_area_key, story.level_cap_mode = _area0, _mode0
print("7) after the title, wild Pokemon still keep their area's own levels (Jordan 11-24)")
_saved_team = list(story.player_team)
for p_ in story.player_team:
    if p_:
        p_.level = 90
_pw = [levels.wild_level(g, "ROUTE_1") for _ in range(200)]
check(max(_pw) <= levels.canon_area_level(g, "ROUTE_1") + 1, f"a Lv 90 team: Route 1's wild Pokemon stay Lv {min(_pw)}-{max(_pw)}")
story.player_team = _saved_team
print(f"##### {fails} failures")
