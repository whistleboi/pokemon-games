# The Royal Unova (batch 3a's close-out, 11-21; src/world/royal_unova.py): the evening cruise from Castelia's Cruise Dock,
# played as a player meets it. Boarding only in the season's evening hours, once a day, $1,000; aboard in the live 3D
# view, the crewman's count, the port and starboard hints, cabin doors paired to their cabins, the day's Trainers in
# their cabins (B2W2's teams), 5 whistles 45 s apart (a long talker skips to the next), the prize when all are beaten,
# and off at the Cruise Dock.
#   bash dev/checks/run.sh unova_royal
import datetime
from src.states.overworld import CityState, PlayState as _PS
from src.world import royal_unova as ru, seasons

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.story_flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
story.story_flags["visited_CASTELIA_CITY"] = True
said = []
_say0 = None


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard: shared, Checks C5)


def until(cond, n=400):
    for _ in range(n):
        if cond():
            return True
        settle(1)
    return cond()


def pick(value):
    """Answer the pick list that's up (Board / Not now, Stay / Disembark)."""
    st = g.current_state
    if type(st).__name__ == "PickListState":
        st.pick(value); settle(5)
        return True
    return False


def dock():
    story.current_area_key = "CASTELIA_CITY"
    g.walk_town_pos = ("CASTELIA_CITY", (18, 17), (0, -1)); g.walk_town_room = ("CASTELIA_CITY", "cruise_dock")
    g.change_state(CityState(g)); settle()
    return g.current_state


day = datetime.date.today()
lo, hi = ru.EVENING[seasons.current_season(day)]
DAY = ru.DAYS[day.weekday()]

print("1) boarding at the Cruise Dock")
story.money = 5000
story._cruise_now = datetime.datetime.combine(day, datetime.time(12, 0))
t = dock()
check(getattr(t, "room", None) == "cruise_dock", "the Cruise Dock opens")
said.clear(); t._talk((18, 16)); settle(30)
check(type(g.current_state).__name__ != "PickListState" and "come back" in heard().lower(),
      f"at noon the attendant says to come back in the evening ({said[-1:]})")
story._cruise_now = datetime.datetime.combine(day, datetime.time(lo, 30))
t = dock(); said.clear(); t._talk((18, 16)); settle(30)
check(type(g.current_state).__name__ == "PickListState", "in the evening, she offers a ticket")
pick(False)
check(story.money == 5000 and story.current_area_key == "CASTELIA_CITY", "...'Not now' keeps your money")
t = dock(); t._talk((18, 16)); settle(30); pick(True)
until(lambda: type(g.current_state).__name__ == "DungeonState"); settle(5)
s = g.current_state
check(story.money == 4000 and story.current_area_key == "ROYAL_UNOVA" and type(s).__name__ == "DungeonState",
      f"'Board' takes $1,000 and puts you aboard, on the route walker ({story.money}, {story.current_area_key}, {type(s).__name__})")
check(tuple(s.run.player) == ru.BOARD_AT, f"...at the bow end of the hall ({tuple(s.run.player)})")
check(s._dl_live(), "...in the live 3D view")

s.run.player = s.anim_from = s.partner = s.partner_from = (29, 11); s.anim = 0; settle(3)
said.clear(); s.step(0, -1); settle(60)
check(story.story_flags.get("b2_ru_deck_note") and "observation deck" in heard(), "at the top of the stairs: the deck is just ahead (Black 2's own trigger)")
s.run.player = s.anim_from = s.partner = s.partner_from = ru.BOARD_AT; s.anim = 0; settle(3)

print("2) aboard: the crew and the cabins")
day_list = ru.todays(s)
check(len(day_list) == [4, 3, 4, 5, 4, 6, 7][day.weekday()], f"today ({DAY}) the game's number of Trainers sail ({day_list})")
said.clear(); s._use_figure(next(m for m in s.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "Sailor by the stairs")); settle(20)
check(f"{len(day_list)} Trainers aboard" in heard() and type(g.current_state).__name__ == "PickListState",
      f"the sailor by the stairs counts today's Trainers and offers to let you off ({said[:2]})")
pick(False)
said.clear(); s._use_figure(next(m for m in s.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "Sailor to port")); settle(20)
cab = s.recipe["art"]["cruise"]["cabins"]
port = sum(1 for x in day_list if cab[x]["side"] == "port")
check(f"{port} Trainer" in heard() and "port side" in heard(), f"the port sailor: {port} on the port side ({said[:1]})")
said.clear(); s._use_figure(next(m for m in s.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "Sailor to starboard")); settle(20)
blue = sum(1 for x in day_list if cab[x]["door"] == "blue")
check(f"{blue} of today's" in heard(), f"the starboard sailor: {blue} behind blue doors ({said[:1]})")
names = {m.payload.get("text") for m in s.run.floor.movers if isinstance(getattr(m, "payload", None), dict)}
here = [x for x in day_list if any(n and n.endswith(" " + x) for n in names)]
check(sorted(here) == sorted(day_list), f"exactly today's Trainers stand in their cabins ({sorted(here)})")
links = s.recipe["art"].get("links") or {}
check(len(links) == 30, f"all 30 doors lead somewhere: 15 cabins and back ({len(links)})")
s.run.player = s.anim_from = s.partner = s.partner_from = (14, 15); s.anim = 0; settle(3)
s.step(0, -1); settle(30)
check(69 <= s.run.player[0] <= 78 and s.run.player[1] <= 6, f"the first port cabin's blue door leads into its cabin ({tuple(s.run.player)})")
for _ in range(3):
    if s.run.player[0] < 60:
        break
    s.step(0, 1); settle(30)
check(abs(s.run.player[0] - 14) <= 1 and 15 <= s.run.player[1] <= 16, f"...and back out to the hall by its door ({tuple(s.run.player)})")

import json as _json, os as _os
_M = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_miss = []
for _a in ("ROYAL_UNOVA", "LIBERTY_GARDEN"):
    _txt = _json.dumps(_M[_a])
    for _sh in set(__import__("re").findall(r"sheet:(b2_[a-z0-9_]+\.png)", _txt)):
        if not _os.path.isfile(_os.path.join("assets", "dungeon", "characters", _sh)):
            _miss.append((_a, _sh))
check(not _miss, f"every person aboard and on Liberty Garden has their sprite sheet ({_miss})")

print("3) a Trainer, the whistles, a long talker")
first = day_list[0]
mv = next(m for m in s.run.floor.movers if isinstance(m.payload, dict) and str(m.payload.get("text", "")).rstrip().endswith(" " + first))
s._use_figure(mv); settle(30)
_b = getattr(g.current_state, "next_state", None) or g.current_state
check("Trainer" in type(g.current_state).__name__ and getattr(_b, "opponent_team", None),
      f"walk up to {first} and the battle starts ({type(g.current_state).__name__}: {[(p.id, p.level) for p in getattr(_b, 'opponent_team', [])]})")
g.change_state(s); settle(3)
v = g.royal_unova_voyage
v.pop("hello", None); v["frames"] = ru.WHISTLE_FRAMES - 2; v["blown"] = 1
settle(5)
check(v["blown"] == 2 and "Whistle 2" in s.toast, f"45 seconds in, the second whistle ({v['blown']}, {s.toast})")
frames = v["frames"]
said.clear(); s.say(["A long story..."]); settle(1); fr2 = v["frames"]; settle(20)
check(fr2 == frames or fr2 == frames + 1, "the clock stops while someone's talking")
talk = next((m for m in s.run.floor.movers if isinstance(m.payload, dict) and (m.payload.get("event") or {}).get("cruise") == "talker"), None)
if talk:
    s._use_figure(talk); settle(60)
    check(v["blown"] == 3, f"a long talker: the next whistle blows as they finish ({v['blown']})")
for x in day_list:
    story.story_flags[cab[x]["flag"]] = True
before = story.inventory.get(s.recipe["art"]["cruise"]["prizes"][DAY], 0)
v["frames"] = ru.WHISTLE_FRAMES * 4 - 2
until(lambda: type(g.current_state).__name__ in ("WalkTownState", "CityState") and story.current_area_key == "CASTELIA_CITY", 600); settle(10)
st = g.current_state
check(story.current_area_key == "CASTELIA_CITY" and getattr(st, "room", None) == "cruise_dock",
      f"the fifth whistle: back at the Cruise Dock ({story.current_area_key}, {getattr(st, 'room', None)})")
prize = s.recipe["art"]["cruise"]["prizes"][DAY]
check(story.inventory.get(prize, 0) == before + 1, f"every Trainer beaten: today's prize, a {prize}")
said.clear(); st._talk((18, 16)); settle(30)
check(type(g.current_state).__name__ != "PickListState" and "already sailed" in heard(), "once a day: the attendant won't sell a second ticket")

print("4) after the Hall of Fame: B2W2's stronger teams")
story.story_flags.pop("royal_unova_sailed", None)
story.story_flags["beat_unova_champion"] = True
story.story_flags["unova_move_offered"] = True
story.current_area_key = "ROYAL_UNOVA"; g.arrive_floor = ("ROYAL_UNOVA", 0, list(ru.BOARD_AT)); ru.start(g)
for x in day_list:
    story.story_flags.pop(cab[x]["flag"], None)
g.change_state(_PS(g)); settle(10); s = g.current_state
if type(s).__name__ == "DungeonState":
    mv = next(m for m in s.run.floor.movers if isinstance(m.payload, dict) and str(m.payload.get("text", "")).rstrip().endswith(" " + first))
    s._use_figure(mv); settle(30)
    _b = getattr(g.current_state, "next_state", None) or g.current_state
    team = [(p.id, p.level) for p in getattr(_b, "opponent_team", [])]
    check(team and min(lv for _i, lv in team) >= 60, f"{first}'s team after the Hall of Fame: Lv 60+ ({team})")
else:
    check(False, f"back aboard after the Hall of Fame ({type(s).__name__})")

print(f"##### {len(fails)} failures")
