# Unova batch 5b (11-24): the Pokemon World Tournament (the gate, the grounds and their tutors, the hall, the stadium; the
# story's first Driftveil Tournament: Hugh, Cheren, Colress; every other tournament at its desk), the Plasma Frigate's
# first visit (two Grunts, then tag battles with Cheren and Hugh, Zinzolin, the Shadow Triad), the Relic Passage's three
# chambers (their trainers, dust clouds), Relic Castle's lowest floor (Volcarona).
#   bash dev/checks/run.sh unovab5b
import json
import os
from src.states.overworld import CityState, PlayState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("DRIFTVEIL_CITY", "PWT", "PLASMA_FRIGATE", "RELIC_PASSAGE", "RELIC_PASSAGE_MIDDLE", "RELIC_PASSAGE_NORTH",
          "RELIC_CASTLE_DEPTHS"):
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE"]
flags["b2_quake_badge"] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


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


def walked(area, at):
    story.current_area_key = area; g.walk_town_pos = g.walk_town_room = None
    g.arrive_floor = (area, 0, list(at))
    said.clear()
    g.change_state(PlayState(g)); settle(30)
    return g.current_state


def _opts(o):
    return o.get("any") if isinstance(o, dict) and "any" in o else o if isinstance(o, list) else [o]


def people(st):
    out = {}
    for home, o in (getattr(st, "people", None) or {}).items():
        for c in _opts(o):
            if isinstance(c, dict) and st._shown(c):
                out[str(c.get("text", "")).rstrip()] = home
    return out


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(40)
    return True


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState")


def until(names, n=600):
    for _ in range(n):
        if type(g.current_state).__name__ in names:
            return g.current_state
        settle(1)
    return g.current_state


def win(b, won=True):
    """Stand in for a battle: past the opening words, won (or lost), back to the map."""
    from src.states.battle import TrainerIntroState
    for _ in range(3):
        if isinstance(b, TrainerIntroState) and getattr(b, "next_state", None) is not None:
            b = b.next_state
            g.change_state(b); settle(1)
    b.player_won = won
    if hasattr(b, "exit_battle"):
        b.exit_battle()
    for _ in range(400):
        if type(g.current_state).__name__ not in BATTLES + ("EvolutionState",):
            break
        settle(1)
    settle(60)


def team_of(b):
    b = getattr(b, "next_state", None) or b
    return [(int(getattr(p, "id", 0)), int(getattr(p, "level", 0))) for p in (getattr(b, "opponent_team", None) or [])]


print("1) the places: the PWT and its rooms, the Frigate's deck, the Relic Passage's chambers, Relic Castle's lowest floor")
pw = tmaps.get("PWT") or {}
check({"lobby", "stadium"} <= set(pw.get("rooms") or {}), "the PWT: grounds, hall, stadium")
for a in ("PLASMA_FRIGATE", "RELIC_PASSAGE", "RELIC_PASSAGE_MIDDLE", "RELIC_PASSAGE_NORTH", "RELIC_CASTLE_DEPTHS"):
    check(a in tmaps, f"{a} is walked")
check(set((tmaps["RELIC_CASTLE_DEPTHS"].get("rooms") or {})) == {"hall_w", "middle", "hall_e", "east", "volcarona"},
      "Relic Castle's lowest floor: five rooms in a row and Volcarona's to the north")
check(tmaps["DRIFTVEIL_CITY"]["rooms"]["pwt_gate"]["exits"].get("^") == "PWT", "Driftveil's gate leads on to the PWT")
check(any(o.get("target_area") == "PWT" and not o.get("condition") for o in SP["DRIFTVEIL_CITY"].get("travel_options") or []),
      "Driftveil's PWT link has no stand-in flag (the gate's barrier keeps it shut)")
check("area_boss" not in SP["RELIC_CASTLE"], "Volcarona isn't the menu-era Relic Castle's boss any more")

print("2) the gate: shut till Clay's invitation")
flags.pop("b2_drift_clay_out", None)
st = town("DRIFTVEIL_CITY", (5, 13), "pwt_gate", (0, 1))
check((5, 14) in getattr(st, "barred", {}), "the PWT side is shut")
flags["b2_drift_clay_out"] = True
st = town("DRIFTVEIL_CITY", (5, 13), "pwt_gate", (0, 1))
check((5, 14) not in getattr(st, "barred", {}), "after the invitation it's open")
st.step(0, 1); settle(400)
check(story.current_area_key == "PWT", f"through the gate: the PWT's grounds ({story.current_area_key})")

print("3) the grounds: Clay and Hugh at the door; the tutors")
flags.pop("b2_pwt_arrived", None)
st = town("PWT", (32, 22), face=(-1, 0))
st.step(-1, 0); settle(1200)
check(flags.get("b2_pwt_arrived"), "Clay and Hugh meet you on the plaza")
st = town("PWT", (25, 20), face=(0, -1))
ps = people(st)
check({"Hidden Power guy", "Move Reminder", "Move Deleter", "Ultimate move tutor", "Pledge tutor"} <= set(ps),
      "the five booths (Hidden Power, Reminder, Deleter, the ultimate moves, the Pledges)")
ult = next(c for o in st.people.values() for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Ultimate move tutor")
check(ult["event"]["tutor"]["choices"] == ["FRENZY-PLANT", "BLAST-BURN", "HYDRO-CANNON"] and ult["event"]["tutor"].get("min_friend"),
      "the ultimate moves, for a Pokemon with a strong bond")
st = town("PWT", (56, 19), face=(1, 0))
talk(st, "Worker by the fountain")
check(story.inventory.get("ROCKY_HELMET", 0) >= 1, "the Worker's Rocky Helmet")

print("4) the hall: Cheren, Clay, Colress, Hugh; then the Driftveil Tournament (Hugh, Cheren, Colress)")
flags.pop("b2_pwt_lobby", None)
st = town("PWT", (15, 24), "lobby", (0, -1)); settle(1500)
check(flags.get("b2_pwt_lobby"), "the hall's scene plays")
from src.world import pwt
check(len(pwt.data(g)["tournaments"]) == 13 and len(pwt.data(g)["trainers"]) == 54, "every tournament (13) and every Leader and Champion (54)")
for k in [k for k in flags if k.startswith("b2_pwt_won")]:
    flags.pop(k)
flags.pop("b2_pwt_driftveil_won", None); flags.pop("b2_pwt_run", None)
check(pwt.opponents(g, pwt.tournament("driftveil")) == ["Hugh", "Cheren", "Colress"], "the first visit's three: Hugh, Cheren, Colress")
st = town("PWT", (5, 8), "lobby", (0, -1))
bp0 = __import__("src.world.battle_points", fromlist=["bp"]).bp(story)
talk(st, "Left desk")
cur = until(BATTLES, 400)
first = team_of(cur)
check(type(cur).__name__ in BATTLES and len(first) == 3 and all(l == 25 for _, l in first),
      f"the left desk enters you: round one, Hugh's three at Lv 25 ({first})")
won = 0
for rnd in range(3):
    if type(cur).__name__ not in BATTLES:
        break
    t = team_of(cur)
    win(cur); won += 1
    if rnd < 2:
        cur = until(BATTLES, 400)
check(won == 3 and flags.get("b2_pwt_driftveil_won"), f"three wins: the Driftveil Tournament is yours ({won})")
check(__import__("src.world.battle_points", fromlist=["bp"]).bp(story) == bp0 + 1, "1 BP for it")
check(story.current_area_key == "PWT" and getattr(g.current_state, "room", None) == "lobby", "back in the hall after the final")
settle(1500)
check(flags.get("b2_pwt_after"), "Roxie and Clay after the win")

print("5) the desks after: the left desk's tournaments; the right desk's open with the League and the Leaders")
left = [t["key"] for t in pwt.data(g)["tournaments"] if t["desk"] == "left" and pwt.is_open(g, t)]
check(left == ["driftveil", "rental", "mix"], f"left desk: Driftveil, Rental, Mix ({left})")
right = [t["key"] for t in pwt.data(g)["tournaments"] if t["desk"] == "right" and pwt.is_open(g, t)]
check(right == [], f"right desk: shut till the Pokemon League ({right})")
flags["b2_pwt_won_unova"] = 1
right = [t["key"] for t in pwt.data(g)["tournaments"] if t["desk"] == "right" and pwt.is_open(g, t)]
check({"kanto", "johto", "hoenn", "sinnoh"} <= set(right), f"the Unova Leaders won: Kanto, Johto, Hoenn, Sinnoh open ({right})")
run = {"key": "kanto", "style": "single", "round": 1, "opponents": ["Brock", "Misty", "Giovanni"], "kind": None}
info = pwt.battle_info(g, run)
check(len(info["team"]) == 3 and set(info["levels"]) == {50} and info["battle_options"].get("level_cap") == 50
      and info["battle_options"].get("music") == "unova/vs_rg_leader", f"Brock in the Kanto Leaders Tournament: three at Lv 50, Kanto's Leader theme ({info['team']})")
run = {"key": "champions", "style": "double", "round": 3, "opponents": ["Blue", "Lance", "Cynthia"], "kind": None}
info = pwt.battle_info(g, run)
check(len(info["team"]) == 4 and info["battle_options"].get("double") and info["battle_options"]["music"] == "unova/vs_dp_champ",
      "Cynthia in a Double: four Pokemon, Sinnoh's Champion theme")
flags["b2_pwt_run"] = {"key": "mix", "style": "single", "round": 2, "opponents": ["X", "Cheren", "Roxie"], "kind": None}
shards = sum(story.inventory.get(s, 0) for s in pwt.SHARDS)
nxt = pwt.after_battle(g, {"world": "pwt"}, False)
check(not flags.get("b2_pwt_run") and sum(story.inventory.get(s, 0) for s in pwt.SHARDS) == shards + 1 and callable(nxt),
      "lose a round: out, with a Shard for taking part")
for f in [k for k in flags if k.startswith("b2_pwt_won_") and k != "b2_pwt_won_driftveil"]:
    flags.pop(f)

print("6) outside: Team Plasma runs for the pier; Hugh goes after them")
flags.pop("b2_pwt_plasma_seen", None)
st = town("PWT", (37, 18), face=(0, 1)); settle(1500)
check(flags.get("b2_pwt_plasma_seen"), "the Grunts, Colress, Hugh")
st = town("PWT", (38, 46), face=(1, 0))
check((39, 46) not in getattr(st, "barred", {}), "the ship at the pier can be boarded")

print("7) the Plasma Frigate: two Grunts alone, then with Cheren, then with Hugh; Zinzolin; thrown off")
for k in ("b2_frigate_1", "b2_frigate_2", "b2_frigate_3", "b2_frigate_4", "b2_frigate_done", "b2_frigate_after"):
    flags.pop(k, None); flags.pop(k + "_met", None)
flags.pop("b2_frigate_zinzolin", None)
ds = walked("PLASMA_FRIGATE", (9, 30))
check(story.current_area_key == "PLASMA_FRIGATE", f"aboard the Frigate's deck ({story.current_area_key})")
want = [[109], [568], [88, 552], [88, 20]]   # (Black 2's Grunts 372-377: Koffing; Trubbish; Grimer + Krokorok; Grimer + Raticate)
for i in range(4):
    cur = until(BATTLES, 900)
    t = [s for s, _ in team_of(cur)]
    dbl = bool(getattr(getattr(cur, "next_state", None) or cur, "partner_team", None) or "Double" in type(getattr(cur, "next_state", None) or cur).__name__
               or getattr(getattr(cur, "next_state", None) or cur, "is_double", False))
    check(type(cur).__name__ in BATTLES and t[:len(want[i])] == want[i][:len(t)] and (i < 2 or dbl or len(t) >= 2),
          f"battle {i + 1}: {t}" + (" (a tag battle)" if i >= 2 else ""))
    if type(cur).__name__ not in BATTLES:
        break
    win(cur)
    check(flags.get("b2_frigate_%d" % (i + 1)), f"b2_frigate_{i + 1}")
settle(2500)
check(flags.get("b2_frigate_done"), "Zinzolin, the Shadow Triad: thrown off the ship")
check(story.current_area_key == "PWT", f"back on the PWT's pier ({story.current_area_key})")
settle(1500)
check(flags.get("b2_frigate_after"), "Hugh and Cheren after: Cheren heads for Route 6")
st = town("PWT", (38, 46), face=(1, 0))
check((39, 46) in getattr(st, "barred", {}), "the ship has sailed")

print("8) the Relic Passage: three chambers, their trainers, dust clouds")
for a, n in (("RELIC_PASSAGE_NORTH", 3), ("RELIC_PASSAGE_MIDDLE", 4), ("RELIC_PASSAGE", 3)):
    check(len(SP[a]["trainer_pool"]) == n and SP[a].get("phenomena") == "dust" and SP[a].get("wild_tables"),
          f"{a}: Black 2's {n} trainers, wild Pokemon, dust clouds")
check(SP["RELIC_PASSAGE"]["wild_tables"]["ALL"]["grass"][0][3] <= 18 and SP["RELIC_PASSAGE_NORTH"]["wild_tables"]["ALL"]["grass"][0][3] >= 27,
      "the south chamber's Pokemon are the low ones (Lv 16-19), the north's Lv 27-30")
from src.world import phenomena
ds = walked("RELIC_PASSAGE_NORTH", (17, 4))
check(type(ds).__name__ == "DungeonState" and phenomena._kinds(ds) == ["dust"], f"the north chamber's phenomenon: dust clouds ({phenomena._kinds(ds) if hasattr(ds, 'run') else ds})")
if hasattr(ds, "run"):
    import random as _r
    got = {"shard": 0, "mon": 0}
    for i in range(30):
        _r.seed(i)
        sh = sum(story.inventory.get(s, 0) for s in phenomena.SHARDS)
        ds.mode = "MAP"
        ok = phenomena._jump_out(ds, tuple(ds.run.player), "dust")
        if sum(story.inventory.get(s, 0) for s in phenomena.SHARDS) > sh:
            got["shard"] += 1
        elif ok:
            got["mon"] += 1
            ds.run.floor.movers = [m for m in ds.run.floor.movers if getattr(m, "kind", "") != "wild"]
            ds.mode = "MAP"; ds.encounter = None
    check(got["shard"] > 0 and got["mon"] > 0, f"a dust cloud: a Shard, or its Pokemon ({got})")
ds = walked("RELIC_PASSAGE", (51, 60))
check(type(ds).__name__ == "DungeonState", "the south chamber from the Castelia Sewers")

print("9) Relic Castle's lowest floor: Volcarona")
vo = tmaps["RELIC_CASTLE_DEPTHS"]["rooms"]["volcarona"]
boss = next((c for o in vo.get("people") or [] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"), None)
check(boss and boss["boss"]["id"] == 637 and boss["boss"]["level"] == 35, "Volcarona waits in the north room, Lv 35")
check(tmaps["RELIC_CASTLE_DEPTHS"]["rooms"]["middle"].get("hidden", {}).get("6,7") == "SUN_STONE", "the middle room's hidden Sun Stone")
# each room's own wild Pokemon (main a91de160 "wild_tables" on a room): walk in and see who wanders there
def _room_wild(room):
    fl = 1 + list(tmaps["RELIC_CASTLE_DEPTHS"]["rooms"]).index(room)   # (a route's rooms are its floors after its own)
    seen = set()
    for _ in range(6):
        story.current_area_key = "RELIC_CASTLE_DEPTHS"; g.walk_town_pos = g.walk_town_room = None
        g.arrive_floor = ("RELIC_CASTLE_DEPTHS", fl, [0, 0])   # (the room's own arrival spot)
        g.change_state(PlayState(g)); settle(30)
        ds = g.current_state
        for m in ds.run.floor.movers:
            if m.kind == "wild":
                p = m.payload
                seen.add(p.get("id") if isinstance(p, dict) else getattr(p, "id", None))
    return seen
for room, want in (("volcarona", {343}), ("middle", {343}), ("hall_w", {562, 551, 28, 552})):
    got = _room_wild(room)
    check(got and got <= want, f"Relic Castle's {room} room: its own wild Pokemon, as Black 2 ({sorted(got)})")

print("10) the Journal, the music")
missions = {m["id"]: m for m in prog["JOURNAL_MISSIONS"]}
check("b2_m29" in missions and missions["b2_m29"]["completed_flag"] == "b2_frigate_done", "the Journal follows Hugh onto the Frigate")
for t in ("vs_wcs", "vs_rg_leader", "vs_gs_leader", "vs_rs_leader", "vs_dp_leader", "vs_rg_champ", "vs_dp_champ", "vs_bw_champ"):
    check(os.path.isfile(f"assets/music/unova/{t}.ogg"), f"Black 2's {t} rendered")
blob = json.dumps(json.load(open("assets/music/unova/music.json", encoding="utf-8")))
check('"PWT' in blob and "RELIC_PASSAGE" in blob, "the PWT's and the Relic Passage's own music")

for f in fails:
    print("  -", f)
print(f"##### {len(fails)} failures")
