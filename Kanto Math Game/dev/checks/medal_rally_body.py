# The Medal Rally beyond the starter set (11-25, Unova's roadmap): src/world/medals.py - Black 2's own Medals that the game
# can count (steps, fishing, Center rests, shopping, evolving, PC Boxes, type catchers, mono-type League wins...).
#   bash dev/checks/run.sh medal_rally
from src.world import medals, feats
fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


story = g.story_manager
story.enter_region("UNOVA")
story.current_area_key = "ASPERTIA_CITY"   # (standing in Unova: its counts are Unova's)
print("1) the list")
keys = [m[0] for m in medals.MEDALS]
check(len(keys) == len(set(keys)) and len(keys) >= 90, f"{len(keys)} Medals, each its own key")
check({"first_catch", "hidden_1", "castelia_boss"} <= set(keys), "the starter set's keys stay (saved Medals keep)")
names = {m[0]: m[1] for m in medals.MEDALS}
check(names["hidden_1"] == "Dowsing Beginner" and names["walk_5000"] == "Light Walker", "Black 2's own names")
print("2) counted as you play, in Unova")
story.inventory["MEDAL_BOX"] = 1
for kind, n in (("steps", 5000), ("fish", 10), ("heals", 10), ("purchases", 100), ("spent", 100000), ("evolved", 1)):
    feats.note(story, kind, n)
got = {m[0] for m in medals.waiting(story)}
check({"walk_5000", "fish_1", "fish_10", "center_10", "shop_100", "spend_10k", "spend_100k", "evolve_1", "first_step"} <= got,
      f"steps, fishing, Center rests, shopping, evolving earn theirs ({sorted(got & {'walk_5000', 'fish_10', 'center_10', 'spend_100k'})})")
check("walk_10000" not in got and "spend_1m" not in got, "...and not the next tier up")
print("3) a League won with one type, from the Hall of Fame's record")
story.story_flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": [{"id": 7}, {"id": 8}, {"id": 9}]}]
got = {m[0] for m in medals.waiting(story)}
check("champ_water" in got and "champ_fire" not in got and "champ_one" not in got, "an all-Water team: Water-type Champ only")
story.story_flags["hall_of_fame_records"].append({"region": "UNOVA", "team": [{"id": 6}]})
got = {m[0] for m in medals.waiting(story)}
check({"champ_fire", "champ_flying", "champ_one"} <= got, "one Charizard: Fire, Flying and One and Only")
print("4) Mr. Medal hands them over")
lines = medals.hand_out(story)
check(story.story_flags.get("medal_walk_5000") and any("Light Walker" in l for l in lines), "Light Walker received")
check(not medals.waiting(story) or all(m[0].startswith("rank_") is False for m in medals.waiting(story)), "nothing left waiting but later ranks")
print(f"##### {len(fails)} failures")
