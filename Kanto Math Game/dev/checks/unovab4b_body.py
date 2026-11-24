# Unova batch 4b (11-23): Gear Station and the Battle Subway (Black 2's own Trainers, sets and Bosses, at Lv 50; walk into the
# car, seven a train, the Subway Bosses at 21 / 49, Super lines, the Multi Train beside Nate / Rosa, BP), the Brown Line to
# Anville Town (the Lost Pansage, the turntable's car of the day, the weekend traders, the lost-and-found).
#   bash dev/checks/run.sh unovab4b
import datetime
import json
import os
from src.states.overworld import CityState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("NIMBASA_CITY", "ANVILLE_TOWN"):
    flags["visited_" + a] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
from src.world import battle_subway as bs, anville


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
        if box is not None and getattr(box, "visible", True):
            for line in getattr(box, "text_lines", []) or []:
                if not said or said[-1] != line:
                    said.append(line)
        db = getattr(st, "dialogue_box", None)
        if db is not None and getattr(db, "visible", False):
            db.advance()
        elif getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()


def heard():
    return " ".join(said)


def town(area, at, room=None, face=(0, 1)):
    story.current_area_key = area
    g.walk_town_pos = (area, tuple(at), face)
    g.walk_town_room = (area, room) if room else None
    said.clear()
    g.change_state(CityState(g)); settle(30)
    return g.current_state


def talk(st, label):
    spot = next((k for k, o in st.people.items() if isinstance(o, dict) and str(o.get("text", "")).strip() == label and st._shown(o)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(40)
    return True


def until(names, n=600):
    for _ in range(n):
        if type(g.current_state).__name__ in names:
            return g.current_state
        settle(1)
    return g.current_state


def pick(value):
    """Answer the open pick list with the row whose value is `value`."""
    cur = g.current_state
    if type(cur).__name__ == "PickListState":
        cur.pick(value)
        settle(20)


print("1) the data: Black 2's own Subway (a/2/1/1 sets, a/2/1/2 Trainers, overlay 12's looks)")
D = bs.data(g)
check(len(D["trainers"]) == 314 and len(D["sets"]) > 900 and D["level"] == 50, f"314 Trainers, {len(D['sets'])} Pokemon sets, Lv 50")
ingo = D["trainers"]["307"]
check(ingo["name"] == "Subway Boss Ingo" and [D["sets"][str(s)]["species"] for s in ingo["pool"]] == [569, 558, 601],
      "Ingo's Single Train team: Garbodor, Crustle, Klinklang (the file's)")
check(D["trainers"]["301"]["name"].endswith("Nate") and D["trainers"]["304"]["name"].endswith("Rosa"), "Nate and Rosa: the Multi partners")
miss = sorted({t["sprite"] for t in D["trainers"].values() if not os.path.isfile("assets/sprites/trainers/" + t["sprite"])})
check(not miss, f"every class's Black 2 battle picture, the Clerk (F) too (a/0/7/1 slot 47) ({miss})")
miss = sorted({t["walk"] for t in D["trainers"].values() if t["walk"] and not os.path.isfile("assets/dungeon/characters/" + t["walk"])})
check(not miss, f"every class's walking look ({miss})")
from PIL import Image
rb = Image.open("assets/sprites/trainers/b2_rich_boy.png").convert("RGB").getcolors(6400) or []
check(not any(c[1][1] > 150 and c[1][0] < 120 and c[1][2] < 120 for c in rb if c[0] > 40),
      "the Rich Boy picture is the Rich Boy (11-23: it was N's: no green hair)")

print("2) Gear Station: in from Nimbasa, the eight platforms, the Exchange counters")
nim = tmaps["NIMBASA_CITY"]
check(nim["inside"].get("38,42") == "gear", "Gear Station's door in Nimbasa")
rooms = nim["rooms"]
check(all(("plat_" + l) in rooms for l in ("single", "double", "multi", "wifi", "super_single", "super_double", "super_multi", "anville")),
      "the eight platforms")
gear = rooms["gear"]
check(sorted(set(gear["exits"].values())) == sorted({"ROOM:MAIN"} | {"ROOM:plat_" + l for l in ("single", "double", "multi", "wifi", "super_single",
                                                                                                  "super_double", "super_multi", "anville")}),
      f"each stairway down to its platform, and up to Nimbasa ({sorted(set(gear['exits'].values()))})")
st = town("NIMBASA_CITY", (16, 34), "gear", (0, -1))
labels = {str(o.get("text", "")).strip() for o in st.people.values() if isinstance(o, dict)}
check({"Exchange: items", "Exchange: TMs"} <= labels, "the Exchange Service Corner's two counters (items, TMs)")

print("3) a ride: board, the Trainer walks in, a Lv 50 battle, CONTINUE, seven to a train")
for k in [k for k in flags if k.startswith("b2_sub")]:
    flags.pop(k)
for p in story.player_team:
    p.current_hp = getattr(p, "max_hp", p.current_hp) or p.current_hp
st = town("NIMBASA_CITY", (11, 13), "plat_single", (1, 0))
talk(st, "Depot Agent")
cur = until(("TrainerIntroState",))
check(not tmaps["NIMBASA_CITY"]["rooms"]["car"].get("people"), "the car is empty, as in Black 2: nobody but whoever walks in")
check(type(cur).__name__ == "TrainerIntroState" and flags.get("b2_sub_riding") == "single",
      f"aboard the Single Train: the next Trainer walks in from the next car ({type(cur).__name__})")
if type(cur).__name__ == "TrainerIntroState":
    b = cur.next_state
    check(len(b.opponent_team) == 3 and all(p.level == 50 for p in b.opponent_team), f"three Pokemon, all Lv 50 ({[p.level for p in b.opponent_team]})")
    check(getattr(b, "facility", None) == {"world": "battle_subway", "line": "single"}, "a facility battle: no whiting out, back to the Subway")
    check(bs.battle_info(g, "single")["battle_options"].get("level_cap") == 50, "yours battle at Lv 50 at most (main's battle option)")
    nxt = bs.after_battle(g, b.facility, True)
    nxt(); settle(5)
    check(type(g.current_state).__name__ == "PickListState" and flags.get("b2_sub_single_streak") == 1,
          "won: 1 in a row, and 'NEXT CAR: No. 2' asks CONTINUE or RETIRE")
    pick("go")
    cur = until(("TrainerIntroState",))
    check(type(cur).__name__ == "TrainerIntroState", "CONTINUE: the next Trainer walks in")
from src.world import battle_points as BP
before = BP.bp(story)
flags["b2_sub_single_streak"] = 6
flags["b2_sub_riding"] = "single"; bs.next_foe(g, "single")
nxt = bs.after_battle(g, {"world": "battle_subway", "line": "single"}, True); nxt(); settle(30)
cur = g.current_state
check(getattr(cur, "room", None) == "subway_stop" and flags.get("b2_sub_single_streak") == 7 and BP.bp(story) > before,
      f"the seventh win: off at the end of the line, BP paid ({getattr(cur, 'room', None)}, {BP.bp(story) - before} BP)")
check(flags.get("b2_lost_found_first") is None or flags.get("b2_lost_found_item"), "the train won: Anville's lost-and-found finds something")
talk(cur, "Depot Agent")
check(type(g.current_state).__name__ == "PickListState", "the station's Depot Agent: NEXT TRAIN or BACK TO GEAR STATION")
pick("back")
check(getattr(g.current_state, "room", None) == "gear", "back up to Gear Station")

print("4) the Subway Bosses: Ingo is the 21st; beating him opens the Super Single Train")
check(not bs.is_open(g, "super_single"), "the Super Single Train is shut at first")
flags["b2_sub_single_streak"] = 20; flags["b2_sub_riding"] = "single"
bs.next_foe(g, "single")
check(flags["b2_sub_foe"] == "boss" and bs.foe_sheet(g) == "b2_c207.png", "battle 21: Ingo walks in (Nimbasa's own Ingo look)")
info = bs.battle_info(g, "single")
check(info["name"] == "Subway Boss Ingo" and info["levels"] == [50, 50, 50], f"Ingo's team at Lv 50 ({info['name']})")
nxt = bs.after_battle(g, {"world": "battle_subway", "line": "single"}, True)
check(bs.is_open(g, "super_single") and flags.get("b2_sub_single_boss"), "Ingo beaten: the Super Single Train is open")
flags["b2_sub_super_single_streak"] = 48; flags["b2_sub_riding"] = "super_single"; bs.next_foe(g, "super_single")
info = bs.battle_info(g, "super_single")
check(flags["b2_sub_foe"] == "boss" and [s for s in info["team"]] == [609, 530, 612], f"the Super line's 49th: Ingo's Super team ({info['team']})")
flags["b2_sub_super_single_streak"] = 3; flags["b2_sub_riding"] = "super_single"; flags["b2_sub_foe"] = bs._pick(g, "super_single", 4)
check(111 <= int(flags["b2_sub_foe"]) <= 160, f"a Super line's early Trainers: 111-160 ({flags['b2_sub_foe']})")
flags["b2_sub_double_streak"] = 0; flags["b2_sub_riding"] = "double"; bs.next_foe(g, "double")
info = bs.battle_info(g, "double")
check(info["battle_options"].get("double") and len(info["team"]) == 4, "the Double Train: double battles, four Pokemon")

print("5) the Multi Train: Rosa beside you (a boy), with the team you ask for")
flags["b2_sub_multi_streak"] = 0; flags["b2_sub_riding"] = "multi"; flags["b2_sub_partner_pool"] = 0; bs.next_foe(g, "multi")
info = bs.battle_info(g, "multi")
o = info["battle_options"]
check(o.get("double") and o["partner"]["name"] == "Rosa" and len(o["partner"]["team"]) == 2 and len(info["team"]) == 2
      and len(o["second_trainer"]["team"]) == 2, "two of yours and two of Rosa's against two Trainers' two each")
st = town("NIMBASA_CITY", (11, 13), "plat_multi", (1, 0))
talk(st, "Depot Agent")
check(type(g.current_state).__name__ == "PickListState" and "ROSA" in str(getattr(g.current_state, "title", "")),
      "boarding the Multi Train: Rosa asks what kind of team to bring")
pick(2)
check(flags.get("b2_sub_partner_pool") == 2, "BALANCE picked")

print("6) a loss ends the streak, back on the platform")
flags["b2_sub_double_streak"] = 5; flags["b2_sub_riding"] = "double"
nxt = bs.after_battle(g, {"world": "battle_subway", "line": "double"}, False); nxt(); settle(20)
check(flags.get("b2_sub_double_streak") == 0 and getattr(g.current_state, "room", None) == "plat_double" and not flags.get("b2_sub_riding"),
      "lost: the streak is over, healed, on the Double Train's platform")

print("7) the Brown Line to Anville Town, and back")
st = town("NIMBASA_CITY", (11, 13), "plat_anville", (1, 0))
talk(st, "Depot Agent"); settle(120)
cur = until(("WalkTownState", "CityState"), 300)
settle(60)
check(story.current_area_key == "ANVILLE_TOWN" and tuple(getattr(g.current_state, "player", ())) == (21, 52),
      f"the local train to Anville Town's station ({story.current_area_key}, {getattr(g.current_state, 'player', None)})")
st = g.current_state
talk(st, "Depot Agent")
for _ in range(900):   # (the ride scene plays first: out of Anville's station, into Gear Station)
    settle(1)
    if story.current_area_key == "NIMBASA_CITY" and getattr(g.current_state, "room", None):
        break
check(story.current_area_key == "NIMBASA_CITY" and getattr(g.current_state, "room", None) == "plat_anville",
      f"and back to Gear Station's Brown Line platform ({story.current_area_key}, {getattr(g.current_state, 'room', None)})")

print("8) Anville: the Lost Pansage")
for k in ("b2_pansage_asked", "b2_pansage_back", "b2_pansage_reward"):
    flags.pop(k, None)
st = town("ANVILLE_TOWN", (26, 39), None, (0, -1))
talk(st, "Girl on the platform")
check(flags.get("b2_pansage_asked") and "Pansage" in heard(), "the girl on the bridge: Pansage got on the wrong train")
st = town("NIMBASA_CITY", (50, 20), None, (0, -1))
talk(st, "Depot Agent by the theater")
check(flags.get("b2_pansage_back"), "the Depot Agent outside the Musical Theater has it")
bp_ = story.inventory.get("BRIGHT_POWDER", 0)
st = town("ANVILLE_TOWN", (26, 39), None, (0, -1))
talk(st, "Girl on the platform")
check(story.inventory.get("BRIGHT_POWDER", 0) == bp_ + 1 and flags.get("b2_pansage_reward"), "home again: a BrightPowder for you")
st = town("ANVILLE_TOWN", (15, 50), None, (0, 1))
check(any(str(o.get("text")) == "Pansage" and st._shown(o) for o in st.people.values() if isinstance(o, dict)), "and Pansage is back beside her")

print("9) Anville: the turntable's car, the weekend traders, the lost-and-found")
real = anville._today
anville._today = lambda: datetime.date(2026, 11, 3)   # (a Tuesday, the 3rd: a Multi Train car)
check(anville.car_today()[0] == "a Multi Train" and not anville.condition(story, "weekend"), "the 3rd: a Multi Train on the turntable; a weekday")
st = town("ANVILLE_TOWN", (26, 40), None, (0, -1))
labels = {str(o.get("text", "")) for o in st.people.values() if isinstance(o, dict) and st._shown(o)}
check("Traveller with a pack" not in labels, "no traders on a weekday")
anville._today = lambda: datetime.date(2026, 11, 21)   # (a Saturday)
st = town("ANVILLE_TOWN", (26, 40), None, (0, -1))
labels = {str(o.get("text", "")) for o in st.people.values() if isinstance(o, dict) and st._shown(o)}
check({"Traveller with a pack", "Lady by the tracks"} <= labels, f"Saturday: the traders are in town ({sorted(labels)[:6]})")
anville._today = lambda: datetime.date(2026, 11, 28)   # (a Saturday, but the Hyperspeed Train's day)
check(not anville.condition(story, "weekend") and anville.hyperspeed(), "the 28th: no train comes, no traders")
anville._today = lambda: datetime.date(2026, 11, 21)
story.inventory["ESCAPE_ROPE"] = 2; rv = story.inventory.get("REVIVE", 0)
st = town("ANVILLE_TOWN", (23, 39), None, (0, -1))
talk(st, "Traveller with a pack")
pick("yes")
check(story.inventory.get("REVIVE", 0) == rv + 1 and story.inventory.get("ESCAPE_ROPE", 0) == 0, "two Escape Ropes for a Revive")
labels = {str(o.get("text", "")) for o in g.current_state.people.values() if isinstance(o, dict) and g.current_state._shown(o)}
check("Collector" in labels, "the Star Piece collector too, now PP Up is in the game (main 02ba2d9d)")
story.inventory["STAR_PIECE"] = 1; pu = story.inventory.get("PP_UP", 0)
st = town("ANVILLE_TOWN", (37, 28), None, (0, -1))
talk(st, "Collector"); pick("yes")
check(story.inventory.get("PP_UP", 0) == pu + 1 and not story.inventory.get("STAR_PIECE"), "a Star Piece for a PP Up")
anville._today = real
for k in ("b2_lost_found_first", "b2_lost_found_item", "b2_lost_found_n"):
    flags.pop(k, None)
rc = story.inventory.get("RARE_CANDY", 0)
st = town("ANVILLE_TOWN", (5, 7), "lost_found", (0, -1))
talk(st, "Depot Agent")
check(story.inventory.get("RARE_CANDY", 0) == rc + 1, "the lost-and-found: a Rare Candy first")
anville.found_item(story); anville.found_item(story)
item = flags.get("b2_lost_found_item"); n0 = story.inventory.get(item, 0)
talk(g.current_state, "Depot Agent")
check(item and story.inventory.get(item, 0) == n0 + 2, f"two trains won: two of what he found ({item})")

print("9b) the trains: the Brown Line's ride, a train waiting at each platform (cut from Black 2's Anville picture)")
plat = tmaps["NIMBASA_CITY"]["rooms"]["plat_single"]
check(len(plat.get("barred", [])) > 40 and all(b["look"].startswith("img:b2_train/") for b in plat["barred"]), "the train on the platform's track")
agent = [o for o in tmaps["NIMBASA_CITY"]["rooms"]["plat_anville"]["people"] if isinstance(o, dict) and o.get("text") == "Depot Agent"][0]
from src.states.overworld.area_transition import ride_scene
legs = ride_scene(g, agent["event"]["ride"])
check(legs and len(legs) == 2, "the Brown Line's ride: out of Gear Station, into Anville's station")
back = [o for o in tmaps["ANVILLE_TOWN"]["people"] if isinstance(o, dict) and o.get("text") == "Depot Agent"][0]
check(ride_scene(g, back["event"]["ride"]), "and the ride back")

print("10) the Quest Book, music")
ids = {m["id"] for m in prog["JOURNAL_MISSIONS"]} if isinstance(prog.get("JOURNAL_MISSIONS"), list) else set(prog.get("JOURNAL_MISSIONS", {}))
check({"b2_s_pansage", "b2_s_subway_boss"} <= ids, "side pages: The Lost Pansage, Last Stop: the Subway Boss")
feats = json.load(open("assets/quest_feats.json", encoding="utf-8"))["UNOVA"]
check(any(f["id"] == "subway" for f in feats), "the Feat: Subway Regular (best streak)")
mj = json.load(open("assets/music/unova/music.json", encoding="utf-8"))
blob = json.dumps(mj)
check("gear_station" in blob and "battle_subway" in blob and "t_03" in blob, "Black 2's tracks: Gear Station, the Subway car, Anville Town")
print("11) battle backgrounds: Black 2's own, by each zone's battle background number (11-23)")
from src.world import battle_bg as _bb
_ix = _bb.index(g, "UNOVA")
check(_ix and len(_ix["areas"]) >= 26, "Unova has its own battle background index")
missing = sorted({f for e in _ix["areas"].values() for f in ([e] if isinstance(e, str) else e.values())
                  if not os.path.isfile(os.path.join("assets", "battle_bg", "UNOVA", f))})
check(not missing, f"every picture it names is there ({missing})")
check(str(_bb.pick(g, "UNOVA_ROUTE_19")).endswith("bg01.png") and str(_bb.pick(g, "LOSTLORN_FOREST")).endswith("bg06.png"),
      "Route 19 on Black 2's open field, Lostlorn Forest on its forest (zone values 1 and 6)")
check(str(_bb.pick(g, "NIMBASA_CITY", trainer=True, gym=True)).endswith("bg09.png"), "Elesa's Gym: its room's own background")
print(f"##### {len(fails)} failures")
